"""No tracked JSON document may contain a duplicate key.

Contract source: AGENTS.md (technical standards; the SKOS taxonomies are
controlled vocabulary).  The rule and why it exists are documented in
``validation/json_hygiene.py``.

The decisive test is :func:`test_repository_has_no_duplicate_keys`: two taxonomy
files declared English labels that never reached the published exports, and no
parser complained.
"""

import json
import subprocess
from pathlib import Path

import pytest

from validation.json_hygiene import find_duplicate_keys, scan_json_text

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_KEYS = (
    "skos:prefLabel",
    "skos:scopeNote",
    "skos:exactMatch",
    "dct:title",
)


@pytest.fixture(scope="module")
def tracked_json_files() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "*.json", "*.jsonld"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in listed.stdout.splitlines() if line]


def test_repository_has_no_duplicate_keys(tracked_json_files: list[str]) -> None:
    assert len(tracked_json_files) >= 100, "the scan surface shrank unexpectedly"
    offenders = {
        path: find_duplicate_keys(REPO_ROOT / path) for path in tracked_json_files
    }
    offenders = {path: found for path, found in offenders.items() if found}
    assert offenders == {}, (
        "duplicate keys silently discard data; put multi-valued literals in an "
        f"array: {offenders}"
    )


def test_the_keys_that_were_lost_are_now_arrays() -> None:
    """The four keys that were duplicated must hold every value, not the last."""

    for path in (
        "metadata/taxonomy/compound-taxonomy.skos.jsonld",
        "metadata/taxonomy/content-taxonomy.skos.jsonld",
    ):
        document = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        for node in document["@graph"]:
            for key in REQUIRED_KEYS:
                if key not in node:
                    continue
                values = node[key] if isinstance(node[key], list) else [node[key]]
                assert all(value not in (None, "") for value in values), (path, key)


def test_every_concept_carries_both_languages() -> None:
    """English was the language that disappeared, so it is asserted directly."""

    for path in (
        "metadata/taxonomy/compound-taxonomy.skos.jsonld",
        "metadata/taxonomy/content-taxonomy.skos.jsonld",
    ):
        document = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        for node in document["@graph"]:
            if node.get("@type") != "skos:Concept":
                continue
            labels = node["skos:prefLabel"]
            assert isinstance(labels, list), node["@id"]
            languages = {label.get("@language") for label in labels}
            assert languages == {"en", "ja"}, (node["@id"], languages)


# ---------------------------------------------------------------------------
# the detector
# ---------------------------------------------------------------------------


def test_detects_a_duplicate_key() -> None:
    findings = scan_json_text('{"a": 1, "a": 2}', origin="probe.json")
    assert findings == [
        {"origin": "probe.json", "context": "", "key": "a", "count": 2}
    ]


def test_does_not_flag_unique_or_repeated_values() -> None:
    assert scan_json_text('{"a": [1, 2], "b": 2}') == []
    assert scan_json_text('{"a": {"b": 1}, "c": {"b": 2}}') == []


def test_detects_nested_duplicates_and_names_the_concept() -> None:
    text = '{"@graph": [{"skos:notation": "compound_x", "p": 1, "p": 2}]}'
    findings = scan_json_text(text)
    assert len(findings) == 1
    assert findings[0]["key"] == "p"
    assert findings[0]["context"] == "compound_x"


def test_three_occurrences_are_reported_once_with_the_count() -> None:
    findings = scan_json_text('{"a": 1, "a": 2, "a": 3}')
    assert findings[0]["count"] == 3


def test_invalid_json_still_raises() -> None:
    with pytest.raises(json.JSONDecodeError):
        scan_json_text("{ not json")
