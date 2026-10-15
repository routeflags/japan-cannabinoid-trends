"""JSON query-batch reader for legacy Google Trends response batches.

The recorded legacy shapes covered here are structural batches of query-level
Google Trends results, not full time series:

* ``queries`` as a list of per-query objects (for example related-query probes);
* ``queries`` as a list of query strings with a same-keyed ``data`` object
  containing aggregate/partial findings.

Both shapes are raw responses whose meaning is one row per submitted query.  A
``data`` list would be a different, potentially per-bucket series shape and is
refused rather than guessed (d.md §12 / P8).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonQueryBatchReader"]


def _query_rows(document: dict) -> list[dict]:
    queries = document.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ReaderError("expected a non-empty 'queries' array")
    if all(isinstance(item, dict) for item in queries):
        return [dict(item) for item in queries]
    if all(isinstance(item, str) for item in queries):
        data = document.get("data")
        if data is not None and not isinstance(data, dict):
            raise ReaderError("'data' must be an object when queries are strings")
        rows: list[dict] = []
        for term in queries:
            row = {"query": term}
            if isinstance(data, dict) and term in data:
                row["result"] = data[term]
            rows.append(row)
        return rows
    raise ReaderError("'queries' must contain either all objects or all strings")


class JsonQueryBatchReader(StorageReader):
    reader_id = "json-query-batch-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("raw_response",)
    read_modes = ("queries",)
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
            return ["expected a JSON object with a 'queries' array"]
        if isinstance(document.get("data"), list):
            return [
                "query-batch artifacts must not carry per-bucket data arrays "
                "(d.md §12); declare the artifact as a timeseries instead"
            ]
        try:
            _query_rows(document)
        except ReaderError as error:
            return [str(error)]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "queries"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}; a "
                "query batch is not a full time series (d.md §12 / P8)"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        for index, row in enumerate(_query_rows(document)):
            if limit is not None and index >= limit:
                break
            yield {"record_index": index, "record": row}

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        return len(_query_rows(document))
