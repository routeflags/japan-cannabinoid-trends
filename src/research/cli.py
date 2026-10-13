"""Research catalog CLI (G7 \u00a713, target interface).

Python API (``research.catalog`` / ``research.comparability`` /
``research.views``) is the primary interface; this CLI exposes the same
operations for researchers.  No REST API / web UI (not required, \u00a713).

Commands:

- ``catalog-find``   cross-study discovery (P4: discovery-only)
- ``compare``        cross-study comparability gate for two catalog entries
- ``build-view``     reproducible parallel-timeseries research view
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research import catalog as _catalog
from research import audit as _audit
from research import comparability as _gate
from research import views as _views
from research.views import refuse_raw_output
from validation.reporting import dump_json

EXIT_OK = 0
EXIT_DATA = 1
EXIT_CONFIG = 2
EXIT_IO = 3


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def cmd_catalog_find(args) -> int:
    try:
        catalog = _catalog.build_catalog(args.datasets_root, repo_root=args.repo_root)
    except OSError as error:
        _err(f"catalog build failed: {error}")
        return EXIT_IO
    result = _catalog.find_artifacts(
        catalog,
        compound_id=args.compound,
        source_id=args.source,
        study_id=args.study,
        measurement_id=args.measurement,
        start=args.start,
        end=args.end,
    )
    if args.format == "json":
        print(dump_json(result), end="")
    else:
        for entry in result["entries"]:
            print(f"{entry.get('study_id')} {entry.get('run_id')} {entry.get('source_id')} {entry.get('compound_ids')}")
        print(f"{result['match_count']} match(es). {result['discovery_note']}")
    return EXIT_OK


def cmd_compare(args) -> int:
    try:
        catalog = _catalog.build_catalog(args.datasets_root, repo_root=args.repo_root)
    except OSError as error:
        _err(f"catalog build failed: {error}")
        return EXIT_IO
    by_id = {e["catalog_entry_id"]: e for e in catalog["entries"] if isinstance(e, dict)}
    missing = [i for i in (args.entry_a, args.entry_b) if i not in by_id]
    if missing:
        _err(f"unknown catalog entry: {', '.join(missing)}")
        return EXIT_CONFIG
    verdict = _gate.check_cross_study_comparability(by_id[args.entry_a], by_id[args.entry_b])
    if args.format == "json":
        print(dump_json(verdict), end="")
    else:
        print(f"{verdict['status']}: {', '.join(verdict['reasons'])}")
    return EXIT_OK


def cmd_build_view(args) -> int:
    try:
        definition = _load_json(Path(args.definition))
        series_doc = _load_json(Path(args.series))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        _err(f"cannot read input: {error}")
        return EXIT_IO
    series = series_doc.get("series") if isinstance(series_doc, dict) else None
    if not isinstance(series, list) or not series:
        _err("series file must hold a non-empty 'series' list")
        return EXIT_CONFIG
    try:
        catalog = _catalog.build_catalog(args.datasets_root, repo_root=args.repo_root)
    except OSError as error:
        _err(f"catalog build failed: {error}")
        return EXIT_IO
    try:
        summary = _views.build_view(definition, series, catalog, repo_root=args.repo_root, out_dir=args.out_dir)
    except ValueError as error:
        _err(str(error))
        return EXIT_DATA
    except OSError as error:
        _err(f"view build failed: {error}")
        return EXIT_IO
    if args.format == "json":
        print(dump_json(summary), end="")
    else:
        print(f"view written to {summary['out_dir']}: {summary['row_count']} row(s), {summary['series_count']} series")
    return EXIT_OK


def cmd_audit_studies(args) -> int:
    try:
        inventory = _audit.build_study_inventory(args.datasets_root, repo_root=args.repo_root)
    except OSError as error:
        _err(f"study audit failed: {error}")
        return EXIT_IO
    if args.output:
        try:
            path = Path(args.output)
            refuse_raw_output(path, Path(args.repo_root))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(dump_json(inventory) + "\n", encoding="utf-8")
        except ValueError as error:
            _err(str(error))
            return EXIT_DATA
        except OSError as error:
            _err(f"cannot write output: {error}")
            return EXIT_IO
        _err(
            f"study inventory written: {args.output} "
            f"({inventory['study_count']} studie(s), raw_modified={inventory['raw_modified']})"
        )
    else:
        print(dump_json(inventory), end="")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research", description="G7 federated research catalog")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--datasets-root", default="datasets")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    sub = parser.add_subparsers(dest="command", required=True)

    find = sub.add_parser("catalog-find", help="cross-study discovery (finding is not comparing)")
    find.add_argument("--compound", default=None)
    find.add_argument("--source", default=None)
    find.add_argument("--study", default=None)
    find.add_argument("--measurement", default=None)
    find.add_argument("--start", default=None)
    find.add_argument("--end", default=None)
    find.set_defaults(handler=cmd_catalog_find)

    compare = sub.add_parser("compare", help="cross-study comparability gate for two entries")
    compare.add_argument("--entry-a", required=True)
    compare.add_argument("--entry-b", required=True)
    compare.set_defaults(handler=cmd_compare)

    view = sub.add_parser("build-view", help="build a parallel-timeseries research view")
    view.add_argument("--definition", required=True)
    view.add_argument("--series", required=True)
    view.add_argument("--out-dir", required=True)
    view.set_defaults(handler=cmd_build_view)

    audit = sub.add_parser("audit-studies", help="non-destructive existing-study inventory (G7 16)")
    audit.add_argument("--output", default="docs/audits/g7-study-inventory.json")
    audit.set_defaults(handler=cmd_audit_studies)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
