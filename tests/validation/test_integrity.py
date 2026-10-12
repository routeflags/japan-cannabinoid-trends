"""Integrity and lineage tests (P4-5 / P4-6 / CV-09 / CV-10).

Real files are written under tmp_path; every check is read-only.
"""

import hashlib
import json
from pathlib import Path

from validation.integrity import (
    IO_ISSUE_CODES,
    check_manifest_lineage,
    check_transformation_lineage,
    sha256_file,
    verify_artifact_integrity,
    verify_artifact_manifest,
)


def _payload(tmp_path: Path, name: str = "payload.json", content: bytes = b'{"a": 1}') -> Path:
    target = tmp_path / name
    target.write_bytes(content)
    return target


def _manifest(tmp_path: Path, payload: Path, **overrides) -> dict:
    raw = payload.read_bytes()
    artifact = {
        "artifact_id": "artifact-001",
        "path": payload.name,
        "artifact_type": "raw_records",
        "format": "json",
        "schema_id": "social-post-v1",
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "layer": "raw",
        "completeness": "complete",
    }
    artifact.update(overrides)
    return {
        "schema_version": "1.0.0",
        "run_id": "run-001",
        "artifacts": [artifact],
    }


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


def test_sha256_file_matches_hashlib(tmp_path):
    payload = _payload(tmp_path, content=b"hello world")
    assert sha256_file(payload) == hashlib.sha256(b"hello world").hexdigest()


def test_intact_artifact_passes(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    assert verify_artifact_integrity(manifest, base_dir=tmp_path) == []


def test_cv09_tampered_content_fails(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    payload.write_bytes(b'{"a": 2}')  # size differs too
    issues = verify_artifact_integrity(manifest, base_dir=tmp_path)
    assert "ARTIFACT_HASH_MISMATCH" in _codes(issues)


def test_size_mismatch_is_reported(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload, byte_length=999)
    assert _codes(verify_artifact_integrity(manifest, base_dir=tmp_path)) == [
        "ARTIFACT_SIZE_MISMATCH"
    ]


def test_missing_file_is_io_class(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    payload.unlink()
    issues = verify_artifact_integrity(manifest, base_dir=tmp_path)
    assert _codes(issues) == ["ARTIFACT_FILE_MISSING"]
    assert "ARTIFACT_FILE_MISSING" in IO_ISSUE_CODES


def test_integrity_does_not_modify_files(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    before = payload.read_bytes()
    verify_artifact_integrity(manifest, base_dir=tmp_path)
    assert payload.read_bytes() == before


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------


def test_lineage_resolves_inside_manifest(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    manifest["artifacts"].append(
        {
            "artifact_id": "monthly-counts-001",
            "path": "monthly.json",
            "artifact_type": "aggregate",
            "format": "json",
            "schema_id": "monthly-count-v1",
            "byte_length": 1,
            "sha256": "0" * 64,
            "layer": "processed",
            "completeness": "complete",
            "derived_from": ["artifact-001"],
        }
    )
    assert check_manifest_lineage(manifest) == []


def test_cv10_dangling_reference_fails(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    manifest["artifacts"][0]["derived_from"] = ["artifact-not-existing"]
    issues = check_manifest_lineage(manifest)
    assert _codes(issues) == ["LINEAGE_REFERENCE_MISSING"]
    assert issues[0].path == "/artifacts/0/derived_from/0"


def test_lineage_external_ids_can_satisfy_references(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    manifest["artifacts"][0]["derived_from"] = ["artifact-external"]
    assert check_manifest_lineage(manifest, known_artifact_ids=["artifact-external"]) == []


def test_transformation_lineage_references(tmp_path):
    transformation = json.loads(
        (Path(__file__).parent / "fixtures" / "transformation.json").read_text(encoding="utf-8")
    )
    missing = check_transformation_lineage(transformation, known_artifact_ids=[])
    assert _codes(missing) == [
        "LINEAGE_REFERENCE_MISSING",
        "LINEAGE_REFERENCE_MISSING",
    ]  # one input + one output
    resolved = check_transformation_lineage(
        transformation, known_artifact_ids=["artifact-001", "monthly-counts-001"]
    )
    assert resolved == []


def test_verify_artifact_manifest_end_to_end(tmp_path):
    payload = _payload(tmp_path)
    manifest = _manifest(tmp_path, payload)
    manifest_path = tmp_path / "artifact-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert verify_artifact_manifest(manifest_path, base_dir=tmp_path) == []

    payload.write_bytes(b'{"a": 2}')
    issues = verify_artifact_manifest(manifest_path, base_dir=tmp_path)
    assert "ARTIFACT_HASH_MISMATCH" in _codes(issues)


def test_verify_artifact_manifest_missing_file_is_io():
    issues = verify_artifact_manifest(Path("/nonexistent/artifact-manifest.json"))
    assert _codes(issues) == ["ARTIFACT_MANIFEST_MISSING"]
    assert "ARTIFACT_MANIFEST_MISSING" in IO_ISSUE_CODES


def test_verify_artifact_manifest_rejects_invalid_structure(tmp_path):
    manifest_path = tmp_path / "artifact-manifest.json"
    manifest_path.write_text(json.dumps({"artifacts": "nope"}), encoding="utf-8")
    issues = verify_artifact_manifest(manifest_path, base_dir=tmp_path)
    assert _codes(issues) == ["ARTIFACT_MANIFEST_INVALID"]
