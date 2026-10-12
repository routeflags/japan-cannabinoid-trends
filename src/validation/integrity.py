"""Artifact integrity and lineage validators (Phase 4, P4-5 / P4-6).

Contract sources
----------------
- G4 instruction §10 (storage integrity: SHA-256, byte length, file
  existence), §15 (lineage: derived artifacts reference existing artifacts):
  ``docs/plans/20261013d.md``.
- G5 §8.2 P14/P15/P18 (manifest existence, hash match, transformation
  inputs): ``docs/plans/20261013e.md``.

All functions are read-only: files are opened for reading to compute the
SHA-256, nothing is written, and raw data is never modified (AGENTS.md).

Exit-code relevance: ``ARTIFACT_FILE_MISSING`` and ``ARTIFACT_MANIFEST_MISSING``
are classified as I/O failures by the CLI (exit code 3), separate from data
validation failures (exit code 1) and schema/config errors (exit code 2).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validation.core import validate_document
from validation.reporting import Issue
from validation.schema_registry import get_schema

__all__ = [
    "IO_ISSUE_CODES",
    "check_manifest_lineage",
    "check_transformation_lineage",
    "sha256_file",
    "verify_artifact_integrity",
    "verify_artifact_manifest",
]

#: Issue codes that the CLI classifies as file I/O errors (exit code 3).
IO_ISSUE_CODES = frozenset(
    {
        "ARTIFACT_FILE_MISSING",
        "ARTIFACT_MANIFEST_MISSING",
    }
)

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path) -> str:
    """Return the lowercase hex SHA-256 of ``path`` (streamed)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _issue(code, path, message, rule, severity="error"):
    return Issue(
        code=code,
        path=path,
        severity=severity,
        message=message,
        rule=rule,
    )


def verify_artifact_integrity(manifest: dict, *, base_dir) -> list[Issue]:
    """P4-5 / CV-09: verify every manifest artifact against the filesystem.

    - missing file -> ``ARTIFACT_FILE_MISSING`` (I/O class, exit 3);
    - byte length mismatch -> ``ARTIFACT_SIZE_MISMATCH``;
    - SHA-256 mismatch -> ``ARTIFACT_HASH_MISMATCH``.

    The manifest itself is not modified; checks run on a read-only basis.
    """
    issues: list[Issue] = []
    if not isinstance(manifest, dict):
        return issues
    base = Path(base_dir)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return issues

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        prefix = f"/artifacts/{index}"
        relative = artifact.get("path")
        if not isinstance(relative, str) or not relative:
            continue
        target = base / relative
        if not target.is_file():
            issues.append(
                _issue(
                    "ARTIFACT_FILE_MISSING",
                    f"{prefix}/path",
                    "artifact file does not exist",
                    "artifact_integrity",
                )
            )
            continue
        try:
            size = target.stat().st_size
            digest = sha256_file(target)
        except OSError:
            issues.append(
                _issue(
                    "ARTIFACT_FILE_MISSING",
                    f"{prefix}/path",
                    "artifact file cannot be read",
                    "artifact_integrity",
                )
            )
            continue
        expected_size = artifact.get("byte_length")
        if isinstance(expected_size, int) and expected_size != size:
            issues.append(
                _issue(
                    "ARTIFACT_SIZE_MISMATCH",
                    f"{prefix}/byte_length",
                    "byte_length does not match the file on disk",
                    "artifact_integrity",
                )
            )
        expected_digest = artifact.get("sha256")
        if isinstance(expected_digest, str) and expected_digest != digest:
            issues.append(
                _issue(
                    "ARTIFACT_HASH_MISMATCH",
                    f"{prefix}/sha256",
                    "sha256 does not match the file content",
                    "artifact_integrity",
                )
            )

    return issues


def check_manifest_lineage(manifest: dict, *, known_artifact_ids=()) -> list[Issue]:
    """P4-6 / CV-10: every ``derived_from`` reference must resolve.

    Resolution set = artifact ids declared by this manifest plus any external
    ids the caller knows (e.g. artifacts from other manifests).
    """
    issues: list[Issue] = []
    if not isinstance(manifest, dict):
        return issues
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return issues

    known = set(known_artifact_ids)
    for artifact in artifacts:
        if isinstance(artifact, dict) and isinstance(artifact.get("artifact_id"), str):
            known.add(artifact["artifact_id"])

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        derived_from = artifact.get("derived_from")
        if not isinstance(derived_from, list):
            continue
        for ref_index, reference in enumerate(derived_from):
            if isinstance(reference, str) and reference not in known:
                issues.append(
                    _issue(
                        "LINEAGE_REFERENCE_MISSING",
                        f"/artifacts/{index}/derived_from/{ref_index}",
                        "derived_from references an unknown artifact_id",
                        "lineage",
                    )
                )
    return issues


def check_transformation_lineage(
    transformation: dict, *, known_artifact_ids
) -> list[Issue]:
    """G5-T17 / e.md P18: transformation inputs and outputs must resolve.

    ``known_artifact_ids`` is mandatory here (pass ``frozenset()`` to state
    "no artifacts are known"): a transformation whose references cannot be
    resolved is a lineage failure, not a skipped check.
    """
    issues: list[Issue] = []
    if not isinstance(transformation, dict):
        return issues
    known = set(known_artifact_ids)

    for field in ("input_artifact_ids", "output_artifact_ids"):
        values = transformation.get(field)
        if not isinstance(values, list):
            continue
        for index, reference in enumerate(values):
            if isinstance(reference, str) and reference not in known:
                issues.append(
                    _issue(
                        "LINEAGE_REFERENCE_MISSING",
                        f"/{field}/{index}",
                        f"{field} references an unknown artifact_id",
                        "lineage",
                    )
                )
    return issues


def verify_artifact_manifest(
    path, *, base_dir=None, known_artifact_ids=()
) -> list[Issue]:
    """Load a manifest file and run structural + integrity + lineage checks.

    Returns issues; an unreadable / undecodable manifest yields
    ``ARTIFACT_MANIFEST_MISSING`` (I/O class).  The manifest file itself is
    only read, never rewritten.
    """
    manifest_path = Path(path)
    if not manifest_path.is_file():
        return [
            _issue(
                "ARTIFACT_MANIFEST_MISSING",
                "/artifact_manifest",
                "artifact manifest file does not exist",
                "artifact_integrity",
            )
        ]
    try:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return [
            _issue(
                "ARTIFACT_MANIFEST_MISSING",
                "/artifact_manifest",
                "artifact manifest cannot be read as JSON",
                "artifact_integrity",
            )
        ]

    issues: list[Issue] = []
    result = validate_document(manifest, get_schema("artifact-manifest-v1"))
    if not result.valid:
        # The nested structure is summarized as one issue: the CLI report for
        # a manifest belongs to the manifest validation itself, not the run.
        issues.append(
            _issue(
                "ARTIFACT_MANIFEST_INVALID",
                "/artifact_manifest",
                "artifact manifest does not satisfy artifact-manifest-v1",
                "artifact_manifest",
            )
        )
        return issues

    issues.extend(verify_artifact_integrity(manifest, base_dir=base_dir or manifest_path.parent))
    issues.extend(check_manifest_lineage(manifest, known_artifact_ids=known_artifact_ids))
    return issues
