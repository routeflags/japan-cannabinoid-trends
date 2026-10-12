"""Capability / selection gate for collection plans (G1 §9).

Contract: a.md §9.  Selection rules implemented here:

- only collectors with ``status: active`` are selectable;
- every required capability must be ``supported``; ``unknown`` (including a
  missing entry) is never auto-selected and is never upgraded to
  ``unsupported`` (the registry's tri-state is preserved);
- when the plan names a collector, that collector is used or the collection
  stops - the core never falls back to another collector automatically;
- when the plan does not name one and several collectors qualify, the
  collection stops: the study plan must state the choice explicitly.

The individual capability findings come from
``validation.semantic.check_capability_gate`` so the gate semantics stay in
the validation layer (h.md §6).
"""

from __future__ import annotations

from validation.reporting import Issue
from validation.semantic import (
    Registries,
    check_capability_gate,
    eligible_collectors,
)

from collection.core.registry import find_collector

__all__ = ["select_collector"]


def select_collector(plan: dict, registries: Registries):
    """Resolve the collector for ``plan``.

    Returns ``(collector, issues)``.  ``collector`` is non-None only when the
    plan can proceed; any issues mean fail closed (do not start).
    """
    issues: list[Issue] = []
    if not isinstance(plan, dict):
        issues.append(
            Issue(
                code="GATE_PLAN_INVALID",
                path="",
                severity="error",
                message="collection plan is not a mapping",
                rule="capability_gate",
            )
        )
        return None, issues

    source_id = plan.get("source_id")
    requirements = plan.get("required_capabilities")
    if not isinstance(requirements, list):
        requirements = []
    requested = plan.get("collector_id")

    issues.extend(
        check_capability_gate(
            source_id,
            requirements,
            registries,
            requested_collector_id=requested,
        )
    )
    if issues:
        return None, issues

    if isinstance(requested, str) and requested:
        collector = find_collector(registries, source_id, requested)
        if collector is None:  # pragma: no cover - check_capability_gate guards
            issues.append(
                Issue(
                    code="GATE_COLLECTOR_UNREGISTERED",
                    path="/collector_id",
                    severity="error",
                    message="requested collector is not registered for this "
                    "source_id",
                    rule="capability_gate",
                )
            )
            return None, issues
        return collector, issues

    eligible = eligible_collectors(source_id, requirements, registries)
    if len(eligible) == 1:
        return eligible[0], issues
    # len == 0 has already produced GATE_NO_ELIGIBLE_COLLECTOR above.
    issues.append(
        Issue(
            code="GATE_COLLECTOR_AMBIGUOUS",
            path="/collector_id",
            severity="error",
            message="multiple active collectors satisfy the requirements; "
            "the collection plan must select one explicitly",
            rule="capability_gate",
        )
    )
    return None, issues
