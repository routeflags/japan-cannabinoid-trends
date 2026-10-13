"""Validation pipeline orchestration (P4-11, h.md §12/§13/§14).

Layer order is a contract (rollout plan P4-11):

1. resolve the schema from the registry (unknown -> ValueError; CLI exit 2);
2. Cerberus structural validation (``validation.core``);
3. only when structure passes: semantic checks (``validation.semantic``);
4. artifact verification when the caller asks for it (``validation
   .integrity``);
5. legacy audit branch: no structural failure, missing-field report only.

A structural failure short-circuits the semantic layer; this is tested
mechanically (``tests/validation/test_pipeline.py``) with a spy check.

Nothing in this module mutates the input document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from validation.core import validate_document
from validation.integrity import verify_artifact_manifest
from validation.legacy import LegacyRecord, audit_record, resolve_profile
from validation.reporting import Issue, Report, normalize_cerberus_errors
from validation.schema_registry import get_schema, get_schema_version
from validation.semantic import (
    Registries,
    check_execution_consistency,
    check_query_registry_version,
    check_registry_references,
    check_schema_version,
    check_temporal_semantics,
    scan_for_secrets,
)

__all__ = ["ValidationOutcome", "validate_full"]


@dataclass
class ValidationOutcome:
    """One target's outcome; ``to_report`` renders the stable JSON report."""

    schema_id: str
    target: str
    profile: str
    valid: bool
    issues: list[Issue] = field(default_factory=list)
    legacy: LegacyRecord | None = None

    def to_report(self) -> Report:
        return Report(
            schema_id=self.schema_id,
            target=self.target,
            valid=self.valid,
            issues=list(self.issues),
            profile=self.profile,
            legacy=self.legacy.to_dict() if self.legacy is not None else None,
        )


def _verify_run_artifacts(document, base_dir, artifact_registry=None) -> list[Issue]:
    manifest_name = document.get("artifact_manifest")
    if not isinstance(manifest_name, str) or not manifest_name:
        return []
    base = Path(base_dir)
    return verify_artifact_manifest(
        base / manifest_name, base_dir=base, artifact_registry=artifact_registry
    )


def validate_full(
    document,
    *,
    schema_id: str,
    target: str = "",
    profile: str = "strict",
    registries: Registries | None = None,
    base_dir=None,
    verify_artifacts: bool = False,
    extra_checks=(),
) -> ValidationOutcome:
    """Run the full layer stack for one document.

    ``extra_checks`` are semantic check callables appended after the
    built-ins; they only run when structural validation succeeded (the order
    contract is observable through this hook).

    Raises ``ValueError`` for unknown schema IDs and
    ``validation.legacy.LegacyProfileNotAllowed`` when the legacy profile is
    requested for a run outside the frozen list.
    """
    schema = get_schema(schema_id)
    schema_version = get_schema_version(schema_id)
    effective_profile = resolve_profile(profile, document)

    if effective_profile == "legacy_audit":
        record = audit_record(document, schema)
        return ValidationOutcome(
            schema_id=schema_id,
            target=target,
            profile=effective_profile,
            valid=True,
            issues=[],
            legacy=record,
        )

    structural = validate_document(document, schema)
    if not structural.valid:
        issues = normalize_cerberus_errors(
            structural.errors, schema_version=schema_version
        )
        return ValidationOutcome(
            schema_id=schema_id,
            target=target,
            profile=effective_profile,
            valid=False,
            issues=issues,
        )

    issues: list[Issue] = []
    issues.extend(check_schema_version(document, schema_id))
    issues.extend(check_temporal_semantics(document))
    issues.extend(check_execution_consistency(document))
    if registries is not None:
        issues.extend(check_registry_references(document, registries))
        # G5 P17: version-traceability is advisory only (warning/info),
        # so wiring it here cannot turn an existing strict pass into a
        # failure; a missing query registry disables it (repository
        # convention for missing registries).
        issues.extend(check_query_registry_version(document, registries))
    issues.extend(scan_for_secrets(document))
    for check in extra_checks:
        issues.extend(check(document))
    if verify_artifacts and base_dir is not None:
        issues.extend(
            _verify_run_artifacts(
                document,
                base_dir,
                artifact_registry=(
                    registries.artifact_registry if registries is not None else None
                ),
            )
        )

    # Re-stamp issues produced by semantic checks with the contract version so
    # the report has one stable schema_version per target.
    issues = [
        Issue(
            code=issue.code,
            path=issue.path,
            severity=issue.severity,
            message=issue.message,
            rule=issue.rule,
            schema_version=issue.schema_version or schema_version,
        )
        for issue in issues
    ]
    issues.sort(key=lambda issue: issue.sort_key())

    valid = not any(issue.severity == "error" for issue in issues)
    return ValidationOutcome(
        schema_id=schema_id,
        target=target,
        profile=effective_profile,
        valid=valid,
        issues=issues,
    )
