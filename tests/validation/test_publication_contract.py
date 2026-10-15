"""The publication contract rules must fire on violations and stay quiet on a
conforming artifact.

The previous page validator was inert (its depth rules were unreachable and its
data paths did not exist), so it reported 13 green pages while 13 pages cited a
stale release.  Every rule here is therefore tested both ways: a synthetic repo
root with a targeted violation must produce the finding, and the conforming
fixture must produce none.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from validation.publication_contract import (
    V3_POLICY_MARKER,
    build_publication_contract_report,
)

CFF = 'cff-version: 1.2.0\nversion: "9.9.9"\nidentifiers:\n  - type: doi\n    value: "10.5281/zenodo.99999999"\n'

#: A post permalink, assembled from parts on purpose: ``validation.x_identity``
#: scans tracked files for post permalinks, so a literal one in this fixture
#: would be reported as an X identity exposure (and is).
POST_PERMALINK = "https://" + "x.com/someone/status/1"

#: The run the conforming page cites.  ``_report`` catalogs it (a directory with
#: ``run_metadata.json`` under ``datasets/*/data/raw/**``), so PC-2 can resolve
#: the reference; a page may only name runs the catalog has.
RUN_ID = "20261014T204841Z-google-trends-example-study"

CONFORMING = f"""<html><body>
<h2 id="data-search">Google Trends</h2>
<h3>5年データサマリー</h3><table><tr><td>5年平均</td></tr></table>
<h3>12ヶ月データサマリー</h3><table><tr><td>12ヶ月平均</td></tr></table>
<p>出所: run <code>{RUN_ID}</code>（2026-10-14 収集）。</p>
<h2 id="data-x">X (Twitter)</h2><table><tr><th>95% CI</th></tr></table>
<h2 id="data-youtube">YouTube</h2><table></table><table></table>
<p>Version 9.9.9 DOI 10.5281/zenodo.99999999</p>
</body></html>
"""

GUIDE_CONFORMING = f"""<!DOCTYPE html>
<html lang="ja"><head>
<script type="application/ld+json">{{"@type": "BreadcrumbList"}}</script>
<script type="application/ld+json">{{"@type": "Article"}}</script>
<script type="application/ld+json">{{"@type": "FAQPage"}}</script>
</head><body>
<nav class="breadcrumb">ホーム</nav>
<main>
<div class="summary-block"><h2>このページで分かること</h2></div>
<div class="caution-block"><h3>利益相反の開示</h3><p>医療・治療の助言ではない。CC-BY-4.0。</p></div>
<h1>CBX とは？</h1>
<h2 id="what-is-cbx">CBX とは</h2>
<h2 id="regulation">規制状況</h2>
<h2 id="safety">安全性について</h2>
<h2 id="compare">比較</h2>
<h2 id="methodology">調査方法</h2>
<p>Google Trends の値は相対指数であり、絶対検索数ではありません。サプライヤーCOAであり、独立分析ではありません。</p>
<div class="data-section"><h2 id="data-search">Google Trends</h2></div>
<div class="data-section"><h2 id="data-coa">COA</h2></div>
<div class="data-section"><h2 id="data-x">X</h2></div>
<div class="data-section"><h2 id="data-youtube">YouTube</h2></div>
<h2 id="about">この記録について</h2>
<h2 id="citation">この調査を引用する場合</h2>
<div class="ingredient-cta"><h2>他の成分も探す</h2></div>
<h2 id="faq">よくある質問</h2>
<h3>合法ですか？</h3><h3>違いは？</h3><h3>副作用は？</h3><h3>注意点は？</h3>
<div class="trust-block">確認者</div>
</main><footer class="footer">footer</footer>
<p>Version 9.9.9 DOI 10.5281/zenodo.99999999</p>
</body></html>
"""


def _catalog(tmp_path: Path, *run_ids: str) -> None:
    for run_id in run_ids:
        run_dir = (
            tmp_path
            / "datasets"
            / "example-study"
            / "data"
            / "raw"
            / "google_trends"
            / run_id
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_metadata.json").write_text("{}", encoding="utf-8")


def _artifact_id(name: str) -> str:
    relative = name[:-5] if name.endswith(".html") else name
    return relative.replace("/", "-").replace("_", "-").lower()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_envelope(
    tmp_path: Path, path: Path, *, artifact_id: str | None = None, sha256: str | None = None
) -> None:
    relative = path.relative_to(tmp_path).as_posix()
    artifact_id = artifact_id or _artifact_id(path.relative_to(tmp_path / "publication").as_posix())
    sha256 = sha256 or _sha256(path)
    envelope = tmp_path / "metadata" / "publication" / artifact_id
    envelope.mkdir(parents=True, exist_ok=True)
    (envelope / "artifact.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "record": "publication_artifact_descriptor",
                "artifact_id": artifact_id,
                "path": relative,
                "sha256": sha256,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (envelope / "evidence.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "record": "publication_review_evidence",
                "artifact_id": artifact_id,
                "citations": {
                    "publication_contract": [
                        "validation.cli audit-publication（fixture）: PC-1..PC-8"
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (envelope / "decision.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "record": "publication_decision",
                "decision_id": f"publication-review-{artifact_id}",
                "artifact_id": artifact_id,
                "artifact_sha256": sha256,
                "status": "requires_review",
                "reviewed_at": None,
                "reviewer": None,
                "criteria_version": "PC-7 fixture",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _report(
    tmp_path: Path,
    html: str,
    *,
    cff: str = CFF,
    name: str = "research_page.html",
    envelope: bool = True,
) -> dict:
    (tmp_path / "CITATION.cff").write_text(cff, encoding="utf-8")
    _catalog(tmp_path, RUN_ID)
    publication = tmp_path / "publication"
    publication.mkdir(exist_ok=True)
    for existing in publication.glob("*.html"):
        existing.unlink()
    path = publication / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    if envelope:
        _write_envelope(tmp_path, path)
    return build_publication_contract_report(tmp_path)


def _kinds(report: dict) -> list[str]:
    return [finding["kind"] for finding in report["findings"]]


def test_conforming_artifact_produces_no_findings(tmp_path: Path) -> None:
    report = _report(tmp_path, CONFORMING)

    assert report["summary"] == {
        "artifact_count": 1,
        "finding_count": 0,
        "declared_gap_count": 0,
        "by_rule": {},
        "by_kind": {},
    }
    assert report["release"]["version"] == "9.9.9"
    assert report["declared_gaps"] == []


def test_declared_gaps_keep_a_missing_5_year_series_visible(tmp_path: Path) -> None:
    """A page may declare the series missing; that must not read as "nothing to see"."""

    declared = CONFORMING.replace(
        "<h3>5年データサマリー</h3><table><tr><td>5年平均</td></tr></table>",
        "<h3>5年データサマリー</h3><p>5 年系列は未取得。需要ゼロを意味しない。</p>"
        "<p>5年平均は算出不能（run に平均値の記録なし）。</p>",
    )
    report = _report(tmp_path, declared)

    assert report["summary"]["finding_count"] == 0
    assert {gap["kind"] for gap in report["declared_gaps"]} == {
        "five_year_not_collected",
        "five_year_value_uncomputable",
    }


def test_release_version_and_doi_are_compared_to_the_declaration(tmp_path: Path) -> None:
    html = CONFORMING.replace("Version 9.9.9", "Version 1.2.3").replace(
        "10.5281/zenodo.99999999", "10.5281/zenodo.11111111"
    )

    kinds = _kinds(_report(tmp_path, html))

    assert "release_version_behind" in kinds
    assert "release_doi_not_declared" in kinds


def test_duplicate_section_id_is_reported(tmp_path: Path) -> None:
    html = CONFORMING.replace('<h2 id="data-x">', '<h2 id="data-youtube">')

    assert "duplicate_section_id" in _kinds(_report(tmp_path, html))


def test_google_trends_needs_both_timeframes(tmp_path: Path) -> None:
    html = CONFORMING.replace("<h3>5年データサマリー</h3>", "")

    findings = _report(tmp_path, html)["findings"]

    assert [f["kind"] for f in findings] == ["gt_timeframe_missing"]
    assert "5年" in findings[0]["detail"]


def test_a_definition_mention_does_not_satisfy_the_timeframe_rule(tmp_path: Path) -> None:
    """The old validator accepted the token anywhere; only headings name a table."""

    html = CONFORMING.replace(
        "<h3>5年データサマリー</h3>", "<p>5年の平均値はこちらを参照</p>"
    )

    assert "gt_timeframe_missing" in _kinds(_report(tmp_path, html))


def test_x_section_needs_the_interval(tmp_path: Path) -> None:
    html = CONFORMING.replace("<th>95% CI</th>", "<th>比率</th>")

    assert "x_interval_missing" in _kinds(_report(tmp_path, html))


def test_youtube_section_needs_depth(tmp_path: Path) -> None:
    html = CONFORMING.replace(
        '<h2 id="data-youtube">YouTube</h2><table></table><table></table>',
        '<h2 id="data-youtube">YouTube</h2><table></table>',
    )

    assert "youtube_table_count_low" in _kinds(_report(tmp_path, html))


def test_date_modified_must_agree_with_the_page(tmp_path: Path) -> None:
    html = CONFORMING.replace(
        "<body>", '<body><script type="application/ld+json">{"dateModified": "2026-01-02"}</script>'
    ).replace("</p>\n</body>", "</p><p><strong>最終更新:</strong> 2026-01-03。</p>\n</body>")

    assert "date_modified_mismatch" in _kinds(_report(tmp_path, html))


@pytest.mark.parametrize(
    "html",
    [
        pytest.param(
            '<p>データソース: YouTube Search via Apify + YouTube Data API</p>',
            id="v3_unmarked",
        ),
    ],
)
def test_retired_source_must_be_marked(tmp_path: Path, html: str) -> None:
    marked = html + f"<p>{V3_POLICY_MARKER}</p>"

    assert "youtube_data_api_unmarked" in _kinds(_report(tmp_path, html))
    assert "youtube_data_api_unmarked" not in _kinds(_report(tmp_path, marked))


@pytest.mark.parametrize(
    "expression",
    [
        pytest.param(
            f'<p><a href="{POST_PERMALINK}">post</a></p>', id="permalink"
        ),
        pytest.param("<p>投稿者 @some_handle による言及</p>", id="handle"),
        pytest.param("<p>views, likes, reposts, replies の4項目</p>", id="post_fields"),
    ],
)
def test_per_post_x_expressions_are_reported(tmp_path: Path, expression: str) -> None:
    findings = _report(tmp_path, CONFORMING.replace("</body>", f"{expression}</body>"))["findings"]

    assert [f["kind"] for f in findings] == ["x_post_level_expression"]


def test_json_ld_and_code_blocks_are_not_post_handles(tmp_path: Path) -> None:
    """``@type`` (JSON-LD), ``@media`` (CSS) and ``@dataset{`` (BibTeX) are not handles."""

    html = CONFORMING.replace(
        "</body>",
        '<pre><code>@dataset{kato2026, author = {Kato}}</code></pre>'
        '<script type="application/ld+json">{"@type": "Dataset"}</script>'
        "<style>@media print { }</style></body>",
    )

    assert _kinds(_report(tmp_path, html)) == []


def test_section_depth_rules_apply_to_research_pages_only(tmp_path: Path) -> None:
    """PC-5 comes from the research-page generator; the guide has its own."""

    shallow = CONFORMING.replace("<h3>5年データサマリー</h3>", "")

    assert "gt_timeframe_missing" in _kinds(_report(tmp_path, shallow))
    assert _kinds(_report(tmp_path, shallow, name="guide.html")) == []


def test_all_publication_contract_rules_are_implemented(tmp_path: Path) -> None:
    """Implemented rules are explicit, and the unimplemented list is empty."""

    report = _report(tmp_path, CONFORMING)

    assert report["unimplemented_rules"] == []
    assert set(report["implemented_rules"]) == {f"PC-{index}" for index in range(1, 9)}


def test_google_trends_section_must_name_its_run(tmp_path: Path) -> None:
    """PC-2: the generated numbers must not lose the run they came from."""

    html = CONFORMING.replace(f"<p>出所: run <code>{RUN_ID}</code>（2026-10-14 収集）。</p>", "")

    assert "gt_run_not_named" in _kinds(_report(tmp_path, html))


def test_a_page_cannot_cite_a_run_the_catalog_does_not_have(tmp_path: Path) -> None:
    """PC-2: a citation of a withdrawn or mistyped run is a broken claim."""

    html = CONFORMING.replace(RUN_ID, "20200101T000000Z-google-trends-gone")
    findings = _report(tmp_path, html)["findings"]

    assert [finding["kind"] for finding in findings] == ["run_reference_unresolved"]
    assert "20200101T000000Z-google-trends-gone" in findings[0]["detail"]


def test_the_run_catalog_is_reported(tmp_path: Path) -> None:
    """The resolution target is part of the report, so a reader can size it."""

    assert _report(tmp_path, CONFORMING)["catalog_run_count"] == 1


def test_publication_artifacts_need_review_envelopes(tmp_path: Path) -> None:
    """PC-7: an HTML artifact without a decision envelope is not reviewable."""

    findings = _report(tmp_path, CONFORMING, envelope=False)["findings"]

    assert [finding["kind"] for finding in findings] == ["publication_review_envelope_missing"]


def test_review_envelope_must_pin_the_current_artifact_hash(tmp_path: Path) -> None:
    """PC-7: a stale decision cannot silently satisfy the review-record rule."""

    (tmp_path / "CITATION.cff").write_text(CFF, encoding="utf-8")
    _catalog(tmp_path, RUN_ID)
    publication = tmp_path / "publication"
    publication.mkdir(exist_ok=True)
    path = publication / "research_page.html"
    path.write_text(CONFORMING, encoding="utf-8")
    _write_envelope(tmp_path, path, sha256="0" * 64)

    kinds = _kinds(build_publication_contract_report(tmp_path))

    assert kinds.count("publication_review_hash_mismatch") == 2


def test_guide_structure_requirements_are_mechanical_and_nonempty(tmp_path: Path) -> None:
    """PC-8 applies the guide generator's checkable structure requirements."""

    assert _kinds(_report(tmp_path, GUIDE_CONFORMING, name="guide_cbx_rewrite.html")) == []

    shallow = GUIDE_CONFORMING.replace('<h2 id="data-coa">COA</h2>', "<h2>COA</h2>")
    findings = _report(tmp_path, shallow, name="guide_cbx_rewrite.html")["findings"]

    assert [finding["kind"] for finding in findings] == ["guide_section_missing"]
    assert 'id="data-coa"' in findings[0]["detail"]


def test_guide_faq_must_have_four_questions(tmp_path: Path) -> None:
    """PC-8: the guide skill says FAQ has at least four questions."""

    short = GUIDE_CONFORMING.replace(
        "<h3>合法ですか？</h3><h3>違いは？</h3><h3>副作用は？</h3><h3>注意点は？</h3>",
        "<h3>合法ですか？</h3><h3>違いは？</h3><h3>副作用は？</h3>",
    )

    assert "guide_faq_too_short" in _kinds(_report(tmp_path, short, name="guide_cbx_rewrite.html"))


def test_guide_coa_section_must_not_name_the_requester(tmp_path: Path) -> None:
    """PC-8: the COA requester stays in provenance records, not publication."""

    named = GUIDE_CONFORMING.replace(
        '<div class="data-section"><h2 id="data-coa">COA</h2></div>',
        '<div class="data-section"><h2 id="data-coa">COA</h2><p class="meta">依頼者: Hempbin</p></div>',
    )
    findings = _report(tmp_path, named, name="guide_cbx_rewrite.html")["findings"]

    assert [finding["kind"] for finding in findings] == ["guide_coa_requester_mention"]
