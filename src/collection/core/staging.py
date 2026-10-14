"""Declaration-driven staging driver (COL-017): declaration -> ``stage_run``.

An operator who obtained a payload outside the pipeline (a cloud dataset
export, a handover directory, a shell script) writes **one declaration
document** (``staging-declaration-v1``) that states what only the operator can
know: which search produced each file, the requested window and the relative
request it was resolved from, the run timestamps and their basis, and what the
collector reported.  This module turns that declaration into exactly the inputs
``collection.core.pipeline.stage_run`` takes, for every run the declaration
lists.

Role boundary (the whole point of the driver being separate from the gate):

- adoption is not decided here - ``stage_run`` writes ``.staging/<run-id>/``
  and ``adopt`` owns the L1 verdict (producer / verdict separation, spec §3.3);
- no rule of ``stage_run`` / the storage contract is re-implemented: window
  completeness and ordering, registry references, path safety, run-id
  collisions and payload interpretation stay where they already live.  A
  declared ``record_count`` is passed through unchanged for L1 to verify; an
  absent one is derived with the registered reader for the declared schema -
  one counting implementation (``storage.readers``), never a line count;
- the driver adds **no source knowledge**: the declaration (not this module)
  names the source, collector, query and artifact schema, so the core keeps
  its platform-name-free rule (P1).

What the declaration can never do: make the driver guess.  The keyword ->
``query_id`` mapping is declared per run and validated against the query
registry (an unregistered ``query_id`` is a configuration error; the registry
is the record of truth for ``compound_id`` / ``intent_id``).  The payload's own
columns are never consulted to decide what a file is.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from validation.core import validate_document
from validation.reporting import normalize_cerberus_errors
from validation.schemas.artifact import (
    ARTIFACT_FORMATS,
    ARTIFACT_TYPES,
    COMPLETENESS_VALUES,
)
from validation.schemas.collection_run import EXECUTION_STATUSES
from validation.schemas.temporal import COLLECTOR_WINDOW_TYPES, GRANULARITIES
from validation.semantic import Registries

from storage.contracts import ArtifactDescriptor
from storage.readers import get_reader
from storage.registry import ArtifactRegistry

from collection.core.pipeline import CollectedArtifact, stage_run

__all__ = [
    "STAGING_DECLARATION_VERSION",
    "STAGING_DRIVER_VERSION",
    "Declaration",
    "DeclarationError",
    "load_declaration",
    "stage_declaration",
]

STAGING_DRIVER_VERSION = "1.0.0"
STAGING_DECLARATION_VERSION = "staging-declaration-v1"

_ARTIFACT_SCHEMA = {
    "source": {"type": "string", "required": True, "empty": False},
    "path": {"type": "string", "required": True, "empty": False},
    "artifact_type": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_TYPES,
    },
    "format": {"type": "string", "required": True, "allowed": ARTIFACT_FORMATS},
    "schema_id": {"type": "string", "required": True, "empty": False},
    "completeness": {"type": "string", "allowed": COMPLETENESS_VALUES},
    "record_count": {"type": "integer", "nullable": True, "min": 0},
    "media_type": {"type": "string", "nullable": True},
}

_RUN_SCHEMA = {
    # Optional: when omitted, ``stage_run`` derives it from started_at
    # (``YYYYMMDDTHHMMSSZ-<source>-<study>``, AGENTS.md).
    "run_id": {"type": "string", "nullable": True, "empty": False},
    "study_id": {"type": "string", "required": True, "empty": False},
    "source_id": {"type": "string", "required": True, "empty": False},
    "collector_id": {"type": "string", "required": True, "empty": False},
    "purpose": {"type": "string", "required": True, "empty": False},
    # The search this payload answers.  Declared, never inferred from the
    # payload; ``query_id`` must resolve in the query registry.
    "query": {
        "type": "dict",
        "required": True,
        "schema": {
            "keyword": {"type": "string", "required": True, "empty": False},
            "query_id": {"type": "string", "required": True, "empty": False},
        },
    },
    # The absolute window recorded as the requested period (the pipeline
    # requires one); ``window_id`` is passed through when registered.
    "window": {
        "type": "dict",
        "required": True,
        "schema": {
            "window_id": {"type": "string", "empty": False},
            "start": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "end_exclusive": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "granularity": {
                "type": "string",
                "required": True,
                "allowed": GRANULARITIES,
            },
            "timezone": {"type": "string", "required": True, "empty": False},
        },
    },
    # What the collector request actually was, and the reference time it was
    # resolved against (recorded in temporal_provenance / submitted_parameters).
    "collection_request": {
        "type": "dict",
        "required": True,
        "schema": {
            "date_filter": {"type": "string", "required": True, "empty": False},
            "reference_time": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
        },
        "allow_unknown": True,
    },
    # What only the collector can know about its period handling.  Declared,
    # because the driver has no source knowledge and no compiler runs here.
    "temporal": {
        "type": "dict",
        "required": True,
        "schema": {
            "collector_window_type": {
                "type": "string",
                "required": True,
                "allowed": COLLECTOR_WINDOW_TYPES,
            },
            "boundary_semantics": {"type": "string", "required": True},
            "exact_window_match": {"type": "boolean", "required": True},
            "limitations": {
                "type": "list",
                "nullable": True,
                "schema": {"type": "string", "empty": False},
            },
        },
    },
    # Run start / finish and the evidence each timestamp is based on.
    "timestamps": {
        "type": "dict",
        "required": True,
        "schema": {
            "started_at": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "finished_at": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "basis": {"type": "string", "required": True, "empty": False},
        },
    },
    "execution": {
        "type": "dict",
        "required": True,
        "schema": {
            "status": {
                "type": "string",
                "required": True,
                "allowed": EXECUTION_STATUSES,
            },
            "returned_count": {"type": "integer", "nullable": True, "min": 0},
            "errors": {"type": "list", "nullable": True},
            "pagination_exhausted": {"type": "boolean", "nullable": True},
        },
    },
    "artifacts": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {"type": "dict", "schema": _ARTIFACT_SCHEMA},
    },
    # Free-form declared detail, recorded verbatim (extension areas).
    "environment": {"type": "dict", "nullable": True, "allow_unknown": True},
}

STAGING_DECLARATION_SCHEMA = {
    "declaration_version": {
        "type": "string",
        "required": True,
        "allowed": [STAGING_DECLARATION_VERSION],
    },
    "description": {"type": "string", "nullable": True},
    "runs": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {"type": "dict", "schema": _RUN_SCHEMA},
    },
}


class DeclarationError(ValueError):
    """The declaration cannot be used (structural or reference failure).

    ``issues`` carries the structural findings (``validation.reporting.Issue``)
    when the failure is a schema mismatch; reference failures carry a message
    that names the path inside the declaration.
    """

    def __init__(self, message: str, issues=()):
        super().__init__(message)
        self.issues = list(issues)


@dataclass(frozen=True)
class Declaration:
    """One loaded, structurally valid declaration document."""

    path: Path
    name: str
    sha256: str
    document: dict


def load_declaration(path) -> Declaration:
    """Read and structurally validate a ``staging-declaration-v1`` document.

    I/O failures (missing file, undecodable bytes) and JSON syntax errors
    propagate as ``OSError`` / ``UnicodeDecodeError`` / ``json.JSONDecodeError``
    so the CLI can classify them as I/O errors; a well-formed document that
    does not match the declaration schema raises :class:`DeclarationError`.
    """
    target = Path(path)
    data = target.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    document = json.loads(data.decode("utf-8"))
    outcome = validate_document(document, STAGING_DECLARATION_SCHEMA)
    if not outcome.valid:
        issues = normalize_cerberus_errors(outcome.errors)
        raise DeclarationError(
            "the declaration does not match " + STAGING_DECLARATION_VERSION,
            issues,
        )
    return Declaration(path=target, name=target.name, sha256=sha256, document=document)


def _find_query(queries, query_id: str):
    for query in queries:
        if isinstance(query, dict) and query.get("query_id") == query_id:
            return query
    return None


def _reader_for(registries: Registries, declaration_artifact: dict):
    """Resolve the registered reader for a declared artifact, or None.

    The resolution follows the storage contract (schema_id -> reader_id) so a
    derived count is the same number the S8 check will compare against.
    """
    document = registries.artifact_registry
    if not isinstance(document, dict):
        return None
    entry = ArtifactRegistry(document).schema_entry(declaration_artifact["schema_id"])
    if entry is None:
        return None
    reader_id = entry.get("reader_id")
    if not isinstance(reader_id, str):
        return None
    reader = get_reader(reader_id)
    if reader is None:
        return None
    return reader_id, reader


def _prepare_artifacts(run: dict, prefix: str, registries: Registries):
    """Build CollectedArtifact declarations and the record-count basis map."""
    artifacts = []
    basis: dict = {}
    for index, declared in enumerate(run["artifacts"]):
        count = declared.get("record_count")
        if count is None:
            resolved = _reader_for(registries, declared)
            if resolved is None:
                raise DeclarationError(
                    f"{prefix}.artifacts[{index}].record_count: absent and no "
                    "registered reader covers schema_id "
                    f"{declared['schema_id']!r}; register a reader or declare "
                    "the count explicitly (it is verified by L1)"
                )
            reader_id, reader = resolved
            descriptor = ArtifactDescriptor(
                artifact_id="declared-source",
                artifact_type=declared["artifact_type"],
                format=declared["format"],
                schema_id=declared["schema_id"],
                path=str(declared["source"]),
            )
            count = reader.count(descriptor)
            if count is None:
                raise DeclarationError(
                    f"{prefix}.artifacts[{index}].source: record_count cannot "
                    f"be determined with {reader_id!r} (unreadable or malformed "
                    "payload); declare record_count explicitly or fix the file"
                )
            basis[declared["path"]] = f"derived:{reader_id}"
        else:
            basis[declared["path"]] = "declared"
        artifacts.append(
            CollectedArtifact(
                source=declared["source"],
                path=declared["path"],
                artifact_type=declared["artifact_type"],
                format=declared["format"],
                schema_id=declared["schema_id"],
                completeness=declared.get("completeness", "complete"),
                record_count=count,
                media_type=declared.get("media_type"),
            )
        )
    return artifacts, basis


def _prepare_run(run: dict, index: int, registries: Registries, declaration: Declaration) -> dict:
    """Turn one declared run into the exact inputs ``stage_run`` takes.

    Every failure here is a declaration failure (the operator must fix the
    document), not a pipeline refusal; ``stage_run`` still applies its own
    rules afterwards - this function deliberately does not duplicate them.
    """
    prefix = f"runs[{index}]"
    query_id = run["query"]["query_id"]
    query_entry = _find_query(registries.queries, query_id)
    if query_entry is None:
        raise DeclarationError(
            f"{prefix}.query.query_id: {query_id!r} is not registered in the "
            "query registry; register it (G2) or correct the declaration - "
            "the driver never maps a keyword to a query itself"
        )

    query = {
        "text": run["query"]["keyword"],
        "compound_id": query_entry.get("compound_id"),
    }
    if query_entry.get("intent_id"):
        query["intent_id"] = query_entry["intent_id"]
    plan = {
        "study_id": run["study_id"],
        "source_id": run["source_id"],
        "collector_id": run["collector_id"],
        "query_id": query_id,
        "query": query,
        # A staged run makes no request, so it requires no capability (the
        # capability gate constrains requests, not handed-over payloads).
        "required_capabilities": [],
        "window": dict(run["window"]),
        "purpose": run["purpose"],
    }

    artifacts, count_basis = _prepare_artifacts(run, prefix, registries)

    execution = {
        "status": run["execution"]["status"],
        "errors": list(run["execution"].get("errors") or []),
    }
    returned_count = run["execution"].get("returned_count")
    if returned_count is None:
        returned_count = sum(artifact.record_count or 0 for artifact in artifacts)
        returned_basis = "derived:sum(artifacts)"
    else:
        returned_basis = "declared"
    execution["returned_count"] = returned_count
    if run["execution"].get("pagination_exhausted") is not None:
        execution["pagination_exhausted"] = run["execution"]["pagination_exhausted"]

    request = dict(run["collection_request"])
    temporal = dict(run["temporal"])
    if temporal.get("limitations") is None:
        temporal.pop("limitations", None)
    temporal["reference_time"] = request["reference_time"]

    environment = dict(run.get("environment") or {})
    environment["handover"] = {
        "declaration_version": STAGING_DECLARATION_VERSION,
        "declaration_name": declaration.name,
        "declaration_sha256": declaration.sha256,
        "timestamp_basis": run["timestamps"]["basis"],
        "record_counts": count_basis,
        "returned_count": returned_basis,
    }

    return {
        "plan": plan,
        "artifacts": artifacts,
        "execution": execution,
        "started_at": run["timestamps"]["started_at"],
        "finished_at": run["timestamps"]["finished_at"],
        "temporal": temporal,
        "submitted_parameters": request,
        "environment": environment,
        "run_id": run.get("run_id"),
        "query_id": query_id,
        "keyword": run["query"]["keyword"],
    }


def stage_declaration(
    declaration: Declaration,
    *,
    workspace_root,
    datasets_root,
    registries: Registries,
) -> dict:
    """Stage every run a declaration lists; never decides adoption.

    The declaration is prepared in full before anything is written, so a
    declaration-level failure (unregistered query, unreadable payload) is a
    configuration error with nothing staged.  A run that ``stage_run`` itself
    refuses (missing artifact, run-id collision, unregistered collector) is
    reported per run and does not stop the remaining runs - each staged
    directory is an independent, fail-closed unit.
    """
    prepared = [
        _prepare_run(run, index, registries, declaration)
        for index, run in enumerate(declaration.document["runs"])
    ]

    results = []
    for index, entry in enumerate(prepared):
        result = stage_run(
            entry["plan"],
            artifacts=entry["artifacts"],
            execution=entry["execution"],
            started_at=entry["started_at"],
            finished_at=entry["finished_at"],
            workspace_root=workspace_root,
            datasets_root=datasets_root,
            registries=registries,
            temporal=entry["temporal"],
            submitted_parameters=entry["submitted_parameters"],
            environment=entry["environment"],
            run_id=entry["run_id"],
        )
        record = result.to_dict()
        record["declaration_index"] = index
        record["query_id"] = entry["query_id"]
        record["keyword"] = entry["keyword"]
        results.append(record)

    staged = sum(1 for record in results if record["action"] == "staged")
    return {
        "driver": "staging-declaration",
        "driver_version": STAGING_DRIVER_VERSION,
        "declaration_version": declaration.document["declaration_version"],
        "declaration_name": declaration.name,
        "declaration_sha256": declaration.sha256,
        "runs_requested": len(prepared),
        "staged": staged,
        "stopped": len(prepared) - staged,
        "results": results,
    }
