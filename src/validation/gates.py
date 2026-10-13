"""Collection gates (Phase 6, P6-1 / P6-2).

Contract sources
----------------
- Rollout instruction §12 (validation pipeline: Collection Plan -> ... ->
  L1 Collection Validity -> FAIL -> Quarantine -> L2 -> Catalog).
- G1 §9 (Capability Gate) and §13 (raw storage / quarantine):
  ``docs/plans/20261013a.md``; G1 §11 L1-06/L1-07/L1-09 (raw evidence,
  hash, missingness).

These functions decide *from validation results* whether a collection may
start / be adopted:

- ``pre_collection_gate``: FAIL -> do not start (fail closed; unknown
  capabilities are never auto-selected);
- ``post_collection_gate``: PASS -> catalog, FAIL -> quarantine.  The gate
  only reports the action; moving files is the collector's job and the raw
  data is never overwritten (P6-2 acceptance).

L1 (Collection Integrity) additions on top of the semantic layer:

- a terminal run must reference an artifact manifest whose raw artifacts
  exist and verify (hash / byte length) - L1-06 / L1-07;
- missingness/completeness semantics (zero vs missing vs failure) are checked
  by ``semantic.check_missingness_consistency`` - L1-09;
- a run whose execution **failed** is preserved in quarantine instead of
  being adopted as research data (G1 P4: fail closed, raw retained).

Wiring into the collection adapters: the G1 collection core
(``collection.core.pipeline``) calls these gates in-process, and the shell
entry point is ``scripts/validation/run-gates.sh`` (P6-5) so that validation
logic stays in one place (h.md §6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from validation.integrity import (
    load_artifact_manifest,
    verify_artifact_manifest,
)
from validation.reporting import Issue
from validation.semantic import (
    Registries,
    check_capability_gate,
    check_execution_consistency,
    check_missingness_consistency,
    check_registry_references,
    check_schema_version,
    check_temporal_semantics,
    scan_for_secrets,
)
from validation.windows import check_plan_window_registry

__all__ = ["GateResult", "post_collection_gate", "pre_collection_gate"]


@dataclass
class GateResult:
    passed: bool
    action: str
    issues: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "action": self.action,
            "issues": [issue.to_dict() for issue in self.issues],
        }


_PRE_ACTIONS = {True: "proceed", False: "stop"}
_POST_ACTIONS = {True: "catalog", False: "quarantine"}


def _failed(issues: list[Issue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def pre_collection_gate(plan: dict, *, registries: Registries) -> GateResult:
    """P6-1: validate a Collection Plan before collection starts.

    FAIL (any error-severity issue) means the collection must not start
    (fail closed).  ``plan`` is structurally validated by the caller against
    ``collection-plan-v1``; this gate adds the registry / capability /
    temporal semantics.
    """
    issues: list[Issue] = []
    if not isinstance(plan, dict):
        issues.append(
            Issue(
                code="GATE_PLAN_INVALID",
                path="",
                severity="error",
                message="collection plan is not a mapping",
                rule="collection_gate",
            )
        )
        return GateResult(False, _PRE_ACTIONS[False], issues)

    requirements = plan.get("required_capabilities")
    if not isinstance(requirements, list):
        requirements = []
    if registries.collectors:
        # The capability gate needs a collector registry; when none exists the
        # gate cannot verify anything and validate-registries reports the
        # missing registry instead of the gate inventing an outcome.
        issues.extend(
            check_capability_gate(
                plan.get("source_id"),
                requirements,
                registries,
                requested_collector_id=plan.get("collector_id"),
            )
        )

    if registries.queries and isinstance(plan.get("query_id"), str):
        known = any(
            isinstance(item, dict) and item.get("query_id") == plan["query_id"]
            for item in registries.queries
        )
        if not known:
            issues.append(
                Issue(
                    code="REFERENCE_QUERY_UNREGISTERED",
                    path="/query_id",
                    severity="error",
                    message="query_id is not registered in the query registry",
                    rule="collection_gate",
                )
            )

    window = plan.get("window")
    if isinstance(window, dict):
        issues.extend(check_temporal_semantics(window))
        # G3 P1: when the absolute window registry exists and the plan claims
        # a registered window_id, the plan must carry that window (fail
        # closed on drift).  Without a registry the check is disabled.
        if registries.windows:
            issues.extend(check_plan_window_registry(window, registries.windows))

    passed = not _failed(issues)
    return GateResult(passed, _PRE_ACTIONS[passed], issues)


def post_collection_gate(
    document: dict,
    *,
    registries: Registries | None = None,
    base_dir=None,
    schema_id: str = "collection-run-v1",
) -> GateResult:
    """P6-2 / L1: decide catalog vs quarantine for a collected run.

    Structural validation is expected to have run first (``validate_full``);
    this gate adds semantic checks, the L1 missingness / completeness rules
    and, when ``base_dir`` is given, artifact integrity.  Raw data is never
    moved or rewritten by the gate itself (quarantine keeps the raw
    untouched).

    A failed execution is never adopted: the raw (including the error
    record) is preserved in quarantine instead (G1 §13, P4).
    """
    issues: list[Issue] = []
    issues.extend(check_schema_version(document, schema_id))
    issues.extend(check_temporal_semantics(document))
    issues.extend(check_execution_consistency(document))
    if registries is not None:
        issues.extend(check_registry_references(document, registries))
    issues.extend(scan_for_secrets(document))

    manifest = None
    manifest_name = None
    if isinstance(document, dict):
        manifest_name = document.get("artifact_manifest")
    if base_dir is not None and isinstance(manifest_name, str) and manifest_name:
        manifest_path = Path(base_dir) / manifest_name
        manifest, _ = load_artifact_manifest(manifest_path)
        issues.extend(
            verify_artifact_manifest(
                manifest_path,
                base_dir=base_dir,
                manifest=manifest,
                artifact_registry=(
                    registries.artifact_registry if registries is not None else None
                ),
            )
        )
        if isinstance(manifest, dict):
            document_run_id = document.get("run_id")
            manifest_run_id = manifest.get("run_id")
            if (
                isinstance(document_run_id, str)
                and isinstance(manifest_run_id, str)
                and document_run_id != manifest_run_id
            ):
                issues.append(
                    Issue(
                        code="MANIFEST_RUN_ID_MISMATCH",
                        path="/artifact_manifest",
                        severity="error",
                        message="artifact manifest belongs to a different run_id",
                        rule="collection_integrity",
                    )
                )

    issues.extend(check_missingness_consistency(document, manifest))

    if isinstance(document, dict):
        execution = document.get("execution")
        if isinstance(execution, dict) and execution.get("status") == "failed":
            issues.append(
                Issue(
                    code="COLLECTION_FAILED_NOT_ADOPTED",
                    path="/execution/status",
                    severity="error",
                    message="a failed collection is preserved in quarantine, "
                    "not adopted as research data",
                    rule="collection_integrity",
                )
            )

    issues.sort(key=lambda issue: issue.sort_key())
    passed = not _failed(issues)
    return GateResult(passed, _POST_ACTIONS[passed], issues)
