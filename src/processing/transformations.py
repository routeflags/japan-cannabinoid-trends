'''Build ``transformation-v1`` records from the declared derivations.

Authority rule (ISS-20261015-PRV-010)
--------------------------------------
The executable derivation registry :data:`processing.reproduce.DERIVATIONS` is
the authoritative declaration of *what derivation exists and how it executes*
(source, columns, kind, discrepancies).  Records built here are *derived
views* emitted alongside a generation for machine-readable lineage: they are
never hand-edited, never stored as a second registry, and never written for
historical outputs whose inputs and derivation are not explicit and verifiable
(no retroactive fabrication; new generations only).

Enforcement stays in one place: :func:`processing.reproduce.reproduce_artifact`
and :func:`processing.reproduce.audit_processed_artifacts` decide whether an
artifact is re-derivable.  This module only renders the declared derivation
into the ``transformation-v1`` shape and refuses anything undeclared
(``KeyError`` for an artifact with no ``DERIVATIONS`` entry) or structurally
invalid (``ValueError``).

Structural truth stays in one place as well: records are validated with the
existing ``TRANSFORMATION_SCHEMA``
(:mod:`validation.schemas.provenance`) and lineage-checked with the existing
:func:`validation.integrity.check_transformation_lineage`.  Nothing here
redefines the schema or the lineage rule.

Granularity
-----------
One record describes one *execution*.  ``build_transformation_record`` renders
a single declared derivation (default inputs ``[derivation.source]``, default
output the artifact path).  ``build_platform_trends_records`` renders the one
``build_platform_trends`` execution that emits all five release files: inputs
are the source documents the manifest itself records (reused, not redeclared)
and outputs are the five processed paths.  Per-table input fiction (e.g.
claiming the code-static metric dictionary was read from the Google Trends
summary) is deliberately avoided; the static-table caveat travels in
``parameters``.

The builder writes nothing into ``data/processed/`` on its own: callers pass
a manifest (or an artifact path) plus the execution context and decide where
the record goes.  There is no side channel into the release layer.
'''

from __future__ import annotations

__all__ = [
    "TRANSFORMATION_BUILDER_VERSION",
    "PLATFORM_TRENDS_OUTPUT_PREFIX",
    "transformation_id_for",
    "build_transformation_record",
    "build_platform_trends_records",
]

TRANSFORMATION_BUILDER_VERSION = "1.0.0"

#: Default downstream layer for the platform-trends release files.  This is the
#: same directory the ``make platform-trends`` production target writes; tests
#: and synthetic runs override it via ``output_prefix``.
PLATFORM_TRENDS_OUTPUT_PREFIX = (
    "datasets/cannabinoid-platform-trends/data/processed"
)

#: Artifacts emitted by one ``build_platform_trends`` execution, in manifest
#: ``outputs`` order plus the manifest itself.
PLATFORM_TRENDS_OUTPUT_NAMES = (
    "trend_observations.csv",
    "platform_coverage.csv",
    "metric_dictionary.csv",
    "source_run_index.csv",
    "manifest.json",
)


def transformation_id_for(artifact_path: str, kind: str) -> str:
    """Deterministic record id for one declared derivation.

    The id names the transformation (``kind`` + artifact path); the execution
    is distinguished by ``executed_at``.  Readable on purpose so a reviewer
    can link a record back to its registry entry without a lookup table.
    """
    return f"{kind}:{artifact_path}"


def build_transformation_record(
    artifact_path: str,
    *,
    executed_at: str,
    status: str = "success",
    code_commit: str | None = None,
    input_artifact_ids: list[str] | tuple[str, ...] | None = None,
    output_artifact_ids: list[str] | tuple[str, ...] | None = None,
    parameters: dict | None = None,
) -> dict:
    """Render one ``DERIVATIONS`` entry as a ``transformation-v1`` record.

    Raises ``KeyError`` when ``artifact_path`` has no declared derivation (no
    record without a declaration) and ``ValueError`` when the rendered record
    does not satisfy ``TRANSFORMATION_SCHEMA`` (fail closed, e.g. a naive
    ``executed_at`` or an unknown ``status``).  Read-only: the registry and
    the artifact are never modified.
    """
    from processing.reproduce import DERIVATIONS
    from validation.core import validate_document
    from validation.schema_registry import get_schema

    derivation = DERIVATIONS[artifact_path]
    record: dict = {
        "transformation_id": transformation_id_for(artifact_path, derivation.kind),
        "transformation_name": derivation.kind,
        "transformation_version": TRANSFORMATION_BUILDER_VERSION,
        "executed_at": executed_at,
        "input_artifact_ids": (
            list(input_artifact_ids)
            if input_artifact_ids is not None
            else [derivation.source]
        ),
        "output_artifact_ids": (
            list(output_artifact_ids)
            if output_artifact_ids is not None
            else [artifact_path]
        ),
        "parameters": (
            dict(parameters)
            if parameters is not None
            else {
                "derivation_kind": derivation.kind,
                "columns": list(derivation.columns),
                "notes": list(derivation.notes),
                "source_published": derivation.source_published,
                "builder_version": TRANSFORMATION_BUILDER_VERSION,
            }
        ),
        "status": status,
    }
    if code_commit is not None:
        record["code_commit"] = code_commit
    result = validate_document(record, get_schema("transformation-v1"))
    if not result.valid:
        raise ValueError(
            f"rendered transformation record is invalid: {result.errors!r}"
        )
    return record


def build_platform_trends_records(
    manifest: dict,
    *,
    executed_at: str,
    status: str = "success",
    code_commit: str | None = None,
    output_prefix: str = PLATFORM_TRENDS_OUTPUT_PREFIX,
) -> list[dict]:
    """Render the one ``build_platform_trends`` execution as a record.

    Inputs are the source documents the ``manifest`` itself records
    (``manifest["sources"]``); outputs are the five processed paths under
    ``output_prefix``.  ``manifest`` is read, never modified.  Raises
    ``KeyError`` when the manifest lacks ``sources`` / ``outputs`` / one of
    the expected tables (no guessing of inputs) and ``ValueError`` when the
    rendered record is structurally invalid.
    """
    from processing.platform_trends import (
        COVERAGE_COLUMNS,
        METRIC_COLUMNS,
        OBSERVATION_COLUMNS,
        RUN_INDEX_COLUMNS,
    )
    from validation.core import validate_document
    from validation.schema_registry import get_schema

    sources = manifest["sources"]
    outputs = manifest["outputs"]
    table_columns = {
        outputs["trend_observations"]: list(OBSERVATION_COLUMNS),
        outputs["platform_coverage"]: list(COVERAGE_COLUMNS),
        outputs["metric_dictionary"]: list(METRIC_COLUMNS),
        outputs["source_run_index"]: list(RUN_INDEX_COLUMNS),
    }
    ordered_outputs = [f"{output_prefix}/{name}" for name in PLATFORM_TRENDS_OUTPUT_NAMES]
    record: dict = {
        "transformation_id": (
            "platform-trends:build_platform_trends:"
            f"{output_prefix}/trend_observations.csv"
        ),
        "transformation_name": "platform-trends:build_platform_trends",
        "transformation_version": TRANSFORMATION_BUILDER_VERSION,
        "executed_at": executed_at,
        "input_artifact_ids": list(sources),
        "output_artifact_ids": ordered_outputs,
        "parameters": {
            "generated_by": "processing.platform_trends.build_platform_trends",
            "table_columns": table_columns,
            "row_counts": dict(manifest["row_counts"]),
            "static_table_note": (
                "metric_dictionary rows are code-defined in "
                "processing.platform_trends._metric_rows (cross-platform "
                "comparability is always 'no'); the execution still emits "
                "the file, so it is listed as an output."
            ),
            "excluded_sources": dict(manifest.get("excluded_sources", {})),
            "builder_version": TRANSFORMATION_BUILDER_VERSION,
        },
        "status": status,
    }
    if code_commit is not None:
        record["code_commit"] = code_commit
    result = validate_document(record, get_schema("transformation-v1"))
    if not result.valid:
        raise ValueError(
            f"rendered platform-trends record is invalid: {result.errors!r}"
        )
    return [record]
