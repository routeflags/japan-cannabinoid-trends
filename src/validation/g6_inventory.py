"""G6 §15 git tracking inventory (non-destructive, read-only).

Contract sources
----------------
- G6 instruction §8 (git tracking validator, judgment table), §9 (ignore
  policy), §15 (legacy tracking audit): ``docs/plans/20261013f.md``.
- AGENTS.md Git rules (never commit secrets / customer data / unreviewed
  sensitive raw) win on any conflict.

Scope
-----
Read-only classification of the real working tree into:

- ``tracked`` (in the git index),
- ``ignored`` (untracked + matched by an ignore rule),
- ``untracked_unignored`` (neither tracked nor ignored; accidental-add risk),
- ``absent`` (a known local-only path that does not exist in this checkout;
  absence is recorded as absent, never as zero content - P8).

``private/`` contents are never opened: only the directory's existence and
its ignore state are recorded.  No file is added, removed or committed and
no history is rewritten.  Raw files are hashed before and after the scan
and ``raw_modified`` records any drift (like the G4 inventory).
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.integrity import sha256_file
from validation.storage_policy import git_ignored, git_tracked

__all__ = [
    "INVENTORY_VERSION",
    "KNOWN_LOCAL_ONLY_PATHS",
    "build_git_tracking_inventory",
    "classify_path",
]

INVENTORY_VERSION = "1.0.0"

#: Local-only paths that exist in some checkouts but are never publication
#: candidates.  They are classified by existence + ignore state; absent paths
#: are recorded as ``absent`` (P8: missing is not zero).  ``private/`` entries
#: are directories: their contents are never listed or opened.
KNOWN_LOCAL_ONLY_PATHS = (
    "trends.db",
    "datasets/x-consistency/data/trends.db",
    "datasets/youtube-consistency/data/trends.db",
    ".staging",
    ".quarantine",
    "tmp",
    ".venv",
)

#: Private-data boundary markers (existence + ignore state only).
KNOWN_PRIVATE_MARKERS = (
    "datasets/cbx-social-trends/data/private",
    "datasets/cbx-search-trends/data/private",
    "datasets/cannabinoid-multi-trends/data/private",
    "datasets/cannabinoid-social-trends/data/private",
    "datasets/cbx-liquid-online-trend/data/private",
    "datasets/cbx-product-coa/data/private",
    "datasets/x-26week-trends/data/private",
    "datasets/x-consistency/data/private",
    "datasets/youtube-consistency/data/private",
)

_DANGEROUS_BLANKET_PATTERNS = ("*.csv", "*.json", "*.db", "*")


def classify_path(root: Path, relative: str) -> dict:
    """Classify one repository-relative path (read-only git only)."""
    target = root / relative
    exists = target.exists()
    if not exists:
        return {
            "path": relative,
            "exists": False,
            "state": "absent",
            "tracked": False,
            "ignored": git_ignored(root, relative),
        }
    tracked = git_tracked(root, relative)
    ignored = git_ignored(root, relative)
    if tracked:
        state = "tracked"
    elif ignored:
        state = "ignored"
    else:
        state = "untracked_unignored"
    return {
        "path": relative,
        "exists": True,
        "state": state,
        "tracked": tracked,
        "ignored": ignored,
    }


def _iter_dataset_files(datasets_root: Path, *, include_private: bool):
    for path in sorted(datasets_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in (".gitkeep", ".gitignore"):
            continue
        if not include_private and "private" in path.parts:
            continue
        yield path


def build_git_tracking_inventory(
    repo_root,
    *,
    datasets_root=None,
    include_private: bool = False,
) -> dict:
    """Build the §15 tracking inventory (read-only, non-destructive)."""
    repo_root = Path(repo_root)
    datasets_root = Path(datasets_root) if datasets_root is not None else repo_root / "datasets"
    entries: list[dict] = []
    hash_before: dict[str, str | None] = {}
    if datasets_root.is_dir():
        for path in _iter_dataset_files(datasets_root, include_private=include_private):
            try:
                relative = str(path.relative_to(repo_root))
            except ValueError:
                relative = str(path)
            try:
                hash_before[relative] = sha256_file(path)
            except OSError:
                hash_before[relative] = None
            record = classify_path(repo_root, relative)
            record["sha256"] = hash_before[relative]
            entries.append(record)
    # Key non-dataset paths: audits (must stay tracked), exports, plans
    # (local-only), known local-only paths and private markers.
    extra_paths: list[str] = []
    for name in ("docs/audits", "exports/taxonomy", "docs/plans"):
        candidate = repo_root / name
        if candidate.is_dir():
            for path in sorted(candidate.iterdir()):
                if path.is_file():
                    try:
                        extra_paths.append(str(path.relative_to(repo_root)))
                    except ValueError:
                        continue
    extra_paths.extend(KNOWN_LOCAL_ONLY_PATHS)
    extra_paths.extend(KNOWN_PRIVATE_MARKERS)
    extras: list[dict] = []
    for relative in extra_paths:
        # ``private`` markers are directories: never list contents.
        target = repo_root / relative
        if "private" in Path(relative).parts and target.is_dir():
            extras.append(
                {
                    "path": relative,
                    "exists": True,
                    "state": "ignored" if git_ignored(repo_root, relative) else (
                        "tracked" if git_tracked(repo_root, relative) else "untracked_unignored"
                    ),
                    "tracked": git_tracked(repo_root, relative),
                    "ignored": git_ignored(repo_root, relative),
                    "kind": "private_marker",
                }
            )
            continue
        if target.is_dir() and relative not in KNOWN_LOCAL_ONLY_PATHS and "private" not in Path(relative).parts:
            continue
        record = classify_path(repo_root, relative)
        record["kind"] = "private_marker" if "private" in Path(relative).parts else "local_only"
        extras.append(record)
    # Raw immutability evidence: re-hash dataset files after the scan.
    raw_modified = False
    for entry in entries:
        relative = entry["path"]
        try:
            after = sha256_file(repo_root / relative)
        except OSError:
            after = None
        entry["sha256_after"] = after
        entry["unchanged"] = after == entry.get("sha256")
        if entry["unchanged"] is False:
            raw_modified = True
    states: dict[str, int] = {}
    for entry in entries + extras:
        states[entry["state"]] = states.get(entry["state"], 0) + 1
    # Dangerous-pattern screen: a policy or ignore rule that would silently
    # swallow broad file classes (G6 §9 warns against blanket application).
    # Values are never emitted; only rule text is quoted.
    warnings: list[dict] = []
    try:
        gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")
    except OSError:
        gitignore_text = ""
    for lineno, line in enumerate(gitignore_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        if stripped in _DANGEROUS_BLANKET_PATTERNS:
            warnings.append(
                {
                    "code": "GITIGNORE_BLANKET_PATTERN",
                    "path": f".gitignore:{lineno}",
                    "pattern": stripped,
                    "note": "blanket ignore pattern risks hiding research data; keep exclusions scoped",
                }
            )
    # Untracked + unignored dataset files are a future accidental-add risk
    # (G6-T06): list paths only, never values.
    at_risk = sorted(entry["path"] for entry in entries if entry["state"] == "untracked_unignored")
    return {
        "audit_version": INVENTORY_VERSION,
        "profile": "g6_git_tracking_inventory",
        "spec": "docs/plans/20261013f.md §15 (local plan; not tracked)",
        "target_root": str(datasets_root.relative_to(repo_root)) if datasets_root.is_relative_to(repo_root) else str(datasets_root),
        "include_private": include_private,
        "count": len(entries),
        "extra_count": len(extras),
        "raw_modified": raw_modified,
        "state_summary": dict(sorted(states.items())),
        "entries": entries,
        "extras": extras,
        "accidental_add_risk": at_risk,
        "ignore_warnings": warnings,
    }
