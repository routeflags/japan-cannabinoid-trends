"""Compute the Google Trends summary a publication page shows, from the raw run.

Why this exists
---------------
The 5-year tables on ``publication/research_*.html`` were typed by hand.  Three
published averages could not be reproduced from any committed record
(``ISS-20261015-GT-003``) and every new compound repeated the same arithmetic.
This module derives the values from the run record, so a page's numbers are
*generated* rather than retyped, and a value the record cannot support is
reported as such instead of being invented.

Can it always recompute?
-------------------------
No, and the difference matters:

- a run that stored the weekly series (``data``) is recomputed in full;
- a run that stored a summary is passed through (the average is a recorded
  fact, not a derived one);
- the 2026-10-02 ``*-5y`` runs stored neither a series nor an average, so the
  5-year mean **cannot** be recomputed from the repository.  The missing input
  is named in ``unavailable`` - re-collecting that one 5-year series lets this
  module produce the number with no code change.

Record shapes (all four occur under ``datasets/*/data/raw/google_trends/``)
--------------------------------------------------------------------------
1. ``series``    weekly points: ``{"keyword", "timeframe", "data": [{"date", "value"}]}``
   (the 12-month runs and the 2026-10-12 ``○○ リキッド`` 5-year runs)
2. ``baseline``  ``{"compound", "data_points", "first_value", "last_value",
   "peak_value", "peak_date", "avg_5y"}`` (``20261008T093228Z-...-5y-baseline``)
3. ``partial``   ``{"peak": {...}, "first_mention", "data_summary":
   {"data_points_nonzero", "data_points_zero", "period_with_data"}}``
   (the 2026-10-02 ``*-5y`` runs, and ``cbn`` / ``crdp`` / ``hhch``)
4. ``averaged``  ``data_summary`` with ``total_weeks`` / ``nonzero_weeks`` /
   ``zero_weeks`` / ``average_all`` (``20261008T121338Z-...-crdh-5y``)

Nothing is inferred: a field the shape does not carry stays unavailable with a
reason, and the renderer shows the page's marker for it (``算出不能``).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

#: Timeframe labels as the runs record them (``--timeframe`` keys).
TIMEFRAMES = {"5y": "today 5-y", "12m": "today 12-m"}

SHAPE_SERIES = "series"
SHAPE_BASELINE = "baseline"
SHAPE_PARTIAL = "partial"
SHAPE_AVERAGED = "averaged"

#: Markers the rendered table uses; the publication contract extracts them so a
#: declared gap stays visible in the audit report.
UNCOMPUTABLE_MARKER = "算出不能（run に記録なし）"
NOT_COLLECTED_MARKER = "未取得"

#: The window label a record carries, in the wording the pages use.
WINDOW_LABELS = {"today 5-y": "過去5年（週次）", "today 12-m": "過去12ヶ月（週次）"}

#: Query suffix used for the separate Japanese product-line series (「○○ リキッド」);
#: it is a different query and must never be taken for the compound's own series.
PRODUCT_LINE_SUFFIX = "リキッド"

_SECTION_HEADING = "  <h3>5年データサマリー（個別正規化値）</h3>"


def load_record(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"not a record document: {path}")
    return document


def record_keyword(record: dict) -> str:
    """The query term a record describes (``keyword`` or the baseline's
    ``compound``)."""

    value = record.get("keyword") or record.get("compound") or ""
    return str(value).strip()


def classify_shape(record: dict) -> str:
    if isinstance(record.get("data"), list):
        return SHAPE_SERIES
    if "avg_5y" in record:
        return SHAPE_BASELINE
    summary = record.get("data_summary")
    if isinstance(summary, dict) and "average_all" in summary:
        return SHAPE_AVERAGED
    return SHAPE_PARTIAL


def _format_number(value) -> str:
    """Decimals trimmed, integers kept as integers (32.5, 3, 1.2).

    The recorded value decides the precision: a summary that stored ``14``
    renders ``14``, not ``14.0`` (no precision is invented).
    """

    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _peak_date(value: str) -> str:
    """``2025-08-31 to 2025-09-06`` (a week) reads as its first day."""

    return str(value).split(" to ")[0].strip()


def summarize_record(record: dict) -> dict:
    """Per-field statistics for one record, plus why a field is unavailable.

    ``unavailable`` names the missing input for each field it cannot fill, so
    the reason is recorded rather than left to the reader (or to a later
    "recompute" that would silently invent it).
    """

    shape = classify_shape(record)
    stats: dict = {}
    unavailable: dict = {}

    if shape == SHAPE_SERIES:
        points = [p for p in record["data"] if isinstance(p, dict)]
        values = [p.get("value", 0) for p in points]
        dates = [p.get("date") for p in points]
        weeks = len(points)
        peak_value = max(values) if values else None
        nonzero = [index for index, value in enumerate(values) if value]
        stats.update(
            weeks=weeks,
            mean=round(sum(values) / weeks, 4) if weeks else None,
            peak_date=dates[values.index(peak_value)] if weeks else None,
            peak_value=peak_value,
            last_value=values[-1] if weeks else None,
            first_nonzero_date=dates[nonzero[0]] if nonzero else None,
            first_value=values[nonzero[0]] if nonzero else None,
            nonzero_weeks=len(nonzero),
            zero_weeks=weeks - len(nonzero),
            data_period=f"{dates[0]} 〜 {dates[-1]}" if weeks else None,
        )
    elif shape == SHAPE_BASELINE:
        stats.update(
            weeks=record.get("data_points"),
            mean=record.get("avg_5y"),
            peak_date=_peak_date(record.get("peak_date", "")) or None,
            peak_value=record.get("peak_value"),
            last_value=record.get("last_value"),
            first_value=record.get("first_value"),
        )
        unavailable["first_nonzero_date"] = "run が初出を記録していない"
        unavailable["nonzero_weeks"] = "run が非ゼロ週数を記録していない"
        unavailable["data_period"] = "run がデータあり期間を記録していない"
    else:
        summary = record.get("data_summary") or {}
        peak = record.get("peak") or {}
        nonzero = summary.get("data_points_nonzero", summary.get("nonzero_weeks"))
        zero = summary.get("data_points_zero", summary.get("zero_weeks"))
        stats.update(
            weeks=summary.get("total_weeks") or (
                nonzero + zero if nonzero is not None and zero is not None else None
            ),
            mean=summary.get("average_all"),
            peak_date=_peak_date(peak.get("date", "")) or None,
            peak_value=peak.get("value"),
            first_nonzero_date=record.get("first_mention") or None,
            first_value=record.get("first_value"),
            nonzero_weeks=nonzero,
            zero_weeks=zero,
            data_period=summary.get("period_with_data") or None,
        )
        if stats["mean"] is None:
            unavailable["mean"] = "run が平均値を記録していない（系列も未保存）"
        stats.setdefault("average_nonzero", summary.get("average_nonzero"))
        unavailable["last_value"] = "run が最新値を記録していない"
        if stats["data_period"] is None:
            unavailable["data_period"] = "run がデータあり期間を記録していない"

    return {
        "keyword": record_keyword(record),
        "timeframe": record.get("timeframe"),
        "collected_at": record.get("collected_at"),
        "shape": shape,
        "stats": stats,
        "unavailable": unavailable,
    }


def find_run(datasets_root: Path, compound: str, timeframe: str) -> Path | None:
    """The record file for ``compound`` at ``timeframe``, or ``None``.

    Product-line series (``○○ リキッド``) are excluded: they are a different
    query and a different normalisation, so they cannot stand in for the
    compound.  When several records match, the most recently collected wins
    (``collected_at`` then the run id).
    """

    wanted = compound.strip().upper()
    candidates = []
    for path in sorted(Path(datasets_root).rglob("google_trends/*/*.json")):
        if path.name == "run_metadata.json":
            continue
        try:
            record = load_record(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        keyword = record_keyword(record)
        if PRODUCT_LINE_SUFFIX in keyword or keyword.upper() != wanted:
            continue
        if record.get("timeframe") != timeframe:
            continue
        candidates.append((str(record.get("collected_at") or ""), path.parent.name, path))
    if not candidates:
        return None
    return max(candidates)[2]


def render_block(summary: dict, *, run_id: str, geo: str = "JP") -> str:
    """The 5-year block a research page carries, generated from the record."""

    stats = summary["stats"]
    unavailable = summary["unavailable"]
    timeframe = summary["timeframe"] or ""

    weeks = stats.get("weeks")
    window = WINDOW_LABELS.get(timeframe, timeframe)
    if stats.get("data_period"):
        period_label = f"{stats['data_period']}（{weeks}週）" if weeks else stats["data_period"]
    else:
        period_label = f"{window}・{weeks}週" if weeks else window

    mean = (
        f"<strong>{_format_number(stats['mean'])}</strong>"
        if stats.get("mean") is not None
        else UNCOMPUTABLE_MARKER
    )
    peak = (
        f"{stats['peak_date']}（値: {stats['peak_value']}）"
        if stats.get("peak_date") and stats.get("peak_value") is not None
        else UNCOMPUTABLE_MARKER
    )
    last = (
        _format_number(stats["last_value"])
        if stats.get("last_value") is not None
        else UNCOMPUTABLE_MARKER
    )

    extras = []
    if stats.get("first_nonzero_date"):
        first = stats["first_nonzero_date"]
        if stats.get("first_value") is not None:
            first += f"（値 {stats['first_value']}）"
        extras.append(f"初出 {first}")
    if stats.get("nonzero_weeks") is not None:
        extras.append(f"非ゼロ {stats['nonzero_weeks']} 週 / ゼロ {stats['zero_weeks']} 週")
    if stats.get("average_nonzero") is not None:
        extras.append(f"非ゼロ平均 {_format_number(stats['average_nonzero'])}")
    if stats.get("data_period"):
        extras.append(f"データあり期間 {stats['data_period']}")
    for field in ("mean", "last_value"):
        if field in unavailable:
            extras.append(f"{field}: {unavailable[field]}")

    source = (
        f"  <p><strong>出所:</strong> run <code>{run_id}</code>"
        f"（{geo} / {timeframe} / {summary.get('collected_at') or '収集日不明'} 収集）。"
        + ("記録にある項目: " + "、".join(extras) + "。" if extras else "")
        + "</p>"
    )

    return (
        f"{_SECTION_HEADING}\n"
        "  <table>\n"
        "    <thead>\n"
        "      <tr>\n"
        "        <th>指標</th>\n"
        "        <th>値</th>\n"
        "      </tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        f"      <tr>\n        <td>収集期間</td>\n        <td>{period_label}</td>\n      </tr>\n"
        f"      <tr>\n        <td>5年平均</td>\n        <td>{mean}</td>\n      </tr>\n"
        f"      <tr>\n        <td>ピーク</td>\n        <td>{peak}</td>\n      </tr>\n"
        f"      <tr>\n        <td>最新値</td>\n        <td>{last}</td>\n      </tr>\n"
        "    </tbody>\n"
        "  </table>\n"
        f"{source}"
    )

def render_not_collected(compound: str, timeframe: str = "today 5-y") -> str:
    """The block for a compound whose series was never collected.

    Blocks end without a trailing newline: the page keeps the blank line before
    the next heading, so a regenerated block neither loses nor accumulates
    whitespace.
    """

    label = "5 年" if timeframe == "today 5-y" else "12ヶ月"
    return (
        f"{_SECTION_HEADING}\n"
        f"  <p>{label}系列は{NOT_COLLECTED_MARKER}（収集 run が存在しない）。これは"
        "<strong>欠測であり、需要ゼロを意味しない</strong>。後日再取得する。</p>"
    )


def _run_id(path: Path) -> str:
    return path.parent.name


def build_gt_summary(datasets_root: Path, compounds, timeframe: str) -> dict:
    """One entry per compound: the recomputed statistics or the missing input."""

    entries = []
    for compound in compounds:
        path = find_run(datasets_root, compound, timeframe)
        if path is None:
            entries.append(
                {
                    "compound": compound,
                    "status": "not_collected",
                    "timeframe": timeframe,
                    "block": render_not_collected(compound, timeframe),
                }
            )
            continue
        summary = summarize_record(load_record(path))
        entries.append(
            {
                "compound": compound,
                "status": "computed",
                "run_id": _run_id(path),
                "path": path.as_posix(),
                "shape": summary["shape"],
                "stats": summary["stats"],
                "unavailable": summary["unavailable"],
                "block": render_block(summary, run_id=_run_id(path)),
            }
        )

    def count(field: str) -> dict:
        counts: dict = {}
        for entry in entries:
            key = str(entry.get(field))
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "processing.cli gt-summary",
        "datasets_root": Path(datasets_root).as_posix(),
        "timeframe": timeframe,
        "summary": {
            "compound_count": len(entries),
            "by_status": count("status"),
            "by_shape": count("shape"),
            "unavailable_mean": [
                entry["compound"]
                for entry in entries
                if "mean" in entry.get("unavailable", {})
            ],
        },
        "compounds": entries,
    }


#: The compounds the publication pages cover (``publication/research_*.html``).
PUBLICATION_COMPOUNDS = (
    "CBD",
    "THC",
    "CBG",
    "CBN",
    "THCV",
    "THCH",
    "HHC",
    "THC-O",
    "H4CBH",
    "HHBD",
    "HHCH",
    "CRDP",
    "CRDH",
)


def page_filename(compound: str) -> str:
    return f"research_{compound.lower()}.html"


_BLOCK_RE = re.compile(
    re.escape(_SECTION_HEADING) + r".*?(?=\s*<h3>)", re.S
)


def replace_block(html: str, block: str) -> str:
    """Swap the page's 5-year block for the generated one.

    The block ends at the next ``<h3>`` whatever its indentation: the 12-month
    heading follows it and must survive (an anchor that assumed two leading
    spaces silently ate the 12-month table when the heading was flush left).
    """

    replaced, count = _BLOCK_RE.subn(lambda _match: block, html, count=1)
    if count != 1:
        raise ValueError("5年データサマリー block not found exactly once")
    return replaced
