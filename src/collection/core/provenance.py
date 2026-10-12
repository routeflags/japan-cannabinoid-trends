"""Run manifest / provenance building for new collection runs (G1 §10).

Every new run is written as three files in its staging directory:

- ``payload.json`` (or the adapter's filename): the raw transport response,
  preserved as received;
- ``artifact-manifest.json`` (``artifact-manifest-v1``): SHA-256 and byte
  length computed from the files on disk - never copied from a template;
- ``run_metadata.json`` (``collection-run-v1``): collection provenance.

The required-9 mapping (G5 §4.1, e.md) is:

===============  =======================================
legacy field     new field
===============  =======================================
run_id           run_id
study_id         study_id
source           source_id
collection_tool  collector.collector_id / .version
collection_ts    collection_started_at
queries          query_provenance
data count       execution.returned_count
purpose          purpose
error record     execution.errors
===============  =======================================

Secret handling (G1 §10): only non-secret, allow-listed parameters are
recorded; the adapter decides what enters ``submitted_parameters``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from validation.integrity import sha256_file

from collection.core.contracts import CollectionResult

__all__ = [
    "COLLECTION_CORE_VERSION",
    "StagedArtifact",
    "build_artifact_manifest",
    "build_run_metadata",
    "default_run_id",
    "iso_timestamp",
    "run_id_timestamp",
]

COLLECTION_CORE_VERSION = "1.0.0"


def _ensure_aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def run_id_timestamp(moment: datetime) -> str:
    """``YYYYMMDDTHHMMSSZ`` (AGENTS.md run identity format)."""
    return _ensure_aware(moment).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_timestamp(moment: datetime) -> str:
    """Second-precision ISO 8601 UTC timestamp for metadata fields."""
    return _ensure_aware(moment).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(value: str) -> str:
    cleaned = []
    for character in value.lower():
        if character.isalnum() or character in "-_.":
            cleaned.append(character)
        elif character in " \t\n_":
            cleaned.append("-")
    slug = "".join(cleaned).strip("-.")
    return slug or "run"


def default_run_id(source_id: str, study_id: str, moment: datetime) -> str:
    """``<timestamp>-<source>-<study>`` (AGENTS.md run identity format).

    Repeated runs of the same query remain distinguishable through the
    timestamp; an explicit ``run_id`` may be supplied instead (tests and
    replays use fixed IDs for determinism).
    """
    return f"{run_id_timestamp(moment)}-{_slug(source_id)}-{_slug(study_id)}"


@dataclass
class StagedArtifact:
    """One file in a staged run that becomes an artifact manifest entry."""

    artifact_id: str
    path: str  # relative to the run directory
    artifact_type: str
    format: str
    schema_id: str
    layer: str = "raw"
    completeness: str = "complete"
    record_count: int | None = None
    media_type: str | None = None
    derived_from: list = field(default_factory=list)


def build_artifact_manifest(run_id: str, run_dir, artifacts) -> dict:
    """Build an ``artifact-manifest-v1`` document from files on disk.

    ``sha256`` / ``byte_length`` are computed from the actual files; a
    missing file is a caller error (the pipeline stages every artifact before
    building the manifest).
    """
    items = []
    base = Path(run_dir)
    for artifact in artifacts:
        target = base / artifact.path
        stat = target.stat()
        item = {
            "artifact_id": artifact.artifact_id,
            "path": artifact.path,
            "artifact_type": artifact.artifact_type,
            "format": artifact.format,
            "schema_id": artifact.schema_id,
            "byte_length": stat.st_size,
            "sha256": sha256_file(target),
            "layer": artifact.layer,
            "completeness": artifact.completeness,
        }
        if artifact.media_type:
            item["media_type"] = artifact.media_type
        if artifact.record_count is not None:
            item["record_count"] = artifact.record_count
        if artifact.derived_from:
            item["derived_from"] = list(artifact.derived_from)
        items.append(item)
    return {"schema_version": "1.0.0", "run_id": run_id, "artifacts": items}


def _temporal_provenance(plan: dict, result: CollectionResult, window_id: str) -> dict:
    """Merge the plan's requested window with the adapter's observed facts.

    The adapter's ``temporal`` block carries what only the source can know
    (granularity, week boundary, window type, observed bounds); the plan
    supplies the requested window and, when given, granularity / timezone as
    fallbacks.
    """
    plan_window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    temporal = result.temporal if isinstance(result.temporal, dict) else {}

    block = {
        "window_id": window_id,
        "requested_start": plan_window.get("start"),
        "requested_end_exclusive": plan_window.get("end_exclusive"),
        "granularity": temporal.get("granularity", plan_window.get("granularity")),
        "timezone": plan_window.get("timezone") or temporal.get("timezone") or "UTC",
    }
    if plan_window.get("week_start"):
        block["week_start"] = plan_window["week_start"]
    for key in (
        "collector_window_type",
        "boundary_semantics",
        "exact_window_match",
        "observed_min_timestamp",
        "observed_max_timestamp",
        "week_start",
    ):
        if key in temporal:
            block[key] = temporal[key]
    if result.submitted_parameters:
        block["submitted_parameters"] = dict(result.submitted_parameters)
    return block


def build_run_metadata(
    *,
    plan: dict,
    collector_entry: dict,
    adapter,
    result: CollectionResult,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    artifact_manifest_name: str,
    window_id: str,
    environment: dict | None = None,
    query_registry_version: str | None = None,
) -> dict:
    """Build a ``collection-run-v1`` run_metadata document from real facts.

    Identity fields come from the registry entry (collector) and the adapter
    (adapter_id) - the pipeline has already cross-checked that they agree.
    ``query_registry_version`` records which query-registry definition version
    the run was planned against (b.md §7); it is omitted when no registry is
    loaded so the field is never invented.
    """
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    query_provenance = {
        "query_id": plan.get("query_id"),
        "submitted_query": query.get("text"),
    }
    if query.get("compound_id"):
        query_provenance["compound_id"] = query["compound_id"]
    if query.get("intent_id"):
        query_provenance["intent_id"] = query["intent_id"]
    if query_registry_version:
        query_provenance["query_registry_version"] = query_registry_version

    collector_block = {
        "collector_id": collector_entry.get("collector_id"),
        "adapter_id": adapter.adapter_id,
        "version": collector_entry.get("version", adapter.version),
    }
    for key in ("provider", "transport", "external_id"):
        if collector_entry.get(key):
            collector_block[key] = collector_entry[key]

    execution = {
        "status": result.status,
        "returned_count": result.returned_count,
        "errors": list(result.errors),
    }
    if result.pagination_exhausted is not None:
        execution["pagination_exhausted"] = result.pagination_exhausted

    document = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "study_id": plan.get("study_id"),
        "source_id": plan.get("source_id"),
        "purpose": plan.get("purpose") or "collection run",
        "collector": collector_block,
        "collection_started_at": iso_timestamp(started_at),
        "collection_finished_at": iso_timestamp(finished_at),
        "query_provenance": query_provenance,
        "temporal_provenance": _temporal_provenance(plan, result, window_id),
        "execution": execution,
        "artifact_manifest": artifact_manifest_name,
    }
    if environment:
        document["environment"] = dict(environment)
    return document
