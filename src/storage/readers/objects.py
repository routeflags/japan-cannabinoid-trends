"""JSON object reader (raw responses, checkpoints).

Some stored artifacts are single JSON objects whose meaning is recorded in
the manifest (e.g. ``raw_response``, ``checkpoint``).  The reader exposes the
document as one record and implements no series mode - reading a checkpoint
as a dataset is a caller error, not a guess.
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonObjectReader"]


class JsonObjectReader(StorageReader):
    reader_id = "json-object-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("raw_response", "checkpoint")
    read_modes = ("object",)

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        if not isinstance(document, dict):
            return ["expected a JSON object"]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "object"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}"
            )
        if limit is not None and limit <= 0:
            return
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        yield {"record_index": 0, "record": document}
