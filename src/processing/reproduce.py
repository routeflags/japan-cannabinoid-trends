"""Re-derivation audit over committed ``datasets/*/data/processed`` artifacts.

AGENTS.md requires every derived field to have a documented, reproducible
derivation, and requires derived totals to be reconcilable with their upstream
records.  Before this module the repository had committed processed artifacts whose
derivation lived only in prose (or nowhere at all), and nothing noticed when an
artifact and its rules drifted apart.

The rule enforced here is one rule for all artifacts: **a committed processed
artifact must be either**

1. re-derivable from tracked inputs by an executable transformation
   (:data:`DERIVATIONS`), or
2. explicitly declared non-reproducible from repository contents, naming the
   missing inputs (:data:`NON_REPRODUCIBLE`).

An artifact in neither registry fails the audit, so a newly committed processed
file cannot quietly skip this question.  Two further states are failures rather
than warnings, because both mean a declaration is lying:

- ``undeclared_drift`` -- the derivation differs from the committed artifact in a
  way no declaration covers;
- ``stale_declaration`` -- a declared discrepancy no longer occurs, e.g. because
  the artifact was corrected.

The audit is read-only: it derives in memory, compares, and never rewrites a
committed dataset file or touches raw data.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from processing.anonymize import ANONYMIZED_COLUMNS, anonymize_rows
from processing.rulespec import ContentRules, load_content_rules
from validation.storage_policy import git_tracked

__all__ = [
    "AUDIT_VERSION",
    "STATUS_REPRODUCIBLE",
    "STATUS_DECLARED_DISCREPANCY",
    "STATUS_NOT_REPRODUCIBLE",
    "STATUS_PLACEHOLDER",
    "PLACEHOLDER_NAMES",
    "STATUS_UNDECLARED",
    "DERIVATIONS",
    "NON_REPRODUCIBLE",
    "REVIEW_NOTES",
    "DeclaredDiscrepancy",
    "audit_processed_artifacts",
    "reproduce_artifact",
]

AUDIT_VERSION = "1.0.0"

STATUS_REPRODUCIBLE = "reproducible"
STATUS_DECLARED_DISCREPANCY = "reproducible_with_declared_discrepancy"
STATUS_NOT_REPRODUCIBLE = "not_reproducible_from_repository"
STATUS_PLACEHOLDER = "placeholder"
STATUS_UNDECLARED = "undeclared"

#: Tracked files that exist only to keep an empty directory in git.  They hold no
#: data, so "reproducible" is vacuous for them; they are reported under their own
#: status rather than silently skipped.
PLACEHOLDER_NAMES = frozenset({".gitkeep"})


@dataclass(frozen=True)
class DeclaredDiscrepancy:
    """A difference between the derivation and the committed artifact that is
    known, dated, and deliberately accepted."""

    column: str
    derived_value: str
    committed_value: str
    rows: int
    identified_on: str
    reason: str


@dataclass(frozen=True)
class Derivation:
    """An executable transformation from a tracked source to an artifact."""

    source: str
    columns: tuple[str, ...]
    kind: str
    discrepancies: tuple[DeclaredDiscrepancy, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class NonReproducible:
    """An artifact that cannot be re-derived from repository contents."""

    reason: str
    missing_inputs: tuple[str, ...]
    upstream_step: str
    notes: tuple[str, ...] = ()


#: Executable derivations, keyed by repository-relative artifact path.
DERIVATIONS: dict[str, Derivation] = {
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv": Derivation(
        source="datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv",
        columns=ANONYMIZED_COLUMNS,
        kind="x-summary-anonymization",
        discrepancies=(
            DeclaredDiscrepancy(
                column="week",
                derived_value="W5",
                committed_value="unknown",
                rows=3,
                identified_on="2026-10-13",
                reason=(
                    "The committed artifact labels the three 2026-08-31 rows "
                    "'unknown' while the Monday-anchored week rule (WEEK_ANCHOR "
                    "2026-08-03) yields W5.  Every other row matches the rule.  "
                    "The artifact is left unchanged: correcting it would rewrite "
                    "published derived data, which AGENTS.md forbids.  The "
                    "discrepancy is recorded so a future correction is a new "
                    "version, not a silent edit."
                ),
            ),
        ),
    ),
}

#: Declared non-reproducible artifacts, keyed by repository-relative artifact path.
NON_REPRODUCIBLE: dict[str, NonReproducible] = {
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv": NonReproducible(
        reason=(
            "Deduplicated from an Apify collection whose raw response is not in "
            "the repository, and the collection is non-deterministic: repeating "
            "it would not reproduce these 147 rows."
        ),
        missing_inputs=(
            "datasets/cbx-social-trends/data/raw/x/202608/ (declared by "
            "cbx-social-trends/methodology.md section 2.1; absent from the "
            "repository)",
        ),
        upstream_step="raw (Apify daily JSON) -> language filter -> dedup by tweet_id",
        notes=(
            "This file is the input to DERIVATIONS for the anonymized summary, "
            "so the anonymization rule is verified even though this source is "
            "not reproducible.",
        ),
    ),
    "datasets/cbx-social-trends/data/processed/youtube_filtered_202607/records_filtered.csv": NonReproducible(
        reason=(
            "Filtered from a YouTube collection that is not in the repository.  "
            "The filter rule itself is documented in the sibling "
            "filter_metadata.json, but its input records are not."
        ),
        missing_inputs=(
            "Apify run 20261001T075500Z-youtube-cbx-rikiddo-v2 (named as "
            "source_run in filter_metadata.json; no raw artifact in the repository)",
        ),
        upstream_step="raw (Apify YouTube JSON) -> timestamp exclusion filter",
    ),
    "datasets/cbx-social-trends/data/processed/youtube_filtered_202607/records_filtered.json": NonReproducible(
        reason=(
            "Same derivation as records_filtered.csv; the JSON variant is the "
            "same filtered records in a different serialization."
        ),
        missing_inputs=(
            "Apify run 20261001T075500Z-youtube-cbx-rikiddo-v2 (no raw artifact "
            "in the repository)",
        ),
        upstream_step="raw (Apify YouTube JSON) -> timestamp exclusion filter",
    ),
    "datasets/cbx-social-trends/data/processed/youtube_filtered_202607/filter_metadata.json": NonReproducible(
        reason=(
            "Records the outcome of the filter step (original_count 26, "
            "filtered_count 24, 2 excluded videos).  The filter *rule* is stated "
            "here and is reusable, but the counts and the excluded items come "
            "from the same absent collection."
        ),
        missing_inputs=(
            "Apify run 20261001T075500Z-youtube-cbx-rikiddo-v2 (no raw artifact "
            "in the repository)",
        ),
        upstream_step="raw (Apify YouTube JSON) -> timestamp exclusion filter",
        notes=(
            "This file is the documented rule for its sibling records_filtered.* "
            "and is deliberately kept: it is the only trace of the filter step.",
        ),
    ),
    "datasets/cannabinoid-multi-trends/data/processed/collection-summary.md": NonReproducible(
        reason=(
            "Hand-written collection summary combining source-side totals.  The "
            "Google Trends tables can be recomputed from tracked records_*.json, "
            "but the X (316 items) and YouTube (182 items) totals cannot; no "
            "executable transformation has ever existed for this file."
        ),
        missing_inputs=(
            "X and YouTube raw collections for the 2026-10-02 run (not in the "
            "repository)",
        ),
        upstream_step="collection run -> hand-written summary",
        notes=(
            "A future improvement is to regenerate the Google Trends tables and "
            "mark the X/YouTube rows as source-reported rather than re-derived.",
        ),
    ),
    "datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv": NonReproducible(
        reason=(
            "Analysis artifact whose derivation is documented nowhere: no "
            "script, no methodology section, no recorded parameters.  The "
            "interpretive fields (cohort, persistence_class, emergence_score) "
            "have no stated rule at all."
        ),
        missing_inputs=(
            "Derivation rule and parameters (unrecorded); some 5-year Google "
            "Trends inputs are present under "
            "datasets/cannabinoid-multi-trends/data/raw/google_trends/"
        ),
        upstream_step="Google Trends + regulatory knowledge graph -> undocumented analysis",
        notes=(
            "Recovering this derivation is the next increment: it is the only "
            "committed artifact with no rule whatsoever, and its regulated-status "
            "columns duplicate the knowledge graph.",
        ),
    ),
}

#: Review notes surfaced by the report without changing any status.
REVIEW_NOTES: dict[str, tuple[str, ...]] = {
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv": (
        "Privacy: this tracked file holds X usernames, display names, post text "
        "and post URLs.  AGENTS.md requires a redistribution review before "
        "publishing social-platform records, and the anonymized sibling exists "
        "precisely so the publishable artifact omits them.  Whether the "
        "non-anonymized summary should remain tracked is an open decision for "
        "the maintainer; this audit only records it.",
    ),
}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def reproduce_artifact(
    root: Path, relative: str, rules: ContentRules | None = None
) -> dict:
    """Re-derive one artifact and compare it with the committed file.

    Returns a report dict; it does not raise on a mismatch.  Callers decide what
    to do with ``status`` and ``discrepancies``.
    """

    derivation = DERIVATIONS[relative]
    source_path = root / derivation.source
    target_path = root / relative
    report: dict = {
        "artifact": relative,
        "source": derivation.source,
        "derivation": derivation.kind,
        "columns": list(derivation.columns),
        "notes": list(derivation.notes),
    }

    committed = _read_rows(target_path)
    if derivation.kind == "x-summary-anonymization":
        active = rules if rules is not None else load_content_rules(repo_root=root)
        derived = anonymize_rows(_read_rows(source_path), active)
    else:  # pragma: no cover - registry is closed; guarded by tests
        raise ValueError(f"unknown derivation kind: {derivation.kind!r}")

    observed: Counter[tuple[str, str, str]] = Counter()
    row_count_matches = len(derived) == len(committed)
    if row_count_matches:
        for derived_row, committed_row in zip(derived, committed):
            for column in derivation.columns:
                if derived_row[column] != committed_row[column]:
                    observed[(column, derived_row[column], committed_row[column])] += 1

    declared = Counter(
        {
            (d.column, d.derived_value, d.committed_value): d.rows
            for d in derivation.discrepancies
        }
    )

    undeclared = observed - declared
    stale = declared - observed

    report["rows"] = {
        "derived": len(derived),
        "committed": len(committed),
        "match": row_count_matches,
    }
    report["discrepancies"] = [
        {
            "column": column,
            "derived_value": derived_value,
            "committed_value": committed_value,
            "rows": count,
        }
        for (column, derived_value, committed_value), count in sorted(observed.items())
    ]
    report["declared_discrepancies"] = [
        {
            "column": d.column,
            "derived_value": d.derived_value,
            "committed_value": d.committed_value,
            "rows": d.rows,
            "identified_on": d.identified_on,
            "reason": d.reason,
        }
        for d in derivation.discrepancies
    ]
    report["undeclared_drift"] = [
        {
            "column": column,
            "derived_value": derived_value,
            "committed_value": committed_value,
            "rows": count,
        }
        for (column, derived_value, committed_value), count in sorted(undeclared.items())
    ]
    report["stale_declarations"] = [
        {
            "column": column,
            "derived_value": derived_value,
            "committed_value": committed_value,
            "declared_rows": declared[(column, derived_value, committed_value)],
        }
        for column, derived_value, committed_value in sorted(stale)
    ]
    if not row_count_matches:
        report["status"] = STATUS_UNDECLARED
    elif undeclared or stale:
        report["status"] = STATUS_UNDECLARED
    elif observed:
        report["status"] = STATUS_DECLARED_DISCREPANCY
    else:
        report["status"] = STATUS_REPRODUCIBLE
    return report


def _committed_processed_files(root: Path, datasets_root: Path) -> list[str]:
    """Repository-relative paths of git-tracked files under ``data/processed``."""

    found: list[str] = []
    if not datasets_root.is_dir():
        return found
    for study in sorted(p for p in datasets_root.iterdir() if p.is_dir()):
        processed = study / "data" / "processed"
        if not processed.is_dir():
            continue
        for path in sorted(p for p in processed.rglob("*") if p.is_file()):
            relative = path.relative_to(root).as_posix()
            if git_tracked(root, relative):
                found.append(relative)
    return found


def audit_processed_artifacts(root: Path, datasets_root: Path) -> dict:
    """Audit every committed processed artifact against its derivation status."""

    root = Path(root).resolve()
    datasets_root = Path(datasets_root)
    if not datasets_root.is_absolute():
        datasets_root = root / datasets_root

    entries: list[dict] = []
    rules: ContentRules | None = None
    counts = Counter()

    for relative in _committed_processed_files(root, datasets_root):
        if Path(relative).name in PLACEHOLDER_NAMES:
            entry = {
                "artifact": relative,
                "status": STATUS_PLACEHOLDER,
                "reason": "Directory placeholder with no data content.",
            }
        elif relative in DERIVATIONS:
            if rules is None:
                rules = load_content_rules(repo_root=root)
            entry = reproduce_artifact(root, relative, rules)
        elif relative in NON_REPRODUCIBLE:
            declared = NON_REPRODUCIBLE[relative]
            entry = {
                "artifact": relative,
                "status": STATUS_NOT_REPRODUCIBLE,
                "reason": declared.reason,
                "missing_inputs": list(declared.missing_inputs),
                "upstream_step": declared.upstream_step,
                "notes": list(declared.notes),
            }
        else:
            entry = {
                "artifact": relative,
                "status": STATUS_UNDECLARED,
                "reason": (
                    "Committed processed artifact is in neither DERIVATIONS nor "
                    "NON_REPRODUCIBLE.  Provide an executable derivation or "
                    "declare the missing inputs."
                ),
            }
        if relative in REVIEW_NOTES:
            entry["review_notes"] = list(REVIEW_NOTES[relative])
        counts[entry["status"]] += 1
        entries.append(entry)

    failures = [
        entry["artifact"]
        for entry in entries
        if entry["status"] == STATUS_UNDECLARED
    ]

    return {
        "audit_version": AUDIT_VERSION,
        "root": str(root),
        "count": len(entries),
        "status_summary": dict(counts),
        "failure_count": len(failures),
        "failures": failures,
        "entries": entries,
    }
