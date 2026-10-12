"""Collection CLI (G1 slice): ``python -m collection.core.cli collect|adopt``.

Commands
--------
- ``collect --plan <plan.json>``: run the full pipeline (pre-gate -> adapter ->
  staging -> L1 -> catalog/quarantine).  The adapter comes from the plan's
  ``source_id``; for ``google-trends`` a ``--fixture`` (recorded response) is
  required because live collection is not executed by this environment.
- ``adopt --staged <dir>``: L1 + catalog/quarantine for a run staged by an
  external collector (shell scripts) - the migration path for
  ``src/collection/*.sh``.

Exit codes (shared with the validation CLI):
0 = adopted / 1 = quarantined or stopped / 2 = configuration error /
3 = I/O error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from collection.adapters import AdapterUnavailable, get_adapter_factory
from collection.core.pipeline import PipelineResult, adopt_staged, run_collection
from collection.core.registry import ConfigError, load_registries
from collection.core.selection import select_collector

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
    _add_common(collect)
    collect.set_defaults(handler=cmd_collect)

    adopt = sub.add_parser(
        "adopt", help="L1 + catalog/quarantine for a staged run directory"
    )
    adopt.add_argument("--staged", required=True)
    _add_common(adopt)
    adopt.set_defaults(handler=cmd_adopt)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
