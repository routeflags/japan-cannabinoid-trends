"""Builder tests for ``transformation-v1`` records (ISS-20261015-PRV-010).

Contract sources: ``validation.schemas.provenance.TRANSFORMATION_SCHEMA`` (the
single structural truth), ``processing.reproduce.DERIVATIONS`` (the single
declaration of what derivation exists), ``docs/specs/validation-framework.md``
§18.3.

The decisive tests are :func:`test_every_declared_derivation_renders_a_valid_record`
(the registry and the record cannot drift apart: every declaration renders)
and :func:`test_platform_trends_slice_links_records_to_derived_artifacts` (a
fresh synthetic execution of the real builder produces records whose lineage
resolves against the files it just wrote).

No test writes a historical record: ``executed_at`` is always explicit (a
required keyword, never ``now()``), so a record can only describe the
execution the test just performed.
"""

from __future__ import annotations

import inspect
from copy import deepcopy
from pathlib import Path

import pytest

from processing.reproduce import DERIVATIONS
from processing.transformations import (
    TRANSFORMATION_BUILDER_VERSION,
    build_platform_trends_records,
    build_transformation_record,
    transformation_id_for,
)
from validation.core import validate_document
from validation.integrity import check_transformation_lineage
from validation.schema_registry import get_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTED_AT = "2026-10-15T00:00:00Z"


def _assert_valid_with_resolved_lineage(record: dict, known_ids) -> None:
    assert validate_document(record, get_schema("transformation-v1")).valid is True
    assert check_transformation_lineage(record, known_artifact_ids=frozenset(known_ids)) == []


# ---------------------------------------------------------------------------
# per-artifact records from the authoritative registry
# ---------------------------------------------------------------------------


def test_every_declared_derivation_renders_a_valid_record() -> None:
    """Each registry entry renders; the record cannot drift from the declaration."""

    assert DERIVATIONS  # the authority the builder renders must not be empty
    for artifact_path, derivation in sorted(DERIVATIONS.items()):
        record = build_transformation_record(artifact_path, executed_at=EXECUTED_AT)
        assert record["transformation_id"] == transformation_id_for(
            artifact_path, derivation.kind
        )
        assert record["parameters"]["derivation_kind"] == derivation.kind
        _assert_valid_with_resolved_lineage(
            record, [derivation.source, artifact_path]
        )


def test_record_defaults_follow_the_declaration() -> None:
    artifact_path = "datasets/cannabinoid-platform-trends/data/processed/manifest.json"
    derivation = DERIVATIONS[artifact_path]
    record = build_transformation_record(artifact_path, executed_at=EXECUTED_AT)
    assert record["input_artifact_ids"] == [derivation.source]
    assert record["output_artifact_ids"] == [artifact_path]
    assert record["status"] == "success"
    assert record["transformation_version"] == TRANSFORMATION_BUILDER_VERSION


def test_undeclared_artifact_has_no_record() -> None:
    """No declaration, no record: the builder never invents provenance."""

    with pytest.raises(KeyError):
        build_transformation_record(
            "datasets/stub-study/data/processed/unregistered.csv",
            executed_at=EXECUTED_AT,
        )


def test_invalid_execution_context_fails_closed() -> None:
    artifact_path = next(iter(sorted(DERIVATIONS)))
    with pytest.raises(ValueError):
        build_transformation_record(artifact_path, executed_at="2026-10-15 00:00:00")
    with pytest.raises(ValueError):
        build_transformation_record(artifact_path, executed_at=EXECUTED_AT, status="done")
    with pytest.raises(ValueError):
        build_transformation_record(
            artifact_path, executed_at=EXECUTED_AT, input_artifact_ids=[]
        )


def test_executed_at_is_always_explicit() -> None:
    """History cannot be back-filled: there is no default timestamp."""

    signature = inspect.signature(build_transformation_record)
    assert signature.parameters["executed_at"].default is inspect.Parameter.empty
    signature = inspect.signature(build_platform_trends_records)
    assert signature.parameters["executed_at"].default is inspect.Parameter.empty


def test_building_records_mutates_neither_registry_nor_inputs() -> None:
    before_registry = deepcopy(DERIVATIONS)
    artifact_path = next(iter(sorted(DERIVATIONS)))
    build_transformation_record(artifact_path, executed_at=EXECUTED_AT)
    assert DERIVATIONS == before_registry


def test_records_are_deterministic() -> None:
    artifact_path = next(iter(sorted(DERIVATIONS)))
    first = build_transformation_record(artifact_path, executed_at=EXECUTED_AT)
    second = build_transformation_record(artifact_path, executed_at=EXECUTED_AT)
    assert first == second


# ---------------------------------------------------------------------------
# platform-trends execution slice: records linked to derived artifacts
# ---------------------------------------------------------------------------


def test_platform_trends_slice_links_records_to_derived_artifacts(tmp_path) -> None:
    """A fresh synthetic execution yields records whose lineage resolves."""

    from processing.platform_trends import build_platform_trends

    manifest = build_platform_trends(REPO_ROOT, tmp_path)
    manifest_snapshot = deepcopy(manifest)

    (records) = build_platform_trends_records(
        manifest,
        executed_at=EXECUTED_AT,
        output_prefix=tmp_path.as_posix(),
    )
    assert manifest == manifest_snapshot  # the builder only reads the manifest
    assert len(records) == 1
    (record,) = records

    # Inputs are exactly the sources the manifest records (reused, not redeclared).
    assert record["input_artifact_ids"] == list(manifest["sources"])
    # Outputs are the five files the execution just wrote.
    assert len(record["output_artifact_ids"]) == 5
    for output_id in record["output_artifact_ids"]:
        assert Path(output_id).is_file()
    assert record["parameters"]["row_counts"] == manifest["row_counts"]

    known_ids = set(record["input_artifact_ids"]) | set(record["output_artifact_ids"])
    _assert_valid_with_resolved_lineage(record, known_ids)


def test_platform_trends_record_refuses_a_guessed_manifest() -> None:
    with pytest.raises(KeyError):
        build_platform_trends_records({"outputs": {}}, executed_at=EXECUTED_AT)
