"""G6 §13 private data catalog frame (existence only, values never read).

Contract sources
----------------
- G6 instruction §13 (private data catalog) and §4 (storage / tracking /
  publication are three independent axes): ``docs/plans/20261013f.md``.
- AGENTS.md first-party / social data rules win on any conflict.

Scope
-----
``build_private_catalog`` records the *boundary* between publishable and
non-publishable data: for each known private marker it reports existence,
git tracking state and publication status.  File contents are never opened,
listed, counted or hashed; no value, identifier or secret ever enters the
report.  The catalog itself is publication-reviewed before any release
(f.md §13: catalog contents also need review).
"""

from __future__ import annotations

from pathlib import Path

from validation.g6_inventory import KNOWN_PRIVATE_MARKERS
from validation.storage_policy import git_ignored, git_tracked

__all__ = ["CATALOG_VERSION", "build_private_catalog"]

CATALOG_VERSION = "1.0.0"


def build_private_catalog(repo_root) -> dict:
    """Build the §13 boundary catalog (existence only)."""
    repo_root = Path(repo_root)
    entries: list[dict] = []
    for relative in KNOWN_PRIVATE_MARKERS:
        target = repo_root / relative
        exists = target.exists()
        entries.append(
            {
                "path": relative,
                "exists": exists,
                "tracked": git_tracked(repo_root, relative) if exists else False,
                "ignored": git_ignored(repo_root, relative),
                "classification": "restricted",
                "availability": "private",
                "publication_status": "not_approved",
                "note": "contents never inspected; existence and exclusion state only",
            }
        )
    present = sum(1 for entry in entries if entry["exists"])
    return {
        "catalog_version": CATALOG_VERSION,
        "spec": "docs/plans/20261013f.md §13 (local plan; not tracked)",
        "count": len(entries),
        "present": present,
        "absent": len(entries) - present,
        "entries": entries,
    }
