"""Check that a release archive's embedded metadata matches the release.

Why this exists
---------------
v1.13.0 shipped a GitHub Release whose clean archive advertised the previous
(Zenodo) DOI instead of the DOI of the release it was shipped in, because the
DOI was only known after the archive was built (ISS-20261015-REL-015).  The
archive is immutable once published, so the check has to run *before* upload:
the workflow extracts CITATION.cff / metadata/datapackage.json / README.md
from the zip and compares them with the expected release identity.

Record-only, exit 1 on any mismatch:

- version in CITATION.cff / datapackage.json == the release tag version;
- the expected concept DOI is cited by CITATION.cff (identifiers +
  preferred-citation) and by datapackage.json (.doi and citation);
- README's DOI badge is the expected concept DOI;
- the archive carries no disallowed path (.github, credentials, legacy
  per-post X study directories, private data).

Usage:
  python scripts/validation/check-release-archive.py \
      --archive release-archives/japan-cannabinoid-trends-v1.13.2-clean.zip \
      --version 1.13.2 \
      --concept-doi 10.5281/zenodo.23390594
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile

DOI_RE = re.compile(r"10\.5281/zenodo\.[0-9]+")

#: Paths that must never ship in a clean archive (top-level prefixes or exact).
DISALLOWED_PREFIXES = (
    ".github/",
    ".serena/",
    ".opencode/",
    "artifacts/",
    "datasets/cbx-social-trends/",
    "datasets/youtube-consistency/",
    "datasets/x-consistency/",
    "data/private/",
)
DISALLOWED_EXACT = {
    ".env", ".env.local", "opencode.json", "project.json", "project.yml",
    ".gitignore",
}


def _fail(message: str) -> "list[str]":
    return [message]


def check_archive(archive: str, version: str, concept_doi: str) -> list[str]:
    """Return the list of problems; empty list == archive is shippable."""
    problems: list[str] = []
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()

        # 1. disallowed paths
        for name in names:
            if name in DISALLOWED_EXACT or name.startswith(DISALLOWED_PREFIXES):
                problems.append(f"disallowed path in archive: {name}")
            if name.endswith("/agent.md") or name == "agent.md":
                problems.append(f"agent file in archive: {name}")

        def read(path: str) -> str:
            return zf.read(path).decode("utf-8")

        # 2. CITATION.cff
        if "CITATION.cff" not in names:
            problems.append("CITATION.cff missing from archive")
        else:
            cff = read("CITATION.cff")
            match = re.search(r'^version:\s*"([^"]+)"', cff, re.M)
            if not match:
                problems.append("CITATION.cff has no version field")
            elif match.group(1) != version:
                problems.append(
                    f"CITATION.cff version {match.group(1)!r} != release version {version!r}"
                )
            cff_dois = set(DOI_RE.findall(cff))
            if concept_doi not in cff_dois:
                problems.append(
                    f"CITATION.cff does not cite the expected concept DOI {concept_doi}; "
                    f"found {sorted(cff_dois) or 'none'}"
                )
            # preferred-citation must pin the concept DOI too
            pref = cff.split("preferred-citation:", 1)
            if len(pref) == 2 and concept_doi not in DOI_RE.findall(pref[1]):
                problems.append(
                    f"CITATION.cff preferred-citation does not cite {concept_doi}"
                )

        # 3. datapackage.json
        if "metadata/datapackage.json" not in names:
            problems.append("metadata/datapackage.json missing from archive")
        else:
            dp = json.loads(read("metadata/datapackage.json"))
            if dp.get("version") != version:
                problems.append(
                    f"datapackage.json version {dp.get('version')!r} != release version {version!r}"
                )
            dp_dois = set(DOI_RE.findall(json.dumps(dp.get("citation", ""))))
            if dp.get("doi"):
                dp_dois.add(dp["doi"])
            if concept_doi not in dp_dois:
                problems.append(
                    f"datapackage.json does not cite the expected concept DOI {concept_doi}"
                )

        # 4. README badge
        if "README.md" not in names:
            problems.append("README.md missing from archive")
        else:
            badge = DOI_RE.findall(read("README.md"))
            if not badge:
                problems.append("README.md has no DOI badge")
            elif concept_doi not in badge:
                problems.append(
                    f"README.md badge {badge[0]} != expected concept DOI {concept_doi}"
                )
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", required=True)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.13.2")
    parser.add_argument(
        "--concept-doi", required=True, help="expected Zenodo concept DOI"
    )
    args = parser.parse_args(argv)
    if not DOI_RE.fullmatch(args.concept_doi):
        print(f"invalid --concept-doi: {args.concept_doi}", file=sys.stderr)
        return 2
    problems = check_archive(args.archive, args.version, args.concept_doi)
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        print(
            f"release archive check: {len(problems)} problem(s)", file=sys.stderr
        )
        return 1
    print(
        f"release archive check OK: version {args.version}, concept DOI {args.concept_doi}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
