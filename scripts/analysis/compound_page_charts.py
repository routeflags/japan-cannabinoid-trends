#!/usr/bin/env python3
"""publication/research_<compound>.html の2図(SVG/PNG/CSV)を物質ごとに生成する。

図1: 検索関心度の5年推移(折れ線)。ページの「5年データサマリー」が引用する
run の raw 系列(records_*.json、単独系列)を入力とする。

図2: 動画の年次公開件数(縦棒)。ページの「年次分布」表を機械抽出したもの。
raw payload は Git 非追跡・非公開のため、図2は公開済み表の可視化であり、
リポジトリの raw からは再計算できない。

入力はページ記載値と raw の両方で検証する。合計・平均・ピーク・最新値・
観測範囲のいずれかが食い違えば生成は失敗する(可視化ではなく出所の変化を
疑う)。図は新しい数値を作らない。

stdlib のみで動く。SVG に生成時刻を埋め込まない。PNG は rsvg-convert が
あれば描画する。リポジトリ root から全物質、または物質を指定して:

    python3 scripts/analysis/compound_page_charts.py
    python3 scripts/analysis/compound_page_charts.py cbd thc
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STUDY = REPO / "datasets/cannabinoid-raw-collection"
RAW_GT = STUDY / "data/raw/google_trends"
ANALYSIS = STUDY / "analysis"
PUBLICATION = REPO / "publication"
# 図本体は公開層に置き、ページから相対参照する。CSV と出所記録は study 側に残す。
FIGURES = PUBLICATION / "figures"

FONT = "system-ui, sans-serif"
BLUE = "#1f5fa8"
RED = "#b3261e"

# 見出しの語をファイル名に使うための対応表。ここに無い語は小文字化するだけ。
SLUG_WORDS = {"収集": "collection", "リキッド": "liquid"}

RUN_RE = r"\d{8}T\d{6}Z-[a-z0-9-]+"


def fail(ctx: str, message: str) -> None:
    raise SystemExit(f"compound_page_charts[{ctx}]: {message}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", html).split())


def slugify(text: str) -> str:
    return "-".join(SLUG_WORDS.get(token, token.lower()) for token in text.split())


def h2_sections(html: str) -> list:
    """<h2> 単位に分割する。見出しの語は図のラベル決定に使う。"""
    sections = []
    for part in re.split(r"(?=<h2[^>]*>)", html):
        matched = re.match(r"<h2[^>]*>(.*?)</h2>", part, re.S)
        if matched:
            sections.append((strip_tags(matched.group(1)), part))
    return sections


def two_column_rows(table_html: str) -> list:
    return [
        (strip_tags(key), strip_tags(value))
        for key, value in re.findall(
            r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", table_html, re.S
        )
    ]


def first_number(text: str, ctx: str, field: str) -> str:
    matched = re.search(r"-?\d+(?:\.\d+)?", text)
    if matched is None:
        fail(ctx, f"{field}: no numeric value in {text!r}")
    return matched.group(0)


def parse_trends(name: str, html: str) -> dict:
    """5年サマリー表と、その直後に引用された run を取り出す。"""
    section = next((part for heading, part in h2_sections(html) if "Google Trends 検索需要" in heading), None)
    if section is None:
        fail(name, "Google Trends 検索需要 section not found")
    matched = re.search(r"<h3>5年データサマリー[^<]*</h3>(.*?)</table>", section, re.S)
    if matched is None:
        fail(name, "5-year summary table not found")
    cells = dict(two_column_rows(matched.group(1)))
    run = re.search(RUN_RE, section[matched.end():])
    if run is None:
        fail(name, "run id not found after the 5-year summary table")
    return {"cells": cells, "run_id": run.group(0)}


def load_series(name: str, run_id: str) -> tuple:
    """ページが引用する run の raw 系列を読む。run ディレクトリは一意に決まること。"""
    run_dirs = sorted(RAW_GT.glob(f"{run_id}*"))
    if len(run_dirs) != 1:
        fail(name, f"expected exactly one raw dir for {run_id}, found {len(run_dirs)}")
    record_files = sorted(run_dirs[0].glob("records_*.json"))
    if len(record_files) != 1:
        fail(name, f"expected exactly one records file in {run_dirs[0].name}")
    doc = json.loads(record_files[0].read_text(encoding="utf-8"))
    points = [(row["date"], int(row["value"])) for row in doc["data"]]
    if not points:
        fail(name, "raw series is empty")
    return points, run_dirs[0], record_files[0]


def check_against_page(name: str, cells: dict, points: list, run_dir: Path) -> dict:
    """図にする前に、ページ記載値と raw が一致することを確かめる。"""
    values = [v for _, v in points]
    mean_text = cells.get("5年平均")
    if mean_text is None:
        fail(name, "5年平均 row missing")
    mean_number = first_number(mean_text, name, "5年平均")
    decimals = len(mean_number.split(".")[1]) if "." in mean_number else 0
    mean = round(sum(values) / len(values), decimals)
    if f"{mean:.{decimals}f}" != mean_number:
        fail(name, f"5年平均 mismatch: raw {mean:.{decimals}f} vs page {mean_text!r}")

    peak_text = cells.get("ピーク", "")
    peak_date = re.search(r"\d{4}-\d{2}-\d{2}", peak_text)
    peak_value = re.search(r"値:\s*(\d+)", peak_text)
    if peak_date is None or peak_value is None:
        fail(name, f"peak row not parseable: {peak_text!r}")
    peak = max(values)
    if peak != int(peak_value.group(1)):
        fail(name, f"peak value mismatch: raw {peak} vs page {peak_value.group(1)}")
    peak_dates = [d for d, v in points if v == peak]
    if peak_date.group(0) not in peak_dates:
        fail(name, f"peak date mismatch: raw {peak_dates} vs page {peak_date.group(0)}")

    latest_text = cells.get("最新値")
    if latest_text is None:
        fail(name, "最新値 row missing")
    if points[-1][1] != int(first_number(latest_text, name, "最新値")):
        fail(name, f"latest value mismatch: raw {points[-1][1]} vs page {latest_text!r}")

    range_text = cells.get("観測範囲（返却点の範囲）") or cells.get("観測範囲")
    if range_text is None:
        fail(name, "観測範囲 row missing")
    range_dates = re.findall(r"\d{4}-\d{2}-\d{2}", range_text)
    if len(range_dates) != 2:
        fail(name, f"観測範囲 not parseable: {range_text!r}")
    if (points[0][0], points[-1][0]) != tuple(range_dates):
        fail(name, f"observed range mismatch: raw {points[0][0]}..{points[-1][0]} vs page {range_dates}")
    weeks = re.search(r"(\d+)\s*週", range_text)
    if weeks is not None and int(weeks.group(1)) != len(points):
        fail(name, f"week count mismatch: raw {len(points)} vs page {weeks.group(1)}")

    return {
        "points": len(points),
        "mean": mean,
        "decimals": decimals,
        "max": peak,
        "max_dates": peak_dates,
        "latest": {"date": points[-1][0], "value": points[-1][1]},
        "nonzero_weeks": sum(1 for v in values if v != 0),
        "observed_start": points[0][0],
        "observed_end": points[-1][0],
    }

def parse_yearly(name: str, html: str) -> list:
    """ページの「年次分布」表を、所属する節の見出しと出所付きで取り出す。"""
    figures = []
    for heading, section in h2_sections(html):
        if "の月次公開日件数" not in heading:
            continue
        subject = heading.split("の月次公開日件数")[0].split("独自データ: ")[-1].strip()
        for matched in re.finditer(r"<h3>(.*?)</h3>(.*?)</table>", section, re.S):
            title = strip_tags(matched.group(1))
            if "年次分布" not in title:
                continue
            rows = [
                (year, int(count.replace(",", "")))
                for year, count in re.findall(
                    r"<tr><td>(\d{4})</td><td>([\d,]+)</td></tr>", matched.group(2)
                )
            ]
            if not rows:
                fail(name, f"empty yearly table under {title!r}")
            if [y for y, _ in rows] != sorted({y for y, _ in rows}):
                fail(name, f"yearly years are not strictly ascending under {title!r}")
            before = section[: matched.start()]
            run = re.findall(RUN_RE, before)
            returned = re.findall(r"<td>返却件数</td>\s*<td>\s*(?:<strong>)?([\d,]+)", before)
            observed = re.findall(
                r"<td>観測公開日範囲[^<]*</td>\s*<td>\s*(\d{4}-\d{2}-\d{2})\s*〜\s*(\d{4}-\d{2}-\d{2})",
                before,
            )
            if not run or not returned:
                fail(name, f"run/返却件数 not found for yearly table {title!r}")
            total = int(returned[-1].replace(",", ""))
            if sum(count for _, count in rows) != total:
                fail(
                    name,
                    f"yearly sum {sum(c for _, c in rows)} != 返却件数 {total} for {title!r}",
                )
            label = title.replace("の年次分布", "").strip()
            if label in ("", "年次分布"):
                label = ""
            figures.append(
                {
                    "subject": subject,
                    "label": label,
                    "slug": slugify(label or subject),
                    "heading": heading,
                    "run_id": run[-1],
                    "returned": total,
                    "observed_start": observed[-1][0] if observed else None,
                    "observed_end": observed[-1][1] if observed else None,
                    "rows": rows,
                }
            )
    return figures


def common_scale_run(name: str, html: str) -> dict:
    """5年共通スケール（compare_terms）の 出所 と、その直前の表を取り出す。

    単独系列の 出所 も ``today 5-y`` を含むため、「comparison 成果物を持つ run
    を引用している出所」だけを候補にする。候補が複数なら失敗させる。
    """
    candidates = {}
    # 「出所:」「出所（5年）:」など接尾辞付きの見出しも拾う。
    for matched in re.finditer(r"<p><strong>出所[^<]{0,16}[:：]</strong>(.*?)</p>", html, re.S):
        paragraph = matched.group(1)
        if "today 5-y" not in paragraph:
            continue
        run = re.search(RUN_RE, paragraph)
        if run is None:
            continue
        run_id = run.group(0)
        run_dirs = sorted(RAW_GT.glob(f"{run_id}*"))
        if len(run_dirs) != 1 or not list(run_dirs[0].glob("comparison_*.json")):
            continue
        tables = list(re.finditer(r"<table>(.*?)</table>", html[: matched.start()], re.S))
        if not tables:
            fail(name, f"no table before the common-scale citation of {run_id}")
        candidates.setdefault(run_id, tables[-1].group(1))
    if len(candidates) != 1:
        fail(name, f"expected one 5-year common-scale run, got {sorted(candidates)}")
    run_id = next(iter(candidates))
    page_means = {}
    for row in re.findall(r"<tr>(.*?)</tr>", candidates[run_id], re.S):
        cells = [strip_tags(cell) for cell in re.findall(r"<td>(.*?)</td>", row, re.S)]
        if len(cells) < 2 or cells[0] == "検索語":
            continue
        term = cells[0].split("（")[0].strip()
        if re.fullmatch(r"[\d.]+", cells[1]):
            page_means[term] = cells[1]
    return {"run_id": run_id, "page_means": page_means}


def load_comparison(name: str, run_id: str) -> tuple:
    run_dirs = sorted(RAW_GT.glob(f"{run_id}*"))
    if len(run_dirs) != 1:
        fail(name, f"expected one raw dir for {run_id}")
    artifacts = sorted(run_dirs[0].glob("comparison_*.json"))
    if len(artifacts) != 1:
        fail(name, f"expected one comparison artifact in {run_dirs[0].name}")
    doc = json.loads(artifacts[0].read_text(encoding="utf-8"))
    meta = json.loads((run_dirs[0] / "run_metadata.json").read_text(encoding="utf-8"))
    query_id = meta.get("query_provenance", {}).get("query_id", "")
    return doc, artifacts[0], query_id


def annual_means(doc: dict) -> tuple:
    """週次共通スケール値の暦年（週開始日）平均と、年の完全性を返す。

    年の部分性は、年間の週数が完全な年に比べて少ないことで判定する（推定しない）。
    """
    terms = doc["terms"]
    by_year: dict = {}
    for row in doc["data"]:
        year = row["date"][:4]
        bucket = by_year.setdefault(year, {term: [] for term in terms})
        for term in terms:
            bucket[term].append(row[term])
    weeks = {year: len(bucket[terms[0]]) for year, bucket in by_year.items()}
    full = max(weeks.values())
    annual = {
        term: {
            year: sum(by_year[year][term]) / len(by_year[year][term]) for year in by_year
        }
        for term in terms
    }
    return terms, annual, {year: (count >= full - 3) for year, count in weeks.items()}, weeks


def check_common_scale(name: str, doc: dict, page_means: dict) -> dict:
    terms = doc["terms"]
    means = {term: round(sum(row[term] for row in doc["data"]) / len(doc["data"]), 4) for term in terms}
    for term, value in page_means.items():
        if term not in means:
            fail(name, f"page term {term} not in the comparison request {terms}")
        if f"{means[term]:.4f}" != value:
            fail(name, f"{term} common-scale mean mismatch: raw {means[term]:.4f} vs page {value}")
    if not any(term in page_means for term in terms):
        fail(name, "no page term matched the comparison request")
    return means

def write_csv(path: Path, header: list, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def svg_head(width: int, height: int, left: int, label: str, title: str, subtitle: str, notes: list) -> list:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        # 以降のテキストはグループの font-family を継承する。
        f'<g font-family="{FONT}">',
        f'<text x="{left}" y="34" font-size="19" font-weight="600">{title}</text>',
        f'<text x="{left}" y="58" font-size="12.5" fill="#444">{subtitle}</text>',
    ]
    for offset, note in enumerate(notes):
        parts.append(f'<text x="{left}" y="{78 + 18 * offset}" font-size="12" fill="{RED}">{note}</text>')
    return parts


def trends_svg(points: list, meta: dict) -> str:
    width, height = 960, 470
    left, right, top, bottom = 78, 36, 110, 74
    plot_w = width - left - right
    plot_h = height - top - bottom
    n = len(points)
    mean = meta["mean"]

    def x(i: int) -> float:
        return left + (plot_w * i / (n - 1))

    def y(v: float) -> float:
        return top + plot_h * (1 - v / 100)

    parts = svg_head(
        width, height, left, f"{meta['compound']} Google Trends standalone series, Japan, 5 years",
        f"{meta['compound']} 検索関心度の5年推移",
        f"Google Trends 日本 JP / today 5-y / {meta['observed_start']} 〜 {meta['observed_end']} {n}週 / run {meta['run_id']}",
        ["相対指数(系列最大=100)。絶対検索数ではなく他系列と比較不可。"],
    )
    for value in (0, 25, 50, 75, 100):
        gy = y(value)
        color = "#d0d0d0" if value else "#888"
        parts.append(f'<line x1="{left}" y1="{gy:.1f}" x2="{left + plot_w}" y2="{gy:.1f}" stroke="{color}"/>')
        parts.append(f'<text x="{left - 10}" y="{gy + 4:.1f}" text-anchor="end" font-size="12">{value}</text>')
    seen: set = set()
    last_year_x = None
    for i, (date, _) in enumerate(points):
        year = date[:4]
        if year in seen:
            continue
        seen.add(year)
        parts.append(f'<line x1="{x(i):.1f}" y1="{top}" x2="{x(i):.1f}" y2="{top + plot_h}" stroke="#e6e6e6"/>')
        # 年跨ぎ直後の点は前年ラベルと重なるため、幅が足りない年は目盛りだけ描く。
        if last_year_x is None or x(i) - last_year_x >= 36:
            parts.append(f'<text x="{x(i):.1f}" y="{top + plot_h + 22}" text-anchor="middle" font-size="12">{year}</text>')
            last_year_x = x(i)
    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(points))
    parts.append(f'<polyline points="{line}" fill="none" stroke="{BLUE}" stroke-width="1.6"/>')
    parts.append(f'<line x1="{left}" y1="{y(mean):.1f}" x2="{left + plot_w}" y2="{y(mean):.1f}" stroke="{RED}" stroke-dasharray="5 4"/>')
    # 平均の注記は凡例として左上に置く（折れ線やピーク注記と重ならせない）。
    parts.append(f'<line x1="{left + 8}" y1="{top + 16}" x2="{left + 40}" y2="{top + 16}" stroke="{RED}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    parts.append(f'<text x="{left + 46}" y="{top + 20}" font-size="12" fill="{RED}">平均 {mean:.{meta["decimals"]}f}（週次平均）</text>')
    peak_i = next(i for i, (_, v) in enumerate(points) if v == meta["max"])
    px, py = x(peak_i), y(meta["max"])
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{RED}"/>')
    anchor = "end" if px > left + plot_w - 170 else "start"
    label_x = px - 8 if anchor == "end" else px + 8
    parts.append(f'<text x="{label_x:.1f}" y="{py - 10:.1f}" text-anchor="{anchor}" font-size="12" fill="{RED}">{meta["max_dates"][0]} = {meta["max"]}</text>')
    lx, ly = x(n - 1), y(points[-1][1])
    parts.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{BLUE}"/>')
    # 最新値がピークと一致する系列（THCNM など）はピーク注記に兼ねる。
    if points[-1][1] != meta["max"]:
        parts.append(f'<text x="{lx - 4:.1f}" y="{ly + 20:.1f}" text-anchor="end" font-size="12" fill="{BLUE}">最新 {points[-1][1]}</text>')
    parts.append(f'<text x="{left}" y="{height - 22}" font-size="11.5" fill="#666">週次{n}点 平均{mean:.{meta["decimals"]}f} 非ゼロ{meta["nonzero_weeks"]}週 相対指数であり絶対検索数ではない</text>')
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"

def yearly_svg(meta: dict) -> str:
    yearly = meta["rows"]
    width, height = 960, 500
    left, right, top, bottom = 64, 24, 130, 96
    plot_w = width - left - right
    plot_h = height - top - bottom
    # 観測公開日の範囲が年を覆っていない年は部分年（件数はその日数分だけ）。
    partial_years = [
        year
        for year, _ in yearly
        if not (
            meta["observed_start"] <= f"{year}-01-01"
            and meta["observed_end"] >= f"{year}-12-31"
        )
    ]
    peak_count = max(c for _, c in yearly)
    # 目盛り単位を値の大きさに合わせ、ピークが上端に張り付かないようにする。
    unit = 10 if peak_count <= 40 else 20 if peak_count <= 90 else 40
    y_max = ((peak_count + unit - 1) // unit) * unit
    step = plot_w / len(yearly)
    bar_w = min(step * 0.62, 52)
    title_subject = meta["subject"]
    suffix = f"（{meta['label']}）" if meta["label"] else ""

    def y(v: float) -> float:
        return top + plot_h * (1 - v / y_max)

    def cx(i: int) -> float:
        return left + step * i + step / 2

    parts = svg_head(
        width, height, left, f"{title_subject} yearly video counts in returned sample",
        f"{title_subject} 動画の年次公開件数{suffix}",
        f"返却 {meta['returned']}件 / "
        + (
            f"{meta['observed_start']} 〜 {meta['observed_end']} の公開日 / "
            if meta["observed_start"] and meta["observed_end"]
            else "公開日範囲はページに記載なし / "
        )
        + f"run {meta['run_id']}",
        [
            "返却サンプル内の年次公開日件数であり、YouTube 全体の投稿数ではない。",
            "date_filter の異なる run とは比較せず、複数 run を合算しない。",
        ],
    )
    value = 0
    while value <= y_max:
        gy = y(value)
        color = "#d0d0d0" if value else "#888"
        parts.append(f'<line x1="{left}" y1="{gy:.1f}" x2="{left + plot_w}" y2="{gy:.1f}" stroke="{color}"/>')
        parts.append(f'<text x="{left - 10}" y="{gy + 4:.1f}" text-anchor="end" font-size="12">{value}</text>')
        value += unit
    peak_index = next(i for i, (_, c) in enumerate(yearly) if c == peak_count)
    for i, (year, count) in enumerate(yearly):
        bx = cx(i) - bar_w / 2
        by = y(count)
        color = RED if i == peak_index else BLUE
        parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{top + plot_h - by:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{cx(i):.1f}" y="{by - 6:.1f}" text-anchor="middle" font-size="12">{count}</text>')
        mark = "*" if year in partial_years else ""
        parts.append(f'<text x="{cx(i):.1f}" y="{top + plot_h + 22}" text-anchor="middle" font-size="{10 if len(yearly) > 16 else 12}">{year}{mark}</text>')
    parts.append(f'<text x="{cx(peak_index):.1f}" y="{y(peak_count) - 24:.1f}" text-anchor="middle" font-size="12" fill="{RED}">ピーク {yearly[peak_index][0]}年</text>')
    if partial_years:
        parts.append(
            f'<text x="{left}" y="{height - 58}" font-size="11.5" fill="{RED}">'
            f"* 部分年（{'、'.join(partial_years)}）: 観測 {meta['observed_start']} 〜 "
            f"{meta['observed_end']} の分だけ。年の比較に使わない。</text>"
        )
    parts.append(f'<text x="{left}" y="{height - 40}" font-size="11.5" fill="#666">公開日がサンプルにない年は行を作らない。未取得を0として扱わない。</text>')
    parts.append(f'<text x="{left}" y="{height - 22}" font-size="11.5" fill="#666">年次合計は返却件数と一致する({meta["returned"]}件)。</text>')
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def bubble_svg(meta: dict) -> str:
    """物質×年のバブルマトリクス（同一 compare_terms 要求の共通スケール）。"""
    terms = meta["terms"]
    annual = meta["annual"]
    complete = meta["complete"]
    years = sorted(annual[terms[0]])
    vmax = max(v for term in terms for v in annual[term].values()) or 1.0

    width = 960
    left, right = 176, 40
    top, bottom = 158, 96
    row_h = 74
    height = top + row_h * len(terms) + bottom
    col_w = (width - left - right) / len(years)
    r_max, r_min = 30.0, 2.0

    def cx(index: int) -> float:
        return left + col_w * index + col_w / 2

    def cy(index: int) -> float:
        return top + row_h * index + row_h / 2

    def color(value: float) -> str:
        t = min(value / vmax, 1.0)
        light = (0xDC, 0xE8, 0xF6)
        dark = (0x12, 0x3F, 0x6D)
        rgb = tuple(round(lo + (hi - lo) * t) for lo, hi in zip(light, dark))
        return "#%02x%02x%02x" % rgb

    parts = svg_head(
        width,
        height,
        left - 60,
        f"{meta['compound']} annual search interest bubble matrix",
        f"{'・'.join(terms)} — 年間検索ボリューム（共通スケール）",
        f"run {meta['run_id']} / {meta['timeframe']} / {meta['geo']} / {meta['start']} 〜 {meta['end']}",
        [
            "値は同一 compare_terms 要求の共通スケール（要求内の最大 = 100）。要求間・単独系列とは換算不可。",
            "円の面積は年間平均に比例（極小値は最小半径）。0 は相対指数の最小値への丸めで、欠測ではない。",
        ],
    )

    for index, year in enumerate(years):
        mark = "" if complete[year] else "*"
        parts.append(
            f'<text x="{cx(index):.1f}" y="{top - 18}" text-anchor="middle" font-size="15" '
            f'font-weight="600" fill="#333">{year}{mark}</text>'
        )
    for index, term in enumerate(terms):
        y = cy(index)
        parts.append(
            f'<line x1="{left - 8}" y1="{y + row_h / 2:.1f}" x2="{width - right}" '
            f'y2="{y + row_h / 2:.1f}" stroke="#ececec"/>'
        )
        parts.append(
            f'<text x="{left - 16}" y="{y + 5:.1f}" text-anchor="end" font-size="15" '
            f'fill="#222">{term}</text>'
        )
        for index_year, year in enumerate(years):
            value = annual[term][year]
            # 面積を値に比例させる（radius ∝ √value）。極小値だけ最小半径で可視化する。
            radius = max(r_min, r_max * (value / vmax) ** 0.5)
            x, y = cx(index_year), cy(index)
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color(value)}"/>'
            )
            label = f"{value:.1f}"
            if radius >= 14:
                fill = "#ffffff" if value / vmax > 0.45 else "#123f6d"
                parts.append(
                    f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="12" '
                    f'fill="{fill}">{label}</text>'
                )
            else:
                parts.append(
                    f'<text x="{x + radius + 5:.1f}" y="{y + 4:.1f}" text-anchor="start" '
                    f'font-size="12" fill="#555">{label}</text>'
                )

    footnote_y = top + row_h * len(terms) + 24
    partial = [f"{year}（{meta['weeks'][year]}週）" for year in years if not complete[year]]
    parts.append(
        f'<text x="{left - 60}" y="{footnote_y}" font-size="11.5" fill="#666">'
        f"* 部分年: {'、'.join(partial) if partial else 'なし'}。完全年は 52 週前後。"
        f"値は年間平均の相対指数（要求内最大 = 100）。</text>"
    )
    return "\n".join(parts) + "\n</g>\n</svg>\n"


def render_png(tool: str, svg_path: Path, png_path: Path) -> str:
    subprocess.run([tool, "-w", "1920", str(svg_path), "-o", str(png_path)], check=True)
    done = subprocess.run([tool, "--version"], capture_output=True, text=True, check=True)
    return done.stdout.strip().splitlines()[0]


def write_readme(out: Path, name: str, trends: dict, yearly: list) -> None:
    lines = [
        f"# {trends['compound']} の2図\n",
        f"`publication/research_{name}.html` の系列を図にした成果物。数値はページ記載と一致させており、\n"
        "ここで新しい値は作らない。図本体は `publication/figures/` に置き、このディレクトリには\n"
        "CSV（元系列）と出所記録を残す。\n",
        "## 図\n",
        "| 図 | ファイル | 出所 |",
        "|---|---|---|",
        f"| 検索関心度の5年推移（折れ線） | `trends-5y-standalone.{{svg,png}}` / `.csv` | "
        f"Google Trends run `{trends['run_id']}`（{trends['stats']['observed_start']} 〜 "
        f"{trends['stats']['observed_end']}、{trends['stats']['points']} 週） |",
    ]
    for figure in yearly:
        label = f"{figure['label']}・" if figure["label"] else ""
        lines.append(
            f"| 動画の年次公開件数（{label}{figure['returned']} 件） | "
            f"`{figure['file']}.{{svg,png}}` / `.csv` | YouTube run `{figure['run_id']}` |"
        )
    lines.append(
        f"| 年間検索ボリュームのバブルマトリクス | `{trends['matrix_id']}.{{svg,png}}` / `.csv` | "
        f"Google Trends run `{trends['matrix_run']}`（compare_terms、同一要求内で比較） |"
    )
    lines += [
        "",
        "## 読み方と制約",
        "",
        "- 推移図の値は**単独系列**の相対指数（この系列の最大が 100）。共通スケール要求の値とは",
        "  別の物差しで、換算できない。絶対検索数でもない。",
        "- 年次件数は**返却サンプル内**の公開日件数であり、YouTube 全体の投稿数ではない。",
        "  公開日がサンプルにない年は行を作らず、0 として埋めない。観測範囲が年を覆わない年は",
        "  部分年として `*` を付け、その年の日数分の件数であることを図に明記する。",
        "- 年次表は `publication/` の公開済み集計からの機械抽出である。raw payload は Git",
        "  非追跡・非公開のため、本リポジトリの raw からは再計算できない。",
        "- バブルマトリクスは同じ `compare_terms` 要求の共通スケール内だけで比較する。要求間・単独系列とは",
        "  換算できない（各要求はその中の最大 = 100 で正規化される）。年間平均は週次値の暦年平均で、",
        "  部分年は週数で明示し、欠測を補わない。",
        "- 3 つの図は異なる現象の測定値であり、合算・比較しない（source separation）。",
        "",
        "## 生成",
        "",
        "```bash",
        f"python3 scripts/analysis/compound_page_charts.py {name}",
        "```",
        "",
        "stdlib のみで動き、SVG に生成時刻を埋め込まない。PNG は `rsvg-convert` がある場合のみ",
        "生成し、無ければ SVG のみを作って `provenance.json` に記録する。",
        "",
        "## 公開スコープ",
        "",
        f"- 図本体は `publication/figures/{out.name.removesuffix('-page-charts')}/` にあり、ページから",
        "  `figures/<compound>/…` で相対参照する。差し込みは",
        "  `scripts/publication/embed_compound_figures.py` が行う。",
        "- ページは hash 単位の公開承認であり、図を差し込むと SHA-256 が変わるため再承認が要る。",
        "- 配布スライス `datasets/cannabinoid-platform-trends/` には含めない。",
        "",
    ]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")


def compound_pages() -> list:
    return sorted(PUBLICATION.glob("research_*.html"))


def build(name: str, page: Path, renderer: str | None) -> dict:
    html = page.read_text(encoding="utf-8")
    trends = parse_trends(name, html)
    display = re.search(r"独自データ:\s*(.+?)\s*の Google Trends 検索需要", html)
    if display is None:
        fail(name, "compound display name not found")
    compound = display.group(1)
    slug = slugify(compound)
    out = ANALYSIS / f"{slug}-page-charts"
    figs = FIGURES / slug
    out.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    points, run_dir, record_file = load_series(name, trends["run_id"])
    stats = check_against_page(name, trends["cells"], points, run_dir)
    meta = {
        "compound": compound,
        "run_id": trends["run_id"],
        "observed_start": stats["observed_start"],
        "observed_end": stats["observed_end"],
        "mean": stats["mean"],
        "decimals": stats["decimals"],
        "max": stats["max"],
        "max_dates": stats["max_dates"],
        "nonzero_weeks": stats["nonzero_weeks"],
    }
    trends_csv = out / "trends-5y-standalone.csv"
    trends_svg_path = figs / "trends-5y-standalone.svg"
    trends_png = figs / "trends-5y-standalone.png"
    write_csv(trends_csv, ["date", "value"], points)
    trends_svg_path.write_text(trends_svg(points, meta), encoding="utf-8")
    renderer_version = render_png(renderer, trends_svg_path, trends_png) if renderer else None
    outputs = [trends_csv, trends_svg_path]
    if renderer_version:
        outputs.append(trends_png)

    yearly_records = []
    for figure in parse_yearly(name, html):
        stem = f"youtube-yearly-{figure['slug']}"
        csv_path = out / f"{stem}.csv"
        svg_path = figs / f"{stem}.svg"
        png_path = figs / f"{stem}.png"
        write_csv(csv_path, ["year", "count"], figure["rows"])
        svg_path.write_text(
            yearly_svg(
                {
                    "subject": figure["subject"],
                    "label": figure["label"],
                    "run_id": figure["run_id"],
                    "returned": figure["returned"],
                    "observed_start": figure["observed_start"],
                    "observed_end": figure["observed_end"],
                    "rows": figure["rows"],
                }
            ),
            encoding="utf-8",
        )
        if renderer:
            renderer_version = render_png(renderer, svg_path, png_path)
        outputs += [csv_path, svg_path] + ([png_path] if renderer_version else [])
        yearly_records.append({**figure, "file": stem, "svg": svg_path, "csv": csv_path})

    # 共通スケール（compare_terms）のバブルマトリクス。同じ要求の中だけで比較する。
    common = common_scale_run(name, html)
    comparison, comparison_file, query_id = load_comparison(name, common["run_id"])
    means = check_common_scale(name, comparison, common["page_means"])
    request_terms, annual, complete, weeks = annual_means(comparison)
    # ページが載せていない語は描かない（ページの公開範囲を図が広げないため）。
    terms = [term for term in request_terms if term in common["page_means"]]
    if not terms:
        fail(name, "no page term to plot in the bubble matrix")
    matrix_slug = re.sub(r"^comparison-(5y-)?", "", query_id or "request").replace("current-", "")
    matrix_id = f"bubble-matrix-{matrix_slug}"
    matrix_meta = {
        "compound": compound,
        "run_id": common["run_id"],
        "timeframe": comparison["timeframe"],
        "geo": comparison["geo"],
        "start": comparison["data"][0]["date"],
        "end": comparison["data"][-1]["date"],
        "terms": terms,
        "annual": annual,
        "complete": complete,
        "weeks": weeks,
    }
    matrix_csv = out / f"{matrix_id}.csv"
    matrix_svg = figs / f"{matrix_id}.svg"
    matrix_png = figs / f"{matrix_id}.png"
    write_csv(
        matrix_csv,
        ["term", "year", "annual_mean", "weeks", "complete_year"],
        [
            [term, year, f"{annual[term][year]:.4f}", weeks[year], "yes" if complete[year] else "no"]
            for term in terms
            for year in sorted(annual[term])
        ],
    )
    matrix_svg.write_text(bubble_svg(matrix_meta), encoding="utf-8")
    if renderer:
        renderer_version = render_png(renderer, matrix_svg, matrix_png)
    matrix_outputs = [matrix_csv, matrix_svg] + ([matrix_png] if renderer_version else [])
    outputs += matrix_outputs
    write_readme(
        out,
        name,
        {
            "compound": compound,
            "run_id": trends["run_id"],
            "stats": stats,
            "matrix_id": matrix_id,
            "matrix_run": common["run_id"],
        },
        yearly_records,
    )
    provenance = {
        "schema_version": "1.0.0",
        "record": "analysis_derivation",
        "analysis_id": f"{slug}-page-charts",
        "page": str(page.relative_to(REPO)),
        "page_sha256": sha256(page),
        "report": "README.md",
        "figures": [
            {
                "id": "trends-5y-standalone",
                "title": f"{compound} 検索関心度の5年推移",
                "source": {
                    "source_id": "google-trends",
                    "run_id": trends["run_id"],
                    "geo": "JP",
                    "timeframe": "today 5-y",
                    "normalization": f"standalone series max = {stats['max']} ({stats['max_dates'][0]})",
                },
                "inputs": [
                    {"path": str(record_file.relative_to(REPO)), "sha256": sha256(record_file)},
                    {"path": str((run_dir / "run_metadata.json").relative_to(REPO)), "sha256": sha256(run_dir / "run_metadata.json")},
                ],
                "stats": stats,
                "verification": "page 5-year summary mean/peak/latest/observed range matched the raw series",
            },
            {
                "id": matrix_id,
                "title": f"{'・'.join(terms)} — 年間検索ボリューム（共通スケール）",
                "source": {
                    "source_id": "google-trends",
                    "run_id": common["run_id"],
                    "query_id": query_id,
                    "geo": comparison["geo"],
                    "timeframe": comparison["timeframe"],
                    "terms": terms,
                    "request_terms": request_terms,
                    "normalization": "same request max = 100; comparable only within this request",
                },
                "inputs": [
                    {
                        "path": str(comparison_file.relative_to(REPO)),
                        "sha256": sha256(comparison_file),
                    }
                ],
                "derivation": (
                    "annual mean of the weekly common-scale index, bucketed by the UTC year of "
                    "the week-start date; partial years flagged by week count (not imputed)"
                ),
                "stats": {
                    "years": sorted(annual[terms[0]]),
                    "weeks_per_year": weeks,
                    "complete_years": sorted(y for y, ok in complete.items() if ok),
                    "mean_5y": {term: f"{means[term]:.4f}" for term in terms},
                    "page_terms_verified": common["page_means"],
                },
                "verification": "per-term 5-year means matched the page's 共通スケール table",
            },
            *[
                {
                    "id": f"youtube-yearly-{figure['slug']}",
                    "title": f"{figure['subject']} 動画の年次公開件数{('（' + figure['label'] + '）') if figure['label'] else ''}",
                    "source": {
                        "source_id": "youtube",
                        "run_id": figure["run_id"],
                        "returned_count": figure["returned"],
                        "observed_publish_start": figure["observed_start"],
                        "observed_publish_end": figure["observed_end"],
                        "partial_years": [
                            year
                            for year, _ in figure["rows"]
                            if not (
                                (figure["observed_start"] or "")
                                <= f"{year}-01-01"
                                and (figure["observed_end"] or "")
                                >= f"{year}-12-31"
                            )
                        ],
                        "note": "Yearly counts extracted from the published table in the page; raw payload is local-only.",
                    },
                    "years": len(figure["rows"]),
                    "yearly_sum": sum(c for _, c in figure["rows"]),
                    "verification": "yearly sum equals the published 返却件数",
                }
                for figure in yearly_records
            ],
        ],
        "not_comparable": "Trends relative index and YouTube sample counts measure different phenomena; never combined.",
        "png_renderer": renderer_version or "rsvg-convert not available; SVG only",
        "derived_by": "scripts/analysis/compound_page_charts.py",
        "publication_scope": "Analysis artifacts. Embedding into the page needs republication review; not done here.",
        "output_sha256": {str(path.relative_to(REPO)): sha256(path) for path in outputs},
    }
    (out / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "compound": compound,
        "dir": out.name,
        "trends": stats["points"],
        "yearly": [(f["label"] or f["subject"], f["returned"]) for f in yearly_records],
    }


def index_entry(page: Path) -> dict:
    html = page.read_text(encoding="utf-8")
    matched = re.search(r"独自データ:\s*(.+?)\s*の Google Trends 検索需要", html)
    if matched is None:
        fail(page.name, "compound display name not found")
    compound = matched.group(1)
    return {
        "compound": compound,
        "dir": f"{slugify(compound)}-page-charts",
        "yearly": len(parse_yearly(page.name, html)),
    }


def write_index(pages: list) -> None:
    entries = [index_entry(page) for page in pages]
    lines = [
        "# analysis — 図と集計の派生物\n",
        "`publication/research_*.html` の系列を可視化した成果物を置く。ここに raw は置かない。\n",
        "- `<compound>-page-charts/`: 物質ごとの図（推移・年次・バブルマトリクス）の CSV と出所記録",
        "- `cbd-common-scale-5y/`: CBD の共通スケール系列（`scripts/analysis/cbd_common_scale_plot.py`）\n",
        "## 物質別の図\n",
        "| 物質 | ディレクトリ | 検索推移 | 動画年次の図 | 共通スケール |",
        "|---|---|---|---|---|",
    ]
    for entry in entries:
        yearly = f"{entry['yearly']} 図" if entry["yearly"] else "なし"
        lines.append(f"| {entry['compound']} | `{entry['dir']}/` | 5年 | {yearly} | 5年（同一要求） |")
    lines += [
        "",
        "図ごとの出所・検証・制約は各ディレクトリの `README.md` と `provenance.json` にある。",
        "生成は全物質または物質を指定して:",
        "",
        "```bash",
        "python3 scripts/analysis/compound_page_charts.py",
        "python3 scripts/analysis/compound_page_charts.py cbd thc",
        "```",
        "",
        "スクリプトはページ記載値と raw を照合し、食い違えば生成を止める。図はこの階層の",
        "分析成果物であり、`publication/` への埋め込みは再公開審査の対象になる。",
        "",
    ]
    (ANALYSIS / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list) -> None:
    wanted = {item.lower() for item in argv}
    all_pages = compound_pages()
    pages = [p for p in all_pages if not wanted or p.stem.split("research_", 1)[1] in wanted]
    if not pages:
        fail("all", f"no page matched {sorted(wanted)}")
    renderer = shutil.which("rsvg-convert")
    built = []
    for page in pages:
        built.append(build(page.stem.split("research_", 1)[1], page, renderer))
    write_index(all_pages)
    print(f"built {len(built)} compound figure sets under {ANALYSIS.relative_to(REPO)}:")
    for item in built:
        yearly = ", ".join(f"{label}={count}" for label, count in item["yearly"]) or "none"
        print(f"  {item['compound']:8} {item['dir']:26} trends={item['trends']} yearly[{yearly}]")


if __name__ == "__main__":
    main(sys.argv[1:])
