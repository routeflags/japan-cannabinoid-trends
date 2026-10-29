"""Aggregate one adopted YouTube run to monthly returned-result counts.

The output contains no video identifiers, titles, channel names, descriptions,
or engagement values. Months with no returned rows are omitted: this search
result sample is not a census of YouTube uploads.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "RUN_ID",
    "OUTPUT_COLUMNS",
    "YouTubeAggregationError",
    "aggregate_youtube_rows",
    "build_youtube_monthly_aggregate",
    "write_youtube_monthly_aggregate",
]

STUDY_ID = "cannabinoid-raw-collection"
RUN_ID = "20261010T141947Z-youtube-cannabinoid-raw-collection"
QUERY_ID = "hhbd-liquid-ja"
QUERY_TEXT = "HHBD リキッド"
OUTPUT_COLUMNS = (
    "source",
    "run_id",
    "query_id",
    "query_text",
    "metric",
    "value",
    "unit",
    "period_start",
    "period_end_exclusive",
    "granularity",
    "status",
)
METRIC = "returned_video_sample_count"


class YouTubeAggregationError(ValueError):
    """The raw YouTube run does not satisfy the declared aggregation inputs."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _month_of(raw_date: str, *, row_number: int) -> str:
    text = raw_date.strip()
    try:
        timestamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise YouTubeAggregationError(
            f"row {row_number}: date is not an ISO-8601 timestamp"
        ) from error
    if timestamp.tzinfo is None:
        raise YouTubeAggregationError(
            f"row {row_number}: date has no timezone; refusing to assume UTC"
        )
    timestamp = timestamp.astimezone(timezone.utc)
    return f"{timestamp.year:04d}-{timestamp.month:02d}"


def aggregate_youtube_rows(
    rows: list[dict[str, str]], *, query_text: str = QUERY_TEXT
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Count distinct returned video IDs by UTC publication month.

    Duplicate IDs within this run are counted once. If duplicates place the same
    video in different months, fail rather than choosing an arbitrary date.
    """
    month_by_video: dict[str, str] = {}
    counts: Counter[str] = Counter()
    duplicates_removed = 0

    for row_number, row in enumerate(rows, start=2):
        video_id = (row.get("id") or "").strip()
        raw_date = (row.get("date") or "").strip()
        input_query = (row.get("input") or "").strip()
        if not video_id:
            raise YouTubeAggregationError(f"row {row_number}: missing video id")
        if not raw_date:
            raise YouTubeAggregationError(f"row {row_number}: missing publication date")
        if input_query != query_text:
            raise YouTubeAggregationError(
                f"row {row_number}: input query does not match the adopted query"
            )

        month = _month_of(raw_date, row_number=row_number)
        previous_month = month_by_video.get(video_id)
        if previous_month is not None:
            if previous_month != month:
                raise YouTubeAggregationError(
                    f"row {row_number}: duplicate video ID has conflicting months"
                )
            duplicates_removed += 1
            continue
        month_by_video[video_id] = month
        counts[month] += 1

    output = []
    for month, count in sorted(counts.items()):
        year, month_number = (int(part) for part in month.split("-"))
        next_year, next_month = (
            (year + 1, 1) if month_number == 12 else (year, month_number + 1)
        )
        output.append(
            {
                "source": "youtube",
                "run_id": RUN_ID,
                "query_id": QUERY_ID,
                "query_text": query_text,
                "metric": METRIC,
                "value": str(count),
                "unit": "videos",
                "period_start": f"{year:04d}-{month_number:02d}-01",
                "period_end_exclusive": f"{next_year:04d}-{next_month:02d}-01",
                "granularity": "month",
                "status": "observed_nonzero",
            }
        )

    return output, {
        "raw_record_count": len(rows),
        "distinct_video_count": len(month_by_video),
        "duplicates_removed": duplicates_removed,
        "month_count": len(output),
    }


def build_youtube_monthly_aggregate(
    study_dir: str | Path, *, run_id: str = RUN_ID
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Read and validate the selected adopted run before aggregating it."""
    if run_id != RUN_ID:
        raise YouTubeAggregationError(f"unsupported run_id: {run_id}")

    root = Path(study_dir)
    run_dir = root / "data" / "raw" / "youtube" / run_id
    try:
        metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
        manifest = json.loads((run_dir / "artifact-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise YouTubeAggregationError(f"run provenance is unavailable: {run_dir}") from error

    query = metadata.get("query_provenance") or {}
    if (
        metadata.get("study_id") != STUDY_ID
        or metadata.get("source_id") != "youtube"
        or metadata.get("run_id") != run_id
        or manifest.get("run_id") != run_id
        or query.get("query_id") != QUERY_ID
        or query.get("submitted_query") != QUERY_TEXT
    ):
        raise YouTubeAggregationError("run metadata does not match the target study and query")

    artifacts = manifest.get("artifacts")
    csv_artifacts = [
        item for item in artifacts or []
        if isinstance(item, dict)
        and item.get("layer") == "raw"
        and item.get("format") == "csv"
    ]
    if len(csv_artifacts) != 1:
        raise YouTubeAggregationError("expected exactly one raw CSV artifact")

    artifact = csv_artifacts[0]
    payload = (run_dir / str(artifact.get("path", ""))).resolve()
    if run_dir.resolve() not in payload.parents or not payload.is_file():
        raise YouTubeAggregationError("raw CSV artifact path is missing or unsafe")
    if _sha256(payload) != artifact.get("sha256"):
        raise YouTubeAggregationError("raw CSV SHA-256 does not match its manifest")

    try:
        with payload.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"id", "date", "input"}
            if not required.issubset(reader.fieldnames or []):
                raise YouTubeAggregationError("raw CSV lacks required fields")
            raw_rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise YouTubeAggregationError("raw CSV could not be read") from error

    expected_count = metadata.get("execution", {}).get("returned_count")
    if (
        len(raw_rows) != expected_count
        or len(raw_rows) != artifact.get("record_count")
    ):
        raise YouTubeAggregationError("raw CSV record count does not match run provenance")

    output, diagnostics = aggregate_youtube_rows(raw_rows, query_text=QUERY_TEXT)
    diagnostics["input_sha256"] = _sha256(payload)
    return output, diagnostics


def write_youtube_monthly_aggregate(
    rows: list[dict[str, str]], output_path: str | Path
) -> Path:
    """Write deterministic aggregate CSV output."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(OUTPUT_COLUMNS), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return path
