"""Comparability gates (Phase 4, P4-8).

Contract sources
----------------
- G1 §12 (L2 research comparability), G3 §12 (temporal comparability gate),
  G7 §8 (cross-study comparability gate): ``docs/plans/20261013a.md``,
  ``20261013c.md``, ``20261013g.md``.

Design notes
------------
- Results carry reason codes (c.md §12.2: "L2の判定結果には、理由コードを
  必ず保存する").
- ``comparable`` is intentionally *not* produced by the current gates: it
  requires coverage / sampling / publication checks that are not yet
  modelled (G7 CS06-CS13).  The strongest outcome available today is
  ``conditional``, exactly as the g.md §9 reference code returns for matching
  datasets.  This is recorded in ``docs/specs/validation-framework.md``.
- ``unknown`` is returned instead of guessing when required metadata is
  absent (AGENTS.md: no fabrication of missing values).
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "ComparabilityResult",
    "compare_measurements",
    "compare_temporal_windows",
]

_COMPARABLE = "comparable"
_CONDITIONAL = "conditional"
_NOT_COMPARABLE = "not_comparable"
_UNKNOWN = "unknown"


@dataclass
class ComparabilityResult:
    status: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"status": self.status, "reasons": list(self.reasons)}


# ---------------------------------------------------------------------------
# G7 §9 / §8.3: measurement comparability
# ---------------------------------------------------------------------------

_MEASUREMENT_KEYS = (
    "compound_id",
    "granularity",
    "measurement_id",
)


def _get_measurement_field(measurement: dict, key: str):
    if key == "intent":
        return measurement.get("query_intent", measurement.get("intent_id"))
    if key == "time_axis":
        return measurement.get("time_axis", measurement.get("time_axis_id"))
    return measurement.get(key)


def compare_measurements(a: dict, b: dict) -> ComparabilityResult:
    """G7 §8 gate (CS01-CS08 subset) / g.md §9 reference semantics.

    - missing identity fields -> ``unknown`` (insufficient metadata);
    - compound / intent / granularity / time axis / measurement / unit
      mismatch -> ``not_comparable`` with reason codes;
    - Google Trends relative index requires the same normalization scale
      (comparison set) on both sides, otherwise direct comparison is
      refused (g.md §8.3: "GT異なる比較セットは原則として直接比較不可");
    - otherwise ``conditional`` (coverage / sampling review still required).
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return ComparabilityResult(_UNKNOWN, ["insufficient_metadata"])

    for key in _MEASUREMENT_KEYS:
        if _get_measurement_field(a, key) in (None, "") or _get_measurement_field(b, key) in (None, ""):
            return ComparabilityResult(_UNKNOWN, ["insufficient_metadata"])

    reasons: list[str] = []

    if a.get("compound_id") != b.get("compound_id"):
        reasons.append("compound_mismatch")
    if _get_measurement_field(a, "intent") != _get_measurement_field(b, "intent"):
        reasons.append("intent_mismatch")
    if a.get("granularity") != b.get("granularity"):
        reasons.append("granularity_mismatch")
    if _get_measurement_field(a, "time_axis") != _get_measurement_field(b, "time_axis"):
        reasons.append("time_axis_mismatch")
    if a.get("measurement_id") != b.get("measurement_id"):
        reasons.append("measurement_mismatch")

    unit_a = a.get("unit")
    unit_b = b.get("unit")
    if unit_a is not None and unit_b is not None and unit_a != unit_b:
        reasons.append("unit_mismatch")

    # Google Trends: relative index values are only comparable inside the same
    # normalization scale / comparison set.
    relative_index_units = {"relative_index_0_100"}
    if unit_a in relative_index_units and unit_b in relative_index_units:
        scale_a = a.get("normalization_scale", a.get("comparison_set"))
        scale_b = b.get("normalization_scale", b.get("comparison_set"))
        if scale_a in (None, "") or scale_b in (None, ""):
            return ComparabilityResult(_UNKNOWN, ["normalization_scale_unknown"])
        if scale_a != scale_b:
            reasons.append("normalization_scale_mismatch")

    if reasons:
        return ComparabilityResult(_NOT_COMPARABLE, reasons)
    return ComparabilityResult(_CONDITIONAL, ["coverage_and_sampling_review_required"])


# ---------------------------------------------------------------------------
# G3 §12 / c.md §12.2: temporal comparability
# ---------------------------------------------------------------------------


def _window_bounds(window: dict):
    start = window.get("start", window.get("requested_start"))
    end = window.get("end_exclusive", window.get("requested_end_exclusive"))
    return start, end


def compare_temporal_windows(a: dict, b: dict) -> ComparabilityResult:
    """G3 §12 gate (T1-T8 subset).

    - different requested windows / timezone / granularity / week boundary ->
      ``not_comparable`` (T1-T4);
    - a window that did not exactly match the collector's boundary ->
      ``conditional`` (T5: boundary interpretation needs review);
    - different time axis (e.g. publication time vs observation time,
      c.md §12.1 T8) -> ``not_comparable``;
    - missing window bounds -> ``unknown``.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return ComparabilityResult(_UNKNOWN, ["insufficient_metadata"])

    start_a, end_a = _window_bounds(a)
    start_b, end_b = _window_bounds(b)
    if start_a in (None, "") or end_a in (None, "") or start_b in (None, "") or end_b in (None, ""):
        return ComparabilityResult(_UNKNOWN, ["insufficient_metadata"])

    reasons: list[str] = []
    if start_a != start_b or end_a != end_b:
        reasons.append("window_mismatch")
    if a.get("timezone") != b.get("timezone"):
        reasons.append("timezone_mismatch")
    if a.get("granularity") != b.get("granularity"):
        reasons.append("granularity_mismatch")
    if a.get("granularity") == "week" and a.get("week_start") != b.get("week_start"):
        reasons.append("week_boundary_mismatch")

    axis_a = a.get("time_axis", a.get("time_axis_id"))
    axis_b = b.get("time_axis", b.get("time_axis_id"))
    if axis_a is not None or axis_b is not None:
        if axis_a != axis_b:
            reasons.append("time_axis_mismatch")

    if reasons:
        return ComparabilityResult(_NOT_COMPARABLE, reasons)

    conditionals = []
    if a.get("exact_window_match") is False or b.get("exact_window_match") is False:
        conditionals.append("window_not_exact")
    conditionals.append("coverage_and_sampling_review_required")
    return ComparabilityResult(_CONDITIONAL, conditionals)
