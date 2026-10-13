"""G7 research layer: federated catalog, comparability gate, research views.

Contract source: ``docs/plans/20261013g.md`` (G7).

Design rules (AGENTS.md + G7 P1-P8):

- Study directories are never moved, merged or edited here (P1, P2, P7).
  The catalog only *points at* studies.
- The catalog is a regenerable derived index (G7 \u00a75.1 / \u00a714,
  G4 ``storage.catalog`` precedent): manifests and registries are the
  source of truth.  Rebuilds are deterministic and carry no timestamps.
- Discovery (finding artifacts) never implies statistical comparability
  (P4).  Every search result carries that note.
- Units are recorded source-natively and never force-normalized (P6).
- No ``cerberus`` import here: structural checks go through
  ``validation.*`` (structure/meaning separation).
- Read-only: builders never modify raw data or old metadata.
"""
