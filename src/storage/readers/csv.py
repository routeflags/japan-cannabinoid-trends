"""CSV record reader - one header record followed by data records.

A dataset export (``.csv``) is a header record naming the columns, followed
by one record per collected item.  Quoted fields may contain the field
separator, doubled quotes and embedded newlines, so the file is read with
``newline=""`` and the record count is the number of **CSV records** - it is
decidedly *not* the number of physical lines (observed exports carry roughly
55 physical lines per record because their long text fields are quoted
multi-line values).

Fixed semantics (contract tests pin each one):

- the file is UTF-8, optionally with a BOM; it is never repaired;
- one header record is required; an empty file, a file without a header or a
  header with empty / duplicate column names is refused (a record mapping
  cannot represent those names honestly);
- blank physical lines between records are not records (RFC 4180 parsers
  return an empty row for them);
- every data record must have exactly as many fields as the header - a
  ragged record is refused rather than padded or truncated (it is also the
  strongest malformed-quoting signal available, because the ``csv`` module
  is lenient about unclosed quotes);
- ``count`` is the number of data records (an observed zero is expressible:
  a header-only file counts 0);
- ``read(mode="records")`` yields ``{"record_index": int, "record": {column:
  value}}``; unknown modes raise ``UnsupportedRead``.

Everything is read-only: the file is opened for reading and never rewritten
(storage contract, d.md §8).
"""

from __future__ import annotations

import csv
from pathlib import Path

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)

__all__ = ["CsvRecordReader"]


class CsvRecordReader(StorageReader):
    """Reader for delimited text exports under one header record."""

    reader_id = "csv-record-reader"
    reader_version = "1.0.0"
    formats = ("csv",)
    artifact_types = ("raw_records",)
    read_modes = ("records",)

    # -- internals ---------------------------------------------------------

    def _open(self, path: Path):
        try:
            return path.open("r", encoding="utf-8-sig", newline="")
        except OSError as error:
            raise ReaderError(
                f"CSV file cannot be opened ({error.__class__.__name__})"
            ) from error

    def _read_header(self, reader: csv.reader) -> list[str]:
        try:
            header = next(reader)
        except StopIteration:
            raise ReaderError("CSV file has no header record") from None
        except (csv.Error, UnicodeDecodeError, OSError) as error:
            raise ReaderError(
                f"CSV file cannot be read ({error.__class__.__name__})"
            ) from error
        if not header or any(name == "" for name in header):
            raise ReaderError("CSV header record has empty column names")
        if len(set(header)) != len(header):
            raise ReaderError(
                "CSV header has duplicate column names; a record mapping "
                "cannot represent them"
            )
        return header

    def _iter_records(self, path: Path):
        """Yield ``(record_index, header, values)`` for every data record."""
        with self._open(path) as handle:
            reader = csv.reader(handle)
            header = self._read_header(reader)
            index = 0
            try:
                for values in reader:
                    if not values:
                        # A blank physical line is not a record; the fields
                        # of a real record are never returned as [] .
                        continue
                    if len(values) != len(header):
                        raise ReaderError(
                            f"CSV record {index + 1} has {len(values)} fields; "
                            f"the header declares {len(header)}"
                        )
                    yield index, header, values
                    index += 1
            except csv.Error as error:
                raise ReaderError(f"CSV parse error: {error}") from error
            except (UnicodeDecodeError, OSError) as error:
                raise ReaderError(
                    f"CSV file cannot be read ({error.__class__.__name__})"
                ) from error

    # -- StorageReader contract -------------------------------------------

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            for _ in self._iter_records(path):
                pass
        except ReaderError as error:
            return [str(error)]
        return []

    def read(
        self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None
    ):
        if mode not in (None, "records"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}"
            )
        for index, header, values in self._iter_records(artifact.resolve()):
            if limit is not None and index >= limit:
                break
            yield {"record_index": index, "record": dict(zip(header, values))}

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        try:
            return sum(1 for _ in self._iter_records(artifact.resolve()))
        except ReaderError:
            return None
