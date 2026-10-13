"""G4 storage contract checks (d.md §10 integrity, §11 pagination, §12
summary/timeseries distinction, §13 SQLite lineage, §15 lineage).

Layers that already cover part of the §10 table:

========  ==========================================================
S2        manifest structure -> ``validation.core`` (artifact-manifest-v1)
S3-S5     existence / byte length / SHA-256 -> ``validation.integrity``
S10       raw immutability -> the run-level overwrite refusal (G1 §13)
          and the audit's hash-before/after evidence; a rewritten raw file
          is *detected* as an S5 hash mismatch
========  ==========================================================

This module adds the content- and contract-level checks:

- S1 ``ARTIFACT_ID_DUPLICATE`` - artifact ids unique within the manifest;
- S6 ``ARTIFACT_FORMAT_MISMATCH`` - declared format vs actual content;
- S7 ``ARTIFACT_SCHEMA_INVALID`` - reader ``validate`` violations;
- S8 ``ARTIFACT_RECORD_COUNT_MISMATCH`` - when the schema's
  ``record_count_mode`` defines comparable semantics (never for summaries);
- S9 ``ARTIFACT_READER_UNREGISTERED`` - schema / format / type without an
  active registered reader;
- S11 ``ARTIFACT_PATH_UNSAFE`` - absolute / parent-traversal / escaping path;
- §11 group checks - ``ARTIFACT_GROUP_COUNT_MISMATCH``,
  ``ARTIFACT_PAGE_INDEX_DUPLICATE``, ``ARTIFACT_PAGE_REFERENCE_MISSING``,
  ``ARTIFACT_PAGE_MISSING`` (partial; error only when a complete claim
  contradicts the evidence), ``ARTIFACT_PAGE_INDEX_UNEXPECTED``,
  ``ARTIFACT_PAGINATION_INCOMPLETE`` (``pagination_exhausted=false`` forbids
  a ``complete`` claim);
- §12 ``ARTIFACT_SUMMARY_TIMESERIES_CONFLICT``;
- §13 ``ARTIFACT_DATABASE_LINEAGE_MISSING`` / ``ARTIFACT_DATABASE_TABLE_MISSING``;
- registry document consistency (``validate-registries``): duplicate ids,
  unknown reader references, active-but-unimplemented readers, format drift.

A missing artifact registry disables only the reader-dependent checks
(S7 / S8 / S9) - the same convention as every other registry in this
repository.  All functions are read-only.
"""

from __future__ import annotations

from pathlib import Path

from storage.contracts import ArtifactDescriptor, ReaderError
from storage.readers import get_reader
from storage.registry import ArtifactRegistry
from storage.sniff import sniff_path
from validation.reporting import Issue

__all__ = [
    "check_artifact_registry",
    "check_manifest_storage_contract",
]

_RULE = "storage_contract"

#: d.md §6.2: record-count semantics that a reader can actually compare.
_COUNTING_MODES = frozenset(
    {"array_length", "items_length", "data_points", "data_rows"}
)


def _issue(code, path, message, severity="error"):
    return Issue(
        code=code, path=path, severity=severity, message=message, rule=_RULE
    )


def _path_unsafe_reason(base: Path, relative: str) -> str | None:
    """d.md §10 S11: manifest paths must stay inside the run directory."""
    if not relative:
        return "empty path"
    candidate = Path(relative)
    if candidate.is_absolute():
        return "absolute paths are not allowed"
    if ".." in candidate.parts:
        return "parent traversal is not allowed"
    try:
        resolved = (base / candidate).resolve()
        base_resolved = base.resolve()
    except OSError:
        return None
    if resolved != base_resolved and base_resolved not in resolved.parents:
        return "path escapes the run directory"
    return None


_FORMAT_NEVER_COMPARED = frozenset({"unknown", "other", None})


def _format_matches(declared, sniffed) -> bool:
    """d.md §10 S6: declared format vs actual content.

    An unidentified / explicitly-open format is never used to accuse a
    file (``other`` means the producer declared "some other format");
    everything else must match the content identification exactly.
    """
    if sniffed in _FORMAT_NEVER_COMPARED:
        return True
    return declared == sniffed


# ---------------------------------------------------------------------------
# registry document consistency (validate-registries)
# ---------------------------------------------------------------------------


def check_artifact_registry(document) -> list[Issue]:
    """Internal consistency of ``artifact-registry-v1`` (d.md §7)."""
    issues: list[Issue] = []
    if not isinstance(document, dict):
        return issues
    readers = document.get("readers")
    schemas = document.get("artifact_schemas")
    readers = readers if isinstance(readers, list) else []
    schemas = schemas if isinstance(schemas, list) else []

    reader_by_id: dict = {}
    seen_readers = set()
    for index, reader in enumerate(readers):
        if not isinstance(reader, dict):
            continue
        reader_id = reader.get("reader_id")
        if isinstance(reader_id, str):
            if reader_id in seen_readers:
                issues.append(
                    _issue(
                        "ARTIFACT_REGISTRY_DUPLICATE_ID",
                        f"/readers/{index}/reader_id",
                        "duplicate reader_id in the artifact registry",
                    )
                )
            seen_readers.add(reader_id)
            reader_by_id.setdefault(reader_id, reader)

    seen_schemas = set()
    for index, schema in enumerate(schemas):
        if not isinstance(schema, dict):
            continue
        schema_id = schema.get("schema_id")
        if isinstance(schema_id, str):
            if schema_id in seen_schemas:
                issues.append(
                    _issue(
                        "ARTIFACT_REGISTRY_DUPLICATE_ID",
                        f"/artifact_schemas/{index}/schema_id",
                        "duplicate schema_id in the artifact registry",
                    )
                )
            seen_schemas.add(schema_id)

    for index, reader in enumerate(readers):
        if not isinstance(reader, dict):
            continue
        reader_id = reader.get("reader_id")
        if reader.get("status") == "active" and isinstance(reader_id, str):
            if get_reader(reader_id) is None:
                issues.append(
                    _issue(
                        "ARTIFACT_REGISTRY_UNIMPLEMENTED",
                        f"/readers/{index}/reader_id",
                        "reader is registered as active but no implementation "
                        "exists in storage.readers",
                    )
                )

    for index, schema in enumerate(schemas):
        if not isinstance(schema, dict):
            continue
        reader_id = schema.get("reader_id")
        reader = reader_by_id.get(reader_id)
        if reader is None:
            issues.append(
                _issue(
                    "ARTIFACT_REGISTRY_UNKNOWN_READER",
                    f"/artifact_schemas/{index}/reader_id",
                    "schema entry references a reader_id that is not registered",
                )
            )
            continue
        if reader.get("status") == "planned":
            issues.append(
                _issue(
                    "ARTIFACT_REGISTRY_PLANNED_REFERENCE",
                    f"/artifact_schemas/{index}/reader_id",
                    "schema entry references a planned reader; the format is "
                    "declared but not yet readable",
                    severity="warning",
                )
            )
        formats = reader.get("formats") or ()
        if schema.get("format") not in formats:
            issues.append(
                _issue(
                    "ARTIFACT_REGISTRY_FORMAT_MISMATCH",
                    f"/artifact_schemas/{index}/format",
                    "the referenced reader does not cover this format",
                )
            )

    return issues


# ---------------------------------------------------------------------------
# manifest contract checks
# ---------------------------------------------------------------------------


def _check_reader_registration(registry, artifact, index, issues):
    """S9 / S7 / S8: resolve and use the registered reader for one artifact."""
    schema_id = artifact.get("schema_id")
    format_value = artifact.get("format")
    artifact_type = artifact.get("artifact_type")

    entry = registry.schema_entry(schema_id)
    if entry is None:
        issues.append(
            _issue(
                "ARTIFACT_READER_UNREGISTERED",
                f"/artifacts/{index}/schema_id",
                "no artifact schema is registered for this schema_id "
                "(register a reader first - d.md §7)",
            )
        )
        return None, None
    if entry.get("format") != format_value or artifact_type not in (
        entry.get("artifact_types") or ()
    ):
        issues.append(
            _issue(
                "ARTIFACT_READER_UNREGISTERED",
                f"/artifacts/{index}/format",
                "the registered schema does not cover this (format, "
                "artifact_type) combination",
            )
        )
        return None, None

    reader_id = entry.get("reader_id")
    reader_entry = registry.reader_entry(reader_id)
    if reader_entry is None or reader_entry.get("status") != "active":
        issues.append(
            _issue(
                "ARTIFACT_READER_UNREGISTERED",
                f"/artifacts/{index}/schema_id",
                "the schema's reader is not registered as active",
            )
        )
        return None, None
    reader = get_reader(reader_id)
    if reader is None:
        issues.append(
            _issue(
                "ARTIFACT_READER_UNREGISTERED",
                f"/artifacts/{index}/schema_id",
                "the schema's reader is not implemented in storage.readers",
            )
        )
        return None, None
    return entry, reader


def _check_artifact_contents(artifact, index, base: Path, registry, issues) -> None:
    """S6 / S7 / S8 for one artifact (only when the file exists)."""
    relative = artifact.get("path")
    target = base / relative
    sniff = sniff_path(target)
    if not _format_matches(artifact.get("format"), sniff.format):
        issues.append(
            _issue(
                "ARTIFACT_FORMAT_MISMATCH",
                f"/artifacts/{index}/format",
                "declared format does not match the content on disk",
            )
        )
    if registry is None:
        return
    entry, reader = _check_reader_registration(registry, artifact, index, issues)
    if reader is None:
        return
    descriptor = ArtifactDescriptor.from_manifest_artifact(artifact, base)
    violations = reader.validate(descriptor)
    if violations:
        issues.append(
            _issue(
                "ARTIFACT_SCHEMA_INVALID",
                f"/artifacts/{index}/path",
                f"artifact does not satisfy its schema: {violations[0]}",
            )
        )
    mode = entry.get("record_count_mode")
    declared_count = artifact.get("record_count")
    if mode in _COUNTING_MODES and isinstance(declared_count, int):
        determined = reader.count(descriptor)
        if determined is not None and determined != declared_count:
            issues.append(
                _issue(
                    "ARTIFACT_RECORD_COUNT_MISMATCH",
                    f"/artifacts/{index}/record_count",
                    "record_count does not match the count the reader can "
                    "determine",
                )
            )


def _check_database_artifact(artifact, index, base: Path, issues) -> None:
    """d.md §13: a database artifact must carry its tables and lineage."""
    block = artifact.get("database")
    prefix = f"/artifacts/{index}/database"
    if not isinstance(block, dict):
        issues.append(
            _issue(
                "ARTIFACT_DATABASE_LINEAGE_MISSING",
                prefix,
                "a database artifact must record its schema version, tables "
                "and source run/artifact references (d.md §13)",
            )
        )
        return
    problems: list[tuple[str, str]] = []
    if not isinstance(block.get("db_schema_version"), str) or not block.get(
        "db_schema_version"
    ):
        problems.append((f"{prefix}/db_schema_version", "db_schema_version is required"))
    tables = block.get("tables")
    if not isinstance(tables, list) or not tables:
        problems.append((f"{prefix}/tables", "at least one table must be declared"))
        tables = []
    for table_index, table in enumerate(tables):
        table_prefix = f"{prefix}/tables/{table_index}"
        if not isinstance(table, dict):
            problems.append((table_prefix, "table entry must be a mapping"))
            continue
        if not isinstance(table.get("table_name"), str) or not table.get("table_name"):
            problems.append((f"{table_prefix}/table_name", "table_name is required"))
        for field in ("source_run_ids", "source_artifact_ids"):
            value = table.get(field)
            if not isinstance(value, list) or not value:
                problems.append(
                    (
                        f"{table_prefix}/{field}",
                        f"{field} must list the sources merged into this table "
                        "(provenance is never assumed)",
                    )
                )
        for field in ("deduplication_rule", "transformation_version"):
            if not isinstance(table.get(field), str) or not table.get(field):
                problems.append((f"{table_prefix}/{field}", f"{field} is required"))
    for path, message in problems:
        issues.append(_issue("ARTIFACT_DATABASE_LINEAGE_MISSING", path, message))

    # Declared tables must exist in the physical database (when readable).
    relative = artifact.get("path")
    if artifact.get("format") == "sqlite" and isinstance(relative, str):
        target = base / relative
        if target.is_file():
            reader = get_reader("sqlite-reader")
            if reader is not None:
                try:
                    actual = set(
                        reader.tables(
                            ArtifactDescriptor.from_manifest_artifact(artifact, base)
                        )
                    )
                except ReaderError:
                    actual = None
                if actual is not None:
                    for table_index, table in enumerate(tables):
                        if isinstance(table, dict):
                            name = table.get("table_name")
                            if isinstance(name, str) and name and name not in actual:
                                issues.append(
                                    _issue(
                                        "ARTIFACT_DATABASE_TABLE_MISSING",
                                        f"{prefix}/tables/{table_index}/table_name",
                                        "declared table is not present in the "
                                        "database (read-only check)",
                                    )
                                )


def _check_groups(manifest, issues) -> None:
    """d.md §11: pagination group consistency (page gaps are partial)."""
    groups = manifest.get("artifact_groups")
    if not isinstance(groups, list):
        return
    artifacts = {
        artifact.get("artifact_id"): artifact
        for artifact in manifest.get("artifacts", []) or []
        if isinstance(artifact, dict) and isinstance(artifact.get("artifact_id"), str)
    }
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        prefix = f"/artifact_groups/{group_index}"
        members = group.get("artifacts")
        members = members if isinstance(members, list) else []
        collected = group.get("collected_pages")
        expected = group.get("expected_pages")
        exhausted = group.get("pagination_exhausted")

        if collected != len(members):
            issues.append(
                _issue(
                    "ARTIFACT_GROUP_COUNT_MISMATCH",
                    f"{prefix}/collected_pages",
                    "collected_pages does not match the group's page artifacts",
                )
            )
        indexes: list[int] = []
        for member_index, member in enumerate(members):
            if not isinstance(member, dict):
                continue
            artifact_id = member.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id not in artifacts:
                issues.append(
                    _issue(
                        "ARTIFACT_PAGE_REFERENCE_MISSING",
                        f"{prefix}/artifacts/{member_index}/artifact_id",
                        "group references an artifact_id that the manifest does "
                        "not declare",
                    )
                )
            page_index = member.get("page_index")
            if isinstance(page_index, int):
                indexes.append(page_index)
            artifact = artifacts.get(artifact_id)
            if isinstance(artifact, dict):
                declared_group = artifact.get("artifact_group_id")
                if (
                    isinstance(declared_group, str)
                    and declared_group != group.get("artifact_group_id")
                ):
                    issues.append(
                        _issue(
                            "ARTIFACT_GROUP_ID_MISMATCH",
                            f"{prefix}/artifacts/{member_index}/artifact_id",
                            "page artifact belongs to a different artifact_group_id",
                            severity="warning",
                        )
                    )
        seen: set[int] = set()
        for value in indexes:
            if value in seen:
                issues.append(
                    _issue(
                        "ARTIFACT_PAGE_INDEX_DUPLICATE",
                        f"{prefix}/artifacts",
                        "page_index values must be unique within a group",
                    )
                )
                break
            seen.add(value)

        if isinstance(expected, int):
            missing = sorted(set(range(1, expected + 1)) - seen)
            extra = sorted(value for value in seen if value > expected)
            if extra:
                issues.append(
                    _issue(
                        "ARTIFACT_PAGE_INDEX_UNEXPECTED",
                        f"{prefix}/artifacts",
                        "page_index exceeds expected_pages",
                    )
                )
            if missing:
                # A gap with pagination_exhausted=false is a consistent
                # partial collection (warning); claiming exhaustion while
                # pages are missing is a contradiction (error).
                issues.append(
                    _issue(
                        "ARTIFACT_PAGE_MISSING",
                        f"{prefix}/expected_pages",
                        f"{len(missing)} expected page(s) are missing; a missing "
                        "page is not observed zero",
                        severity="error" if exhausted is True else "warning",
                    )
                )
        if exhausted is False and group.get("completeness") == "complete":
            issues.append(
                _issue(
                    "ARTIFACT_PAGINATION_INCOMPLETE",
                    f"{prefix}/completeness",
                    "pagination_exhausted is false; a group must not claim "
                    "complete (d.md §11)",
                )
            )


def check_manifest_storage_contract(
    manifest, *, base_dir, artifact_registry=None
) -> list[Issue]:
    """Run the G4 storage contract checks for one manifest (read-only).

    ``artifact_registry`` may be an ``ArtifactRegistry`` instance or the raw
    registry document (the ``Registries`` carrier keeps documents); None
    disables the reader-dependent checks.
    """
    issues: list[Issue] = []
    if not isinstance(manifest, dict):
        return issues
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return issues
    if isinstance(artifact_registry, dict):
        artifact_registry = ArtifactRegistry(artifact_registry)
    base = Path(base_dir)

    # S1: artifact id uniqueness.
    seen_ids = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str):
            if artifact_id in seen_ids:
                issues.append(
                    _issue(
                        "ARTIFACT_ID_DUPLICATE",
                        f"/artifacts/{index}/artifact_id",
                        "artifact_id must be unique within a manifest",
                    )
                )
            seen_ids.add(artifact_id)

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        relative = artifact.get("path")
        safe_target_exists = False
        if isinstance(relative, str) and relative:
            reason = _path_unsafe_reason(base, relative)
            if reason:
                issues.append(
                    _issue(
                        "ARTIFACT_PATH_UNSAFE",
                        f"/artifacts/{index}/path",
                        f"artifact path is not safe: {reason}",
                    )
                )
            else:
                safe_target_exists = (base / relative).is_file()

        if safe_target_exists:
            _check_artifact_contents(artifact, index, base, artifact_registry, issues)

        # §12: a summary must not claim to contain the full timeseries.
        if (
            artifact.get("artifact_type") == "summary"
            and artifact.get("contains_full_timeseries") is True
        ):
            issues.append(
                _issue(
                    "ARTIFACT_SUMMARY_TIMESERIES_CONFLICT",
                    f"/artifacts/{index}/contains_full_timeseries",
                    "a summary artifact must not claim contains_full_timeseries "
                    "(d.md §12 / P8)",
                )
            )
        if artifact_registry is not None:
            entry = artifact_registry.schema_entry(artifact.get("schema_id"))
            if (
                isinstance(entry, dict)
                and artifact.get("contains_full_timeseries") is True
                and entry.get("contains_full_timeseries") is False
            ):
                issues.append(
                    _issue(
                        "ARTIFACT_SUMMARY_TIMESERIES_CONFLICT",
                        f"/artifacts/{index}/contains_full_timeseries",
                        "the registered schema does not contain a full "
                        "timeseries (d.md §12)",
                    )
                )

        if artifact.get("artifact_type") == "database":
            _check_database_artifact(artifact, index, base, issues)

    _check_groups(manifest, issues)
    issues.sort(key=lambda issue: issue.sort_key())
    return issues
