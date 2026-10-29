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
import hashlib
import json
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from processing.anonymize import ANONYMIZED_COLUMNS, anonymize_rows
from processing.platform_trends import (
    COVERAGE_COLUMNS,
    METRIC_COLUMNS,
    OBSERVATION_COLUMNS,
    RUN_INDEX_COLUMNS,
    build_platform_trends,
)
from processing.youtube_monthly_aggregate import (
    OUTPUT_COLUMNS as YOUTUBE_MONTHLY_COLUMNS,
    aggregate_youtube_rows,
)
from processing.rulespec import ContentRules, load_content_rules
from validation.storage_policy import git_tracked

__all__ = [
    "AUDIT_VERSION",
    "STATUS_REPRODUCIBLE",
    "STATUS_DECLARED_DISCREPANCY",
    "STATUS_NOT_REPRODUCIBLE",
    "STATUS_PRIVATE_INPUT",
    "STATUS_PLACEHOLDER",
    "STATUS_WITHDRAWN",
    "PLACEHOLDER_NAMES",
    "STATUS_UNDECLARED",
    "DERIVATIONS",
    "NON_REPRODUCIBLE",
    "WITHDRAWN",
    "DeclaredDiscrepancy",
    "Derivation",
    "Withdrawn",
    "audit_processed_artifacts",
    "reproduce_artifact",
]

AUDIT_VERSION = "1.1.0"

STATUS_REPRODUCIBLE = "reproducible"
STATUS_DECLARED_DISCREPANCY = "reproducible_with_declared_discrepancy"
STATUS_NOT_REPRODUCIBLE = "not_reproducible_from_repository"
STATUS_PRIVATE_INPUT = "reproducible_requires_non_published_input"
STATUS_PLACEHOLDER = "placeholder"
STATUS_WITHDRAWN = "withdrawn_from_publication"
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
    """An executable transformation from a source to an artifact.

    ``source_published`` records whether the source is allowed to be published.
    When it is ``False`` the source is expected to be absent in any clone or CI
    run, and the artifact is reported as reproducible-but-not-verifiable-here
    rather than as a failure (AGENTS.md: publish derived data plus methodology
    when raw redistribution is unsuitable).
    """

    source: str
    columns: tuple[str, ...]
    kind: str
    discrepancies: tuple[DeclaredDiscrepancy, ...] = ()
    notes: tuple[str, ...] = ()
    source_published: bool = True


@dataclass(frozen=True)
class NonReproducible:
    """An artifact that cannot be re-derived from repository contents."""

    reason: str
    missing_inputs: tuple[str, ...]
    upstream_step: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Withdrawn:
    """An artifact that was tracked and has been removed from publication.

    AGENTS.md forbids silently removing records, so a withdrawal is a recorded
    fact with a reason, not a deleted registry entry.  The audit also fails if a
    withdrawn path becomes tracked again without a new decision.
    """

    withdrawn_on: str
    reason: str
    replacement: str
    exposure: str
    notes: tuple[str, ...] = ()


#: Executable derivations, keyed by repository-relative artifact path.
#:
#: Since 2026-10-15 the per-post derivation is withdrawn (see WITHDRAWN);
#: the live derivation is the coarse monthly X aggregate (option ii of
#: ISS-20261014-PUB-029, further coarsened by owner decision on 2026-10-15).
#: Its source is the private per-post input
#: (gitignored, absent from any clone and from CI), so in a fresh checkout
#: they report ``reproducible_requires_non_published_input`` rather than
#: failing; fixture tests cover the rule unconditionally.
DERIVATIONS: dict[str, Derivation] = {
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_monthly_coarse_aggregates.csv": Derivation(
        source="datasets/cbx-social-trends/data/private/x_cbx_202608_summary_anonymized.csv",
        columns=(
            "month",
            "compound",
            "breakdown",
            "category",
            "post_count",
        ),
        kind="x-aggregate-monthly-coarse",
        source_published=False,
        notes=(
            "ISS-20261014-PUB-029 option ii (2026-10-15): coarse monthly group "
            "counts (marginal topic and engagement-tier breakdowns). No per-post row.",
        ),
    ),
    "datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv": Derivation(
        source="docs/audits/gt-summary.json",
        columns=OBSERVATION_COLUMNS,
        kind="platform-trends:trend_observations",
        notes=(
            "Cross-platform release slice generated by processing.platform_trends "
            "from Google Trends summary evidence, the COL-033 YouTube adoption "
            "declaration, and the query registry. X is excluded by owner decision "
            "on 2026-10-15.",
        ),
    ),
    "datasets/cannabinoid-platform-trends/data/processed/platform_coverage.csv": Derivation(
        source="docs/audits/gt-summary.json",
        columns=COVERAGE_COLUMNS,
        kind="platform-trends:platform_coverage",
        notes=(
            "Coverage matrix generated by processing.platform_trends. Missing or "
            "not-collected YouTube entries are recorded as not_collected, never as "
            "zero observations.",
        ),
    ),
    "datasets/cannabinoid-platform-trends/data/processed/metric_dictionary.csv": Derivation(
        source="docs/audits/gt-summary.json",
        columns=METRIC_COLUMNS,
        kind="platform-trends:metric_dictionary",
        notes=(
            "Metric dictionary generated by processing.platform_trends. Every "
            "metric is marked non-comparable across platforms because Google "
            "Trends indices and YouTube returned counts have different units.",
        ),
    ),
    "datasets/cannabinoid-platform-trends/data/processed/source_run_index.csv": Derivation(
        source="docs/audits/gt-summary.json",
        columns=RUN_INDEX_COLUMNS,
        kind="platform-trends:source_run_index",
        notes=(
            "Run-level provenance index generated by processing.platform_trends "
            "without redistributing raw YouTube video rows.",
        ),
    ),
    "datasets/cannabinoid-platform-trends/data/processed/manifest.json": Derivation(
        source="docs/audits/gt-summary.json",
        columns=(),
        kind="platform-trends:manifest",
        notes=(
            "Generated manifest for the cannabinoid-platform-trends processed "
            "tables. It records the source documents and row counts.",
        ),
    ),
    "datasets/cannabinoid-raw-collection/data/processed/youtube_monthly_counts.csv": Derivation(
        source=(
            "datasets/cannabinoid-raw-collection/data/raw/youtube/"
            "20261010T141947Z-youtube-cannabinoid-raw-collection/"
            "dataset_youtube-scraper_2026-10-10_14-19-47-693.csv"
        ),
        columns=YOUTUBE_MONTHLY_COLUMNS,
        kind="youtube-monthly-search-results",
        notes=(
            "Count distinct returned video IDs by UTC month from the HHBD リキッド "
            "YouTube run. This describes one search-result sample, not all YouTube "
            "uploads. Months with no returned rows are omitted, not encoded as zero.",
        ),
        source_published=False,
    ),
}

#: Artifacts removed from publication, keyed by the path they had while tracked.
#: Recorded rather than deleted (AGENTS.md: never silently remove records).
WITHDRAWN: dict[str, Withdrawn] = {
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv": Withdrawn(
        withdrawn_on="2026-10-15",
        reason=(
            "Per-post X data.  The 2026-10-15 decision (ISS-20261015-COL-030 "
            "4.1, transcribed in ISS-20261015-XID-034) is that a post-level X "
            "dataset is not published even anonymized: 147 rows are 147 posts, "
            "with post timestamps and per-post engagement, so publishing it "
            "redistributes the collection's structure.  It was tracked (and "
            "shipped in the release archives) until this withdrawal."
        ),
        replacement=(
            "None: no per-post representation is published.  The classification "
            "distributions the pages cite are recorded in "
            "config/content-classification-rules.json, and the anonymization rule "
            "stays executable in src/processing/anonymize.py."
        ),
        exposure=(
            "Tracked since 2026-10-13 (commit 6ef52a9) and present in tags "
            "v1.6.2 / v1.7.0 / v1.7.1 / v1.8.0 / v1.9.0 / v1.10.0 / v1.11.0 / "
            "v1.12.0, i.e. in those GitHub Releases and their Zenodo archives "
            "(DOI 10.5281/zenodo.23253840, open access).  Withdrawing it stops "
            "further distribution; it does not retract the published archives "
            "(the same posture as the withdrawal below, spec section 21.6).  "
            "2026-10-15: the 8 Zenodo records holding this file (v1.6.2-v1.12.0) "
            "were deleted by the owner (self-service, within 30 days of "
            "publication); the Zenodo API returns 410 Gone for all of them.  "
            "The GitHub Release zips of those tags are unchanged."
        ),
        notes=(
            "The derivation this artifact declared, kept here so the record is "
            "not lost: kind x-summary-anonymization, source "
            "datasets/cbx-social-trends/data/private/x_cbx_202608_summary.csv "
            "(gitignored, absent from any clone and from CI), 16 columns, and one "
            "declared discrepancy - column week, the rule yields W5 for the three "
            "2026-08-31 rows while the artifact said unknown (identified_on "
            "2026-10-13).  With the artifact withdrawn the discrepancy is "
            "history, not a live correction.",
            "The 2026-10-13 publication approval in metadata/publication/"
            "x-cbx-202608-summary-anonymized/ is superseded by a denied decision "
            "(2026-10-15) naming this policy; the review envelope is kept because "
            "it is the record of the earlier review, not because the artifact is "
            "publishable.",
        ),
    ),
    "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv": Withdrawn(
        withdrawn_on="2026-10-13",
        reason=(
            "Carried X post text, account handles, display names and post URLs.  "
            "docs/specs/sns-redistribution-assessment.md 1.4 (2026-10-01) already "
            "required exactly these fields to be kept out of DOI archives, and "
            "docs/data-dictionary.md 1.1 already warned that username and "
            "author_name need care on redistribution; neither was enforced, so "
            "the file shipped in every release archive instead."
        ),
        replacement=(
            "None since 2026-10-15.  It pointed at "
            "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv "
            "(same 147 records, hashed id, sequential account pseudonyms, no text "
            "or URLs), which was withdrawn as well: per-post X data is not "
            "published even anonymized (ISS-20261015-COL-030 4.1)."
        ),
        exposure=(
            "Public since 2026-10-01 (commit 2dae15b) and present in all 14 tags "
            "and GitHub Releases, including Zenodo DOI 10.5281/zenodo.23253840 "
            "(open access).  Withdrawing it stops further distribution; it does "
            "not retract the published archives.  Recorded here so the exposure "
            "is not lost.  2026-10-15: all 12 Zenodo records holding this file "
            "(v1.5.2-v1.12.0) were deleted by the owner (self-service, within "
            "30 days of publication); the Zenodo API returns 410 Gone for all "
            "of them.  The GitHub Release zips of those tags are unchanged."
        ),
        notes=(
            "The non-published copy used to verify the anonymization rule lives "
            "at datasets/cbx-social-trends/data/private/x_cbx_202608_summary.csv "
            "(gitignored, absent from any clone and from CI).",
            "A PRIVACY review note: this file is the reason "
            "src/validation/privacy.py exists.",
        ),
    ),
    "datasets/cannabinoid-raw-collection/data/processed/early-warning-index-v1.csv": Withdrawn(
        withdrawn_on="2026-10-15",
        reason=(
            "Work-in-progress artifact: the maintainer withdrew it because its "
            "derivation was never recorded (the earlier declaration here said the "
            "same) and nothing in the repository derives from it.  A half-finished "
            "analysis file in the published processed layer invites citing numbers "
            "whose meaning is unstated."
        ),
        replacement=(
            "None.  The publication that carried this index was renamed to "
            "publication/search-emergence-tracker/ (2026-10-09) and does not use "
            "this file as an input; the compound classification it once evidenced "
            "is canonical in metadata/taxonomy/compound-taxonomy.skos.jsonld and "
            "docs/data-dictionary.md section 6.4."
        ),
        exposure=(
            "Tracked since 2026-10-02 (commit 2c9a3bc) and present in tags v1.8.0 "
            "through v1.12.0, so it shipped in those GitHub Releases and in their "
            "Zenodo archives.  Withdrawing it stops further distribution; it does "
            "not retract the published archives."
        ),
        notes=(
            "docs/specs/validation-framework.md section 20.5 records the decision; "
            "docs/provenance/compound-taxonomy.md cited this file as the evidence "
            "for the H4CBH/HHBD semi-synthetic classification and carries a dated "
            "note at that citation.",
            "Dated research documents that mention the file "
            "(research/google-trends/20261004-google-trends-comparison.md, "
            "research/strategy/20261005-collection-strategy-recommendations.md, "
            "research/strategy/20261005-chair-data-collection-priorities.md, "
            "docs/reports/20261010a-data-quality-reproducibility-instructions.md, "
            "CHANGELOG.md 1.8.0) are left as they were: they record what was true "
            "on their date.",
            "A CHANGELOG entry belongs to the next release: the version-sync gate "
            "compares the CHANGELOG's first heading with the latest tag, so an "
            "[Unreleased] heading cannot be added.",
        ),
    ),
}

#: Declared non-reproducible artifacts, keyed by repository-relative artifact path.
NON_REPRODUCIBLE: dict[str, NonReproducible] = {
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
}

def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compare_rows(
    report: dict,
    derivation: Derivation,
    derived: list[dict[str, str]],
    committed: list[dict[str, str]],
) -> dict:
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


def _reproduce_platform_trends(
    root: Path, relative: str, derivation: Derivation, report: dict
) -> dict:
    target_path = root / relative
    output_name = Path(relative).name
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory)
        manifest = build_platform_trends(root, output_dir)
        derived_path = output_dir / output_name
        if output_name.endswith(".json"):
            committed = json.loads(target_path.read_text(encoding="utf-8"))
            derived = json.loads(derived_path.read_text(encoding="utf-8"))
            match = committed == derived
            report["rows"] = {
                "derived": manifest.get("row_counts"),
                "committed": committed.get("row_counts")
                if isinstance(committed, dict)
                else None,
                "match": match,
            }
            report["discrepancies"] = []
            report["declared_discrepancies"] = []
            report["undeclared_drift"] = []
            report["stale_declarations"] = []
            if match:
                report["status"] = STATUS_REPRODUCIBLE
            else:
                report["status"] = STATUS_UNDECLARED
                report["undeclared_drift"] = [
                    {
                        "column": "file_sha256",
                        "derived_value": _sha256_file(derived_path),
                        "committed_value": _sha256_file(target_path),
                        "rows": 1,
                    }
                ]
            return report
        return _compare_rows(
            report,
            derivation,
            _read_rows(derived_path),
            _read_rows(target_path),
        )


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

    if not source_path.is_file():
        if derivation.source_published:
            raise FileNotFoundError(
                f"published source missing for {relative}: {derivation.source}"
            )
        report["status"] = STATUS_PRIVATE_INPUT
        report["reason"] = (
            "The source is deliberately not published, so the derivation cannot be "
            "verified in this checkout.  It is verified wherever the "
            "non-published copy is present (locally), and its rules are covered "
            "by fixture tests unconditionally."
        )
        report["rows"] = {
            "derived": None,
            "committed": len(_read_rows(target_path)),
            "match": None,
        }
        report["discrepancies"] = []
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
        report["undeclared_drift"] = []
        report["stale_declarations"] = []
        return report

    if derivation.kind.startswith("platform-trends:"):
        return _reproduce_platform_trends(root, relative, derivation, report)
    if derivation.kind == "x-summary-anonymization":
        active = rules if rules is not None else load_content_rules(repo_root=root)
        derived = anonymize_rows(_read_rows(source_path), active)
    elif derivation.kind == "x-aggregate-monthly-coarse":
        from processing.aggregate_x import aggregate_coarse_monthly_rows

        source_rows = _read_rows(source_path)
        derived, _diagnostics = aggregate_coarse_monthly_rows(source_rows)
    elif derivation.kind == "youtube-monthly-search-results":
        source_rows = _read_rows(source_path)
        derived, _diagnostics = aggregate_youtube_rows(source_rows)
    else:  # pragma: no cover - registry is closed; guarded by tests
        raise ValueError(f"unknown derivation kind: {derivation.kind!r}")

    return _compare_rows(report, derivation, derived, _read_rows(target_path))


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
    withdrawn_entries: list[dict] = []
    withdrawn_errors: list[str] = []

    for relative, record in sorted(WITHDRAWN.items()):
        still_tracked = git_tracked(root, relative)
        if still_tracked:
            withdrawn_errors.append(relative)
        withdrawn_entries.append(
            {
                "artifact": relative,
                "status": STATUS_WITHDRAWN,
                "withdrawn_on": record.withdrawn_on,
                "reason": record.reason,
                "replacement": record.replacement,
                "exposure": record.exposure,
                "notes": list(record.notes),
                "tracked_again": still_tracked,
            }
        )

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
        counts[entry["status"]] += 1
        entries.append(entry)

    failures = [
        entry["artifact"]
        for entry in entries
        if entry["status"] == STATUS_UNDECLARED
    ]
    failures.extend(withdrawn_errors)

    return {
        "audit_version": AUDIT_VERSION,
        "root": str(root),
        "count": len(entries),
        "status_summary": dict(counts),
        "failure_count": len(failures),
        "failures": failures,
        "entries": entries,
        "withdrawn": withdrawn_entries,
    }
