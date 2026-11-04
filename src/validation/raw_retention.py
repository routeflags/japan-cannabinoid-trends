"""Raw retention: Repository Storage (Git tracking), not local raw existence.

Why this exists
---------------
The raw layer is machine-local: ``.gitignore`` excludes ``**/data/raw/*``
except Google Trends, so a checkout can hold committed claims about a run
without the payload.  Two different situations looked identical from the
committed files alone:

- the raw payload is supposed to be Repository Storage and is absent (a real
  gap);
- the raw payload is deliberately not Repository Storage because platform
  terms, copyright or redistribution constraints forbid committing it (a
  storage decision, not a missing run).

The second run still exists.  A machine-local copy may sit under
``data/raw/`` and the repository retains only non-content provenance: query,
request conditions, timestamps, counts, hashes when available, aggregate or
derived evidence, and the decision reference.

Contract
--------
``docs/specs/raw-data-policy.md`` §5.  The vocabulary has exactly two values:

- ``git_tracked``: the raw payload is retained as Repository Storage.  It is
  committed under Git and a clone can substantiate the run from the tracked
  tree.
- ``git_untracked``: the raw payload is not Repository Storage.  It is never
  added to Git; a local copy may exist in an ignored directory, and the
  repository keeps only non-content provenance.  Local presence is not
  retention.

The words ``retainable`` / ``not_retainable`` are deliberately not used: they
were read as "a local raw copy exists", which is a different question.

Where the status comes from
---------------------------
1. A per-run decision in
   ``metadata/provenance/retention/<date>-<slug>.json``
   (``record: "raw_retention_decision"``).  A decision is the only way an
   owner, legal or publication review can set the state, and it always carries
   ``reason`` and a resolvable ``decision_reference``.
2. Otherwise the ``artifact_layer: raw`` policy in
   ``config/storage-policies.json`` for the source ``kind`` in
   ``config/sources.json`` -- the same policy that governs ``.gitignore``.
3. If that registry is unavailable the status fails closed to ``git_tracked``:
   a missing registry never excuses an absent run.

``retention_status`` and publication are independent axes.  The decision
record carries ``publication_status`` separately, and this module never treats
a tracking status as permission to publish (or the reverse).  The validator
records the decision; it does not decide whether a platform term or a law
permits repository storage.

Read-only and deterministic: no timestamps, sorted output, no cost fields.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from validation.schemas.storage_policy import PUBLICATION_STATES
from validation.storage_policy import select_policy

__all__ = [
    "GIT_TRACKED",
    "GIT_UNTRACKED",
    "PUBLICATION_STATUSES",
    "RELATED_AUDITS",
    "RETENTION_DECISION",
    "RETENTION_DIR",
    "RETENTION_STATUSES",
    "RETENTION_VERSION",
    "assess_retention",
    "build_retention_report",
    "load_retention",
    "retention_run_claims",
    "run_prefixes",
    "study_aliases",
    "tracked_repo_paths",
]

RETENTION_VERSION = "1.0.0"
RETENTION_DIR = "metadata/provenance/retention"
RETENTION_DECISION = "raw_retention_decision"
GIT_TRACKED = "git_tracked"
GIT_UNTRACKED = "git_untracked"
RETENTION_STATUSES = (GIT_TRACKED, GIT_UNTRACKED)

#: Reuse the publication vocabulary instead of inventing a second one.  The
#: two axes are independent: this field says whether the raw payload may be
#: published, not whether it may be committed.
PUBLICATION_STATUSES = tuple(PUBLICATION_STATES)

#: Existing audits this contract aligns with (actual index state and the
#: private-data boundary).  Referenced in the report so readers do not treat
#: this audit as a replacement for either.
RELATED_AUDITS = ("g6-git-tracking", "g6-private-catalog")

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RUN_KEYS = ("study_id", "source_id", "run_id")


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _normalize_source(value: str) -> str:
    """Directory spelling differs from the registry id for Google Trends."""

    return value.replace("-", "_").lower()


def _non_empty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.name


def _resolves(repo_root: Path, reference) -> bool:
    """True when ``reference`` is a repository-relative path to a file."""

    if not _non_empty(reference):
        return False
    root = repo_root.resolve()
    target = (root / reference).resolve()
    return target.is_relative_to(root) and target.is_file()


def study_aliases(repo_root) -> dict[str, str]:
    """Recorded study id -> the study directory name that holds its raw.

    Shared by the retention and completeness audits so a renamed study
    resolves the same way in both.
    """

    document = _load_json(
        Path(repo_root) / "metadata" / "studies" / "study-registry.json"
    )
    aliases: dict[str, str] = {}
    studies = document.get("studies") if isinstance(document, dict) else None
    if not isinstance(studies, list):
        return aliases
    for study in studies:
        if not isinstance(study, dict):
            continue
        current = study.get("study_id")
        if not _non_empty(current):
            continue
        aliases[current] = current
        for previous in study.get("previous_study_ids") or []:
            if _non_empty(previous):
                aliases[previous] = current
    return aliases


# ---------------------------------------------------------------------------
# Storage-policy default
# ---------------------------------------------------------------------------


def _policy_status(policy: dict) -> tuple[str, str | None]:
    """Map one raw-layer policy to the two-state vocabulary.

    ``conditional`` cannot excuse absence (the run is still expected in the
    repository once the condition is met), and an unknown value fails closed.
    """

    tracking = policy.get("git_tracking")
    if tracking == "ignored":
        return GIT_UNTRACKED, tracking
    return GIT_TRACKED, tracking if isinstance(tracking, str) else None


def _policy_resolution(model: dict, source_id: str) -> dict:
    """Resolve the raw-layer storage policy for one source."""

    kind = model["source_kinds"].get(_normalize_source(source_id))
    policy = None
    if model["policy_document"] is not None:
        policy = select_policy(
            model["policy_document"], artifact_layer="raw", source_kind=kind
        )
    if not isinstance(policy, dict):
        return {
            "retention_status": GIT_TRACKED,
            "retention_source": "fail_closed",
            "retention_policy_id": None,
            "retention_policy_git_tracking": None,
            "retention_reference": None,
            "publication_status": "unknown",
            "publication_source": "unavailable",
        }
    status, tracking = _policy_status(policy)
    publication = policy.get("publication")
    if publication not in PUBLICATION_STATUSES:
        publication = "unknown"
    policy_id = policy.get("policy_id")
    return {
        "retention_status": status,
        "retention_source": "storage_policy",
        "retention_policy_id": policy_id if _non_empty(policy_id) else None,
        "retention_policy_git_tracking": tracking,
        "retention_reference": (
            f"config/storage-policies.json#{policy_id}"
            if _non_empty(policy_id)
            else "config/storage-policies.json"
        ),
        "publication_status": publication,
        "publication_source": "storage_policy",
    }


# ---------------------------------------------------------------------------
# Decision records
# ---------------------------------------------------------------------------


def _record_violation(path: str, reason: str, **extra) -> dict:
    return {"path": path, "reason": reason, **extra}


def _parse_record(
    document: dict, path: str, repo_root: Path
) -> tuple[dict, list[dict]]:
    violations: list[dict] = []

    def bad(reason: str, **extra) -> None:
        violations.append(_record_violation(path, reason, **extra))

    if not _non_empty(document.get("schema_version")):
        bad("retention_schema_version_missing")

    decision_id = document.get("retention_decision_id")
    if not _non_empty(decision_id):
        bad("retention_decision_id_missing")
        decision_id = None

    decided_at = document.get("decided_at")
    if not (_non_empty(decided_at) and _DATE.fullmatch(decided_at)):
        bad("retention_decided_at_invalid")

    decided_by = document.get("decided_by")
    if not _non_empty(decided_by):
        bad("retention_decided_by_missing")

    status = document.get("retention_status")
    if status not in RETENTION_STATUSES:
        bad("retention_status_invalid")
        status = None

    reason = document.get("reason")
    if not _non_empty(reason):
        bad("retention_reason_missing")

    reference = document.get("decision_reference")
    if not _non_empty(reference):
        bad("retention_decision_reference_missing")
    elif not _resolves(repo_root, reference):
        bad("retention_decision_reference_unresolved", reference=reference)

    publication = document.get("publication_status")
    if publication not in PUBLICATION_STATUSES:
        bad("publication_status_invalid")
        publication = None
    publication_reason = document.get("publication_reason")
    if publication == "denied" and not _non_empty(publication_reason):
        bad("publication_reason_missing")

    publication_reference = document.get("publication_decision_reference")
    if publication_reference is not None:
        if not _non_empty(publication_reference):
            bad("publication_decision_reference_missing")
        elif not _resolves(repo_root, publication_reference):
            bad(
                "publication_decision_reference_unresolved",
                reference=publication_reference,
            )

    raw_supersedes = document.get("supersedes", [])
    supersedes: list[str] = []
    if not isinstance(raw_supersedes, list) or not all(
        _non_empty(entry) for entry in raw_supersedes
    ):
        bad("retention_supersedes_invalid")
    else:
        supersedes = list(raw_supersedes)

    runs: list[dict] = []
    raw_runs = document.get("runs")
    if not isinstance(raw_runs, list) or not raw_runs:
        bad("retention_runs_missing")
    else:
        for index, item in enumerate(raw_runs):
            if not isinstance(item, dict) or not all(
                _non_empty(item.get(key)) for key in _RUN_KEYS
            ):
                bad("retention_run_invalid", run_index=index)
                continue
            runs.append({key: item[key] for key in _RUN_KEYS})

    record = {
        "path": path,
        "retention_decision_id": decision_id,
        "decided_at": decided_at,
        "decided_by": decided_by,
        "retention_status": status,
        "reason": reason,
        "decision_reference": reference,
        "publication_status": publication,
        "publication_reason": publication_reason,
        "publication_decision_reference": publication_reference,
        "supersedes": supersedes,
        "runs": runs,
        "superseded": False,
        "valid": not violations,
    }
    return record, violations


def _decision_key(
    aliases: dict[str, str], study_id: str, source_id: str, run_id: str
) -> tuple[str, str, str]:
    return (
        aliases.get(study_id, study_id),
        _normalize_source(source_id),
        run_id,
    )


def _sorted_violations(violations: list[dict]) -> list[dict]:
    return sorted(
        violations,
        key=lambda item: (
            str(item.get("path") or ""),
            str(item.get("reason") or ""),
            str(item.get("study_id") or ""),
            str(item.get("source_id") or ""),
            str(item.get("run_id") or ""),
            str(item.get("run_index", "")),
            str(item.get("reference") or ""),
        ),
    )


def load_retention(repo_root=".", retention_dir=None) -> dict:
    """Load decisions and the policy default; never writes anything."""

    repo_root = Path(repo_root)
    directory = (
        Path(retention_dir) if retention_dir is not None else repo_root / RETENTION_DIR
    )
    aliases = study_aliases(repo_root)

    policy_document = _load_json(repo_root / "config" / "storage-policies.json")
    if not isinstance(policy_document, dict):
        policy_document = None
    source_document = _load_json(repo_root / "config" / "sources.json")
    source_kinds: dict[str, str] = {}
    sources = source_document.get("sources") if isinstance(source_document, dict) else None
    if isinstance(sources, list):
        for source in sources:
            if not isinstance(source, dict):
                continue
            source_id = source.get("source_id")
            kind = source.get("kind")
            if _non_empty(source_id) and _non_empty(kind):
                source_kinds[_normalize_source(source_id)] = kind

    records: list[dict] = []
    violations: list[dict] = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            relative = _relative(path, repo_root)
            document = _load_json(path)
            if not isinstance(document, dict):
                violations.append(
                    _record_violation(relative, "retention_record_unreadable")
                )
                continue
            if document.get("record") != RETENTION_DECISION:
                continue
            record, record_violations = _parse_record(document, relative, repo_root)
            records.append(record)
            violations.extend(record_violations)

    counts = Counter(
        record["retention_decision_id"]
        for record in records
        if record["retention_decision_id"]
    )
    for record in records:
        decision_id = record["retention_decision_id"]
        if decision_id and counts[decision_id] > 1:
            record["valid"] = False
            violations.append(
                _record_violation(record["path"], "retention_decision_duplicate_id")
            )

    known_ids = {
        record["retention_decision_id"]
        for record in records
        if record["retention_decision_id"]
    }
    for record in records:
        for target in record["supersedes"]:
            if target == record["retention_decision_id"]:
                record["valid"] = False
                violations.append(
                    _record_violation(
                        record["path"],
                        "retention_supersedes_self",
                        reference=target,
                    )
                )
            elif target not in known_ids:
                record["valid"] = False
                violations.append(
                    _record_violation(
                        record["path"],
                        "retention_supersedes_unknown",
                        reference=target,
                    )
                )

    superseded_ids: set[str] = set()
    for record in records:
        if record["valid"]:
            superseded_ids.update(record["supersedes"])
    for record in records:
        if record["retention_decision_id"] in superseded_ids:
            record["superseded"] = True

    by_run: dict[tuple[str, str, str], list[tuple[dict, dict]]] = {}
    for record in records:
        if not record["valid"] or record["superseded"]:
            continue
        for run in record["runs"]:
            key = _decision_key(
                aliases, run["study_id"], run["source_id"], run["run_id"]
            )
            by_run.setdefault(key, []).append((record, run))

    decisions: dict[tuple[str, str, str], dict] = {}
    run_entries: list[dict] = []
    for key in sorted(by_run):
        entries = by_run[key]
        entries.sort(key=lambda pair: pair[0]["path"])
        if len(entries) > 1:
            run = entries[0][1]
            violations.append(
                {
                    "reason": "retention_decision_conflict",
                    "study_id": run["study_id"],
                    "source_id": run["source_id"],
                    "run_id": run["run_id"],
                    "records": sorted(record["path"] for record, _ in entries),
                }
            )
            continue
        record, run = entries[0]
        decisions[key] = record
        run_entries.append(
            {
                **run,
                "resolved_study_id": key[0],
                "retention_status": record["retention_status"],
                "retention_decision_id": record["retention_decision_id"],
                "retention_reason": record["reason"],
                "retention_decision_reference": record["decision_reference"],
                "publication_status": record["publication_status"],
                "publication_decision_reference": record[
                    "publication_decision_reference"
                ],
                "record_path": record["path"],
            }
        )

    run_entries.sort(
        key=lambda item: (item["study_id"], item["source_id"], item["run_id"])
    )
    return {
        "retention_version": RETENTION_VERSION,
        "repo_root": str(repo_root),
        "retention_dir": str(directory),
        "policy_registry": "config/storage-policies.json",
        "policy_available": policy_document is not None,
        "source_registry": "config/sources.json",
        "source_kinds": dict(sorted(source_kinds.items())),
        "statuses": list(RETENTION_STATUSES),
        "publication_statuses": list(PUBLICATION_STATUSES),
        "study_aliases": aliases,
        "policy_document": policy_document,
        "records": records,
        "decisions": decisions,
        "run_entries": run_entries,
        "violations": _sorted_violations(violations),
    }


def retention_run_claims(model: dict) -> list[dict]:
    """One claim per run named by an active retention decision."""

    return [
        {
            "study_id": entry["study_id"],
            "source_id": entry["source_id"],
            "run_id": entry["run_id"],
            "claimed_by": "retention_decision",
            "reference": entry["record_path"],
        }
        for entry in model["run_entries"]
    ]


# ---------------------------------------------------------------------------
# Resolution and the Git index fact
# ---------------------------------------------------------------------------


def tracked_repo_paths(repo_root=".") -> dict:
    """Repository-relative paths in the Git index (read-only)."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return {"available": False, "paths": []}
    if result.returncode != 0:
        return {"available": False, "paths": []}
    paths = [
        entry
        for entry in result.stdout.decode("utf-8", "replace").split("\0")
        if entry
    ]
    return {"available": True, "paths": sorted(set(paths))}


def run_prefixes(
    datasets_root, study_id: str, source_id: str, run_id: str, repo_root="."
) -> tuple[str, ...]:
    """Candidate repository paths for one run's raw directory.

    The source directory spelling differs from the registry id for Google
    Trends, so both spellings are tried.
    """

    if datasets_root is None:
        return ()
    try:
        relative = (
            Path(datasets_root).resolve().relative_to(Path(repo_root).resolve()).as_posix()
        )
    except (OSError, ValueError):
        return ()
    prefix = "" if relative == "." else f"{relative}/"
    spellings = {
        source_id,
        _normalize_source(source_id),
        source_id.replace("_", "-"),
    }
    return tuple(
        sorted(
            f"{prefix}{study_id}/data/raw/{spelling}/{run_id}/"
            for spelling in spellings
            if spelling
        )
    )


def assess_retention(
    model: dict,
    study_id: str,
    source_id: str,
    run_id: str,
    *,
    prefixes=(),
    tracked=None,
) -> dict:
    """Resolve the two-state status and the actual index state for one run.

    ``tracking_mismatch`` is ``None`` or the violation reason; callers decide
    whether the mismatch is a finding in their context.  The tracking state is
    ``unavailable`` when this is not a Git checkout or the run has no
    repository-relative path.
    """

    key = _decision_key(model["study_aliases"], study_id, source_id, run_id)
    policy = _policy_resolution(model, source_id)
    decision = model["decisions"].get(key)
    if decision is not None:
        base = {
            "retention_status": decision["retention_status"],
            "retention_source": "decision",
            "retention_decision_id": decision["retention_decision_id"],
            "retention_decision_reference": decision["decision_reference"],
            "retention_reason": decision["reason"],
            "retention_decision_path": decision["path"],
            "publication_status": decision["publication_status"],
            "publication_source": "decision",
            "publication_decision_reference": decision[
                "publication_decision_reference"
            ],
        }
    else:
        base = {
            "retention_status": policy["retention_status"],
            "retention_source": policy["retention_source"],
            "retention_decision_id": None,
            "retention_decision_reference": None,
            "retention_reason": None,
            "retention_decision_path": None,
            "publication_status": policy["publication_status"],
            "publication_source": policy["publication_source"],
            "publication_decision_reference": None,
        }
    base.update(
        {
            "retention_policy_id": policy["retention_policy_id"],
            "retention_policy_git_tracking": policy[
                "retention_policy_git_tracking"
            ],
            "retention_policy_status": policy["retention_status"],
            "retention_reference": (
                decision["decision_reference"]
                if decision is not None
                else policy["retention_reference"]
            ),
        }
    )

    tracking_state = "unavailable"
    tracked_count = None
    if tracked is not None and tracked.get("available") and prefixes:
        tracked_count = sum(
            1
            for path in tracked["paths"]
            if any(path.startswith(prefix) for prefix in prefixes)
        )
        tracking_state = "tracked" if tracked_count else "untracked"

    if tracking_state == "tracked" and base["retention_status"] == GIT_UNTRACKED:
        mismatch = "retention_git_untracked_but_tracked"
    elif tracking_state == "untracked" and base["retention_status"] == GIT_TRACKED:
        mismatch = "retention_git_tracked_but_untracked"
    else:
        mismatch = None

    return {
        "study_id": study_id,
        "source_id": source_id,
        "run_id": run_id,
        **base,
        "git_tracking_state": tracking_state,
        "tracked_file_count": tracked_count,
        "tracking_mismatch": mismatch,
    }


# ---------------------------------------------------------------------------
# Standalone report
# ---------------------------------------------------------------------------


def build_retention_report(
    repo_root=".", retention_dir=None, *, datasets_root=None, claims=None
) -> dict:
    """Validate decisions and report the two-state status for every claim.

    ``claims`` are ``{study_id, source_id, run_id}`` mappings (the catalog and
    declaration claims).  Raw payloads are never read; the Git index is used
    when available, so this runs on a clone without ``data/raw/``.
    """

    repo_root = Path(repo_root)
    model = load_retention(repo_root, retention_dir)
    tracked = (
        tracked_repo_paths(repo_root)
        if datasets_root is not None
        else {"available": False, "paths": []}
    )

    keys: set[tuple[str, str, str]] = {
        (entry["study_id"], entry["source_id"], entry["run_id"])
        for entry in model["run_entries"]
    }
    for claim in claims or []:
        if not isinstance(claim, dict):
            continue
        values = tuple(claim.get(name) for name in _RUN_KEYS)
        if all(_non_empty(value) for value in values):
            keys.add(values)

    runs: list[dict] = []
    violations = list(model["violations"])
    for study_id, source_id, run_id in sorted(keys):
        resolved_study = model["study_aliases"].get(study_id, study_id)
        prefixes = (
            run_prefixes(
                datasets_root, resolved_study, source_id, run_id, repo_root
            )
            if datasets_root is not None
            else ()
        )
        entry = assess_retention(
            model,
            study_id,
            source_id,
            run_id,
            prefixes=prefixes,
            tracked=tracked,
        )
        entry["resolved_study_id"] = resolved_study
        entry["violations"] = []
        if entry["tracking_mismatch"]:
            violation = {
                "study_id": study_id,
                "source_id": source_id,
                "run_id": run_id,
                "reason": entry["tracking_mismatch"],
                "path": entry["retention_decision_path"]
                or entry["retention_reference"],
            }
            entry["violations"].append(violation)
            violations.append(violation)
        runs.append(entry)

    violations = _sorted_violations(violations)
    return {
        "retention_version": RETENTION_VERSION,
        "repo_root": str(repo_root),
        "retention_dir": model["retention_dir"],
        "policy_registry": "config/storage-policies.json",
        "policy_available": model["policy_available"],
        "source_registry": "config/sources.json",
        "tracked_index_available": tracked["available"],
        "related_audits": list(RELATED_AUDITS),
        "statuses": list(RETENTION_STATUSES),
        "publication_statuses": list(PUBLICATION_STATUSES),
        "record_count": len(model["records"]),
        "active_record_count": sum(
            1
            for record in model["records"]
            if record["valid"] and not record["superseded"]
        ),
        "run_count": len(runs),
        "git_tracked_count": sum(
            1 for run in runs if run["retention_status"] == GIT_TRACKED
        ),
        "git_untracked_count": sum(
            1 for run in runs if run["retention_status"] == GIT_UNTRACKED
        ),
        "violation_count": len(violations),
        "failure_count": len(violations),
        "records": model["records"],
        "runs": runs,
        "violations": violations,
    }
