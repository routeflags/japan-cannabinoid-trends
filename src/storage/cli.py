"""storage CLI (G4): read / inspect / catalog - read-only surfaces.

Usage (repository root; ``python -m storage.cli``):

- ``read --path P [--schema-id S] [--mode M] [--limit N] [--table T]``
  reads one artifact through its registered reader and prints the normalized
  records.  A mode the reader does not implement is *refused* (exit 1): a
  summary is never returned as a full timeseries (d.md §12 / P8).
- ``inspect --path P`` prints the content identification (sniff) plus the
  registry resolution for one file.
- ``catalog --datasets-root datasets [--output F] [--check-lineage]`` builds
  the manifest-derived catalog (d.md §14) and optionally verifies lineage
  references across manifests (d.md §15).
- ``catalog --study-dir datasets/<study-id> --persist [--check-lineage]``
  persists one study's catalog to its canonical derived location
  ``datasets/<study-id>/metadata/data-catalog.json`` (d.md §17.1).  With
  ``--check-lineage``, dangling references refuse (exit 1) *before* any
  write, so a failed persist never creates or modifies the canonical file.
  A study with no manifests persists the stable empty catalog
  (``count: 0``); ``--persist`` requires ``--study-dir`` and cannot be
  combined with ``--output``.
- ``verify-trends-db [--db P]`` checks a local ``trends.db`` copy read-only
  (expected tables / views / row counts / lineage-table presence).  The
  database is Git-ignored and never required: an absent database is a
  graceful ``EXIT_IO`` with a pointer to the local procedure, not a
  traceback.  ``record_lineage`` absence is reported as deferred (ART-007),
  never a failure.

Exit codes: 0 = ok / read served; 1 = refused (unsupported mode, unknown
reader, dangling lineage); 2 = configuration error (registry unreadable);
3 = I/O or malformed content.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from storage.catalog import (
    build_catalog,
    build_study_catalog,
    catalog_path_for_study,
    dump_catalog,
    write_catalog,
)
from storage.contracts import ArtifactDescriptor, ReaderError, UnsupportedRead
from storage.lineage import check_catalog_lineage
from storage.registry import ArtifactRegistry
from storage.sniff import sniff_path
from storage.readers import get_reader

__all__ = ["main"]

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_CONFIG = 2
EXIT_IO = 3

#: Expected store shape for ``datasets/youtube-consistency`` (see
#: ``schema/schema.sql``).  ``record_lineage`` is intentionally *not* listed:
#: its introduction is deferred (ART-007), so its absence is reported, never
#: a failure.
TRENDS_DB_EXPECTED_TABLES = ("run_videos", "runs", "videos")
TRENDS_DB_EXPECTED_VIEWS = ("v_run_summary", "v_video_appearance")
TRENDS_DB_DEFAULT_PATH = "datasets/youtube-consistency/data/trends.db"


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _load_registry(metadata_dir) -> ArtifactRegistry | None:
    """Load the artifact registry; malformed file raises ConfigError."""
    try:
        return ArtifactRegistry.load(
            Path(metadata_dir) / "artifacts" / "artifact-registry.json"
        )
    except ValueError as error:
        raise ConfigError(str(error)) from error


class ConfigError(Exception):
    """Schema / configuration problem (exit code 2)."""


def _resolve_reader(registry, sniff, schema_id):
    """Resolve the reader for a sniffed artifact, or None (fail closed).

    A known ``schema_id`` must resolve through its own registry entry - it is
    never bypassed by the type-only fallback; that fallback applies only when
    no schema is known at all and the (format, artifact_type) pair resolves
    uniquely (P3 - never a guess).
    """
    if registry is None:
        return None
    if schema_id:
        return registry.reader_for(
            schema_id=schema_id, artifact_type=sniff.artifact_type, format=sniff.format
        )
    return registry.reader_for(artifact_type=sniff.artifact_type, format=sniff.format)


def cmd_read(args) -> int:
    path = Path(args.path)
    if not path.is_file():
        _err(f"cannot read artifact: {path}")
        return EXIT_IO
    try:
        registry = _load_registry(args.metadata_dir)
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    sniff = sniff_path(path)
    schema_id = args.schema_id or sniff.schema_id
    if sniff.format == "unknown":
        _err(f"artifact format cannot be identified: {path}")
        return EXIT_REFUSED
    if registry is None:
        _err(
            "artifact registry not found (metadata/artifacts/artifact-registry.json "
            f"under {args.metadata_dir!r}); reader resolution requires the registry"
        )
        return EXIT_CONFIG
    reader_id = _resolve_reader(registry, sniff, schema_id)
    if reader_id is None:
        _err(
            "no registered reader for this artifact "
            f"(schema_id={schema_id!r}, artifact_type={sniff.artifact_type!r}, "
            f"format={sniff.format!r}); register a reader first (d.md §7)"
        )
        return EXIT_REFUSED
    reader = get_reader(reader_id)
    if reader is None:
        _err(f"reader is registered but not implemented: {reader_id}")
        return EXIT_CONFIG
    mode = args.mode or (reader.read_modes[0] if reader.read_modes else None)
    descriptor = ArtifactDescriptor(
        artifact_id="cli-read",
        artifact_type=sniff.artifact_type,
        format=sniff.format,
        schema_id=schema_id,
        path=str(path),
    )
    try:
        read_kwargs = {"mode": mode, "limit": args.limit}
        if args.table is not None:
            read_kwargs["table"] = args.table
        records = list(reader.read(descriptor, **read_kwargs))
    except UnsupportedRead as error:
        _err(str(error))
        return EXIT_REFUSED
    except (ReaderError, TypeError) as error:
        _err(f"read failed: {error}")
        return EXIT_IO
    document = {
        "reader_id": reader.reader_id,
        "reader_version": reader.reader_version,
        "mode": mode,
        "path": str(path),
        "schema_id": schema_id,
        "artifact_type": sniff.artifact_type,
        "contains_full_timeseries": reader.contains_full_timeseries,
        "limit": args.limit,
        "count": len(records),
        "records": records,
    }
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return EXIT_OK


def cmd_inspect(args) -> int:
    path = Path(args.path)
    if not path.is_file():
        _err(f"cannot read artifact: {path}")
        return EXIT_IO
    try:
        registry = _load_registry(args.metadata_dir)
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    sniff = sniff_path(path)
    reader_id = _resolve_reader(registry, sniff, sniff.schema_id)
    if reader_id is not None:
        registered = bool(
            registry.reader_is_active(reader_id)
            and registry.reader_is_implemented(reader_id)
        )
    elif registry is not None and (sniff.schema_id or sniff.artifact_type):
        registered = False
    else:
        registered = None
    document = {
        "path": str(path),
        "format": sniff.format if sniff.format != "unknown" else None,
        "sniff_state": sniff.state,
        "artifact_type": sniff.artifact_type,
        "schema_id": sniff.schema_id,
        "contains_full_timeseries": sniff.contains_full_timeseries,
        "record_count": sniff.record_count,
        "declared_data_points": sniff.declared_data_points,
        "evidence": list(sniff.evidence),
        "reader_id": reader_id,
        "reader_registered": registered,
    }
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return EXIT_OK


def _report_lineage_problems(problems: list[dict]) -> None:
    for problem in problems:
        _err(f"[{problem['code']}] {problem['path']}: {problem['message']}")
    _err(f"lineage: {len(problems)} dangling reference(s)")


def cmd_catalog(args) -> int:
    try:
        _load_registry(args.metadata_dir)
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    persist = bool(getattr(args, "persist", False))
    study_dir = getattr(args, "study_dir", None)
    if persist and not study_dir:
        _err("catalog --persist requires --study-dir <study-dir>")
        return EXIT_CONFIG
    if persist and args.output:
        _err(
            "catalog --persist writes only to "
            "<study-dir>/metadata/data-catalog.json; "
            "--output cannot be combined with --persist"
        )
        return EXIT_CONFIG
    if persist:
        study = Path(study_dir)
        if not study.is_dir():
            _err(f"study directory not found: {study_dir}")
            return EXIT_CONFIG
        catalog = build_study_catalog(study)
        problems = check_catalog_lineage(catalog) if args.check_lineage else []
        if problems:
            # Fail before any write: a refused persist neither creates nor
            # modifies the canonical file (a previous good version, if any,
            # keeps its bytes; no temp file remains).
            _report_lineage_problems(problems)
            return EXIT_REFUSED
        target = catalog_path_for_study(study)
        try:
            write_catalog(catalog, target)
        except OSError as error:
            _err(f"cannot write catalog: {target} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"catalog persisted: {target} ({catalog['count']} entries)")
        if args.check_lineage:
            _err("lineage: all derived_from references resolve")
        return EXIT_OK
    root = Path(study_dir) / "data" if study_dir else Path(args.datasets_root)
    catalog = build_catalog(root)
    problems = check_catalog_lineage(catalog) if args.check_lineage else []
    if args.output:
        try:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(dump_catalog(catalog), encoding="utf-8")
        except OSError as error:
            _err(f"cannot write catalog: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"catalog written: {args.output} ({catalog['count']} entries)")
    else:
        print(dump_catalog(catalog), end="")
    if problems:
        _report_lineage_problems(problems)
        return EXIT_REFUSED
    if args.check_lineage:
        _err("lineage: all derived_from references resolve")
    return EXIT_OK


def _sqlite_views_ro(path: Path) -> list[str]:
    """Read-only view enumeration (same ``mode=ro`` discipline as the reader)."""
    import sqlite3

    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()


def cmd_verify_trends_db(args) -> int:
    """Verify a local ``trends.db`` copy without changing it (ART-007)."""
    from storage.contracts import ArtifactDescriptor

    path = Path(args.db)
    if not path.is_file():
        _err(
            f"database not found: {path} (local-only store; it is Git-ignored "
            "and never committed - see datasets/youtube-consistency/README.md "
            "for the local procedure)"
        )
        return EXIT_IO
    reader = get_reader("sqlite-reader")
    if reader is None:  # pragma: no cover - registry/reader wiring guard
        _err("sqlite-reader is not implemented")
        return EXIT_CONFIG
    descriptor = ArtifactDescriptor(
        artifact_id="cli-verify-trends-db",
        artifact_type="database",
        format="sqlite",
        schema_id="sqlite-trends-db-v1",
        path=str(path),
    )
    violations = reader.validate(descriptor)
    if violations:
        _err(f"database cannot be verified: {violations[0]}: {path}")
        return EXIT_IO
    try:
        tables = reader.tables(descriptor)
        views = _sqlite_views_ro(path)
    except Exception as error:  # read-only probe failed; report, never raise
        _err(f"database cannot be inspected ({error.__class__.__name__}): {path}")
        return EXIT_IO
    row_counts = {table: reader.table_row_count(descriptor, table) for table in tables}
    lineage = reader.lineage_summary(descriptor)
    missing_tables = [t for t in TRENDS_DB_EXPECTED_TABLES if t not in tables]
    missing_views = [v for v in TRENDS_DB_EXPECTED_VIEWS if v not in views]
    problems = [
        *(f"table is not present in the database: {name}" for name in missing_tables),
        *(f"view is not present in the database: {name}" for name in missing_views),
    ]
    document = {
        "db": str(path),
        "read_only": True,
        "tables": {
            "expected": list(TRENDS_DB_EXPECTED_TABLES),
            "present": sorted(tables),
            "missing": missing_tables,
            "row_counts": row_counts,
        },
        "views": {
            "expected": list(TRENDS_DB_EXPECTED_VIEWS),
            "present": sorted(views),
            "missing": missing_views,
        },
        "lineage": {
            "table": lineage["lineage_table"],
            "present": lineage["lineage_table_present"],
            "row_count": lineage.get("lineage_row_count"),
            # Deferred by decision (ART-007): absence is information, not a
            # failure.  See datasets/youtube-consistency/README.md.
            "status": "present" if lineage["lineage_table_present"] else "deferred_absent",
        },
        "ok": not problems,
        "problems": problems,
    }
    print(json.dumps(document, ensure_ascii=False, indent=2))
    if problems:
        for problem in problems:
            _err(problem)
        return EXIT_REFUSED
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m storage.cli",
        description="G4 storage contract CLI (readers / sniff / catalog)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    read = sub.add_parser("read", help="read one artifact through its reader")
    read.add_argument("--path", required=True)
    read.add_argument("--schema-id", help="force a registered schema id")
    read.add_argument("--mode", help="reader mode (defaults to the first)")
    read.add_argument("--limit", type=int, default=10)
    read.add_argument("--table", help="table name for database readers")
    read.add_argument("--metadata-dir", default="metadata")
    read.set_defaults(handler=cmd_read)

    inspect = sub.add_parser("inspect", help="identify one stored artifact")
    inspect.add_argument("--path", required=True)
    inspect.add_argument("--metadata-dir", default="metadata")
    inspect.set_defaults(handler=cmd_inspect)

    catalog = sub.add_parser("catalog", help="build the manifest-derived catalog")
    catalog.add_argument("--datasets-root", default="datasets")
    catalog.add_argument(
        "--study-dir",
        default=None,
        help="scope the catalog to one study (<study-dir>/data); "
        "required with --persist",
    )
    catalog.add_argument("--output", help="write the catalog JSON to this path")
    catalog.add_argument(
        "--persist",
        action="store_true",
        help="persist to <study-dir>/metadata/data-catalog.json "
        "(requires --study-dir; incompatible with --output)",
    )
    catalog.add_argument(
        "--check-lineage",
        action="store_true",
        help="verify derived_from references across manifests",
    )
    catalog.add_argument("--metadata-dir", default="metadata")
    catalog.set_defaults(handler=cmd_catalog)

    verify = sub.add_parser(
        "verify-trends-db", help="read-only check of a local trends.db copy"
    )
    verify.add_argument("--db", default=TRENDS_DB_DEFAULT_PATH)
    verify.set_defaults(handler=cmd_verify_trends_db)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
