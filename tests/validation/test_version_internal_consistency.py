"""The version and DOI documents must agree with each other.

Why this exists: the P0 issue ISS-20261002-001 reported 12 version/DOI
inconsistencies, and the release-time check that guards them
(``scripts/validation/validate-version-sync.sh``) derives its baseline from the
latest git tag and the Zenodo/GitHub APIs.  That is why it is deliberately not a CI
gate (``docs/specs/validation-framework.md`` 6.1): on a branch older than the latest
tag it fails innocently, and when the network is unreachable the baseline comes back
empty and the check passes silently.

The consequence was measured here: ``metadata/datapackage.json`` declared
``version: 1.12.0`` while its ``doi`` field still held the v1.11.0 DOI
(10.5281/zenodo.23243495 against 10.5281/zenodo.23253840 everywhere else).  The
release-time script did not look at that field at all, so it reported PASS 12 /
FAIL 0.  It now checks the field, and this test covers the same ground with no
tags and no network, so CI can enforce it on every push.

The two checks are not duplicates: ``validate-version-sync.sh`` answers "does this
match the latest release?" (release-time, needs the outside world), and this one
answers "do these files contradict each other?" (any time, local only).
"""

import json
import re
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CITATION = REPO_ROOT / "CITATION.cff"
DATAPACKAGE = REPO_ROOT / "metadata/datapackage.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
README = REPO_ROOT / "README.md"


@pytest.fixture(scope="module")
def document() -> dict:
    citation = CITATION.read_text(encoding="utf-8")
    datapackage = json.loads(DATAPACKAGE.read_text(encoding="utf-8"))
    changelog = CHANGELOG.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    changelog_entry = re.search(r"^## \[([^\]]+)\](?: - (\S+))?", changelog, re.M)
    assert changelog_entry, "CHANGELOG has no version heading"

    def first(pattern: str, text: str, what: str) -> str:
        match = re.search(pattern, text, re.MULTILINE)
        assert match, f"could not read {what}"
        return match.group(1)

    citation_string = datapackage["citation"]
    return {
        "cversions": {
            "citation.version": first(r'^version:\s*"?([^"\n]+)"?', citation, "citation.version"),
            "citation.preferred-citation.version": first(
                r'preferred-citation:(?:.|\n)*?version:\s*"?([^"\n]+)"?',
                citation,
                "preferred-citation.version",
            ),
            "datapackage.version": datapackage["version"],
            "datapackage.citation.version": first(
                r"([0-9]+\.[0-9]+\.[0-9]+)", citation_string, "version in datapackage.citation"
            ),
            "CHANGELOG newest": changelog_entry.group(1),
        },
        "cdois": {
            "citation.identifiers.doi": first(
                r'identifiers:(?:.|\n)*?doi:\s*"?([^"\n]+)"?', citation, "identifiers.doi"
            ),
            "citation.preferred-citation.doi": first(
                r'preferred-citation:(?:.|\n)*?doi:\s*"?([^"\n]+)"?', citation, "preferred-citation.doi"
            ),
            "datapackage.doi": datapackage["doi"],
            "datapackage.citation.doi": first(
                r"(10\.5281/zenodo\.[0-9]+)", citation_string, "DOI in datapackage.citation"
            ),
            "README badge": first(
                r"https://doi\.org/(10\.5281/zenodo\.[0-9]+)", readme, "README badge DOI"
            ),
        },
        "changelog_date": changelog_entry.group(2),
        "modified": datapackage["modified"],
    }


def test_versions_agree(document: dict) -> None:
    values = set(document["cversions"].values())
    assert len(values) == 1, document["cversions"]


def test_dois_agree(document: dict) -> None:
    """Exact equality, not a prefix match: the badge loophole was a prefix check."""

    values = set(document["cdois"].values())
    assert len(values) == 1, document["cdois"]
    assert values.pop().startswith("10.5281/zenodo.")


def test_datapackage_is_not_older_than_the_newest_changelog_entry(document: dict) -> None:
    """Closes ISS-20261002-016 (datapackage modified date lagging the release)."""

    assert document["changelog_date"], "the newest CHANGELOG entry has no date"
    assert date.fromisoformat(document["modified"]) >= date.fromisoformat(
        document["changelog_date"]
    ), (document["modified"], document["changelog_date"])
