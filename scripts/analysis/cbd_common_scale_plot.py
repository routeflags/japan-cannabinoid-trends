#!/usr/bin/env python3
"""Derive the CBD series and an SVG plot from the current 5-year common scale.

Source separation: the input is one Google Trends ``compare_terms`` run
(setA: CBD / THC / CBG / HHC / THCV, ``geo=JP``, ``today 5-y``, window
``2021-10-31_2026-11-08``).  Nothing else is joined to it, and the CBD values
are *not* the standalone CBD series: a common-scale value is normalised by the
largest point inside its own request, so the two are not convertible.

The script is stdlib-only on purpose: the repository has no plotting
dependency, and a text SVG stays reproducible without one.  It writes
``series.csv``, ``cbd-common-scale-5y.svg`` and ``provenance.json`` into the
study's ``analysis/`` directory (not ``publication/`` and not the release
slice).  Run it from the repository root:

    python3 scripts/analysis/cbd_common_scale_plot.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN_ID = "20261104T195126Z-google-trends-cannabinoid-raw-collection"
RUN_DIR = REPO / "datasets/cannabinoid-raw-collection/data/raw/google_trends" / RUN_ID
COMPARISON = RUN_DIR / "comparison_cbd-thc-cbg-hhc-thcv.json"
OUT = REPO / "datasets/cannabinoid-raw-collection/analysis/cbd-common-scale-5y"
WINDOW_ID = "2021-10-31_2026-11-08"

WIDTH, HEIGHT = 960, 460
LEFT, RIGHT, TOP, BOTTOM = 78, 36, 84, 74


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> dict:
    return json.loads(COMPARISON.read_text(encoding="utf-8"))


def stats(points: list[tuple[str, int]]) -> dict:
    values = [v for _, v in points]
    peak = max(values)
    return {
        "points": len(values),
        "mean": round(sum(values) / len(values), 4),
        "median": statistics.median(values),
        "max": peak,
        "max_dates": [d for d, v in points if v == peak],
        "min": min(values),
        "nonzero_weeks": sum(1 for v in values if v != 0),
        "zero_weeks": sum(1 for v in values if v == 0),
    }


def write_csv(doc: dict) -> None:
    terms = doc["terms"]
    with (OUT / "series.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["date", *terms])
        for row in doc["data"]:
            writer.writerow([row["date"], *(row[t] for t in terms)])


def write_svg(doc: dict, points: list[tuple[str, int]], cbd: dict) -> None:
    plot_w = WIDTH - LEFT - RIGHT
    plot_h = HEIGHT - TOP - BOTTOM
    n = len(points)

    def x(i: int) -> float:
        return LEFT + (plot_w * i / (n - 1))

    def y(v: float) -> float:
        return TOP + plot_h * (1 - v / 100)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-label="CBD Google Trends common scale, Japan, 5 years">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        f'<text x="{LEFT}" y="34" font-family="system-ui, sans-serif" font-size="19" '
        'font-weight="600" fill="#111">CBD — Google Trends 共通スケール（setA）</text>',
        f'<text x="{LEFT}" y="58" font-family="system-ui, sans-serif" font-size="12.5" fill="#444">'
        f'geo=JP / today 5-y / 窓 {WINDOW_ID} / {n} 週 / run {RUN_ID}</text>',
        f'<text x="{LEFT}" y="76" font-family="system-ui, sans-serif" font-size="12" fill="#b3261e">'
        f'相対指数（同じ要求内の最大 = 100）。単独系列とは換算できない。</text>',
    ]

    for value in (0, 25, 50, 75, 100):
        gy = y(value)
        parts.append(
            f'<line x1="{LEFT}" y1="{gy:.1f}" x2="{LEFT + plot_w}" y2="{gy:.1f}" '
            f'stroke="{"#d0d0d0" if value else "#888"}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{LEFT - 10}" y="{gy + 4:.1f}" text-anchor="end" '
            f'font-family="system-ui, sans-serif" font-size="12" fill="#444">{value}</text>'
        )

    year_start = {d[:4] for d, _ in points}
    seen: set[str] = set()
    for i, (date, _) in enumerate(points):
        year = date[:4]
        if year in seen or year not in year_start:
            continue
        seen.add(year)
        parts.append(
            f'<line x1="{x(i):.1f}" y1="{TOP}" x2="{x(i):.1f}" y2="{TOP + plot_h}" '
            'stroke="#e6e6e6" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x(i):.1f}" y="{TOP + plot_h + 22}" text-anchor="middle" '
            f'font-family="system-ui, sans-serif" font-size="12" fill="#444">{year}</text>'
        )

    polyline = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(points))
    parts.append(
        f'<polyline points="{polyline}" fill="none" stroke="#1f5fa8" stroke-width="1.8" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )

    parts.append(
        f'<line x1="{LEFT}" y1="{y(cbd["mean"]):.1f}" x2="{LEFT + plot_w}" '
        f'y2="{y(cbd["mean"]):.1f}" stroke="#b3261e" stroke-width="1.2" stroke-dasharray="5 4"/>'
    )
    parts.append(
        f'<text x="{LEFT + plot_w - 4}" y="{y(cbd["mean"]) - 6:.1f}" text-anchor="end" '
        f'font-family="system-ui, sans-serif" font-size="12" fill="#b3261e">'
        f'平均 {cbd["mean"]:.4f}</text>'
    )

    peak_i = next(i for i, (_, v) in enumerate(points) if v == cbd["max"])
    px, py = x(peak_i), y(cbd["max"])
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#b3261e"/>')
    parts.append(
        f'<text x="{px - 8:.1f}" y="{py - 10:.1f}" text-anchor="end" '
        f'font-family="system-ui, sans-serif" font-size="12" fill="#b3261e">'
        f'{cbd["max_dates"][0]} = 100</text>'
    )

    parts.append(
        f'<text x="{LEFT}" y="{HEIGHT - 22}" font-family="system-ui, sans-serif" font-size="11.5" '
        f'fill="#666">非ゼロ {cbd["nonzero_weeks"]} / ゼロ {cbd["zero_weeks"]} 週。'
        'Google Trends の相対指数であり、絶対検索数ではない。</text>'
    )
    parts.append("</svg>")
    (OUT / "cbd-common-scale-5y.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = load()
    points = [(row["date"], row["CBD"]) for row in doc["data"]]
    cbd = stats(points)
    write_csv(doc)
    write_svg(doc, points, cbd)

    provenance = {
        "schema_version": "1.0.0",
        "record": "analysis_derivation",
        "analysis_id": "cbd-common-scale-5y",
        "report": "README.md",
        "source": {
            "source_id": "google-trends",
            "run_id": RUN_ID,
            "query_id": "comparison-5y-setA",
            "geo": doc["geo"],
            "timeframe": doc["timeframe"],
            "window_id": WINDOW_ID,
            "collected_at": doc["collected_at"],
        },
        "source_files": [
            {
                "path": str(COMPARISON.relative_to(REPO)),
                "sha256": sha256(COMPARISON),
            },
            {
                "path": str((RUN_DIR / "run_metadata.json").relative_to(REPO)),
                "sha256": sha256(RUN_DIR / "run_metadata.json"),
            },
            {
                "path": str((RUN_DIR / "payload.json").relative_to(REPO)),
                "sha256": sha256(RUN_DIR / "payload.json"),
            },
            {
                "path": str((RUN_DIR / "artifact-manifest.json").relative_to(REPO)),
                "sha256": sha256(RUN_DIR / "artifact-manifest.json"),
            },
        ],
        "request_terms": doc["terms"],
        "reported_series": "CBD",
        "observed_start": points[0][0],
        "observed_end": points[-1][0],
        "normalization": "same request max = 100 (CBD 2025-08-31)",
        "cbd": cbd,
        "not_comparable": (
            "Common-scale values are normalised within this request and are not "
            "the standalone CBD series; neither is convertible to the other."
        ),
        "source_separation": (
            "One Google Trends compare_terms run only. No other source, window or "
            "run is joined to these values."
        ),
        "derived_by": "scripts/analysis/cbd_common_scale_plot.py",
        "generated_at": "2026-11-05",
        "outputs": ["series.csv", "cbd-common-scale-5y.svg"],
        "release_scope": (
            "Study analysis artifact. Not part of the cannabinoid-platform-trends "
            "release slice and not added to data-catalog.json."
        ),
    }
    (OUT / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUT.relative_to(REPO)}: n={cbd['points']} mean={cbd['mean']} "
          f"nonzero={cbd['nonzero_weeks']} max={cbd['max']}@{cbd['max_dates']}")


if __name__ == "__main__":
    main()
