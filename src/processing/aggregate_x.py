"""Weekly / monthly aggregate derivation for the private per-post X input.

Owner decision 2026-10-15 (ISS-20261014-PUB-029, option ii): only the
aggregator is implemented. The per-post anonymized CSV (issue sections 2-2,
10, 11) is withdrawn history; section 2-3 input measurements stay valid and
sections 3-6 transformation rules are reused here as pre-processing.

The private per-post input (16 columns, 147 rows) is read read-only and
never modified. No per-post row, identifier, text, URL, exact timestamp or
exact engagement count ever enters an aggregate output: each output row is
a group count over period x compound x classification x engagement-bin.

Small cells are reported, never suppressed: the k-anonymity threshold is
undecided (issue section 8), so this module must not delete or merge groups
on its own authority.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "AGGREGATOR_VERSION",
    "INPUT_COLUMNS",
    "WEEKLY_COLUMNS",
    "MONTHLY_COLUMNS",
    "COARSE_MONTHLY_COLUMNS",
    "ENGAGEMENT_BIN_LABELS",
    "TEXT_LENGTH_BIN_LABELS",
    "COMPOUND_DEFAULT",
    "COMPOUND_PROVENANCE",
    "AggregateError",
    "bin_engagement",
    "bin_text_length",
    "month_of",
    "week_monday_of",
    "parse_created_at",
    "read_private_input",
    "aggregate_rows",
    "aggregate_coarse_monthly_rows",
    "write_aggregate_csv",
    "scan_output_for_identifiers",
    "sha256_file",
]

AGGREGATOR_VERSION = "1.0.0"

INPUT_COLUMNS: tuple[str, ...] = (
    "tweet_id_hash",
    "createdAt",
    "week",
    "lang",
    "author_id",
    "views",
    "likes",
    "reposts",
    "replies",
    "has_text",
    "text_length",
    "topic_id",
    "intent_id",
    "format_id",
    "platform",
    "language",
)

_GROUP_COLUMNS: tuple[str, ...] = (
    "compound",
    "topic_id",
    "intent_id",
    "format_id",
    "views_bin",
    "likes_bin",
    "reposts_bin",
    "replies_bin",
    "text_length_bin",
    "has_text",
)

WEEKLY_COLUMNS: tuple[str, ...] = ("week_start",) + _GROUP_COLUMNS + ("post_count",)
MONTHLY_COLUMNS: tuple[str, ...] = ("month",) + _GROUP_COLUMNS + ("post_count",)
COARSE_MONTHLY_COLUMNS: tuple[str, ...] = (
    "month",
    "compound",
    "breakdown",
    "category",
    "post_count",
)

_ENGAGEMENT_EDGES: tuple[tuple[int, str], ...] = (
    (0, "0"),
    (4, "1"),
    (19, "2"),
    (99, "3"),
    (499, "4"),
    (1999, "5"),
    (9999, "6"),
)
ENGAGEMENT_BIN_LABELS = ("0", "1", "2", "3", "4", "5", "6", "7")

_TEXT_EDGES: tuple[tuple[int, str], ...] = (
    (0, "0"),
    (20, "1"),
    (50, "2"),
    (100, "3"),
    (200, "4"),
    (280, "5"),
)
TEXT_LENGTH_BIN_LABELS = ("0", "1", "2", "3", "4", "5", "6")

COMPOUND_DEFAULT = "CBX"
COMPOUND_PROVENANCE = (
    "datasets/cbx-social-trends/methodology.md section 3.1 "
    "(query CBX liquid) + metadata/queries/query-registry.json "
    "(cbx-liquid-ja -> compound_cbx)"
)

BANNED_HEADER_NAMES = frozenset(
    {
        "tweet_id",
        "tweet_id_hash",
        "author_id",
        "username",
        "author_name",
        "screen_name",
        "display_name",
        "url",
        "text",
        "createdAt",
        "views",
        "likes",
        "reposts",
        "replies",
        "text_length",
        "week",
        "lang",
        "platform",
        "language",
    }
)

_INT_RE = re.compile(r"^(0|[1-9][0-9]*)$")


class AggregateError(ValueError):
    """The private input is not in the state the aggregation assumes."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bin_value(raw: str, *, column: str, edges: tuple[tuple[int, str], ...], top: str) -> str:
    text = raw.strip() if isinstance(raw, str) else ""
    if text == "":
        return ""
    if not _INT_RE.match(text):
        raise AggregateError(
            "column %r: value %r is not a non-negative integer; "
            "missing stays missing and zero stays zero, anything else must "
            "be an exact count" % (column, raw)
        )
    value = int(text)
    for upper, label in edges:
        if value <= upper:
            return label
    return top


def bin_engagement(raw: str, *, column: str = "views") -> str:
    return _bin_value(raw, column=column, edges=_ENGAGEMENT_EDGES, top="7")


def bin_text_length(raw: str) -> str:
    return _bin_value(raw, column="text_length", edges=_TEXT_EDGES, top="6")


def parse_created_at(raw: str) -> datetime | None:
    text = raw.strip() if isinstance(raw, str) else ""
    if text == "":
        return None
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        raise AggregateError(
            "createdAt %r carries no timezone; refusing to assume UTC" % (raw,)
        )
    return stamp.astimezone(timezone.utc)


def month_of(stamp: datetime) -> str:
    return "%04d-%02d-01" % (stamp.year, stamp.month)


def week_monday_of(stamp: datetime) -> str:
    day = stamp.date()
    monday = day.fromordinal(day.toordinal() - day.weekday())
    return monday.isoformat()


def read_private_input(path: str | Path) -> tuple[list[dict[str, str]], str]:
    path = Path(path)
    digest = sha256_file(path)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != INPUT_COLUMNS:
            raise AggregateError(
                "input header %r != expected %r"
                % (tuple(reader.fieldnames or ()), INPUT_COLUMNS)
            )
        rows = [dict(row) for row in reader]
    return rows, digest


def _has_text_value(raw: str) -> str:
    text = raw.strip() if isinstance(raw, str) else ""
    if text == "":
        return ""
    if text not in ("yes", "no"):
        raise AggregateError("has_text %r is not yes / no / missing" % (raw,))
    return text


def aggregate_rows(
    rows: list[dict[str, str]], *, compound: str = COMPOUND_DEFAULT
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict]:
    weekly: Counter[tuple[str, ...]] = Counter()
    monthly: Counter[tuple[str, ...]] = Counter()
    week_discrepancies = 0
    unknown_periods = 0
    missing = Counter()

    for index, row in enumerate(rows):
        absent = [c for c in INPUT_COLUMNS if c not in row]
        if absent:
            raise AggregateError("row %d: missing input columns %s" % (index, absent))
        for column in ("views", "likes", "reposts", "replies", "text_length", "has_text"):
            if (row[column] or "").strip() == "":
                missing[column] += 1

        stamp = parse_created_at(row["createdAt"])
        if stamp is None:
            if (row["createdAt"] or "").strip() == "":
                missing["createdAt"] += 1
            week_start = ""
            month = ""
            unknown_periods += 1
        else:
            week_start = week_monday_of(stamp)
            month = month_of(stamp)
        if row["week"] != "" and stamp is not None and row["week"] == "unknown":
            week_discrepancies += 1

        key = (
            compound,
            row["topic_id"] or "",
            row["intent_id"] or "",
            row["format_id"] or "",
            bin_engagement(row["views"], column="views"),
            bin_engagement(row["likes"], column="likes"),
            bin_engagement(row["reposts"], column="reposts"),
            bin_engagement(row["replies"], column="replies"),
            bin_text_length(row["text_length"]),
            _has_text_value(row["has_text"]),
        )
        weekly[(week_start,) + key] += 1
        monthly[(month,) + key] += 1

    def _table(counter: Counter[tuple[str, ...]], period_name: str) -> list[dict[str, str]]:
        table: list[dict[str, str]] = []
        for full_key in sorted(counter):
            record = dict(zip((period_name,) + _GROUP_COLUMNS, full_key))
            record["post_count"] = str(counter[full_key])
            table.append(record)
        return table

    diagnostics = {
        "input_rows": len(rows),
        "legacy_week_unknown_with_valid_timestamp": week_discrepancies,
        "unknown_period_rows": unknown_periods,
        "missing": dict(sorted(missing.items())),
    }
    return _table(weekly, "week_start"), _table(monthly, "month"), diagnostics


def _coarse_engagement_category(metric: str, raw: str) -> str:
    label = bin_engagement(raw, column=metric)
    if label == "":
        return f"{metric}_missing"
    value = int(label)
    if metric == "views":
        # Coarsen the previous 8 exposure bins into two public buckets:
        # 0-499 and 500+.  This removes the rare 10,000+ cell while retaining
        # the low / non-low split reviewers asked for.
        return "views_0_499" if value <= 4 else "views_500_plus"
    if metric == "likes":
        if value <= 1:
            return "likes_0_4"
        if value == 2:
            return "likes_5_19"
        return "likes_20_plus"
    if metric in ("reposts", "replies"):
        return f"{metric}_0" if value == 0 else f"{metric}_1_plus"
    raise AggregateError(f"unsupported engagement metric for coarse aggregation: {metric}")


def aggregate_coarse_monthly_rows(
    rows: list[dict[str, str]], *, compound: str = COMPOUND_DEFAULT, threshold: int = 5
) -> tuple[list[dict[str, str]], dict]:
    """Build the publication-oriented coarse monthly aggregate.

    The fine weekly/monthly group products remain useful for review, but the
    owner selected "coarsen the aggregation" for publication.  This output uses
    monthly marginal breakdowns instead of crossing period x classification x
    several engagement bins.  Topic categories below ``threshold`` within a
    month are merged into ``other_topic_lt5``; engagement bins are also collapsed
    to broad tiers.  The result is still deterministic and derived directly from
    the private input, but avoids publishing fine cells that approximate
    individual posts.
    """

    if threshold < 1:
        raise AggregateError("coarse aggregation threshold must be >= 1")

    monthly_total: Counter[tuple[str, str]] = Counter()
    monthly_topic: Counter[tuple[str, str, str]] = Counter()
    monthly_engagement: dict[str, Counter[tuple[str, str, str]]] = {
        "views_tier": Counter(),
        "likes_tier": Counter(),
        "reposts_tier": Counter(),
        "replies_tier": Counter(),
    }
    unknown_periods = 0

    for index, row in enumerate(rows):
        absent = [c for c in INPUT_COLUMNS if c not in row]
        if absent:
            raise AggregateError("row %d: missing input columns %s" % (index, absent))
        stamp = parse_created_at(row["createdAt"])
        if stamp is None:
            month = ""
            unknown_periods += 1
        else:
            month = month_of(stamp)

        monthly_total[(month, compound)] += 1
        monthly_topic[(month, compound, row["topic_id"] or "")] += 1
        for metric, breakdown in (
            ("views", "views_tier"),
            ("likes", "likes_tier"),
            ("reposts", "reposts_tier"),
            ("replies", "replies_tier"),
        ):
            monthly_engagement[breakdown][
                (month, compound, _coarse_engagement_category(metric, row[metric]))
            ] += 1

    output: list[dict[str, str]] = []

    def add(month: str, compound_value: str, breakdown: str, category: str, count: int) -> None:
        output.append(
            {
                "month": month,
                "compound": compound_value,
                "breakdown": breakdown,
                "category": category,
                "post_count": str(count),
            }
        )

    for month, compound_value in sorted(monthly_total):
        add(month, compound_value, "total", "all", monthly_total[(month, compound_value)])

        other_topic_count = 0
        topic_rows: list[tuple[str, int]] = []
        for topic_key, count in sorted(
            (topic, count)
            for (topic_month, topic_compound, topic), count in monthly_topic.items()
            if topic_month == month and topic_compound == compound_value
        ):
            if count < threshold:
                other_topic_count += count
            else:
                topic_rows.append((topic_key or "topic_missing", count))
        for category, count in topic_rows:
            add(month, compound_value, "topic", category, count)
        if other_topic_count:
            add(month, compound_value, "topic", f"other_topic_lt{threshold}", other_topic_count)

        for breakdown in ("views_tier", "likes_tier", "reposts_tier", "replies_tier"):
            for category, count in sorted(
                (category, count)
                for (metric_month, metric_compound, category), count in monthly_engagement[
                    breakdown
                ].items()
                if metric_month == month and metric_compound == compound_value
            ):
                add(month, compound_value, breakdown, category, count)

    small_cells = [
        row
        for row in output
        if row["breakdown"] != "total" and int(row["post_count"]) < threshold
    ]
    diagnostics = {
        "threshold": threshold,
        "input_rows": len(rows),
        "unknown_period_rows": unknown_periods,
        "groups": len(output),
        "small_cells_lt_threshold": len(small_cells),
        "minimum_group_size": min((int(row["post_count"]) for row in output), default=0),
        "breakdowns": sorted({row["breakdown"] for row in output}),
    }
    return output, diagnostics


def write_aggregate_csv(
    path: str | Path, columns: tuple[str, ...], rows: list[dict[str, str]]
) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(row[c] for c in columns))
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return sha256_file(target)


def scan_output_for_identifiers(
    columns: tuple[str, ...], rows: list[dict[str, str]]
) -> list[str]:
    findings: list[str] = []
    for name in columns:
        if name in BANNED_HEADER_NAMES:
            findings.append("banned header: %s" % name)
    url_re = re.compile(r"https?://")
    iso_re = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:")
    for index, row in enumerate(rows):
        for column in columns:
            value = row[column]
            if url_re.search(value):
                findings.append("row %d: URL in %s" % (index, column))
            if iso_re.search(value):
                findings.append("row %d: exact datetime in %s" % (index, column))
    return findings
