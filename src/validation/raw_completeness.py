"""Committed claims about raw runs versus the raw layer on this checkout.

Why this exists
The catalog (``datasets/<study>/metadata/data-catalog.json``) and every
committed ``staging-declaration-v1`` document name runs whose payloads live in
``data/raw/``.  That directory is machine-local: ``.gitignore`` excludes
``**/data/raw/*`` except Google Trends, so a clone or a partial worktree can
carry the claims without the payloads.  Nothing reported that gap, and the two
failure modes look identical from the committed files alone:

- the run was never adopted (a real backlog item);
- the run was adopted somewhere else and this checkout cannot substantiate it
  (a portability fact, not a data error).

This audit reports the second state explicitly.  It is read-only and
checkout-local by design: a missing directory says "this checkout cannot show
the raw run", never "the run does not exist".

What is checked
---------------
1. every catalog run id and every declared run id resolves to
   ``datasets/<study>/data/raw/<source>/<run-id>/`` with a readable
   ``run_metadata.json`` (or is reported as missing);
2. every declaration-correction record under
   ``metadata/provenance/corrections/`` pins the declaration bytes it claims to
   correct (SHA-256) and names runs that the referenced declaration contains.
   A correction is how post-staging fixes are recorded without rewriting the
   handover document (whose SHA-256 is stored in the raw run metadata);
3. a declaration whose study has no catalog is reported, not failed: some
   studies keep declarations only (for example ``youtube-consistency`` in a
   checkout that does not carry its catalog).

Exit status is the CLI's decision: a missing raw run in the current checkout is
a finding (exit 1); an absent ``data/raw/`` root is not an exception.

Deterministic output: no timestamps, all collections sorted, no cost fields.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

__all__ = [
    "AUDIT_VERSION",
    "DECLARATION_VERSION",
    "CORRECTION_RECORD",
    "build_raw_completeness",
    "catalog_run_claims",
    "declaration_run_claims",
    "present_raw_runs",
]

AUDIT_VERSION = "1.0.0"
DECLARATION_VERSION = "staging-declaration-v1"
CORRECTION_RECORD = "declaration_correction"
RUN_METADATA_NAME = "run_metadata.json"


def _normalize_source(value: str) -> str:
    """Directory spelling differs from the registry id for Google Trends."""

    return value.replace("-", "_").lower()


def _study_aliases(repo_root) -> dict[str, str]:
    """Recorded study id -> the study directory name that holds its raw."""

    document = _load_json(Path(repo_root) / "metadata" / "studies" / "study-registry.json")
    aliases: dict[str, str] = {}
    studies = document.get("studies") if isinstance(document, dict) else None
    if not isinstance(studies, list):
        return aliases
    for study in studies:
        if not isinstance(study, dict):
            continue
        current = study.get("study_id")
        if not isinstance(current, str) or not current:
            continue
        aliases[current] = current
        for previous in study.get("previous_study_ids") or []:
            if isinstance(previous, str) and previous:
                aliases[previous] = current
    return aliases


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_paths(datasets: Path) -> list[Path]:
    if not datasets.is_dir():
        return []
    return sorted(datasets.glob("*/metadata/data-catalog.json"))


def catalog_run_claims(datasets_root) -> list[dict]:
    """One claim per ``(study_id, source_id, run_id)`` named by a catalog."""

    datasets = Path(datasets_root)
    claims: list[dict] = []
    for path in _catalog_paths(datasets):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        entries = document.get("entries")
        if not isinstance(entries, list):
            continue
        study_from_path = path.parent.parent.name
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            run_id = entry.get("run_id")
            source_id = entry.get("source_id")
            if not isinstance(run_id, str) or not run_id:
                continue
            if not isinstance(source_id, str) or not source_id:
                continue
            study_id = entry.get("study_id")
            if not isinstance(study_id, str) or not study_id:
                study_id = study_from_path
            claims.append(
                {
                    "study_id": study_id,
                    "source_id": source_id,
                    "run_id": run_id,
                    "claimed_by": "catalog",
                    "reference": path.relative_to(datasets.parent).as_posix()
                    if datasets.parent in path.parents
                    else path.as_posix(),
                }
            )
    return _merge_claims(claims)


def declaration_run_claims(declarations_dir) -> list[dict]:
    """One claim per run declared in a ``staging-declaration-v1`` document."""

    directory = Path(declarations_dir)
    claims: list[dict] = []
    if not directory.is_dir():
        return claims
    for path in sorted(directory.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            continue
        if document.get("declaration_version") != DECLARATION_VERSION:
            continue
        runs = document.get("runs")
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, dict):
                continue
            run_id = run.get("run_id")
            study_id = run.get("study_id")
            source_id = run.get("source_id")
            if not all(isinstance(value, str) and value for value in (run_id, study_id, source_id)):
                continue
            claims.append(
                {
                    "study_id": study_id,
                    "source_id": source_id,
                    "run_id": run_id,
                    "claimed_by": "declaration",
                    "reference": path.name,
                }
            )
    return _merge_claims(claims)


def _merge_claims(claims: list[dict]) -> list[dict]:
    """Merge duplicate claims, keeping every reference that names the run."""

    merged: dict[tuple[str, str, str], dict] = {}
    for claim in claims:
        key = (claim["study_id"], claim["source_id"], claim["run_id"])
        record = merged.setdefault(
            key,
            {
                "study_id": claim["study_id"],
                "source_id": claim["source_id"],
                "run_id": claim["run_id"],
                "claimed_by": [],
                "references": [],
            },
        )
        kinds = claim.get("claimed_by")
        kinds = kinds if isinstance(kinds, list) else [kinds]
        for kind in kinds:
            if kind and kind not in record["claimed_by"]:
                record["claimed_by"].append(kind)
        references = claim.get("references")
        if not isinstance(references, list):
            references = [
                {"kind": claim.get("claimed_by"), "path": claim.get("reference")}
            ]
        for reference in references:
            if reference not in record["references"]:
                record["references"].append(reference)
    for record in merged.values():
        record["claimed_by"].sort()
        record["references"].sort(key=lambda item: (item["kind"], item["path"]))
    return [merged[key] for key in sorted(merged)]


def present_raw_runs(datasets_root) -> dict[str, list[dict]]:
    """Map run id -> every raw location that carries that id on this checkout.

    A directory is recorded even when ``run_metadata.json`` is missing: the
    payload may exist while its metadata does not, and the claim check has to
    distinguish the two.
    """

    datasets = Path(datasets_root)
    present: dict[str, list[dict]] = {}
    if not datasets.is_dir():
        return present
    for study_dir in sorted(p for p in datasets.iterdir() if p.is_dir()):
        raw_root = study_dir / "data" / "raw"
        if not raw_root.is_dir():
            continue
        for source_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
            for run_dir in sorted(p for p in source_dir.iterdir() if p.is_dir()):
                if run_dir.name.startswith("."):
                    continue
                metadata = run_dir / RUN_METADATA_NAME
                present.setdefault(run_dir.name, []).append(
                    {
                        "study_id": study_dir.name,
                        "source_id": source_dir.name,
                        "directory_present": True,
                        "run_metadata_present": metadata.is_file(),
                    }
                )
    for locations in present.values():
        locations.sort(key=lambda item: (item["study_id"], item["source_id"]))
    return present


def _correction_violations(repo_root: Path, corrections_dir: Path) -> tuple[list[dict], list[dict]]:
    """Check correction records against the declaration bytes they pin."""

    records: list[dict] = []
    violations: list[dict] = []
    if not corrections_dir.is_dir():
        return records, violations
    for path in sorted(corrections_dir.glob("*.json")):
        document = _load_json(path)
        if not isinstance(document, dict):
            violations.append(
                {"path": path.name, "reason": "correction_record_unreadable"}
            )
            continue
        if document.get("record") != CORRECTION_RECORD:
            continue
        original = document.get("original_declarations")
        corrected = document.get("corrected_declarations")
        original_runs: set[str] = set()
        checked_paths: list[str] = []
        for section_name, section in (
            ("original_declarations", original),
            ("corrected_declarations", corrected),
        ):
            if section is None:
                continue
            if not isinstance(section, list):
                violations.append(
                    {"path": path.name, "reason": f"{section_name}_not_a_list"}
                )
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue
                relative = item.get("path")
                pinned = item.get("sha256")
                if not isinstance(relative, str) or not relative:
                    violations.append(
                        {"path": path.name, "reason": f"{section_name}_path_missing"}
                    )
                    continue
                target = repo_root / relative
                checked_paths.append(relative)
                if not target.is_file():
                    violations.append(
                        {
                            "path": path.name,
                            "reason": f"{section_name}_file_absent",
                            "reference": relative,
                        }
                    )
                    continue
                if not isinstance(pinned, str) or _sha256(target) != pinned:
                    violations.append(
                        {
                            "path": path.name,
                            "reason": f"{section_name}_sha256_mismatch",
                            "reference": relative,
                        }
                    )
                    continue
                if section_name == "original_declarations":
                    declaration = _load_json(target)
                    runs = declaration.get("runs") if isinstance(declaration, dict) else None
                    if isinstance(runs, list):
                        original_runs.update(
                            run.get("run_id")
                            for run in runs
                            if isinstance(run, dict) and isinstance(run.get("run_id"), str)
                        )
        corrections = document.get("corrections")
        if isinstance(corrections, list):
            for entry in corrections:
                if not isinstance(entry, dict):
                    continue
                run_id = entry.get("run_id")
                if isinstance(run_id, str) and run_id and run_id not in original_runs:
                    violations.append(
                        {
                            "path": path.name,
                            "reason": "corrected_run_id_not_in_original_declaration",
                            "run_id": run_id,
                        }
                    )
        records.append(
            {
                "path": path.name,
                "correction_id": document.get("correction_id"),
                "status": document.get("status"),
                "checked_declaration_paths": sorted(set(checked_paths)),
            }
        )
    return records, violations


def build_raw_completeness(
    datasets_root,
    declarations_dir,
    corrections_dir=None,
    repo_root=".",
) -> dict:
    """Report which committed raw-run claims this checkout can substantiate."""

    datasets = Path(datasets_root)
    aliases = _study_aliases(repo_root)
    claims = catalog_run_claims(datasets) + declaration_run_claims(declarations_dir)
    merged = _merge_claims(claims)
    present = present_raw_runs(datasets)

    runs: list[dict] = []
    for claim in merged:
        resolved_study = aliases.get(claim["study_id"], claim["study_id"])
        locations = present.get(claim["run_id"], [])
        matched = [
            location
            for location in locations
            if location["study_id"] == resolved_study
            and _normalize_source(location["source_id"])
            == _normalize_source(claim["source_id"])
        ]
        if not matched:
            state = "missing_directory"
        elif any(location["run_metadata_present"] for location in matched):
            state = "present"
        else:
            state = "missing_run_metadata"
        runs.append(
            {
                **claim,
                "resolved_study_id": resolved_study,
                "state": state,
                "locations": matched,
            }
        )

    missing = [run for run in runs if run["state"] != "present"]
    catalog_studies = {
        aliases.get(claim["study_id"], claim["study_id"])
        for claim in catalog_run_claims(datasets)
    }
    declaration_studies = {
        aliases.get(claim["study_id"], claim["study_id"])
        for claim in declaration_run_claims(declarations_dir)
    }
    corrections, correction_violations = (
        _correction_violations(Path(repo_root), Path(corrections_dir))
        if corrections_dir
        else ([], [])
    )

    return {
        "audit_version": AUDIT_VERSION,
        "datasets_root": str(datasets),
        "declarations_dir": str(declarations_dir),
        "claim_count": len(runs),
        "catalog_run_count": sum(1 for claim in catalog_run_claims(datasets)),
        "declaration_run_count": sum(
            1 for claim in declaration_run_claims(declarations_dir)
        ),
        "present_count": sum(1 for run in runs if run["state"] == "present"),
        "missing_count": len(missing),
        "missing_directory_count": sum(
            1 for run in missing if run["state"] == "missing_directory"
        ),
        "missing_run_metadata_count": sum(
            1 for run in missing if run["state"] == "missing_run_metadata"
        ),
        "declaration_studies_without_catalog": sorted(
            declaration_studies - catalog_studies
        ),
        "catalog_studies_without_declaration": sorted(
            catalog_studies - declaration_studies
        ),
        "corrections": corrections,
        "correction_violation_count": len(correction_violations),
        "correction_violations": correction_violations,
        "failure_count": len(missing) + len(correction_violations),
        "runs": runs,
        "missing": missing,
    }
