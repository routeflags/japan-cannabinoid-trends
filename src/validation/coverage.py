"""G3 coverage validation + legacy temporal inventory (c.md §9, §11, §15).

Contract sources
----------------
- G3 §9 (coverage types / status / manifest), §11 (missingness contract),
  §15 (audit of existing runs): ``docs/plans/20261013c.md``.

Design notes
------------
- The four coverage types of §9.1 are kept apart: ``requested`` (study
  window), ``collector`` (the period the collector specification searches,
  nominal resolution only), ``observed`` (bucket labels actually present in
  the payload), ``verified`` (never fabricated — empty until verification
  evidence exists).
- Missingness (P7): a Google Trends zero *point* is never classified
  ``observed_zero``; a platform no-data response is ``below_threshold``
  (treated as missing for aggregation, matching
  ``docs/collection-gap-analysis.md`` §3.5); collection failures are
  ``collection_failed`` / status ``missing``.  Only a completed, exactly
  resolved search with observed bounds covering the requested window may be
  reported ``complete``.
- ``partial`` is the honest terminal state for rolling relative windows:
  data was returned, but the boundary semantics are unverified, so coverage
  of the *requested absolute window* cannot be asserted.
- The legacy inventory (§15) extracts facts only.  It intentionally does
  **not** convert old relative timeframes into absolute windows
  (``resolved_absolute_window: null``) — that would be a retroactive guess
  (P1, AGENTS.md).

Read-only: nothing in this module writes any file.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from validation.integrity import sha256_file
from validation.windows import (
    RELATIVE_TIMEFRAME_MODELS,
    WINDOW_MATCH_TOLERANCE,
    parse_datetime,
    resolve_relative_timeframe,
)

__all__ = [
    "COVERAGE_VERSION",
    "build_temporal_inventory",
    "evaluate_coverage",
    "scan_run_directory",
]

COVERAGE_VERSION = "1.0.0"

#: Metadata files inside a run directory that are not payload evidence.
_NON_PAYLOAD_FILES = frozenset(
    {"run_metadata.json", "artifact-manifest.json", "quarantine-reason.json"}
)

#: Consecutive label gaps longer than this are reported (c.md §14 G3-T13:
#: a blank month stays blank; it is never padded with zeroes).
_LABEL_GAP_DAYS = 31

#: Field names that may record a retrieval / pagination limit (§15).
_LIMIT_FIELDS = (
    "max_pages",
    "limit",
    "max_results",
    "maxItems",
    "maxResults",
    "resultsLimit",
)


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _iso_label(value: str) -> str:
    return f"{value}T00:00:00Z"


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def scan_run_directory(run_dir) -> dict:
    """Best-effort, read-only evidence extraction from a run directory.

    Recognized payload shapes are the recorded ones of the current
    collectors: a single-term series ``{keyword, data: [{date, value}]}``, a
    comparison series ``{data: [{date, <term>: value, ...}]}`` and a no-data
    record ``{no_data_keywords: [{keyword, status, note}]}``.  Unknown shapes
    are ignored, never guessed at.
    """
    path = Path(run_dir)
    result = {
        "files": [],
        "terms": {},
        "timeframe_hints": [],
        "reference_hints": [],
        "no_data_terms": {},
        "limits": [],
    }
    for file in sorted(path.glob("*.json")):
        if file.name in _NON_PAYLOAD_FILES:
            continue
        document = _read_json(file)
        result["files"].append(file.name)
        if not isinstance(document, dict):
            continue
        if isinstance(document.get("timeframe"), str):
            result["timeframe_hints"].append((document["timeframe"], file.name))
        for key in ("collected_at", "collected_on", "collection_date"):
            if isinstance(document.get(key), str):
                result["reference_hints"].append((document[key], file.name))
        for key in _LIMIT_FIELDS:
            if key in document:
                result["limits"].append((key, document[key], file.name))

        data = document.get("data")
        keyword = document.get("keyword")
        if isinstance(data, list):
            if data and all(isinstance(point, dict) and "date" in point for point in data):
                point_keys = [key for key in data[0] if key != "date"]
                if "value" in point_keys and isinstance(keyword, str):
                    _accumulate_term(result["terms"], keyword, data, "value", file.name)
                else:
                    for term_key in point_keys:
                        if term_key != "value":
                            _accumulate_term(result["terms"], term_key, data, term_key, file.name)
            elif isinstance(keyword, str):
                # A successful response carrying an empty series registers the
                # term without points; the state stays ``unknown`` unless
                # platform evidence says otherwise (P7: no invented zero).
                _touch_term(result["terms"], keyword, file.name)
        for item in document.get("no_data_keywords") or []:
            if isinstance(item, dict) and isinstance(item.get("keyword"), str):
                result["no_data_terms"][item["keyword"]] = {
                    "status": item.get("status"),
                    "note": item.get("note"),
                    "source": file.name,
                }
    return result


def _touch_term(terms: dict, name: str, source: str) -> None:
    term = terms.setdefault(
        name,
        {
            "points": 0,
            "zeros": 0,
            "nonzero": 0,
            "min_label": None,
            "max_label": None,
            "sources": [],
            "gaps": [],
        },
    )
    if source not in term["sources"]:
        term["sources"].append(source)


def _accumulate_term(terms: dict, name: str, data: list, key: str, source: str) -> None:
    _touch_term(terms, name, source)
    term = terms[name]
    labels = []
    for point in data:
        label = point.get("date")
        if not isinstance(label, str):
            continue
        value = point.get(key)
        if value is None:
            continue
        term["points"] += 1
        labels.append(label)
        if isinstance(value, (int, float)) and value == 0:
            term["zeros"] += 1
        elif value != 0:
            term["nonzero"] += 1
    for label in labels:
        if term["min_label"] is None or label < term["min_label"]:
            term["min_label"] = label
        if term["max_label"] is None or label > term["max_label"]:
            term["max_label"] = label
    try:
        dates = sorted(datetime.fromisoformat(label) for label in labels)
    except ValueError:
        dates = []
    term["gaps"].extend(
        (dates[index + 1] - dates[index]).days for index in range(len(dates) - 1)
    )


def _finalize_states(scan: dict, *, execution_failed: bool) -> dict:
    """Compute per-term missingness states (§11) from the raw scan."""
    states = {}
    for name, term in scan["terms"].items():
        if execution_failed:
            state = "collection_failed"
        elif term["points"] == 0:
            state = "unknown"
        elif term["nonzero"] > 0:
            state = "observed_nonzero"
        else:
            # All points are zero: a Google Trends zero display is not an
            # observed zero (c.md §11); aggregation must treat it as missing.
            state = "below_threshold"
        states[name] = {
            "state": state,
            "point_count": term["points"],
            "zero_count": term["zeros"],
            "observed_min": _iso_label(term["min_label"]) if term["min_label"] else None,
            "observed_max": _iso_label(term["max_label"]) if term["max_label"] else None,
            "sources": list(term["sources"]),
            "gaps": list(term["gaps"]),
        }
    for name, evidence in scan["no_data_terms"].items():
        entry = states.setdefault(
            name,
            {
                "state": "unknown",
                "point_count": 0,
                "zero_count": 0,
                "observed_min": None,
                "observed_max": None,
                "sources": [],
                "gaps": [],
            },
        )
        if entry["point_count"] == 0 and not execution_failed:
            # Platform no-data evidence: below threshold is the documented
            # reading; an observed zero would be a fabrication (P7).
            entry["state"] = "below_threshold"
        if evidence.get("source") and evidence["source"] not in entry["sources"]:
            entry["sources"].append(evidence["source"])
        entry["platform_no_data"] = {
            key: evidence[key] for key in ("status", "note", "source") if evidence.get(key)
        }
    return states


def _max_label_gap(states: dict) -> int:
    max_gap = 0
    for entry in states.values():
        for gap in entry.get("gaps") or ():
            max_gap = max(max_gap, gap)
    return max_gap


def _public_states(states: dict) -> dict:
    public = {}
    for name, entry in states.items():
        item = {key: value for key, value in entry.items() if key != "gaps"}
        public[name] = item
    return public


def _observed_coverage(states: dict) -> dict | None:
    """Observed interval from bucket labels (nominal span, not verification)."""
    minimum = None
    maximum = None
    gaps = set()
    for entry in states.values():
        if entry["observed_min"] and (minimum is None or entry["observed_min"] < minimum):
            minimum = entry["observed_min"]
        if entry["observed_max"] and (maximum is None or entry["observed_max"] > maximum):
            maximum = entry["observed_max"]
        gaps.update(entry.get("gaps") or ())
    if minimum is None or maximum is None:
        return None
    coverage = {"start": minimum, "end_exclusive": None, "basis": "bucket_labels"}
    if gaps and len(gaps) == 1:
        span = timedelta(days=next(iter(gaps)))
        end = datetime.fromisoformat(maximum.replace("Z", "+00:00")) + span
        coverage["end_exclusive"] = _iso(end)
    return coverage


def _collector_coverage(provenance: dict) -> dict | None:
    """Nominal collector resolution from recorded provenance (new runs only)."""
    reference = provenance.get("reference_time")
    submitted = provenance.get("submitted_parameters")
    timeframe = submitted.get("timeframe") if isinstance(submitted, dict) else None
    timezone_name = provenance.get("timezone") or "UTC"
    if not isinstance(reference, str) or not isinstance(timeframe, str):
        return None
    if timeframe not in RELATIVE_TIMEFRAME_MODELS:
        return None
    try:
        start, end = resolve_relative_timeframe(timeframe, parse_datetime(reference), timezone_name)
    except ValueError:
        return None
    return {
        "start": _iso(start),
        "end_exclusive": _iso(end),
        "basis": "nominal_resolution",
        "timeframe": timeframe,
    }


def _covers(requested: dict, observed: dict) -> bool:
    if not observed.get("end_exclusive"):
        return False
    try:
        start = parse_datetime(requested["start"])
        end = parse_datetime(requested["end_exclusive"])
        observed_start = parse_datetime(observed["start"])
        observed_end = parse_datetime(observed["end_exclusive"])
    except (KeyError, ValueError, TypeError):
        return False
    return (
        observed_start <= start + WINDOW_MATCH_TOLERANCE
        and observed_end >= end - WINDOW_MATCH_TOLERANCE
    )


def evaluate_coverage(target) -> dict:
    """Evaluate coverage for one run directory / ``run_metadata.json``.

    Returns a §9.3-shaped manifest.  The evaluation never fails the caller:
    missing or contradictory evidence lowers the status, it is not replaced
    by an invented value.
    """
    path = Path(target)
    run_dir = path if path.is_dir() else path.parent
    metadata_path = run_dir / "run_metadata.json"

    manifest = {
        "coverage_version": COVERAGE_VERSION,
        "profile": "g3_coverage",
        "run_id": None,
        "target": str(target),
        "window_id": None,
        "coverage": {
            "requested": None,
            "requested_relative": None,
            "collector": None,
            "observed": None,
            "verified": None,
            "status": "unknown",
            "pagination_exhausted": None,
            "truncated": None,
            "verified_intervals": [],
            "missing_intervals": [],
            "unknown_intervals": [],
            "states": {},
            "reasons": [],
            "evidence": [],
        },
    }
    coverage = manifest["coverage"]

    document = _read_json(metadata_path) if metadata_path.is_file() else None
    if not isinstance(document, dict):
        coverage["reasons"] = ["run_metadata_missing"]
        return manifest

    manifest["run_id"] = document.get("run_id")
    provenance = document.get("temporal_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    execution = document.get("execution")
    if not isinstance(execution, dict):
        execution = {}

    scan = scan_run_directory(run_dir)
    coverage["evidence"] = ["run_metadata.json", *scan["files"]]

    requested = None
    if isinstance(provenance.get("requested_start"), str) and isinstance(
        provenance.get("requested_end_exclusive"), str
    ):
        requested = {
            "start": provenance["requested_start"],
            "end_exclusive": provenance["requested_end_exclusive"],
        }
    coverage["requested"] = requested
    manifest["window_id"] = provenance.get("window_id")

    # Relative request evidence (legacy runs): recorded verbatim, never
    # resolved into an absolute window (P1 / c.md §15 not-derived rule).
    timeframes = []
    for value, source in scan["timeframe_hints"]:
        if (value, source) not in timeframes:
            timeframes.append((value, source))
    if isinstance(document.get("timeframe"), str):
        timeframes.insert(0, (document["timeframe"], "run_metadata.json"))
    queries = document.get("queries")
    if isinstance(queries, list):
        for item in queries:
            if isinstance(item, dict) and isinstance(item.get("timeframe"), str):
                entry = (item["timeframe"], "run_metadata.json:queries")
                if entry not in timeframes:
                    timeframes.append(entry)
    references = []
    if isinstance(document.get("collection_timestamp"), str):
        references.append((document["collection_timestamp"], "run_metadata.json"))
    for value, source in scan["reference_hints"]:
        if (value, source) not in references:
            references.append((value, source))
    if timeframes and requested is None:
        coverage["requested_relative"] = {
            "timeframes": sorted({value for value, _ in timeframes}),
            "sources": sorted({source for _, source in timeframes}),
            "reference": references[0][0] if references else None,
            "reference_source": references[0][1] if references else None,
            "resolved_absolute_window": None,
            "resolution_note": "not derived: a relative legacy period is "
            "not a canonical absolute window (P1, c.md §15)",
        }
        coverage["reasons"].append("relative_window_not_resolved")

    if isinstance(execution.get("pagination_exhausted"), bool):
        coverage["pagination_exhausted"] = execution["pagination_exhausted"]
    exact_window_match = provenance.get("exact_window_match")

    execution_failed = execution.get("status") == "failed"
    states = _finalize_states(scan, execution_failed=execution_failed)
    max_gap = _max_label_gap(states)

    observed = _observed_coverage(states)
    if observed is None and isinstance(
        provenance.get("observed_min_timestamp"), str
    ) and isinstance(provenance.get("observed_max_timestamp"), str):
        observed = {
            "start": provenance["observed_min_timestamp"],
            "end_exclusive": None,
            "basis": "bucket_labels",
        }
    coverage["observed"] = observed
    coverage["collector"] = _collector_coverage(provenance)
    coverage["states"] = _public_states(states)

    reasons = list(coverage["reasons"])
    if any(entry["zero_count"] > 0 for entry in states.values()):
        reasons.append("zero_points_not_observed_zero")

    if execution_failed:
        status = "missing"
        reasons.append("collection_failed")
    elif any(entry["point_count"] > 0 for entry in states.values()):
        if coverage["pagination_exhausted"] is False:
            status = "partial"
            reasons.append("pagination_not_exhausted")
        elif (
            exact_window_match is True
            and coverage["pagination_exhausted"] is True
            and requested is not None
            and observed is not None
            and _covers(requested, observed)
        ):
            status = "complete"
            reasons.append("coverage_verified")
        else:
            status = "partial"
            reasons.append(
                "boundary_semantics_unverified"
                if exact_window_match is False
                else "coverage_not_verified"
            )
    elif any("platform_no_data" in entry for entry in states.values()):
        status = "missing"
        reasons.append("platform_no_data")
    elif states:
        status = "unknown"
        reasons.append("no_observations_no_evidence")
    else:
        status = "unknown"
        reasons.append("no_series_evidence")

    if max_gap > _LABEL_GAP_DAYS:
        reasons.append("label_gap_detected")
        coverage["label_gap_days"] = max_gap

    coverage["status"] = status
    if requested is not None:
        if status == "complete":
            coverage["verified_intervals"] = [requested]
        elif status == "partial":
            coverage["unknown_intervals"] = [requested]
        elif status == "missing":
            coverage["missing_intervals"] = [requested]
        elif status == "unknown":
            coverage["unknown_intervals"] = [requested]
    coverage["reasons"] = sorted(set(reasons))
    return manifest


# ---------------------------------------------------------------------------
# Legacy temporal inventory (c.md §15 / §16 Phase 1)
# ---------------------------------------------------------------------------


def _hash_run_files(run_dir: Path) -> dict:
    return {
        file.name: sha256_file(file)
        for file in sorted(run_dir.glob("*.json"))
    }


def _display_path(metadata_path: Path, root: Path) -> str:
    """Repository-relative display path (location-independent audit).

    ``datasets/x/run_metadata.json`` must be recorded the same whether the
    caller passed a relative or an absolute datasets root, so the audit can
    be recomputed from any checkout location.
    """
    for base in (root.parent, root):
        try:
            return str(metadata_path.relative_to(base))
        except ValueError:
            continue
    return str(metadata_path)


def build_temporal_inventory(datasets_root) -> dict:
    """Build the non-destructive §15 inventory of ``run_metadata.json`` files.

    Extracts what the runs themselves state (timeframe, reference datetime,
    observed labels, completeness/limit evidence) and classifies each run's
    period evidence as ``verified`` / ``inferred`` / ``ambiguous`` /
    ``unknown``.  The inventory never derives an absolute window from a
    relative period and re-hashes every touched file to prove raw immutability.
    """
    root = Path(datasets_root)
    targets = sorted(root.glob("**/run_metadata.json"))

    before_hashes = {}
    for metadata_path in targets:
        before_hashes[metadata_path] = _hash_run_files(metadata_path.parent)

    records = []
    classification_summary = {"verified": 0, "inferred": 0, "unknown": 0, "ambiguous": 0}
    for metadata_path in targets:
        run_dir = metadata_path.parent
        document = _read_json(metadata_path)
        if not isinstance(document, dict):
            document = {}
        scan = scan_run_directory(run_dir)

        timeframes = []
        if isinstance(document.get("timeframe"), str):
            timeframes.append((document["timeframe"], "run_metadata.json"))
        queries = document.get("queries")
        if isinstance(queries, list):
            for item in queries:
                if isinstance(item, dict) and isinstance(item.get("timeframe"), str):
                    entry = (item["timeframe"], "run_metadata.json:queries")
                    if entry not in timeframes:
                        timeframes.append(entry)
        for value, source in scan["timeframe_hints"]:
            entry = (value, source)
            if entry not in timeframes:
                timeframes.append(entry)

        references = []
        if isinstance(document.get("collection_timestamp"), str):
            references.append((document["collection_timestamp"], "run_metadata.json"))
        for value, source in scan["reference_hints"]:
            entry = (value, source)
            if entry not in references:
                references.append(entry)

        provenance = document.get("temporal_provenance")
        provenance = provenance if isinstance(provenance, dict) else {}
        has_absolute = isinstance(provenance.get("requested_start"), str) and isinstance(
            provenance.get("requested_end_exclusive"), str
        )
        distinct_timeframes = sorted({value for value, _ in timeframes})
        if has_absolute:
            classification = "verified"
        elif not distinct_timeframes:
            classification = "unknown"
        elif len(distinct_timeframes) > 1:
            classification = "ambiguous"
        elif not references:
            classification = "unknown"
        else:
            classification = "inferred"
        classification_summary[classification] += 1

        completeness = []
        for field_name in ("note", "zero_status", "anchor_terms", "rate_limit_429", "errors"):
            if field_name in document:
                completeness.append({"field": field_name, "source": "run_metadata.json"})
        for term, evidence in scan["no_data_terms"].items():
            completeness.append(
                {"field": f"no_data_keywords[{term}]", "source": evidence.get("source")}
            )
        for key, value, source in scan["limits"]:
            completeness.append({"field": key, "source": source})
        for key in _LIMIT_FIELDS:
            if key in document:
                completeness.append({"field": key, "source": "run_metadata.json"})

        observed = _observed_coverage(
            _finalize_states(scan, execution_failed=False)
        )
        pagination = None
        execution = document.get("execution")
        if isinstance(execution, dict) and isinstance(execution.get("pagination_exhausted"), bool):
            pagination = execution["pagination_exhausted"]

        records.append(
            {
                "run_id": document.get("run_id"),
                "path": _display_path(metadata_path, root),
                "sha256": before_hashes[metadata_path].get("run_metadata.json"),
                "timeframes": [
                    {"value": value, "source": source} for value, source in timeframes
                ],
                "reference": (
                    {"value": references[0][0], "source": references[0][1]}
                    if references
                    else None
                ),
                "observed_bounds": observed,
                "pagination": pagination,
                "completeness_evidence": completeness,
                "classification": classification,
                "resolved_absolute_window": None,
                "resolution_note": "not derived: conversion of legacy relative "
                "periods into absolute windows is prohibited (P1, c.md §15)",
            }
        )

    raw_modified = False
    for metadata_path in targets:
        after = _hash_run_files(metadata_path.parent)
        if after != before_hashes[metadata_path]:
            raw_modified = True

    return {
        "audit_version": "1.0.0",
        "profile": "g3_temporal_inventory",
        "spec": "docs/plans/20261013c.md \u00a715 (local plan; not tracked)",
        "target_glob": "datasets/**/run_metadata.json",
        "count": len(records),
        "raw_modified": raw_modified,
        "classification_summary": classification_summary,
        "runs": records,
    }
