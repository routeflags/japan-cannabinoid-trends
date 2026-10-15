"""JSON no-data reader (platform no-data responses).

A no-data response records that the platform returned no series for the
listed keywords (below-threshold volume, not a zero series).  It is a
different artifact from a timeseries and from a summary: there are no
per-bucket values to read, and the keyword entries are evidence of absence,
not records (d.md §12 / P8; AGENTS.md: missing is not zero).

The reader therefore offers only ``keywords`` (one row per
``no_data_keywords`` entry) and refuses every series mode.  A document that
carries per-bucket ``data`` values is refused in ``validate``: such a
response is not a no-data response, and claiming it as one would conflate
absence with values.  The keyword count is exposed through ``read`` only;
``count`` returns None (``record_count_mode: none``) so the entries are
never compared as a record count (d.md §6.2).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonNoDataReader"]


def _keywords(document):
    entries = document.get("no_data_keywords")
    if isinstance(entries, list):
        return entries
    return None


class JsonNoDataReader(StorageReader):
    reader_id = "json-no-data-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("raw_response",)
    read_modes = ("keywords",)

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        if not isinstance(document, dict):
            return ["expected a JSON object with a 'no_data_keywords' array"]
        entries = _keywords(document)
        if entries is None:
            return ["expected a 'no_data_keywords' array"]
        data = document.get("data")
        if isinstance(data, list) and data:
            return [
                "a no-data response must not carry per-bucket data values "
                "(d.md §12); declare the artifact as a timeseries instead"
            ]
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                return [f"no_data_keywords[{index}] is not an object"]
            keyword = entry.get("keyword")
            if not isinstance(keyword, str) or not keyword:
                return [f"no_data_keywords[{index}] has no keyword label"]
            status = entry.get("status")
            if not isinstance(status, str) or not status:
                return [f"no_data_keywords[{index}] has no status label"]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "keywords"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}; a "
                "no-data response carries no per-bucket values (d.md §12 / P8)"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        entries = _keywords(document)
        if entries is None:
            raise ReaderError("expected a 'no_data_keywords' array")
        for index, entry in enumerate(entries):
            if limit is not None and index >= limit:
                break
            if not isinstance(entry, dict):
                raise ReaderError(f"no_data_keywords[{index}] is not an object")
            yield {
                "record_index": index,
                "keyword": entry.get("keyword"),
                "status": entry.get("status"),
                "note": entry.get("note"),
            }

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        # Never: the keyword entries record absence, not records (d.md §6.2;
        # AGENTS.md missing-data vocabulary).  Callers read the keywords.
        return None
