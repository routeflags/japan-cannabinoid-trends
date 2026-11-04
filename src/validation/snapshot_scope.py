"""What a Git checkout can reproduce from the audit snapshots (ISS-20261105-CI-032).

The audit snapshots under ``docs/audits/`` are *checkout-local* inventories:
``docs/audits/snapshot-scope.json`` records ``audit_scope: checkout_local`` and
lists the runs whose raw is ``git_untracked`` (``not_repository_retained_run_ids``).
Those runs exist on the machine that collected them and never in a fresh clone,
so a snapshot generated there carries per-run rows and aggregate counts that CI
cannot reproduce - and CI is where the freshness tests run.

The rule this module implements: **compare the repository-retained view on both
sides**.  A snapshot keeps its local rows (nothing is deleted); before comparing,
the non-retained rows and the aggregates that count local raw are removed from
both the committed document and the regenerated one.  What remains is the part
every checkout must agree on: the retained runs, their paths and hashes, and the
non-numeric facts.

``raw_combined_sha256`` is dropped for the same reason: it hashes every raw file
on disk, so it changes with the checkout's visibility, not with the repository.
"""

from __future__ import annotations

import json
from pathlib import Path

#: String fields that hash or describe local raw as a whole.
_RAW_DEPENDENT_FIELDS = frozenset({"raw_combined_sha256"})


def non_retained_run_ids(repo_root: Path) -> set[str]:
    """Run ids the sidecar declares as ``git_untracked`` (not repository-retained)."""

    sidecar = repo_root / "docs" / "audits" / "snapshot-scope.json"
    document = json.loads(sidecar.read_text(encoding="utf-8"))
    return set(document.get("not_repository_retained_run_ids") or ())


def retained_view(document, non_retained: set[str]):
    """Drop the facts that depend on raw this checkout happens to have."""

    if isinstance(document, dict):
        return {
            key: retained_view(value, non_retained)
            for key, value in document.items()
            if key not in _RAW_DEPENDENT_FIELDS
            and not (isinstance(value, (int, float)) and not isinstance(value, bool))
        }
    if isinstance(document, list):
        return [
            retained_view(item, non_retained)
            for item in document
            if not (isinstance(item, dict) and item.get("run_id") in non_retained)
        ]
    return document
