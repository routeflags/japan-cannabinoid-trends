"""Publication contract (``docs/specs/contracts.md``): the requirements a
published artifact must satisfy.

Why this exists
---------------
The publication layer was outside the contract framework, so the artifacts
could drift from the release and from the data policy without anything
noticing (measured 2026-10-15: 13 pages still cited ``Version 1.9.0`` and the
old DOI; 7 pages lacked the required 5-year Google Trends table; every page
carried a duplicate section id; and the page validator that was supposed to
catch this could not).  This module is the single implementation of the rules;
``scripts/validation/validate-research-pages.py`` had an inert copy (its depth
rules were unreachable and its data paths did not exist) and was removed.

Record-only
-----------
The rules need a content refresh to pass (phase 4 of
``docs/reports/20261015c-publication-refresh-plan.md``), so this audit records
findings and exits 0 - the same treatment as ``gate-publication`` and
``boundary-report``.  Making it fatal is a separate decision; the committed
report and ``tests/validation/test_publication_contract.py`` keep the findings
from going unnoticed until then.

Implemented (mechanical only, no judgement)
-------------------------------------------
- PC-1 release version and DOI: a publication artifact must present the
  release the repository currently publishes (``CITATION.cff`` /
  ``metadata/datapackage.json`` are the declaration).
- PC-3 policy-out sources: a page citing ``YouTube Data API`` must also record
  that the source was retired by the 2026-10-12 decision; a page must not
  express per-post X data (permalink, handle, or a list of post-record
  fields).  See ``ISS-20261015-XID-034``.
- PC-4 declared metadata: ``dateModified`` and ``最終更新`` must agree.
- PC-5 section requirements on the research pages (``research_*.html``):
  Google Trends needs both the 12-month and the 5-year table, X needs the
  confidence interval, each YouTube section needs its depth (two or more
  tables).  The requirement comes from the research-page generator contract
  (``.github/skills/generate-research-data-page/SKILL.md``); the guide follows
  its own generator (``generate-compound-guide``) whose requirements are not
  encoded as a check yet (PC-8 below).
- PC-6 HTML validity: section ids must be unique.

Deliberately not implemented (named, so the gap cannot be silent):

- PC-2 (every published number traceable to a run id) - needs the content
  refresh; the pages currently name collection dates only.
- PC-7 (a review envelope per artifact) - needs the review records.
- PC-8 (the guide's own structure requirements) - the guide is not a research
  page, so PC-5 does not apply to it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPORT_SCHEMA_VERSION = "1.0.0"

#: The note a page must carry when it cites the retired YouTube Data API v3.
V3_POLICY_MARKER = "方針判断により使用を取り止め"

#: Post-record fields from the now banned per-post X dataset.  Naming three or
#: more of them in one paragraph describes the post-record shape, which the
#: 2026-10-15 decision bans together with storage (ISS-20261015-XID-034).
POST_FIELD_NAMES = (
    "views",
    "likes",
    "reposts",
    "replies",
    "username",
    "createdAt",
    "author_id",
    "text_length",
)
POST_FIELD_THRESHOLD = 3

_VERSION_RE = re.compile(r"Version\s+([0-9]+\.[0-9]+\.[0-9]+)")
_DOI_RE = re.compile(r"10\.5281/zenodo\.[0-9]+")
_CFF_VERSION_RE = re.compile(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', re.M)
_DATE_MODIFIED_RE = re.compile(r'"dateModified"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"')
_LAST_UPDATED_RE = re.compile(r"最終更新:</strong>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
_SECTION_RE = re.compile(r'<h2 id="([^"]+)">')
_ID_RE = re.compile(r'id="([^"]+)"')
_HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{2,}")
_PERMALINK_RE = re.compile(r"https://(?:twitter|x)\.com/[^\s\"<]*")
_SCRIPT_STYLE_RE = re.compile(
    r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>"
    r"|<pre\b[^>]*>.*?</pre>|<code\b[^>]*>.*?</code>",
    re.S | re.I,
)
_H3_RE = re.compile(r"<h3>(.*?)</h3>", re.S)

#: Artifacts the research-page structure requirements (PC-5) apply to.
#: The requirement comes from the research-page generator contract; the guide
#: has its own generator and is therefore not covered by PC-5.
RESEARCH_PAGE_GLOB = "research_*.html"

#: Rules without an implementation, reported so the gap is visible.
UNIMPLEMENTED = (
    {
        "rule": "PC-2",
        "requirement": "every published number names its source run",
        "reason": "needs the content refresh (phase 4 of the refresh plan)",
    },
    {
        "rule": "PC-7",
        "requirement": "a committed review envelope per publication artifact",
        "reason": "needs the review records (metadata/publication/)",
    },
    {
        "rule": "PC-8",
        "requirement": "the guide's own structure requirements",
        "reason": (
            "the guide follows generate-compound-guide, not the research-page "
            "contract, so PC-5 does not apply to it"
        ),
    },
)


def _strip_non_content(html: str) -> str:
    """Remove script / style / pre / code blocks.

    JSON-LD (``@type``), CSS (``@media``) and BibTeX (``@dataset{``) all use
    ``@`` without being a post handle, and none of them is prose.  Stripping
    these blocks keeps the per-post rule from firing on them.
    """

    return _SCRIPT_STYLE_RE.sub("", html)


def _sections(html: str) -> list[tuple[str, str]]:
    """Split the body into ``(id, content)`` at every ``<h2 id=...>``.

    Splitting on the boundaries rather than looking an id up keeps duplicate
    ids (PC-6) reportable while still checking each section separately.
    """

    matches = list(_SECTION_RE.finditer(html))
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(html)
        sections.append((match.group(1), html[match.start():end]))
    return sections


def _reading(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _release(repo_root: Path) -> dict:
    """The release the repository declares.  CITATION.cff is the version and
    DOI declaration; ``metadata/datapackage.json`` may declare a DOI as well.
    """

    cff = _reading(repo_root / "CITATION.cff")
    version_match = _CFF_VERSION_RE.search(cff)
    dois = set(_DOI_RE.findall(cff))
    datapackage = repo_root / "metadata" / "datapackage.json"
    if datapackage.is_file():
        dois.update(_DOI_RE.findall(_reading(datapackage)))
    return {
        "version": version_match.group(1) if version_match else "",
        "declared_dois": sorted(dois),
        "declared_in": ["CITATION.cff", "metadata/datapackage.json"],
    }


def _version_finding(version: str, declared: str):
    if not version or not declared or version == declared:
        return None
    if _as_tuple(version) < _as_tuple(declared):
        return (
            "release_version_behind",
            f"presents Version {version}; the repository publishes {declared}",
        )
    return (
        "release_version_ahead",
        f"presents Version {version}; the repository publishes {declared}",
    )


def _as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _artifact_findings(path: Path, repo_root: Path, release: dict) -> list[dict]:
    raw = _reading(path)
    html = _strip_non_content(raw)
    relative = path.relative_to(repo_root).as_posix()
    findings: list[dict] = []

    def add(rule: str, kind: str, detail: str) -> None:
        findings.append({"rule": rule, "kind": kind, "path": relative, "detail": detail})

    # PC-1 - the release this artifact presents.
    versions = _VERSION_RE.findall(html)
    if versions:
        finding = _version_finding(versions[0], release["version"])
        if finding:
            add("PC-1", finding[0], finding[1])
    for doi in sorted(set(_DOI_RE.findall(html))):
        if release["declared_dois"] and doi not in release["declared_dois"]:
            add(
                "PC-1",
                "release_doi_not_declared",
                f"cites {doi}; declared DOIs are {', '.join(release['declared_dois'])}",
            )

    # PC-6 - section ids must be unique (the duplicate id hid a section from
    # the previous section-scoped checks).
    seen: dict[str, int] = {}
    for identifier in _ID_RE.findall(html):
        seen[identifier] = seen.get(identifier, 0) + 1
    for identifier, count in sorted(seen.items()):
        if count > 1:
            add("PC-6", "duplicate_section_id", f'id="{identifier}" appears {count} times')

    # PC-4 - declared metadata must agree.
    date_modified = _DATE_MODIFIED_RE.search(raw)
    last_updated = _LAST_UPDATED_RE.search(html)
    if date_modified and last_updated and date_modified.group(1) != last_updated.group(1):
        add(
            "PC-4",
            "date_modified_mismatch",
            f"dateModified {date_modified.group(1)} but 最終更新 {last_updated.group(1)}",
        )

    # PC-3 - policy-out sources.
    if "YouTube Data API" in html and V3_POLICY_MARKER not in html:
        add(
            "PC-3",
            "youtube_data_api_unmarked",
            "cites the retired YouTube Data API v3 without recording the"
            " 2026-10-12 decision",
        )
    permalinks = sorted(set(_PERMALINK_RE.findall(html)))
    if permalinks:
        add("PC-3", "x_post_level_expression", f"post permalink: {permalinks[0]}")
    handles = sorted(set(_HANDLE_RE.findall(html)))
    if handles:
        add("PC-3", "x_post_level_expression", f"account handle: {handles[0]}")
    for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", html, re.S):
        named = [name for name in POST_FIELD_NAMES if name in paragraph]
        if len(named) >= POST_FIELD_THRESHOLD:
            add(
                "PC-3",
                "x_post_level_expression",
                "describes the post-record shape: " + ", ".join(named),
            )
            break

    # PC-5 - section depth requirements on the research pages (per section, not
    # per id lookup).
    if not path.match(RESEARCH_PAGE_GLOB):
        return findings
    for section_id, content in _sections(html):
        if section_id == "data-search":
            # The required shape is a 5-year table *and* a 12-month table
            # (the page generator's contract); the headings name them, so a
            # definition sentence containing "12ヶ月" cannot satisfy the rule.
            headings = " | ".join(_H3_RE.findall(content))
            missing = [
                label
                for label, token in (("5年", "5年"), ("12ヶ月", "12ヶ月"))
                if token not in headings
            ]
            if missing:
                add(
                    "PC-5",
                    "gt_timeframe_missing",
                    "Google Trends section has no table heading for: "
                    + ", ".join(missing),
                )
        elif section_id == "data-x":
            if "95%" not in content:
                add("PC-5", "x_interval_missing", "X section has no 95% interval")
        elif section_id.startswith("data-youtube"):
            tables = content.count("<table")
            if tables < 2:
                add(
                    "PC-5",
                    "youtube_table_count_low",
                    f"{section_id} has {tables} table(s), 2 required",
                )
    return findings


def build_publication_contract_report(repo_root: Path) -> dict:
    """Check every committed publication HTML artifact.  Read-only."""

    repo_root = Path(repo_root)
    publication_root = repo_root / "publication"
    release = _release(repo_root)
    artifacts = sorted(publication_root.rglob("*.html")) if publication_root.is_dir() else []

    findings: list[dict] = []
    for artifact in artifacts:
        findings.extend(_artifact_findings(artifact, repo_root, release))
    findings.sort(key=lambda entry: (entry["path"], entry["rule"], entry["kind"]))

    def count(field: str) -> dict:
        counts: dict[str, int] = {}
        for finding in findings:
            counts[finding[field]] = counts.get(finding[field], 0) + 1
        return dict(sorted(counts.items()))

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_by": "validation.cli audit-publication",
        "publication_root": "publication",
        "release": release,
        "summary": {
            "artifact_count": len(artifacts),
            "finding_count": len(findings),
            "by_rule": count("rule"),
            "by_kind": count("kind"),
        },
        "implemented_rules": ["PC-1", "PC-3", "PC-4", "PC-5", "PC-6"],
        "unimplemented_rules": list(UNIMPLEMENTED),
        "findings": findings,
    }
