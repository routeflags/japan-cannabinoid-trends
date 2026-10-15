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
NO_DATA = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261002T064135Z-google-trends-nodata/records_nodata.json"
)
AVERAGES = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m/comparison_ja1.json"
)
AVERAGES_ALT_KEY = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261005T100000Z-google-trends-common-scale-expansion/comparison_setB.json"
)
AVERAGES_WITH_PEAK = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261008T125719Z-google-trends-common-scale-crdh/comparison.json"
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


def _validate_averages(path) -> list:
    reader = get_reader("json-averages-reader")
    return reader.validate(_descriptor(path, artifact_type="summary"))


def _validate_no_data(path) -> list:
    reader = get_reader("json-no-data-reader")
    return reader.validate(_descriptor(path, artifact_type="raw_response"))


def test_reader_ids_are_stable():
    assert reader_ids() == [
        "csv-record-reader",
        "json-averages-reader",
        "json-comparison-reader",
        "json-no-data-reader",
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


def test_averages_reader_reads_both_recorded_spellings():
    reader = get_reader("json-averages-reader")
    assert reader.contains_full_timeseries is False
    first = _descriptor(AVERAGES, artifact_type="summary")
    assert reader.validate(first) == []
    rows = list(reader.read(first, mode="averages"))
    assert [row["term"] for row in rows][:3] == ["CBX リキッド", "CBD リキッド", "THC リキッド"]
    assert rows[1]["average"] == 64
    assert reader.count(first) is None
    with pytest.raises(UnsupportedRead):
        list(reader.read(first, mode="points"))

    second = _descriptor(AVERAGES_ALT_KEY, artifact_type="summary")
    assert reader.validate(second) == []
    alt_rows = list(reader.read(second, mode="averages"))
    assert [(row["term"], row["average"]) for row in alt_rows] == [
        ("CBN", 55),
        ("CRDP", 2),
        ("HHCH", 0),
        ("THC-O", 0),
        ("THCV", 0),
    ]
    assert reader.count(second) is None


def test_averages_reader_tolerates_annotation_keys():
    reader = get_reader("json-averages-reader")
    descriptor = _descriptor(AVERAGES_WITH_PEAK, artifact_type="summary")
    assert reader.validate(descriptor) == []
    assert [(row["term"], row["average"]) for row in reader.read(descriptor)] == [
        ("CRDH", 0),
        ("CBD", 47),
        ("THC", 12),
    ]


def test_averages_reader_refuses_unattested_variants(tmp_path):
    both = tmp_path / "both.json"
    both.write_text(
        '{"terms": ["A"], "averages": {"A": 1}, "average_interest": {"A": 2}}',
        encoding="utf-8",
    )
    violations = _validate_averages(both)
    assert violations == ["expected exactly one of 'averages' / 'average_interest' objects"]

    series = tmp_path / "series.json"
    series.write_text(
        '{"terms": ["A"], "averages": {"A": 1}, '
        '"data": [{"date": "2026-01-04", "value": 1}]}',
        encoding="utf-8",
    )
    violations = _validate_averages(series)
    assert violations and "per-bucket" in violations[0]

    bad = tmp_path / "bad.json"
    bad.write_text('{"terms": ["A"], "averages": {"A": "high"}}', encoding="utf-8")
    violations = _validate_averages(bad)
    assert violations == ["average for term 'A' is not a number"]

    missing = tmp_path / "missing.json"
    missing.write_text('{"collected_at": "2026-10-05"}', encoding="utf-8")
    assert _validate_averages(missing) == ["expected a non-empty 'terms' string array"]


def test_no_data_reader_reads_the_recorded_no_data_response():
    reader = get_reader("json-no-data-reader")
    descriptor = _descriptor(NO_DATA, artifact_type="raw_response")
    assert reader.validate(descriptor) == []
    rows = list(reader.read(descriptor, mode="keywords"))
    assert [row["keyword"] for row in rows] == ["THCV", "THC-O"]
    assert all(row["status"] == "no_data" for row in rows)
    # Keyword entries record absence, not records: no record count exists
    # (d.md §6.2; a no-data response is never an observed zero).
    assert reader.count(descriptor) is None
    with pytest.raises(UnsupportedRead):
        list(reader.read(descriptor, mode="points"))


def test_no_data_reader_rejects_a_series_document(tmp_path):
    series = tmp_path / "series.json"
    series.write_text(
        '{"no_data_keywords": [{"keyword": "A", "status": "no_data"}], '
        '"data": [{"date": "2026-01-04", "value": 1}]}',
        encoding="utf-8",
    )
    violations = _validate_no_data(series)
    assert violations and "per-bucket" in violations[0]


def test_no_data_reader_rejects_malformed_entries(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        '{"no_data_keywords": [{"keyword": "", "status": "no_data"}]}',
        encoding="utf-8",
    )
    assert _validate_no_data(bad) == [
        "no_data_keywords[0] has no keyword label"
    ]
    missing = tmp_path / "missing.json"
    missing.write_text('{"collected_at": "2026-10-02"}', encoding="utf-8")
    assert _validate_no_data(missing) == [
        "expected a 'no_data_keywords' array"
    ]


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
