"""The publication contract rules must fire on violations and stay quiet on a
conforming artifact.

The previous page validator was inert (its depth rules were unreachable and its
data paths did not exist), so it reported 13 green pages while 13 pages cited a
stale release.  Every rule here is therefore tested both ways: a synthetic repo
root with a targeted violation must produce the finding, and the conforming
fixture must produce none.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validation.publication_contract import (
    UNIMPLEMENTED,
    V3_POLICY_MARKER,
    build_publication_contract_report,
)

CFF = 'cff-version: 1.2.0\nversion: "9.9.9"\nidentifiers:\n  - type: doi\n    value: "10.5281/zenodo.99999999"\n'

#: A post permalink, assembled from parts on purpose: ``validation.x_identity``
#: scans tracked files for post permalinks, so a literal one in this fixture
#: would be reported as an X identity exposure (and is).
POST_PERMALINK = "https://" + "x.com/someone/status/1"

CONFORMING = """<html><body>
<h2 id="data-search">Google Trends</h2>
<h3>5年データサマリー</h3><table><tr><td>5年平均</td></tr></table>
<h3>12ヶ月データサマリー</h3><table><tr><td>12ヶ月平均</td></tr></table>
<h2 id="data-x">X (Twitter)</h2><table><tr><th>95% CI</th></tr></table>
<h2 id="data-youtube">YouTube</h2><table></table><table></table>
<p>Version 9.9.9 DOI 10.5281/zenodo.99999999</p>
</body></html>
"""


def _report(tmp_path: Path, html: str, *, cff: str = CFF, name: str = "research_page.html") -> dict:
    (tmp_path / "CITATION.cff").write_text(cff, encoding="utf-8")
    publication = tmp_path / "publication"
    publication.mkdir(exist_ok=True)
    for existing in publication.glob("*.html"):
        existing.unlink()
    (publication / name).write_text(html, encoding="utf-8")
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


def test_the_report_names_the_rules_it_does_not_implement(tmp_path: Path) -> None:
    """An unimplemented rule must be named in the report, not silently absent."""

    report = _report(tmp_path, CONFORMING)

    assert {entry["rule"] for entry in report["unimplemented_rules"]} == {
        entry["rule"] for entry in UNIMPLEMENTED
    }
    assert {entry["rule"] for entry in report["unimplemented_rules"]} >= {"PC-2", "PC-7"}
