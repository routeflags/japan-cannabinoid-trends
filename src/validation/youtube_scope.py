"""Primary-scope inventory for the study's YouTube collection.

Why this exists
The study declares its YouTube query design (for this collection: liquid
product terms only, ``<compound> リキッド``).  That design is a study fact, not
a property of the generic YouTube skill, so it lives in
``datasets/<study>/metadata/query-design.json`` and this module reads it.  A
run whose query intent is outside the declared primary intent is not a failure
and must not be deleted: raw is immutable.  It is **retained provenance** and
has no effect on primary coverage.  The failure this audit prevents is the
quiet one: counting a bare compound-term run as if it completed liquid coverage
for that compound.

Inputs are committed facts (query design, query registry, declarations, catalog)
plus two checkout-local booleans per run (raw directory and run metadata
present).  Missing raw is reported, not raised: the raw layer is machine-local.

Coverage is reported at two levels and never collapsed into one number:

- **query**: a required primary query (a registry query with the design's
  primary intent) is covered when at least one adopted run carries its
  ``query_id``;
- **compound**: complete only when *all* of that compound's required primary
  queries are covered; some-but-not-all is ``partial``, none is ``missing``.

A compound can therefore be declared with more than one required primary query
(the registry is the authority), and one run never stands in for another query.

Output is deterministic (sorted ids, no timestamps) and carries no cost field.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "AUDIT_VERSION",
    "build_youtube_scope",
    "load_query_design",
]

AUDIT_VERSION = "1.0.0"
RUN_METADATA_NAME = "run_metadata.json"


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def load_query_design(path, study_id: str, source_id: str = "youtube") -> dict:
    """Return the declared design for one study/source.

    Raises ``ValueError`` when the document is absent or the design is
    ambiguous: a missing declaration must not silently fall back to a default
    query shape (the whole point is that the study declares the rule).
    """

    document = _load_json(Path(path))
    if not isinstance(document, dict):
        raise ValueError(f"query design is missing or unreadable: {path}")
    if document.get("study_id") != study_id:
        raise ValueError(
            f"query design study_id {document.get('study_id')!r} does not "
            f"match {study_id!r}"
        )
    designs = document.get("query_designs")
    if not isinstance(designs, list):
        raise ValueError(f"query design has no query_designs list: {path}")
    matches = [
        design
        for design in designs
        if isinstance(design, dict) and design.get("source_id") == source_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {source_id!r} design in {path}, found "
            f"{len(matches)}"
        )
    design = matches[0]
    if not isinstance(design.get("primary_intent_id"), str) or not design[
        "primary_intent_id"
    ]:
        raise ValueError(f"design has no primary_intent_id: {path}")
    return design


def _registry_queries(path) -> dict[str, dict]:
    document = _load_json(Path(path))
    queries = document.get("queries") if isinstance(document, dict) else None
    if not isinstance(queries, list):
        raise ValueError(f"query registry is missing or unreadable: {path}")
    by_id: dict[str, dict] = {}
    for entry in queries:
        if not isinstance(entry, dict):
            continue
        query_id = entry.get("query_id")
        if isinstance(query_id, str) and query_id:
            by_id[query_id] = entry
    return by_id


def _declaration_runs(declarations_dir: Path, study_id: str) -> list[dict]:
    runs: list[dict] = []
    if not declarations_dir.is_dir():
        return runs
    for path in sorted(declarations_dir.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        if document.get("declaration_version") != "staging-declaration-v1":
            continue
        for run in document.get("runs") or []:
            if not isinstance(run, dict):
                continue
            if run.get("study_id") != study_id or run.get("source_id") != "youtube":
                continue
            query = run.get("query") if isinstance(run.get("query"), dict) else {}
            execution = run.get("execution") if isinstance(run.get("execution"), dict) else {}
            window = run.get("window") if isinstance(run.get("window"), dict) else {}
            runs.append(
                {
                    "run_id": run.get("run_id"),
                    "query_id": query.get("query_id"),
                    "query_text": query.get("keyword"),
                    "returned_count": execution.get("returned_count"),
                    "window_start": window.get("start"),
                    "window_end_exclusive": window.get("end_exclusive"),
                    "adopted_by": ["declaration"],
                    "declaration_files": [path.name],
                }
            )
    return runs


def _catalog_runs(catalog_path: Path, study_id: str) -> list[dict]:
    document = _load_json(catalog_path)
    entries = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return []
    runs: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("study_id") != study_id or entry.get("source_id") != "youtube":
            continue
        run_id = entry.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            continue
        runs.append(
            {
                "run_id": run_id,
                "query_id": entry.get("query_id"),
                "query_text": None,
                "returned_count": entry.get("record_count"),
                "window_start": None,
                "window_end_exclusive": None,
                "adopted_by": ["catalog"],
                "declaration_files": [],
            }
        )
    return runs


def _merge_runs(declared: list[dict], cataloged: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for run in declared + cataloged:
        run_id = run.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            continue
        record = merged.setdefault(run_id, dict(run))
        for kind in run.get("adopted_by") or []:
            if kind not in record["adopted_by"]:
                record["adopted_by"].append(kind)
        for name in run.get("declaration_files") or []:
            if name not in record["declaration_files"]:
                record["declaration_files"].append(name)
        for field in ("query_id", "query_text", "returned_count", "window_start", "window_end_exclusive"):
            if record.get(field) in (None, "") and run.get(field) not in (None, ""):
                record[field] = run[field]
    for record in merged.values():
        record["adopted_by"].sort()
        record["declaration_files"].sort()
    return [merged[key] for key in sorted(merged)]


def _raw_present(datasets_root: Path, study_id: str, run_id: str) -> bool:
    return (
        datasets_root / study_id / "data" / "raw" / "youtube" / run_id / RUN_METADATA_NAME
    ).is_file()


def build_youtube_scope(
    study_id: str,
    *,
    query_design_path,
    query_registry_path,
    declarations_dir,
    catalog_path,
    datasets_root,
    require_complete: bool = False,
) -> dict:
    """Split adopted YouTube runs into primary liquid coverage and retained runs."""

    design = load_query_design(query_design_path, study_id)
    registry = _registry_queries(query_registry_path)
    runs = _merge_runs(
        _declaration_runs(Path(declarations_dir), study_id),
        _catalog_runs(Path(catalog_path), study_id),
    )
    datasets = Path(datasets_root)
    primary_intent = design["primary_intent_id"]
    out_of_primary = set(design.get("out_of_primary_intent_ids") or [])

    violations: list[dict] = []
    for run in runs:
        query_id = run.get("query_id")
        entry = registry.get(query_id) if isinstance(query_id, str) else None
        if entry is None:
            run["intent_id"] = None
            run["compound_id"] = None
            run["query_registered"] = False
            violations.append(
                {"run_id": run["run_id"], "reason": "unregistered_query_id", "query_id": query_id}
            )
        else:
            run["intent_id"] = entry.get("intent_id")
            run["compound_id"] = entry.get("compound_id")
            run["query_registered"] = True
            if run.get("query_text") in (None, ""):
                run["query_text"] = entry.get("canonical_text")
            if run["intent_id"] != primary_intent and run["intent_id"] not in out_of_primary:
                violations.append(
                    {
                        "run_id": run["run_id"],
                        "reason": "intent_outside_declared_design",
                        "intent_id": run["intent_id"],
                    }
                )
        run["raw_present"] = _raw_present(datasets, study_id, run["run_id"])

    primary_runs = sorted(
        (run for run in runs if run.get("intent_id") == primary_intent),
        key=lambda item: item["run_id"],
    )
    retained_runs = sorted(
        (run for run in runs if run.get("intent_id") != primary_intent),
        key=lambda item: item["run_id"],
    )
    for run in retained_runs:
        run["primary_coverage"] = "none"
        run["retained_reason"] = (
            "query intent is outside the declared primary design; kept as "
            "provenance and excluded from primary coverage"
        )

    primary_queries = {
        query_id: entry
        for query_id, entry in registry.items()
        if entry.get("intent_id") == primary_intent
    }
    coverage: list[dict] = []
    for query_id in sorted(primary_queries):
        entry = primary_queries[query_id]
        matching = [run for run in primary_runs if run.get("query_id") == query_id]
        coverage.append(
            {
                "compound_id": entry.get("compound_id"),
                "query_id": query_id,
                "canonical_text": entry.get("canonical_text"),
                "covered": bool(matching),
                "run_count": len(matching),
                "run_ids": [run["run_id"] for run in matching],
                "raw_present_run_count": sum(1 for run in matching if run["raw_present"]),
            }
        )

    # Compound level: a compound is complete only when every one of its required
    # primary queries is covered.  Some-but-not-all is ``partial``, none is
    # ``missing``.  A run covers only its own query_id, so the second query of a
    # two-query compound never stands in for the first.
    required_by_compound: dict[str, list[dict]] = {}
    for item in coverage:
        required_by_compound.setdefault(item["compound_id"], []).append(item)
    compound_coverage: list[dict] = []
    for compound_id in sorted(required_by_compound, key=lambda value: str(value)):
        queries = sorted(required_by_compound[compound_id], key=lambda item: item["query_id"])
        adopted = [item for item in queries if item["covered"]]
        pending = [item for item in queries if not item["covered"]]
        if not pending:
            state = "complete"
        elif adopted:
            state = "partial"
        else:
            state = "missing"
        compound_coverage.append(
            {
                "compound_id": compound_id,
                "state": state,
                "required_query_count": len(queries),
                "covered_query_count": len(adopted),
                "required_query_ids": [item["query_id"] for item in queries],
                "covered_query_ids": [item["query_id"] for item in adopted],
                "missing_query_ids": [item["query_id"] for item in pending],
                "run_ids": [run_id for item in adopted for run_id in item["run_ids"]],
            }
        )

    covered_compounds = [
        item["compound_id"] for item in compound_coverage if item["state"] == "complete"
    ]
    partial_compounds = [
        item["compound_id"] for item in compound_coverage if item["state"] == "partial"
    ]
    missing_compounds = [
        item["compound_id"] for item in compound_coverage if item["state"] == "missing"
    ]
    if require_complete:
        violations.extend(
            {"reason": "primary_coverage_missing", "compound_id": compound_id}
            for compound_id in missing_compounds
        )
        violations.extend(
            {
                "reason": "primary_coverage_partial",
                "compound_id": item["compound_id"],
                "missing_query_ids": item["missing_query_ids"],
            }
            for item in compound_coverage
            if item["state"] == "partial"
        )

    return {
        "audit_version": AUDIT_VERSION,
        "study_id": study_id,
        "design_id": design.get("design_id"),
        "primary_intent_id": primary_intent,
        "query_pattern": design.get("query_pattern"),
        "one_query_per_run": design.get("one_query_per_run"),
        "primary_run_count": len(primary_runs),
        "primary_compound_count": len(covered_compounds),
        "retained_out_of_scope_run_count": len(retained_runs),
        "total_adopted_run_count": len(runs),
        "primary_query_count": len(coverage),
        "primary_query_covered_count": sum(1 for item in coverage if item["covered"]),
        "partial_primary_compound_count": len(partial_compounds),
        "missing_primary_compound_count": len(missing_compounds),
        "covered_compounds": covered_compounds,
        "partial_compounds": partial_compounds,
        "missing_compounds": missing_compounds,
        "primary_runs": primary_runs,
        "retained_out_of_scope_runs": retained_runs,
        "coverage": coverage,
        "compound_coverage": compound_coverage,
        "violation_count": len(violations),
        "violations": violations,
        "require_complete": bool(require_complete),
        "failure_count": len(violations),
    }
