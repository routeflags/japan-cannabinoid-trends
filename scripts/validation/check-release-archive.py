#!/usr/bin/env python3
"""CLI for scripts/validation/check-release-archive.py (release identity gate)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from validation.release_archive_check import DOI_RE, check_archive  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", required=True)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.13.2")
    parser.add_argument("--concept-doi", required=True, help="expected Zenodo concept DOI")
    args = parser.parse_args(argv)
    if not DOI_RE.fullmatch(args.concept_doi):
        print(f"invalid --concept-doi: {args.concept_doi}", file=sys.stderr)
        return 2
    problems = check_archive(args.archive, args.version, args.concept_doi)
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        print(f"release archive check: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"release archive check OK: version {args.version}, concept DOI {args.concept_doi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
