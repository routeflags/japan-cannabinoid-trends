"""JSON timeseries reader (bucket / value points).

Two recorded series shapes are covered by one reader because they are the
same contract (a per-bucket value series) with different field names:

- G1 payload shape ``{keyword, geo, timeframe, collected_at,
  data:[{date, value}]}`` (``google-trends-interest-over-time-v1``);
- earlier MCP shape ``{query, geo, ..., data:[{date, interest}]}``
  (``google-trends-records-v1``).

A summary document (declared ``data_points`` but no per-bucket values) is
*not* a timeseries here: this reader refuses it in ``validate`` and the
summary reader owns that shape (d.md §12 / P8: no reconstruction from
summary).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonTimeseriesReader", "VALUE_KEYS"]

#: Field names observed for the per-bucket number, in priority order.
VALUE_KEYS = ("value", "interest")


def _series(document):
    if isinstance(document, dict) and isinstance(document.get("data"), list):
        return document["data"]
    return None


def _point_value(point):
    for key in VALUE_KEYS:
        if isinstance(point.get(key), (int, float)) and not isinstance(point.get(key), bool):
            return key, point[key]
    return None, None


class JsonTimeseriesReader(StorageReader):
    reader_id = "json-timeseries-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("timeseries", "raw_response")
    read_modes = ("points",)
    contains_full_timeseries = True

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        data = _series(document)
        if data is None:
            return ["expected an object with a 'data' array of bucket values"]
        for index, point in enumerate(data):
            if not isinstance(point, dict):
                return [f"data[{index}] is not an object"]
            if not isinstance(point.get("date"), str):
                return [f"data[{index}] has no date label"]
            key, _ = _point_value(point)
            if key is None:
                return [
                    f"data[{index}] has no numeric value field "
                    f"({' / '.join(VALUE_KEYS)})"
                ]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "points"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}"
            )
        document = load_json(artifact.resolve())
        data = _series(document)
        if data is None:
            raise ReaderError("expected an object with a 'data' array")
        for index, point in enumerate(data):
            if limit is not None and index >= limit:
                break
            key, value = _point_value(point)
            yield {
                "record_index": index,
                "bucket": point.get("date"),
                "value": value,
                "value_field": key,
            }

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        try:
            data = _series(load_json(artifact.resolve()))
        except ReaderError:
            return None
        if data is None:
            return None
        return len(data)
