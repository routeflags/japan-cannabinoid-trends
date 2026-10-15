"""Content identification tests (d.md P3 / §16).

Real repository artifacts pin the recorded shapes; synthetic documents pin
the ambiguous/unknown paths (they must stay ambiguous - never forced into a
schema).
"""

from pathlib import Path

from storage.sniff import sniff_document, sniff_path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
R = REPO_ROOT / "datasets"

SERIES = R / "cannabinoid-multi-trends/data/raw/google_trends/20261012T064246Z-google-trends-ja-rikiddo-5y-main5/records_cbd-rikiddo-5y.json"
LEGACY_SERIES = R / "cbx-search-trends/data/raw/google_trends/20261001T115959Z-google-trends-cbx-rikiddo/records.json"
SUMMARY = R / "cannabinoid-multi-trends/data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/cbd_5y_summary.json"
COMPARISON = R / "cannabinoid-multi-trends/data/raw/google_trends/20261002T064236Z-google-trends-comparison-setA/comparison_setA.json"
RELATED = R / "cbx-search-trends/data/raw/google_trends/20261001T115959Z-google-trends-cbx-rikiddo/related_queries.json"
AVERAGES = R / "cannabinoid-multi-trends/data/raw/google_trends/20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m/comparison_ja1.json"
AVERAGES_ALT_KEY = R / "cannabinoid-multi-trends/data/raw/google_trends/20261005T100000Z-google-trends-common-scale-expansion/comparison_setB.json"
AVERAGES_WITH_PEAK = R / "cannabinoid-multi-trends/data/raw/google_trends/20261008T125719Z-google-trends-common-scale-crdh/comparison.json"


def test_recorded_full_timeseries_is_recognized():
    result = sniff_path(SERIES)
    assert (result.format, result.state) == ("json", "recognized")
    assert result.schema_id == "google-trends-interest-over-time-v1"
    assert result.contains_full_timeseries is True
    assert result.record_count == 262
    assert "series:date+value" in result.evidence


def test_legacy_interest_series_maps_to_its_own_schema():
    result = sniff_path(LEGACY_SERIES)
    assert result.schema_id == "google-trends-records-v1"
    assert result.contains_full_timeseries is True


def test_summary_is_never_a_full_timeseries():
    result = sniff_path(SUMMARY)
    assert result.artifact_type == "summary"
    assert result.contains_full_timeseries is False
    assert result.record_count is None  # a declared data_points is not a count
    assert result.declared_data_points == 261
    assert any("declared_data_points:261" in evidence for evidence in result.evidence)


def test_comparison_is_its_own_type():
    result = sniff_path(COMPARISON)
    assert result.schema_id == "google-trends-comparison-v1"
    assert result.artifact_type == "comparison"
    assert result.record_count == 53


def test_related_queries_response_is_recognized():
    result = sniff_path(RELATED)
    assert result.schema_id == "google-trends-related-queries-v1"
    assert result.artifact_type == "raw_response"


def test_no_data_response_is_recognized():
    result = sniff_path(
        R / "cannabinoid-multi-trends/data/raw/google_trends/20261002T064135Z-google-trends-nodata/records_nodata.json"
    )
    assert (result.format, result.state) == ("json", "recognized")
    assert result.schema_id == "google-trends-no-data-v1"
    assert result.artifact_type == "raw_response"
    assert "fields:no_data_keywords" in result.evidence


def test_empty_no_data_shape_is_still_the_no_data_shape():
    result = sniff_document({"collected_at": "2026-10-02", "no_data_keywords": []})
    assert result.state == "recognized"
    assert result.schema_id == "google-trends-no-data-v1"


def test_comparison_averages_are_recognized_in_both_recorded_spellings():
    for path in (AVERAGES, AVERAGES_ALT_KEY, AVERAGES_WITH_PEAK):
        result = sniff_path(path)
        assert (result.format, result.state) == ("json", "recognized")
        assert result.schema_id == "google-trends-comparison-averages-v1"
        assert result.artifact_type == "summary"
        assert result.contains_full_timeseries is False
        assert result.record_count is None  # averages are not a record count
        assert "comparison:averages_only" in result.evidence


def test_comparison_averages_variants_stay_partial():
    both_keys = sniff_document(
        {"terms": ["A", "B"], "averages": {"A": 1}, "average_interest": {"A": 2}}
    )
    assert both_keys.state == "partial"
    assert both_keys.schema_id is None

    with_data = sniff_document(
        {"terms": ["A"], "averages": {"A": 1}, "data": {"A": [1]}}
    )
    assert with_data.state == "partial"
    assert with_data.schema_id is None


def test_page_fixture_is_recognized():
    result = sniff_path(FIXTURES / "search_list_response.json")
    assert result.schema_id == "youtube-search-list-response-v1"
    assert result.record_count == 3


def test_checkpoint_fixture_is_recognized():
    result = sniff_path(FIXTURES / "checkpoint_state.json")
    assert result.schema_id == "collection-checkpoint-v1"
    assert result.artifact_type == "checkpoint"


def test_sqlite_is_detected_by_magic_bytes(tmp_path):
    import sqlite3

    path = tmp_path / "store.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY)")
    connection.commit()
    connection.close()
    result = sniff_path(path)
    assert result.format == "sqlite"
    assert result.schema_id == "sqlite-trends-db-v1"
    assert any(evidence.startswith("tables:") for evidence in result.evidence)


def test_ambiguous_documents_are_not_forced_into_a_schema():
    both = sniff_document(
        {"keyword": "A", "data": [{"date": "2026-01-04", "value": 1}], "data_points": 261}
    )
    assert both.state == "ambiguous"
    assert both.schema_id is None

    empty = sniff_document([])
    assert empty.state == "ambiguous"
    assert empty.record_count == 0

    mixed = sniff_document(
        {"keyword": "A", "data": [{"date": "2026-01-04", "value": 1, "interest": 2}]}
    )
    assert mixed.state == "ambiguous"


def test_partial_shapes_keep_their_evidence():
    error = sniff_document({"error": {"message": "rate limited"}})
    assert error.state == "partial"
    assert "fields:error" in error.evidence

    queries_batch = sniff_document({"queries": [{"term": "A"}], "collected_at": "2026-10-01"})
    assert queries_batch.state == "partial"
    assert "fields:queries" in queries_batch.evidence


def test_csv_and_text_and_binary(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    assert sniff_path(csv).format == "csv"
    text = tmp_path / "log.txt"
    text.write_text("hello\n", encoding="utf-8")
    assert sniff_path(text).format == "text"
    blob = tmp_path / "scan.pdf"
    blob.write_bytes(b"%PDF-1.7\x00\x01")
    result = sniff_path(blob)
    assert (result.format, result.state) == ("binary", "partial")
    assert "magic:pdf" in result.evidence


def test_empty_and_unreadable_files_are_unknown(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_bytes(b"")
    assert sniff_path(empty).state == "unknown"
    assert sniff_path(tmp_path / "ghost.json").state == "unknown"


def test_broken_json_is_reported_not_guessed(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    result = sniff_path(broken)
    assert result.format == "json"
    assert result.state == "unknown"
    assert "json_parse_error" in result.evidence
