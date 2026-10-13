"""JSON array record reader - the d.md §9 reference reader shape.

Yields ``{"record_index": int, "record": <item>}`` for every element of a
top-level JSON array.  A JSON object, a JSONL stream or a paginated wrapper
is a different format and belongs to another reader (d.md §9).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonRecordReader"]


class JsonRecordReader(StorageReader):
    reader_id = "json-record-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("raw_records", "normalized_records", "aggregate")
    read_modes = ("records",)

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        if not isinstance(document, list):
            return ["expected a JSON array (d.md §9)"]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "records"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, list):
            raise ReaderError("expected a JSON array")
        for index, record in enumerate(document):
            if limit is not None and index >= limit:
                break
            yield {"record_index": index, "record": record}

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        try:
            document = load_json(artifact.resolve())
        except ReaderError:
            return None
        if isinstance(document, list):
            return len(document)
        return None
