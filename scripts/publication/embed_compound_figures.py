#!/usr/bin/env python3
"""生成済みの物質別図を publication/research_<compound>.html に差し込む。

図の定義（題名・出所 run・件数）は study 側の `provenance.json` を正本とし、
このスクリプトはそれを使って figure 要素を組み立てる。位置はページの構造で決める。

- 検索推移図: 「5年データサマリー」表の後の最初の <h3> の直前
- 年次図: 対応する「年次分布」表の直後（文書順で対応）

何度実行してもよい（マーカーの間を置き換える）。ただしページは hash 単位で
公開承認されているため、差し込むと artifact_sha256 が変わる。公開状態の節は
その事実（再承認が必要）に書き換える。承認自体は owner の判断であり、ここでは
行わない。

    python3 scripts/publication/embed_compound_figures.py
    python3 scripts/publication/embed_compound_figures.py cbd thc
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUBLICATION = REPO / "publication"
ANALYSIS = REPO / "datasets/cannabinoid-raw-collection/analysis"

TRENDS_FIGURE = "trends-5y-standalone"
STATE_MARK = "<!-- publication-state:figures-embedded -->"


def fail(ctx: str, message: str) -> None:
    raise SystemExit(f"embed_compound_figures[{ctx}]: {message}")


def marker(figure_id: str, edge: str) -> str:
    return f"<!-- figure:{figure_id} {edge} -->"


def strip_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", html).split())


def svg_size(path: Path) -> tuple:
    head = path.read_text(encoding="utf-8")[:400]
    matched = re.search(r'width="(\d+)" height="(\d+)"', head)
    if matched is None:
        fail(path.name, "svg width/height not found")
    return int(matched.group(1)), int(matched.group(2))


def trends_caption(figure: dict) -> str:
    source = figure["source"]
    stats = figure["stats"]
    mean = f"{stats['mean']:.{stats['decimals']}f}"
    return (
        f"値は単独系列の相対指数（この系列の最大 = {stats['max']}、{stats['max_dates'][0]}）で、"
        f"絶対検索数ではない。破線は週次平均 {mean}。"
        f"観測範囲 {stats['observed_start']} 〜 {stats['observed_end']}（{stats['points']} 週）。"
        f"出所: run <code>{source['run_id']}</code>。"
    )


def matrix_caption(figure: dict) -> str:
    source = figure["source"]
    stats = figure["stats"]
    terms = "・".join(source["terms"])
    partial = [
        f"{year}（{stats['weeks_per_year'][year]} 週）"
        for year in stats["years"]
        if year not in stats["complete_years"]
    ]
    zeros = [term for term, value in stats["mean_5y"].items() if value == "0.0000"]
    caption = (
        f"値は同一 <code>compare_terms</code> 要求（{terms}）の共通スケールによる年間平均で、"
        "要求内の最大 = 100。要求間・単独系列とは換算できない。"
        f"年間平均は週次値の暦年平均（部分年: {'、'.join(partial) if partial else 'なし'}）。"
    )
    if zeros:
        caption += (
            f"{'・'.join(zeros)} は 5 年平均 0.0000 で、相対指数の最小値への丸めであり、"
            "需要ゼロの観測ではない。"
        )
    return caption + f"出所: run <code>{source['run_id']}</code>。"


def matrix_anchor(html: str, run_id: str, ctx: str) -> int:
    """5年共通スケールの出所段落の直前の表の直後を差し込み位置にする。"""
    for matched in re.finditer(r"<p><strong>出所[^<]{0,16}[:：]</strong>(.*?)</p>", html, re.S):
        paragraph = matched.group(1)
        if "today 5-y" in paragraph and f"<code>{run_id}</code>" in paragraph:
            table_end = html.rfind("</table>", 0, matched.start())
            if table_end == -1:
                fail(ctx, f"no table before the common-scale citation of {run_id}")
            return table_end + len("</table>")
    fail(ctx, f"no 5-year common-scale citation of {run_id}")


def yearly_caption(figure: dict) -> str:
    source = figure["source"]
    start = source.get("observed_publish_start") or "不明"
    end = source.get("observed_publish_end") or "不明"
    partial = source.get("partial_years") or []
    note = f"部分年（{'、'.join(partial)}）は * で示し、その年の観測日数分の件数である。" if partial else ""
    return (
        f"{note}"
        f"返却サンプル内の公開日件数であり、YouTube 全体の投稿数ではない。"
        f"観測公開日 {start} 〜 {end}、返却 {source['returned_count']} 件（年次合計と一致）。"
        "公開日がサンプルにない年は棒を作らない。"
        f"出所: run <code>{source['run_id']}</code>。"
    )


def figure_block(number: int, figure: dict, svg_path: Path, caption: str) -> str:
    figure_id = figure["id"]
    width, height = svg_size(svg_path)
    src = svg_path.relative_to(PUBLICATION).as_posix()
    return "\n".join(
        [
            marker(figure_id, "start"),
            f'<figure id="figure-{figure_id}">',
            f'  <img src="{src}" alt="{figure["title"]}" width="{width}" height="{height}" '
            'style="max-width:100%;height:auto">',
            f"  <figcaption><strong>図{number}: {figure['title']}</strong>。{caption}</figcaption>",
            "</figure>",
            marker(figure_id, "end"),
        ]
    )


def drop_existing_blocks(html: str) -> str:
    """差し込み済みの figure をマーカーごと取り除く（再実行を同じ結果にする）。"""
    while True:
        start = re.search(marker_any("start"), html)
        if start is None:
            return html
        end_token = start.group(1) + " end -->"
        end = html.find(end_token, start.end())
        if end == -1:
            fail("marker", f"unterminated figure block {start.group(1)}")
        pre = html[: start.start()].rstrip()
        suf = html[end + len(end_token):].lstrip("\n")
        html = pre + "\n\n" + suf


def marker_any(edge: str) -> str:
    # 図 id は setA のように大文字を含むため、英数字すべてを許す。
    return r"<!-- figure:([A-Za-z0-9-]+) " + edge + r" -->"


def insert_at(html: str, position: int, block: str) -> str:
    """position の直前に差し込む。前後の空行はちょうど1行にする。"""
    prefix = html[:position].rstrip()
    suffix = html[position:].lstrip("\n")
    return prefix + "\n\n" + block + "\n\n" + suffix


def embed(ctx: str, page: Path, figures_dir: Path, provenance: dict) -> None:
    html = page.read_text(encoding="utf-8")
    html = drop_existing_blocks(html)

    figures = provenance["figures"]
    trends = next((f for f in figures if f["id"] == TRENDS_FIGURE), None)
    if trends is None:
        fail(ctx, "provenance has no trends figure")
    yearly = [f for f in figures if f["id"].startswith("youtube-yearly-")]

    slots = []
    summary = re.search(r"<h3>5年データサマリー[^<]*</h3>(.*?)</table>", html, re.S)
    if summary is None:
        fail(ctx, "5-year summary table not found")
    next_h3 = html.find("<h3", summary.end())
    if next_h3 == -1:
        fail(ctx, "no heading after the 5-year summary table")
    slots.append((next_h3, trends, trends_caption(trends)))

    tables = [m for m in re.finditer(r"<h3>(.*?)</h3>(.*?)</table>", html, re.S) if "年次分布" in m.group(1)]
    if len(tables) != len(yearly):
        fail(ctx, f"{len(tables)} yearly tables on the page but {len(yearly)} in provenance")
    for table, figure in zip(tables, yearly):
        slots.append((table.end(), figure, yearly_caption(figure)))

    for figure in (f for f in figures if f["id"].startswith("bubble-matrix-")):
        position = matrix_anchor(html, figure["source"]["run_id"], ctx)
        slots.append((position, figure, matrix_caption(figure)))

    # 図番号は文書順で振る（H4CBH・HHBD は YouTube 節が Trends 節より前にある）。
    blocks = {}
    ordered = sorted(slots, key=lambda item: item[0])
    for number, (_, figure, caption) in enumerate(ordered, start=1):
        svg_path = figures_dir / f"{figure['id']}.svg"
        if not svg_path.exists():
            fail(ctx, f"missing figure {svg_path.relative_to(REPO)}")
        blocks[figure["id"]] = figure_block(number, figure, svg_path, caption)

    # 後ろから差し込んで、前の位置がずれないようにする。
    for position, figure, _ in sorted(slots, key=lambda item: item[0], reverse=True):
        html = insert_at(html, position, blocks[figure["id"]])

    html = update_publication_state(html, page.stem.replace("research_", "research-"), ctx)
    page.write_text(html, encoding="utf-8")


def update_publication_state(html: str, envelope_id: str, ctx: str) -> str:
    claim = re.compile(r"<p>本ページは<strong>公開承認済み.*?</p>", re.S)
    existing = re.compile(STATE_MARK + r"\s*<p>.*?</p>", re.S)
    replacement = (
        STATE_MARK
        + "\n  <p><strong>公開状態: 図を埋め込んだため再承認待ち。</strong>"
        "本文の内容は envelope <code>metadata/publication/"
        + envelope_id
        + "/decision.json</code> の承認（status <code>approved</code>）の対象だが、"
        "<code>artifact_sha256</code> は図を埋め込む前の HTML の値であり、現行 HTML とは一致しない。"
        "図を含む版の公開には、再承認と <code>decision.json</code> の hash 再固定、"
        "本節の監査記録の更新が必要である。</p>"
    )
    if existing.search(html):
        return existing.sub(replacement, html, count=1)
    matched = claim.search(html)
    if matched is None:
        fail(ctx, "publication-state paragraph not found")
    return html[: matched.start()] + replacement + html[matched.end():]


def main(argv: list) -> None:
    wanted = {item.lower() for item in argv}
    pages = sorted(PUBLICATION.glob("research_*.html"))
    pages = [p for p in pages if not wanted or p.stem.split("research_", 1)[1] in wanted]
    if not pages:
        fail("all", f"no page matched {sorted(wanted)}")
    for page in pages:
        name = page.stem.split("research_", 1)[1]
        figures_dir = PUBLICATION / "figures" / name
        provenance_path = ANALYSIS / f"{name}-page-charts/provenance.json"
        if not provenance_path.exists():
            fail(name, f"provenance not found: {provenance_path.relative_to(REPO)}; run the chart generator first")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        embed(name, page, figures_dir, provenance)
        print(f"embedded {len(provenance['figures'])} figures into {page.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1:])
