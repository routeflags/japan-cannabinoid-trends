"""Read-only reconciliation of run unknowns against the evidence registry.

Contract sources: ``docs/specs/validation-framework.md`` §18.3 (the missing
pass), ``validation.schemas.provenance.EVIDENCE_REGISTRY_SCHEMA`` (entry
shape), ``validation.provenance`` (the assessor that produces the unknowns).

What this pass does and does not do
-------------------------------------
It compares the ``unknown`` required paths of assessed runs with the entries
of ``metadata/provenance/evidence-registry.json`` and emits *candidates*:
``(unknown path, evidence entry)`` pairs a reviewer may cite to upgrade the
path.  It never promotes anything itself: the output vocabulary is
``candidate`` / ``no_covering_evidence`` only -- ``observed`` / ``inferred`` /
``ambiguous`` are never emitted here (G5 P2/P5: no guessing), and the inputs
(registry document, assessment) are never modified.

Coverage is deliberately narrow.  Only registry definitions whose field
mapping is known (:data:`REFERENCE_FIELD_COVERAGE`) can cover a required
path; audit reports, taxonomies, fixtures and external references are context,
not field evidence, and are reported as such.  A covering entry whose hash is
unrecorded is still a candidate, but carries the caveat that its integrity is
unverified -- pinning that hash is a witnessed owner action, not something
this pass back-fills (see ``docs/provenance/evidence-hash-policy.md``).
"""

from __future__ import annotations

from pathlib import Path

from validation.provenance import is_external_reference

__all__ = [
    "RECONCILIATION_VERSION",
    "REFERENCE_FIELD_COVERAGE",
    "COVERAGE_NOTE",
    "classify_hash_status",
    "covered_paths",
    "unknowns_from_assessment",
    "reconcile_evidence",
]

RECONCILIATION_VERSION = "1.0.0"

#: Local registry references with a known field mapping, and the run-required
#: dotted paths each one may evidence.  Anything not listed here (taxonomy,
#: artifact registry, audit reports, fixtures, collector logs, external URLs)
#: is context for a reviewer, never field coverage: without a declared mapping
#: a citation would be a guess (G5 P2/P5).
#:
#: - the source registry declares which sources exist, so it may evidence a
#:   run's ``source_id`` claim -- nothing else;
#: - the collector registry declares collector/adapter identities;
#: - the query registry declares query identities (``query_id`` only: the
#:   registry holds canonical text, not the submitted query string);
#: - absolute window documents declare the requested window bounds.
REFERENCE_FIELD_COVERAGE: dict[str, tuple[str, ...]] = {
    "config/sources.json": ("source_id",),
    "config/collectors.json": (
        "collector.collector_id",
        "collector.adapter_id",
    ),
    "metadata/queries/query-registry.json": ("query_provenance.query_id",),
}

#: Prefix rules for references that live under a directory (window documents).
WINDOW_REFERENCE_PREFIX = "metadata/windows/"
WINDOW_COVERED_PATHS = (
    "temporal_provenance.window_id",
    "temporal_provenance.requested_start",
    "temporal_provenance.requested_end_exclusive",
    "temporal_provenance.granularity",
    "temporal_provenance.timezone",
)

#: Prefix for machine-regenerated snapshots.  Their bytes change on every
#: regeneration (``make audit-snapshots``), so a pinned hash would go stale;
#: they are cited by reference + observation time, never by hash.
REGENERATED_REFERENCE_PREFIX = "docs/audits/"

COVERAGE_NOTE = (
    "Only registry definitions with a declared field mapping cover a "
    "required path; every other entry is reviewer context, never a "
    "promotion. No finding upgrades unknown to observed or inferred."
)

#: Hash-status vocabulary for evidence entries (policy truth lives in
#: ``docs/provenance/evidence-hash-policy.md``; this function classifies, the
#: registrar decides).
HASH_PINNED = "pinned"
HASH_REGENERATED_OUTPUT = "regenerated_output"
HASH_NEEDS_OBSERVATION = "needs_witnessed_observation"
HASH_EXTERNAL = "external_unverifiable"
HASH_UNRESOLVABLE = "reference_unresolvable"


def covered_paths(entry: dict) -> tuple[str, ...]:
    """Run-required dotted paths ``entry`` may evidence (possibly none)."""
    if not isinstance(entry, dict):
        return ()
    reference = entry.get("reference")
    if not isinstance(reference, str) or is_external_reference(reference):
        return ()
    if entry.get("evidence_type") != "registry_definition":
        return ()
    if reference in REFERENCE_FIELD_COVERAGE:
        return REFERENCE_FIELD_COVERAGE[reference]
    if reference.startswith(WINDOW_REFERENCE_PREFIX):
        return WINDOW_COVERED_PATHS
    return ()


def classify_hash_status(entry: dict, *, repo_root) -> str:
    """Classify what the hash policy says about one evidence entry.

    Read-only.  ``pinned`` means a hash is recorded (matching is verified
    separately by ``validation.provenance.check_evidence_registry``); every
    other status explains *why* no hash is recorded instead of inventing one.
    """
    if not isinstance(entry, dict):
        return HASH_UNRESOLVABLE
    reference = entry.get("reference")
    if not isinstance(reference, str) or not reference:
        return HASH_UNRESOLVABLE
    if is_external_reference(reference):
        return HASH_EXTERNAL
    if isinstance(entry.get("sha256"), str) and entry["sha256"]:
        return HASH_PINNED
    if reference.startswith(REGENERATED_REFERENCE_PREFIX):
        return HASH_REGENERATED_OUTPUT
    if (Path(repo_root) / reference).is_file():
        return HASH_NEEDS_OBSERVATION
    return HASH_UNRESOLVABLE


def unknowns_from_assessment(assessment: dict) -> list[dict]:
    """Extract per-run ``unknown`` required paths from an assessment report.

    Accepts the output of
    :func:`validation.provenance.build_provenance_assessment` (``runs`` with
    ``confidence.fields``).  Read-only.
    """
    unknowns: list[dict] = []
    runs = assessment.get("runs") if isinstance(assessment, dict) else None
    if not isinstance(runs, list):
        return unknowns
    for run in runs:
        if not isinstance(run, dict):
            continue
        confidence = run.get("confidence")
        fields = confidence.get("fields") if isinstance(confidence, dict) else None
        if not isinstance(fields, dict):
            continue
        missing = sorted(path for path, level in fields.items() if level == "unknown")
        if missing:
            unknowns.append(
                {
                    "run_id": run.get("run_id"),
                    "run_path": run.get("path"),
                    "unknown_paths": missing,
                }
            )
    return unknowns


def reconcile_evidence(evidence_registry: dict, unknowns: list[dict], *, repo_root) -> dict:
    """Match run unknowns against covering evidence entries (read-only).

    Returns ``{"reconciliation_version", "candidates", "uncovered",
    "summary"}``.  ``candidates`` carry the citation plus the hash caveat
    and the required owner action; ``uncovered`` records unknowns no entry
    covers.  Neither input is modified, and no finding promotes a path.
    """
    entries = evidence_registry.get("evidence") if isinstance(evidence_registry, dict) else None
    if not isinstance(entries, list):
        entries = []
    covering: list[tuple[dict, tuple[str, ...]]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        paths = covered_paths(entry)
        if not paths:
            continue
        reference = entry.get("reference")
        if not (Path(repo_root) / reference).is_file():
            continue  # a missing reference cannot evidence anything (owned
            # as EVIDENCE_REFERENCE_MISSING by check_evidence_registry)
        covering.append((entry, paths))

    candidates: list[dict] = []
    uncovered: list[dict] = []
    for unknown in unknowns:
        if not isinstance(unknown, dict):
            continue
        for path in unknown.get("unknown_paths") or []:
            cited = False
            for entry, paths in covering:
                if path not in paths:
                    continue
                cited = True
                hash_status = classify_hash_status(entry, repo_root=repo_root)
                candidates.append(
                    {
                        "run_id": unknown.get("run_id"),
                        "run_path": unknown.get("run_path"),
                        "unknown_path": path,
                        "evidence_id": entry.get("evidence_id"),
                        "evidence_type": entry.get("evidence_type"),
                        "reference": entry.get("reference"),
                        "hash_status": hash_status,
                        "verdict": "candidate",
                        "action": (
                            "Owner review: cite this entry to upgrade the path "
                            "in a witnessed evidence-registry update; do not "
                            "auto-apply."
                            + (
                                " Integrity unverified (hash unrecorded); pin "
                                "the hash at observation time first."
                                if hash_status != HASH_PINNED
                                else ""
                            )
                        ),
                    }
                )
            if not cited:
                uncovered.append(
                    {
                        "run_id": unknown.get("run_id"),
                        "run_path": unknown.get("run_path"),
                        "unknown_path": path,
                        "verdict": "no_covering_evidence",
                    }
                )
    candidates.sort(
        key=lambda item: (
            str(item["run_id"]),
            str(item["unknown_path"]),
            str(item["evidence_id"]),
        )
    )
    uncovered.sort(key=lambda item: (str(item["run_id"]), str(item["unknown_path"])))
    return {
        "reconciliation_version": RECONCILIATION_VERSION,
        "coverage_note": COVERAGE_NOTE,
        "candidate_count": len(candidates),
        "uncovered_count": len(uncovered),
        "candidates": candidates,
        "uncovered": uncovered,
        "summary": {
            "runs_with_unknowns": len(unknowns),
            "covering_entries": len(covering),
        },
    }
