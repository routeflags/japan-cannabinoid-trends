"""G5 provenance assessment: completeness, confidence, integrity, readiness.

Contract sources
----------------
- G5 instruction §9 (Provenance Completeness / Evidence Confidence /
  Integrity / Reproducibility Readiness) and §10 (legacy audit evidence
  levels): ``docs/plans/20261013e.md``.
- G5 §4.1 (required-9 mapping) and §8.2 P01 (run_id uniqueness) / P17
  (registry version traceability).
- G5 §11 (evidence registry reference / hash checks).

Canonical split (G5 duplicate整理 T1)
--------------------------------------
- run_metadata *construction* lives in ``collection.core.provenance``
  (``build_run_metadata``); the required-9 field mapping table there is
  canonical and is mirrored (not forked) in ``ESSENTIAL_PROVENANCE_PATHS``
  below.
- structural shape lives in ``validation.schemas.collection_run``
  (``collection-run-v1``) and ``validation.schemas.provenance``
  (``transformation-v1`` / ``evidence-registry-v1``).
- *this* module never builds run_metadata and never mutates its input: it
  only assesses already-collected documents (read-only, AGENTS.md Raw Data
  Rule).  No ``cerberus`` import (``validation.core`` owns it); no platform
  names (G5 P8, source agnostic).

Evidence levels (§9.2)
----------------------
``observed`` (present in the file) and ``unknown`` (absent or null) are
assigned mechanically.  ``inferred`` / ``ambiguous`` exist in the vocabulary
for future cited upgrades via the evidence registry, but this module never
emits them on its own (G5 P2/P5: 推定で埋めない).  A contract test pins this.
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.core import validate_document
from validation.integrity import (
    check_transformation_lineage,
    sha256_file,
    verify_artifact_manifest,
)
from validation.reporting import Issue
from validation.schema_registry import get_schema

__all__ = [
    "ASSESSMENT_VERSION",
    "ESSENTIAL_PROVENANCE_PATHS",
    "EVIDENCE_LEVELS",
    "READINESS_LEVELS",
    "REGISTRY_REFERENCE_ERROR_CODES",
    "REQUIRED_PROVENANCE_PATHS",
    "assess_completeness",
    "assess_confidence",
    "assess_integrity",
    "assess_readiness",
    "assess_run",
    "build_provenance_assessment",
    "check_evidence_registry",
    "find_duplicate_run_ids",
    "get_path",
    "is_external_reference",
]

ASSESSMENT_VERSION = "1.0.0"

#: Evidence-level vocabulary (e.md §9.2).  Only ``observed`` / ``unknown``
#: are auto-assigned; see the module docstring.
EVIDENCE_LEVELS = ("observed", "inferred", "unknown", "ambiguous")

#: Reproducibility-readiness vocabulary (§9.4).  ``ready`` never promises a
#: byte-identical refetch: source APIs are non-deterministic, so readiness
#: means "the re-collection / re-computation inputs are fully recorded".
READINESS_LEVELS = ("ready", "partial", "not_ready", "unknown")

#: Flattened required paths of ``collection-run-v1`` (10 top-level required
#: keys plus their required nested leaves).  Pinned by a contract test so
#: the completeness denominator cannot drift silently.
REQUIRED_PROVENANCE_PATHS = (
    "schema_version",
    "run_id",
    "study_id",
    "source_id",
    "purpose",
    "collector",
    "collector.collector_id",
    "collector.adapter_id",
    "collection_started_at",
    "query_provenance",
    "query_provenance.query_id",
    "query_provenance.submitted_query",
    "temporal_provenance",
    "temporal_provenance.window_id",
    "temporal_provenance.requested_start",
    "temporal_provenance.requested_end_exclusive",
    "temporal_provenance.granularity",
    "temporal_provenance.timezone",
    "execution",
    "execution.status",
    "execution.returned_count",
    "execution.errors",
)

#: The required-9 legacy mapping (e.md §4.1) expressed as dotted paths.
#: Canonical table: ``collection.core.provenance`` module docstring.
ESSENTIAL_PROVENANCE_PATHS = (
    "run_id",
    "study_id",
    "source_id",
    "collector.collector_id",
    "collection_started_at",
    "query_provenance.query_id",
    "execution.returned_count",
    "purpose",
    "execution.errors",
)


#: Error-severity codes that mean "a registry reference does not resolve"
#: (P4-2 family).  Used to derive ``registry_resolvable`` for readiness.
#: Warnings/info (deprecated query, legacy collector, untraceable version)
#: never block resolvability.
REGISTRY_REFERENCE_ERROR_CODES = frozenset(
    {
        "REFERENCE_SOURCE_UNREGISTERED",
        "REFERENCE_COLLECTOR_UNREGISTERED",
        "REFERENCE_COLLECTOR_SOURCE_MISMATCH",
        "REFERENCE_ADAPTER_MISMATCH",
        "REFERENCE_QUERY_UNREGISTERED",
        "REFERENCE_COMPOUND_MISMATCH",
        "REFERENCE_STUDY_UNREGISTERED",
    }
)


def _issue(code, path, message, rule, severity="error"):
    return Issue(
        code=code,
        path=path,
        severity=severity,
        message=message,
        rule=rule,
    )


def get_path(document, dotted: str):
    """Return the value at ``dotted`` (``a.b.c``) or ``None`` when absent.

    ``None`` values count as absent: an explicit null is an explicit unknown
    (G5 P5), not a verified fact.
    """
    node = document
    if not isinstance(node, dict):
        return None
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return None if node is None else node


def _present(document, dotted: str) -> bool:
    value = get_path(document, dotted)
    if value is None:
        return False
    if isinstance(value, str) and not value:
        return False
    return True


def assess_completeness(document) -> dict:
    """§9.1: fraction of verified required paths (plus essential misses).

    A high score never excuses a missing essential path (§9.1: 重要な必須
    フィールドが1つ欠けても高得点で合格させない); ``essential_missing``
    carries that verdict separately for the readiness gate.
    """
    if not isinstance(document, dict):
        return {
            "total": len(REQUIRED_PROVENANCE_PATHS),
            "verified": 0,
            "score": 0.0,
            "missing": list(REQUIRED_PROVENANCE_PATHS),
            "essential_missing": list(ESSENTIAL_PROVENANCE_PATHS),
        }
    missing = [p for p in REQUIRED_PROVENANCE_PATHS if not _present(document, p)]
    essential_missing = [p for p in ESSENTIAL_PROVENANCE_PATHS if not _present(document, p)]
    verified = len(REQUIRED_PROVENANCE_PATHS) - len(missing)
    return {
        "total": len(REQUIRED_PROVENANCE_PATHS),
        "verified": verified,
        "score": round(verified / len(REQUIRED_PROVENANCE_PATHS), 4),
        "missing": missing,
        "essential_missing": essential_missing,
    }


def assess_confidence(document) -> dict:
    """§9.2: per-path evidence levels (mechanical: observed vs unknown).

    ``inferred`` / ``ambiguous`` are never emitted here (G5 P2/P5); they
    remain available for future cited upgrades recorded in the evidence
    registry (§11) and assessed by a later pass.
    """
    fields = {}
    for path in REQUIRED_PROVENANCE_PATHS:
        if isinstance(document, dict) and _present(document, path):
            fields[path] = "observed"
        else:
            fields[path] = "unknown"
    observed = sum(1 for level in fields.values() if level == "observed")
    return {
        "fields": fields,
        "observed_count": observed,
        "unknown_count": len(fields) - observed,
    }


def assess_integrity(document, *, base_dir=None, artifact_registry=None) -> dict:
    """§9.3: manifest existence / validity / hash verification summary.

    Read-only: delegates to ``validation.integrity.verify_artifact_manifest``
    and only summarizes its issue codes.  When no manifest is referenced or
    no ``base_dir`` is available the verdict is ``unknown`` (判定不能), never
    a pass and never a failure (G5 P5).
    """
    reference = document.get("artifact_manifest") if isinstance(document, dict) else None
    if not isinstance(reference, str) or not reference:
        return {
            "manifest_reference": None,
            "manifest_present": None,
            "manifest_valid": None,
            "verified": None,
            "artifact_issues": [],
            "note": "no artifact manifest referenced (integrity unknown)",
        }
    if base_dir is None:
        return {
            "manifest_reference": reference,
            "manifest_present": None,
            "manifest_valid": None,
            "verified": None,
            "artifact_issues": [],
            "note": "no base directory available (integrity unknown)",
        }
    issues = verify_artifact_manifest(
        Path(base_dir) / reference,
        base_dir=base_dir,
        artifact_registry=artifact_registry,
    )
    codes = sorted({issue.code for issue in issues})
    manifest_missing = "ARTIFACT_MANIFEST_MISSING" in codes
    manifest_invalid = "ARTIFACT_MANIFEST_INVALID" in codes
    manifest_present = not manifest_missing
    manifest_valid = manifest_present and not manifest_invalid
    file_problems = {
        "ARTIFACT_FILE_MISSING",
        "ARTIFACT_SIZE_MISMATCH",
        "ARTIFACT_HASH_MISMATCH",
    }
    verified = bool(manifest_valid) and not (set(codes) & file_problems)
    return {
        "manifest_reference": reference,
        "manifest_present": manifest_present,
        "manifest_valid": manifest_valid,
        "verified": verified,
        "artifact_issues": codes,
        "note": "",
    }


def assess_readiness(
    *,
    completeness: dict,
    strict_valid: bool | None,
    strict_error_codes=(),
    registry_resolvable: bool | None = None,
    integrity_verified: bool | None = None,
) -> dict:
    """§9.4: whether re-collection / re-computation inputs are recorded.

    Inputs are verdicts from the other three assessments plus the strict
    validation outcome; this function performs no I/O.  ``registry_resolvable``
    / ``integrity_verified`` accept ``None`` (判定不能) and degrade to
    ``partial`` rather than failing or passing silently.
    """
    if strict_valid is None:
        return {"readiness": "unknown", "reasons": ["strict validation was not run"]}
    if not isinstance(completeness, dict):
        return {"readiness": "unknown", "reasons": ["completeness was not assessed"]}
    essential_missing = completeness.get("essential_missing", [])
    if essential_missing:
        return {
            "readiness": "not_ready",
            "reasons": [f"essential provenance missing: {', '.join(essential_missing)}"],
        }
    if strict_valid is False:
        codes = sorted(set(strict_error_codes))
        suffix = f" ({', '.join(codes)})" if codes else ""
        return {"readiness": "not_ready", "reasons": [f"strict validation failed{suffix}"]}
    if registry_resolvable is False:
        return {"readiness": "not_ready", "reasons": ["registry references do not resolve"]}
    if integrity_verified is False:
        return {"readiness": "not_ready", "reasons": ["artifact integrity failed"]}
    partial_reasons = []
    if registry_resolvable is None:
        partial_reasons.append("registry references not checked (unknown)")
    if integrity_verified is None:
        partial_reasons.append("artifact integrity not verified (unknown)")
    if partial_reasons:
        return {"readiness": "partial", "reasons": partial_reasons}
    return {
        "readiness": "ready",
        "reasons": ["strict valid, references resolve, artifacts verified"],
    }


def find_duplicate_run_ids(entries) -> dict:
    """§8.2 P01: run_ids claimed by more than one strict run document.

    ``entries`` is an iterable of ``(target, run_id)``; ``None`` / empty
    run_ids (unreadable files) are ignored — absence is not identity.
    Returns ``{run_id: [targets...]}`` for duplicates only.
    """
    seen: dict[str, list] = {}
    for target, run_id in entries:
        if not isinstance(run_id, str) or not run_id:
            continue
        seen.setdefault(run_id, []).append(str(target))
    return {run_id: targets for run_id, targets in seen.items() if len(targets) > 1}


def is_external_reference(reference: str) -> bool:
    """True when ``reference`` names evidence outside this repository.

    Cloud actor-run URLs, dataset handles and URNs cannot be re-checked
    locally; they are recorded but reported as unverifiable (判定不能),
    never failed and never guessed (G5 P2/P5).
    """
    if not isinstance(reference, str):
        return False
    lowered = reference.lower()
    if "://" in reference:
        return True
    return lowered.startswith(("http:", "https:", "apify:", "urn:"))


def check_evidence_registry(document, *, repo_root) -> list[Issue]:
    """G5 §11: every evidence entry must be checkable or explicitly unknown.

    - local references (repository-relative paths) must exist, else
      ``EVIDENCE_REFERENCE_MISSING`` (error);
    - a recorded ``sha256`` must match the file, else
      ``EVIDENCE_HASH_MISMATCH`` (error; messages never contain digests);
    - external references yield ``EVIDENCE_REFERENCE_EXTERNAL`` (info:
      recorded but unverifiable);
    - a null ``sha256`` yields ``EVIDENCE_HASH_UNRECORDED`` (info: honest
      unknown, G5 P5);
    - duplicate ``evidence_id`` values yield ``EVIDENCE_ID_DUPLICATE``.

    Read-only.  Never records secrets: callers run
    ``validation.semantic.scan_for_secrets`` alongside (P7).
    """
    issues: list[Issue] = []
    if not isinstance(document, dict):
        return issues
    entries = document.get("evidence")
    if not isinstance(entries, list):
        return issues
    root = Path(repo_root)
    seen_ids: dict[str, int] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        prefix = f"/evidence/{index}"
        evidence_id = entry.get("evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            if evidence_id in seen_ids:
                issues.append(
                    _issue(
                        "EVIDENCE_ID_DUPLICATE",
                        f"{prefix}/evidence_id",
                        "duplicate evidence_id in the evidence registry",
                        "evidence_registry",
                    )
                )
            else:
                seen_ids[evidence_id] = index
        reference = entry.get("reference")
        if not isinstance(reference, str) or not reference:
            continue
        if is_external_reference(reference):
            issues.append(
                _issue(
                    "EVIDENCE_REFERENCE_EXTERNAL",
                    f"{prefix}/reference",
                    "external evidence reference is recorded but cannot be verified locally",
                    "evidence_registry",
                    severity="info",
                )
            )
            continue
        target = root / reference
        if not target.is_file():
            issues.append(
                _issue(
                    "EVIDENCE_REFERENCE_MISSING",
                    f"{prefix}/reference",
                    "evidence reference file does not exist",
                    "evidence_registry",
                )
            )
            continue
        expected = entry.get("sha256")
        if expected is None:
            issues.append(
                _issue(
                    "EVIDENCE_HASH_UNRECORDED",
                    f"{prefix}/sha256",
                    "evidence hash is not recorded (integrity unknown)",
                    "evidence_registry",
                    severity="info",
                )
            )
        elif isinstance(expected, str) and expected:
            try:
                actual = sha256_file(target)
            except OSError:
                issues.append(
                    _issue(
                        "EVIDENCE_REFERENCE_MISSING",
                        f"{prefix}/reference",
                        "evidence reference file cannot be read",
                        "evidence_registry",
                    )
                )
                continue
            if actual != expected:
                issues.append(
                    _issue(
                        "EVIDENCE_HASH_MISMATCH",
                        f"{prefix}/sha256",
                        "evidence sha256 does not match the file content",
                        "evidence_registry",
                    )
                )
    return issues


def _transformation_reports(run_dir: Path, known_artifact_ids) -> list[dict]:
    """Validate ``transformation-*.json`` files found beside a run (G5-T17).

    An absent transformation record is not a failure here — raw-only runs
    (like the G1 replay slice) have no derived data yet; the assessment
    records the absence explicitly.  A present record must be structurally
    valid and every input/output id must resolve (P18).
    """
    try:
        schema = get_schema("transformation-v1")
    except ValueError:
        return []
    reports = []
    for path in sorted(run_dir.glob("transformation-*.json")):
        try:
            with path.open(encoding="utf-8") as handle:
                record = json.load(handle)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            reports.append(
                {
                    "file": path.name,
                    "transformation_id": None,
                    "structurally_valid": False,
                    "lineage_issue_codes": ["TRANSFORMATION_FILE_UNREADABLE"],
                }
            )
            continue
        structural = validate_document(record, schema)
        lineage = check_transformation_lineage(
            record, known_artifact_ids=known_artifact_ids
        )
        reports.append(
            {
                "file": path.name,
                "transformation_id": record.get("transformation_id")
                if isinstance(record, dict)
                else None,
                "structurally_valid": bool(structural.valid),
                "lineage_issue_codes": sorted({issue.code for issue in lineage}),
            }
        )
    return reports


def _manifest_artifact_ids(run_dir: Path, reference) -> tuple[frozenset, bool]:
    """Artifact ids declared by the run's manifest (``(ids, readable)``)."""
    if not isinstance(reference, str) or not reference:
        return frozenset(), False
    try:
        with (run_dir / reference).open(encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return frozenset(), False
    artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(artifacts, list):
        return frozenset(), True
    return (
        frozenset(
            artifact["artifact_id"]
            for artifact in artifacts
            if isinstance(artifact, dict)
            and isinstance(artifact.get("artifact_id"), str)
        ),
        True,
    )


def assess_run(
    document,
    *,
    target: str = "",
    sha256: str | None = None,
    sha256_after: str | None = None,
    unchanged: bool | None = None,
    registries=None,
    base_dir=None,
) -> dict:
    """One run's full G5 assessment (§9 + §10 evidence levels + lineage).

    Runs the strict gate (never the legacy profile: the assessment must show
    what a new run would face), then derives completeness / confidence /
    integrity / readiness.  Read-only; ``document`` is never modified.
    """
    from validation.pipeline import validate_full  # deferred: no import cycle

    run_id = document.get("run_id") if isinstance(document, dict) else None
    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        target=target,
        registries=registries if registries is not None and registries.any() else None,
        base_dir=base_dir,
        verify_artifacts=base_dir is not None,
    )
    error_codes = sorted(
        {issue.code for issue in outcome.issues if issue.severity == "error"}
    )
    completeness = assess_completeness(document)
    confidence = assess_confidence(document)
    integrity = assess_integrity(
        document,
        base_dir=base_dir,
        artifact_registry=registries.artifact_registry if registries is not None else None,
    )
    if registries is None or not registries.any():
        registry_resolvable = None
    else:
        registry_resolvable = not (set(error_codes) & REGISTRY_REFERENCE_ERROR_CODES)
    readiness = assess_readiness(
        completeness=completeness,
        strict_valid=bool(outcome.valid),
        strict_error_codes=error_codes,
        registry_resolvable=registry_resolvable,
        integrity_verified=integrity.get("verified"),
    )
    manifest_reference = (
        document.get("artifact_manifest") if isinstance(document, dict) else None
    )
    run_dir = Path(base_dir) if base_dir is not None else None
    if run_dir is not None:
        known_ids, _ = _manifest_artifact_ids(run_dir, manifest_reference)
        transformations = _transformation_reports(run_dir, known_ids)
        lineage = {
            "run_id": run_id if isinstance(run_id, str) else None,
            "artifact_ids": sorted(known_ids),
            "transformations": transformations,
        }
    else:
        lineage = {
            "run_id": run_id if isinstance(run_id, str) else None,
            "artifact_ids": [],
            "transformations": [],
        }
    return {
        "run_id": run_id if isinstance(run_id, str) else None,
        "path": target,
        "sha256": sha256,
        "sha256_after": sha256_after,
        "unchanged": unchanged,
        "strict_valid": bool(outcome.valid),
        "strict_error_codes": error_codes,
        "completeness": completeness,
        "confidence": confidence,
        "integrity": integrity,
        "readiness": readiness["readiness"],
        "readiness_reasons": readiness["reasons"],
        "lineage": lineage,
        # v1 records no per-run evidence links; the registry-level evidence
        # lives in metadata/provenance/evidence-registry.json (G5 §11).
        "evidence_refs": [],
    }


def build_provenance_assessment(datasets_root, *, registries=None) -> dict:
    """Non-destructive G5 assessment over every ``run_metadata.json`` (§9/§10).

    Mirrors the ``audit-legacy`` / ``audit-temporal`` read-only convention:
    each file is hashed before and after, ``raw_modified`` records any drift,
    and unreadable files become ``unreadable`` / ``unknown`` entries — never
    failures of the audit itself.  No guessing (P2/P5): absent provenance is
    reported as ``unknown``, never inferred.
    """
    root = Path(datasets_root)
    files = sorted(root.rglob("run_metadata.json")) if root.is_dir() else []
    runs = []
    for path in files:
        try:
            before = sha256_file(path)
            with path.open(encoding="utf-8") as handle:
                document = json.load(handle)
            after = sha256_file(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            runs.append(
                {
                    "run_id": None,
                    "path": str(path),
                    "sha256": None,
                    "sha256_after": None,
                    "unchanged": None,
                    "strict_valid": None,
                    "strict_error_codes": [],
                    "completeness": assess_completeness(None),
                    "confidence": assess_confidence(None),
                    "integrity": assess_integrity(None),
                    "readiness": "unknown",
                    "readiness_reasons": ["run_metadata.json cannot be read"],
                    "lineage": {
                        "run_id": None,
                        "artifact_ids": [],
                        "transformations": [],
                    },
                    "evidence_refs": [],
                }
            )
            continue
        runs.append(
            assess_run(
                document,
                target=str(path),
                sha256=before,
                sha256_after=after,
                unchanged=before == after,
                registries=registries,
                base_dir=path.parent,
            )
        )
    readiness_counts: dict[str, int] = {}
    scores = []
    strict_valid_count = 0
    integrity_verified_count = 0
    for entry in runs:
        readiness_counts[entry["readiness"]] = readiness_counts.get(entry["readiness"], 0) + 1
        scores.append(entry["completeness"]["score"])
        if entry["strict_valid"] is True:
            strict_valid_count += 1
        if entry["integrity"].get("verified") is True:
            integrity_verified_count += 1
    return {
        "assessment_version": ASSESSMENT_VERSION,
        "profile": "provenance_assessment",
        "schema_id": "collection-run-v1",
        "target_glob": "datasets/**/run_metadata.json",
        "count": len(runs),
        "raw_modified": any(entry.get("unchanged") is False for entry in runs),
        "summary": {
            "readiness": readiness_counts,
            "mean_completeness": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "strict_valid": strict_valid_count,
            "integrity_verified": integrity_verified_count,
        },
        "runs": runs,
    }
