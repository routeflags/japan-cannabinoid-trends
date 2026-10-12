"""Validation CLI (Phase 5, h.md §13 / §14).

Commands
--------
- ``validate``            one file against one registered schema
- ``validate-study``      every ``run_metadata.json`` under a study
- ``validate-registries`` every known registry file that exists
- ``validate-all``        registries + all studies (JSON report for CI)
- ``gate-plan``           pre-collection gate for a collection plan (P6-1)
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

from validation.gates import pre_collection_gate
from validation.integrity import IO_ISSUE_CODES, sha256_file
from validation.legacy import LegacyProfileNotAllowed, audit_record
from validation.pipeline import validate_full
from validation.reporting import (
    VALIDATION_VERSION,
    Issue,
    Report,
    ReportBundle,
    dump_json,
)
from validation.schema_registry import get_schema
from validation.semantic import Registries

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


def load_registries(config_dir: Path, metadata_dir: Path) -> Registries:
    """Build the reference-check registries from present files only.

    Returns an empty ``Registries`` while the G1/G2/G7 registry files do not
    exist yet; reference checks are then skipped instead of failing.
    """
    return Registries.from_documents(
        source_registry=_load_optional_json(config_dir / "sources.json"),
        collector_registry=_load_optional_json(config_dir / "collectors.json"),
        query_registry=_load_optional_json(
            metadata_dir / "queries" / "query-registry.json"
        ),
        study_registry=_load_optional_json(
            metadata_dir / "studies" / "study-registry.json"
        ),
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
            outcome = validate_full(
                document, schema_id=schema_id, target=str(path)
            )
            bundle.reports.append(outcome.to_report())

    if not found:
        bundle.note = (
            "no registry files found (G1/G2/G6/G7 registries are not "
            "implemented yet); nothing to validate"
        )
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
