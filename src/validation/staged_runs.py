"""Lightweight pre-commit guard for staged collection-run metadata.

Policy (decided 2026-10-15, ``ISS-20261015-COL-020``):

- The pre-commit hook is stdlib-only, so it cannot run the Cerberus-based
  ``validation.pipeline``.  This module checks only what the standard library
  can check: every staged ``datasets/*/data/raw/*/*/run_metadata.json`` is
  read **from the Git index** (``git show :<path>``), must be valid JSON, must
  carry a non-empty string ``run_id``, and -- unless frozen -- must carry the
  minimal provenance keys listed in :data:`REQUIRED_PROVENANCE_PATHS`.
- Frozen legacy runs are exempt.  The exemption reuses the CI gate's own
  source of truth, :data:`validation.legacy.LEGACY_RUN_IDS`, keyed on exact
  ``run_id`` equality.  A missing or non-string ``run_id`` is never exempt
  (fail closed, mirroring ``validation.new_runs.audit_new_runs``).
- Everything else -- types, temporal provenance, registry references,
  artifact manifests -- stays in CI (``python -m validation.cli
  audit-new-runs``).  A pass here is not a certificate; it only catches
  obvious omissions before commit.

The guard is read-only: it inspects staged blobs and writes nothing.  Error
output names only the staged path and the missing dotted paths (or a fixed
``malformed JSON`` label); staged payload content is never printed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import PurePosixPath

from validation.legacy import LEGACY_RUN_IDS

__all__ = [
    "AUDIT_VERSION",
    "REQUIRED_PROVENANCE_PATHS",
    "RUN_METADATA_NAME",
    "audit_staged_runs",
    "check_document",
    "is_run_metadata_path",
    "main",
]

AUDIT_VERSION = "1.0.0"

RUN_METADATA_NAME = "run_metadata.json"

#: Minimal provenance presence check for a non-frozen staged run.  This is a
#: deliberately reduced subset of the ``collection-run-v1`` required fields
#: (``src/validation/schemas/collection_run.py``): presence of these keys is
#: what lets CI perform the full strict check at all.  Types, allowed values,
#: temporal provenance, registry references and artifact verification are
#: CI-only and intentionally not repeated here.
REQUIRED_PROVENANCE_PATHS = (
    "study_id",
    "source_id",
    "collector.collector_id",
    "collector.adapter_id",
    "collection_started_at",
    "query_provenance.query_id",
    "execution.status",
    "execution.returned_count",
    "execution.errors",
)

#: What this guard does not do (kept next to the scope so the two cannot
#: drift apart without review).
CI_ONLY_SCOPE = (
    "type and value validation (Cerberus collection-run-v1), "
    "temporal_provenance, registry references, artifact manifests"
)


def is_run_metadata_path(path: str) -> bool:
    """True for a cataloged raw run metadata path.

    ``datasets/<study>/data/raw/<source>/<run-id>/run_metadata.json``
    (``COL-018(a)``); deeper nesting below ``raw/`` is also checked
    (conservative: a ``run_metadata.json`` under ``data/raw/`` is by
    definition a run record, so an unexpected layout should be inspected,
    not silently skipped).
    """

    parts = PurePosixPath(path).parts
    if len(parts) < 7:
        return False
    if parts[0] != "datasets":
        return False
    if parts[2] != "data" or parts[3] != "raw":
        return False
    return parts[-1] == RUN_METADATA_NAME


def _is_present(document, dotted: str) -> bool:
    """True when the dotted path exists and is not null.

    Intermediate nodes must be mappings; a ``None`` value counts as missing
    because the CI contract cannot validate it either.
    """

    node = document
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return node is not None


def check_document(document) -> tuple[str, bool, list[str]]:
    """Check one parsed metadata document.

    Returns ``(run_id, frozen_legacy, missing)`` where ``missing`` holds the
    deterministically sorted dotted paths absent from the document.
    """

    run_id = document.get("run_id") if isinstance(document, dict) else None
    if not isinstance(run_id, str) or not run_id:
        missing = ["run_id"]
        if isinstance(document, dict):
            missing.extend(
                path for path in REQUIRED_PROVENANCE_PATHS if not _is_present(document, path)
            )
        else:
            missing.extend(REQUIRED_PROVENANCE_PATHS)
        return ("", False, sorted(set(missing)))
    if run_id in LEGACY_RUN_IDS:
        return (run_id, True, [])
    if not isinstance(document, dict):
        return (run_id, False, sorted(REQUIRED_PROVENANCE_PATHS))
    return (
        run_id,
        False,
        sorted(path for path in REQUIRED_PROVENANCE_PATHS if not _is_present(document, path)),
    )


def _staged_paths(root: str) -> list[str]:
    """Repository-relative staged paths (added/copied/modified/renamed)."""

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        cwd=root,
        capture_output=True,
        text=False,
        check=False,
    )
    if result.returncode != 0:
        raise OSError(f"git diff --cached failed (exit {result.returncode})")
    return [entry for entry in result.stdout.split(b"\x00") if entry]


def _staged_blob(root: str, path: str) -> bytes:
    """Raw bytes of the staged blob, read from the index (never the worktree)."""

    result = subprocess.run(
        ["git", "show", f":{path}"],
        cwd=root,
        capture_output=True,
        text=False,
        check=False,
    )
    if result.returncode != 0:
        raise OSError(f"cannot read staged blob from the Git index: {path}")
    return result.stdout


def audit_staged_runs(root: str, *, staged: list[str] | None = None) -> dict:
    """Audit staged run metadata blobs.  Read-only; writes nothing.

    ``staged`` overrides the staged-path list (repository-relative paths),
    which lets tests exercise the report without a throwaway git repository;
    blobs are otherwise always read from the Git index.
    """

    candidates = sorted(
        {path for path in (staged if staged is not None else [
            entry.decode("utf-8", "surrogateescape") for entry in _staged_paths(root)
        ]) if is_run_metadata_path(path)}
    )

    checked: list[dict] = []
    for path in candidates:
        try:
            blob = _staged_blob(root, path)
        except OSError:
            checked.append(
                {
                    "path": path,
                    "run_id": "",
                    "frozen_legacy": False,
                    "valid": False,
                    "unreadable": True,
                    "missing": [],
                }
            )
            continue
        try:
            document = json.loads(blob.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            checked.append(
                {
                    "path": path,
                    "run_id": "",
                    "frozen_legacy": False,
                    "valid": False,
                    "unreadable": True,
                    "missing": [],
                }
            )
            continue
        run_id, frozen, missing = check_document(document)
        checked.append(
            {
                "path": path,
                "run_id": run_id,
                "frozen_legacy": frozen,
                "valid": not missing,
                "unreadable": False,
                "missing": missing,
            }
        )

    failures = [entry for entry in checked if not entry["valid"]]
    return {
        "audit_version": AUDIT_VERSION,
        "root": root,
        "candidate_count": len(candidates),
        "frozen_legacy_seen": sum(1 for entry in checked if entry["frozen_legacy"]),
        "failure_count": len(failures),
        "failures": failures,
        "checked": checked,
    }


def main(argv: list[str] | None = None) -> int:
    """Stdlib-only entry point: ``python3 -m validation.staged_runs``.

    The pre-commit hook runs before a virtualenv can be assumed, and
    ``validation.cli`` pulls in Cerberus (via ``validation.core``), so the
    hook calls this module directly -- the same arrangement as
    ``validation.x_identity``.  CI uses ``python -m validation.cli
    audit-new-runs``, which remains authoritative.

    Exit codes: 0 clean (or nothing staged), 1 findings, 2 git/index error.
    """

    parser = argparse.ArgumentParser(prog="python -m validation.staged_runs")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    try:
        report = audit_staged_runs(args.repo_root)
    except OSError as error:
        print(f"staged-run guard cannot read the Git index: {error}", file=sys.stderr)
        return 2

    for entry in report["failures"]:
        if entry["unreadable"]:
            print(f"{entry['path']}: malformed JSON (staged blob is not valid UTF-8 JSON)")
        else:
            print(f"{entry['path']}: missing {', '.join(entry['missing'])}")
    print(
        f"staged-run guard (lightweight local check): "
        f"checked={report['candidate_count']} "
        f"failures={report['failure_count']} "
        f"frozen_legacy_seen={report['frozen_legacy_seen']}. "
        f"Full strict validation ({CI_ONLY_SCOPE}) remains in CI: "
        f"python -m validation.cli audit-new-runs.",
        file=sys.stderr,
    )
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
