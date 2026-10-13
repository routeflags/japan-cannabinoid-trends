"""SQLite reader (d.md §13).

Opened strictly read-only: the connection uses the ``file:...?mode=ro`` URI
so a reader can never create, modify or vacuum a database.  Tables are
enumerated from ``sqlite_master``; a table name coming from a manifest is
checked against that enumeration before any query is built (the name is never
interpolated unchecked - d.md §10 S11).

The reader also exposes the conceptual ``record_lineage`` table (d.md §13)
when the database carries one; a database without lineage information is
reported, never assumed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)

__all__ = ["SqliteReader"]

SQLITE_MAGIC = b"SQLite format 3\x00"


class SqliteReader(StorageReader):
    reader_id = "sqlite-reader"
    reader_version = "1.0.0"
    formats = ("sqlite",)
    artifact_types = ("database",)
    read_modes = ("tables", "table_rows")

    #: Name of the conceptual lineage table (d.md §13).
    lineage_table = "record_lineage"

    def _connect(self, path: Path) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        except sqlite3.Error as error:
            raise ReaderError(f"SQLite database cannot be opened ({error})") from error
        connection.row_factory = None
        return connection

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            header = path.open("rb").read(len(SQLITE_MAGIC))
        except OSError as error:
            return [f"file cannot be read ({error.__class__.__name__})"]
        if header != SQLITE_MAGIC:
            return ["file is not a SQLite database (magic header mismatch)"]
        try:
            connection = self._connect(path)
        except ReaderError as error:
            return [str(error)]
        try:
            connection.execute("SELECT name FROM sqlite_master LIMIT 1")
        except sqlite3.Error as error:
            return [f"SQLite database is not readable ({error})"]
        finally:
            connection.close()
        return []

    def tables(self, artifact: ArtifactDescriptor) -> list[str]:
        """Read-only table enumeration (excluding SQLite internals)."""
        connection = self._connect(artifact.resolve())
        try:
            cursor = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as error:
            raise ReaderError(f"table enumeration failed ({error})") from error
        finally:
            connection.close()

    def read(
        self,
        artifact: ArtifactDescriptor,
        *,
        mode: str | None = None,
        limit: int | None = None,
        table: str | None = None,
    ):
        path = artifact.resolve()
        if mode in (None, "tables"):
            for index, name in enumerate(self.tables(artifact)):
                yield {"record_index": index, "table": name}
            return
        if mode == "table_rows":
            if not isinstance(table, str) or not table:
                raise ReaderError("read mode 'table_rows' requires a table name")
            if table not in self.tables(artifact):
                raise ReaderError(f"table is not present in the database: {table}")
            connection = self._connect(path)
            try:
                cursor = connection.execute(f'SELECT * FROM "{table}"')  # noqa: S608 - checked against sqlite_master
                columns = [description[0] for description in cursor.description]
                for index, row in enumerate(cursor):
                    if limit is not None and index >= limit:
                        break
                    yield {"record_index": index, "record": dict(zip(columns, row))}
            except sqlite3.Error as error:
                raise ReaderError(f"table read failed ({error})") from error
            finally:
                connection.close()
            return
        raise UnsupportedRead(
            f"{self.reader_id} does not implement read mode {mode!r}"
        )

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        # A database's record count belongs to a table; there is no single
        # file-level count (d.md §6.2).  Callers use read_table / table_rows.
        return None

    def table_row_count(self, artifact: ArtifactDescriptor, table: str) -> int | None:
        if table not in self.tables(artifact):
            return None
        connection = self._connect(artifact.resolve())
        try:
            cursor = connection.execute(f'SELECT COUNT(*) FROM "{table}"')  # noqa: S608
            return int(cursor.fetchone()[0])
        except sqlite3.Error:
            return None
        finally:
            connection.close()

    def lineage_summary(self, artifact: ArtifactDescriptor) -> dict:
        """Report the conceptual lineage table when present (d.md §13).

        Read-only: presence and row count only, no record values.
        """
        tables = self.tables(artifact)
        summary = {
            "lineage_table": self.lineage_table,
            "lineage_table_present": self.lineage_table in tables,
        }
        if summary["lineage_table_present"]:
            summary["lineage_row_count"] = self.table_row_count(
                artifact, self.lineage_table
            )
        return summary
