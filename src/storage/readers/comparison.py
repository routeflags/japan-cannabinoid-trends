"""JSON comparison reader (multi-term common-scale tables).

A comparison artifact stores one row per bucket with a column per term
(relative common scale).  It is a different artifact type from a single-term
timeseries: the values are relative *within the comparison set* and must not
be merged into one series (d.md §1 / §12; the `note` field in the recorded
files says the same).  The reader therefore only offers ``comparison_rows``.
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonComparisonReader"]


class JsonComparisonReader(StorageReader):
    reader_id = "json-comparison-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("comparison",)
    read_modes = ("comparison_rows",)
    contains_full_timeseries = True

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
        terms = document.get("terms")
        if not isinstance(terms, list) or not terms:
            return ["expected a non-empty 'terms' list"]
        data = document.get("data")
        if not isinstance(data, list):
            return ["expected a 'data' array of comparison rows"]
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                return [f"data[{index}] is not an object"]
            if not isinstance(row.get("date"), str):
                return [f"data[{index}] has no date label"]
            if not any(isinstance(row.get(term), (int, float)) for term in terms):
                return [f"data[{index}] has no numeric term values"]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "comparison_rows"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}; a "
                "comparison table is never returned as a single series"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, dict) or not isinstance(document.get("data"), list):
            raise ReaderError("expected a comparison document")
        terms = [term for term in document.get("terms", []) if isinstance(term, str)]
        for index, row in enumerate(document["data"]):
            if limit is not None and index >= limit:
                break
            yield {
                "record_index": index,
                "bucket": row.get("date"),
                "values": {term: row.get(term) for term in terms},
            }

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        try:
            document = load_json(artifact.resolve())
        except ReaderError:
            return None
        if isinstance(document, dict) and isinstance(document.get("data"), list):
            return len(document["data"])
        return None
