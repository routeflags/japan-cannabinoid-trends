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
import re
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
    STATUS_PRIVATE_INPUT,
    STATUS_REPRODUCIBLE,
    STATUS_UNDECLARED,
    STATUS_WITHDRAWN,
    WITHDRAWN,
    DeclaredDiscrepancy,
    Derivation,
    audit_processed_artifacts,
    reproduce_artifact,
)
from processing.rulespec import load_content_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = "datasets/cbx-social-trends/data/processed"
#: The published per-post artifact was withdrawn on 2026-10-15 (per-post X data
#: is not published even anonymized); the rule that produced it is still covered
#: here, the artifact no longer is.  ``SOURCE`` remains the non-published copy the
#: rule needs where it exists.
SOURCE = "datasets/cbx-social-trends/data/private/x_cbx_202608_summary.csv"
WITHDRAWN_PATH = f"{PROCESSED}/x_cbx_202608_summary.csv"
ANONYMIZED_PATH = f"{PROCESSED}/x_cbx_202608_summary_anonymized.csv"

requires_source = pytest.mark.skipif(
    not (REPO_ROOT / SOURCE).is_file(),
    reason="non-published X summary not present in this checkout",
)


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


@requires_source
def test_source_columns_are_the_ones_the_source_file_carries() -> None:
    """The declared source columns must actually be present, or the rule is fiction."""

    source_header = set(_rows(REPO_ROOT / SOURCE)[0])
    assert set(SOURCE_COLUMNS) <= source_header
    assert "tweet_id" in source_header


# ---------------------------------------------------------------------------
# re-derivation (fixture-based since the real artifact was withdrawn)
# ---------------------------------------------------------------------------
#
# The only committed derivation used to be the anonymized per-post X summary.
# Per-post X data is not published in any form since 2026-10-15
# (ISS-20261015-COL-030 4.1), so that artifact is withdrawn and the real-data
# check ended with it (see ``WITHDRAWN`` in src/processing/reproduce.py).  The
# machinery is what makes an artifact re-derivable rather than merely declared,
# so it is exercised here on a fixture repository instead.

STUDY_SOURCE = "datasets/stub-study/data/private/source.csv"
STUDY_ARTIFACT = "datasets/stub-study/data/processed/out.csv"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fixture_repo(tmp_path: Path, rules) -> tuple[list[dict], list[dict]]:
    """Write a source and its correct derivation; return both row lists."""

    source_rows = [
        _source_row(tweet_id="1", createdAt="2026-08-03T00:00:00.000Z"),
        _source_row(tweet_id="2", username="bob", createdAt="2026-08-31T00:01:33.000Z"),
    ]
    derived_rows = anonymize_rows(source_rows, rules)
    _write_csv(tmp_path / STUDY_SOURCE, source_rows)
    _write_csv(tmp_path / STUDY_ARTIFACT, derived_rows)
    return source_rows, derived_rows


def _register(monkeypatch, **overrides) -> None:
    import processing.reproduce as module

    monkeypatch.setitem(
        module.DERIVATIONS,
        STUDY_ARTIFACT,
        Derivation(
            source=STUDY_SOURCE,
            columns=ANONYMIZED_COLUMNS,
            kind="x-summary-anonymization",
            source_published=overrides.get("source_published", False),
            discrepancies=overrides.get("discrepancies", ()),
        ),
    )


def test_a_registered_derivation_is_re_derived_and_matches(tmp_path, rules, monkeypatch) -> None:
    _fixture_repo(tmp_path, rules)
    _register(monkeypatch)

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)

    assert report["status"] == STATUS_REPRODUCIBLE
    assert report["rows"] == {"derived": 2, "committed": 2, "match": True}
    assert report["discrepancies"] == []


def test_an_undeclared_difference_is_reported_with_its_rows(
    tmp_path, rules, monkeypatch
) -> None:
    """The artifact is the output of the rule, so a difference is drift, not noise."""

    _, derived_rows = _fixture_repo(tmp_path, rules)
    derived_rows[1]["likes"] = "999"
    _write_csv(tmp_path / STUDY_ARTIFACT, derived_rows)
    _register(monkeypatch)

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)

    assert report["status"] == STATUS_UNDECLARED
    assert report["undeclared_drift"] == [
        {"column": "likes", "derived_value": "1", "committed_value": "999", "rows": 1}
    ]


def test_a_declared_discrepancy_is_accepted_and_reported(tmp_path, rules, monkeypatch) -> None:
    _, derived_rows = _fixture_repo(tmp_path, rules)
    derived_rows[1]["week"] = "unknown"
    _write_csv(tmp_path / STUDY_ARTIFACT, derived_rows)
    _register(
        monkeypatch,
        discrepancies=(
            DeclaredDiscrepancy(
                column="week",
                derived_value="W5",
                committed_value="unknown",
                rows=1,
                identified_on="2026-10-15",
                reason="fabricated for the test",
            ),
        ),
    )

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)

    assert report["status"] == STATUS_DECLARED_DISCREPANCY
    assert report["undeclared_drift"] == []
    assert report["stale_declarations"] == []
    assert report["discrepancies"] == [
        {"column": "week", "derived_value": "W5", "committed_value": "unknown", "rows": 1}
    ]


def test_an_absent_source_is_a_declared_state_not_a_failure(tmp_path, rules, monkeypatch) -> None:
    """A source that is deliberately not published cannot be verified here."""

    _, derived_rows = _fixture_repo(tmp_path, rules)
    (tmp_path / STUDY_SOURCE).unlink()
    _register(monkeypatch)

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)

    assert report["status"] == STATUS_PRIVATE_INPUT
    assert report["rows"] == {"derived": None, "committed": 2, "match": None}
    assert report["undeclared_drift"] == []


def test_a_published_source_that_is_missing_is_an_error(tmp_path, rules, monkeypatch) -> None:
    _fixture_repo(tmp_path, rules)
    (tmp_path / STUDY_SOURCE).unlink()
    _register(monkeypatch, source_published=True)

    with pytest.raises(FileNotFoundError, match="published source missing"):
        reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)


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

    target = "datasets/cannabinoid-multi-trends/data/processed/collection-summary.md"
    monkeypatch.delitem(NON_REPRODUCIBLE, target)
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    assert target in report["failures"]
    entry = next(e for e in report["entries"] if e["artifact"] == target)
    assert entry["status"] == STATUS_UNDECLARED


def test_stale_declaration_is_reported(tmp_path, rules, monkeypatch) -> None:
    """A declaration that no longer describes reality is itself a failure."""

    _fixture_repo(tmp_path, rules)
    _register(
        monkeypatch,
        discrepancies=(
            DeclaredDiscrepancy(
                column="likes",
                derived_value="1",
                committed_value="999",
                rows=7,
                identified_on="2026-10-15",
                reason="fabricated for the test",
            ),
        ),
    )

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)

    assert report["status"] == STATUS_UNDECLARED
    assert report["stale_declarations"] == [
        {
            "column": "likes",
            "derived_value": "1",
            "committed_value": "999",
            "declared_rows": 7,
        }
    ]


def test_declarations_and_non_reproducible_entries_do_not_overlap() -> None:
    assert not set(DERIVATIONS) & set(NON_REPRODUCIBLE)
    assert not set(DERIVATIONS) & set(WITHDRAWN)
    assert not set(NON_REPRODUCIBLE) & set(WITHDRAWN)
    for path in list(DERIVATIONS) + list(NON_REPRODUCIBLE):
        assert (REPO_ROOT / path).is_file(), path


def test_every_withdrawn_artifact_is_recorded_absent_and_absent_from_git() -> None:
    """Removal must be a recorded fact, not a deletion (AGENTS.md).

    Withdrawals differ in why they happened, so the shared rules are checked for
    all of them and the entries keep their own dated narrative.
    """

    from validation.storage_policy import git_tracked

    assert WITHDRAWN
    for path, record in sorted(WITHDRAWN.items()):
        assert not (REPO_ROOT / path).exists(), path
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", record.withdrawn_on), path
        assert record.reason and record.exposure and record.notes, path
        assert "zenodo" in record.exposure.lower() or "not retract" in record.exposure, path
        # ``replacement`` is either a repository path that exists, or "None"
        # followed by what stands in for the artifact (nothing, when a policy
        # forbids it in any form).
        head = record.replacement.split(" ")[0].strip()
        if not head.startswith("None"):
            assert (REPO_ROOT / head).is_file(), path
        assert not git_tracked(REPO_ROOT, path), path


def test_withdrawn_artifacts_are_listed_by_the_audit() -> None:
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    reported = {entry["artifact"] for entry in report["withdrawn"]}
    assert reported == set(WITHDRAWN)
    for entry in report["withdrawn"]:
        assert entry["status"] == STATUS_WITHDRAWN
        assert entry["tracked_again"] is False
        assert entry["artifact"] not in report["failures"]


def test_withdrawn_artifact_fails_if_tracked_again(monkeypatch) -> None:
    """Re-adding a withdrawn artifact must require a new decision."""

    import processing.reproduce as module

    monkeypatch.setattr(module, "git_tracked", lambda root, path: path == WITHDRAWN_PATH)
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    assert WITHDRAWN_PATH in report["failures"]


def test_non_published_source_reports_its_own_status(tmp_path, rules, monkeypatch) -> None:
    """Absent source is a declared state, not a verification failure.

    The published artifact is written without its source, which is exactly the
    situation in any fresh clone and in CI.
    """

    _, derived_rows = _fixture_repo(tmp_path, rules)
    (tmp_path / STUDY_SOURCE).unlink()
    _register(monkeypatch)

    report = reproduce_artifact(tmp_path, STUDY_ARTIFACT, rules)
    assert report["status"] == STATUS_PRIVATE_INPUT
    assert report["rows"]["derived"] is None
    assert report["undeclared_drift"] == []
    assert report["stale_declarations"] == []
    assert len(derived_rows) == 2


def test_placeholder_status_is_reserved_for_gitkeep() -> None:
    report = audit_processed_artifacts(REPO_ROOT, REPO_ROOT / "datasets")
    for entry in report["entries"]:
        if entry["status"] == STATUS_PLACEHOLDER:
            assert Path(entry["artifact"]).name == ".gitkeep"
