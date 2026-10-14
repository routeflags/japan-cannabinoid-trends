"""Reader code registry: ``reader_id`` -> implementation (d.md §7 / §8).

The artifact registry file (``metadata/artifacts/artifact-registry.json``)
may only reference readers implemented here.  ``validation.storage_contract
.check_artifact_registry`` verifies the correspondence, so a registry entry
can never claim a reader that does not exist (fail closed).

Adding a new storage format means: (1) implement a ``StorageReader`` in this
package, (2) register it in ``READER_CLASSES``, (3) add reader / schema
entries to the artifact registry, (4) add contract tests (d.md §7 / §17
G4-T17).
"""

from __future__ import annotations

from storage.contracts import StorageReader
from storage.readers.comparison import JsonComparisonReader
from storage.readers.csv import CsvRecordReader
from storage.readers.objects import JsonObjectReader
from storage.readers.pages import JsonPageReader
from storage.readers.records import JsonRecordReader
from storage.readers.sqlite import SqliteReader
from storage.readers.summary import JsonSummaryReader
from storage.readers.timeseries import JsonTimeseriesReader

__all__ = ["READER_CLASSES", "get_reader", "reader_ids"]

#: Every implemented reader, keyed by reader_id.  Order is irrelevant.
READER_CLASSES: tuple[type[StorageReader], ...] = (
    JsonRecordReader,
    JsonPageReader,
    JsonTimeseriesReader,
    JsonSummaryReader,
    JsonComparisonReader,
    JsonObjectReader,
    SqliteReader,
    CsvRecordReader,
)

_BY_ID = {cls.reader_id: cls for cls in READER_CLASSES}


def get_reader(reader_id: str) -> StorageReader | None:
    """Return a fresh reader instance for ``reader_id`` or None."""
    reader_class = _BY_ID.get(reader_id)
    if reader_class is None:
        return None
    return reader_class()


def reader_ids() -> list[str]:
    """Every implemented reader id, sorted (stable for reports/tests)."""
    return sorted(_BY_ID)
