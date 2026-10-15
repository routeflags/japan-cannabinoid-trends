"""Catalog layout tests: COL-018(a) source hierarchy (G1 \u00a73)."""

from pathlib import Path

from collection.core.pipeline import _catalog_dir, _source_slug


def test_source_slug_normalizes_registry_source_id():
    assert _source_slug("google-trends") == "google_trends"
    assert _source_slug("google_trends") == "google_trends"
    assert _source_slug("YouTube-Apify-Scraper") == "youtube_apify_scraper"


def test_source_slug_falls_back_to_unknown():
    assert _source_slug(None) == "unknown"
    assert _source_slug("") == "unknown"


def test_catalog_dir_places_run_under_source(tmp_path):
    assert _catalog_dir(tmp_path, "cbx-search-trends", "run-1", "google-trends") == (
        Path(tmp_path)
        / "cbx-search-trends"
        / "data"
        / "raw"
        / "google_trends"
        / "run-1"
    )


def test_catalog_dir_without_source_uses_unknown(tmp_path):
    target = _catalog_dir(tmp_path, "cbx-search-trends", "run-1", None)
    assert target.parent.name == "unknown"
