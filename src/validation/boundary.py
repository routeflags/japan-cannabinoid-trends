"""Relative-timeframe boundary evidence and the `exact` promotion rule.

Contract: ``docs/specs/gt-boundary-verification.md`` (ISS-20261015-GT-001).

This module is the read-only *analysis* side of the boundary-measurement
protocol.  It extracts, per run, the collected relative timeframe, its
reference time, the nominal resolution (``validation.windows``) and the
observed bucket labels, and classifies the correspondence:

- ``consistent`` - the first observed bucket label and the last bucket end
  are both within one weekly bucket (``WINDOW_MATCH_TOLERANCE``) of the
  nominal resolution;
- ``inconsistent`` - outside that tolerance;
- ``insufficient_evidence`` - a missing / failed / empty record (a missing
  observation is never treated as an observed zero).

Rows carry an ``evidence_class``:

- ``measurement`` - the run declares the measurement protocol marker
  (``environment.measurement.protocol``); only these feed the promotion rule;
- ``recorded_contract`` - a current-contract run without the marker;
- ``recorded_legacy`` - a pre-contract recorded run (e.g. the 2026-10-12 5y
  run).  Its reference is the session-recorded collection timestamp and the
  label transformation epoch is not guaranteed, so it corroborates but never
  promotes.

``evaluate_promotion_rule`` states the rule mechanically (spec §3): every
registered relative timeframe needs at least two consistent measurement runs
whose reference times span at least seven days, with no failed run in the
cohort.  The rule is evaluated, never applied: promotion is a separate
reviewed change (spec §6).  Nothing in this module writes any file.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from math import gcd
from pathlib import Path

from validation.coverage import scan_run_directory
from validation.windows import (
    RELATIVE_TIMEFRAME_MODELS,
    WINDOW_MATCH_TOLERANCE,
    parse_datetime,
    resolve_relative_timeframe,
)

__all__ = [
    "BOUNDARY_REPORT_VERSION",
    "MEASUREMENT_PROTOCOL_ID",
    "RAW_ARTIFACT_NAME",
    "MEASUREMENT_RAW_SCHEMA_ID",
    "build_boundary_report",
    "evaluate_promotion_rule",
    "scan_boundary_rows",
]

BOUNDARY_REPORT_VERSION = "1.0.0"

#: The protocol marker a measurement run declares in
#: ``environment.measurement.protocol`` (contract with the staging tooling in
#: ``collection.adapters.google_trends.boundary``).
MEASUREMENT_PROTOCOL_ID = "gt-boundary-verification@1"

#: Verbatim MCP tool result file a measurement run carries (R5 evidence).
RAW_ARTIFACT_NAME = "mcp-tool-result.json"

#: Registered artifact schema of that file.
MEASUREMENT_RAW_SCHEMA_ID = "google-trends-mcp-tool-result-v1"

RUN_METADATA_NAME = "run_metadata.json"
ARTIFACT_MANIFEST_NAME = "artifact-manifest.json"
_DEFAULT_TIMEZONE = "UTC"

#: Allowed label steps: Google Trends serves daily points (short lookbacks) or
#: weekly points (Sunday start); anything else is irregular and cannot anchor a
#: boundary comparison.
_ALLOWED_LABEL_STEPS = (1, 7)


# ---------------------------------------------------------------------------
# evidence extraction
# ---------------------------------------------------------------------------


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _display_path(metadata_path: Path, root: Path) -> str:
    """Repository-relative display path (location-independent report)."""
    for base in (root.parent, root):
        try:
            return str(metadata_path.relative_to(base))
        except ValueError:
            continue
    return metadata_path.name


def _timeframe_candidates(document: dict, scan: dict) -> set[str]:
    candidates: set[str] = set()
    provenance = document.get("temporal_provenance")
    if isinstance(provenance, dict):
        submitted = provenance.get("submitted_parameters")
        if isinstance(submitted, dict) and isinstance(submitted.get("timeframe"), str):
            candidates.add(submitted["timeframe"])
    queries = document.get("queries")
    if isinstance(queries, list):
        for item in queries:
            if isinstance(item, dict) and isinstance(item.get("timeframe"), str):
                candidates.add(item["timeframe"])
    for value, _source in scan.get("timeframe_hints") or ():
        if isinstance(value, str):
            candidates.add(value)
    return candidates


def _reference(document: dict, scan: dict):
    provenance = document.get("temporal_provenance")
    if isinstance(provenance, dict) and isinstance(provenance.get("reference_time"), str):
        return provenance["reference_time"], "temporal_provenance.reference_time"
    if isinstance(document.get("collection_timestamp"), str):
        return document["collection_timestamp"], "run_metadata.collection_timestamp"
    for value, source in scan.get("reference_hints") or ():
        if isinstance(value, str):
            return value, f"payload.{source}"
    return None, None


def _observed(scan: dict):
    """Observed bucket labels and the bucket step.

    ``first`` / ``last`` are the run's min / max labels; ``span_days`` is the
    bucket step estimated as the greatest common divisor of the observed
    label gaps (7 for weekly data, 1 for daily data; a missing week does not
    change it), used to estimate the last bucket's end.  ``None`` means no
    observation - never zero.
    """
    terms = scan.get("terms") or {}
    first = None
    last = None
    step = 0
    for entry in terms.values():
        if not isinstance(entry, dict):
            continue
        minimum = entry.get("min_label")
        maximum = entry.get("max_label")
        if isinstance(minimum, str) and (first is None or minimum < first):
            first = minimum
        if isinstance(maximum, str) and (last is None or maximum > last):
            last = maximum
        for gap in entry.get("gaps") or ():
            if isinstance(gap, int) and gap > 0:
                step = gap if step == 0 else gcd(step, gap)
    return first, last, (step or None)


def _raw_artifact_present(run_dir: Path):
    """True/False when a manifest can adjudicate R5, else None."""
    manifest = _load_json(run_dir / ARTIFACT_MANIFEST_NAME)
    artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(artifacts, list):
        return None
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        if (
            artifact.get("path") == RAW_ARTIFACT_NAME
            or artifact.get("schema_id") == MEASUREMENT_RAW_SCHEMA_ID
        ):
            path = artifact.get("path")
            return bool(isinstance(path, str) and (run_dir / path).is_file())
    return False


def _days_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 86400.0


def _label_moment(label: str) -> datetime:
    return datetime.fromisoformat(label).replace(tzinfo=timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _row_for_run(run_dir: Path, *, display_root: Path) -> tuple[dict | None, str | None]:
    """Build one report row; ``(None, reason)`` when the run is out of scope."""
    document = _load_json(run_dir / RUN_METADATA_NAME)
    if not isinstance(document, dict):
        return {
            "run_id": None,
            "path": _display_path(run_dir / RUN_METADATA_NAME, display_root),
            "evidence_class": "unreadable",
            "verdict": "insufficient_evidence",
            "reasons": ["run_metadata_unreadable"],
        }, None

    scan = scan_run_directory(run_dir)
    candidates = _timeframe_candidates(document, scan)
    if not candidates:
        return None, "no_relative_timeframe"
    registered = sorted(
        candidate for candidate in candidates if candidate in RELATIVE_TIMEFRAME_MODELS
    )

    provenance = document.get("temporal_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    execution = document.get("execution")
    execution = execution if isinstance(execution, dict) else {}
    environment = document.get("environment")
    environment = environment if isinstance(environment, dict) else {}
    measurement = environment.get("measurement")
    measurement = measurement if isinstance(measurement, dict) else {}
    is_measurement = measurement.get("protocol") == MEASUREMENT_PROTOCOL_ID
    if is_measurement:
        evidence_class = "measurement"
    elif provenance.get("reference_time"):
        evidence_class = "recorded_contract"
    else:
        evidence_class = "recorded_legacy"

    row = {
        "run_id": document.get("run_id"),
        "path": _display_path(run_dir / RUN_METADATA_NAME, display_root),
        "source_id": document.get("source_id"),
        "collector_id": (
            document.get("collector").get("collector_id")
            if isinstance(document.get("collector"), dict)
            else None
        ),
        "evidence_class": evidence_class,
        "measurement_protocol": MEASUREMENT_PROTOCOL_ID if is_measurement else None,
        "execution_status": execution.get("status"),
        "window_id": provenance.get("window_id"),
        "requested_start": provenance.get("requested_start"),
        "requested_end_exclusive": provenance.get("requested_end_exclusive"),
        "timeframe": registered[0] if len(registered) == 1 else None,
        "timeframe_candidates": sorted(candidates),
        "reference_time": None,
        "reference_source": None,
        "timezone": provenance.get("timezone") or _DEFAULT_TIMEZONE,
        "timezone_source": "plan" if provenance.get("timezone") else "default_utc",
        "nominal_start": None,
        "nominal_end_exclusive": None,
        "observed_first": None,
        "observed_last": None,
        "observed_end_exclusive": None,
        "first_offset_days": None,
        "last_end_offset_days": None,
        "raw_artifact_present": _raw_artifact_present(run_dir),
        "verdict": "insufficient_evidence",
        "reasons": [],
    }

    if execution.get("status") == "failed":
        row["reasons"].append("collection_failed")
        return row, None
    if len(registered) != 1:
        row["reasons"].append(
            "ambiguous_timeframes" if registered else "unregistered_timeframe"
        )
        return row, None

    timeframe = registered[0]
    reference, reference_source = _reference(document, scan)
    row["reference_time"] = reference
    row["reference_source"] = reference_source
    if reference is None:
        row["reasons"].append("reference_missing")
        return row, None
    try:
        reference_moment = parse_datetime(reference)
        nominal_start, nominal_end = resolve_relative_timeframe(
            timeframe, reference_moment, row["timezone"]
        )
    except ValueError:
        row["reasons"].append("reference_invalid")
        return row, None
    row["nominal_start"] = _iso(nominal_start)
    row["nominal_end_exclusive"] = _iso(nominal_end)

    first, last, span_days = _observed(scan)
    if first is None or last is None:
        row["reasons"].append("no_series_observed")
        return row, None
    if not isinstance(span_days, int) or span_days <= 0:
        row["reasons"].append("label_gap_unknown")
        return row, None
    if span_days not in _ALLOWED_LABEL_STEPS:
        row["reasons"].append("irregular_label_step")
        row["label_step_days"] = span_days
        return row, None
    row["observed_first"] = first
    row["observed_last"] = last
    try:
        first_moment = _label_moment(first)
        last_moment = _label_moment(last)
    except ValueError:
        row["reasons"].append("label_invalid")
        return row, None
    last_end = last_moment + timedelta(days=span_days)
    row["observed_end_exclusive"] = _iso(last_end)
    first_offset = _days_between(nominal_start, first_moment)
    last_end_offset = _days_between(nominal_end, last_end)
    tolerance_days = WINDOW_MATCH_TOLERANCE.total_seconds() / 86400.0
    row["first_offset_days"] = round(first_offset, 3)
    row["last_end_offset_days"] = round(last_end_offset, 3)
    if abs(first_offset) <= tolerance_days and abs(last_end_offset) <= tolerance_days:
        row["verdict"] = "consistent"
    else:
        row["verdict"] = "inconsistent"
        row["reasons"].append("offset_outside_one_weekly_bucket")
    return row, None


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def _study_of(metadata_path: Path, root: Path) -> str | None:
    """Study id, i.e. the first path component under the datasets root."""
    try:
        return metadata_path.relative_to(root).parts[0]
    except (ValueError, IndexError):
        return None


def scan_boundary_rows(datasets_root, *, study=None, run=None) -> list[dict]:
    """Build report rows for the runs under ``datasets_root`` (or one run)."""
    root = Path(datasets_root)
    if run is not None:
        targets = [Path(run)]
    else:
        targets = sorted(root.glob("**/" + RUN_METADATA_NAME)) if root.is_dir() else []
        if study:
            targets = [
                path for path in targets if _study_of(path, root) == study
            ]
    rows = []
    for target in targets:
        run_dir = target if target.is_dir() else target.parent
        row, _excluded = _row_for_run(run_dir, display_root=root)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda row: (str(row.get("run_id")), str(row.get("path"))))
    return rows


def _cohort(rows) -> list[dict]:
    return [row for row in rows if row.get("evidence_class") == "measurement"]


def evaluate_promotion_rule(
    rows,
    *,
    required_timeframes=None,
    min_runs_per_timeframe: int = 2,
    min_reference_days: int = 2,
    min_reference_span_days: int = 7,
) -> dict:
    """Evaluate the promotion rule over report rows (spec §3).  Read-only.

    Only ``measurement`` rows participate.  The rule needs, per registered
    timeframe, at least ``min_runs_per_timeframe`` consistent successful runs
    with a present raw artifact whose reference times cover
    ``min_reference_days`` distinct UTC days and span at least
    ``min_reference_span_days``; no failed run may sit in the cohort.
    Returns the condition-by-condition verdict.
    """
    required = tuple(required_timeframes or RELATIVE_TIMEFRAME_MODELS)
    cohort = _cohort(rows)
    timeframes = {}
    for timeframe in required:
        entries = [row for row in cohort if row.get("timeframe") == timeframe]
        consistent = [
            row
            for row in entries
            if row.get("verdict") == "consistent"
            and row.get("execution_status") == "success"
            and row.get("raw_artifact_present") is True
        ]
        # R2 counts *runs*, not rows: two rows sharing a run_id are one run and
        # must not satisfy the two-run minimum on their own.
        by_run_id: dict[str, dict] = {}
        for row in consistent:
            by_run_id.setdefault(str(row.get("run_id")), row)
        consistent = list(by_run_id.values())
        days = sorted(
            {row["reference_time"][:10] for row in consistent if row.get("reference_time")}
        )
        span_days = None
        if len(days) >= 2:
            first_day = datetime.fromisoformat(days[0]).replace(tzinfo=timezone.utc)
            last_day = datetime.fromisoformat(days[-1]).replace(tzinfo=timezone.utc)
            span_days = _days_between(first_day, last_day)
        reasons = []
        if len(consistent) < min_runs_per_timeframe:
            reasons.append("insufficient_consistent_runs")
        if len(days) < min_reference_days:
            reasons.append("insufficient_reference_days")
        if span_days is None or span_days < min_reference_span_days:
            reasons.append("reference_span_below_minimum")
        timeframes[timeframe] = {
            "runs": len(entries),
            "consistent_runs": len(consistent),
            "consistent_run_ids": sorted(str(row.get("run_id")) for row in consistent),
            "reference_days": days,
            "reference_span_days": span_days,
            "satisfied": not reasons,
            "reasons": reasons,
        }

    failed = [
        row
        for row in cohort
        if row.get("verdict") == "insufficient_evidence"
        and "collection_failed" in (row.get("reasons") or [])
    ]

    reasons = []
    for timeframe, verdict in timeframes.items():
        if not verdict["satisfied"]:
            reasons.append(f"timeframe_not_satisfied:{timeframe}")
    if failed:
        reasons.append("failed_run_in_cohort")

    return {
        "protocol": MEASUREMENT_PROTOCOL_ID,
        "required_timeframes": list(required),
        "min_runs_per_timeframe": min_runs_per_timeframe,
        "min_reference_days": min_reference_days,
        "min_reference_span_days": min_reference_span_days,
        "cohort_run_count": len(cohort),
        "cohort_run_ids": sorted(str(row.get("run_id")) for row in cohort),
        "failed_run_ids": sorted(str(row.get("run_id")) for row in failed),
        "timeframes": timeframes,
        "eligible": not reasons,
        "reasons": reasons,
    }


def build_boundary_report(datasets_root, *, study=None, run=None) -> dict:
    """Assemble the correspondence table plus the promotion-rule evaluation."""
    rows = scan_boundary_rows(datasets_root, study=study, run=run)
    return {
        "boundary_report_version": BOUNDARY_REPORT_VERSION,
        "protocol": MEASUREMENT_PROTOCOL_ID,
        "datasets_root": str(datasets_root),
        "study": study,
        "rows": rows,
        "row_count": len(rows),
        "measurement_row_count": len(_cohort(rows)),
        "rule": evaluate_promotion_rule(rows),
    }
