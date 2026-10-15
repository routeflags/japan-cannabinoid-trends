#!/usr/bin/env python3
"""Generate a release-manifest-v1 document (validation input only).

The manifest declares the intended release identity and archive scope so
``python -m validation.cli validate-release-manifest`` can check the built
clean archive before the Zenodo upload step (ISS-20261015-REL-014).  The
include roots, required paths, and forbidden paths come from the single
source of truth in ``validation.release_manifest`` (which mirrors
``INCLUDE_PATHS`` and reuses the canonical ``DISALLOWED_*`` policy); this
script only binds them to one version / concept DOI / archive path.

Validation only: this script never publishes, pushes, uploads, or modifies
``release-archives/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from validation.release_archive_check import DOI_RE  # noqa: E402
from validation.release_manifest import default_manifest  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True, help="release version, e.g. 1.13.2")
    parser.add_argument("--concept-doi", required=True, help="expected Zenodo concept DOI")
    parser.add_argument("--archive", required=True, help="archive path recorded in the manifest")
    parser.add_argument("--output", help="write the manifest JSON here (default: stdout)")
    args = parser.parse_args(argv)
    if not DOI_RE.fullmatch(args.concept_doi):
        print(f"invalid --concept-doi: {args.concept_doi}", file=sys.stderr)
        return 2
    manifest = default_manifest(
        version=args.version,
        concept_doi=args.concept_doi,
        archive_path=args.archive,
    )
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
