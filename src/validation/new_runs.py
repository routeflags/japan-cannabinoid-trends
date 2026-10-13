"""Runs outside the frozen legacy list must satisfy the current contract.

Why this exists
---------------
The live collectors write raw JSON to whatever path the caller asks for
(``src/collection/apify_run.sh``: ``<actor_id> <input_json> <out_base>``), with no
registry lookup, run identity, provenance or gate, and the framework's
``collection.core.cli collect`` is offline-replay only (``--fixture``, "live
collection is not executed here").  Nothing therefore stopped a live collection
from landing in ``datasets/`` without passing a gate -- the Phase 6 wiring gap.

``validate-all`` states the right rule (every run must satisfy the contract) but
cannot be the gate: the 29 frozen legacy runs make it exit 1 by design
(``docs/specs/validation-framework.md`` section 12).  This module states the rule
that CI *can* enforce: run ids named by ``validation.legacy.LEGACY_RUN_IDS`` are
grandfathered, and **every other run must pass strict validation including the
reference checks** against the query and study registries.

A pass here is not a certificate, and the audit is deliberately not vacuous: it
reports how many frozen runs it saw, so a rule that stopped matching anything
would be visible.  A run produced outside the framework cannot pass at all, because
it lacks the provenance fields the contract requires -- which is the point:
bypassing the framework becomes a CI failure instead of a silent act.

This is read-only.  It never writes into ``datasets/`` and never modifies a run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from validation.legacy import LEGACY_RUN_IDS
from validation.pipeline import validate_full
from validation.semantic import Registries

__all__ = [
    "AUDIT_VERSION",
    "NEW_RUN_SCHEMA_ID",
    "RUN_METADATA_NAME",
    "CheckedRun",
    "audit_new_runs",
]

AUDIT_VERSION = "1.0.0"

#: Schema every non-frozen run must satisfy (the current contract).
NEW_RUN_SCHEMA_ID = "collection-run-v1"

RUN_METADATA_NAME = "run_metadata.json"


@dataclass(frozen=True)
class CheckedRun:
    """One run found on disk and what the contract says about it."""

    run_id: str
    path: str
    frozen: bool
    valid: bool
    issue_codes: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "path": self.path,
            "frozen_legacy": self.frozen,
            "valid": self.valid,
            "issue_codes": list(self.issue_codes),
        }


def _iter_run_metadata(datasets_root: Path) -> list[Path]:
    if not datasets_root.is_dir():
        return []
    return sorted(datasets_root.rglob(RUN_METADATA_NAME))


def audit_new_runs(
    root: str | Path,
    datasets_root: str | Path,
    *,
    registries: Registries | None = None,
) -> dict:
    """Check every non-frozen run against the current contract.

    ``registries`` enables the reference checks (query / study registries).  When
    it is ``None`` those checks are skipped, which is weaker; callers that gate a
    commit should pass it.
    """

    root = Path(root).resolve()
    datasets = Path(datasets_root)
    if not datasets.is_absolute():
        datasets = root / datasets

    checked: list[CheckedRun] = []
    for path in _iter_run_metadata(datasets):
        relative = path.relative_to(root).as_posix()
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            checked.append(
                CheckedRun("", relative, False, False, ("RUN_METADATA_UNREADABLE",))
            )
            continue

        run_id = document.get("run_id") if isinstance(document, dict) else None
        run_id = run_id if isinstance(run_id, str) else ""

        if run_id and run_id in LEGACY_RUN_IDS:
            checked.append(CheckedRun(run_id, relative, True, True, ()))
            continue

        outcome = validate_full(
            document,
            schema_id=NEW_RUN_SCHEMA_ID,
            target=relative,
            profile="strict",
            registries=registries,
        )
        checked.append(
            CheckedRun(
                run_id,
                relative,
                False,
                bool(outcome.valid),
                tuple(issue.code for issue in outcome.issues),
            )
        )

    frozen = [entry for entry in checked if entry.frozen]
    new = [entry for entry in checked if not entry.frozen]
    failures = [entry for entry in new if not entry.valid]

    return {
        "audit_version": AUDIT_VERSION,
        "schema_id": NEW_RUN_SCHEMA_ID,
        "root": str(root),
        "datasets_root": str(datasets),
        "run_count": len(checked),
        "frozen_legacy_declared": len(LEGACY_RUN_IDS),
        "frozen_legacy_seen": len(frozen),
        "new_run_count": len(new),
        "failure_count": len(failures),
        "failures": [entry.to_dict() for entry in failures],
        "runs": [entry.to_dict() for entry in checked],
    }
