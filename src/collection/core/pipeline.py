"""Collection pipeline: plan -> pre-gate -> adapter -> staging -> L1 -> catalog / quarantine.

Contract sources
----------------
- G1 §3 (architecture), §9 (capability gate), §10 (run manifest), §11 (L1),
  §13 (staging / quarantine), §15 (contract tests): ``docs/plans/20261013a.md``.
- Operating notes: ``docs/specs/collection-pipeline.md``.

Flow (fail closed at every step):

1. structural validation of the plan (``collection-plan-v1``);
2. collector selection (capability gate, no auto-switch);
3. pre-collection gate (registry / query / temporal semantics; G3 window
   registry consistency when ``metadata/windows`` exists);
3b. G3 window compilation: an absolute plan window is compiled into the
   collector's registered parameters *before* collection and the result is
   verified (fail closed: ``WINDOW_NOT_REPRESENTABLE``,
   ``WINDOW_TIMEFRAME_CONFLICT``, ``WINDOW_EXACTNESS_UNAVAILABLE``);
4. adapter contract + identity + capability cross-checks;
5. adapter-specific plan validation;
6. ``collect`` into ``<workspace>/.staging/<run-id>/`` with the payload,
   the artifact manifest and ``run_metadata.json``;
7. L1 evaluation (``collection.core.integrity``);
8. L1 pass -> move to ``<datasets-root>/<study>/data/raw/<source>/<run-id>/``
   (catalog, COL-018(a) source hierarchy); L1 fail -> move to ``<workspace>/.quarantine/<run-id>/``
   with a ``quarantine-reason.json`` (raw preserved, never deleted).

No overwrite: an existing run-id in staging, catalog or quarantine refuses
the collection (G1 §13 "同じrun_idへの上書きは禁止").

``adopt_staged`` runs steps 7-8 for a run staged by an external collector
(e.g. a shell script), which is the migration path for the existing
``src/collection/*.sh`` flows (decision A in the G1 slice plan).

``stage_run`` is the producer side of that same boundary: an external
collector (an MCP session, a cloud dataset export, a shell script) obtained
the payload somewhere else, and this function turns the declaration of that
run - the same collection plan ``collect`` takes, plus the files the collector
produced and the execution facts it recorded - into the staged directory
``adopt_staged`` evaluates.  Producer and verdict stay separate, so the gate
never depends on the code that produced its input.  See
``docs/specs/collection-pipeline.md`` section 3.3.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from validation.gates import pre_collection_gate
from validation.pipeline import validate_full
from validation.reporting import Issue
from validation.semantic import Registries
from validation.windows import (
    WindowCompilationError,
    check_plan_window_registry,
    parse_datetime,
)

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
from collection.core.registry import find_collector, load_registries
from collection.core.selection import select_collector

__all__ = [
    "PIPELINE_VERSION",
    "CollectedArtifact",
    "PipelineResult",
    "adopt_staged",
    "run_collection",
    "stage_run",
    "staging_artifact_id",
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


#: A run id / study id becomes a directory name (``.staging/<run-id>/``,
#: ``<datasets-root>/<study-id>/data/raw/<source>/<run-id>/``) and arrives from outside
#: the repository (a handover directory, a staged ``run_metadata.json``), so it
#: is validated as one path-safe component wherever the pipeline accepts it.
_IDENTIFIER_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_MAX_IDENTIFIER_LENGTH = 128

#: ``environment`` keys the pipeline owns.  ``environment`` adds
#: collector-specific detail; it cannot restate what ran here.
_FINGERPRINT_KEYS = (
    "adapter",
    "adapter_contract_version",
    "code_commit",
    "collection_core_version",
    "runtime_version",
)


def _identifier_component_reason(value, field_name: str) -> str | None:
    """Why ``value`` cannot be used as one directory name (None = it can)."""
    if not isinstance(value, str) or not value:
        return f"{field_name} must be a non-empty string"
    if len(value) > _MAX_IDENTIFIER_LENGTH:
        return f"{field_name} must be at most {_MAX_IDENTIFIER_LENGTH} characters"
    if not _IDENTIFIER_COMPONENT.match(value):
        return (
            f"{field_name} must be one path-safe component (letters, digits, "
            "'.', '_' or '-', starting with a letter or digit)"
        )
    return None


def _run_environment(environment, adapter, workspace_root) -> dict:
    """Merge a caller's ``environment`` with the pipeline-owned fingerprint.

    The fingerprint (adapter identity, core / contract versions, code commit)
    describes what ran here, so the pipeline writes it and a caller cannot
    replace it; ``environment`` contributes collector detail only.
    ``code_commit`` is recorded only when the workspace really is a git
    checkout - an unverifiable claim is dropped rather than repeated.
    """
    merged = {
        key: value
        for key, value in (environment or {}).items()
        if key not in _FINGERPRINT_KEYS
    }
    merged["collection_core_version"] = COLLECTION_CORE_VERSION
    merged["adapter_contract_version"] = ADAPTER_CONTRACT_VERSION
    merged["runtime_version"] = f"python-{platform.python_version()}"
    if hasattr(adapter, "describe_execution"):
        merged["adapter"] = adapter.describe_execution()
    commit = _git_commit(workspace_root)
    if commit:
        merged["code_commit"] = commit
    return merged


def _resolve_window_compiler(collector_id):
    """Resolve the G3 window compiler for a collector (lazy import).

    The platform-name resolution table lives in ``collection.adapters`` only
    (P1); the core never imports a vendor module directly.  A collector
    without a compiler keeps the pre-G3 behaviour (the adapter owns its
    period parameters).
    """
    if not collector_id:
        return None
    try:
        from collection.adapters import get_window_compiler
    except Exception:  # noqa: BLE001 - resolution is optional by design
        return None
    return get_window_compiler(collector_id)


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


def _source_slug(source_id) -> str:
    """Directory name for a source (``google-trends`` -> ``google_trends``).

    The catalog keeps the repository's existing per-source raw layout
    (``data/raw/google_trends/<run-id>/``), which is what the storage policy and
    .gitignore expect: search raw is tracked (``raw-search-tracked``), other
    sources' raw stays private.  Placing every pipeline run directly under
    ``data/raw/<run-id>/`` silently ignored the public ones (measured
    2026-10-15: the first live Google Trends runs landed in an ignored path).
    """

    return str(source_id or "unknown").strip().replace("-", "_").lower()


def _catalog_dir(datasets_root, study_id: str, run_id: str, source_id=None) -> Path:
    return (
        Path(datasets_root)
        / study_id
        / "data"
        / "raw"
        / _source_slug(source_id)
        / run_id
    )


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
        target = _catalog_dir(
            datasets_root, str(study_id), run_id, document.get("source_id")
        )
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
    invents one (AGENTS.md dataset structure), and ``study_id`` names a
    directory under the datasets root, so it must be one safe component."""
    if not plan_study_id:
        return [_issue("STUDY_ID_MISSING", "/study_id", "plan has no study_id")]
    unsafe = _identifier_component_reason(plan_study_id, "study_id")
    if unsafe:
        return [_issue("STUDY_ID_UNSAFE", "/study_id", unsafe)]
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
    compiler=None,
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

    # 3b. G3 window compilation: the absolute window is verified against the
    # collector's registered vocabulary *before* anything is collected
    # (c.md §6/§P6: no silent fallback; unsupported windows must not start a
    # collection with a different period).
    moment = now or datetime.now(timezone.utc)
    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    if compiler is None:
        compiler = _resolve_window_compiler(collector_entry.get("collector_id"))
    compiled = None
    if compiler is not None and window:
        try:
            compiled = compiler.compile(
                window,
                reference_time=moment,
                capabilities=collector_entry.get("capabilities"),
            )
        except WindowCompilationError as error:
            return PipelineResult(
                action="stopped",
                issues=[
                    _issue(
                        "WINDOW_NOT_REPRESENTABLE",
                        "/window",
                        "window compilation refused ("
                        + ", ".join(error.codes)
                        + "): "
                        + str(error),
                    )
                ],
            )
    effective_plan = plan
    if compiled is not None:
        # Source-agnostic merge (P1): the compiler's parameters are merged
        # into the plan's adapter extension area; a plan that already
        # declares a conflicting non-empty value stops the run (P6: the
        # period is never switched silently).
        effective_plan = dict(plan)
        query = dict(plan.get("query")) if isinstance(plan.get("query"), dict) else {}
        for key, value in compiled.parameters.items():
            declared = query.get(key)
            if key in query and declared not in (None, "") and declared != value:
                return PipelineResult(
                    action="stopped",
                    issues=[
                        _issue(
                            "WINDOW_TIMEFRAME_CONFLICT",
                            f"/query/{key}",
                            "the plan's declared period parameter does not match "
                            f"the compiled window ({declared!r} != {value!r}); "
                            "the period is never switched silently (P6)",
                        )
                    ],
                )
            query[key] = value
        effective_plan["query"] = query
        if window.get("exact_required") is True and compiled.exact is False:
            return PipelineResult(
                action="stopped",
                issues=[
                    _issue(
                        "WINDOW_EXACTNESS_UNAVAILABLE",
                        "/window/exact_required",
                        "the plan requires an exact window but the compiled "
                        "collector window is inexact (c.md §6.2); record "
                        "exact_required only for collectors with verified "
                        "boundaries",
                    )
                ],
            )

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

    # 5. adapter-specific plan validation (against the effective plan, i.e.
    # with the compiled timeframe when a window compiler ran)
    adapter_violations = adapter.validate_plan(effective_plan)
    if adapter_violations:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue("ADAPTER_PLAN_REJECTED", "/query", violation)
                for violation in adapter_violations
            ],
        )

    # 6. staging
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
        _catalog_dir(
            datasets_root,
            str(plan.get("study_id")),
            effective_run_id,
            plan.get("source_id"),
        ),
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
        result = adapter.collect(effective_plan)
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
    if finished_at < started_at:
        # Deterministic replay: an explicit reference/collection time may be
        # ahead of the wall clock; a run cannot finish before it started, and
        # the recorded pair must stay internally consistent (G5-T08).
        finished_at = started_at

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

    # The id follows the same rule the staging driver uses
    # (``staging_artifact_id``), so a derived artifact can reference it.
    artifact = StagedArtifact(
        artifact_id=staging_artifact_id(effective_run_id, result.payload_filename),
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

    # The payload is the verbatim response (preserved as produced).  An adapter
    # that can also parse the response may declare the derived files that belong
    # in the same run - the parsed series a consumer reads without re-parsing the
    # source (optional hook: see collection/core/contracts.py).
    artifacts = [artifact]
    hook = getattr(adapter, "derived_artifacts", None)
    if callable(hook):
        for derived in hook(effective_plan, result, observations, started_at) or []:
            derived_path = staged_dir / derived["path"]
            _write_json(derived_path, derived["document"])
            artifacts.append(
                StagedArtifact(
                    artifact_id=staging_artifact_id(effective_run_id, derived["path"]),
                    path=derived["path"],
                    artifact_type=derived["artifact_type"],
                    format=derived.get("format", "json"),
                    schema_id=derived["schema_id"],
                    layer=derived.get("layer", "raw"),
                    completeness=derived.get("completeness", "complete"),
                    record_count=derived.get("record_count"),
                    derived_from=[artifact.artifact_id],
                )
            )

    manifest = build_artifact_manifest(effective_run_id, staged_dir, artifacts)
    _write_json(staged_dir / ARTIFACT_MANIFEST_NAME, manifest)

    run_environment = _run_environment(environment, adapter, workspace_root)

    window_id = window.get("window_id") or f"{window.get('start')}_{window.get('end_exclusive')}"
    document = build_run_metadata(
        plan=effective_plan,
        collector_entry=collector_entry,
        adapter=adapter,
        result=result,
        run_id=effective_run_id,
        started_at=started_at,
        finished_at=finished_at,
        artifact_manifest_name=ARTIFACT_MANIFEST_NAME,
        window_id=window_id,
        environment=run_environment,
        query_registry_version=registries.query_registry_version,
        compiled=compiled,
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
    (quarantine).  The declared ``run_id`` is untrusted input that names the
    catalog / quarantine directory, so it must be one path-safe component.
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

    unsafe_run_id = _identifier_component_reason(run_id, "run_id")
    if unsafe_run_id:
        return PipelineResult(
            action="stopped",
            run_id=run_id,
            issues=[_issue("RUN_ID_UNSAFE", "/run_id", unsafe_run_id)],
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
            _catalog_dir(
                datasets_root,
                str(document.get("study_id")),
                run_id,
                document.get("source_id"),
            ),
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


# ---------------------------------------------------------------------------
# External collector staging (producer side of the staging contract)
# ---------------------------------------------------------------------------


def staging_artifact_id(run_id: str, path: str) -> str:
    """The artifact_id a staged artifact is registered under.

    Public because producers that declare lineage (``derived_from``) must
    reference the id the manifest will actually carry; the rule stays here so
    it is implemented once.
    """
    slug = "".join(
        character if character.isalnum() else "-" for character in path.lower()
    ).strip("-")
    return f"{run_id}-{slug or 'artifact'}"


@dataclass
class CollectedArtifact:
    """One file an external collector produced, and the claim about it.

    ``source`` is where the collector left the file; ``path`` is the name it
    gets inside the staged run (relative, no traversal).  The artifact claim
    (type / format / schema / record_count) is *declared* here and verified by
    L1 against the registered reader at adoption - the stager never recomputes
    a count it cannot read, and never inspects the payload's meaning.
    """

    source: str
    path: str
    artifact_type: str
    format: str
    schema_id: str
    completeness: str = "complete"
    record_count: int | None = None
    media_type: str | None = None
    derived_from: list = field(default_factory=list)

    def staged(self, run_id: str) -> StagedArtifact:
        return StagedArtifact(
            artifact_id=staging_artifact_id(run_id, self.path),
            path=self.path,
            artifact_type=self.artifact_type,
            format=self.format,
            schema_id=self.schema_id,
            completeness=self.completeness,
            record_count=self.record_count,
            media_type=self.media_type,
            derived_from=list(self.derived_from),
        )


@dataclass(frozen=True)
class _DeclaredCollectorIdentity:
    """The collector identity recorded for a staged run.

    ``adapter_id`` / ``version`` come from the collector registry entry, never
    from the declaration: the registry is the record of truth and a stager
    must not upgrade a collector (G1 §7.2).
    """

    adapter_id: str
    version: str

    def describe_execution(self) -> dict:
        """Non-secret fingerprint.  The mode says the payload was handed
        over rather than fetched by this repository; collector-specific detail
        belongs to the declaration's own ``environment``."""
        return {
            "collection_mode": "external_staged",
            "collector_version": self.version,
        }


_STAGING_WINDOW_FIELDS = ("start", "end_exclusive", "granularity", "timezone")


def _staging_path_reason(relative) -> str | None:
    if not isinstance(relative, str) or not relative:
        return "artifact path must be a non-empty relative path"
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return "artifact path must stay inside the run directory"
    if candidate.name in ("", ".", ".."):
        return "artifact path must name a file inside the run directory"
    return None


def _staging_moment(value, field_name: str) -> tuple:
    """Parse a declared timestamp; returns ``(moment, error_message)``."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return None, f"{field_name} must carry a timezone offset"
        return value, None
    try:
        return parse_datetime(value), None
    except ValueError as error:
        return None, f"{field_name}: {error}"


def stage_run(
    plan: dict,
    *,
    artifacts,
    execution: dict,
    started_at,
    finished_at,
    workspace_root,
    datasets_root,
    registries: Registries | None = None,
    temporal: dict | None = None,
    submitted_parameters: dict | None = None,
    environment: dict | None = None,
    run_id: str | None = None,
) -> PipelineResult:
    """Write the staged directory for a run an external collector produced.

    ``plan`` is the same ``collection-plan-v1`` document ``collect`` takes and
    is structurally validated here.  It must name the collector that produced
    the payload (``collector_id``) and the requested window completely; the
    run-level gates and the L1 verdict are ``adopt_staged``'s job, so nothing
    here decides adoption.  Returns ``action="staged"`` (not "adopted"): a
    staged run has passed no gate yet.

    ``artifacts`` are :class:`CollectedArtifact` declarations; each ``source``
    file is copied into the staging directory byte-for-byte and the manifest is
    computed from the files on disk.  ``execution`` carries the collector's
    own outcome (``status`` / ``returned_count`` / ``errors`` / optionally
    ``pagination_exhausted``); the outcome itself must be declared - the two
    fields above are required, because a stager that did not observe them must
    not have them invented here.  Completeness is declared per artifact
    (:attr:`CollectedArtifact.completeness`): the run metadata contract has no
    run-level field for it.  ``temporal`` carries what only the collector can
    know (observed bounds, boundary semantics, limitations) and is merged into
    ``temporal_provenance`` exactly as an adapter's temporal block is.

    Everything accepted here arrives from outside the repository, so the names
    that become directories (``run_id`` / ``study_id``) are validated as single
    path-safe components and the pipeline-owned fingerprint keys in
    ``environment`` cannot be replaced by the declaration.

    Deliberate omissions, both documented in the module docstring:

    - no capability gate: capabilities constrain a *request*, and a run that
      has already been collected makes none.  The registry references
      (source / collector / query / study) are still checked - by L1;
    - no artifact inspection: the declared record count is verified against
      the registered reader by the L1 storage contract, in one place.
    """
    if registries is None:
        registries = load_registries(
            Path(workspace_root) / "config", Path(workspace_root) / "metadata"
        )

    plan_outcome = validate_full(plan, schema_id="collection-plan-v1", target="plan")
    if not plan_outcome.valid:
        return PipelineResult(action="stopped", issues=list(plan_outcome.issues))

    collector_entry = None
    collector_id = plan.get("collector_id")
    if isinstance(collector_id, str) and collector_id:
        collector_entry = find_collector(
            registries, plan.get("source_id"), collector_id
        )
    if collector_entry is None:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_COLLECTOR_UNKNOWN",
                    "/collector_id",
                    "a staged run must name the registered collector that "
                    "produced its payload (the registry is the record of "
                    "truth)",
                )
            ],
        )
    if not collector_entry.get("adapter_id"):
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_COLLECTOR_INCOMPLETE",
                    "/collector_id",
                    "the registered collector declares no adapter_id; the "
                    "registry entry must be completed before a run can "
                    "reference it",
                )
            ],
        )

    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    missing = [
        field_name
        for field_name in _STAGING_WINDOW_FIELDS
        if not window.get(field_name)
    ]
    if missing:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_WINDOW_INCOMPLETE",
                    "/window",
                    "a staged run must state the requested window "
                    "completely (missing: " + ", ".join(missing) + ")",
                )
            ],
        )
    window_start, window_start_error = _staging_moment(
        window.get("start"), "window.start"
    )
    window_end, window_end_error = _staging_moment(
        window.get("end_exclusive"), "window.end_exclusive"
    )
    window_error = window_start_error or window_end_error
    if window_error:
        return PipelineResult(
            action="stopped",
            issues=[_issue("STAGING_WINDOW_INVALID", "/window", window_error)],
        )
    if window_end <= window_start:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_WINDOW_ORDER",
                    "/window",
                    "window.start must be earlier than window.end_exclusive",
                )
            ],
        )
    if registries.windows:
        registry_issues = check_plan_window_registry(window, registries.windows)
        if registry_issues:
            return PipelineResult(action="stopped", issues=registry_issues)

    started, started_error = _staging_moment(started_at, "started_at")
    finished, finished_error = _staging_moment(finished_at, "finished_at")
    error = started_error or finished_error
    if error:
        return PipelineResult(
            action="stopped",
            issues=[_issue("STAGING_TIMESTAMP_INVALID", "", error)],
        )
    if finished < started:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_TIMESTAMP_ORDER",
                    "",
                    "the run cannot finish before it started",
                )
            ],
        )

    if not isinstance(execution, dict):
        execution = {}
    undeclared = [
        field_name
        for field_name in ("status", "returned_count")
        if execution.get(field_name) is None
    ]
    if undeclared:
        return PipelineResult(
            action="stopped",
            issues=[
                _issue(
                    "STAGING_EXECUTION_INCOMPLETE",
                    "/execution",
                    "a staged run must declare what the collector observed "
                    "(missing: " + ", ".join(undeclared) + ")",
                )
            ],
        )

    effective_run_id = run_id or default_run_id(
        str(plan.get("source_id")), str(plan.get("study_id")), started
    )
    unsafe_run_id = _identifier_component_reason(effective_run_id, "run_id")
    if unsafe_run_id:
        return PipelineResult(
            action="stopped",
            run_id=effective_run_id,
            issues=[_issue("RUN_ID_UNSAFE", "/run_id", unsafe_run_id)],
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
        _catalog_dir(
            datasets_root,
            str(plan.get("study_id")),
            effective_run_id,
            plan.get("source_id"),
        ),
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

    collected = list(artifacts or [])
    if not collected:
        return PipelineResult(
            action="stopped",
            run_id=effective_run_id,
            issues=[
                _issue(
                    "STAGING_NO_ARTIFACTS",
                    "/artifacts",
                    "a staged run without a raw artifact has no evidence to "
                    "adopt (a claim is not a collection)",
                )
            ],
        )
    staged_artifacts = []
    for artifact in collected:
        reason = _staging_path_reason(artifact.path)
        if reason:
            return PipelineResult(
                action="stopped",
                run_id=effective_run_id,
                issues=[
                    _issue("STAGING_ARTIFACT_PATH_UNSAFE", "/artifacts", reason)
                ],
            )
        if not Path(artifact.source).is_file():
            return PipelineResult(
                action="stopped",
                run_id=effective_run_id,
                issues=[
                    _issue(
                        "STAGING_ARTIFACT_MISSING",
                        "/artifacts",
                        "the declared artifact file does not exist: "
                        f"{artifact.source}",
                    )
                ],
            )
        staged_artifacts.append(artifact.staged(effective_run_id))

    staged_dir.mkdir(parents=True)
    for artifact, staged in zip(collected, staged_artifacts):
        target = staged_dir / staged.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(artifact.source), str(target))
    manifest = build_artifact_manifest(effective_run_id, staged_dir, staged_artifacts)
    _write_json(staged_dir / ARTIFACT_MANIFEST_NAME, manifest)

    identity = _DeclaredCollectorIdentity(
        adapter_id=str(collector_entry.get("adapter_id")),
        version=str(collector_entry.get("version", "unknown")),
    )
    run_environment = _run_environment(environment, identity, workspace_root)

    document = build_run_metadata(
        plan=plan,
        collector_entry=collector_entry,
        adapter=identity,
        result=CollectionResult(
            raw=None,
            status=execution.get("status"),
            returned_count=execution.get("returned_count"),
            errors=list(execution.get("errors") or []),
            pagination_exhausted=execution.get("pagination_exhausted"),
            submitted_parameters=dict(submitted_parameters or {}),
            temporal=dict(temporal or {}),
        ),
        run_id=effective_run_id,
        started_at=started,
        finished_at=finished,
        artifact_manifest_name=ARTIFACT_MANIFEST_NAME,
        window_id=window.get("window_id")
        or f"{window.get('start')}_{window.get('end_exclusive')}",
        environment=run_environment,
        query_registry_version=registries.query_registry_version,
    )
    _write_json(staged_dir / RUN_METADATA_NAME, document)

    return PipelineResult(
        action="staged",
        run_id=effective_run_id,
        staging_dir=str(staged_dir),
    )
