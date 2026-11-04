"""Preflight / postflight guard for ``make audit-snapshots``.

Why this exists
---------------
``make audit-snapshots`` rewrites eleven tracked reports and the deterministic
scope sidecar from whatever raw tree the current checkout happens to hold.  The raw layer is machine-local
(``.gitignore``: everything under ``data/raw/`` except Google Trends), so a
partial checkout produces a snapshot that is a mixture of two things:

- the runs it could see (a correct addition);
- the runs it could not see, whose rows disappear (a wrong deletion).

The guard has to separate a genuinely missing repository run from a run whose
payload is deliberately ``git_untracked`` (``docs/specs/raw-data-policy.md``
§5).  A ``git_untracked`` run is not missing: its raw payload is not Repository
Storage, so an absent ``data/raw/`` directory is the expected state on a
clone.  Snapshots are **checkout-local inventories**, not reconstructions of
the complete research state (owner decision 2026-11-02).  The committed catalog
and declarations remain the complete provenance claim;
``docs/audits/snapshot-scope.json`` records the scope and the
``not_repository_retained_run_ids``.

This guard refuses before the first write when:

- a run that resolves to ``git_tracked`` has no raw directory with
  ``run_metadata.json`` in this checkout (or no tracked payload in the index);
- a retention decision is invalid (missing reason/reference, unresolved
  reference, conflicting decisions), so "intentionally untracked" is not
  proven.

A ``git_untracked`` run may be absent; that is not a refusal.  If a
``git_untracked`` run is nevertheless present in the Git index, the guard
reports ``retention_git_untracked_but_tracked`` as a warning (the hard failure
is ``make audit-raw-retention``), because the final instruction is that only
``git_tracked`` raw loss/inconsistency blocks the snapshot run.

``git_untracked`` runs are excluded from the missing set and recorded as
``not_repository_retained_run_ids``.  An optional ``--expected-run-ids`` file
can add runs the owner knows about but no committed claim names yet.

After the writes, ``--phase postflight`` compares the run ids in the new
snapshots with the ids recorded by the preflight state file.  Only a
``git_tracked`` run id that was present before and absent afterwards is a
failure.  A raw-derived row for a ``git_untracked`` run may disappear and is
reported as ``intentionally_dropped_run_ids``; that is an intentional
non-repository-retained state, not a zero observation.  Additions are reported,
not failed.

Read-only with one deliberate exception: the preflight writes its state file
(``.staging/audit-snapshot-guard.json`` by default in the Makefile) so the
postflight can compare the same checkout.  It never writes a snapshot and never
touches raw.  Output is deterministic: sorted ids, no timestamps, no cost
fields.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from validation.raw_completeness import (
    catalog_run_claims,
    declaration_run_claims,
    present_raw_runs,
)
from validation.raw_retention import (
    GIT_TRACKED,
    assess_retention,
    load_retention,
    retention_run_claims,
    run_prefixes,
    tracked_repo_paths,
)

__all__ = [
    "GUARD_VERSION",
    "SCOPE_FILE",
    "SNAPSHOT_FILES",
    "postflight",
    "preflight",
    "snapshot_run_ids",
]

GUARD_VERSION = "1.2.0"

#: The deterministic scope sidecar.  It carries the committed claim list, not
#: raw-derived snapshot rows, so its ``run_id`` values are deliberately not
#: counted as snapshot run ids (the postflight must still notice a raw-derived
#: row that disappeared).
SCOPE_FILE = "snapshot-scope.json"

#: The files ``make audit-snapshots`` writes, in Makefile order: the deterministic
#: scope sidecar first, then eleven raw-derived snapshots.  The two recorded
#: publication-gate invocations (``g6-*-publication-eligibility.json``) are not
#: part of that target and are deliberately absent.
SNAPSHOT_FILES = (
    "snapshot-scope.json",
    "contract-ledger.json",
    "g2-query-inventory.json",
    "gt-summary.json",
    "publication-contract.json",
    "g3-temporal-inventory.json",
    "g4-storage-inventory.json",
    "g5-legacy-runs.json",
    "g5-provenance-assessment.json",
    "g6-git-tracking-inventory.json",
    "g6-private-catalog.json",
    "g7-study-inventory.json",
)


#: The documented run-id form (AGENTS.md "Run Identity").  Snapshots also
#: use ``run_id`` as a label in a few non-run places (a query id, a status
#: word), so a bare key match is not enough to treat a string as a raw run.
_RUN_ID_FORM = re.compile(r"^[0-9]{8}T[0-9]{6}Z-")


def _collect_run_ids(value, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "run_id" and isinstance(item, str) and _RUN_ID_FORM.match(item):
                found.add(item)
            elif key == "run_ids" and isinstance(item, list):
                found.update(
                    entry
                    for entry in item
                    if isinstance(entry, str) and _RUN_ID_FORM.match(entry)
                )
            else:
                _collect_run_ids(item, found)
    elif isinstance(value, list):
        for item in value:
            _collect_run_ids(item, found)


def snapshot_run_ids(audits_dir) -> dict:
    """Run ids recorded by each snapshot that exists, plus their union."""

    directory = Path(audits_dir)
    per_file: dict[str, list[str]] = {}
    missing: list[str] = []
    union: set[str] = set()
    for name in SNAPSHOT_FILES:
        path = directory / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            missing.append(name)
            continue
        found: set[str] = set()
        if name != SCOPE_FILE:
            _collect_run_ids(document, found)
        per_file[name] = sorted(found)
        union.update(found)
    return {
        "per_file": per_file,
        "union": sorted(union),
        "missing_files": missing,
    }


def _expected_file_ids(path) -> list[str]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(document, dict):
        document = document.get("run_ids")
    if not isinstance(document, list) or not all(
        isinstance(entry, str) and entry for entry in document
    ):
        raise ValueError(
            "--expected-run-ids must be a JSON array of non-empty run ids "
            "(or an object with a 'run_ids' array)"
        )
    return sorted(set(document))


def _present_ids(datasets_root, *, require_metadata: bool) -> set[str]:
    return {
        run_id
        for run_id, locations in present_raw_runs(datasets_root).items()
        if any(
            location["directory_present"]
            and (location["run_metadata_present"] or not require_metadata)
            for location in locations
        )
    }


def _write_state(path, document: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def preflight(
    datasets_root,
    audits_dir,
    declarations_dir,
    *,
    expected_run_ids=None,
    state_file=None,
    repo_root=None,
    retention_dir=None,
) -> dict:
    """Refuse a snapshot regeneration this checkout cannot substantiate."""

    repo_root = Path(repo_root) if repo_root is not None else Path(datasets_root).parent
    retention = load_retention(repo_root, retention_dir)
    tracked = tracked_repo_paths(repo_root)
    claims = (
        catalog_run_claims(datasets_root)
        + declaration_run_claims(declarations_dir)
        + retention_run_claims(retention)
    )
    catalog_ids = {claim["run_id"] for claim in claims if "catalog" in claim["claimed_by"]}
    declaration_ids = {
        claim["run_id"] for claim in claims if "declaration" in claim["claimed_by"]
    }
    retention_ids = {
        claim["run_id"]
        for claim in claims
        if "retention_decision" in claim["claimed_by"]
    }
    snapshots = snapshot_run_ids(audits_dir)
    extra_ids = _expected_file_ids(expected_run_ids) if expected_run_ids else []

    assessments: dict[str, list[dict]] = {}
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        key = (claim["study_id"], claim["source_id"], claim["run_id"])
        if key in seen:
            continue
        seen.add(key)
        resolved_study = retention["study_aliases"].get(
            claim["study_id"], claim["study_id"]
        )
        assessments.setdefault(claim["run_id"], []).append(
            assess_retention(
                retention,
                claim["study_id"],
                claim["source_id"],
                claim["run_id"],
                prefixes=run_prefixes(
                    datasets_root,
                    resolved_study,
                    claim["source_id"],
                    claim["run_id"],
                    repo_root,
                ),
                tracked=tracked,
            )
        )

    def is_repository_retained(run_id: str) -> bool:
        """A run with no claim, or any git_tracked claim, stays strict."""

        entries = assessments.get(run_id)
        if not entries:
            return True
        return any(entry["retention_status"] == GIT_TRACKED for entry in entries)

    adopted_expected = (
        set(catalog_ids) | set(declaration_ids) | set(retention_ids) | set(extra_ids)
    )
    expected: set[str] = adopted_expected | set(snapshots["union"])
    retained_expected = {run_id for run_id in expected if is_repository_retained(run_id)}
    not_retained = sorted(expected - retained_expected)
    present_adopted = _present_ids(datasets_root, require_metadata=True)
    present_dirs = _present_ids(datasets_root, require_metadata=False)
    adopted_missing = sorted(
        (adopted_expected & retained_expected) - present_adopted
    )
    snapshot_missing = sorted(
        (set(snapshots["union"]) & retained_expected) - present_dirs
    )
    missing = sorted(set(adopted_missing) | set(snapshot_missing))
    present = present_dirs

    retention_violations = list(retention["violations"])
    retention_warnings: list[dict] = []
    recorded: set[tuple[str, str]] = set()
    for run_id in sorted(expected):
        for entry in assessments.get(run_id, []):
            if not entry["tracking_mismatch"]:
                continue
            key = (entry["tracking_mismatch"], run_id)
            if key in recorded:
                continue
            recorded.add(key)
            record = {
                "study_id": entry["study_id"],
                "source_id": entry["source_id"],
                "run_id": run_id,
                "reason": entry["tracking_mismatch"],
                "path": entry["retention_decision_path"]
                or entry["retention_reference"],
            }
            if entry["tracking_mismatch"] == "retention_git_untracked_but_tracked":
                # The hard failure lives in ``audit-raw-retention``; the snapshot
                # guard only blocks git_tracked loss/inconsistency.
                retention_warnings.append(record)
            else:
                retention_violations.append(record)
    for collection in (retention_violations, retention_warnings):
        collection.sort(
            key=lambda item: (
                str(item.get("path") or ""),
                str(item.get("reason") or ""),
                str(item.get("study_id") or ""),
                str(item.get("source_id") or ""),
                str(item.get("run_id") or ""),
            )
        )

    report = {
        "guard_version": GUARD_VERSION,
        "phase": "preflight",
        "audit_scope": "checkout_local",
        "raw_visibility": "partial",
        "datasets_root": str(datasets_root),
        "audits_dir": str(audits_dir),
        "declarations_dir": str(declarations_dir),
        "retention_dir": retention["retention_dir"],
        "retention_policy_available": retention["policy_available"],
        "tracked_index_available": tracked["available"],
        "retention_record_count": len(retention["records"]),
        "expected_run_id_count": len(expected),
        "present_raw_run_count": len(present),
        "not_repository_retained_run_count": len(not_retained),
        "adopted_missing_raw_count": len(adopted_missing),
        "missing_raw_run_count": len(missing),
        "snapshot_run_id_count": len(snapshots["union"]),
        "snapshot_missing_raw_count": len(snapshot_missing),
        "retention_violation_count": len(retention_violations),
        "retention_warning_count": len(retention_warnings),
        "missing_snapshot_files": snapshots["missing_files"],
        "expected_run_ids": sorted(expected),
        "not_repository_retained_run_ids": not_retained,
        "adopted_missing_run_ids": adopted_missing,
        "missing_run_ids": missing,
        "snapshot_missing_run_ids": snapshot_missing,
        "retention_violations": retention_violations,
        "retention_warnings": retention_warnings,
        "state_file": str(state_file) if state_file else None,
        "refused": bool(missing or retention_violations),
    }
    if state_file:
        _write_state(
            state_file,
            {
                "guard_version": GUARD_VERSION,
                "phase": "preflight",
                "audit_scope": "checkout_local",
                "raw_visibility": "partial",
                "snapshot_files": snapshots["per_file"],
                "snapshot_run_ids": snapshots["union"],
                "expected_run_ids": sorted(expected),
                "not_repository_retained_run_ids": not_retained,
                "present_raw_run_ids": sorted(present),
                "adopted_missing_run_ids": adopted_missing,
                "missing_run_ids": missing,
                "retention_warning_count": len(retention_warnings),
            },
        )
    return report


def postflight(state_file, audits_dir) -> dict:
    """Fail if a retained run id that existed before the writes disappeared."""

    state_path = Path(state_file)
    if not state_path.is_file():
        raise ValueError(
            f"preflight state file is absent: {state_path}; run the preflight "
            "phase before regenerating snapshots"
        )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    before = set(state.get("snapshot_run_ids") or [])
    before_files = state.get("snapshot_files") or {}
    not_retained = set(state.get("not_repository_retained_run_ids") or [])
    after = snapshot_run_ids(audits_dir)
    after_ids = set(after["union"])

    disappeared = before - after_ids
    lost = sorted(disappeared - not_retained)
    intentionally_dropped = sorted(disappeared & not_retained)
    added = sorted(after_ids - before)
    lost_files = sorted(
        name for name in before_files if name not in after["per_file"]
    )
    expected = set(state.get("expected_run_ids") or [])

    return {
        "guard_version": GUARD_VERSION,
        "phase": "postflight",
        "audit_scope": state.get("audit_scope", "checkout_local"),
        "raw_visibility": state.get("raw_visibility", "partial"),
        "audits_dir": str(audits_dir),
        "state_file": str(state_file),
        "before_run_id_count": len(before),
        "after_run_id_count": len(after_ids),
        "lost_run_id_count": len(lost),
        "intentionally_dropped_run_id_count": len(intentionally_dropped),
        "added_run_id_count": len(added),
        "lost_run_ids": lost,
        "intentionally_dropped_run_ids": intentionally_dropped,
        "not_repository_retained_run_ids": sorted(not_retained),
        "added_run_ids": added,
        "lost_files": lost_files,
        "expected_not_in_after": sorted(expected - after_ids - not_retained),
        "refused": bool(lost or lost_files),
    }
