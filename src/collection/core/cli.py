"""Collection CLI (G1 slice): ``python -m collection.core.cli collect|adopt``.

Commands
--------
- ``collect --plan <plan.json>``: run the full pipeline (pre-gate -> window
  compile -> adapter -> staging -> L1 -> catalog/quarantine).  The adapter
  comes from the plan's ``source_id``; for ``google-trends`` a ``--fixture``
  (recorded response) is required because live collection is not executed by
  this environment.  ``--now`` fixes the reference/collection time for
  deterministic replays (G3 window compilation resolves relative timeframes
  against it).
- ``adopt --staged <dir>``: L1 + catalog/quarantine for a run staged by an
  external collector (shell scripts) - the migration path for
  ``src/collection/*.sh``.
- ``compile-window``: G3 §6 dry-run: compile an absolute window into the
  collector's registered parameters and print the result (fail closed).

Exit codes (shared with the validation CLI):
0 = adopted / 1 = quarantined or stopped / 2 = configuration error /
3 = I/O error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from collection.adapters import AdapterUnavailable, get_adapter_factory, get_window_compiler
from collection.core.pipeline import PipelineResult, adopt_staged, run_collection
from collection.core.registry import ConfigError, load_registries
from collection.core.selection import select_collector
from validation.windows import (
    WindowCompilationError,
    check_window_compiler,
    find_window,
    load_window_documents,
    parse_datetime,
)

__all__ = ["main"]

EXIT_OK = 0
EXIT_GATE = 1
EXIT_CONFIG = 2
EXIT_IO = 3


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _emit(result: PipelineResult, *, fmt: str, output: str | None) -> None:
    report = result.to_dict()
    if fmt == "json":
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    lines = [
        f"{result.action.upper()} run_id={result.run_id} "
        f"{'-> ' + result.final_dir if result.final_dir else ''}".rstrip()
    ]
    for issue in result.issues:
        lines.append(f"  [{issue.code}] {issue.path}: {issue.message}")
    if result.l1 is not None:
        for issue in result.l1.issues:
            lines.append(f"  [L1:{issue.code}] {issue.path}: {issue.message}")
    stream = sys.stderr
    for line in lines:
        print(line, file=stream)


def _emit_report(report: dict, *, fmt: str, output: str | None, human_lines) -> None:
    if fmt == "json":
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    for line in human_lines:
        print(line, file=sys.stderr)


def _load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def cmd_collect(args) -> int:
    plan_path = Path(args.plan)
    try:
        plan = _load_json(plan_path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        _err(f"cannot read plan file: {plan_path}")
        return EXIT_IO

    now = None
    if args.now:
        try:
            now = parse_datetime(args.now)
        except ValueError as error:
            _err(f"invalid --now: {error}")
            return EXIT_CONFIG

    source_id = plan.get("source_id") if isinstance(plan, dict) else None
    try:
        factory = get_adapter_factory(source_id)
    except AdapterUnavailable as error:
        _err(str(error))
        return EXIT_CONFIG

    workspace = Path(args.workspace)
    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    # Resolve the collector entry first so the adapter can report exactly the
    # capabilities the registry records (the record of truth).
    collector_entry, selection_issues = select_collector(plan, registries)
    if selection_issues:
        result = PipelineResult(action="stopped", issues=selection_issues)
        _emit(result, fmt=args.format, output=args.output)
        return EXIT_GATE

    adapter = factory(
        fixture=args.fixture,
        capabilities=collector_entry.get("capabilities"),
    )
    result = run_collection(
        plan,
        adapter=adapter,
        workspace_root=workspace,
        datasets_root=Path(args.datasets_root),
        registries=registries,
        run_id=args.run_id,
        now=now,
    )
    _emit(result, fmt=args.format, output=args.output)
    if result.adopted:
        return EXIT_OK
    return EXIT_GATE


def cmd_adopt(args) -> int:
    workspace = Path(args.workspace)
    try:
        registries = load_registries(
            Path(args.config_dir), Path(args.metadata_dir)
        )
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG

    result = adopt_staged(
        args.staged,
        workspace_root=workspace,
        datasets_root=Path(args.datasets_root),
        registries=registries,
    )
    _emit(result, fmt=args.format, output=args.output)
    if result.action == "stopped":
        return EXIT_GATE
    if result.adopted:
        return EXIT_OK
    return EXIT_GATE


def cmd_compile_window(args) -> int:
    """G3 §6 window compilation dry-run (no collection is performed).

    Reads an absolute window (file or ``--window-id`` from the window
    registry), compiles it for the collector's registered vocabulary and
    prints the result.  Exit 0 = representable (the compiled window carries
    ``exact=false`` until boundary verification), 1 = refused (fail closed,
    P6), 2 = configuration error (unknown collector / no compiler), 3 =
    unreadable input.
    """
    if bool(args.window) == bool(args.window_id):
        _err("exactly one of --window / --window-id is required")
        return EXIT_CONFIG

    if args.window:
        try:
            window = _load_json(Path(args.window))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            _err(f"cannot read window file: {args.window}")
            return EXIT_IO
    else:
        try:
            documents = load_window_documents(Path(args.metadata_dir) / "windows")
        except ValueError as error:
            _err(str(error))
            return EXIT_CONFIG
        window = find_window(documents, args.window_id)
        if window is None:
            _err(f"window_id is not registered in metadata/windows: {args.window_id}")
            return EXIT_CONFIG

    try:
        reference_time = parse_datetime(args.reference_time)
    except ValueError as error:
        _err(f"invalid --reference-time: {error}")
        return EXIT_CONFIG

    try:
        registries = load_registries(Path(args.config_dir), Path(args.metadata_dir))
    except ConfigError as error:
        _err(str(error))
        return EXIT_CONFIG
    collector_entry = next(
        (
            collector
            for collector in registries.collectors
            if isinstance(collector, dict)
            and collector.get("collector_id") == args.collector
        ),
        None,
    )
    if collector_entry is None:
        _err(f"collector is not registered: {args.collector}")
        return EXIT_CONFIG

    compiler = get_window_compiler(args.collector)
    if compiler is None:
        _err(f"no window compiler is registered for collector: {args.collector}")
        return EXIT_CONFIG
    violations = check_window_compiler(compiler)
    if violations:
        for violation in violations:
            _err(f"window compiler contract violation: {violation}")
        return EXIT_CONFIG

    window_id = window.get("window_id") if isinstance(window, dict) else None
    try:
        compiled = compiler.compile(
            window,
            reference_time=reference_time,
            capabilities=collector_entry.get("capabilities"),
        )
    except WindowCompilationError as error:
        report = {
            "command": "compile-window",
            "collector_id": args.collector,
            "window_id": window_id,
            "reference_time": args.reference_time,
            "refused": True,
            "reason_codes": list(error.codes),
            "message": str(error),
            "compiled": None,
        }
        lines = [
            f"REFUSED window_id={window_id} collector={args.collector}",
            f"  codes: {', '.join(error.codes)}",
            f"  {error}",
        ]
        _emit_report(report, fmt=args.format, output=args.output, human_lines=lines)
        return EXIT_GATE

    report = {
        "command": "compile-window",
        "collector_id": args.collector,
        "window_id": window_id,
        "reference_time": args.reference_time,
        "refused": False,
        "reason_codes": [],
        "message": None,
        "compiled": compiled.to_dict(),
    }
    lines = [
        f"COMPILED window_id={window_id} collector={args.collector} "
        f"timeframe={compiled.parameters.get('timeframe')} exact={compiled.exact}",
        f"  resolved: {compiled.resolved_start} .. {compiled.resolved_end_exclusive}",
    ]
    for limitation in compiled.limitations:
        lines.append(f"  limitation: {limitation}")
    _emit_report(report, fmt=args.format, output=args.output, human_lines=lines)
    return EXIT_OK


def _add_common(parser):
    parser.add_argument(
        "--workspace", default=".", help="root for .staging / .quarantine"
    )
    parser.add_argument("--datasets-root", default="datasets")
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--metadata-dir", default="metadata")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", help="write the JSON report to this path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m collection.core.cli",
        description="G1 collection core CLI (docs/specs/collection-pipeline.md)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="run the collection pipeline")
    collect.add_argument("--plan", required=True)
    collect.add_argument(
        "--fixture",
        help="recorded response fixture (required for offline replay; live "
        "collection is not executed here)",
    )
    collect.add_argument("--run-id", help="explicit run_id (default: timestamped)")
    collect.add_argument(
        "--now",
        help="ISO 8601 reference / collection time override (deterministic "
        "replays; the reference is also what relative windows are compiled "
        "against). Default: current UTC time",
    )
    _add_common(collect)
    collect.set_defaults(handler=cmd_collect)

    adopt = sub.add_parser(
        "adopt", help="L1 + catalog/quarantine for a staged run directory"
    )
    adopt.add_argument("--staged", required=True)
    _add_common(adopt)
    adopt.set_defaults(handler=cmd_adopt)

    compile_window = sub.add_parser(
        "compile-window",
        help="G3 §6: compile an absolute window into collector parameters "
        "(dry run; no collection)",
    )
    compile_window.add_argument("--window", help="path to a window document (temporal-window-v1)")
    compile_window.add_argument("--window-id", help="window_id from metadata/windows/")
    compile_window.add_argument("--collector", required=True)
    compile_window.add_argument(
        "--reference-time",
        required=True,
        help="ISO 8601 collection reference time the relative timeframe is resolved against",
    )
    compile_window.add_argument(
        "--config-dir", default="config", help="registry root"
    )
    compile_window.add_argument("--metadata-dir", default="metadata")
    compile_window.add_argument("--format", choices=("text", "json"), default="text")
    compile_window.add_argument("--output", help="write the JSON report to this path")
    compile_window.set_defaults(handler=cmd_compile_window)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
