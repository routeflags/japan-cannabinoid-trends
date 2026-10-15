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
- PC-2 run references: a research page's Google Trends section must name the run
  its 5-year table was generated from (``processing.cli gt-summary`` writes the
  source line), and every run id named anywhere on a page must be resolvable
  either to cataloged raw metadata or to a committed staging declaration.  A page
  cannot cite a run that does not exist, and the generated numbers cannot lose
  their source without a finding.  The other sections (X / YouTube / COA) are
  backed by legacy study data that has no run record to cite, so naming a run
  there is not required - resolving it is.
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
  encoded by PC-5.
- PC-6 HTML validity: section ids must be unique.
- PC-7 review envelopes: each publication HTML artifact must have a committed
  ``metadata/publication/<artifact_id>/`` envelope whose descriptor hash matches
  the file and whose decision records a concrete review state.  ``requires_review``
  is valid for a not-yet-public artifact; PC-7 records that the review state
  exists, while ``gate-publication`` decides whether it is publishable.
- PC-8 guide structure: ``guide_*`` pages are checked against the mechanical
  parts of ``generate-compound-guide`` (JSON-LD blocks, H1, guide sections,
  required disclosure / limitation markers, FAQ length).  Tone, judgement and
  scientific adequacy remain human review items.

Deliberately not implemented: none.  If a publication rule cannot be checked
mechanically, it must appear as human review evidence in the PC-7 envelope, not
as a green automated rule.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from validation.x_identity import POST_RECORD_FIELDS

REPORT_SCHEMA_VERSION = "1.0.0"

#: The note a page must carry when it cites the retired YouTube Data API v3.
V3_POLICY_MARKER = "方針判断により使用を取り止め"

#: Post-record field names from the now banned per-post X dataset.  Naming three or
#: more of them in one paragraph describes the post-record shape, which the
#: 2026-10-15 decision bans together with storage and the post-level dataset
#: (ISS-20261015-XID-034).  The list itself lives in :mod:`validation.x_identity`
#: (one list, two surfaces: the tracked-file structure and published prose).
_PROSE_VISIBLE = frozenset(
    {
        "views",
        "likes",
        "reposts",
        "replies",
        "username",
        "createdAt",
        "author_id",
        "text_length",
    }
)

#: The prose-visible subset, in the canonical order.  Column names that are X-only
#: (``tweet_id_hash``, ``has_text``) do not occur in published prose, so counting
#: them here would only make the paragraph rule noisier.
POST_FIELD_NAMES = tuple(name for name in POST_RECORD_FIELDS if name in _PROSE_VISIBLE)
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

#: A collection run id as the pipeline writes it (``YYYYMMDDTHHMMSSZ-source-study``).
#: This is what a page cites to say which run produced its numbers (PC-2).
_RUN_ID_RE = re.compile(r"\b\d{8}T\d{6}Z-[A-Za-z0-9-]+")

#: Artifacts the research-page structure requirements (PC-5) apply to.
#: The requirement comes from the research-page generator contract; the guide
#: has its own generator and is therefore not covered by PC-5.
RESEARCH_PAGE_GLOB = "research_*.html"

#: Markers a page uses when the section the contract requires exists but a
#: value cannot be given.  These are extracted into ``declared_gaps`` (a report
#: list, not a finding): the page is compliant, but the missing evidence has to
#: stay visible in the report instead of turning into a green "write 未取得".
MISSING_MARKER = "未取得"
UNCOMPUTABLE_MARKER = "算出不能"

#: Rules without an implementation, reported so the gap is visible.  This is
#: intentionally empty now that PC-7 and PC-8 are mechanical.  Keeping the
#: constant preserves the report shape and tests that no rule silently falls out.
UNIMPLEMENTED: tuple[dict, ...] = ()

DECISION_STATES = {"approved", "denied", "requires_review", "unknown"}

GUIDE_REQUIRED_JSON_LD_TYPES = ("BreadcrumbList", "Article", "FAQPage")
GUIDE_REQUIRED_H2_IDS = (
    "what-is-cbx",
    "regulation",
    "safety",
    "compare",
    "methodology",
    "data-search",
    "data-coa",
    "data-x",
    "data-youtube",
    "about",
    "citation",
    "faq",
)
GUIDE_REQUIRED_CLASSES = (
    "breadcrumb",
    "summary-block",
    "caution-block",
    "data-section",
    "ingredient-cta",
    "trust-block",
    "footer",
)
GUIDE_REQUIRED_MARKERS = (
    "利益相反の開示",
    "CC-BY-4.0",
    "医療・治療の助言",
    "Google Trends の値は相対指数",
    "絶対検索数ではありません",
    "サプライヤーCOA",
    "独立分析ではありません",
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _publication_artifact_id(path: Path, repo_root: Path) -> str:
    """Stable id used by PC-7 review envelope directories.

    The id is derived from the publication path, not from the page title, so a
    title edit does not move the envelope.  ``publication/search-emergence-
    tracker/index.html`` becomes ``search-emergence-tracker-index``.
    """

    relative = path.relative_to(repo_root / "publication").as_posix()
    if relative.endswith(".html"):
        relative = relative[:-5]
    return relative.replace("/", "-").replace("_", "-").lower()


def _load_json_document(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(_reading(path)), None
    except FileNotFoundError:
        return None, "missing"
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return None, f"not valid JSON: {error}"


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


def _review_envelope_findings(path: Path, repo_root: Path) -> list[dict]:
    """PC-7: every publication artifact must have a concrete review state.

    This does not approve the artifact.  A ``requires_review`` decision is a
    valid state for an unpublished artifact; publication approval is still
    enforced by ``gate-publication`` / PUB-10.
    """

    relative = path.relative_to(repo_root).as_posix()
    artifact_id = _publication_artifact_id(path, repo_root)
    envelope = repo_root / "metadata" / "publication" / artifact_id
    current_hash = _sha256(path)
    findings: list[dict] = []

    def add(kind: str, detail: str) -> None:
        findings.append({"rule": "PC-7", "kind": kind, "path": relative, "detail": detail})

    if not envelope.is_dir():
        add(
            "publication_review_envelope_missing",
            f"metadata/publication/{artifact_id}/ is missing",
        )
        return findings

    artifact, artifact_error = _load_json_document(envelope / "artifact.json")
    evidence, evidence_error = _load_json_document(envelope / "evidence.json")
    decision, decision_error = _load_json_document(envelope / "decision.json")
    for filename, error in (
        ("artifact.json", artifact_error),
        ("evidence.json", evidence_error),
        ("decision.json", decision_error),
    ):
        if error:
            add("publication_review_envelope_incomplete", f"{artifact_id}/{filename}: {error}")

    if isinstance(artifact, dict):
        if artifact.get("record") != "publication_artifact_descriptor":
            add("publication_review_descriptor_invalid", "artifact.json has no publication_artifact_descriptor record")
        if artifact.get("artifact_id") != artifact_id:
            add(
                "publication_review_descriptor_invalid",
                f"artifact.json artifact_id {artifact.get('artifact_id')!r} != {artifact_id!r}",
            )
        if artifact.get("path") != relative:
            add(
                "publication_review_descriptor_invalid",
                f"artifact.json path {artifact.get('path')!r} != {relative!r}",
            )
        if artifact.get("sha256") != current_hash:
            add(
                "publication_review_hash_mismatch",
                "artifact.json sha256 does not match the current publication artifact",
            )
    if isinstance(evidence, dict):
        if evidence.get("record") != "publication_review_evidence":
            add("publication_review_evidence_invalid", "evidence.json has no publication_review_evidence record")
        if evidence.get("artifact_id") != artifact_id:
            add(
                "publication_review_evidence_invalid",
                f"evidence.json artifact_id {evidence.get('artifact_id')!r} != {artifact_id!r}",
            )
        citations = evidence.get("citations")
        if not isinstance(citations, dict) or not citations.get("publication_contract"):
            add(
                "publication_review_evidence_invalid",
                "evidence.json must cite the publication contract audit",
            )
    if isinstance(decision, dict):
        if decision.get("record") != "publication_decision":
            add("publication_review_decision_invalid", "decision.json has no publication_decision record")
        if decision.get("artifact_id") != artifact_id:
            add(
                "publication_review_decision_invalid",
                f"decision.json artifact_id {decision.get('artifact_id')!r} != {artifact_id!r}",
            )
        if decision.get("artifact_sha256") != current_hash:
            add(
                "publication_review_hash_mismatch",
                "decision.json artifact_sha256 does not match the current publication artifact",
            )
        if decision.get("status") not in DECISION_STATES:
            add(
                "publication_review_decision_invalid",
                f"decision.json status {decision.get('status')!r} is not a publication state",
            )
        if not decision.get("criteria_version"):
            add("publication_review_decision_invalid", "decision.json criteria_version is empty")
    return findings


def _guide_structure_findings(path: Path, repo_root: Path, raw: str, html: str) -> list[dict]:
    """PC-8: mechanical parts of ``generate-compound-guide`` for guide pages."""

    if not path.name.startswith("guide_"):
        return []
    relative = path.relative_to(repo_root).as_posix()
    findings: list[dict] = []

    def add(kind: str, detail: str) -> None:
        findings.append({"rule": "PC-8", "kind": kind, "path": relative, "detail": detail})

    h1_count = len(re.findall(r"<h1\b", html, re.I))
    if h1_count != 1:
        add("guide_h1_count", f"guide page has {h1_count} h1 elements; exactly 1 required")

    for json_ld_type in GUIDE_REQUIRED_JSON_LD_TYPES:
        if f'"@type": "{json_ld_type}"' not in raw and f'"@type":"{json_ld_type}"' not in raw:
            add("guide_structured_data_missing", f"JSON-LD {json_ld_type} block is missing")

    section_ids = {section_id for section_id, _ in _sections(html)}
    for section_id in GUIDE_REQUIRED_H2_IDS:
        if section_id not in section_ids:
            add("guide_section_missing", f'h2 id="{section_id}" is missing')

    for class_name in GUIDE_REQUIRED_CLASSES:
        if class_name not in html:
            add("guide_class_missing", f'class "{class_name}" is missing')

    for marker in GUIDE_REQUIRED_MARKERS:
        if marker not in html:
            add("guide_required_marker_missing", f"required marker is missing: {marker}")

    faq_sections = [content for section_id, content in _sections(html) if section_id == "faq"]
    faq_count = len(_H3_RE.findall(faq_sections[0])) if faq_sections else 0
    if faq_count < 4:
        add("guide_faq_too_short", f"FAQ has {faq_count} question heading(s); 4 required")

    for section_id, content in _sections(html):
        if section_id == "data-coa" and "依頼者" in content:
            add(
                "guide_coa_requester_mention",
                'COA section must not name the requester (client); requester info stays in provenance records, not in publication (ISS-20261002-011)',
            )
    return findings


def _artifact_findings(
    path: Path, repo_root: Path, release: dict, catalog_run_ids: set[str]
) -> list[dict]:
    raw = _reading(path)
    html = _strip_non_content(raw)
    relative = path.relative_to(repo_root).as_posix()
    findings: list[dict] = []

    def add(rule: str, kind: str, detail: str) -> None:
        findings.append({"rule": rule, "kind": kind, "path": relative, "detail": detail})

    findings.extend(_review_envelope_findings(path, repo_root))
    findings.extend(_guide_structure_findings(path, repo_root, raw, html))

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

    # PC-2 - the run a number came from must be named and must exist.  The run
    # id sits inside ``<code>`` in the generated source line and
    # ``_strip_non_content`` removes code blocks (it exists so ``@`` inside them
    # cannot read as a handle), so this rule reads the raw text.
    if path.match(RESEARCH_PAGE_GLOB):
        for section_id, content in _sections(raw):
            if section_id == "data-search" and not _RUN_ID_RE.search(content):
                add(
                    "PC-2",
                    "gt_run_not_named",
                    "the Google Trends section names no collection run",
                )
    for run_id in sorted(set(_RUN_ID_RE.findall(raw))):
        if run_id not in catalog_run_ids:
            add(
                "PC-2",
                "run_reference_unresolved",
                f"cites run {run_id}, which is not in the catalog",
            )

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


def _declared_gaps(path: Path, html: str, relative: str) -> list[dict]:
    """Evidence the page itself declares as missing (research pages only).

    A 5-year section may legitimately say the series was never collected or that
    a value cannot be computed from its run record (ISS-20261015-GT-003).  The
    section requirement (PC-5) is then satisfied, so this list is what keeps the
    gap reviewable rather than making it disappear into a green report.
    """

    gaps = []
    if not path.match(RESEARCH_PAGE_GLOB):
        return gaps
    for section_id, content in _sections(html):
        if section_id != "data-search":
            continue
        if MISSING_MARKER in content:
            gaps.append(
                {
                    "path": relative,
                    "kind": "five_year_not_collected",
                    "detail": f"the Google Trends section declares {MISSING_MARKER}",
                }
            )
        if UNCOMPUTABLE_MARKER in content:
            gaps.append(
                {
                    "path": relative,
                    "kind": "five_year_value_uncomputable",
                    "detail": f"a value is declared {UNCOMPUTABLE_MARKER} from its run record",
                }
            )
    return gaps


def _declaration_run_ids(repo_root: Path) -> set[str]:
    """Run ids adopted through committed staging declarations.

    External payloads are adopted by declaration before raw files are staged or
    when raw payloads must remain outside a public release archive.  Treating the
    declaration as a resolver keeps PC-2 aligned with the collection pipeline:
    publication prose can cite an adopted run without requiring the raw payload
    itself to be tracked.
    """

    declarations = repo_root / "metadata" / "provenance" / "declarations"
    if not declarations.is_dir():
        return set()

    run_ids: set[str] = set()
    for path in declarations.rglob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if document.get("declaration_version") != "staging-declaration-v1":
            continue
        for run in document.get("runs", []):
            if not isinstance(run, dict):
                continue
            run_id = run.get("run_id")
            if isinstance(run_id, str) and _RUN_ID_RE.fullmatch(run_id):
                run_ids.add(run_id)
    return run_ids


def _catalog_run_ids(repo_root: Path) -> set[str]:
    """Run ids present in a committed provenance resolver (PC-2).

    A run is resolvable when either:

    - it is cataloged under ``datasets/*/data/raw/**`` with ``run_metadata.json``;
      or
    - it appears in a committed ``staging-declaration-v1`` document under
      ``metadata/provenance/declarations/``.

    A page citing anything else is making a provenance claim the repository
    cannot support - a withdrawn or mistyped run is exactly the case this rule
    exists for.
    """

    datasets = repo_root / "datasets"
    cataloged = set()
    if datasets.is_dir():
        cataloged = {path.parent.name for path in datasets.rglob("run_metadata.json")}
    return cataloged | _declaration_run_ids(repo_root)


def build_publication_contract_report(repo_root: Path) -> dict:
    """Check every committed publication HTML artifact.  Read-only."""

    repo_root = Path(repo_root)
    publication_root = repo_root / "publication"
    release = _release(repo_root)
    artifacts = sorted(publication_root.rglob("*.html")) if publication_root.is_dir() else []
    catalog_run_ids = _catalog_run_ids(repo_root)

    findings: list[dict] = []
    declared_gaps: list[dict] = []
    for artifact in artifacts:
        relative = artifact.relative_to(repo_root).as_posix()
        findings.extend(_artifact_findings(artifact, repo_root, release, catalog_run_ids))
        declared_gaps.extend(
            _declared_gaps(artifact, _strip_non_content(_reading(artifact)), relative)
        )
    findings.sort(key=lambda entry: (entry["path"], entry["rule"], entry["kind"]))
    declared_gaps.sort(key=lambda entry: (entry["path"], entry["kind"]))

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
        "catalog_run_count": len(catalog_run_ids),
        "summary": {
            "artifact_count": len(artifacts),
            "finding_count": len(findings),
            "declared_gap_count": len(declared_gaps),
            "by_rule": count("rule"),
            "by_kind": count("kind"),
        },
        "implemented_rules": ["PC-1", "PC-2", "PC-3", "PC-4", "PC-5", "PC-6", "PC-7", "PC-8"],
        "unimplemented_rules": list(UNIMPLEMENTED),
        "findings": findings,
        "declared_gaps": declared_gaps,
    }
