"""G4 §14 data catalog: a regenerable index built from artifact manifests.

"Manifestが正本、Catalogは派生インデックス": the catalog is generated from the
``artifact-manifest.json`` documents (plus the sibling ``run_metadata.json``
for study / source / query / window enrichment).  It carries no timestamp
and is sorted deterministically, so identical manifests always produce
byte-identical output (G4-T16).

Legacy artifacts without a manifest are not listed here (P8); they are
covered by ``storage.inventory`` instead.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["CATALOG_VERSION", "build_catalog"]

CATALOG_VERSION = "1.0.0"


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _display_path(path: Path, root: Path) -> str:
    for base in (root.parent, root):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def build_catalog(datasets_root) -> dict:
    """Build the search index over every artifact manifest under the root."""
    root = Path(datasets_root)
    manifest_paths = sorted(root.rglob("artifact-manifest.json")) if root.is_dir() else []
    entries: list[dict] = []
    errors: list[dict] = []

    for manifest_path in manifest_paths:
        manifest = _load_json(manifest_path)
        if not isinstance(manifest, dict):
            errors.append(
                {"path": _display_path(manifest_path, root), "reason": "manifest_unreadable"}
            )
            continue
        base = manifest_path.parent
        metadata = _load_json(base / "run_metadata.json")
        metadata = metadata if isinstance(metadata, dict) else {}
        query = metadata.get("query_provenance")
        query = query if isinstance(query, dict) else {}
        temporal = metadata.get("temporal_provenance")
        temporal = temporal if isinstance(temporal, dict) else {}
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list):
            errors.append(
                {
                    "path": _display_path(manifest_path, root),
                    "reason": "artifacts_not_a_list",
                }
            )
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            entry = {
                "artifact_id": artifact.get("artifact_id"),
                "study_id": metadata.get("study_id"),
                "run_id": manifest.get("run_id") or metadata.get("run_id"),
                "source_id": metadata.get("source_id"),
                "compound_id": query.get("compound_id"),
                "query_id": query.get("query_id"),
                "window_id": temporal.get("window_id"),
                "artifact_type": artifact.get("artifact_type"),
                "format": artifact.get("format"),
                "schema_id": artifact.get("schema_id"),
                "layer": artifact.get("layer"),
                "record_count": artifact.get("record_count"),
                "completeness": artifact.get("completeness"),
                "path": _display_path(base / str(artifact.get("path")), root),
            }
            if isinstance(artifact.get("derived_from"), list):
                entry["derived_from"] = [ref for ref in artifact["derived_from"] if isinstance(ref, str)]
            if isinstance(artifact.get("transformation"), dict):
                entry["transformation"] = {
                    "name": artifact["transformation"].get("name"),
                    "version": artifact["transformation"].get("version"),
                }
            entries.append(entry)

    entries.sort(
        key=lambda entry: (
            str(entry.get("study_id") or ""),
            str(entry.get("run_id") or ""),
            str(entry.get("layer") or ""),
            str(entry.get("artifact_id") or ""),
        )
    )
    return {
        "catalog_version": CATALOG_VERSION,
        "generated_from": ["artifact-manifest-v1", "collection-run-v1"],
        "datasets_root": _display_path(root, root),
        "manifest_count": len(manifest_paths),
        "count": len(entries),
        "errors": errors,
        "entries": entries,
    }
