"""Local trends.db verification tests (ART-007).

Every database here is synthetic and lives in ``tmp_path``: the repository
SQLite stores are local-only and never required.  One test executes the real
``datasets/youtube-consistency/schema/schema.sql`` so the verifier's
expected tables stay honest against the committed schema.
"""

import json
import sqlite3
from pathlib import Path

from storage.cli import (
    EXIT_IO,
    EXIT_OK,
    EXIT_REFUSED,
    TRENDS_DB_DEFAULT_PATH,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = REPO_ROOT / "datasets" / "youtube-consistency" / "schema" / "schema.sql"


def _from_schema(tmp_path: Path, name: str = "trends.db") -> Path:
    path = tmp_path / name
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO runs (run_id, search_term, max_videos, collection_timestamp) "
        "VALUES ('run-1', 'synthetic', 10, '2026-10-15T00:00:00Z')"
    )
    connection.commit()
    connection.close()
    return path


def _run(argv):
    return main(argv)


def test_schema_sql_builds_a_verifiable_store(tmp_path, capsys):
    code = _run(["verify-trends-db", "--db", str(_from_schema(tmp_path))])
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["ok"] is True
    assert document["problems"] == []
    assert document["read_only"] is True
    assert set(document["tables"]["present"]) >= {"runs", "videos", "run_videos"}
    assert set(document["views"]["present"]) >= {"v_run_summary", "v_video_appearance"}
    assert document["tables"]["row_counts"]["runs"] == 1


def test_record_lineage_absence_is_deferred_not_a_failure(tmp_path, capsys):
    code = _run(["verify-trends-db", "--db", str(_from_schema(tmp_path))])
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["lineage"] == {
        "table": "record_lineage",
        "present": False,
        "row_count": None,
        "status": "deferred_absent",
    }


def test_missing_table_is_refused(tmp_path, capsys):
    path = tmp_path / "thin.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY)")
    connection.commit()
    connection.close()
    code = _run(["verify-trends-db", "--db", str(path)])
    assert code == EXIT_REFUSED
    document = json.loads(capsys.readouterr().out)
    assert document["ok"] is False
    assert any("videos" in problem for problem in document["problems"])


def test_absent_database_fails_gracefully(tmp_path, capsys):
    code = _run(["verify-trends-db", "--db", str(tmp_path / "ghost.db")])
    assert code == EXIT_IO
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "database not found" in captured.err
    assert "Git-ignored" in captured.err


def test_default_path_targets_the_youtube_consistency_store():
    assert TRENDS_DB_DEFAULT_PATH == "datasets/youtube-consistency/data/trends.db"


def test_non_database_file_fails_gracefully(tmp_path, capsys):
    text = tmp_path / "not.db"
    text.write_text("plain text", encoding="utf-8")
    code = _run(["verify-trends-db", "--db", str(text)])
    assert code == EXIT_IO
    assert "cannot be verified" in capsys.readouterr().err
