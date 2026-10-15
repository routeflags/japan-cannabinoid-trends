#!/usr/bin/env python3
"""Safely probe or run Google Trends live recollection tooling.

Examples:

  # Tooling discovery only; no observation fetch and no raw write.
  PYTHONPATH=src python3 scripts/collection/google-trends-live-guard.py probe \
    --timeout 30

  # Authorized live collection through the repository pipeline, bounded by an
  # outer timeout.  This may catalog a new raw run if the pipeline succeeds.
  PYTHONPATH=src python3 scripts/collection/google-trends-live-guard.py fetch \
    --plan path/to/plan.json \
    --run-id 20261015T000000Z-google-trends-cbd-5y-recollection \
    --timeout 300

The script intentionally avoids ``npx ... --help`` and output-truncating pipes
such as ``head``/``tail``.  Logs go under ``.staging/tooling_logs`` by default,
which is ignored by Git and is safe for issue diagnostics after human review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from collection.adapters.google_trends.live_guard import (
    DEFAULT_LOG_ROOT,
    DEFAULT_MCP_COMMAND,
    SCRIPT_EXIT_CODES,
    probe_mcp_tools,
    run_bounded_command,
    utc_run_id,
)


def _print_result(result, *, emit_json: bool) -> None:
    payload = result.to_dict()
    if emit_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(
        f"{payload['classification'].upper()} "
        f"exit={payload['exit_code']} timeout={payload['timed_out']} "
        f"log_dir={payload['log_dir']}",
        file=sys.stderr,
    )
    if payload.get("message"):
        print(f"  {payload['message']}", file=sys.stderr)
    print(f"  report: {payload['report_path']}", file=sys.stderr)
    print(f"  stdout: {payload['stdout_log']}", file=sys.stderr)
    print(f"  stderr: {payload['stderr_log']}", file=sys.stderr)


def cmd_probe(args) -> int:
    command = args.command if args.command else list(DEFAULT_MCP_COMMAND)
    result = probe_mcp_tools(
        command,
        timeout_seconds=args.timeout,
        log_root=Path(args.log_dir),
        run_id=args.run_id or utc_run_id("gt-probe"),
        cwd=args.cwd,
    )
    _print_result(result, emit_json=args.json)
    return SCRIPT_EXIT_CODES[result.classification]


def cmd_fetch(args) -> int:
    run_id = args.guard_run_id or utc_run_id("gt-fetch")
    output_report = Path(args.log_dir) / run_id / "collection-report.json"
    command = [
        sys.executable,
        "-m",
        "collection.core.cli",
        "collect",
        "--live",
        "--plan",
        args.plan,
        "--run-id",
        args.run_id,
        "--workspace",
        args.workspace,
        "--datasets-root",
        args.datasets_root,
        "--config-dir",
        args.config_dir,
        "--metadata-dir",
        args.metadata_dir,
        "--format",
        "json",
        "--output",
        str(output_report),
    ]
    if args.now:
        command.extend(["--now", args.now])
    result = run_bounded_command(
        command,
        timeout_seconds=args.timeout,
        log_root=Path(args.log_dir),
        run_id=run_id,
        cwd=args.cwd,
    )
    _print_result(result, emit_json=args.json)
    return SCRIPT_EXIT_CODES[result.classification]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded Google Trends live tooling guard. Use 'probe' before any "
            "authorized 'fetch'; never call npx google-trends-mcp directly."
        )
    )
    sub = parser.add_subparsers(dest="command_name", required=True)

    probe = sub.add_parser(
        "probe",
        help="initialize the MCP server and list tools without fetching observations",
    )
    probe.add_argument("--timeout", type=float, default=30.0)
    probe.add_argument("--log-dir", default=str(DEFAULT_LOG_ROOT))
    probe.add_argument("--run-id", help="diagnostic log run id (default: timestamped)")
    probe.add_argument("--cwd", help="working directory for the child process")
    probe.add_argument("--json", action="store_true", help="print JSON report to stdout")
    probe.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help=(
            "collector command after '--'. Defaults to: "
            + " ".join(DEFAULT_MCP_COMMAND)
        ),
    )
    probe.set_defaults(handler=cmd_probe)

    fetch = sub.add_parser(
        "fetch",
        help=(
            "run the repository collection pipeline with --live under an outer "
            "timeout; may write a new raw run if authorized and successful"
        ),
    )
    fetch.add_argument("--plan", required=True)
    fetch.add_argument("--run-id", required=True, help="collection run_id to catalog/stage")
    fetch.add_argument("--timeout", type=float, default=300.0)
    fetch.add_argument("--log-dir", default=str(DEFAULT_LOG_ROOT))
    fetch.add_argument("--guard-run-id", help="diagnostic log run id (default: timestamped)")
    fetch.add_argument("--workspace", default=".")
    fetch.add_argument("--datasets-root", default="datasets")
    fetch.add_argument("--config-dir", default="config")
    fetch.add_argument("--metadata-dir", default="metadata")
    fetch.add_argument("--now", help="deterministic collection/reference time override")
    fetch.add_argument("--cwd", help="working directory for the child process")
    fetch.add_argument("--json", action="store_true", help="print JSON report to stdout")
    fetch.set_defaults(handler=cmd_fetch)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) and args.command[0] == "--":
        args.command = args.command[1:]
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
