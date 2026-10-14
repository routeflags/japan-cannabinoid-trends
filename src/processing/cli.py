"""Processing CLI:

- ``audit-processed``  every committed ``data/processed`` artifact is either
  verifiably re-derivable or explicitly declared non-reproducible
- ``classify``         classify one text against the content taxonomy notations

The Python API (:mod:`processing.reproduce`, :mod:`processing.classify`) is the
primary interface; this CLI exposes it for operators and CI.

Exit codes follow the repository convention (``docs/specs/validation-framework.md``):
``0`` success, ``1`` data/audit failure, ``2`` configuration error, ``3`` I/O.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from processing.classify import classify_text
from processing.gt_statistics import (
    PUBLICATION_COMPOUNDS,
    TIMEFRAMES,
    build_gt_summary,
    page_filename,
    replace_block,
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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
