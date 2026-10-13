"""Legacy audit profile (Phase 8, h.md §18).

The repository contains 29 ``run_metadata.json`` files that predate the G5
contract (see ``docs/audits/g5-legacy-runs.json``).  Legacy runs must not be
forced through strict validation (h.md §18: "既存runには新規runと同じ必須条件を
無条件に適用しない"), but the legacy profile must not become a bypass for new
runs either ("Legacy Profileを使って新規runの検証を回避できないようにする").

Mechanism (rollout plan P8-3): a *frozen* allow-list of the run_ids observed
by the 2026-10-13 audit.  ``--profile legacy`` is only accepted for those
run_ids; a new run asking for the legacy profile is a configuration error.
The list is intentionally not auto-extending: adding a run_id requires a new
audit and a review (AGENTS.md: no silent reclassification).

``missing_required_paths`` walks the schema's ``required`` declarations and
reports only what is structurally absent.  It never guesses values ("推定で
埋めない") and never modifies the document.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA

__all__ = [
    "LEGACY_RUN_IDS",
    "LegacyProfileNotAllowed",
    "missing_required_paths",
    "resolve_profile",
    "audit_record",
    "LegacyRecord",
]

#: run_ids frozen by the 2026-10-13 legacy audit (P8-2).  Do not add new
#: entries without a fresh non-destructive audit; see docs/audits/.
#:
#: 2026-10-13 second pass: five Google Trends runs collected on 2026-10-12 (the
#: day before the framework landed) were imported with the origin branch.  They
#: are pre-framework records -- none carries ``schema_version``
#: (``test_frozen_runs_are_pre_framework`` enforces this) -- so they belong to
#: the audit rather than to the strict gate.  Runs collected after the
#: framework exists must never be added here.
LEGACY_RUN_IDS = frozenset(
    {
        "20261001T115959Z-google-trends-cbx-rikiddo",
        "20261001T121949Z-google-trends-h4cbh-hhbd",
        # Three run_ids deviate from their directory names; the audit records
        # the run_id value, not the directory (see docs/audits).
        "disambiguated_queries",
        "variance_check",
        "20261002T063821Z-google-trends-cbd",
        "20261002T063852Z-google-trends-thc",
        "20261002T063924Z-google-trends-cbg",
        "20261002T064008Z-google-trends-hhc",
        "20261002T064118Z-google-trends-thch",
        "20261002T064135Z-google-trends-nodata",
        "20261002T064236Z-google-trends-comparison-setA",
        "20261002T071255Z-google-trends-thc-o-5y",
        "20261002T080652Z-google-trends-h4cbh-5y",
        "20261002T080800Z-google-trends-hhbd-5y",
        "20261002T081839Z-google-trends-cbn-12m",
        "20261002T082000Z-google-trends-cbn-5y",
        "20261002T085022Z-google-trends-crdp-12m",
        "20261002T085359Z-google-trends-crdp-5y",
        "20261002T094657Z-google-trends-hhch-12m",
        "20261002T094730Z-google-trends-hhch-5y",
        "20261005T100000Z-google-trends-common-scale-expansion",
        "20261008T093228Z-google-trends-5y-baseline",
        "20261008T121338Z-google-trends-crdh-5y",
        "common-scale-missing-20261009",
        "20261012T054920Z-google-trends-notation-presurvey",
        "20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m",
        "20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m",
        "20261012T061614Z-google-trends-ja-rikiddo-phase-b-12m",
        "20261012T064246Z-google-trends-ja-rikiddo-5y-main5",
    }
)


class LegacyProfileNotAllowed(ValueError):
    """Raised when the legacy profile is requested for a non-legacy run."""


def resolve_profile(profile: str, document) -> str:
    """Return the effective profile, refusing legacy for unknown run_ids.

    ``profile`` is ``"strict"`` or ``"legacy"``.  The returned profile name
    for audit records is ``"legacy_audit"`` (h.md §18 format).
    """
    if profile == "strict":
        return "strict"
    if profile != "legacy":
        raise ValueError(f"Unknown profile: {profile}")
    run_id = document.get("run_id") if isinstance(document, dict) else None
    if run_id not in LEGACY_RUN_IDS:
        raise LegacyProfileNotAllowed(
            "legacy profile is only allowed for run_ids in the frozen legacy "
            f"audit list (got {run_id!r}); new runs must use strict validation"
        )
    return "legacy_audit"


@dataclass
class LegacyRecord:
    """h.md §18 audit record: profile / run_id / status / missing_fields."""

    run_id: str | None
    status: str
    missing_fields: list[str] = field(default_factory=list)
    sha256: str | None = None
    profile: str = "legacy_audit"

    def to_dict(self) -> dict:
        record = {
            "profile": self.profile,
            "run_id": self.run_id,
            "status": self.status,
            "missing_fields": list(self.missing_fields),
        }
        if self.sha256 is not None:
            record["sha256"] = self.sha256
        return record


def missing_required_paths(document, schema) -> list[str]:
    """Return the dotted paths of required fields absent from ``document``.

    Recurses into nested dict structures (``collector.collector_id``).  List
    items are not descended: the audit reports the registry-level absence
    only and never invents per-item conclusions.
    """
    if not isinstance(document, dict):
        return []
    missing: list[str] = []

    def walk(node, spec, prefix: str) -> None:
        if not isinstance(node, dict) or not isinstance(spec, dict):
            return
        for key, rules in spec.items():
            if not isinstance(rules, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if rules.get("required") and key not in node:
                missing.append(path)
                continue
            child = node.get(key)
            child_spec = rules.get("schema")
            if isinstance(child, dict) and isinstance(child_spec, dict):
                walk(child, child_spec, path)

    walk(document, schema, "")
    return missing


def audit_record(document, schema=COLLECTION_RUN_SCHEMA, *, sha256=None) -> LegacyRecord:
    """Build the legacy audit record for one document without modifying it."""
    run_id = document.get("run_id") if isinstance(document, dict) else None
    missing = missing_required_paths(document, schema)
    status = "incomplete" if missing else "complete"
    return LegacyRecord(
        run_id=run_id if isinstance(run_id, str) else None,
        status=status,
        missing_fields=missing,
        sha256=sha256,
    )
