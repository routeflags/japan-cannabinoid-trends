"""X (Twitter) identity exposure gate over tracked files.

Policy (decided 2026-10-13, enforced here):

- X post text, account handles, display names and post permalinks must not be
  tracked.  Publish the anonymized derivation instead
  (``x_cbx_202608_summary_anonymized.csv``) plus the executable rule
  (:mod:`processing.anonymize`).
- YouTube metadata is out of scope: ``docs/specs/sns-redistribution-assessment.md``
  section 2 permits video titles and channel names.

Why this gate exists: the repository had already written that policy down.  The
assessment (2026-10-01) and ``docs/data-dictionary.md`` section 1.1 both required
X handles and text to stay out of DOI archives, and
``datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv`` shipped in
all 14 release archives anyway, because nothing checked.  A documented rule
without an executable check is what failed, so the check is the fix.

Detection is deliberately narrow, because a noisy gate gets switched off:

- ``identity_column`` -- a tracked CSV/TSV whose header names an identity column;
- ``post_permalink`` -- an ``x.com/<handle>/status/<id>`` link, i.e. redistributed
  post data.  Documentation placeholders (``x.com/user/status/123``) are excluded
  by :data:`PLACEHOLDER_HANDLES`, which is a rule about placeholder literals, not a
  per-file exception;
- ``known_handle`` -- any token whose salted digest is in
  ``metadata/privacy/x-identity-denylist.json``.  The denylist stores digests only,
  so the gate catches re-publication of the same accounts without the repository
  carrying the handles a second time in plaintext.

Display names are deliberately not in the denylist: the withdrawn collection
contained 1-character display names (``'R'``, ``'s'``) that match almost any text,
so digest matching on them would produce only false positives.

Acknowledgements keep a rule-based gate usable without pretending a real finding
is not there: each entry names the file, the digest, and why it is acceptable, and
an acknowledgement that no longer matches anything is itself a failure.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

from validation.storage_policy import git_tracked

__all__ = [
    "AUDIT_VERSION",
    "DEFAULT_DENYLIST",
    "TEXT_SUFFIXES",
    "IDENTITY_COLUMNS",
    "PLACEHOLDER_HANDLES",
    "ACKNOWLEDGED",
    "audit_x_identity",
    "digest_token",
]

AUDIT_VERSION = "1.0.0"

#: Repository-relative location of the salted digest denylist.
DEFAULT_DENYLIST = "metadata/privacy/x-identity-denylist.json"

#: Extensions that are always scanned.  Files outside this set are still scanned
#: when they decode as NUL-free UTF-8, so a handle cannot hide in a suffixless
#: text file such as ``.gitignore``; :data:`TEXT_SUFFIXES` only documents the
#: intended text surface and keeps the report readable.
TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".html",
        ".htm",
        ".csv",
        ".tsv",
        ".json",
        ".jsonld",
        ".yaml",
        ".yml",
        ".cff",
        ".txt",
        ".py",
        ".sh",
        ".sql",
        ".ttl",
        ".toml",
    }
)

#: CSV/TSV header names that mean 'this column identifies an account'.
IDENTITY_COLUMNS = frozenset(
    {"username", "author_name", "screen_name", "display_name", "user_name", "screenname"}
)

#: Handles used in documentation examples.  A permalink on one of these is an
#: illustration, not redistributed post data.
PLACEHOLDER_HANDLES = frozenset({"user", "example", "handle", "username", "screen_name"})

_PERMALINK = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/\d+", re.IGNORECASE
)
_TOKEN = re.compile(r"[A-Za-z0-9_]{4,30}")

#: Digest of the one account from the withdrawn X collection that also appears in
#: the YouTube results.  Written as a digest for the same reason as the denylist.
_YOUTUBE_ACCOUNT_DIGEST = (
    "3bafabd2efa0f9f0e05dd8307949f528e1c65b45e198711f1d271128576562de"
)

#: ``(path, digest)`` -> reason.  A gate with an allowlist is only honest if the
#: exceptions are visible and reviewed, so each one is justified in place and
#: checked for staleness.  Entries are keyed by digest rather than by handle so
#: that acknowledging an account does not write the handle back into the
#: repository that this gate is meant to keep it out of.
ACKNOWLEDGED: dict[tuple[str, str], str] = {
    (
        "datasets/cbx-social-trends/data/processed/youtube_filtered_202607/records_filtered.csv",
        _YOUTUBE_ACCOUNT_DIGEST,
    ): (
        "Appears in a YouTube video title in the filtered YouTube results, not in "
        "redistributed X post data.  docs/specs/sns-redistribution-assessment.md "
        "section 2 permits video titles and channel names, and the maintainer "
        "decided on 2026-10-13 to leave YouTube data unchanged."
    ),
    (
        "datasets/cbx-social-trends/data/processed/youtube_filtered_202607/records_filtered.json",
        _YOUTUBE_ACCOUNT_DIGEST,
    ): (
        "Same occurrence as the CSV variant: a YouTube video title, permitted by "
        "sns-redistribution-assessment.md section 2."
    ),
}


def digest_token(token: str, salt: str) -> str:
    """Return ``sha256(salt + U+001F + lowercased token)`` in hex."""

    return hashlib.sha256((salt + "\x1f" + token.strip().lower()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _Denylist:
    salt: str
    digests: frozenset[str]
    account_count: int


def _load_denylist(path: Path) -> _Denylist:
    document = json.loads(path.read_text(encoding="utf-8"))
    return _Denylist(
        salt=document["salt"],
        digests=frozenset(document["digests"]),
        account_count=int(document.get("account_count", len(document["digests"]))),
    )


def _tracked_files(root: Path) -> list[str]:
    """Repository-relative tracked paths, intended-text files first."""

    intended: list[str] = []
    rest: list[str] = []
    for line in _git_ls_files(root):
        (intended if Path(line).suffix.lower() in TEXT_SUFFIXES else rest).append(line)
    return intended + rest


def _git_ls_files(root: Path) -> list[str]:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"], cwd=str(root), capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def _read_text(path: Path) -> str | None:
    """Return the file's text, or ``None`` when it is not NUL-free UTF-8."""

    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _identity_columns(text: str, suffix: str) -> list[str]:
    if suffix not in {".csv", ".tsv"}:
        return []
    delimiter = "\t" if suffix == ".tsv" else ","
    first_line = text.splitlines()[0] if text.splitlines() else ""
    try:
        header = next(csv.reader(io.StringIO(first_line), delimiter=delimiter))
    except (StopIteration, csv.Error):
        return []
    return sorted(
        name.strip().strip('"').lower()
        for name in header
        if name.strip().strip('"').lower() in IDENTITY_COLUMNS
    )


def _permalinks(text: str) -> list[str]:
    found = set()
    for match in _PERMALINK.finditer(text):
        if match.group(1).lower() not in PLACEHOLDER_HANDLES:
            found.add(match.group(0))
    return sorted(found)


def audit_x_identity(
    root: str | Path,
    *,
    denylist_path: str | Path = DEFAULT_DENYLIST,
    files: list[str] | None = None,
) -> dict:
    """Audit tracked files for X identity exposure.

    Read-only.  Returns a report; callers decide what to do with ``findings``.
    ``files`` overrides the tracked-file list (repository-relative paths), which
    lets tests exercise the gate without creating throwaway git repositories.
    """

    root = Path(root).resolve()
    denylist_file = Path(denylist_path)
    if not denylist_file.is_absolute():
        denylist_file = root / denylist_file
    denylist = _load_denylist(denylist_file)

    scanned_candidates = _tracked_files(root) if files is None else list(files)
    contents: dict[str, str] = {}
    tokens: dict[str, set[str]] = {}
    unique_tokens: set[str] = set()
    skipped: list[str] = []
    for relative in scanned_candidates:
        text = _read_text(root / relative)
        if text is None:
            skipped.append(relative)
            continue
        contents[relative] = text
        found = set(_TOKEN.findall(text))
        tokens[relative] = found
        unique_tokens |= found

    flagged = {
        token
        for token in unique_tokens
        if digest_token(token, denylist.salt) in denylist.digests
    }

    findings: list[dict] = []
    matched_acknowledgements: set[tuple[str, str]] = set()

    for relative in sorted(contents):
        text = contents[relative]
        suffix = Path(relative).suffix.lower()

        columns = _identity_columns(text, suffix)
        if columns:
            findings.append(
                {
                    "path": relative,
                    "kind": "identity_column",
                    "detail": ", ".join(columns),
                }
            )

        links = _permalinks(text)
        if links:
            findings.append(
                {
                    "path": relative,
                    "kind": "post_permalink",
                    "detail": f"{len(links)} link(s)",
                }
            )

        for token in sorted(tokens[relative] & flagged):
            digest = digest_token(token, denylist.salt)
            key = (relative, digest)
            if key in ACKNOWLEDGED:
                matched_acknowledgements.add(key)
                continue
            findings.append(
                {"path": relative, "kind": "known_handle", "detail": digest}
            )

    stale = [
        {"path": path, "digest": digest, "reason": reason}
        for (path, digest), reason in sorted(ACKNOWLEDGED.items())
        if (path, digest) not in matched_acknowledgements
    ]

    return {
        "audit_version": AUDIT_VERSION,
        "root": str(root),
        "denylist": str(denylist_file.relative_to(root))
        if denylist_file.is_relative_to(root)
        else str(denylist_file),
        "account_count": denylist.account_count,
        "scanned_count": len(contents),
        "skipped": sorted(skipped),
        "finding_count": len(findings),
        "findings": findings,
        "acknowledged": [
            {"path": path, "digest": digest, "reason": ACKNOWLEDGED[(path, digest)]}
            for path, digest in sorted(matched_acknowledgements)
        ],
        "stale_acknowledgements": stale,
        "failures": [f["path"] for f in findings] + [s["path"] for s in stale],
    }


def main(argv: list[str] | None = None) -> int:
    """Stdlib-only entry point: ``python3 -m validation.x_identity``.

    The pre-commit hook runs before a virtualenv can be assumed, and
    ``validation.cli`` pulls in cerberus (via ``validation.core``), so the hook
    calls this module directly.  CI uses ``python -m validation.cli
    audit-x-identity``, which exposes the same report.

    Exit codes: 0 clean, 1 findings, 2 unusable denylist, 3 I/O.
    """

    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="python -m validation.x_identity")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--denylist", default=DEFAULT_DENYLIST)
    args = parser.parse_args(argv)

    try:
        report = audit_x_identity(args.repo_root, denylist_path=args.denylist)
    except (json.JSONDecodeError, KeyError) as error:
        print(f"denylist is unusable: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"cannot scan: {error}", file=sys.stderr)
        return 3

    for finding in report["findings"]:
        print(f"{finding['kind']:16} {finding['path']}  {finding['detail']}")
    for stale in report["stale_acknowledgements"]:
        print(f"stale_acknowledgement  {stale['path']}  {stale['digest'][:16]}…")
    print(
        f"x identity audit: scanned={report['scanned_count']} "
        f"findings={report['finding_count']} "
        f"acknowledged={len(report['acknowledged'])} "
        f"stale_acknowledgements={len(report['stale_acknowledgements'])}",
        file=sys.stderr,
    )
    return 1 if report["failures"] else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
