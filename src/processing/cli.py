"""Processing CLI:

- ``audit-processed``  every committed ``data/processed`` artifact is either
  verifiably re-derivable or explicitly declared non-reproducible
- ``classify``         classify one text against the content taxonomy notations
- ``aggregate-x``        weekly/monthly group counts from the private per-post
  X input (read-only; no per-post output)
- ``build-platform-trends``  Google Trends + YouTube cross-platform release
  tables (X excluded by owner decision)
- ``youtube-monthly-aggregate``  monthly counts from the adopted HHBD YouTube
  search-result sample (no per-video fields)

The Python API (:mod:`processing.reproduce`, :mod:`processing.classify`) is the
primary interface; this CLI exposes it for operators and CI.

Exit codes follow the repository convention (``docs/specs/validation-framework.md``):
``0`` success, ``1`` data/audit failure, ``2`` configuration error, ``3`` I/O.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from processing.classify import classify_text
from processing.aggregate_x import (
    AGGREGATOR_VERSION,
    COMPOUND_DEFAULT,
    COARSE_MONTHLY_COLUMNS,
    MONTHLY_COLUMNS,
    WEEKLY_COLUMNS,
    AggregateError,
    aggregate_coarse_monthly_rows,
    aggregate_rows,
    read_private_input,
    scan_output_for_identifiers,
    sha256_file,
    write_aggregate_csv,
)
from processing.gt_statistics import (
    PUBLICATION_COMPOUNDS,
    TIMEFRAMES,
    build_gt_summary,
    page_filename,
    replace_block,
)
from processing.gt_legacy_label_corrections import write_manifest as write_gt_legacy_label_corrections
from processing.platform_trends import build_platform_trends
from processing.youtube_export import build_video_export, write_export
from processing.youtube_monthly_aggregate import (
    YouTubeAggregationError,
    build_youtube_monthly_aggregate,
    write_youtube_monthly_aggregate,
)
from processing.reproduce import audit_processed_artifacts, reproduce_artifact
from processing.rulespec import RuleSpecError, load_content_rules
from validation.reporting import dump_json

EXIT_OK = 0
EXIT_DATA = 1
EXIT_CONFIG = 2
EXIT_IO = 3


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def cmd_audit_processed(args) -> int:
    try:
        report = audit_processed_artifacts(args.repo_root, args.datasets_root)
    except RuleSpecError as error:
        _err(f"classifier specification could not be read: {error}")
        return EXIT_CONFIG
    except OSError as error:
        _err(f"audit failed: {error}")
        return EXIT_IO

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dump_json(report), encoding="utf-8")

    if args.format == "json":
        print(dump_json(report), end="")
    else:
        for entry in report["entries"]:
            print(f"{entry['status']:38} {entry['artifact']}")
            for drift in entry.get("undeclared_drift", []):
                print(
                    f"    undeclared: {drift['column']} derived="
                    f"{drift['derived_value']!r} committed={drift['committed_value']!r} "
                    f"({drift['rows']} row(s))"
                )
            for stale in entry.get("stale_declarations", []):
                print(
                    f"    stale declaration: {stale['column']} declared "
                    f"{stale['declared_rows']} row(s), observed 0"
                )
        summary = ", ".join(f"{k}={v}" for k, v in report["status_summary"].items())
        print(f"processed artifact audit: {report['count']} artifact(s) [{summary}]")
        if report["failures"]:
            print(f"FAILURES: {len(report['failures'])}", file=sys.stderr)
    return EXIT_DATA if report["failures"] else EXIT_OK


def cmd_reproduce(args) -> int:
    try:
        report = reproduce_artifact(Path(args.repo_root), args.artifact)
    except KeyError:
        _err(f"no derivation registered for {args.artifact}")
        return EXIT_CONFIG
    except RuleSpecError as error:
        _err(f"classifier specification could not be read: {error}")
        return EXIT_CONFIG
    except OSError as error:
        _err(f"re-derivation failed: {error}")
        return EXIT_IO

    if args.format == "json":
        print(dump_json(report), end="")
    else:
        rows = report["rows"]
        print(f"{report['artifact']}")
        print(f"  source: {report['source']} ({report['derivation']})")
        print(f"  rows: derived={rows['derived']} committed={rows['committed']}")
        print(f"  status: {report['status']}")
        for drift in report["discrepancies"]:
            print(
                f"    {drift['column']}: derived={drift['derived_value']!r} "
                f"committed={drift['committed_value']!r} ({drift['rows']} row(s))"
            )
    return EXIT_OK if report["status"] != "undeclared" else EXIT_DATA


def cmd_classify(args) -> int:
    try:
        rules = load_content_rules(repo_root=args.repo_root)
    except RuleSpecError as error:
        _err(f"classifier specification could not be read: {error}")
        return EXIT_CONFIG
    result = classify_text(args.text, rules)
    if args.format == "json":
        print(dump_json(result), end="")
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return EXIT_OK


def cmd_build_platform_trends(args) -> int:
    try:
        manifest = build_platform_trends(args.repo_root, args.output_dir)
    except OSError as error:
        _err(f"build-platform-trends: cannot write dataset: {error}")
        return EXIT_IO
    except (json.JSONDecodeError, KeyError) as error:
        _err(f"build-platform-trends: invalid source evidence: {error}")
        return EXIT_CONFIG
    if args.format == "json":
        print(dump_json(manifest), end="")
    else:
        counts = ", ".join(
            f"{name}={count}" for name, count in manifest["row_counts"].items()
        )
        print(f"platform trends dataset written: {args.output_dir} [{counts}]")
    return EXIT_OK


def cmd_aggregate_x(args) -> int:
    """Aggregate the private per-post X input (read-only) into group counts."""
    from processing.aggregate_x import COMPOUND_PROVENANCE

    try:
        rows, digest_before = read_private_input(args.input)
    except AggregateError as error:
        _err(f"aggregate-x: invalid input: {error}")
        return EXIT_CONFIG
    except OSError as error:
        _err(f"aggregate-x: cannot read input: {error}")
        return EXIT_IO
    try:
        weekly, monthly, diagnostics = aggregate_rows(rows, compound=args.compound)
        coarse_monthly, coarse_diagnostics = aggregate_coarse_monthly_rows(
            rows, compound=args.compound
        )
    except AggregateError as error:
        _err(f"aggregate-x: validation error: {error}")
        return EXIT_DATA
    if not (args.weekly_out or args.monthly_out or args.monthly_coarse_out):
        _err("aggregate-x: specify at least one output path")
        return EXIT_CONFIG
    output_tables = []
    if args.weekly_out:
        output_tables.append((WEEKLY_COLUMNS, weekly))
    if args.monthly_out:
        output_tables.append((MONTHLY_COLUMNS, monthly))
    if args.monthly_coarse_out:
        output_tables.append((COARSE_MONTHLY_COLUMNS, coarse_monthly))
    for columns, table in output_tables:
        findings = scan_output_for_identifiers(columns, table)
        if findings:
            for finding in findings:
                _err(f"aggregate-x: identifier scan: {finding}")
            return EXIT_DATA
    weekly_total = sum(int(r["post_count"]) for r in weekly)
    monthly_total = sum(int(r["post_count"]) for r in monthly)
    if weekly_total != len(rows) or monthly_total != len(rows):
        _err(
            "aggregate-x: totals do not reconcile "
            f"(input={len(rows)} weekly={weekly_total} monthly={monthly_total})"
        )
        return EXIT_DATA
    try:
        output = {}
        if args.weekly_out:
            output["weekly"] = {
                "path": args.weekly_out,
                "sha256": write_aggregate_csv(args.weekly_out, WEEKLY_COLUMNS, weekly),
            }
        if args.monthly_out:
            output["monthly"] = {
                "path": args.monthly_out,
                "sha256": write_aggregate_csv(args.monthly_out, MONTHLY_COLUMNS, monthly),
            }
        if args.monthly_coarse_out:
            output["monthly_coarse"] = {
                "path": args.monthly_coarse_out,
                "sha256": write_aggregate_csv(
                    args.monthly_coarse_out, COARSE_MONTHLY_COLUMNS, coarse_monthly
                ),
            }
    except OSError as error:
        _err(f"aggregate-x: cannot write output: {error}")
        return EXIT_IO
    digest_after = sha256_file(args.input)
    if digest_after != digest_before:
        _err("aggregate-x: private input changed during the run; refusing output")
        return EXIT_DATA
    if args.report:
        import json

        small_weekly = [int(r["post_count"]) for r in weekly]
        small_monthly = [int(r["post_count"]) for r in monthly]
        report = {
            "aggregator_version": AGGREGATOR_VERSION,
            "compound": args.compound,
            "compound_provenance": COMPOUND_PROVENANCE,
            "input": {
                "path": args.input,
                "sha256_before": digest_before,
                "sha256_after": digest_after,
                "unchanged": digest_before == digest_after,
                "rows": len(rows),
            },
            "diagnostics": diagnostics,
            "reconciliation": {
                "input_rows": len(rows),
                "weekly_sum": weekly_total,
                "monthly_sum": monthly_total,
                "match": weekly_total == len(rows) and monthly_total == len(rows),
            },
            "small_cell": {
                "weekly_groups": len(weekly),
                "weekly_n1": sum(1 for n in small_weekly if n == 1),
                "weekly_n_le2": sum(1 for n in small_weekly if n <= 2),
                "monthly_groups": len(monthly),
                "monthly_n1": sum(1 for n in small_monthly if n == 1),
                "monthly_n_le2": sum(1 for n in small_monthly if n <= 2),
            },
            "coarse_monthly": coarse_diagnostics,
            "identifier_scan": "pass",
            "output": output,
        }
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"aggregate-x: input={len(rows)} weekly_groups={len(weekly)} "
        f"monthly_groups={len(monthly)} coarse_monthly_groups={len(coarse_monthly)} "
        f"version={AGGREGATOR_VERSION}"
    )
    return EXIT_OK


def _write_page_blocks(report: dict, repo_root: Path) -> list[str]:
    """Put each generated block into its page.  Returns the compounds written.

    The block is swapped for the one the record produces, so a re-collection
    reaches the page with one command and a hand-edited page is visibly
    overwritten rather than silently kept (``test_every_page_carries_the_
    generated_block`` fails first anyway).
    """

    written: list[str] = []
    for entry in report["compounds"]:
        page = repo_root / "publication" / page_filename(entry["compound"])
        if not page.is_file():
            continue
        html = page.read_text(encoding="utf-8")
        replaced = replace_block(html, entry["block"])
        if replaced != html:
            page.write_text(replaced, encoding="utf-8")
            written.append(entry["compound"])
    return written


def cmd_gt_summary(args) -> int:
    """Recompute the Google Trends summary the publication pages show.

    A value the run record cannot support is reported as 算出不能
    (with the missing input named) instead of being recomputed from nothing;
    ``--html`` prints the block to paste into a page and ``--write`` replaces
    the block in the page itself.  See ``processing/gt_statistics.py`` for the
    record shapes and the limits.
    """
    compounds = (
        [args.compound.upper()] if args.compound else list(PUBLICATION_COMPOUNDS)
    )
    timeframe = TIMEFRAMES[args.timeframe]
    try:
        report = build_gt_summary(Path(args.datasets_root), compounds, timeframe)
    except (OSError, ValueError) as error:
        _err(f"gt summary failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dump_json(report), encoding="utf-8")

    if args.write:
        written = _write_page_blocks(report, Path(args.repo_root))
        _err(f"updated {len(written)} page(s): {', '.join(written) or 'none'}")

    if args.html:
        for entry in report["compounds"]:
            print(entry["block"], end="")
    elif args.format == "json":
        print(dump_json(report), end="")
    else:
        for entry in report["compounds"]:
            if entry["status"] == "not_collected":
                print(f"{entry['compound']:6} not collected ({report['timeframe']})")
                continue
            stats = entry["stats"]
            print(
                f"{entry['compound']:6} {entry['shape']:8} run={entry['run_id']}\n"
                f"        weeks={stats.get('weeks')} mean={stats.get('mean')} "
                f"peak={stats.get('peak_date')} last={stats.get('last_value')}"
            )
            for field, reason in sorted(entry["unavailable"].items()):
                print(f"        {field}: {reason}")
    summary = report["summary"]
    _err(
        f"gt summary ({report['timeframe']}): {summary['compound_count']} compound(s) "
        f"[{', '.join(f'{k}={v}' for k, v in summary['by_status'].items())}] "
        f"mean unavailable={len(summary['unavailable_mean'])}"
    )
    return EXIT_OK


def cmd_youtube_export(args) -> int:
    try:
        result = build_video_export(args.study_dir)
        paths = write_export(result, args.output_dir)
    except OSError as error:
        _err(f"youtube export failed: {error}")
        return EXIT_IO
    summary = {
        "study_dir": args.study_dir,
        "output_dir": args.output_dir,
        "exported_run_count": len(result["runs"]),
        "video_row_count": len(result["videos"]),
        "withheld_run_count": len(result["withheld"]),
        "withheld": result["withheld"],
        "written": [str(path) for path in paths],
    }
    if args.format == "json":
        print(dump_json(summary), end="")
    else:
        print(
            f"youtube export written: {args.output_dir} "
            f"exported_runs={summary['exported_run_count']} "
            f"videos={summary['video_row_count']} "
            f"withheld_runs={summary['withheld_run_count']} (not written)"
        )
    return EXIT_OK


def cmd_youtube_monthly_aggregate(args) -> int:
    try:
        rows, diagnostics = build_youtube_monthly_aggregate(
            args.study_dir, run_id=args.run_id
        )
        path = write_youtube_monthly_aggregate(rows, args.output)
    except YouTubeAggregationError as error:
        _err(f"YouTube monthly aggregation failed: {error}")
        return EXIT_DATA
    except OSError as error:
        _err(f"YouTube monthly aggregation failed: {error}")
        return EXIT_IO

    print(
        f"YouTube monthly aggregate written: {path} "
        f"raw_records={diagnostics['raw_record_count']} "
        f"distinct_videos={diagnostics['distinct_video_count']} "
        f"duplicates_removed={diagnostics['duplicates_removed']} "
        f"months={diagnostics['month_count']} "
        f"input_sha256={diagnostics['input_sha256']}"
    )
    return EXIT_OK


def cmd_gt_legacy_label_corrections(args) -> int:
    try:
        manifest = write_gt_legacy_label_corrections(
            args.repo_root,
            args.output,
        )
    except (OSError, ValueError) as error:
        _err(f"gt legacy label corrections failed: {error.__class__.__name__}: {error}")
        return EXIT_CONFIG if isinstance(error, ValueError) else EXIT_IO
    if args.format == "json":
        print(dump_json(manifest), end="")
    else:
        summary = manifest["summary"]
        print(
            "gt legacy label correction manifest written: "
            f"{args.output} affected_file_count={summary['affected_file_count']} "
            f"raw_files_modified={summary['raw_files_modified']}"
        )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m processing.cli")
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser(
        "audit-processed", help="audit committed data/processed artifacts"
    )
    audit.add_argument("--datasets-root", default="datasets")
    audit.add_argument("--output", default=None)
    audit.add_argument("--format", choices=("text", "json"), default="text")
    audit.set_defaults(func=cmd_audit_processed)

    reproduce = sub.add_parser("reproduce", help="re-derive one artifact")
    reproduce.add_argument("--artifact", required=True)
    reproduce.add_argument("--format", choices=("text", "json"), default="text")
    reproduce.set_defaults(func=cmd_reproduce)

    classify = sub.add_parser("classify", help="classify one text")
    classify.add_argument("--text", required=True)
    classify.add_argument("--format", choices=("text", "json"), default="text")
    classify.set_defaults(func=cmd_classify)

    platform = sub.add_parser(
        "build-platform-trends",
        help="build Google Trends + YouTube cross-platform release tables (X excluded)",
    )
    platform.add_argument(
        "--output-dir",
        default="datasets/cannabinoid-platform-trends/data/processed",
    )
    platform.add_argument("--format", choices=("text", "json"), default="text")
    platform.set_defaults(func=cmd_build_platform_trends)

    aggregate = sub.add_parser(
        "aggregate-x",
        help=("weekly/monthly group counts from the private per-post X input"),
    )
    aggregate.add_argument("--input", required=True)
    aggregate.add_argument("--weekly-out", default=None)
    aggregate.add_argument("--monthly-out", default=None)
    aggregate.add_argument("--monthly-coarse-out", default=None)
    aggregate.add_argument("--compound", default=COMPOUND_DEFAULT)
    aggregate.add_argument("--report", default=None)
    aggregate.set_defaults(func=cmd_aggregate_x)

    gt_summary = sub.add_parser(
        "gt-summary",
        help=(
            "recompute the Google Trends summary for the publication pages "
            "(--html prints the block, --write puts it in the page)"
        ),
    )
    gt_summary.add_argument("--datasets-root", default="datasets")
    gt_summary.add_argument("--timeframe", choices=tuple(TIMEFRAMES), default="5y")
    gt_summary.add_argument("--compound", default=None)
    gt_summary.add_argument("--html", action="store_true")
    gt_summary.add_argument(
        "--write",
        action="store_true",
        help="replace each page's 5-year block with the generated one",
    )
    gt_summary.add_argument("--output", default=None)
    gt_summary.add_argument("--format", choices=("text", "json"), default="text")
    gt_summary.set_defaults(func=cmd_gt_summary)

    youtube_export = sub.add_parser(
        "youtube-export",
        help=(
            "write the aggregate-only YouTube view (per-video id/title/channel; "
            "the raw stays local)"
        ),
    )
    youtube_export.add_argument(
        "--study-dir", default="datasets/cannabinoid-raw-collection"
    )
    youtube_export.add_argument(
        "--output-dir",
        default="datasets/cannabinoid-raw-collection/data/processed",
    )
    youtube_export.add_argument("--format", choices=("text", "json"), default="text")
    youtube_export.set_defaults(func=cmd_youtube_export)

    youtube_monthly = sub.add_parser(
        "youtube-monthly-aggregate",
        help="aggregate the adopted HHBD YouTube run by UTC publication month",
    )
    youtube_monthly.add_argument(
        "--study-dir", default="datasets/cannabinoid-raw-collection"
    )
    youtube_monthly.add_argument(
        "--run-id",
        default="20261010T141947Z-youtube-cannabinoid-raw-collection",
    )
    youtube_monthly.add_argument(
        "--output",
        default=(
            "datasets/cannabinoid-raw-collection/data/processed/"
            "youtube_monthly_counts.csv"
        ),
    )
    youtube_monthly.set_defaults(func=cmd_youtube_monthly_aggregate)

    gt_corrections = sub.add_parser(
        "gt-legacy-label-corrections",
        help="write the interim manifest for frozen GT legacy label corrections",
    )
    gt_corrections.add_argument(
        "--output",
        default=(
            "datasets/cannabinoid-raw-collection/data/interim/google_trends/"
            "20261015_gt_legacy_label_corrections.json"
        ),
    )
    gt_corrections.add_argument("--format", choices=("text", "json"), default="text")
    gt_corrections.set_defaults(func=cmd_gt_legacy_label_corrections)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
