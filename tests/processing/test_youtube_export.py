"""Tests for the aggregate-only YouTube export (processing.youtube_export)."""

import csv
import json
from pathlib import Path

from processing.youtube_export import (
    RUN_COLUMNS,
    VIDEO_COLUMNS,
    build_video_export,
    write_export,
)


def _run(root: Path, run_id: str, payloads: dict, metadata: dict | None = None) -> Path:
    run_dir = root / "data" / "raw" / "youtube" / run_id
    run_dir.mkdir(parents=True)
    if metadata is not None:
        (run_dir / "run_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
        )
    for name, payload in payloads.items():
        (run_dir / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return run_dir


def _api_items(rows):
    return [
        {
            "kind": "youtube#searchResult",
            "id": {"kind": "youtube#video", "videoId": video_id},
            "snippet": {
                "title": title,
                "channelTitle": channel,
                "description": description,
            },
        }
        for video_id, title, channel, description in rows
    ]


def test_published_run_is_exported_without_the_description(tmp_path):
    study = tmp_path / "study"
    _run(
        study,
        "20261002T064739Z-youtube-cbd",
        {
            "records.json": _api_items(
                [("vid1", "CBD explained", "Chan A", "Business: someone@example.com")]
            )
        },
        metadata={"search_term": "CBD", "collection_timestamp": "2026-10-02T06:47:40Z"},
    )

    result = build_video_export(study)

    assert len(result["videos"]) == 1
    assert set(result["videos"][0]) == set(VIDEO_COLUMNS)
    assert result["videos"][0]["video_id"] == "vid1"
    # The description is the field that carries third-party contact addresses,
    # so it must never reach the export.
    assert "someone@example.com" not in json.dumps(result["videos"])
    assert [run["run_id"] for run in result["runs"]] == ["20261002T064739Z-youtube-cbd"]
    assert result["withheld"] == []


def test_unreviewed_and_withdrawn_runs_are_withheld_with_a_reason(tmp_path):
    study = tmp_path / "study"
    _run(
        study,
        "20261004T142147Z-youtube-cbd-10years",
        {"records_2025.json": {"error": {"code": 403, "message": "quota"}}},
    )
    _run(study, "20261009T160738Z-youtube-cbd-dated", {"records.json": _api_items(
        [("vid2", "dated", "Chan B", "")]
    )})
    _run(study, "20260101T000000Z-youtube-unreviewed", {"records.json": []})

    result = build_video_export(study)

    assert result["videos"] == []
    # Nothing about a withheld run reaches the artifact: not its videos, not its
    # run row.  The reason is kept for the operator and for the code only.
    assert result["runs"] == []
    withheld = {run["run_id"]: run["status"] for run in result["withheld"]}
    assert "10-year series" in withheld["20261004T142147Z-youtube-cbd-10years"]
    assert "YouTube Data API v3" in withheld["20261009T160738Z-youtube-cbd-dated"]
    assert withheld["20260101T000000Z-youtube-unreviewed"] == (
        "provenance not reviewed for publication"
    )


def test_duplicate_video_ids_within_a_run_collapse_to_one_row(tmp_path):
    study = tmp_path / "study"
    _run(
        study,
        "20261002T064739Z-youtube-cbd",
        {
            "records_page1.json": {"items": _api_items([("vid1", "a", "Ch", "")])},
            "records_page2.json": {"items": _api_items([("vid1", "a", "Ch", "")])},
        },
    )

    result = build_video_export(study)

    assert len(result["videos"]) == 1


def test_oct08_hhc_repeat_keeps_cross_run_duplicates(tmp_path):
    # ISS-20261024-YT-013: HHC was observed twice (2026-10-02 and 2026-10-08).
    # The same videoId in both runs stays two rows (one per run); a duplicate
    # inside one run still collapses to one row.
    study = tmp_path / "study"
    _run(
        study,
        "20261002T064850Z-youtube-hhc",
        {
            "records.json": _api_items(
                [("shared1", "a", "Ch", ""), ("old-only", "b", "Ch", "")]
            )
        },
        metadata={"search_term": "HHC", "collection_timestamp": "2026-10-02T06:48:50Z"},
    )
    _run(
        study,
        "20261008T122515Z-youtube-hhc",
        {
            "records.json": _api_items(
                [
                    ("shared1", "a", "Ch", ""),
                    ("shared1", "a", "Ch", ""),
                    ("new-only", "c", "Ch", ""),
                ]
            )
        },
    )

    result = build_video_export(study)

    by_run: dict[str, list[str]] = {}
    for row in result["videos"]:
        by_run.setdefault(row["run_id"], []).append(row["video_id"])
    assert sorted(by_run["20261002T064850Z-youtube-hhc"]) == ["old-only", "shared1"]
    assert sorted(by_run["20261008T122515Z-youtube-hhc"]) == ["new-only", "shared1"]
    assert sum(1 for row in result["videos"] if row["video_id"] == "shared1") == 2
    assert len(result["videos"]) == 4


def test_repeat_export_keeps_row_order(tmp_path):
    # Same raw + same exporter => same rows in the same order
    # (videos.sort key is (run_id, video_id)).
    study = tmp_path / "study"
    _run(
        study,
        "20261002T064850Z-youtube-hhc",
        {
            "records.json": _api_items(
                [("vid-b", "b", "Ch", ""), ("vid-a", "a", "Ch", "")]
            )
        },
    )
    _run(
        study,
        "20261008T122515Z-youtube-hhc",
        {"records.json": _api_items([("vid-c", "c", "Ch", "")])},
    )

    first = build_video_export(study)
    second = build_video_export(study)

    assert first["videos"] == second["videos"]
    assert first["runs"] == second["runs"]
    assert [(row["run_id"], row["video_id"]) for row in first["videos"]] == sorted(
        (row["run_id"], row["video_id"]) for row in first["videos"]
    )


def test_unrecorded_run_search_term_and_collected_at_stay_empty(tmp_path):
    # The 2026-10-08 batch has no recorded search condition: no search_term
    # in run_metadata.json (6 runs have no file at all, 3 carry only an
    # Apify id/status), so youtube_runs.csv leaves search_term empty instead
    # of inferring it from the run-id.  collected_at is empty for the same
    # reason (no collection_timestamp recorded).
    study = tmp_path / "study"
    _run(
        study,
        "20261008T122515Z-youtube-hhc",
        {"records.json": _api_items([("vid1", "a", "Ch", "")])},
    )
    _run(
        study,
        "20261008T122605Z-youtube-thch",
        {"records.json": _api_items([("vid2", "b", "Ch", "")])},
        metadata={"id": "xqAdRpFby6bKSHszN", "status": "SUCCEEDED"},
    )

    result = build_video_export(study)

    by_run = {run["run_id"]: run for run in result["runs"]}
    assert by_run["20261008T122515Z-youtube-hhc"]["search_term"] == ""
    assert by_run["20261008T122515Z-youtube-hhc"]["collected_at"] == ""
    assert by_run["20261008T122605Z-youtube-thch"]["search_term"] == ""
    assert by_run["20261008T122605Z-youtube-thch"]["collected_at"] == ""


def test_write_export_emits_both_tables(tmp_path):
    study = tmp_path / "study"
    _run(
        study,
        "20261002T064739Z-youtube-cbd",
        {"records.json": _api_items([("vid1", "a", "Ch", "")])},
    )
    out = tmp_path / "out"

    paths = write_export(build_video_export(study), out)

    assert [path.name for path in paths] == ["youtube_videos.csv", "youtube_runs.csv"]
    videos = list(csv.DictReader((out / "youtube_videos.csv").open(encoding="utf-8")))
    runs = list(csv.DictReader((out / "youtube_runs.csv").open(encoding="utf-8")))
    assert list(videos[0]) == list(VIDEO_COLUMNS)
    assert list(runs[0]) == list(RUN_COLUMNS)
    assert videos[0]["video_id"] == "vid1"
    assert runs[0]["video_rows"] == "1"
