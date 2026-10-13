"""G7 \u00a715 internal / public catalog separation.

Contract source: ``docs/plans/20261013g.md`` \u00a715 (inherits the G6
publication policy).

- The internal catalog keeps full entries (including ``run_dir`` lookup
  paths) for researchers.
- The public catalog carries approved metadata only: identifiers, registry
  links and statuses.  Lookup paths and any secret-bearing fields are
  stripped.  Nothing is published by this module (declaration only).
"""

from __future__ import annotations

__all__ = ["POLICY_VERSION", "split_public_internal", "PUBLIC_FIELDS"]

POLICY_VERSION = "1.0.0"

#: Fields safe for the public catalog (no paths, no credentials, no counts
#: that would leak non-public holdings beyond the entry's own identity).
PUBLIC_FIELDS = (
    "catalog_entry_id",
    "study_id",
    "run_id",
    "artifact_id",
    "source_id",
    "compound_ids",
    "query_ids",
    "measurement_id",
    "unit",
    "granularity",
    "availability",
    "quality_status",
)


def split_public_internal(catalog: dict, *, approved_ids: set[str] | frozenset = frozenset()) -> dict:
    """Split a catalog into public (approved only, stripped) and internal."""
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        entries = []
    approved = set(approved_ids)
    public: list[dict] = []
    internal: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        internal.append(entry)
        key = entry.get("catalog_entry_id")
        if key in approved and entry.get("availability") in ("public", "approved"):
            public.append({field: entry.get(field) for field in PUBLIC_FIELDS})
    return {
        "policy_version": POLICY_VERSION,
        "internal_count": len(internal),
        "public_count": len(public),
        "public": public,
        "internal": internal,
        "note": (
            "no publication performed: public lists approved metadata only; "
            "paths and credentials never enter the public catalog"
        ),
    }
