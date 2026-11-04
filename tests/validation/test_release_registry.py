"""The release registry must record the DOI Zenodo minted for each version.

The concept DOI follows the series; the version DOI pins one upload.  Mixing
them up silently points a citation at whatever is latest, so the two are
checked apart, together with the tag / CHANGELOG / declared-version agreement.
"""

import json
from pathlib import Path

import pytest

from validation.release_registry import check_release_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CONCEPT = "10.5281/zenodo.23390594"
VERSION_DOI = "10.5281/zenodo.23961844"


def _registry(**overrides) -> dict:
    document = {
        "schema_version": "1.0.0",
        "record": "release_registry",
        "concept_doi": CONCEPT,
        "releases": [
            {
                "version": "1.14.3",
                "tag": "v1.14.3",
                "version_doi": VERSION_DOI,
                "released_at": "2026-11-04T19:33:01Z",
            }
        ],
    }
    document.update(overrides)
    return document


def _check(document, *, version="1.14.4", changelog=("1.14.3", "1.14.4")):
    return check_release_registry(
        document,
        citation_version=version,
        datapackage_version=version,
        declared_concept_doi=CONCEPT,
        changelog_versions=set(changelog),
    )


def _codes(issues) -> list[str]:
    return [issue["code"] for issue in issues]


def test_a_consistent_registry_has_no_issues():
    assert _check(_registry()) == []


def test_a_version_doi_may_not_be_the_concept_doi():
    document = _registry()
    document["releases"][0]["version_doi"] = CONCEPT

    assert "RELEASE_VERSION_DOI_IS_CONCEPT" in _codes(_check(document))


def test_the_tag_must_name_the_version():
    document = _registry()
    document["releases"][0]["tag"] = "v1.14.4"

    assert "RELEASE_TAG_MISMATCH" in _codes(_check(document))


def test_every_release_needs_a_changelog_entry():
    assert "RELEASE_NOT_IN_CHANGELOG" in _codes(_check(_registry(), changelog=("1.14.4",)))


def test_the_declared_version_may_not_be_older_than_the_newest_release():
    assert "RELEASE_AHEAD_OF_DECLARATION" in _codes(_check(_registry(), version="1.14.2"))


def test_preparing_the_next_release_is_a_normal_state():
    """CITATION ahead of the newest entry means "not released yet"."""

    assert _check(_registry(), version="1.14.9") == []


def test_the_concept_doi_must_match_the_dataset_declaration():
    document = _registry(concept_doi="10.5281/zenodo.11111111")

    assert "RELEASE_CONCEPT_DOI_DISAGREES" in _codes(_check(document))


def test_a_malformed_doi_is_a_structural_failure():
    document = _registry()
    document["releases"][0]["version_doi"] = "zenodo-123"

    assert "RELEASE_REGISTRY_INVALID" in _codes(_check(document))


def test_versions_are_unique_and_ordered():
    document = _registry()
    document["releases"] = [
        {"version": "1.14.3", "tag": "v1.14.3", "version_doi": VERSION_DOI, "released_at": "2026-11-04T19:33:01Z"},
        {"version": "1.14.2", "tag": "v1.14.2", "version_doi": "10.5281/zenodo.23961329", "released_at": "2026-11-04T19:16:00Z"},
    ]

    assert "RELEASE_ORDER_INVALID" in _codes(_check(document))


def test_the_committed_registry_is_consistent():
    document = json.loads((REPO_ROOT / "metadata" / "releases.json").read_text(encoding="utf-8"))
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    version = citation.split('version: "', 1)[1].split('"', 1)[0]
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    import re

    versions = set(re.findall(r"^## \[([^\]]+)\]", changelog, re.M))

    issues = check_release_registry(
        document,
        citation_version=version,
        datapackage_version=json.loads(
            (REPO_ROOT / "metadata" / "datapackage.json").read_text(encoding="utf-8")
        )["version"],
        declared_concept_doi=CONCEPT,
        changelog_versions=versions,
    )

    assert issues == []
