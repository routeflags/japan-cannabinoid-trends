"""Schema Registry resolving stable schema IDs to schema documents.

Contract (docs/plans/20261013h.md §9):

- Every schema is addressable by a stable string ID (``collection-run-v1``
  plus the G1-G7 schemas registered in Phase 3).
- The registry manages both the schema *ID* and the schema *version*; the
  version is compared against a document's ``schema_version`` field by
  ``validation.semantic.check_schema_version`` (CV-20).
- Registering a new schema requires a matching Contract Test (§16 / §9).
  ``tests/validation/test_schema_coverage.py`` fails when a registered ID has
  no declared test module, so the rule is enforced mechanically.
- Unknown IDs raise ``ValueError`` so that CLI/config errors can be mapped to
  exit code 2 (schema / configuration error).

Profile handling
----------------
``collection-run-v1`` is the finalized (strict) G5 profile.
``collection-run-v1-running`` is the derived running-run profile (P3-1); see
``validation.schemas.collection_run`` for the exact difference.
"""

from __future__ import annotations

from validation.schemas.artifact import ARTIFACT_MANIFEST_SCHEMA
from validation.schemas.artifact_registry import ARTIFACT_REGISTRY_SCHEMA
from validation.schemas.collection_plan import COLLECTION_PLAN_SCHEMA
from validation.schemas.collection_run import (
    COLLECTION_RUN_RUNNING_SCHEMA,
    COLLECTION_RUN_SCHEMA,
)
from validation.schemas.coverage import COVERAGE_MANIFEST_SCHEMA
from validation.schemas.provenance import EVIDENCE_REGISTRY_SCHEMA, TRANSFORMATION_SCHEMA
from validation.schemas.query import (
    QUERY_REGISTRY_SCHEMA,
    QUERY_VARIANTS_REGISTRY_SCHEMA,
    QUERY_VARIANTS_SCHEMA,
)
from validation.schemas.registries import (
    COLLECTOR_REGISTRY_SCHEMA,
    SOURCE_REGISTRY_SCHEMA,
)
from validation.schemas.release import RELEASE_MANIFEST_SCHEMA
from validation.schemas.storage_policy import (
    PUBLICATION_DECISION_SCHEMA,
    STORAGE_POLICY_REGISTRY_SCHEMA,
)
from validation.schemas.study import (
    MEASUREMENT_REGISTRY_SCHEMA,
    RESEARCH_VIEW_SCHEMA,
    STUDY_REGISTRY_SCHEMA,
)
from validation.schemas.temporal import TEMPORAL_WINDOW_SCHEMA

SCHEMA_REGISTRY: dict[str, dict] = {
    # G5 run provenance (Phase 2) and its running-run profile (P3-1).
    "collection-run-v1": COLLECTION_RUN_SCHEMA,
    "collection-run-v1-running": COLLECTION_RUN_RUNNING_SCHEMA,
    # G1 source / collector registries (P3-3).
    "source-registry-v1": SOURCE_REGISTRY_SCHEMA,
    "collector-registry-v1": COLLECTOR_REGISTRY_SCHEMA,
    # G2 query registry / variants (P3-4); the variants *file* schema was
    # added with the G2 vertical slice (query-variants-v1 stays the block).
    "query-registry-v1": QUERY_REGISTRY_SCHEMA,
    "query-variants-v1": QUERY_VARIANTS_SCHEMA,
    "query-variants-registry-v1": QUERY_VARIANTS_REGISTRY_SCHEMA,
    # G3 temporal window (P3-5) and coverage manifest (ISS-20261015-COV-004).
    "temporal-window-v1": TEMPORAL_WINDOW_SCHEMA,
    "coverage-manifest-v1": COVERAGE_MANIFEST_SCHEMA,
    # G4 artifact manifest (P3-6) and artifact registry (G4 vertical slice).
    "artifact-manifest-v1": ARTIFACT_MANIFEST_SCHEMA,
    "artifact-registry-v1": ARTIFACT_REGISTRY_SCHEMA,
    # G5 transformation provenance (P3-7) and evidence registry (G5 slice).
    "transformation-v1": TRANSFORMATION_SCHEMA,
    "evidence-registry-v1": EVIDENCE_REGISTRY_SCHEMA,
    # G6 storage policy / publication decision (P3-8).
    "storage-policy-registry-v1": STORAGE_POLICY_REGISTRY_SCHEMA,
    "publication-decision-v1": PUBLICATION_DECISION_SCHEMA,
    # G7 study / measurement / research view (P3-9).
    "study-registry-v1": STUDY_REGISTRY_SCHEMA,
    "measurement-registry-v1": MEASUREMENT_REGISTRY_SCHEMA,
    "research-view-v1": RESEARCH_VIEW_SCHEMA,
    # G6 release manifest (ISS-20261015-REL-014 validation-only slice).
    "release-manifest-v1": RELEASE_MANIFEST_SCHEMA,
    # Collection plan (P6-1 initial contract).
    "collection-plan-v1": COLLECTION_PLAN_SCHEMA,
}

#: Contract version of each registered schema.  A document's
#: ``schema_version`` field must match this value (CV-20); changing a schema
#: requires a version decision recorded under the §19 procedure.
SCHEMA_VERSIONS: dict[str, str] = {
    schema_id: "1.0.0" for schema_id in SCHEMA_REGISTRY
}


def get_schema(schema_id: str) -> dict:
    """Return the schema document registered under ``schema_id``.

    Raises ``ValueError`` for unknown IDs; the registry never falls back to
    a default schema.
    """
    try:
        return SCHEMA_REGISTRY[schema_id]
    except KeyError:
        raise ValueError(f"Unknown schema: {schema_id}") from None


def get_schema_version(schema_id: str) -> str:
    """Return the contract version of ``schema_id`` (CV-20).

    Raises ``ValueError`` for unknown IDs, like :func:`get_schema`.
    """
    if schema_id not in SCHEMA_REGISTRY:
        raise ValueError(f"Unknown schema: {schema_id}")
    return SCHEMA_VERSIONS[schema_id]


def list_schema_ids() -> list[str]:
    """Return the registered schema IDs in sorted order."""
    return sorted(SCHEMA_REGISTRY)

