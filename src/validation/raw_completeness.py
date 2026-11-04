"""Committed claims about raw runs versus the raw layer on this checkout.

Why this exists
The catalog (``datasets/<study>/metadata/data-catalog.json``), every committed
``staging-declaration-v1`` document and every active raw-retention decision
name runs that belong to the raw layer.  That directory is machine-local:
``.gitignore`` excludes ``**/data/raw/*`` except Google Trends, so a clone or a
partial worktree can carry the claims without the payloads.
Nothing reported that gap, and two failure modes looked identical from the
committed files alone:

- the run was never adopted (a real backlog item);
- the run was adopted somewhere else and this checkout cannot substantiate it
  (a portability fact, not a data error).

A third state was added by the raw-retention contract
(``docs/specs/raw-data-policy.md`` §5): a run can be deliberately
``git_untracked`` as Repository Storage because platform terms, copyright or
redistribution constraints forbid committing the payload.  That run is not
missing.  The repository keeps non-content provenance, and a machine-local
copy may exist or not.  This audit separates the declared retention status
from machine-local presence instead of collapsing both into ``missing``.

This audit reports the second and third states explicitly.  It is read-only
and checkout-local by design: a missing directory says "this checkout cannot
show the raw run", never "the run does not exist".

What is checked
---------------
1. every catalog run id, declared run id and retention-decision run id
   resolves by its declared retention status:

   - ``git_tracked``: the run must be present with ``run_metadata.json`` in
     this checkout (or tracked in the Git index but not checked out), and it
     must not be local-only;
   - ``git_untracked``: absence is expected and reported as
     ``not_repository_retained``; local presence is reported as
     ``local_only_present``.  The payload must not be in the Git index.

2. every declaration-correction record under
   ``metadata/provenance/corrections/`` pins the declaration bytes it claims to
   correct (SHA-256) and names runs that the referenced declaration contains.
3. a declaration whose study has no catalog is reported, not failed.
4. retention decisions are validated by ``validation.raw_retention``; an
   invalid decision cannot excuse an absent run (the status falls back to the
   storage policy, or fails closed to ``git_tracked``).

Exit status is the CLI's decision: a missing ``git_tracked`` run and a
retention violation are findings (exit 1); an absent ``data/raw/`` root is not
an exception.

Deterministic output: no timestamps, all collections sorted, no cost fields.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validation.raw_retention import (
    GIT_TRACKED,
    GIT_UNTRACKED,
    assess_retention,
    load_retention,
    retention_run_claims,
    run_prefixes,
    tracked_repo_paths,
)

__all__ = [
    "AUDIT_VERSION",
    "DECLARATION_VERSION",
    "CORRECTION_RECORD",
    "MISSING_STATES",
    "SCOPE_VERSION",
    "build_raw_completeness",
    "build_snapshot_scope",
    "catalog_run_claims",
    "declaration_run_claims",
    "present_raw_runs",
]

AUDIT_VERSION = "1.1.0"
SCOPE_VERSION = "1.0.0"
DECLARATION_VERSION = "staging-declaration-v1"
CORRECTION_RECORD = "declaration_correction"
RUN_METADATA_NAME = "run_metadata.json"

#: States that mean a ``git_tracked`` run cannot be substantiated.
MISSING_STATES = ("missing_directory", "missing_run_metadata")


def _normalize_source(value: str) -> str:
    """Directory spelling differs from the registry id for Google Trends."""

    return value.replace("-", "_").lower()


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_paths(datasets: Path) -> list[Path]:
    if not datasets.is_dir():
        return []
    return sorted(datasets.glob("*/metadata/data-catalog.json"))


def catalog_run_claims(datasets_root) -> list[dict]:
    """One claim per ``(study_id, source_id, run_id)`` named by a catalog."""

    datasets = Path(datasets_root)
    claims: list[dict] = []
    for path in _catalog_paths(datasets):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        entries = document.get("entries")
        if not isinstance(entries, list):
            continue
        study_from_path = path.parent.parent.name
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            run_id = entry.get("run_id")
            source_id = entry.get("source_id")
            if not isinstance(run_id, str) or not run_id:
                continue
            if not isinstance(source_id, str) or not source_id:
                continue
            study_id = entry.get("study_id")
            if not isinstance(study_id, str) or not study_id:
                study_id = study_from_path
            claims.append(
                {
                    "study_id": study_id,
                    "source_id": source_id,
                    "run_id": run_id,
                    "claimed_by": "catalog",
                    "reference": path.relative_to(datasets.parent).as_posix()
                    if datasets.parent in path.parents
                    else path.as_posix(),
                }
            )
    return _merge_claims(claims)


def declaration_run_claims(declarations_dir) -> list[dict]:
    """One claim per run declared in a ``staging-declaration-v1`` document."""

    directory = Path(declarations_dir)
    claims: list[dict] = []
    if not directory.is_dir():
        return claims
    for path in sorted(directory.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        if document.get("declaration_version") != DECLARATION_VERSION:
            continue
        runs = document.get("runs")
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, dict):
                continue
            run_id = run.get("run_id")
            study_id = run.get("study_id")
            source_id = run.get("source_id")
            if not all(isinstance(value, str) and value for value in (run_id, study_id, source_id)):
                continue
            claims.append(
                {
                    "study_id": study_id,
                    "source_id": source_id,
                    "run_id": run_id,
                    "claimed_by": "declaration",
                    "reference": path.name,
                }
            )
    return _merge_claims(claims)


def _merge_claims(claims: list[dict]) -> list[dict]:
    """Merge duplicate claims, keeping every reference that names the run."""

    merged: dict[tuple[str, str, str], dict] = {}
    for claim in claims:
        key = (claim["study_id"], claim["source_id"], claim["run_id"])
        record = merged.setdefault(
            key,
            {
                "study_id": claim["study_id"],
                "source_id": claim["source_id"],
                "run_id": claim["run_id"],
                "claimed_by": [],
                "references": [],
            },
        )
        kinds = claim.get("claimed_by")
        kinds = kinds if isinstance(kinds, list) else [kinds]
        for kind in kinds:
            if kind and kind not in record["claimed_by"]:
                record["claimed_by"].append(kind)
        references = claim.get("references")
        if not isinstance(references, list):
            references = [
                {"kind": claim.get("claimed_by"), "path": claim.get("reference")}
            ]
        for reference in references:
            if reference not in record["references"]:
                record["references"].append(reference)
    for record in merged.values():
        record["claimed_by"].sort()
        record["references"].sort(key=lambda item: (item["kind"], item["path"]))
    return [merged[key] for key in sorted(merged)]


def present_raw_runs(datasets_root) -> dict[str, list[dict]]:
    """Map run id -> every raw location that carries that id on this checkout.

    A directory is recorded even when ``run_metadata.json`` is missing: the
    payload may exist while its metadata does not, and the claim check has to
    distinguish the two.
    """

    datasets = Path(datasets_root)
    present: dict[str, list[dict]] = {}
    if not datasets.is_dir():
        return present
    for study_dir in sorted(p for p in datasets.iterdir() if p.is_dir()):
        raw_root = study_dir / "data" / "raw"
        if not raw_root.is_dir():
            continue
        for source_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
            for run_dir in sorted(p for p in source_dir.iterdir() if p.is_dir()):
                if run_dir.name.startswith("."):
                    continue
                metadata = run_dir / RUN_METADATA_NAME
                present.setdefault(run_dir.name, []).append(
                    {
                        "study_id": study_dir.name,
                        "source_id": source_dir.name,
                        "directory_present": True,
                        "run_metadata_present": metadata.is_file(),
                    }
                )
    for locations in present.values():
        locations.sort(key=lambda item: (item["study_id"], item["source_id"]))
    return present


def _correction_violations(repo_root: Path, corrections_dir: Path) -> tuple[list[dict], list[dict]]:
    """Check correction records against the declaration bytes they pin."""

    records: list[dict] = []
    violations: list[dict] = []
    if not corrections_dir.is_dir():
        return records, violations
    for path in sorted(corrections_dir.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            violations.append(
                {"path": path.name, "reason": "correction_record_unreadable"}
            )
            continue
        if document.get("record") != CORRECTION_RECORD:
            continue
        original = document.get("original_declarations")
        corrected = document.get("corrected_declarations")
        original_runs: set[str] = set()
        checked_paths: list[str] = []
        for section_name, section in (
            ("original_declarations", original),
            ("corrected_declarations", corrected),
        ):
            if section is None:
                continue
            if not isinstance(section, list):
                violations.append(
                    {"path": path.name, "reason": f"{section_name}_not_a_list"}
                )
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue
                relative = item.get("path")
                pinned = item.get("sha256")
                if not isinstance(relative, str) or not relative:
                    violations.append(
                        {"path": path.name, "reason": f"{section_name}_path_missing"}
                    )
                    continue
                target = repo_root / relative
                checked_paths.append(relative)
                if not target.is_file():
                    violations.append(
                        {
                            "path": path.name,
                            "reason": f"{section_name}_file_absent",
                            "reference": relative,
                        }
                    )
                    continue
                if not isinstance(pinned, str) or _sha256(target) != pinned:
                    violations.append(
                        {
                            "path": path.name,
                            "reason": f"{section_name}_sha256_mismatch",
                            "reference": relative,
                        }
                    )
                    continue
                if section_name == "original_declarations":
                    declaration = _load_json(target)
                    runs = declaration.get("runs") if isinstance(declaration, dict) else None
                    if isinstance(runs, list):
                        original_runs.update(
                            run.get("run_id")
                            for run in runs
                            if isinstance(run, dict) and isinstance(run.get("run_id"), str)
                        )
        corrections = document.get("corrections")
        if isinstance(corrections, list):
            for entry in corrections:
                if not isinstance(entry, dict):
                    continue
                run_id = entry.get("run_id")
                if isinstance(run_id, str) and run_id and run_id not in original_runs:
                    violations.append(
                        {
                            "path": path.name,
                            "reason": "corrected_run_id_not_in_original_declaration",
                            "run_id": run_id,
                        }
                    )
        records.append(
            {
                "path": path.name,
                "correction_id": document.get("correction_id"),
                "status": document.get("status"),
                "checked_declaration_paths": sorted(set(checked_paths)),
            }
        )
    return records, violations


def build_raw_completeness(
    datasets_root,
    declarations_dir,
    corrections_dir=None,
    repo_root=".",
    retention_dir=None,
) -> dict:
    """Report which committed raw-run claims this checkout can substantiate."""

    datasets = Path(datasets_root)
    retention = load_retention(repo_root, retention_dir)
    aliases = retention["study_aliases"]
    claims = (
        catalog_run_claims(datasets)
        + declaration_run_claims(declarations_dir)
        + retention_run_claims(retention)
    )
    merged = _merge_claims(claims)
    present = present_raw_runs(datasets)
    tracked = tracked_repo_paths(repo_root)

    runs: list[dict] = []
    retention_violations = list(retention["violations"])
    for claim in merged:
        resolved_study = aliases.get(claim["study_id"], claim["study_id"])
        locations = present.get(claim["run_id"], [])
        matched = [
            location
            for location in locations
            if location["study_id"] == resolved_study
            and _normalize_source(location["source_id"])
            == _normalize_source(claim["source_id"])
        ]
        metadata_present = any(
            location["run_metadata_present"] for location in matched
        )
        assessment = assess_retention(
            retention,
            claim["study_id"],
            claim["source_id"],
            claim["run_id"],
            prefixes=run_prefixes(
                datasets,
                resolved_study,
                claim["source_id"],
                claim["run_id"],
                repo_root,
            ),
            tracked=tracked,
        )

        if assessment["retention_status"] == GIT_TRACKED:
            if matched and metadata_present:
                state = (
                    "present_not_git_tracked"
                    if assessment["tracking_mismatch"]
                    else "present"
                )
            elif matched:
                state = "missing_run_metadata"
            elif assessment["git_tracking_state"] == "tracked":
                state = "tracked_not_checked_out"
            else:
                state = "missing_directory"
        else:
            if assessment["git_tracking_state"] == "tracked":
                state = "git_untracked_but_tracked"
            elif matched:
                state = "local_only_present"
            else:
                state = "not_repository_retained"

        if state in ("present_not_git_tracked", "git_untracked_but_tracked"):
            retention_violations.append(
                {
                    "study_id": claim["study_id"],
                    "source_id": claim["source_id"],
                    "run_id": claim["run_id"],
                    "reason": assessment["tracking_mismatch"],
                    "path": assessment["retention_decision_path"]
                    or assessment["retention_reference"],
                }
            )

        runs.append(
            {
                **claim,
                "resolved_study_id": resolved_study,
                "state": state,
                "locations": matched,
                "retention_status": assessment["retention_status"],
                "retention_source": assessment["retention_source"],
                "retention_policy_id": assessment["retention_policy_id"],
                "retention_policy_git_tracking": assessment[
                    "retention_policy_git_tracking"
                ],
                "retention_policy_status": assessment["retention_policy_status"],
                "retention_reference": assessment["retention_reference"],
                "retention_decision_id": assessment["retention_decision_id"],
                "retention_decision_reference": assessment[
                    "retention_decision_reference"
                ],
                "retention_decision_path": assessment["retention_decision_path"],
                "publication_status": assessment["publication_status"],
                "publication_source": assessment["publication_source"],
                "publication_decision_reference": assessment[
                    "publication_decision_reference"
                ],
                "git_tracking_state": assessment["git_tracking_state"],
                "tracked_file_count": assessment["tracked_file_count"],
            }
        )

    missing = [run for run in runs if run["state"] in MISSING_STATES]
    not_repository_retained = [
        run for run in runs if run["state"] == "not_repository_retained"
    ]
    local_only_present = [
        run for run in runs if run["state"] == "local_only_present"
    ]
    retention_violations.sort(
        key=lambda item: (
            str(item.get("path") or ""),
            str(item.get("reason") or ""),
            str(item.get("study_id") or ""),
            str(item.get("source_id") or ""),
            str(item.get("run_id") or ""),
        )
    )
    catalog_studies = {
        aliases.get(claim["study_id"], claim["study_id"])
        for claim in catalog_run_claims(datasets)
    }
    declaration_studies = {
        aliases.get(claim["study_id"], claim["study_id"])
        for claim in declaration_run_claims(declarations_dir)
    }
    corrections, correction_violations = (
        _correction_violations(Path(repo_root), Path(corrections_dir))
        if corrections_dir
        else ([], [])
    )
    not_repository_retained_ids = sorted(
        {run["run_id"] for run in runs if run["retention_status"] == GIT_UNTRACKED}
    )
    locally_visible_states = {
        "present",
        "local_only_present",
        "present_not_git_tracked",
        "git_untracked_but_tracked",
    }
    raw_visibility = (
        "complete"
        if all(run["state"] in locally_visible_states for run in runs)
        else "partial"
    )

    return {
        "audit_version": AUDIT_VERSION,
        "datasets_root": str(datasets),
        "declarations_dir": str(declarations_dir),
        "retention_dir": retention["retention_dir"],
        "claim_count": len(runs),
        "catalog_run_count": sum(1 for claim in catalog_run_claims(datasets)),
        "declaration_run_count": sum(
            1 for claim in declaration_run_claims(declarations_dir)
        ),
        "retention_record_count": len(retention["records"]),
        "retention_decision_run_count": len(retention["run_entries"]),
        "retention_policy_available": retention["policy_available"],
        "tracked_index_available": tracked["available"],
        "present_count": sum(1 for run in runs if run["state"] == "present"),
        "tracked_not_checked_out_count": sum(
            1 for run in runs if run["state"] == "tracked_not_checked_out"
        ),
        "missing_count": len(missing),
        "missing_directory_count": sum(
            1 for run in missing if run["state"] == "missing_directory"
        ),
        "missing_run_metadata_count": sum(
            1 for run in missing if run["state"] == "missing_run_metadata"
        ),
        "not_repository_retained_count": len(not_repository_retained),
        "local_only_present_count": len(local_only_present),
        "git_tracked_claim_count": sum(
            1 for run in runs if run["retention_status"] == GIT_TRACKED
        ),
        "git_untracked_claim_count": sum(
            1 for run in runs if run["retention_status"] == GIT_UNTRACKED
        ),
        "retention_violation_count": len(retention_violations),
        "declaration_studies_without_catalog": sorted(
            declaration_studies - catalog_studies
        ),
        "catalog_studies_without_declaration": sorted(
            catalog_studies - declaration_studies
        ),
        "corrections": corrections,
        "correction_violation_count": len(correction_violations),
        "correction_violations": correction_violations,
        "retention_violations": retention_violations,
        "failure_count": len(missing)
        + len(correction_violations)
        + len(retention_violations),
        "runs": runs,
        "missing": missing,
        "not_repository_retained": not_repository_retained,
        "local_only_present": local_only_present,
        "audit_scope": "checkout_local",
        "raw_visibility": raw_visibility,
        "raw_visibility_basis": "checkout-local raw payload visibility",
        "not_repository_retained_run_ids": not_repository_retained_ids,
    }


def build_snapshot_scope(
    datasets_root,
    declarations_dir,
    repo_root=".",
    retention_dir=None,
) -> dict:
    """Deterministic scope declaration for ``docs/audits`` snapshots.

    The snapshots are inventories of *this checkout*, not a reconstruction of
    the complete research state.  This sidecar records that scope, preserves
    the committed catalog/declaration claims whose raw is ``git_untracked``,
    and states that a run absent from a snapshot is not an uncollected or zero
    observation.  It never reads a raw payload and generates no raw rows.
    """

    retention = load_retention(repo_root, retention_dir)
    merged = _merge_claims(
        catalog_run_claims(datasets_root)
        + declaration_run_claims(declarations_dir)
        + retention_run_claims(retention)
    )

    runs: list[dict] = []
    git_tracked_ids: set[str] = set()
    git_untracked_ids: set[str] = set()
    for claim in merged:
        resolved_study = retention["study_aliases"].get(
            claim["study_id"], claim["study_id"]
        )
        assessment = assess_retention(
            retention,
            claim["study_id"],
            claim["source_id"],
            claim["run_id"],
        )
        if assessment["retention_status"] == GIT_TRACKED:
            git_tracked_ids.add(claim["run_id"])
            availability = "git_tracked"
            raw_dependent_facts = "not_recorded_in_scope"
        else:
            git_untracked_ids.add(claim["run_id"])
            availability = "not_repository_retained"
            raw_dependent_facts = "unavailable"
        runs.append(
            {
                "run_id": claim["run_id"],
                "study_id": claim["study_id"],
                "resolved_study_id": resolved_study,
                "source_id": claim["source_id"],
                "claim_sources": claim["claimed_by"],
                "references": claim["references"],
                "retention_status": assessment["retention_status"],
                "retention_source": assessment["retention_source"],
                "retention_policy_id": assessment["retention_policy_id"],
                "retention_decision_id": assessment["retention_decision_id"],
                "availability": availability,
                "raw_dependent_facts": raw_dependent_facts,
                "record_count": None,
                "sha256": None,
            }
        )
    runs.sort(key=lambda item: (item["study_id"], item["source_id"], item["run_id"]))

    return {
        "schema_version": SCOPE_VERSION,
        "generated_by": "validation.cli audit-snapshot-scope",
        "audit_scope": "checkout_local",
        "raw_visibility": "partial",
        "raw_visibility_basis": (
            "snapshots are inventories of this checkout; raw payloads are "
            "machine-local and may be absent"
        ),
        "complete_provenance_claim": [
            "datasets/*/metadata/data-catalog.json",
            "metadata/provenance/declarations/*.json",
        ],
        "absence_interpretation": (
            "a run absent from a snapshot is not an uncollected or zero "
            "observation; the catalog and declarations are the complete "
            "provenance claim"
        ),
        "raw_rows_generated": False,
        "raw_dependent_facts": "unavailable",
        "retention_policy_registry": "config/storage-policies.json",
        "retention_policy_available": retention["policy_available"],
        "retention_record_count": len(retention["records"]),
        "retention_violation_count": len(retention["violations"]),
        "retention_violations": retention["violations"],
        "claim_count": len(merged),
        "git_tracked_run_count": len(git_tracked_ids),
        "git_untracked_run_count": len(git_untracked_ids),
        "git_tracked_run_ids": sorted(git_tracked_ids),
        "not_repository_retained_run_ids": sorted(git_untracked_ids),
        "runs": runs,
    }
