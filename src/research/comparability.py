"""G7 \u00a78 cross-study comparability gate (CS01-CS13).

Contract source: ``docs/plans/20261013g.md`` \u00a78 (conditions, verdicts,
examples) and \u00a79 (reference semantics).

Reuse (no duplication): the measurement subset delegates to
``validation.comparability.compare_measurements`` and the run subset to
``validation.comparability.compare_runs``.  This module only adds the CS08-CS13
review layer and the entry-level orchestration.

Verdicts: ``comparable`` / ``conditional`` / ``not_comparable`` / ``unknown``
with reason codes (\u00a78.2).

When ``comparable`` is reachable (definition)
---------------------------------------------
All of CS01-CS07 pass on explicit identity fields AND all of the following
hold with recorded evidence:

- CS08 sampling method is declared on both sides;
- CS09 coverage is ``complete`` on both sides (coverage manifests supplied);
- CS10 missingness is explicit on both sides;
- CS11 normalization scale is identical and recorded (for Google Trends
  relative indices: same fetch group / comparison set);
- CS12 provenance resolves to run metadata + artifact manifests on both sides;
- CS13 both sides are publication-approved (or the purpose is internal
  review, recorded as ``internal_use``).

Legacy runs (the 29 frozen ``run_metadata.json`` files) carry no sampling /
coverage / normalization-scale / approval evidence, so on real repository data
the strongest verdict this gate returns is ``conditional``.  ``comparable`` is
implemented (and unit-tested with synthetic complete entries) but unreachable
on legacy data by construction -- returning it there would fabricate evidence
(AGENTS.md).  See ``COMPARABLE_EVIDENCE_NOTE``.
"""

from __future__ import annotations

from validation.comparability import compare_measurements as _compare_measurements

__all__ = [
    "COMPARABLE_EVIDENCE_NOTE",
    "CS_CONDITIONS",
    "check_cross_study_comparability",
    "check_measurement_pair",
]

#: G7 \u00a78.1 condition catalogue (ids + short labels).
CS_CONDITIONS = {
    "CS01": "compound corresponds",
    "CS02": "query intent corresponds",
    "CS03": "period corresponds",
    "CS04": "time axis corresponds",
    "CS05": "granularity corresponds",
    "CS06": "measurement semantics correspond",
    "CS07": "unit fits the comparison purpose",
    "CS08": "sampling method is explicit",
    "CS09": "coverage fits the comparison purpose",
    "CS10": "missingness is explicit",
    "CS11": "normalization is traceable",
    "CS12": "provenance is traceable",
    "CS13": "publication policy fits",
}

COMPARABLE_EVIDENCE_NOTE = (
    "comparable requires CS01-CS07 identity plus recorded evidence for "
    "CS08/CS09/CS10/CS11/CS12/CS13. Legacy runs lack that evidence, so the "
    "strongest verdict on repository data is conditional."
)

_COMPARABLE = "comparable"
_CONDITIONAL = "conditional"
_NOT_COMPARABLE = "not_comparable"
_UNKNOWN = "unknown"

#: Purposes modelled.  Anything else yields ``unknown`` instead of a verdict
#: under the wrong criteria (mirrors ``compare_runs``).
_DIRECT = ("", "direct_comparison")


def check_measurement_pair(a: dict, b: dict) -> dict:
    """Measurement-level gate for two measurement dicts (G7 \u00a79 pattern).

    Delegates to ``validation.comparability.compare_measurements`` (CS01/CS02
    subset + CS04-CS07 + GT scale rule) and returns a plain verdict dict.
    """
    result = _compare_measurements(a, b)
    return {
        "status": result.status,
        "reasons": list(result.reasons),
        "gate": "measurement_pair",
    }


def _overlap(a: dict, b: dict) -> set[str]:
    return set(a.get("compound_ids") or []) & set(b.get("compound_ids") or [])


def _fetch_group(entry: dict, term: str) -> tuple | None:
    """Fetch-group identity for a Google Trends term inside an entry.

    A relative index is only defined inside its fetch group: the query type,
    the co-fetched term set and the timeframe.  Single-term fetches and
    comparison fetches are different groups even for the same term (G7
    \u00a78.3: different comparison sets are not directly comparable).
    Returns ``None`` when the entry does not record enough to identify a
    group (never guessed).
    """
    for group in entry.get("terms") or []:
        if not isinstance(group, dict):
            continue
        terms = group.get("terms") or []
        if term not in terms:
            continue
        kind = group.get("type")
        timeframe = group.get("timeframe", entry.get("timeframe"))
        if not isinstance(kind, str) or not kind:
            return None
        return (kind, tuple(sorted(t for t in terms if isinstance(t, str))), timeframe)
    return None


def check_cross_study_comparability(a: dict, b: dict, *, purpose: str = "") -> dict:
    """Entry-level CS01-CS13 gate for two research-catalog entries.

    Read-only.  Returns ``{"status", "reasons", "checks"}`` where
    ``checks`` maps each CS id to ``{"result": pass/fail/review/unknown,
    "detail"}``.  ``comparable`` requires full evidence (see module
    docstring); legacy entries peak at ``conditional``.
    """
    checks: dict[str, dict] = {}

    def record(cs: str, result: str, detail: str):
        checks[cs] = {"result": result, "detail": detail}

    if not isinstance(a, dict) or not isinstance(b, dict):
        return {"status": _UNKNOWN, "reasons": ["insufficient_metadata"], "checks": checks}
    if purpose not in _DIRECT:
        return {"status": _UNKNOWN, "reasons": ["unsupported_comparison_purpose"], "checks": checks}

    hard: list[str] = []
    review: list[str] = []

    # -- CS01 compound -----------------------------------------------------
    compounds_a = set(a.get("compound_ids") or [])
    compounds_b = set(b.get("compound_ids") or [])
    if not compounds_a or not compounds_b:
        record("CS01", "unknown", "compound linkage absent on at least one side")
        return {"status": _UNKNOWN, "reasons": ["compound_link_unknown"], "checks": checks}
    shared = compounds_a & compounds_b
    if not shared:
        record("CS01", "fail", f"disjoint compounds {sorted(compounds_a)} vs {sorted(compounds_b)}")
        hard.append("cs01_compound_mismatch")
    else:
        record("CS01", "pass", f"shared compound(s): {sorted(shared)}")

    # -- CS02 intent --------------------------------------------------------
    intents_a = set(a.get("intent_ids") or [])
    intents_b = set(b.get("intent_ids") or [])
    if intents_a and intents_b:
        if intents_a & intents_b:
            record("CS02", "pass", f"shared intent(s): {sorted(intents_a & intents_b)}")
        else:
            record("CS02", "fail", f"intent mismatch {sorted(intents_a)} vs {sorted(intents_b)}")
            hard.append("cs02_intent_mismatch")
    else:
        record("CS02", "review", "intent not recorded on at least one side; review required")
        review.append("cs02_intent_review_required")

    # -- CS03 period --------------------------------------------------------
    timeframe_a, timeframe_b = a.get("timeframe"), b.get("timeframe")
    geo_a, geo_b = a.get("geo"), b.get("geo")
    if isinstance(timeframe_a, str) and isinstance(timeframe_b, str) and timeframe_a and timeframe_b:
        if timeframe_a != timeframe_b:
            record("CS03", "fail", f"timeframe {timeframe_a!r} vs {timeframe_b!r}")
            hard.append("cs03_period_mismatch")
        elif geo_a != geo_b:
            record("CS03", "fail", f"geo {geo_a!r} vs {geo_b!r}")
            hard.append("cs03_geo_mismatch")
        else:
            record("CS03", "pass", f"same timeframe {timeframe_a!r} geo {geo_a!r}")
            if a.get("collection_timestamp") != b.get("collection_timestamp"):
                review.append("cs03_collection_time_offset_review_required")
    else:
        record("CS03", "unknown", "observation period not recorded")
        return {"status": _UNKNOWN, "reasons": ["period_unknown"], "checks": checks}
    if hard:
        return {"status": _NOT_COMPARABLE, "reasons": sorted(hard), "checks": checks}

    # -- CS04 time axis ------------------------------------------------------
    axis_a, axis_b = a.get("time_axis"), b.get("time_axis")
    if axis_a is not None or axis_b is not None:
        if axis_a != axis_b:
            record("CS04", "fail", f"time axis {axis_a!r} vs {axis_b!r}")
            return {"status": _NOT_COMPARABLE, "reasons": ["cs04_time_axis_mismatch"], "checks": checks}
        record("CS04", "pass", f"time axis {axis_a!r}")
    else:
        record("CS04", "review", "time axis not declared; review required")
        review.append("cs04_time_axis_review_required")

    # -- CS05 granularity ----------------------------------------------------
    gran_a, gran_b = a.get("granularity"), b.get("granularity")
    if gran_a is not None or gran_b is not None:
        if gran_a != gran_b:
            record("CS05", "fail", f"granularity {gran_a!r} vs {gran_b!r}")
            return {"status": _NOT_COMPARABLE, "reasons": ["cs05_granularity_mismatch"], "checks": checks}
        record("CS05", "pass", f"granularity {gran_a!r}")
    else:
        record("CS05", "review", "granularity not declared; review required")
        review.append("cs05_granularity_review_required")

    # -- CS06 measurement semantics ------------------------------------------
    meas_a, meas_b = a.get("measurement_id"), b.get("measurement_id")
    if meas_a and meas_b:
        if meas_a != meas_b:
            record("CS06", "fail", f"measurement {meas_a!r} vs {meas_b!r}")
            return {"status": _NOT_COMPARABLE, "reasons": ["cs06_measurement_mismatch"], "checks": checks}
        record("CS06", "pass", f"measurement {meas_a!r}")
    else:
        record("CS06", "unknown", "measurement not recorded")
        return {"status": _UNKNOWN, "reasons": ["measurement_unknown"], "checks": checks}

    # -- CS07 unit ------------------------------------------------------------
    unit_a, unit_b = a.get("unit"), b.get("unit")
    if unit_a is not None and unit_b is not None and unit_a != unit_b:
        record("CS07", "fail", f"unit {unit_a!r} vs {unit_b!r}")
        return {"status": _NOT_COMPARABLE, "reasons": ["cs07_unit_mismatch"], "checks": checks}
    if unit_a is None or unit_b is None:
        record("CS07", "review", "unit not recorded on at least one side")
        review.append("cs07_unit_review_required")
    else:
        record("CS07", "pass", f"unit {unit_a!r}")

    # -- CS11 normalization (before CS08-CS10 so scale refusal precedes reviews)
    relative_units = {"relative_index_0_100"}
    if unit_a in relative_units or unit_b in relative_units:
        # Compare fetch groups only over shared linked terms; entries without
        # a recorded group for the shared term cannot prove traceability.
        # Same group re-fetched under a new run stays on the conditional track:
        # re-fetch instability is a quantified review item (repeat_diff
        # practice), unlike different comparison sets, which are refused.
        group_ok: bool | None = None
        group_detail = ""
        shared_terms: set[str] = set()
        for group in (a.get("terms") or []):
            if isinstance(group, dict):
                shared_terms.update(group.get("terms") or [])
        terms_b: set[str] = set()
        for group in (b.get("terms") or []):
            if isinstance(group, dict):
                terms_b.update(group.get("terms") or [])
        for term in sorted(shared_terms & terms_b):
            group_a = _fetch_group(a, term)
            group_b = _fetch_group(b, term)
            if group_a is None or group_b is None:
                group_ok = None
                group_detail = f"fetch group not traceable for term {term!r}"
                break
            if group_a != group_b:
                group_ok = False
                group_detail = (
                    f"different normalization groups for term {term!r}: "
                    f"{list(group_a)!r} vs {list(group_b)!r}"
                )
                break
            group_ok = True
            group_detail = f"shared normalization group for term {term!r}: {list(group_a)!r}"
        if group_ok is False:
            record("CS11", "fail", group_detail)
            return {"status": _NOT_COMPARABLE, "reasons": ["cs11_normalization_scale_mismatch"], "checks": checks}
        if group_ok is None:
            # Explicit scale evidence supplied by the caller (synthetic
            # complete entries / future manifests) still counts.
            if a.get("normalization_scale") and a.get("normalization_scale") == b.get("normalization_scale"):
                record("CS11", "pass", f"declared shared scale {a.get('normalization_scale')!r}")
            else:
                record("CS11", "review", group_detail or "normalization scale not traceable")
                review.append("cs11_normalization_review_required")
        else:
            record("CS11", "pass", group_detail)
            if a.get("run_id") != b.get("run_id"):
                review.append("cs11_renormalization_instability_review_required")
    else:
        record("CS11", "pass", "non-relative unit; no scale tracking required")

    # -- CS08 sampling --------------------------------------------------------
    sampling_a, sampling_b = a.get("sampling"), b.get("sampling")
    if sampling_a and sampling_b:
        record("CS08", "pass", f"sampling {sampling_a!r} / {sampling_b!r}")
    else:
        record("CS08", "review", "sampling method not explicit")
        review.append("cs08_sampling_review_required")

    # -- CS09 coverage ---------------------------------------------------------
    coverage_a, coverage_b = a.get("coverage"), b.get("coverage")
    if coverage_a == "complete" and coverage_b == "complete":
        record("CS09", "pass", "coverage complete on both sides")
    elif coverage_a == "missing" or coverage_b == "missing":
        record("CS09", "fail", f"coverage missing ({coverage_a!r} / {coverage_b!r})")
        return {"status": _NOT_COMPARABLE, "reasons": ["cs09_coverage_missing"], "checks": checks}
    elif coverage_a == "partial" or coverage_b == "partial":
        record("CS09", "review", f"partial coverage ({coverage_a!r} / {coverage_b!r})")
        review.append("cs09_coverage_partial")
    else:
        record("CS09", "review", "coverage not evidenced")
        review.append("cs09_coverage_review_required")

    # -- CS10 missingness -------------------------------------------------------
    missing_a, missing_b = a.get("missingness"), b.get("missingness")
    if missing_a and missing_b:
        record("CS10", "pass", f"missingness {missing_a!r} / {missing_b!r}")
    else:
        record("CS10", "review", "missingness not explicit")
        review.append("cs10_missingness_review_required")

    # -- CS12 provenance --------------------------------------------------------
    manifest_a, manifest_b = a.get("artifact_id"), b.get("artifact_id")
    if a.get("run_id") and b.get("run_id"):
        if manifest_a and manifest_b:
            record("CS12", "pass", "run + artifact manifest on both sides")
        else:
            record("CS12", "review", "run metadata only; artifact manifest absent")
            review.append("cs12_provenance_partial")
    else:
        record("CS12", "unknown", "run identity absent")
        return {"status": _UNKNOWN, "reasons": ["provenance_unknown"], "checks": checks}

    # -- CS13 publication --------------------------------------------------------
    approved = {"public", "approved"}
    avail_a, avail_b = a.get("availability"), b.get("availability")
    # CS13 is judged strictly: comparing private artifacts is permitted
    # internally, but any release of the comparison needs approval, so
    # non-approved availability always carries a review reason (G6 precedent:
    # processed-public-candidate is conditional, never silently public).
    if avail_a in approved and avail_b in approved:
        record("CS13", "pass", f"availability {avail_a!r} / {avail_b!r}")
    else:
        record("CS13", "review", f"availability {avail_a!r} / {avail_b!r}; internal comparison only")
        review.append("cs13_publication_review_required")

    if review:
        return {"status": _CONDITIONAL, "reasons": sorted(set(review)), "checks": checks}
    return {"status": _COMPARABLE, "reasons": ["all_cs_conditions_satisfied"], "checks": checks}
