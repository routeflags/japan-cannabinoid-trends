"""Validation CLI (Phase 5, h.md §13 / §14).

Commands
--------
- ``validate``            one file against one registered schema
- ``validate-study``      every ``run_metadata.json`` under a study
- ``validate-registries`` every known registry file that exists
- ``validate-all``        registries + all studies (JSON report for CI)
- ``gate-plan``           pre-collection gate for a collection plan (P6-1)
- ``gate-run``            post-collection L1 gate: catalog vs quarantine (P6-2)
- ``compare-runs``        L2 run-level comparability (G1 §12, C1-C3; G3 T6/T7
                          with ``--coverage-a`` / ``--coverage-b``)
- ``coverage-run``        G3 §9 coverage manifest for one run (report only)
- ``audit-temporal``      non-destructive G3 §15 temporal inventory
- ``classify-query``      Stage-1 query-string classification (G2 §8)
- ``compare-queries``     definition-level query comparability (G2 §9)
- ``audit-queries``       non-destructive G2 query inventory (b.md §13)
- ``audit-legacy``        non-destructive G5 legacy audit (Phase 8)

Exit codes (h.md §13)
---------------------
==========  =============================================
 code        meaning
==========  =============================================
0           validation passed
1           data validation failure
2           schema / configuration error (unknown schema, malformed
            registry, legacy profile not allowed for this run)
3           file I/O error (target unreadable, artifact/manifest missing)
==========  =============================================

Precedence when several classes occur in one invocation: 2 > 3 > 1 > 0.
The CLI itself never modifies files except the ``--output`` report path.

Streams: machine-readable JSON goes to stdout (or ``--output``); human-
readable lines go to stderr (h.md §13 "エラー内容は標準エラー出力またはJSON
レポートへ出力する").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validation.comparability import compare_runs
from validation.coverage import build_temporal_inventory, evaluate_coverage
from validation.gates import post_collection_gate, pre_collection_gate
from validation.integrity import IO_ISSUE_CODES, sha256_file
from validation.legacy import LegacyProfileNotAllowed, audit_record
from validation.pipeline import validate_full
from validation.query_semantics import (
    build_query_inventory,
    check_query_registry,
    check_query_variants,
    classify_query_text,
    compare_query_definitions,
    load_compound_vocabulary,
)
from validation.reporting import (
    VALIDATION_VERSION,
    Issue,
    Report,
    ReportBundle,
    dump_json,
)
from validation.schema_registry import get_schema
from validation.semantic import Registries, check_temporal_semantics
from validation.windows import (
    check_window_registry_files,
    load_window_documents,
)

__all__ = ["main"]

EXIT_OK = 0
EXIT_DATA = 1
EXIT_CONFIG = 2
EXIT_IO = 3

#: Precedence used when one invocation produces several failure classes
#: (documented in the module docstring): 2 > 3 > 1 > 0.
_EXIT_PRECEDENCE = {
    EXIT_OK: 0,
    EXIT_DATA: 1,
    EXIT_IO: 2,
    EXIT_CONFIG: 3,
}

#: registry file -> schema ID (P5-3; missing files are skipped with a note)
REGISTRY_FILES = (
    ("sources.json", "source-registry-v1"),
    ("collectors.json", "collector-registry-v1"),
    ("storage-policies.json", "storage-policy-registry-v1"),
)

METADATA_REGISTRY_FILES = (
    ("queries/query-registry.json", "query-registry-v1"),
    ("queries/query-variants.json", "query-variants-registry-v1"),
    ("studies/study-registry.json", "study-registry-v1"),
    ("measurements/measurement-registry.json", "measurement-registry-v1"),
)


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _load_json(path: Path):
    """Load JSON or raise OSError/JSONDecodeError (callers map to exit 3)."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path: Path):
    """Load an existing registry file; missing -> None, malformed -> error."""
    if not path.is_file():
        return None
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(f"registry file cannot be read as JSON: {path}") from error


class ConfigError(Exception):
    """Schema / configuration problem (exit code 2)."""


def _load_query_vocabulary(metadata_dir: Path):
    """Load the compound taxonomy for query semantic checks (G2).

    Returns ``None`` when the taxonomy file is absent (the same convention as
    a missing registry: the corresponding cross-checks are disabled instead
    of producing false failures).  An unreadable taxonomy is a configuration
    error.
    """
    path = Path(metadata_dir) / "taxonomy" / "compound-taxonomy.skos.jsonld"
    if not path.is_file():
        return None
    try:
        return load_compound_vocabulary(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(
            f"compound taxonomy cannot be read as JSON-LD: {path}"
        ) from error


def load_registries(config_dir: Path, metadata_dir: Path) -> Registries:
    """Build the reference-check registries from present files only.

    Returns an empty ``Registries`` while a registry file does not exist yet;
    reference checks are then skipped instead of failing.  The query variants
    bundle and the query-registry version ride along with the query registry
    (G2 vertical slice); the G3 window documents ride along the same way.
    """
    try:
        window_documents = load_window_documents(Path(metadata_dir) / "windows")
    except ValueError as error:
        raise ConfigError(str(error)) from error
    return Registries.from_documents(
        source_registry=_load_optional_json(config_dir / "sources.json"),
        collector_registry=_load_optional_json(config_dir / "collectors.json"),
        query_registry=_load_optional_json(
            metadata_dir / "queries" / "query-registry.json"
        ),
        query_variants_registry=_load_optional_json(
            metadata_dir / "queries" / "query-variants.json"
        ),
        study_registry=_load_optional_json(
            metadata_dir / "studies" / "study-registry.json"
        ),
        window_documents=window_documents,
    )


def _exit_code(issues) -> int:
    if any(issue.code in IO_ISSUE_CODES for issue in issues):
        return EXIT_IO
    if any(issue.severity == "error" for issue in issues):
        return EXIT_DATA
    return EXIT_OK


def _exit_code_for_reports(reports) -> int:
    all_issues = [issue for report in reports for issue in report.issues]
    return _exit_code(all_issues)


def _human_lines(report: Report) -> list[str]:
    verdict = "OK" if report.valid else "FAIL"
    lines = [f"{verdict} {report.profile} {report.schema_id} {report.target}"]
    if report.legacy is not None:
        lines.append(
            f"  legacy_audit run_id={report.legacy.get('run_id')} "
            f"status={report.legacy.get('status')} "
            f"missing_fields={len(report.legacy.get('missing_fields', ()))}"
        )
    for issue in report.issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    summary = {}
    for issue in report.issues:
        summary[issue.severity] = summary.get(issue.severity, 0) + 1
    if summary:
        lines.append(
            "  issues: "
            + ", ".join(f"{key}={summary[key]}" for key in sorted(summary))
        )
    return lines


def _emit(
    document: dict,
    *,
    fmt: str,
    output: str | None,
    human_lines: list[str],
    human_stream=None,
) -> None:
    """Emit the report: JSON to stdout / --output, human lines to stderr.

    ``human_stream`` is resolved at call time (tests replace ``sys.stderr``).
    """
    if fmt == "json":
        text = dump_json(document)
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    stream = human_stream if human_stream is not None else sys.stderr
    for line in human_lines:
        print(line, file=stream)


def _write_output(output: str, document: dict) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(document), encoding="utf-8")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def cmd_validate(args) -> int:
    try:
        get_schema(args.schema)  # unknown schema -> config error before reading
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        _err(f"cannot read input file: {target} ({error.__class__.__name__})")
        return EXIT_IO

    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    try:
        outcome = validate_full(
            document,
            schema_id=args.schema,
            target=str(target),
            profile=args.profile,
            registries=registries if registries.any() else None,
            base_dir=target.parent,
            verify_artifacts=args.verify_artifacts,
        )
    except LegacyProfileNotAllowed as error:
        _err(str(error))
        return EXIT_CONFIG
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    report = outcome.to_report()
    code = _exit_code(outcome.issues)
    _emit(
        report.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_human_lines(report),
    )
    return code


# ---------------------------------------------------------------------------
# validate-study / validate-all
# ---------------------------------------------------------------------------


def _study_dirs(datasets_root: Path):
    if not datasets_root.is_dir():
        return []
    return sorted(
        path
        for path in datasets_root.iterdir()
        if path.is_dir()
    )


def _study_run_files(study_dir: Path):
    return sorted(study_dir.rglob("run_metadata.json"))


def _validate_study(study_id: str, args) -> tuple[ReportBundle, int]:
    datasets_root = Path(args.datasets_root)
    study_dir = datasets_root / study_id
    if not study_dir.is_dir():
        return (
            ReportBundle(
                profile=args.profile,
                note=f"no study directory found: {study_dir}",
            ),
            EXIT_OK,
        )

    files = _study_run_files(study_dir)
    if not files:
        return (
            ReportBundle(
                profile=args.profile,
                note=f"no run_metadata.json found under {study_dir}",
            ),
            EXIT_OK,
        )

    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return ReportBundle(profile=args.profile), EXIT_CONFIG

    bundle = ReportBundle(profile=args.profile)
    for path in files:
        try:
            document = _load_json(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            bundle.reports.append(
                Report(
                    schema_id=args.schema,
                    target=str(path),
                    valid=False,
                    issues=[
                        _io_issue("TARGET_FILE_UNREADABLE", str(path))
                    ],
                )
            )
            continue
        try:
            outcome = validate_full(
                document,
                schema_id=args.schema,
                target=str(path),
                profile=args.profile,
                registries=registries if registries.any() else None,
                base_dir=path.parent,
                verify_artifacts=True,
            )
        except LegacyProfileNotAllowed as error:
            _err(f"{path}: {error}")
            return bundle, EXIT_CONFIG
        bundle.reports.append(outcome.to_report())

    return bundle, _exit_code_for_reports(bundle.reports)


def _io_issue(code: str, target: str):
    return Issue(
        code=code,
        path="",
        severity="error",
        message=f"file cannot be read: {target}",
        rule="io",
    )


def cmd_validate_study(args) -> int:
    bundle, code = _validate_study(args.study, args)
    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return code


def _bundle_lines(bundle: ReportBundle) -> list[str]:
    lines: list[str] = []
    if bundle.note:
        lines.append(f"NOTE {bundle.note}")
    for report in bundle.reports:
        lines.extend(_human_lines(report))
    lines.append(
        f"summary: {len(bundle.reports)} target(s), "
        f"{'valid' if bundle.valid else 'invalid'}"
    )
    return lines


def cmd_validate_all(args) -> int:
    bundle = ReportBundle(profile=args.profile)
    codes: list[int] = []

    registry_reports, registry_code = _validate_registries(args)
    for report in registry_reports.reports:
        bundle.reports.append(report)
    codes.append(registry_code)

    datasets_root = Path(args.datasets_root)
    if datasets_root.is_dir():
        for study_dir in _study_dirs(datasets_root):
            study_bundle, code = _validate_study(study_dir.name, args)
            bundle.reports.extend(study_bundle.reports)
            codes.append(code)

    if not bundle.reports:
        bundle.note = "no validation targets found"

    # None of the target failures is fatal to the others: report everything
    # and keep the highest-precedence exit code (2 > 3 > 1 > 0).
    exit_code = EXIT_OK
    for code in codes:
        if _EXIT_PRECEDENCE[code] > _EXIT_PRECEDENCE[exit_code]:
            exit_code = code

    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return exit_code


# ---------------------------------------------------------------------------
# validate-registries
# ---------------------------------------------------------------------------


def _validate_registries(args) -> tuple[ReportBundle, int]:
    config_dir = Path(args.config_dir)
    metadata_dir = Path(args.metadata_dir)
    # ``validate-registries`` has no --profile option; registry documents are
    # always validated strictly.
    bundle = ReportBundle(profile=getattr(args, "profile", "strict"))

    # G2 sibling documents / taxonomy for the query-registry semantic checks.
    # A file that cannot be loaded here is reported on its own turn below;
    # the query checks then run without the missing cross-reference (missing
    # registries disable checks instead of producing false failures).
    try:
        query_document = _load_optional_json(
            metadata_dir / "queries" / "query-registry.json"
        )
        variants_document = _load_optional_json(
            metadata_dir / "queries" / "query-variants.json"
        )
        vocabulary = _load_query_vocabulary(metadata_dir)
    except ConfigError:
        query_document = None
        variants_document = None
        vocabulary = None

    found = False
    for directory, entries in (
        (config_dir, REGISTRY_FILES),
        (metadata_dir, METADATA_REGISTRY_FILES),
    ):
        for relative, schema_id in entries:
            path = directory / relative
            if not path.is_file():
                continue
            found = True
            try:
                document = _load_json(path)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                bundle.reports.append(
                    Report(
                        schema_id=schema_id,
                        target=str(path),
                        valid=False,
                        issues=[_io_issue("TARGET_FILE_UNREADABLE", str(path))],
                    )
                )
                continue
            extra_checks = []
            if schema_id == "query-registry-v1":
                extra_checks.append(
                    lambda document, _vocabulary=vocabulary: check_query_registry(
                        document, vocabulary=_vocabulary
                    )
                )
            elif schema_id == "query-variants-registry-v1":
                extra_checks.append(
                    lambda document,
                    _registry=query_document,
                    _vocabulary=vocabulary: check_query_variants(
                        document, query_registry=_registry, vocabulary=_vocabulary
                    )
                )
            outcome = validate_full(
                document,
                schema_id=schema_id,
                target=str(path),
                extra_checks=extra_checks,
            )
            bundle.reports.append(outcome.to_report())

    # G3: the absolute window registry (metadata/windows/*.json).  Each
    # document is validated with ``temporal-window-v1`` plus the temporal
    # semantics; cross-file checks (duplicate window_id, file name) are
    # computed over all documents at once.
    windows_dir = metadata_dir / "windows"
    if windows_dir.is_dir():
        window_items = []
        for path in sorted(windows_dir.glob("*.json")):
            found = True
            try:
                window_items.append((path, _load_json(path)))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                bundle.reports.append(
                    Report(
                        schema_id="temporal-window-v1",
                        target=str(path),
                        valid=False,
                        issues=[_io_issue("TARGET_FILE_UNREADABLE", str(path))],
                    )
                )
        cross_checks = check_window_registry_files(window_items)
        for path, document in window_items:
            outcome = validate_full(
                document,
                schema_id="temporal-window-v1",
                target=str(path),
                extra_checks=[
                    lambda document: check_temporal_semantics(document),
                    lambda document, _path=path: cross_checks.get(str(_path), []),
                ],
            )
            bundle.reports.append(outcome.to_report())

    if not found:
        bundle.note = "no registry files found; nothing to validate"
    return bundle, _exit_code_for_reports(bundle.reports)


def cmd_validate_registries(args) -> int:
    bundle, code = _validate_registries(args)
    _emit(
        bundle.to_dict(),
        fmt=args.format,
        output=args.output,
        human_lines=_bundle_lines(bundle),
    )
    return code


# ---------------------------------------------------------------------------
# audit-legacy (Phase 8)
# ---------------------------------------------------------------------------


def cmd_audit_legacy(args) -> int:
    datasets_root = Path(args.datasets_root)
    files = sorted(datasets_root.rglob("run_metadata.json")) if datasets_root.is_dir() else []

    runs = []
    for path in files:
        entry = {
            "profile": "legacy_audit",
            "run_id": None,
            "status": "unreadable",
            "missing_fields": [],
            "path": str(path),
            "sha256": None,
            "sha256_after": None,
            "unchanged": None,
        }
        try:
            before = sha256_file(path)
            document = _load_json(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            runs.append(entry)
            continue
        record = audit_record(document, sha256=before)
        after = sha256_file(path)
        entry.update(
            {
                "run_id": record.run_id,
                "status": record.status,
                "missing_fields": record.missing_fields,
                "sha256": before,
                "sha256_after": after,
                "unchanged": before == after,
            }
        )
        runs.append(entry)

    audit = {
        "audit_version": "1.0.0",
        "profile": "legacy_audit",
        "schema_id": "collection-run-v1",
        "target_glob": "datasets/**/run_metadata.json",
        "count": len(runs),
        "raw_modified": any(entry.get("unchanged") is False for entry in runs),
        "runs": runs,
    }

    if args.output:
        try:
            _write_output(args.output, audit)
        except OSError as error:
            _err(f"cannot write audit output: {args.output} ({error.__class__.__name__})")
            return EXIT_IO
        _err(f"legacy audit written: {args.output} ({len(runs)} run(s))")
    else:
        print(dump_json(audit), end="")

    incomplete = sum(1 for entry in runs if entry.get("status") != "complete")
    _err(f"legacy audit: {len(runs)} run(s), {incomplete} incomplete")
    return EXIT_OK


# ---------------------------------------------------------------------------
# gate-plan (Phase 6 / P6-1 initial CLI surface)
# ---------------------------------------------------------------------------


def cmd_gate_plan(args) -> int:
    """Pre-collection gate: structural validation + registry/capability gate.

    Exit 0 = proceed, 1 = stop (fail closed), 2 = config error, 3 = I/O error.
    This is an initial surface for P6-1; a full Collection Plan contract lands
    with the G1 adapter contract and may extend the checks.
    """
    try:
        get_schema("collection-plan-v1")
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read input file: {target}")
        return EXIT_IO

    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    outcome = validate_full(
        document,
        schema_id="collection-plan-v1",
        target=str(target),
        registries=registries if registries.any() else None,
    )
    issues = list(outcome.issues)
    if outcome.valid:
        gate = pre_collection_gate(document, registries=registries)
        issues.extend(gate.issues)
        action = gate.action
    else:
        action = "stop"
    issues.sort(key=lambda issue: issue.sort_key())

    report = {
        "validation_version": VALIDATION_VERSION,
        "schema_id": "collection-plan-v1",
        "target": str(target),
        "profile": "gate",
        "action": action,
        "valid": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    lines = [f"{action.upper()} collection-plan-v1 {target}"]
    for issue in issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return _exit_code(issues)


# ---------------------------------------------------------------------------
# gate-run (Phase 6 / L1 post-collection decision)
# ---------------------------------------------------------------------------


def cmd_gate_run(args) -> int:
    """Post-collection L1 gate: structural + semantic + missingness + artifacts.

    Exit 0 = catalog (adoptable), 1 = quarantine (keep raw, do not adopt),
    2 = config error, 3 = I/O error.  The command only decides; moving the
    run into/out of staging is the caller's job (G1 §13).
    """
    target = Path(args.file)
    try:
        document = _load_json(target)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read input file: {target}")
        return EXIT_IO

    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    try:
        outcome = validate_full(
            document,
            schema_id="collection-run-v1",
            target=str(target),
            registries=registries if registries.any() else None,
            base_dir=target.parent,
            verify_artifacts=True,
        )
    except ValueError as error:
        _err(str(error))
        return EXIT_CONFIG

    issues = list(outcome.issues)
    if outcome.valid:
        gate = post_collection_gate(
            document,
            registries=registries if registries.any() else None,
            base_dir=target.parent,
        )
        issues.extend(gate.issues)
        action = gate.action
    else:
        action = "quarantine"
    issues.sort(key=lambda issue: issue.sort_key())

    report = {
        "validation_version": VALIDATION_VERSION,
        "schema_id": "collection-run-v1",
        "target": str(target),
        "profile": "gate",
        "action": action,
        "valid": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    lines = [f"{action.upper()} collection-run-v1 {target}"]
    for issue in issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return _exit_code(issues)


# ---------------------------------------------------------------------------
# compare-runs (G1 §12 L2)
# ---------------------------------------------------------------------------


def cmd_compare_runs(args) -> int:
    """L2 run-level comparability report (C1 / C2 / C3 + optional T6/T7).

    Exit code is 0 for any produced verdict: L2 restricts comparison, it does
    not invalidate data (P5).  Unreadable inputs are I/O errors (exit 3).
    When ``--coverage-a`` / ``--coverage-b`` are given (run directories or
    ``run_metadata.json`` paths), the G3 coverage manifests are evaluated and
    the temporal gate additionally applies the T6/T7 coverage conditions.
    """
    documents = []
    for label, path_str in (("a", args.a), ("b", args.b)):
        path = Path(path_str)
        try:
            documents.append(_load_json(path))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            _err(f"cannot read input file ({label}): {path}")
            return EXIT_IO

    coverage_a = None
    coverage_b = None
    if args.coverage_a:
        coverage_a = evaluate_coverage(args.coverage_a)
    if args.coverage_b:
        coverage_b = evaluate_coverage(args.coverage_b)

    result = compare_runs(
        documents[0],
        documents[1],
        purpose=args.purpose or "",
        coverage_a=coverage_a,
        coverage_b=coverage_b,
    )
    report = {
        "validation_version": VALIDATION_VERSION,
        "gate": "L2",
        "schema_id": "collection-run-v1",
        "a": str(args.a),
        "b": str(args.b),
        "purpose": args.purpose or "direct_comparison",
        "status": result.status,
        "reasons": list(result.reasons),
    }
    if coverage_a is not None or coverage_b is not None:
        report["coverage"] = {
            "a": (coverage_a or {}).get("coverage", {}).get("status"),
            "b": (coverage_b or {}).get("coverage", {}).get("status"),
        }
    lines = [f"L2 {result.status} {args.a} vs {args.b}"]
    for reason in result.reasons:
        lines.append(f"  reason: {reason}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


# ---------------------------------------------------------------------------
# coverage-run (G3 §9)
# ---------------------------------------------------------------------------


def cmd_coverage_run(args) -> int:
    """G3 §9 coverage manifest for one run (read-only).

    The command reports; it never invalidates data, so the exit code is 0
    for any produced manifest (like ``compare-runs``).  Unreadable targets
    are I/O errors (exit 3).
    """
    target = Path(args.file)
    if not target.exists():
        _err(f"cannot read target: {target}")
        return EXIT_IO
    manifest = evaluate_coverage(target)
    coverage = manifest["coverage"]
    lines = [
        f"COVERAGE {coverage['status']} run_id={manifest['run_id']} "
        f"window_id={manifest['window_id']}",
        f"  target: {target}",
    ]
    for reason in coverage["reasons"]:
        lines.append(f"  reason: {reason}")
    for term, entry in sorted(coverage["states"].items()):
        lines.append(
            f"  term {term}: state={entry['state']} "
            f"points={entry['point_count']} zeros={entry['zero_count']}"
        )
    _emit(manifest, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


# ---------------------------------------------------------------------------
# audit-temporal (G3 §15)
# ---------------------------------------------------------------------------


def cmd_audit_temporal(args) -> int:
    """Non-destructive G3 §15 temporal inventory over run metadata files.

    Read-only: every file touched is hashed before and after, and
    ``raw_modified`` records any drift.  Relative legacy periods are never
    converted into absolute windows (``resolved_absolute_window: null``).
    """
    inventory = build_temporal_inventory(Path(args.datasets_root))
    if args.output:
        try:
            _write_output(args.output, inventory)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"temporal inventory written: {args.output} "
            f"({inventory['count']} run(s), raw_modified={inventory['raw_modified']})"
        )
    else:
        print(dump_json(inventory), end="")
    summary = ", ".join(
        f"{key}={value}"
        for key, value in sorted(inventory["classification_summary"].items())
    )
    _err(f"temporal inventory: {inventory['count']} run(s) [{summary}]")
    return EXIT_OK


# ---------------------------------------------------------------------------
# classify-query / compare-queries / audit-queries (G2 §8 / §9 / §13)
# ---------------------------------------------------------------------------


def _query_registry_payload(registries: Registries) -> dict:
    return {
        "schema_version": registries.query_registry_version,
        "queries": list(registries.queries),
    }


def _query_variants_payload(registries: Registries) -> dict:
    return {"variant_sets": list(registries.query_variants)}


def _query_reference(entry: dict) -> dict:
    return {
        "query_id": entry.get("query_id"),
        "compound_id": entry.get("compound_id"),
        "intent_id": entry.get("intent_id"),
        "canonical_text": entry.get("canonical_text"),
        "status": entry.get("status"),
    }


def cmd_classify_query(args) -> int:
    """Stage-1 deterministic classification of one query string (G2 §8).

    Exit 0 = the text resolves to a registered query in ``active`` status
    (adoptable as that query); 1 = not adoptable (irrelevant / ambiguous /
    unknown, or a non-active registration); 2 = configuration error (query
    registry missing or unreadable).
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
        vocabulary = _load_query_vocabulary(Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    result = classify_query_text(
        args.text,
        query_registry=_query_registry_payload(registries),
        variant_registry=_query_variants_payload(registries),
        vocabulary=vocabulary,
    )
    result["registry_version"] = registries.query_registry_version
    adoptable = (
        result["classification"] == "relevant"
        and result.get("query_status") == "active"
    )
    lines = [f"{result['classification'].upper()} {result['text']!r}"]
    if result.get("query_id"):
        lines.append(
            f"  query_id: {result['query_id']} "
            f"(status={result.get('query_status')})"
        )
    if result.get("variant_id"):
        lines.append(f"  variant_id: {result['variant_id']}")
    if result.get("rule_id"):
        lines.append(f"  rule: {result['rule_id']} - {result.get('rationale')}")
        lines.append(f"  evidence: {result.get('evidence')}")
    if result.get("matched_tokens"):
        lines.append("  matched tokens: " + ", ".join(result["matched_tokens"]))
    for reason in result.get("reasons", []):
        lines.append(f"  reason: {reason}")
    _emit(result, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK if adoptable else EXIT_DATA


def cmd_compare_queries(args) -> int:
    """Definition-level comparability of two registered queries (G2 §9).

    The verdict never invalidates data (exit 0 for any produced verdict,
    like ``compare-runs``); an unknown query_id is a configuration error
    (exit 2, fail closed).
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    entries = {
        query.get("query_id"): query
        for query in registries.queries
        if isinstance(query, dict)
    }
    for name in (args.a, args.b):
        if name not in entries:
            _err(f"unknown query_id: {name}")
            return EXIT_CONFIG

    result = compare_query_definitions(
        entries[args.a],
        entries[args.b],
        registry_version_a=registries.query_registry_version,
        registry_version_b=registries.query_registry_version,
    )
    report = {
        "validation_version": VALIDATION_VERSION,
        "gate": "G2-query-comparability",
        "schema_id": "query-registry-v1",
        "registry_version": registries.query_registry_version,
        "a": _query_reference(entries[args.a]),
        "b": _query_reference(entries[args.b]),
        "status": result.status,
        "reasons": list(result.reasons),
    }
    lines = [f"G2 {result.status} {args.a} vs {args.b}"]
    for reason in result.reasons:
        lines.append(f"  reason: {reason}")
    _emit(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


def cmd_audit_queries(args) -> int:
    """Non-destructive b.md §13 query inventory over run metadata files.

    Read-only: each file is hashed before and after reading and
    ``raw_modified`` records any drift.  Exit 0 on success, 2 for a missing
    query registry / configuration error, 3 when the output cannot be
    written.
    """
    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
        vocabulary = _load_query_vocabulary(Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    if not registries.queries:
        _err("query registry not found (metadata/queries/query-registry.json)")
        return EXIT_CONFIG

    datasets_root = Path(args.datasets_root)
    files = (
        sorted(datasets_root.rglob("run_metadata.json"))
        if datasets_root.is_dir()
        else []
    )
    entries = []
    for path in files:
        entry = {
            "path": str(path),
            "document": None,
            "sha256": None,
            "sha256_after": None,
            "unchanged": None,
        }
        try:
            before = sha256_file(path)
            document = _load_json(path)
            after = sha256_file(path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            entries.append(entry)
            continue
        entry.update(
            {
                "document": document,
                "sha256": before,
                "sha256_after": after,
                "unchanged": before == after,
            }
        )
        entries.append(entry)

    audit = build_query_inventory(
        entries,
        query_registry=_query_registry_payload(registries),
        variant_registry=_query_variants_payload(registries),
        vocabulary=vocabulary,
    )

    if args.output:
        try:
            _write_output(args.output, audit)
        except OSError as error:
            _err(
                f"cannot write audit output: {args.output} "
                f"({error.__class__.__name__})"
            )
            return EXIT_IO
        _err(
            f"query inventory written: {args.output} "
            f"({audit['count']} run(s), {audit['query_count']} string(s))"
        )
    else:
        print(dump_json(audit), end="")
    summary = ", ".join(
        f"{key}={value}" for key, value in sorted(audit["summary"].items())
    )
    _err(
        f"query inventory: {audit['count']} run(s), "
        f"{audit['query_count']} string(s) [{summary}]"
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


def _add_common(parser, *, with_profile=True):
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="report format (json goes to stdout or --output)",
    )
    parser.add_argument("--output", help="write the JSON report to this path")
    if with_profile:
        parser.add_argument(
            "--profile", choices=("strict", "legacy"), default="strict",
            help="strict (new runs) or legacy (frozen legacy run IDs only)",
        )
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--metadata-dir", default="metadata")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m validation.cli",
        description="Cerberus validation framework CLI (docs/specs/validation-framework.md)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate one file against one schema")
    validate.add_argument("--schema", required=True)
    validate.add_argument("--file", required=True)
    validate.add_argument(
        "--verify-artifacts", action="store_true",
        help="also verify the artifact manifest referenced by the document",
    )
    _add_common(validate)
    validate.set_defaults(handler=cmd_validate)

    study = sub.add_parser("validate-study", help="validate every run under a study")
    study.add_argument("--study", required=True)
    study.add_argument("--datasets-root", default="datasets")
    study.add_argument("--schema", default="collection-run-v1")
    _add_common(study)
    study.set_defaults(handler=cmd_validate_study)

    registries = sub.add_parser(
        "validate-registries", help="validate every registry file that exists"
    )
    _add_common(registries, with_profile=False)
    registries.set_defaults(handler=cmd_validate_registries)

    all_parser = sub.add_parser(
        "validate-all", help="registries plus every study (CI-oriented)"
    )
    all_parser.add_argument("--datasets-root", default="datasets")
    all_parser.add_argument("--schema", default="collection-run-v1")
    _add_common(all_parser)
    all_parser.set_defaults(handler=cmd_validate_all)

    gate = sub.add_parser(
        "gate-plan", help="pre-collection gate for a collection plan (P6-1)"
    )
    gate.add_argument("--file", required=True)
    _add_common(gate, with_profile=False)
    gate.set_defaults(handler=cmd_gate_plan)

    gate_run = sub.add_parser(
        "gate-run",
        help="post-collection L1 gate: catalog vs quarantine (P6-2)",
    )
    gate_run.add_argument("--file", required=True)
    _add_common(gate_run, with_profile=False)
    gate_run.set_defaults(handler=cmd_gate_run)

    compare = sub.add_parser(
        "compare-runs", help="L2 run-level comparability report (G1 §12)"
    )
    compare.add_argument("--a", required=True, help="first run_metadata.json")
    compare.add_argument("--b", required=True, help="second run_metadata.json")
    compare.add_argument(
        "--purpose",
        default="",
        help="comparison purpose; only direct_comparison is modelled today",
    )
    compare.add_argument(
        "--coverage-a",
        help="run directory / run_metadata.json for the G3 coverage conditions "
        "(T6/T7) on side a",
    )
    compare.add_argument(
        "--coverage-b",
        help="run directory / run_metadata.json for the G3 coverage conditions "
        "(T6/T7) on side b",
    )
    compare.add_argument("--format", choices=("text", "json"), default="text")
    compare.add_argument("--output", help="write the JSON report to this path")
    compare.set_defaults(handler=cmd_compare_runs)

    coverage_run = sub.add_parser(
        "coverage-run",
        help="G3 §9 coverage manifest for one run (read-only report)",
    )
    coverage_run.add_argument(
        "--file", required=True, help="run directory or run_metadata.json"
    )
    coverage_run.add_argument("--format", choices=("text", "json"), default="text")
    coverage_run.add_argument("--output", help="write the JSON manifest to this path")
    coverage_run.set_defaults(handler=cmd_coverage_run)

    audit_temporal = sub.add_parser(
        "audit-temporal",
        help="non-destructive G3 §15 temporal inventory over run_metadata files",
    )
    audit_temporal.add_argument("--datasets-root", default="datasets")
    audit_temporal.add_argument(
        "--output", default="docs/audits/g3-temporal-inventory.json"
    )
    audit_temporal.set_defaults(handler=cmd_audit_temporal)

    classify = sub.add_parser(
        "classify-query",
        help="Stage-1 classification of one query string (G2 §8)",
    )
    classify.add_argument("--text", required=True)
    _add_common(classify, with_profile=False)
    classify.set_defaults(handler=cmd_classify_query)

    compare_queries = sub.add_parser(
        "compare-queries",
        help="definition-level comparability of two registered queries (G2 §9)",
    )
    compare_queries.add_argument("--a", required=True, help="query_id (query registry)")
    compare_queries.add_argument("--b", required=True, help="query_id (query registry)")
    _add_common(compare_queries, with_profile=False)
    compare_queries.set_defaults(handler=cmd_compare_queries)

    audit_queries = sub.add_parser(
        "audit-queries",
        help="non-destructive G2 query inventory over run_metadata files (b.md §13)",
    )
    audit_queries.add_argument("--datasets-root", default="datasets")
    audit_queries.add_argument(
        "--output", default="docs/audits/g2-query-inventory.json"
    )
    audit_queries.add_argument("--config-dir", default="config")
    audit_queries.add_argument("--metadata-dir", default="metadata")
    audit_queries.set_defaults(handler=cmd_audit_queries)

    audit = sub.add_parser(
        "audit-legacy", help="non-destructive G5 legacy audit (Phase 8)"
    )
    audit.add_argument("--datasets-root", default="datasets")
    audit.add_argument(
        "--output", default="docs/audits/g5-legacy-runs.json"
    )
    audit.set_defaults(handler=cmd_audit_legacy)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
