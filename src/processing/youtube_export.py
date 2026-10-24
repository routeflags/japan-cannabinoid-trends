"""Export a publishable, aggregate-only view of local YouTube raw runs.

Why this exists
---------------
The YouTube raw payloads under ``datasets/<study>/data/raw/youtube/`` are not
tracked: ``**/data/raw/*`` ignores every source except ``google_trends``, and the
payloads carry the video *description*, where channel operators publish contact
addresses (a scan of the two 10-year runs found 18 such addresses).  The policy
therefore is: **the raw stays local evidence, and only an aggregate is tracked**
(option B, owner decision 2026-10-23).

What is published here is one row per video: the identifier, title, channel and
publish date.  The description is never exported, and no per-video engagement
value is invented when the payload does not contain one.

Shapes that occur under ``data/raw/youtube/``
---------------------------------------------
1. ``{"items": [...]}`` — a YouTube Data API search response (may be paged over
   several files, e.g. ``records_2016_page2.json``);
2. ``[...]`` of API search items — the same records already unwrapped;
3. ``[...]`` of Apify rows — ``videoId`` / ``title`` / ``channel`` / ``publishedAt``;
4. ``{"error": ...}`` — a failed API call.  These are counted per run and
   reported, because a run that lost pages to quota errors must not look
   complete (missing is not zero).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

__all__ = [
    "VIDEO_COLUMNS",
    "RUN_COLUMNS",
    "build_video_export",
    "write_export",
]

VIDEO_COLUMNS = ("run_id", "video_id", "channel_title", "title")
RUN_COLUMNS = (
    "run_id",
    "search_term",
    "collected_at",
    "video_rows",
    "error_payloads",
    "unreadable_files",
)

#: Runs whose videos may be exported.  An allowlist, not a pattern: a run is
#: published only once its provenance has been reviewed, and the numbers here
#: reconcile with the collection summary the study already reports
#: (22+25+34+28+23+23+27 = 182 videos, 2026-10-02; plus
#: 27+20+30+24+22+20+27+21+24 = 215 videos, 2026-10-08; 397 total in 16 runs).
PUBLISHABLE_RUNS = {
    "20261002T064739Z-youtube-cbd": "CBD",
    "20261002T064821Z-youtube-thc": "THC",
    "20261002T064828Z-youtube-cbg": "CBG",
    "20261002T064850Z-youtube-hhc": "HHC",
    "20261002T064857Z-youtube-thcv": "THCV",
    "20261002T064905Z-youtube-cbd-オイル": "CBD オイル",
    "20261002T064911Z-youtube-thc-オイル": "THC オイル",
    # 2026-10-08 batch (ISS-20261024-YT-013): actor, search_term and the
    # retrieval limit are unrecorded, so the value stays "" (empty).  The
    # exporter must not infer the term from the run-id or the row count, and
    # these runs do not supply a search_term via run_metadata.json (6 runs
    # have no such file; the other 3 carry only an Apify id/status with no
    # collection fields).
    "20261008T122515Z-youtube-hhc": "",
    "20261008T122605Z-youtube-thch": "",
    "20261008T122647Z-youtube-thc-o": "",
    "20261008T125306Z-youtube-h4cbh": "",
    "20261008T125348Z-youtube-hhbd": "",
    "20261008T125428Z-youtube-hhch": "",
    "20261008T125501Z-youtube-crdp": "",
    "20261008T125544Z-youtube-crdh": "",
    "20261008T145348Z-youtube-cbn": "",
}

#: Why the other runs stay out.  A run that is not exported is written to
#: neither table -- a published table must not read as an account of it -- so the
#: reason stays here and in the operator's summary, never in the data (AGENTS.md:
#: missing is not zero).
EXCLUSION_REASONS = {
    "20261004T142147Z-youtube-cbd-10years": "incomplete 10-year series excluded from evidence (ISS-20261012-CBD-003): 2025 missing, 2023-2024 partial",
    "20261004T142430Z-youtube-cbg-10years": "incomplete 10-year series excluded from evidence (ISS-20261012-CBD-003)",
    "20261004T142508Z-youtube-thc-10years": "incomplete 10-year series excluded from evidence (ISS-20261012-CBD-003)",
    "20261004T142547Z-youtube-cbn-10years": "incomplete 10-year series excluded from evidence (ISS-20261012-CBD-003)",
    "20261004T144147Z-youtube-japanese-keywords-10years": "incomplete 10-year series excluded from evidence (ISS-20261012-CBD-003)",
    "20261005T132728Z-youtube-relevance-language-test": "methodology test collection, not evidence",
}

#: Runs collected with the YouTube Data API v3, whose raw was removed from the
#: repository by the 2026-10-12 policy decision.  The local copies that survive
#: must not be republished.
V3_DERIVED_MARKER = "-dated"


def _item_to_row(run_id: str, item: dict) -> dict | None:
    """Normalize one payload item, or ``None`` when it carries no video id."""
    snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
    identifier = item.get("id")
    if isinstance(identifier, dict):
        video_id = identifier.get("videoId")
    elif isinstance(identifier, str):
        video_id = identifier
    else:
        video_id = None
    video_id = video_id or item.get("videoId")
    if not isinstance(video_id, str) or not video_id:
        return None
    return {
        "run_id": run_id,
        "video_id": video_id,
        "channel_title": item.get("channel") or snippet.get("channelTitle") or "",
        "title": item.get("title") or snippet.get("title") or "",
    }


def _payload_items(payload) -> tuple[list[dict], bool]:
    """Return ``(items, is_error)`` for one payload document."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)], False
    if isinstance(payload, dict):
        if isinstance(payload.get("error"), (dict, str)):
            return [], True
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)], False
    return [], False


def _status(run_id: str) -> str:
    """``exported`` for a reviewed run, otherwise the reason it is withheld."""
    if run_id in PUBLISHABLE_RUNS:
        return "exported"
    if run_id in EXCLUSION_REASONS:
        return EXCLUSION_REASONS[run_id]
    if run_id.endswith(V3_DERIVED_MARKER):
        return "derived from YouTube Data API v3, withdrawn 2026-10-12"
    return "provenance not reviewed for publication"


def build_video_export(study_dir) -> dict:
    """Read ``data/raw/youtube/<run-id>/`` and return video and run rows."""
    raw = Path(study_dir) / "data" / "raw" / "youtube"
    videos: list[dict] = []
    runs: list[dict] = []
    withheld: list[dict] = []
    for run_dir in sorted(p for p in raw.glob("*") if p.is_dir()) if raw.is_dir() else []:
        status = _status(run_dir.name)
        metadata = {}
        try:
            metadata = json.loads(
                (run_dir / "run_metadata.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            metadata = {}
        seen: set[str] = set()
        video_rows = 0
        errors = 0
        unreadable = 0
        if status != "exported":
            # Withheld runs are not written anywhere in the artifact: the ones
            # that matter here were collected with means this repository has
            # since excluded, and a published table must not read as an account
            # of them.  The reason stays in code (EXCLUSION_REASONS) and in the
            # operator's summary, never in the data.
            withheld.append({"run_id": run_dir.name, "status": status})
            continue
        for payload_path in sorted(run_dir.glob("*.json")):
            if payload_path.name == "run_metadata.json":
                continue
            try:
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                unreadable += 1
                continue
            items, is_error = _payload_items(payload)
            if is_error:
                errors += 1
                continue
            for item in items:
                row = _item_to_row(run_dir.name, item)
                if row is None or row["video_id"] in seen:
                    continue
                seen.add(row["video_id"])
                videos.append(row)
                video_rows += 1
        runs.append(
            {
                "run_id": run_dir.name,
                "search_term": metadata.get("search_term", "")
                or PUBLISHABLE_RUNS.get(run_dir.name, ""),
                "collected_at": metadata.get("collection_timestamp", ""),
                "video_rows": video_rows,
                "error_payloads": errors,
                "unreadable_files": unreadable,
            }
        )
    videos.sort(key=lambda r: (r["run_id"], r["video_id"]))
    return {"videos": videos, "runs": runs, "withheld": withheld}


def write_export(result: dict, output_dir) -> list[Path]:
    """Write ``youtube_videos.csv`` and ``youtube_runs.csv``; return the paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, columns, rows in (
        ("youtube_videos.csv", VIDEO_COLUMNS, result["videos"]),
        ("youtube_runs.csv", RUN_COLUMNS, result["runs"]),
    ):
        path = out / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        written.append(path)
    return written
