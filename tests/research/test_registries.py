"""G7 registry tests (study / measurement registries, G7-T01/T02/T04).

Contract sources: g.md \u00a74 (study registry), \u00a76 (measurement
registry), \u00a717 test requirements.
"""

import json
from copy import deepcopy
from pathlib import Path

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.semantic import (
    Registries,
    check_measurement_registry,
    check_registry_references,
    check_study_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_REGISTRY = REPO_ROOT / "metadata" / "studies" / "study-registry.json"
MEASUREMENT_REGISTRY = REPO_ROOT / "metadata" / "measurements" / "measurement-registry.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


# ---------------------------------------------------------------------------
# Checked-in registries (9-study inventory, P1/P7: the 2-study vertical slice
# plus the 2026-10-13 G7 increment registering the remaining 7 studies)
# ---------------------------------------------------------------------------

def test_study_registry_file_is_structurally_valid():
    document = _load(STUDY_REGISTRY)
    result = validate_document(document, get_schema("study-registry-v1"))
    assert result.valid, result.errors
    assert check_study_registry(document) == []


def test_study_registry_covers_exactly_the_nine_studies():
    document = _load(STUDY_REGISTRY)
    assert [s["study_id"] for s in document["studies"]] == [
        "cbx-search-trends",
        "cannabinoid-multi-trends",
        "cannabinoid-social-trends",
        "cbx-liquid-online-trend",
        "cbx-product-coa",
        "cbx-social-trends",
        "x-26week-trends",
        "x-consistency",
        "youtube-consistency",
    ]


def test_study_registry_questions_come_from_readmes():
    """Research questions match the study READMEs verbatim (no invention).

    Studies without an explicit ``研究質問`` blockquote quote their README
    purpose statement verbatim instead (G7 increment 2026-10-13); the test
    only enforces verbatim presence, never authorship."""
    document = _load(STUDY_REGISTRY)
    by_id = {s["study_id"]: s for s in document["studies"]}
    for study_id in by_id:
        readme = (REPO_ROOT / "datasets" / study_id / "README.md").read_text(encoding="utf-8")
        for question in by_id[study_id]["research_questions"]:
            assert question in readme, f"question not found verbatim in {study_id} README"


def test_measurement_registry_file_is_structurally_valid():
    document = _load(MEASUREMENT_REGISTRY)
    result = validate_document(document, get_schema("measurement-registry-v1"))
    assert result.valid, result.errors
    assert check_measurement_registry(document) == []


def test_measurement_registry_declares_native_units_without_normalization():
    """P6: units stay source-native; no cross-unit conversion is declared."""
    document = _load(MEASUREMENT_REGISTRY)
    by_id = {m["measurement_id"]: m for m in document["measurements"]}
    assert by_id["search_interest_index"]["unit"] == "relative_index_0_100"
    assert by_id["social_post_count"]["unit"] == "posts"
    assert by_id["video_publication_count"]["unit"] == "videos"


# ---------------------------------------------------------------------------
# G7-T01 / T02 / T04 contract behaviour
# ---------------------------------------------------------------------------

def test_g7_t01_duplicate_study_id_fails():
    document = _load(STUDY_REGISTRY)
    doubled = deepcopy(document)
    doubled["studies"].append(deepcopy(document["studies"][0]))
    assert "STUDY_DUPLICATE_ID" in _codes(check_study_registry(doubled))


def test_g7_t02_unregistered_study_reference_fails():
    registries = Registries.from_documents(study_registry=_load(STUDY_REGISTRY))
    assert "REFERENCE_STUDY_UNREGISTERED" in _codes(
        check_registry_references({"study_id": "does-not-exist"}, registries)
    )


def test_registered_slice_studies_pass_reference_check():
    registries = Registries.from_documents(study_registry=_load(STUDY_REGISTRY))
    for study_id in (
        "cbx-search-trends",
        "cannabinoid-multi-trends",
        "cannabinoid-social-trends",
        "cbx-liquid-online-trend",
        "cbx-product-coa",
        "cbx-social-trends",
        "x-26week-trends",
        "x-consistency",
        "youtube-consistency",
    ):
        issues = check_registry_references({"study_id": study_id}, registries)
        assert "REFERENCE_STUDY_UNREGISTERED" not in _codes(issues)


def test_duplicate_measurement_id_fails():
    document = _load(MEASUREMENT_REGISTRY)
    doubled = deepcopy(document)
    doubled["measurements"].append(deepcopy(document["measurements"][0]))
    assert "MEASUREMENT_DUPLICATE_ID" in _codes(check_measurement_registry(doubled))


def test_g7_t04_catalog_measurements_are_all_registered():
    """Every measurement_id the catalog emits resolves in the registry."""
    from research.catalog import build_catalog

    catalog = build_catalog(REPO_ROOT / "datasets", repo_root=REPO_ROOT)
    registered = {m["measurement_id"] for m in _load(MEASUREMENT_REGISTRY)["measurements"]}
    for entry in catalog["entries"]:
        assert entry["measurement_id"] in registered or entry["measurement_id"] is None
