"""G6 §13 private data catalog frame (existence only, values never read).

Contract sources
----------------
- G6 instruction §13 (private data catalog) and §4 (storage / tracking /
  publication are three independent axes): ``docs/plans/20261013f.md``.
- AGENTS.md first-party / social data rules win on any conflict.

Scope
-----
``build_private_catalog`` records the *boundary* between publishable and
non-publishable data: for each known private marker it reports the declared
boundary, git tracking state and publication status.  File contents are never
opened, listed, counted or hashed; no value, identifier or secret ever enters
the report.  The catalog itself is publication-reviewed before any release
(f.md §13: catalog contents also need review).

Committed-safe default (ISS-20261016-MNT-002)
--------------------------------------------
Whether ``datasets/*/data/private`` exists on disk is a fact about *this
checkout*: the markers are gitignored, so a clean clone has none of them
while an owner's checkout may have some.  Recording disk existence in the
committed snapshot therefore churns with every checkout (``present`` /
``absent`` flip) while no repository fact changes.

The default output is therefore checkout-independent: per-entry ``exists``
and the ``present`` / ``absent`` totals are ``None`` (the keys stay so
readers keep one shape), and only repository facts are recorded -- the
declared boundary (``classification`` / ``availability`` /
``publication_status``), the rule-based exclusion state (``ignored``), and
the index fact (``tracked``; like §25's ``tracked_only`` rule, whether a
path is tracked is a repository fact, stable across clean checkouts).
``make audit-snapshots`` uses this mode, so regeneration no longer dirties
the committed file.

Pass ``include_local_state=True`` (CLI ``--include-local-state``) to
inspect this checkout's disk instead: ``exists`` becomes a real boolean
and ``present`` / ``absent`` count it.  Local-mode output must not be
committed over the snapshot (the freshness test pins the default mode
exactly).
"""

from __future__ import annotations

from pathlib import Path

from validation.g6_inventory import KNOWN_PRIVATE_MARKERS
from validation.storage_policy import git_ignored, git_tracked

__all__ = ["CATALOG_VERSION", "build_private_catalog"]

CATALOG_VERSION = "1.0.0"


def build_private_catalog(repo_root, *, include_local_state: bool = False) -> dict:
    """Build the §13 boundary catalog (existence only).

    ``include_local_state=False`` (default) records repository facts only:
    ``exists`` / ``present`` / ``absent`` are ``None`` and the output is
    identical on every checkout of the same commit.  Pass ``True`` to also
    record this checkout's disk state (never commit that output over
    ``docs/audits/g6-private-catalog.json``).
    """
    repo_root = Path(repo_root)
    entries: list[dict] = []
    for relative in KNOWN_PRIVATE_MARKERS:
        target = repo_root / relative
        exists = target.exists() if include_local_state else None
        # The markers are directories, so the ignore rule is checked in its
        # directory form: ``.gitignore`` declares ``datasets/*/data/private/``,
        # and git matches a trailing-slash path against a directory-only pattern
        # even when nothing exists there.  Without the slash a checkout that
        # does not have the private data reads "not ignored", which would make
        # this catalog depend on the checkout instead of the rule
        # (ISS-20261015-AUD-028).
        #
        # ``tracked`` stays a live index lookup in both modes: whether a path
        # is tracked is a repository fact, stable across clean checkouts of
        # the same commit (an absent or ignored marker reads False).  Only
        # disk existence is local, so only ``exists`` / ``present`` /
        # ``absent`` are gated on ``include_local_state``
        # (ISS-20261016-MNT-002).
        as_directory = f"{relative}/"
        entries.append(
            {
                "path": relative,
                "exists": exists,
                "tracked": git_tracked(repo_root, relative),
                "ignored": git_ignored(repo_root, as_directory),
                "classification": "restricted",
                "availability": "private",
                "publication_status": "not_approved",
                "note": "contents never inspected; existence and exclusion state only",
            }
        )
    if include_local_state:
        present: int | None = sum(1 for entry in entries if entry["exists"])
        absent: int | None = len(entries) - present
    else:
        present = None
        absent = None
    return {
        "catalog_version": CATALOG_VERSION,
        "spec": "docs/plans/20261013f.md §13 (local plan; not tracked)",
        "include_local_state": include_local_state,
        "count": len(entries),
        "present": present,
        "absent": absent,
        "entries": entries,
    }
