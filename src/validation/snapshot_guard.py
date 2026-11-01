"""Preflight / postflight guard for ``make audit-snapshots``.

Why this exists
---------------
``make audit-snapshots`` rewrites eleven tracked reports from whatever raw
tree the current checkout happens to hold.  The raw layer is machine-local
(``.gitignore``: everything under ``data/raw/`` except Google Trends), so a
partial checkout produces a snapshot that is a mixture of two things:

- the runs it could see (a correct addition);
- the runs it could not see, whose rows disappear (a wrong deletion).

Re-running the target in that state silently rewrites provenance evidence.
This guard refuses before the first write:

- every run named by a committed catalog, a committed staging declaration, or
  an existing snapshot must have a raw directory with ``run_metadata.json`` in
  this checkout;
- an optional ``--expected-run-ids`` file can add runs the owner knows about
  but no committed claim names yet.  That makes "the expected full raw state"
  explicit instead of implicit in whatever disk happens to contain.

After the writes, ``--phase postflight`` compares the run ids in the new
snapshots with the ids recorded by the preflight state file.  A run id that was
present before and absent afterwards is a failure: no existing run may
disappear.  Additions are reported, not failed.

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

__all__ = [
    "GUARD_VERSION",
    "SNAPSHOT_FILES",
    "postflight",
    "preflight",
    "snapshot_run_ids",
]

GUARD_VERSION = "1.0.0"

#: The files ``make audit-snapshots`` writes, in Makefile order.  The two
#: recorded publication-gate invocations (``g6-*-publication-eligibility.json``)
#: are not part of that target and are deliberately absent.
SNAPSHOT_FILES = (
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
) -> dict:
    """Refuse a snapshot regeneration this checkout cannot substantiate."""

    claims = catalog_run_claims(datasets_root) + declaration_run_claims(
        declarations_dir
    )
    catalog_ids = {claim["run_id"] for claim in claims if "catalog" in claim["claimed_by"]}
    declaration_ids = {
        claim["run_id"] for claim in claims if "declaration" in claim["claimed_by"]
    }
    snapshots = snapshot_run_ids(audits_dir)
    extra_ids = _expected_file_ids(expected_run_ids) if expected_run_ids else []

    adopted_expected = set(catalog_ids) | set(declaration_ids) | set(extra_ids)
    expected: set[str] = adopted_expected | set(snapshots["union"])
    present_adopted = _present_ids(datasets_root, require_metadata=True)
    present_dirs = _present_ids(datasets_root, require_metadata=False)
    adopted_missing = sorted(adopted_expected - present_adopted)
    snapshot_missing = sorted(set(snapshots["union"]) - present_dirs)
    missing = sorted(set(adopted_missing) | set(snapshot_missing))
    present = present_dirs

    report = {
        "guard_version": GUARD_VERSION,
        "phase": "preflight",
        "datasets_root": str(datasets_root),
        "audits_dir": str(audits_dir),
        "declarations_dir": str(declarations_dir),
        "expected_run_id_count": len(expected),
        "present_raw_run_count": len(present),
        "adopted_missing_raw_count": len(adopted_missing),
        "missing_raw_run_count": len(missing),
        "snapshot_run_id_count": len(snapshots["union"]),
        "snapshot_missing_raw_count": len(snapshot_missing),
        "missing_snapshot_files": snapshots["missing_files"],
        "expected_run_ids": sorted(expected),
        "adopted_missing_run_ids": adopted_missing,
        "missing_run_ids": missing,
        "snapshot_missing_run_ids": snapshot_missing,
        "state_file": str(state_file) if state_file else None,
        "refused": bool(missing),
    }
    if state_file:
        _write_state(
            state_file,
            {
                "guard_version": GUARD_VERSION,
                "phase": "preflight",
                "snapshot_files": snapshots["per_file"],
                "snapshot_run_ids": snapshots["union"],
                "expected_run_ids": sorted(expected),
                "present_raw_run_ids": sorted(present),
                "adopted_missing_run_ids": adopted_missing,
                "missing_run_ids": missing,
            },
        )
    return report


def postflight(state_file, audits_dir) -> dict:
    """Fail if a run id that existed before the writes disappeared."""

    state_path = Path(state_file)
    if not state_path.is_file():
        raise ValueError(
            f"preflight state file is absent: {state_path}; run the preflight "
            "phase before regenerating snapshots"
        )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    before = set(state.get("snapshot_run_ids") or [])
    before_files = state.get("snapshot_files") or {}
    after = snapshot_run_ids(audits_dir)
    after_ids = set(after["union"])

    lost = sorted(before - after_ids)
    added = sorted(after_ids - before)
    lost_files = sorted(
        name for name in before_files if name not in after["per_file"]
    )
    expected = set(state.get("expected_run_ids") or [])

    return {
        "guard_version": GUARD_VERSION,
        "phase": "postflight",
        "audits_dir": str(audits_dir),
        "state_file": str(state_file),
        "before_run_id_count": len(before),
        "after_run_id_count": len(after_ids),
        "lost_run_id_count": len(lost),
        "added_run_id_count": len(added),
        "lost_run_ids": lost,
        "added_run_ids": added,
        "lost_files": lost_files,
        "expected_not_in_after": sorted(expected - after_ids),
        "refused": bool(lost or lost_files),
    }
