"""Reader contract tests (d.md §8 / §9 / §12).

Real repository artifacts are read where possible (read-only) so the reader
contract is exercised against the recorded storage shapes, not only fixtures.
The synthetic fixtures under ``tests/storage/fixtures`` are invented shapes
for formats whose recorded files are local-only (pages, checkpoints).
"""

import hashlib
from pathlib import Path

import pytest

from storage.contracts import ArtifactDescriptor, ReaderError, UnsupportedRead
from storage.readers import get_reader, reader_ids

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"

SERIES = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261012T064246Z-google-trends-ja-rikiddo-5y-main5/records_cbd-rikiddo-5y.json"
)
SUMMARY = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261008T093228Z-google-trends-5y-baseline/cbd_5y_summary.json"
)
COMPARISON = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261002T064236Z-google-trends-comparison-setA/comparison_setA.json"
)
RELATED_QUERIES = (
    REPO_ROOT
    / "datasets/cbx-search-trends/data/raw/google_trends"
    / "20261001T115959Z-google-trends-cbx-rikiddo/related_queries.json"
)


def _descriptor(path, **overrides) -> ArtifactDescriptor:
    values = {
        "artifact_id": "test-artifact",
        "artifact_type": None,
        "format": "json",
        "schema_id": None,
        "path": str(path),
    }
    values.update(overrides)
    return ArtifactDescriptor(**values)


def test_reader_ids_are_stable():
    assert reader_ids() == [
        "csv-record-reader",
        "json-comparison-reader",
        "json-object-reader",
        "json-page-reader",
        "json-record-reader",
        "json-summary-reader",
        "json-timeseries-reader",
        "sqlite-reader",
    ]


def test_timeseries_reader_reads_the_recorded_series():
    reader = get_reader("json-timeseries-reader")
    descriptor = _descriptor(SERIES, artifact_type="timeseries")
    assert reader.validate(descriptor) == []
    points = list(reader.read(descriptor, mode="points", limit=5))
    assert [point["bucket"] for point in points][:3] == ["2021-10-10", "2021-10-17", "2021-10-24"]
    assert all(point["value_field"] == "value" for point in points)
    assert reader.count(descriptor) == 262


def test_summary_reader_stays_a_summary():
    reader = get_reader("json-summary-reader")
    descriptor = _descriptor(SUMMARY, artifact_type="summary")
    assert reader.validate(descriptor) == []
    records = list(reader.read(descriptor, mode="summary_fields"))
    assert len(records) == 1
    assert records[0]["record"]["data_points"] == 261
    # A declared data_points is not a record count, and the summary is never
    # answered as a full timeseries (d.md §12 / P8).
    assert reader.count(descriptor) is None
    with pytest.raises(UnsupportedRead):
        list(reader.read(descriptor, mode="points"))


def test_summary_reader_rejects_a_series_document(tmp_path):
    series = tmp_path / "series.json"
    series.write_text('{"keyword": "A", "data": [{"date": "2026-01-04", "value": 1}]}', encoding="utf-8")
    reader = get_reader("json-summary-reader")
    violations = reader.validate(_descriptor(series, artifact_type="summary"))
    assert violations and "per-bucket" in violations[0]


def test_timeseries_reader_rejects_a_summary_document(tmp_path):
    summary = tmp_path / "summary.json"
    summary.write_text('{"compound": "A", "data_points": 261}', encoding="utf-8")
    reader = get_reader("json-timeseries-reader")
    violations = reader.validate(_descriptor(summary, artifact_type="timeseries"))
    assert violations and "data" in violations[0]


def test_comparison_reader_returns_rows_not_a_merged_series():
    reader = get_reader("json-comparison-reader")
    descriptor = _descriptor(COMPARISON, artifact_type="comparison")
    assert reader.validate(descriptor) == []
    rows = list(reader.read(descriptor, mode="comparison_rows", limit=2))
    assert set(rows[0]["values"]) == {"CBD", "THC", "CBG", "HHC", "THCH"}
    with pytest.raises(UnsupportedRead):
        list(reader.read(descriptor, mode="points"))
    assert reader.count(descriptor) == 53


def test_record_reader_requires_an_array(tmp_path):
    reader = get_reader("json-record-reader")
    good = FIXTURES / "search_result_list.json"
    descriptor = _descriptor(good, artifact_type="raw_records")
    assert reader.validate(descriptor) == []
    assert reader.count(descriptor) == 2
    assert [item["record_index"] for item in reader.read(descriptor, limit=1)] == [0]

    bad = tmp_path / "object.json"
    bad.write_text('{"not": "an array"}', encoding="utf-8")
    violations = reader.validate(_descriptor(bad, artifact_type="raw_records"))
    assert violations == ["expected a JSON array (d.md §9)"]


def test_page_reader_accepts_wrapped_and_plain_pages():
    reader = get_reader("json-page-reader")
    wrapped = FIXTURES / "search_list_response.json"
    descriptor = _descriptor(wrapped, artifact_type="page")
    assert reader.validate(descriptor) == []
    assert reader.count(descriptor) == 3
    assert reader.meta(descriptor) == {
        "items_key": "items",
        "total_results": 3,
        "results_per_page": 3,
    }

    plain = FIXTURES / "search_result_list.json"
    assert reader.validate(_descriptor(plain, artifact_type="page")) == []


def test_object_reader_reads_checkpoint_state():
    reader = get_reader("json-object-reader")
    descriptor = _descriptor(
        FIXTURES / "checkpoint_state.json", artifact_type="checkpoint"
    )
    assert reader.validate(descriptor) == []
    records = list(reader.read(descriptor))
    assert records[0]["record"]["status"] == "completed"
    with pytest.raises(UnsupportedRead):
        list(reader.read(descriptor, mode="records"))


def test_object_reader_reads_related_queries_response():
    reader = get_reader("json-object-reader")
    descriptor = _descriptor(RELATED_QUERIES, artifact_type="raw_response")
    assert reader.validate(descriptor) == []
    assert list(reader.read(descriptor))[0]["record"]["result"].startswith(
        "No related queries"
    )


def test_readers_never_modify_the_file():
    before = hashlib.sha256(SERIES.read_bytes()).hexdigest()
    reader = get_reader("json-timeseries-reader")
    descriptor = _descriptor(SERIES, artifact_type="timeseries")
    list(reader.read(descriptor))
    reader.count(descriptor)
    reader.validate(descriptor)
    assert hashlib.sha256(SERIES.read_bytes()).hexdigest() == before


def test_missing_file_is_reported_not_crashed(tmp_path):
    reader = get_reader("json-record-reader")
    violations = reader.validate(_descriptor(tmp_path / "ghost.json"))
    assert violations == ["file does not exist"]
    with pytest.raises(ReaderError):
        list(reader.read(_descriptor(tmp_path / "ghost.json")))
