"""JSON comparison-averages reader (averages-only aggregates).

A comparison-averages artifact records the per-term average interest of one
Google Trends comparison set (a single fetch group) without any per-bucket
time series.  Two key spellings are recorded in the repository
(``averages`` and ``average_interest``); both are proven shapes (ART-006) and
the reader accepts exactly one of them per document.  A document carrying
both spellings, or carrying per-bucket ``data`` values alongside the
averages, is a different (unattested) variant and is refused: averages must
never be answered as a full timeseries (d.md §12 / P8; AGENTS.md: missing
is not zero, aggregates are not records).

The reader therefore offers only ``averages`` (one row per term) and
refuses every series mode.  The average count is exposed through ``read``
only; ``count`` returns None (``record_count_mode: none``) so the averages
are never compared as a record count (d.md §6.2).
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonAveragesReader"]

#: The two recorded spellings of the per-term averages mapping.  Exactly one
#: must be present; both together is an unattested variant (never guessed).
AVERAGES_KEYS = ("averages", "average_interest")


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _mapping(document):
    """Return the per-term averages mapping, or None when not exactly one."""
    present = [key for key in AVERAGES_KEYS if isinstance(document.get(key), dict)]
    if len(present) != 1:
        return None
    return document[present[0]]


class JsonAveragesReader(StorageReader):
    reader_id = "json-averages-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("summary",)
    read_modes = ("averages",)
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
            return ["expected a JSON object with a per-term averages mapping"]
        terms = document.get("terms")
        if not isinstance(terms, list) or not terms or not all(
            isinstance(term, str) for term in terms
        ):
            return ["expected a non-empty 'terms' string array"]
        if "data" in document:
            return [
                "a comparison-averages artifact must not carry per-bucket data values "
                "(d.md §12); declare the artifact as a timeseries instead"
            ]
        mapping = _mapping(document)
        if mapping is None:
            return ["expected exactly one of 'averages' / 'average_interest' objects"]
        for term, value in mapping.items():
            if not _is_number(value):
                return [f"average for term {term!r} is not a number"]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "averages"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}; a "
                "comparison-averages artifact carries no per-bucket values (d.md §12 / P8)"
            )
        document = load_json(artifact.resolve())
        if not isinstance(document, dict):
            raise ReaderError("expected a JSON object")
        mapping = _mapping(document)
        if mapping is None:
            raise ReaderError("expected exactly one of 'averages' / 'average_interest' objects")
        for index, (term, value) in enumerate(mapping.items()):
            if limit is not None and index >= limit:
                break
            if not _is_number(value):
                raise ReaderError(f"average for term {term!r} is not a number")
            yield {
                "record_index": index,
                "term": term,
                "average": value,
            }

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        # Never: per-term averages are aggregate claims, not records (d.md §6.2;
        # AGENTS.md missing-data vocabulary).  Callers read the averages.
        return None
