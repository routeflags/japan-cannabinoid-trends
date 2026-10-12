"""Collection pipeline: plan -> pre-gate -> adapter -> staging -> L1 -> catalog / quarantine.

Contract sources
----------------
- G1 §3 (architecture), §9 (capability gate), §10 (run manifest), §11 (L1),
  §13 (staging / quarantine), §15 (contract tests): ``docs/plans/20261013a.md``.
- Operating notes: ``docs/specs/collection-pipeline.md``.

Flow (fail closed at every step):

1. structural validation of the plan (``collection-plan-v1``);
2. collector selection (capability gate, no auto-switch);
3. pre-collection gate (registry / query / temporal semantics);
4. adapter contract + identity + capability cross-checks;
5. adapter-specific plan validation;
6. ``collect`` into ``<workspace>/.staging/<run-id>/`` with the payload,
   the artifact manifest and ``run_metadata.json``;
7. L1 evaluation (``collection.core.integrity``);
8. L1 pass -> move to ``<datasets-root>/<study>/data/raw/<run-id>/``
   (catalog); L1 fail -> move to ``<workspace>/.quarantine/<run-id>/``
   with a ``quarantine-reason.json`` (raw preserved, never deleted).

No overwrite: an existing run-id in staging, catalog or quarantine refuses
the collection (G1 §13 "同じrun_idへの上書きは禁止").

``adopt_staged`` runs steps 7-8 for a run staged by an external collector
(e.g. a shell script), which is the migration path for the existing
``src/collection/*.sh`` flows (decision A in the G1 slice plan).
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from validation.gates import pre_collection_gate
from validation.pipeline import validate_full
from validation.reporting import Issue
from validation.semantic import Registries

from collection.core.contracts import (
    ADAPTER_CONTRACT_VERSION,
    CollectionResult,
    check_adapter_contract,
)
from collection.core.integrity import L1Decision, evaluate_l1
from collection.core.provenance import (
    COLLECTION_CORE_VERSION,
    StagedArtifact,
    build_artifact_manifest,
    build_run_metadata,
    default_run_id,
    iso_timestamp,
)
from collection.core.registry import load_registries
from collection.core.selection import select_collector

__all__ = [
    "PIPELINE_VERSION",
    "PipelineResult",
    "adopt_staged",
    "run_collection",
]

PIPELINE_VERSION = "1.0.0"

ARTIFACT_MANIFEST_NAME = "artifact-manifest.json"
RUN_METADATA_NAME = "run_metadata.json"
QUARANTINE_REASON_NAME = "quarantine-reason.json"


def _issue(code, path, message, rule="collection_pipeline"):
    return Issue(code=code, path=path, severity="error", message=message, rule=rule)


def _write_json(path: Path, document) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _git_commit(workspace_root) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0:
        commit = result.stdout.strip()
        return commit or None
    return None


@dataclass
class PipelineResult:
    """Outcome of one collect / adopt execution."""

    action: str  # adopted | quarantined | stopped
    run_id: str | None = None
    staging_dir: str | None = None
    final_dir: str | None = None
    l1: L1Decision | None = None
    issues: list[Issue] = field(default_factory=list)

    @property
    def adopted(self) -> bool:
        return self.action == "adopted"

    def to_dict(self) -> dict:
        return {
            "pipeline": "g1-collection-core",
            "pipeline_version": PIPELINE_VERSION,
            "action": self.action,
            "run_id": self.run_id,
            "staging_dir": self.staging_dir,
            "final_dir": self.final_dir,
            "l1": self.l1.to_dict() if self.l1 is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _staging_root(workspace_root) -> Path:
    return Path(workspace_root) / ".staging"


def _quarantine_root(workspace_root) -> Path:
    return Path(workspace_root) / ".quarantine"


def _catalog_dir(datasets_root, study_id: str, run_id: str) -> Path:
    return Path(datasets_root) / study_id / "data" / "raw" / run_id


def _existing_locations(staging, quarantine, catalog) -> list[Path]:
    return [path for path in (staging, quarantine, catalog) if path.exists()]


def _quarantine(
    staged_dir: Path, quarantine_root: Path, run_id: str, decision: L1Decision
) -> tuple[Path, list[Issue]]:
    """Move a failed run into quarantine and record the reason.

    The raw files are moved, never rewritten.  A quarantine containing
    secrets is additionally restricted (chmod 700) - the provisional
    minimum for G1 §13 "アクセス制限された保護領域"; the retention policy
    itself is an open decision (see docs/specs/collection-pipeline.md).
    """
    contains_secrets = any(issue.code == "SECRET_DETECTED" for issue in decision.issues)
    reason = {
        "run_id": run_id,
        "action": "quarantine",
        "quarantined_at": iso_timestamp(datetime.now(timezone.utc)),
        "contains_secrets": contains_secrets,
        "issues": [issue.to_dict() for issue in decision.issues],
    }
    _write_json(staged_dir / QUARANTINE_REASON_NAME, reason)
    target = quarantine_root / run_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staged_dir), str(target))
    issues: list[Issue] = []
    if contains_secrets:
        try:
            os.chmod(target, 0o700)
        except OSError:  # pragma: no cover - platform dependent
            pass
        issues.append(
            _issue(
                "QUARANTINE_RESTRICTED",
                "",
                "quarantine contains detected credential-like data; "
                "access has been restricted (chmod 700)",
            )
        )
    return target, issues


def _finalize(
    *,
    document: dict,
    staged_dir: Path,
    run_id: str,
    datasets_root,
    workspace_root,
    registries: Registries | None,
) -> PipelineResult:
    """L1 evaluation + catalog/quarantine move (shared by collect / adopt)."""
    decision = evaluate_l1(document, registries=registries, base_dir=staged_dir)
    if decision.action == "catalog":
        study_id = document.get("study_id")
        target = _catalog_dir(datasets_root, str(study_id), run_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_dir), str(target))
        return PipelineResult(
            action="adopted",
            run_id=run_id,
            staging_dir=str(staged_dir),
            final_dir=str(target),
            l1=decision,
        )

    target, extra_issues = _quarantine(
        staged_dir, _quarantine_root(workspace_root), run_id, decision
    )
    return PipelineResult(
        action="quarantined",
        run_id=run_id,
        staging_dir=str(staged_dir),
        final_dir=str(target),
        l1=decision,
        issues=extra_issues,
    )


def _check_study_directory(plan_study_id, datasets_root) -> list[Issue]:
    """A study is a curated unit (README / methodology); the pipeline never
    invents one (AGENTS.md dataset structure)."""
    if not plan_study_id:
        return [_issue("STUDY_ID_MISSING", "/study_id", "plan has no study_id")]
    if not (Path(datasets_root) / plan_study_id).is_dir():
        return [
            _issue(
                "STUDY_DIRECTORY_MISSING",
                "/study_id",
                "study directory does not exist under the datasets root; "
                "create the study scaffold first (README / methodology)",
            )
        ]
    return []


def run_collection(
    plan: dict,
    *,
    adapter,
    workspace_root,
    datasets_root,
    registries: Registries | None = None,
    run_id: str | None = None,
    now: datetime | None = None,
    environment: dict | None = None,
) -> PipelineResult:
    """Run the full collection pipeline for one plan (see module docstring)."""
    if registries is None:
        registries = load_registries(Path(workspace_root) / "config", Path(workspace_root) / "metadata")

    # 1. structural plan validation
    plan_outcome = validate_full(plan, schema_id="collection-plan-v1", target="plan")
    if not plan_outcome.valid:
        return PipelineResult(action="stopped", issues=list(plan_outcome.issues))

    # 2. collector selection (capability gate + ambiguity refusal)
    collector_entry, selection_issues = select_collector(plan, registries)
    if selection_issues:
        return PipelineResult(action="stopped", issues=selection_issues)

    # 3. pre-collection gate (registry / query / window semantics)
    plan_document = dict(plan)
    plan_document.setdefault("collector_id", collector_entry.get("collector_id"))
    pre_gate = pre_collection_gate(plan_document, registries=registries)
    if not pre_gate.passed:
        return PipelineResult(action="stopped", issues=pre_gate.issues)

    # 4. adapter contract / identity / capability cross-checks
    contract_violations = check_adapter_contract(adapter)
    if contract_violations:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue("ADAPTER_CONTRACT_VIOLATION", "", violation)
                for violation in contract_violations
            ],
        )
    if (
        adapter.adapter_id != collector_entry.get("adapter_id")
        or adapter.collector_id != collector_entry.get("collector_id")
        or adapter.source_id != collector_entry.get("source_id")
    ):
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "ADAPTER_IDENTITY_MISMATCH",
                    "",
                    "adapter identity does not match the registered collector",
                )
            ],
        )
    if adapter.capabilities() != collector_entry.get("capabilities"):
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "ADAPTER_CAPABILITY_MISMATCH",
                    "",
                    "adapter capabilities do not match the collector registry"
                    " (records are the source of truth)",
                )
            ],
        )

    # 5. adapter-specific plan validation
    adapter_violations = adapter.validate_plan(plan)
    if adapter_violations:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue("ADAPTER_PLAN_REJECTED", "/query", violation)
                for violation in adapter_violations
            ],
        )

    # 6. staging
    moment = now or datetime.now(timezone.utc)
    effective_run_id = run_id or default_run_id(
        str(plan.get("source_id")), str(plan.get("study_id")), moment
    )
    staged_dir = _staging_root(workspace_root) / effective_run_id
    study_issues = _check_study_directory(plan.get("study_id"), datasets_root)
    if study_issues:
        return PipelineResult(
            action="stopped", run_id=effective_run_id, issues=study_issues
        )
    existing = _existing_locations(
        staged_dir,
        _quarantine_root(workspace_root) / effective_run_id,
        _catalog_dir(datasets_root, str(plan.get("study_id")), effective_run_id),
    )
    if existing:
        return PipelineResult(
            action="stopped",
            run_id=effective_run_id,
            issues=[
                _issue(
                    "RUN_ID_ALREADY_EXISTS",
                    "",
                    "run_id already exists; overwriting a run is forbidden "
                    "(G1 §13)",
                )
            ],
        )

    started_at = moment
    try:
        result = adapter.collect(plan)
    except Exception as error:  # noqa: BLE001 - a crash is recorded, not lost
        result = CollectionResult(
            raw={"error": {"exception": error.__class__.__name__}},
            status="failed",
            errors=[{"code": "ADAPTER_EXCEPTION", "message": error.__class__.__name__}],
            returned_count=0,
            pagination_exhausted=None,
            completeness="missing",
        )
    finished_at = datetime.now(timezone.utc)

    observations = list(result.observations)
    if result.status in ("success", "partial") and not observations:
        try:
            observations = adapter.extract_observations(result.raw)
        except Exception as error:  # noqa: BLE001
            observations = []
            result.status = "failed"
            result.completeness = "missing"
            result.errors = list(result.errors) + [
                {"code": "EXTRACTION_FAILED", "message": error.__class__.__name__}
            ]
            result.returned_count = 0

    staged_dir.mkdir(parents=True)
    payload_path = staged_dir / result.payload_filename
    _write_json(payload_path, result.raw)

    artifact = StagedArtifact(
        artifact_id=f"{effective_run_id}-payload",
        path=result.payload_filename,
        artifact_type=result.artifact_type,
        format="json",
        schema_id=result.payload_schema_id,
        layer="raw",
        completeness=result.completeness,
        record_count=(
            len(observations) if result.status in ("success", "partial") else None
        ),
    )
    manifest = build_artifact_manifest(effective_run_id, staged_dir, [artifact])
    _write_json(staged_dir / ARTIFACT_MANIFEST_NAME, manifest)

    run_environment = dict(environment or {})
    run_environment.setdefault("collection_core_version", COLLECTION_CORE_VERSION)
    run_environment.setdefault("adapter_contract_version", ADAPTER_CONTRACT_VERSION)
    run_environment.setdefault("runtime_version", f"python-{platform.python_version()}")
    if hasattr(adapter, "describe_execution"):
        run_environment.setdefault("adapter", adapter.describe_execution())
    commit = _git_commit(workspace_root)
    if commit:
        run_environment.setdefault("code_commit", commit)

    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    window_id = window.get("window_id") or f"{window.get('start')}_{window.get('end_exclusive')}"
    document = build_run_metadata(
        plan=plan,
        collector_entry=collector_entry,
        adapter=adapter,
        result=result,
        run_id=effective_run_id,
        started_at=started_at,
        finished_at=finished_at,
        artifact_manifest_name=ARTIFACT_MANIFEST_NAME,
        window_id=window_id,
        environment=run_environment,
    )
    _write_json(staged_dir / RUN_METADATA_NAME, document)

    return _finalize(
        document=document,
        staged_dir=staged_dir,
        run_id=effective_run_id,
        datasets_root=datasets_root,
        workspace_root=workspace_root,
        registries=registries,
    )


def adopt_staged(
    staged_dir,
    *,
    workspace_root,
    datasets_root,
    registries: Registries | None = None,
) -> PipelineResult:
    """Evaluate L1 and move an externally staged run (G1 §13 staging contract).

    The staged directory must contain ``run_metadata.json`` (plus the
    artifacts its manifest references).  Nothing is modified: the directory
    is only read, then moved (catalog) or moved with an added reason file
    (quarantine).
    """
    staged_path = Path(staged_dir)
    metadata_path = staged_path / RUN_METADATA_NAME
    if not metadata_path.is_file():
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGED_RUN_UNREADABLE",
                    "/run_metadata.json",
                    "staged run has no readable run_metadata.json",
                )
            ],
        )
    try:
        document = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGED_RUN_UNREADABLE",
                    "/run_metadata.json",
                    "staged run has no readable run_metadata.json",
                )
            ],
        )

    run_id = document.get("run_id") if isinstance(document, dict) else None
    if not isinstance(run_id, str) or not run_id:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue("RUN_ID_MISSING", "/run_id", "staged run has no run_id")
            ],
        )

    if registries is None:
        registries = load_registries(
            Path(workspace_root) / "config", Path(workspace_root) / "metadata"
        )

    study_issues = _check_study_directory(document.get("study_id"), datasets_root)
    if study_issues:
        return PipelineResult(action="stopped", run_id=run_id, issues=study_issues)

    existing = [
        path
        for path in (
            _quarantine_root(workspace_root) / run_id,
            _catalog_dir(datasets_root, str(document.get("study_id")), run_id),
        )
        if path.exists()
    ]
    if existing:
        return PipelineResult(
            action="stopped",
            run_id=run_id,
            issues=[
                _issue(
                    "RUN_ID_ALREADY_EXISTS",
                    "",
                    "run_id already exists in the catalog or quarantine; "
                    "overwriting a run is forbidden (G1 §13)",
                )
            ],
        )

    return _finalize(
        document=document,
        staged_dir=staged_path,
        run_id=run_id,
        datasets_root=datasets_root,
        workspace_root=workspace_root,
        registries=registries,
    )
