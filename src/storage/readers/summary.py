"""JSON summary reader (aggregate-only artifacts).

The contract exists to keep a summary *a summary*: it exposes the recorded
fields and refuses every other read mode.  A summary that declares
``data_points: 261`` carries no weekly values, so it must never answer a
``points`` request (d.md §12 / P8).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonSummaryReader"]


class JsonSummaryReader(StorageReader):
    reader_id = "json-summary-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("summary",)
    read_modes = ("summary_fields",)
    contains_full_timeseries = False

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        if not isinstance(document, dict):
            return ["expected a JSON object with aggregate summary fields"]
        data = document.get("data")
        if isinstance(data, list) and data:
            return [
                "a summary artifact must not carry per-bucket data values "
                "(d.md §12); declare the artifact as a timeseries instead"
            ]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "summary_fields"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}; a "
                "summary carries no per-bucket values (d.md §12 / P8)"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        yield {"record_index": 0, "record": document}

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        # Never: a declared ``data_points`` is an aggregate claim, not a
        # record count (d.md §6.2); a summary has no per-record array.
        return None
