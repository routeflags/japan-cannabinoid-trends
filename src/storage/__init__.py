"""G4 storage contract: readers, content identification, inventory, catalog.

Contract source: ``docs/plans/20261013d.md`` (G4 - Artifact Registry,
Storage Contract & Data Catalog; local plan, not tracked).

Modules
-------
- ``storage.contracts``: reader contract (``ArtifactDescriptor`` /
  ``StorageReader``); a reader never rewrites raw data and never guesses a
  missing series (d.md §8, §12).
- ``storage.readers``: reader implementations keyed by ``reader_id``;
  ``metadata/artifacts/artifact-registry.json`` may only reference readers
  that exist here.
- ``storage.registry``: load / resolve the artifact registry (d.md §7).
- ``storage.sniff``: content-based artifact identification (d.md P3 / §16:
  file names alone never decide meaning).
- ``storage.inventory``: non-destructive legacy artifact inventory (§16).
- ``storage.catalog``: manifest-derived data catalog (§14; catalog is a
  regenerable index, the manifest stays the source of truth).
- ``storage.lineage``: catalog-level lineage checks (§15).
- ``storage.cli``: read / inspect / catalog demo CLI.

This package is source-agnostic (P7): nothing here may require a platform
name to read an artifact; platform-specific knowledge lives in the artifact
schemas registered in ``metadata/artifacts/artifact-registry.json``.
"""

from __future__ import annotations

__all__: list[str] = []
