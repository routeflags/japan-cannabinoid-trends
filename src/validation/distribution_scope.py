"""Distribution-scope report for the platform-trends release slice.

Why this exists
The release dataset (``cannabinoid-platform-trends``) deliberately uses the
COL-033 YouTube declaration only: six adopted liquid runs from the
``youtube-consistency`` study.  Its ``platform_coverage.csv`` therefore prints
``not_collected`` for compounds with no run in that slice.  That word is true
about the slice and false about the raw study: the raw study also holds HHC
liquid and HHC compound-term runs, and both are adopted there.  A reader who
sees ``HHC / youtube / not_collected`` without the scope qualifier can
reasonably conclude HHC was never collected.

This module makes the distinction explicit and machine-readable.  It compares
the committed distribution outputs with the committed declarations and reports:

- the exact YouTube scope of the distribution (declaration, study ids, runs);
- per compound, the distribution status next to the raw-study runs that the
  release slice excludes (``scope_gap``);
- the run-id mapping between the two study identities for the same payload
  (``environment.previous_study_run_id``);
- request-parameter drift between ``source_run_index.csv`` and the declaration
  (the committed slice carries a legacy ``maxResults=999999`` placeholder that
  the declaration does not record).

Report-only by default: changing the distribution is a release decision, not a
side effect of an audit.  ``--strict`` turns the drift findings into a non-zero
exit for a caller that wants the gate.  Read-only; deterministic; no cost
fields.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

__all__ = ["AUDIT_VERSION", "build_distribution_scope"]

AUDIT_VERSION = "1.0.0"

DISTRIBUTION_STUDY = "cannabinoid-platform-trends"
DISTRIBUTION_YOUTUBE_DECLARATION = (
    "metadata/provenance/declarations/20261015-youtube-csv-adoption.json"
)
RAW_STUDY = "cannabinoid-raw-collection"
RAW_DECLARATIONS_DIR = "metadata/provenance/declarations"
QUERY_REGISTRY = "metadata/queries/query-registry.json"
PROCESSED_DIR = "datasets/cannabinoid-platform-trends/data/processed"

_MAX_RESULTS = re.compile(r"maxResults=(\d+)")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _queries(repo_root: Path) -> dict[str, dict]:
    document = _load_json(repo_root / QUERY_REGISTRY)
    return {
        entry["query_id"]: entry
        for entry in document.get("queries", [])
        if isinstance(entry, dict) and isinstance(entry.get("query_id"), str)
    }


def _declaration_runs(path: Path) -> list[dict]:
    document = _load_json(path)
    runs = document.get("runs") if isinstance(document, dict) else None
    return [run for run in runs or [] if isinstance(run, dict)]


def _raw_study_runs(repo_root: Path) -> list[dict]:
    """One record per run id.

    Corrected provenance copies share the original run id, so the same run can
    appear in two declaration files.  Counting both would inflate the raw-study
    run count and the per-compound list; the id is the identity.
    """

    merged: dict[str, dict] = {}
    directory = repo_root / RAW_DECLARATIONS_DIR
    if not directory.is_dir():
        return []
    for path in sorted(directory.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        if document.get("declaration_version") != "staging-declaration-v1":
            continue
        for run in document.get("runs") or []:
            if not isinstance(run, dict) or run.get("study_id") != RAW_STUDY:
                continue
            if run.get("source_id") != "youtube":
                continue
            run_id = run.get("run_id")
            if not isinstance(run_id, str) or not run_id:
                continue
            query = run.get("query") if isinstance(run.get("query"), dict) else {}
            environment = run.get("environment") if isinstance(run.get("environment"), dict) else {}
            record = merged.setdefault(
                run_id,
                {
                    "run_id": run_id,
                    "query_id": query.get("query_id"),
                    "query_text": query.get("keyword"),
                    "declaration": path.name,
                    "declarations": [],
                    "previous_study_run_id": environment.get("previous_study_run_id"),
                    "payload_sha256": environment.get("payload_sha256"),
                },
            )
            if path.name not in record["declarations"]:
                record["declarations"].append(path.name)
            if record["query_id"] in (None, "") and query.get("query_id"):
                record["query_id"] = query.get("query_id")
            if record["query_text"] in (None, "") and query.get("keyword"):
                record["query_text"] = query.get("keyword")
            for field in ("previous_study_run_id", "payload_sha256"):
                if record[field] in (None, "") and environment.get(field) not in (None, ""):
                    record[field] = environment.get(field)
    for record in merged.values():
        record["declarations"].sort()
    return [merged[key] for key in sorted(merged)]


def _distribution_runs(repo_root: Path, queries: dict[str, dict]) -> list[dict]:
    runs: list[dict] = []
    path = repo_root / DISTRIBUTION_YOUTUBE_DECLARATION
    for run in _declaration_runs(path):
        query = run.get("query") if isinstance(run.get("query"), dict) else {}
        query_id = query.get("query_id")
        entry = queries.get(query_id, {})
        execution = run.get("execution") if isinstance(run.get("execution"), dict) else {}
        runs.append(
            {
                "run_id": run.get("run_id"),
                "query_id": query_id,
                "query_text": query.get("keyword"),
                "intent_id": entry.get("intent_id"),
                "compound_id": entry.get("compound_id"),
                "returned_count": execution.get("returned_count"),
                "study_id": run.get("study_id"),
                "declaration": DISTRIBUTION_YOUTUBE_DECLARATION,
            }
        )
    return runs


def build_distribution_scope(repo_root=".") -> dict:
    """Report the distribution's YouTube scope and the raw-study runs it excludes."""

    root = Path(repo_root)
    queries = _queries(root)
    distribution_runs = _distribution_runs(root, queries)
    raw_runs = _raw_study_runs(root)
    processed = root / PROCESSED_DIR

    coverage_rows = _load_csv(processed / "platform_coverage.csv")
    run_index_rows = _load_csv(processed / "source_run_index.csv")
    manifest = _load_json(processed / "manifest.json")

    distribution_by_compound: dict[str, list[dict]] = {}
    for run in distribution_runs:
        distribution_by_compound.setdefault(run["compound_id"], []).append(run)
    raw_by_compound: dict[str, list[dict]] = {}
    for run in raw_runs:
        entry = queries.get(run.get("query_id"), {})
        run["intent_id"] = entry.get("intent_id")
        run["compound_id"] = entry.get("compound_id")
        raw_by_compound.setdefault(run["compound_id"], []).append(run)

    by_compound: list[dict] = []
    for row in coverage_rows:
        if row.get("platform") != "youtube":
            continue
        compound_id = row.get("compound_id")
        included = distribution_by_compound.get(compound_id, [])
        raw = raw_by_compound.get(compound_id, [])
        by_compound.append(
            {
                "compound": row.get("compound"),
                "compound_id": compound_id,
                "distribution_status": row.get("status"),
                "distribution_run_count": int(row.get("run_count") or 0),
                "distribution_run_ids": sorted(run["run_id"] for run in included),
                "raw_study_run_count": len(raw),
                "raw_study_run_ids": sorted(run["run_id"] for run in raw),
                "raw_study_intents": sorted(
                    {run["intent_id"] for run in raw if run.get("intent_id")}
                ),
                "scope_gap": row.get("status") == "not_collected" and bool(raw),
                "release_slice_excluded": bool(raw)
                and row.get("status") == "not_collected",
            }
        )
    by_compound.sort(key=lambda item: (item["compound"] or "", item["compound_id"] or ""))

    distribution_ids = {run["run_id"] for run in distribution_runs}
    declared_by_run = {
        run.get("run_id"): run
        for run in _declaration_runs(root / DISTRIBUTION_YOUTUBE_DECLARATION)
    }
    payload_by_distribution_run = {
        run_id: (run.get("environment") or {}).get("payload_sha256")
        for run_id, run in declared_by_run.items()
        if isinstance(run.get("environment"), dict)
    }
    mapping: list[dict] = []
    for run in distribution_runs:
        linked = next(
            (
                raw
                for raw in raw_runs
                if raw.get("previous_study_run_id") == run["run_id"]
            ),
            None,
        )
        basis = "environment.previous_study_run_id" if linked else None
        if linked is None:
            payload = payload_by_distribution_run.get(run["run_id"])
            linked = next(
                (
                    raw
                    for raw in raw_runs
                    if payload and raw.get("payload_sha256") == payload
                ),
                None,
            )
            basis = "environment.payload_sha256" if linked else None
        mapping.append(
            {
                "distribution_run_id": run["run_id"],
                "raw_study_run_id": linked.get("run_id") if linked else None,
                "mapping_basis": basis,
                "mapped": bool(linked),
            }
        )
    mapping.sort(key=lambda item: item["distribution_run_id"] or "")
    findings: list[dict] = []
    for row in run_index_rows:
        if row.get("platform") != "youtube":
            continue
        run_id = row.get("run_id")
        declared = declared_by_run.get(run_id) or {}
        request = (
            declared.get("collection_request")
            if isinstance(declared.get("collection_request"), dict)
            else {}
        )
        documented_match = _MAX_RESULTS.search(row.get("request_parameters") or "")
        documented = int(documented_match.group(1)) if documented_match else None
        declared_value = None
        for key in ("max_results", "maxResults", "max_videos"):
            if isinstance(request.get(key), int):
                declared_value = request[key]
                break
        if documented is not None and declared_value is None:
            findings.append(
                {
                    "kind": "unsupported_max_results",
                    "run_id": run_id,
                    "documented_value": documented,
                    "detail": (
                        "source_run_index.csv records a maxResults value that "
                        "the declaration's collection_request does not contain"
                    ),
                }
            )
        elif documented is not None and documented != declared_value:
            findings.append(
                {
                    "kind": "max_results_mismatch",
                    "run_id": run_id,
                    "documented_value": documented,
                    "declared_value": declared_value,
                }
            )

    unmapped = [entry for entry in mapping if not entry["mapped"]]
    for entry in unmapped:
        findings.append(
            {
                "kind": "distribution_run_without_raw_study_link",
                "run_id": entry["distribution_run_id"],
            }
        )
    findings.sort(key=lambda item: (item["kind"], item.get("run_id") or ""))

    return {
        "audit_version": AUDIT_VERSION,
        "distribution_study_id": DISTRIBUTION_STUDY,
        "distribution_youtube_declaration": DISTRIBUTION_YOUTUBE_DECLARATION,
        "distribution_youtube_study_ids": sorted(
            {run["study_id"] for run in distribution_runs if run.get("study_id")}
        ),
        "distribution_youtube_run_count": len(distribution_runs),
        "distribution_youtube_compounds": sorted(
            {run["compound_id"] for run in distribution_runs if run.get("compound_id")}
        ),
        "distribution_query_intents": sorted(
            {run["intent_id"] for run in distribution_runs if run.get("intent_id")}
        ),
        "distribution_run_ids": sorted(distribution_ids),
        "raw_study_id": RAW_STUDY,
        "raw_study_youtube_run_count": len(raw_runs),
        "scope_gap_compounds": [
            entry["compound"] for entry in by_compound if entry["scope_gap"]
        ],
        "run_id_mapping": mapping,
        "by_compound": by_compound,
        "manifest_youtube_scope": {
            "sources": manifest.get("sources"),
            "excluded_sources": manifest.get("excluded_sources"),
        },
        "finding_count": len(findings),
        "findings": findings,
        "failure_count": len(findings),
    }
