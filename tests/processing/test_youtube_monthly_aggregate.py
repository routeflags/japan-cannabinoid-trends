import csv
import hashlib
import json
from pathlib import Path

import pytest

from processing.youtube_monthly_aggregate import (
    OUTPUT_COLUMNS,
    QUERY_TEXT,
    RUN_ID,
    STUDY_ID,
    YouTubeAggregationError,
    aggregate_youtube_rows,
    build_youtube_monthly_aggregate,
    write_youtube_monthly_aggregate,
)


def _row(video_id: str, date: str, query: str = QUERY_TEXT) -> dict[str, str]:
    return {"id": video_id, "date": date, "input": query}


def _write_run(study_dir: Path, rows: list[dict[str, str]]) -> Path:
    run_dir = study_dir / "data" / "raw" / "youtube" / RUN_ID
    run_dir.mkdir(parents=True)
    payload = run_dir / "videos.csv"
    with payload.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "date", "input"])
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    (run_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "study_id": STUDY_ID,
                "run_id": RUN_ID,
                "source_id": "youtube",
                "query_provenance": {
                    "query_id": "hhbd-liquid-ja",
                    "submitted_query": QUERY_TEXT,
                },
                "execution": {"returned_count": len(rows)},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "artifact-manifest.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "artifacts": [
                    {
                        "path": "videos.csv",
                        "layer": "raw",
                        "format": "csv",
                        "sha256": digest,
                        "record_count": len(rows),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return payload


def test_aggregate_counts_distinct_video_ids_by_utc_month():
    rows = [
        _row("v1", "2025-12-31T23:30:00-02:00"),
        _row("v2", "2026-01-04T10:00:00Z"),
        _row("v1", "2026-01-01T01:30:00Z"),
    ]

    aggregate, diagnostics = aggregate_youtube_rows(rows)

    assert [row["period_start"] for row in aggregate] == [
        "2026-01-01",
    ]
    assert aggregate[0]["value"] == "2"
    assert diagnostics == {
        "raw_record_count": 3,
        "distinct_video_count": 2,
        "duplicates_removed": 1,
        "month_count": 1,
    }
    assert tuple(aggregate[0]) == OUTPUT_COLUMNS
    assert "v1" not in json.dumps(aggregate)


def test_aggregate_rejects_duplicate_ids_with_conflicting_months():
    with pytest.raises(YouTubeAggregationError, match="conflicting months"):
        aggregate_youtube_rows(
            [
                _row("v1", "2025-12-31T23:59:00Z"),
                _row("v1", "2026-01-01T00:00:00Z"),
            ]
        )


@pytest.mark.parametrize(
    "row, message",
    [
        ({"date": "2026-01-01T00:00:00Z", "input": QUERY_TEXT}, "missing video id"),
        (_row("v1", "", QUERY_TEXT), "missing publication date"),
        (_row("v1", "2026-01-01T00:00:00Z", "HHBD"), "query does not match"),
        (_row("v1", "2026-01-01T00:00:00", QUERY_TEXT), "no timezone"),
    ],
)
def test_aggregate_rejects_unusable_source_rows(row, message):
    with pytest.raises(YouTubeAggregationError, match=message):
        aggregate_youtube_rows([row])


def test_build_validates_provenance_and_writes_aggregate_only_csv(tmp_path):
    study_dir = tmp_path / STUDY_ID
    rows = [
        _row("private-video-id-1", "2025-12-31T23:30:00-02:00"),
        _row("private-video-id-2", "2026-01-04T10:00:00Z"),
    ]
    _write_run(study_dir, rows)

    aggregate, diagnostics = build_youtube_monthly_aggregate(study_dir)
    output_path = write_youtube_monthly_aggregate(
        aggregate, tmp_path / "processed" / "youtube_monthly_counts.csv"
    )

    with output_path.open(encoding="utf-8", newline="") as handle:
        output = list(csv.DictReader(handle))
    serialized = output_path.read_text(encoding="utf-8")
    assert len(output) == 1
    assert output[0]["period_start"] == "2026-01-01"
    assert sum(int(row["value"]) for row in output) == diagnostics["distinct_video_count"]
    assert "private-video-id" not in serialized
    assert diagnostics["input_sha256"]


def test_build_rejects_payload_that_differs_from_manifest(tmp_path):
    study_dir = tmp_path / STUDY_ID
    payload = _write_run(study_dir, [_row("v1", "2026-01-01T00:00:00Z")])
    payload.write_text(payload.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(YouTubeAggregationError, match="SHA-256"):
        build_youtube_monthly_aggregate(study_dir)
