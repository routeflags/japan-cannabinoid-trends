"""Cost must not be recorded in tracked documents, data, or configuration.

Contract source: ``AGENTS.md`` (Scope Exclusion: Cost).  The study does not
measure what its collection costs, so a monetary amount or a cost field in a
tracked artifact is a defect, not a detail: it is copied into publications,
it ages as soon as a provider changes a price, and it invites readers to treat
vendor pricing as part of the method.

What the scan deliberately leaves alone (see ``AGENTS.md`` for the rule):

- ``.github/skills/`` and ``.github/agents/`` -- vendor price references kept
  to run a paid collector, not study records;
- statutory penalties, product prices and advertising metrics, which are
  observed research data of their own dataset (listed in ``EXCEPTIONS``);
- collector code that classifies payment failures (HTTP 402, exhausted
  credits): that is a request state, not a cost figure.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Directories whose content is a study or its documentation.
SCANNED_SUFFIXES = frozenset(
    {".md", ".json", ".jsonld", ".csv", ".yaml", ".yml", ".txt", ".html", ".cff"}
)

#: Paths that are out of scope for the ban, with the reason each one is.
UNSCANNED_PREFIXES = {
    ".github/skills/": "vendor price references for running a paid collector",
    ".github/agents/": "agent instructions that mirror those skills",
    "data/raw/": "immutable raw observations",
    ".quarantine/": "raw payloads that were never adopted",
    "docs/audits/": "generated audit snapshots of repository state",
    "tests/": "the check's own patterns and fixtures",
}

#: Individual files that carry monetary values as observed research data.
EXCEPTIONS = {
    "datasets/cbx-social-trends/analysis/cbx_data_collection_report.md": (
        "CPC (advertising cost per click) is an observed keyword metric, not "
        "this study's collection cost"
    ),
    "publication/guide_cbx_rewrite.html": (
        "the public guide repeats the same observed CPC values"
    ),
    "AGENTS.md": "the rule itself has to name the fields it forbids",
    "docs/specs/collection-pipeline.md": (
        "the staging spec forbids cost fields in ``environment`` by name"
    ),
}

#: Patterns that mean "a cost was recorded".
PATTERNS = {
    "currency amount": re.compile(r"\$\s?\d*\.\d+"),
    "yen amount": re.compile(r"[¥￥]\s?\d"),
    "US dollar unit": re.compile(r"\bUSD\b"),
    "cost field": re.compile(
        r"\bcost_usd\b|\busageTotalUsd\b|\bcostPerCompound\b|\bcostEstimate\b"
    ),
    "cost record heading": re.compile(
        r"コスト目安|コスト見積|費用見積|費用サマリー|コスト実績|収集コスト|"
        r"総コスト|請求実績|予算上限|予算配分|予算超過|課金単価|月額合計"
    ),
}


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _scanned_files() -> list[str]:
    selected = []
    for relative in _tracked_files():
        if relative in EXCEPTIONS:
            continue
        if any(relative.startswith(prefix) for prefix in UNSCANNED_PREFIXES):
            continue
        if Path(relative).suffix in SCANNED_SUFFIXES:
            selected.append(relative)
    return selected


def _scan(text: str) -> list[tuple[str, int, str]]:
    found = []
    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            found.append((label, line, text.splitlines()[line - 1].strip()))
    return found


def test_no_tracked_artifact_records_a_cost() -> None:
    problems = []
    for relative in _scanned_files():
        path = REPO_ROOT / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, line, excerpt in _scan(text):
            problems.append(f"{relative}:{line}: {label}: {excerpt[:120]}")
    assert problems == [], (
        "cost must not be recorded in tracked artifacts (AGENTS.md Scope "
        "Exclusion: Cost):\n" + "\n".join(problems)
    )


def test_scan_reports_a_cost_when_one_is_present() -> None:
    """The check has to fail on a real violation, not merely pass."""

    assert _scan("| 収集 | 費用 |\n| X | $0.80 |") != []
    assert _scan("{\"usageTotalUsd\": \"1.19\"}") != []
    assert _scan("| ソース | コスト目安 |\n| X | 約 2 ドル |") != []
    assert _scan("the quote length is 100 units") == []
