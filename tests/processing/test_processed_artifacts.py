"""Derivation and re-derivation-audit tests for committed processed artifacts.

Contract sources: ``docs/data-dictionary.md`` (the documented anonymization
mapping), ``datasets/*/methodology.md``, AGENTS.md (raw immutability, reproducible
transformations, missing is never zero).

The decisive tests are
:func:`test_anonymized_artifact_matches_every_column_but_the_declared_rows` (the
committed artifact really is the output of the rule now in code) and
:func:`test_artifact_in_no_registry_fails_the_audit` (a newly committed processed
artifact cannot skip the reproducible-or-declared question).
"""

import csv
import hashlib
from pathlib import Path

import pytest

from processing.anonymize import (
    ANONYMIZED_COLUMNS,
    SOURCE_COLUMNS,
    AnonymizeError,
    anonymize_rows,
)
from processing.reproduce import (
    DERIVATIONS,
    NON_REPRODUCIBLE,
    STATUS_DECLARED_DISCREPANCY,
    STATUS_PLACEHOLDER,
    STATUS_UNDECLARED,
    DeclaredDiscrepancy,
    Derivation,
    audit_processed_artifacts,
    reproduce_artifact,
)
from processing.rulespec import load_content_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = "datasets/cbx-social-trends/data/processed"
ANONYMIZED = f"{PROCESSED}/x_cbx_202608_summary_anonymized.csv"
SOURCE = f"{PROCESSED}/x_cbx_202608_summary.csv"


@pytest.fixture(scope="module")
def rules():
    return load_content_rules(repo_root=REPO_ROOT)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_row(**overrides: str) -> dict[str, str]:
    row = {
        "tweet_id": "1",
        "createdAt": "2026-08-03T00:00:00.000Z",
        "lang": "ja",
        "username": "alice",
        "views": "10",
        "likes": "1",
        "reposts": "0",
        "replies": "0",
        "text": "成分 の 配合",
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# anonymize_rows rules
# ---------------------------------------------------------------------------


def test_hash_is_sha256_truncated_to_16(rules) -> None:
    row = _source_row(tweet_id="2095355612196671657")
    derived = anonymize_rows([row], rules)[0]
    expected = hashlib.sha256(b"2095355612196671657").hexdigest()[:16]
    assert derived["tweet_id_hash"] == expected
    assert len(derived["tweet_id_hash"]) == 16


def test_author_pseudonyms_follow_first_appearance(rules) -> None:
    rows = [
        _source_row(tweet_id="1", username="bob"),
        _source_row(tweet_id="2", username="alice"),
        _source_row(tweet_id="3", username="bob"),
    ]
    derived = anonymize_rows(rows, rules)
    assert [d["author_id"] for d in derived] == ["author_001", "author_002", "author_001"]


def test_author_count_exceeds_pseudonym_width(rules) -> None:
    """The committed artifact has 55 authors, so 3-digit padding must not truncate."""

    rows = [_source_row(tweet_id=str(i), username=f"u{i}") for i in range(120)]
    derived = anonymize_rows(rows, rules)
    assert derived[99]["author_id"] == "author_100"
    assert derived[119]["author_id"] == "author_120"
    assert len({d["author_id"] for d in derived}) == 120


@pytest.mark.parametrize(
    ("created_at", "expected"),
    [
        ("2026-08-03T00:00:00.000Z", "W1"),
        ("2026-08-09T23:59:59.000Z", "W1"),
        ("2026-08-10T00:00:00.000Z", "W2"),
        ("2026-08-31T00:00:00.000Z", "W5"),
        ("2026-08-02T00:00:00.000Z", "unknown"),
    ],
)
def test_week_uses_the_monday_anchor(rules, created_at: str, expected: str) -> None:
    derived = anonymize_rows([_source_row(createdAt=created_at)], rules)[0]
    assert derived["week"] == expected


def test_text_derivations(rules) -> None:
    derived = anonymize_rows(
        [_source_row(text="成分 と 配合"), _source_row(tweet_id="2", text="   ")],
        rules,
    )
    assert derived[0]["text_length"] == "7"
    assert derived[0]["has_text"] == "yes"
    assert derived[1]["text_length"] == "3"
    assert derived[1]["has_text"] == "no"


def test_derived_columns_match_the_committed_order(rules) -> None:
    derived = anonymize_rows([_source_row()], rules)[0]
    assert tuple(derived) == ANONYMIZED_COLUMNS
    assert "text" not in derived and "username" not in derived


def test_duplicate_tweet_id_is_rejected(rules) -> None:
    rows = [_source_row(tweet_id="1"), _source_row(tweet_id="1")]
    with pytest.raises(AnonymizeError, match="duplicate tweet_id"):
        anonymize_rows(rows, rules)


def test_missing_source_column_is_rejected(rules) -> None:
    incomplete = _source_row()
    del incomplete["username"]
    with pytest.raises(AnonymizeError, match="missing source columns"):
        anonymize_rows([incomplete], rules)


def test_source_columns_are_the_ones_the_source_file_carries() -> None:
    """The declared source columns must actually be present, or the rule is fiction."""

    source_header = set(_rows(REPO_ROOT / SOURCE)[0])
    assert set(SOURCE_COLUMNS) <= source_header
    assert "tweet_id" in source_header


# ---------------------------------------------------------------------------
# re-derivation against the committed artifact
# ---------------------------------------------------------------------------


def test_anonymized_artifact_matches_every_column_but_the_declared_rows(rules) -> None:
    report = reproduce_artifact(REPO_ROOT, ANONYMIZED, rules)
    assert report["status"] == STATUS_DECLARED_DISCREPANCY
    assert report["rows"]["match"] is True
    assert report["rows"]["derived"] == 147
    assert report["undeclared_drift"] == []
    assert report["stale_declarations"] == []
    assert report["discrepancies"] == [
        {
            "column": "week",
            "derived_value": "W5",
            "committed_value": "unknown",
            "rows": 3,
        }
    ]


def test_declared_discrepancy_names_the_affected_rows(rules) -> None:
    """The three rows must be the 2026-08-31 rows, not any three rows."""

    derived = anonymize_rows(_rows(REPO_ROOT / SOURCE), rules)
    committed = _rows(REPO_ROOT / ANONYMIZED)
    differing = [
        (source["createdAt"], got["week"], want["week"])
        for source, got, want in zip(_rows(REPO_ROOT / SOURCE), derived, committed)
        if got["week"] != want["week"]
    ]
    assert differing == [
        ("2026-08-31T08:30:51.000Z", "W5", "unknown"),
        ("2026-08-31T06:01:24.000Z", "W5", "unknown"),
        ("2026-08-31T00:01:33.000Z", "W5", "unknown"),
    ]


# ---------------------------------------------------------------------------
# the audit rule
# ---------------------------------------------------------------------------


def test_every_committed_artifact_is_accounted_for() -> None:
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    assert report["count"] > 0
    assert report["failures"] == []
    assert report["failure_count"] == 0
    for entry in report["entries"]:
        assert entry["status"] != STATUS_UNDECLARED, entry["artifact"]


def test_audit_is_read_only_over_raw_data() -> None:
    from validation.integrity import sha256_file

    raw_root = REPO_ROOT / "datasets/cbx-social-trends/data/raw"
    before = {p: sha256_file(p) for p in sorted(raw_root.rglob("*")) if p.is_file()}
    audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    after = {p: sha256_file(p) for p in sorted(raw_root.rglob("*")) if p.is_file()}
    assert before == after


def test_artifact_in_no_registry_fails_the_audit(monkeypatch) -> None:
    """A newly committed processed artifact must not skip this question."""

    monkeypatch.delitem(NON_REPRODUCIBLE, f"{PROCESSED}/x_cbx_202608_summary.csv")
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    assert f"{PROCESSED}/x_cbx_202608_summary.csv" in report["failures"]
    entry = next(
        e for e in report["entries"] if e["artifact"] == f"{PROCESSED}/x_cbx_202608_summary.csv"
    )
    assert entry["status"] == STATUS_UNDECLARED


def test_stale_declaration_is_reported(monkeypatch) -> None:
    """A declaration that no longer describes reality is itself a failure."""

    original = DERIVATIONS[ANONYMIZED]
    monkeypatch.setitem(
        DERIVATIONS,
        ANONYMIZED,
        Derivation(
            source=original.source,
            columns=original.columns,
            kind=original.kind,
            discrepancies=original.discrepancies
            + (
                DeclaredDiscrepancy(
                    column="has_text",
                    derived_value="yes",
                    committed_value="no",
                    rows=7,
                    identified_on="2026-10-13",
                    reason="fabricated for the test",
                ),
            ),
        ),
    )
    report = reproduce_artifact(REPO_ROOT, ANONYMIZED)
    assert report["status"] == STATUS_UNDECLARED
    assert report["stale_declarations"] == [
        {
            "column": "has_text",
            "derived_value": "yes",
            "committed_value": "no",
            "declared_rows": 7,
        }
    ]


def test_declarations_and_non_reproducible_entries_do_not_overlap() -> None:
    assert not set(DERIVATIONS) & set(NON_REPRODUCIBLE)
    for path in list(DERIVATIONS) + list(NON_REPRODUCIBLE):
        assert (REPO_ROOT / path).is_file(), path


def test_placeholder_status_is_reserved_for_gitkeep() -> None:
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    for entry in report["entries"]:
        if entry["status"] == STATUS_PLACEHOLDER:
            assert Path(entry["artifact"]).name == ".gitkeep"
