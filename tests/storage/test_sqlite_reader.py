"""SQLite reader tests (d.md §13): read-only access, table enumeration,
lineage reporting and refusal of unsafe table names.

The database fixture is created in ``tmp_path`` (synthetic); the repository
SQLite stores are local-only and never required by CI.
"""

import hashlib
import sqlite3

import pytest

from storage.contracts import ArtifactDescriptor, ReaderError
from storage.readers import get_reader


def _build_db(tmp_path, *, with_lineage=True, name="trends.db"):
    path = tmp_path / name
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE runs (run_id TEXT PRIMARY KEY, source TEXT NOT NULL);
        CREATE TABLE videos (video_id TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE run_videos (
            run_id TEXT REFERENCES runs(run_id),
            video_id TEXT REFERENCES videos(video_id),
            position INTEGER,
            PRIMARY KEY (run_id, video_id)
        );
        INSERT INTO runs VALUES ('run-1', 'youtube');
        INSERT INTO videos VALUES ('vid-1', 'synthetic');
        INSERT INTO run_videos VALUES ('run-1', 'vid-1', 1);
        """
    )
    if with_lineage:
        connection.executescript(
            """
            CREATE TABLE record_lineage (
                record_id TEXT NOT NULL,
                source_run_id TEXT NOT NULL,
                source_artifact_id TEXT NOT NULL,
                source_record_id TEXT,
                PRIMARY KEY (record_id, source_run_id, source_artifact_id)
            );
            INSERT INTO record_lineage VALUES ('vid-1', 'run-1', 'artifact-1', 'vid-1');
            """
        )
    connection.commit()
    connection.close()
    return path


def _descriptor(path) -> ArtifactDescriptor:
    return ArtifactDescriptor(
        artifact_id="db-artifact",
        artifact_type="database",
        format="sqlite",
        schema_id="sqlite-trends-db-v1",
        path=str(path),
    )


def test_validate_accepts_a_sqlite_database(tmp_path):
    reader = get_reader("sqlite-reader")
    assert reader.validate(_descriptor(_build_db(tmp_path))) == []


def test_validate_rejects_a_non_database_file(tmp_path):
    reader = get_reader("sqlite-reader")
    text = tmp_path / "not.db"
    text.write_text("plain text", encoding="utf-8")
    violations = reader.validate(_descriptor(text))
    assert violations and "magic" in violations[0]


def test_tables_are_enumerated_sorted(tmp_path):
    reader = get_reader("sqlite-reader")
    tables = reader.tables(_descriptor(_build_db(tmp_path)))
    assert tables[:3] == ["record_lineage", "run_videos", "runs"]


def test_read_mode_tables_lists_names_only(tmp_path):
    reader = get_reader("sqlite-reader")
    rows = list(reader.read(_descriptor(_build_db(tmp_path)), mode="tables"))
    assert {row["table"] for row in rows} >= {"runs", "videos"}


def test_table_rows_require_a_known_table(tmp_path):
    reader = get_reader("sqlite-reader")
    descriptor = _descriptor(_build_db(tmp_path))
    with pytest.raises(ReaderError):
        list(reader.read(descriptor, mode="table_rows", table="runs; DROP TABLE runs"))
    rows = list(reader.read(descriptor, mode="table_rows", table="runs", limit=1))
    assert rows == [{"record_index": 0, "record": {"run_id": "run-1", "source": "youtube"}}]


def test_lineage_summary_reports_the_conceptual_table(tmp_path):
    reader = get_reader("sqlite-reader")
    summary = reader.lineage_summary(_descriptor(_build_db(tmp_path)))
    assert summary == {
        "lineage_table": "record_lineage",
        "lineage_table_present": True,
        "lineage_row_count": 1,
    }
    without = reader.lineage_summary(
        _descriptor(_build_db(tmp_path, with_lineage=False, name="plain.db"))
    )
    assert without["lineage_table_present"] is False


def test_connection_is_read_only_and_leaves_the_file_unchanged(tmp_path):
    import sqlite3

    path = _build_db(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    reader = get_reader("sqlite-reader")
    descriptor = _descriptor(path)
    list(reader.read(descriptor, mode="table_rows", table="videos"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    # The reader's own connection is opened with mode=ro: a write attempt is
    # rejected by SQLite itself, not merely by convention.
    connection = reader._connect(path)
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("INSERT INTO runs VALUES ('run-2', 'x')")


def test_missing_database_is_reported(tmp_path):
    reader = get_reader("sqlite-reader")
    violations = reader.validate(_descriptor(tmp_path / "ghost.db"))
    assert violations == ["file does not exist"]
