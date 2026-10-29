"""Adoption backlog: every raw run directory, and why it is or is not declared.

Why this exists
---------------
``audit-new-runs`` and ``audit-provenance`` both discover runs by
``rglob("run_metadata.json")``.  That is the right unit for "is the declared
metadata valid"; it is the wrong unit for "has this raw run been declared at
all", because a run directory *without* ``run_metadata.json`` cannot match the
glob and so leaves no trace in either audit.  A payload obtained outside the
pipeline can then sit in ``data/raw/`` with no declaration, no failure and no
report line - the adoption backlog is invisible rather than merely pending.

This module enumerates the raw layer itself, one directory at a time:

    datasets/<study>/data/raw/<source>/<run-dir>/

Each run directory gets exactly one state, decided from its own contents only:

``run_metadata``
    ``run_metadata.json`` is a JSON object carrying a ``run_id``.  All three
    generations on disk look like this (current framework, legacy Google
    Trends, Apify-style), so the state says *a run is recorded*, not that the
    record satisfies the current contract - that is ``audit-new-runs``.
``vendor_envelope``
    No ``run_id``: the metadata is the collector's own run envelope (an
    ``id`` / ``status`` record).  The payload is on disk; the collection
    fields a declaration needs are not.
``metadata_unrecognized``
    A JSON object with neither a ``run_id`` nor a vendor envelope, so it
    identifies neither the run nor the request.
``metadata_unreadable``
    ``run_metadata.json`` exists and cannot be read as a JSON object.
``metadata_missing``
    No ``run_metadata.json``.

Two booleans carry what a ``run_metadata`` file leaves unrecorded, because
those are exactly the values a ``staging-declaration-v1`` document must supply
from outside the payload: ``request_recorded`` (a query / keyword / search term
is present) and ``window_recorded`` (an absolute window is present - a relative
spec such as ``today 12-m`` is not one).  ``run_id_matches_directory`` exposes
a metadata ``run_id`` that disagrees with the directory name.  ``run_id_form``
says whether the directory name matches the documented run-id form (AGENTS.md
"Run Identity"), so a directory that is not run-shaped is visible as a layout
divergence rather than as a file someone forgot.

Loose payload files that sit directly in a source directory (not inside any run
directory) are counted separately: they belong to no run at all, so no run-level
state can describe them.

What this audit deliberately does not do
---------------------------------------
It does not decide adoption, and it never invents a value to unblock one.  A
state says what is on disk; the reason string says, in neutral words, what a
declaration would have to supply from outside the payload.  ``cataloged`` only
reports whether the study's ``metadata/data-catalog.json`` already names a file
under the directory - membership, not approval.

Read-only: no file is written, no payload content is read (only the run
metadata file is parsed), and no cost field is copied into the report.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

__all__ = [
    "AUDIT_VERSION",
    "RUN_METADATA_NAME",
    "RUN_ID_FORM",
    "SKIPPED_DIRECTORY_NAMES",
    "STATE_REASONS",
    "build_adoption_backlog",
]

AUDIT_VERSION = "1.0.0"

RUN_METADATA_NAME = "run_metadata.json"

#: The documented run-id form (AGENTS.md "Run Identity"), used only to tell a
#: run directory from a directory that merely happens to sit under ``raw/``.
RUN_ID_FORM = re.compile(r"^[0-9]{8}T[0-9]{6}Z-")

#: Directory names never scanned: ``private`` is the AGENTS.md private-data
#: boundary (``audit-artifacts`` has the same exclusion and the same opt-in),
#: ``.quarantine`` holds rejected payloads that were never adopted.
SKIPPED_DIRECTORY_NAMES = frozenset({"private", ".quarantine"})

#: What a declaration would have to supply for each state.  Neutral wording:
#: the audit reports the gap and never proposes a substitute value.
STATE_REASONS = {
    "run_metadata": (
        "the directory holds run metadata; whether it satisfies the current "
        "contract is audit-new-runs' question, and what it leaves unrecorded "
        "is request_recorded / window_recorded"
    ),
    "vendor_envelope": (
        "the metadata is the collector's own run envelope: source, query, "
        "requested window and time basis must come from outside the payload"
    ),
    "metadata_unrecognized": (
        "the metadata is a JSON object with no run_id and no vendor envelope, "
        "so it identifies neither the run nor the request"
    ),
    "metadata_unreadable": (
        "the metadata cannot be read as a JSON object: the request is not "
        "recorded until it is replaced by a declaration"
    ),
    "metadata_missing": (
        "no run metadata: source, query, requested window and time basis "
        "must come from outside the payload"
    ),
}

#: Field names each recorded fact has taken across the generations of run
#: metadata on disk.  The audit is source-agnostic, so it looks for the
#: vocabulary the collectors already wrote rather than for one collector's
#: spelling: query -> queries / keyword -> keywords / search_term, and the
#: framework's own nesting (``query_provenance`` / ``temporal_provenance``) is
#: read as well as a flat ``window``.
_QUERY_FIELDS = ("query", "queries", "keyword", "keywords", "search_term")
_VENDOR_MARKERS = ("id", "startedAt", "started_at", "finishedAt", "status")


def _request_recorded(document: dict) -> bool:
    if isinstance(document.get("query_provenance"), dict):
        return True
    return any(field in document for field in _QUERY_FIELDS)


def _window_recorded(document: dict) -> bool:
    if isinstance(document.get("window"), dict):
        return True
    if document.get("start_date") and document.get("end_date"):
        return True
    temporal = document.get("temporal_provenance")
    if isinstance(temporal, dict):
        return bool(
            temporal.get("requested_start")
            and temporal.get("requested_end_exclusive")
        )
    return False


def _classify(run_dir: Path) -> dict:
    """Classify one run directory from its own contents only."""

    file_count = sum(1 for path in run_dir.iterdir() if path.is_file())
    record = {
        "run_dir": run_dir.name,
        "run_id": "",
        "state": "metadata_missing",
        "run_id_form": bool(RUN_ID_FORM.match(run_dir.name)),
        "run_id_matches_directory": False,
        "request_recorded": False,
        "window_recorded": False,
        "file_count": file_count,
        "empty": file_count == 0,
    }
    metadata = run_dir / RUN_METADATA_NAME
    if not metadata.is_file():
        return record
    try:
        document = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        record["state"] = "metadata_unreadable"
        return record
    if not isinstance(document, dict):
        record["state"] = "metadata_unreadable"
        return record

    run_id = document.get("run_id")
    if isinstance(run_id, str) and run_id:
        record["state"] = "run_metadata"
        record["run_id"] = run_id
        record["run_id_matches_directory"] = run_id == run_dir.name
        record["request_recorded"] = _request_recorded(document)
        record["window_recorded"] = _window_recorded(document)
        return record
    if any(marker in document for marker in _VENDOR_MARKERS):
        record["state"] = "vendor_envelope"
        return record
    record["state"] = "metadata_unrecognized"
    return record


def _catalog_paths(study_dir: Path) -> set[str] | None:
    """Catalogued paths for one study, or ``None`` when it has no catalog."""

    catalog = study_dir / "metadata" / "data-catalog.json"
    if not catalog.is_file():
        return None
    try:
        document = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    entries = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return set()
    paths: set[str] = set()
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            paths.add(entry["path"])
    return paths


def _catalogued(paths: set[str] | None, study_dir: Path, directory: Path) -> bool:
    if paths is None:
        return False
    try:
        relative = directory.relative_to(study_dir / "data").as_posix()
    except ValueError:
        return False
    prefixes = (relative, f"data/{relative}")
    return any(
        entry == prefix or entry.startswith(f"{prefix}/")
        for entry in paths
        for prefix in prefixes
    )


def build_adoption_backlog(datasets_root, *, include_private: bool = False) -> dict:
    """Enumerate every raw run directory and its adoption state.

    ``datasets_root`` is the ``datasets/`` directory.  An absent root is an
    empty backlog, not an error: the raw layer is machine-local, so a clone
    without it must still answer.
    """

    datasets = Path(datasets_root)
    runs: list[dict] = []
    sources: list[dict] = []
    loose_files: list[dict] = []

    if datasets.is_dir():
        for study_dir in sorted(p for p in datasets.iterdir() if p.is_dir()):
            raw_root = study_dir / "data" / "raw"
            if not raw_root.is_dir():
                continue
            catalog_paths = _catalog_paths(study_dir)
            for source_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
                if source_dir.name.startswith("."):
                    continue
                entries = sorted(source_dir.iterdir())
                run_dirs = [
                    path
                    for path in entries
                    if path.is_dir()
                    and (include_private or path.name not in SKIPPED_DIRECTORY_NAMES)
                ]
                source_loose = [
                    path
                    for path in entries
                    if path.is_file() and not path.name.startswith(".")
                ]
                sources.append(
                    {
                        "study_id": study_dir.name,
                        "source_id": source_dir.name,
                        "run_count": len(run_dirs),
                        "loose_file_count": len(source_loose),
                        "catalog_present": catalog_paths is not None,
                    }
                )
                for path in source_loose:
                    loose_files.append(
                        {
                            "study_id": study_dir.name,
                            "source_id": source_dir.name,
                            "name": path.name,
                        }
                    )
                for run_dir in run_dirs:
                    record = _classify(run_dir)
                    record.update(
                        {
                            "study_id": study_dir.name,
                            "source_id": source_dir.name,
                            "reason": STATE_REASONS[record["state"]],
                            "catalogued": _catalogued(
                                catalog_paths, study_dir, run_dir
                            ),
                        }
                    )
                    runs.append(record)

    states: dict[str, int] = {}
    for run in runs:
        states[run["state"]] = states.get(run["state"], 0) + 1

    violations = [
        run
        for run in runs
        if run["state"] == "metadata_unreadable" or run["empty"]
    ]

    return {
        "audit_version": AUDIT_VERSION,
        "datasets_root": str(datasets),
        "source_count": len(sources),
        "run_count": len(runs),
        "states": states,
        "run_metadata_count": states.get("run_metadata", 0),
        "no_run_metadata_count": states.get("vendor_envelope", 0)
        + states.get("metadata_unrecognized", 0)
        + states.get("metadata_missing", 0)
        + states.get("metadata_unreadable", 0),
        "request_unrecorded_count": sum(
            1 for run in runs if run["state"] == "run_metadata"
            and not run["request_recorded"]
        ),
        "window_unrecorded_count": sum(
            1 for run in runs if run["state"] == "run_metadata"
            and not run["window_recorded"]
        ),
        "run_id_mismatch_count": sum(
            1 for run in runs if run["run_id"] and not run["run_id_matches_directory"]
        ),
        "uncatalogued_count": sum(1 for run in runs if not run["catalogued"]),
        "sources_without_catalog_count": sum(
            1 for source in sources if not source["catalog_present"]
        ),
        "empty_run_count": sum(1 for run in runs if run["empty"]),
        "loose_file_count": len(loose_files),
        "loose_files": loose_files,
        "sources": sources,
        "runs": runs,
        "violations": [
            {
                "run_dir": run["run_dir"],
                "study_id": run["study_id"],
                "source_id": run["source_id"],
                "state": run["state"],
                "empty": run["empty"],
            }
            for run in violations
        ],
    }
