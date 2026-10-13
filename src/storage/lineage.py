"""G4 §15 lineage helpers over a catalog.

The manifest-level check lives in ``validation.integrity.check_manifest_lineage``;
this module adds the cross-manifest view: a derived artifact may reference
an artifact recorded in another manifest, so references are resolved against
the whole catalog (d.md §15 "Lineageの参照先が存在しない場合は検証エラー").

Problems are plain dicts so the storage package stays independent of the
validation report layer; ``validation.storage_contract`` / ``storage.cli``
render them.
"""

from __future__ import annotations

__all__ = ["check_catalog_lineage", "collect_artifact_ids", "trace_ancestors"]


def collect_artifact_ids(catalog: dict) -> set[str]:
    """Every artifact id recorded in the catalog."""
    ids = set()
    for entry in catalog.get("entries", []) if isinstance(catalog, dict) else []:
        if isinstance(entry, dict) and isinstance(entry.get("artifact_id"), str):
            ids.add(entry["artifact_id"])
    return ids


def check_catalog_lineage(catalog: dict, *, known_artifact_ids=()) -> list[dict]:
    """Resolve every ``derived_from`` reference against the catalog + extras."""
    problems: list[dict] = []
    if not isinstance(catalog, dict):
        return problems
    known = set(known_artifact_ids) | collect_artifact_ids(catalog)
    for index, entry in enumerate(catalog.get("entries", []) or []):
        if not isinstance(entry, dict):
            continue
        derived_from = entry.get("derived_from")
        if not isinstance(derived_from, list):
            continue
        for ref_index, reference in enumerate(derived_from):
            if isinstance(reference, str) and reference not in known:
                problems.append(
                    {
                        "code": "LINEAGE_REFERENCE_MISSING",
                        "path": f"/entries/{index}/derived_from/{ref_index}",
                        "message": "derived_from references an unknown artifact_id",
                    }
                )
    return problems


def trace_ancestors(catalog: dict, artifact_id: str) -> list[str]:
    """Trace a derived artifact back to its raw ancestors (d.md §15).

    Breadth-first over ``derived_from``; references are visited in sorted
    order so the result is deterministic.  Cycles (invalid lineage) are
    stopped rather than looping.
    """
    index = {}
    for entry in catalog.get("entries", []) if isinstance(catalog, dict) else []:
        if isinstance(entry, dict) and isinstance(entry.get("artifact_id"), str):
            index[entry["artifact_id"]] = entry

    ancestors: list[str] = []
    seen = {artifact_id}
    queue = [artifact_id]
    while queue:
        current = queue.pop(0)
        entry = index.get(current)
        if not isinstance(entry, dict):
            continue
        for reference in sorted(entry.get("derived_from", []) or []):
            if not isinstance(reference, str) or reference in seen:
                continue
            seen.add(reference)
            ancestors.append(reference)
            queue.append(reference)
    return ancestors
