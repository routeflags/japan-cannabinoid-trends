#!/usr/bin/env python3
"""
JSON ファイルから TikTok 投稿データと日次メトリクスを platform_data.db に投入する。
"""

import argparse
import json
import sqlite3
from pathlib import Path

from create_tiktok_tables import DB_PATH, create_tables


POST_COLUMNS = [
    "video_id",
    "platform",
    "account_id",
    "account_name",
    "video_type",
    "caption",
    "permalink_url",
    "thumbnail_url",
    "duration_seconds",
    "published_at",
    "status",
]

METRIC_COLUMNS = [
    "video_id",
    "snapshot_date",
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "total_play_time_seconds",
    "avg_watch_time_seconds",
    "completion_rate",
    "profile_visits",
    "new_viewers",
    "returning_viewers_pct",
    "non_followers_pct",
    "followers_gained",
    "traffic_for_you_pct",
    "traffic_personal_profile_pct",
    "traffic_search_pct",
    "traffic_following_pct",
    "traffic_sound_pct",
    "traffic_other_pct",
    "estimated_revenue_jpy",
]

POST_DEFAULTS = {
    "platform": "tiktok",
    "account_id": "",
    "account_name": "",
    "video_type": "video",
    "caption": "",
    "permalink_url": "",
    "thumbnail_url": "",
    "duration_seconds": 0,
    "status": "published",
}

METRIC_DEFAULTS = {
    "views": 0,
    "likes": 0,
    "comments": 0,
    "shares": 0,
    "saves": 0,
    "total_play_time_seconds": 0.0,
    "avg_watch_time_seconds": 0.0,
    "completion_rate": 0.0,
    "profile_visits": 0,
    "new_viewers": 0,
    "returning_viewers_pct": 0.0,
    "non_followers_pct": 0.0,
    "followers_gained": 0,
    "traffic_for_you_pct": 0.0,
    "traffic_personal_profile_pct": 0.0,
    "traffic_search_pct": 0.0,
    "traffic_following_pct": 0.0,
    "traffic_sound_pct": 0.0,
    "traffic_other_pct": 0.0,
    "estimated_revenue_jpy": 0.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import TikTok post and metrics JSON into platform_data.db"
    )
    parser.add_argument("input", help="JSON file path")
    return parser.parse_args()


def load_payload(path: Path) -> dict:
    with path.open() as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON must be an object")
    return payload


def normalize_post(item: dict) -> tuple:
    merged = {**POST_DEFAULTS, **item}
    if not merged.get("video_id"):
        raise ValueError("posts[].video_id is required")
    if not merged.get("published_at"):
        raise ValueError(f"published_at is required: {merged['video_id']}")
    if not merged.get("permalink_url"):
        merged["permalink_url"] = (
            f"https://www.tiktok.com/@{merged['account_name']}/video/{merged['video_id']}"
            if merged.get("account_name")
            else ""
        )
    return tuple(merged[column] for column in POST_COLUMNS)


def normalize_metric(item: dict) -> tuple:
    merged = {**METRIC_DEFAULTS, **item}
    if not merged.get("video_id"):
        raise ValueError("metrics[].video_id is required")
    if not merged.get("snapshot_date"):
        raise ValueError(f"snapshot_date is required: {merged['video_id']}")
    if "watch_time_seconds" in merged and "total_play_time_seconds" not in item:
        merged["total_play_time_seconds"] = merged["watch_time_seconds"]
    return tuple(merged[column] for column in METRIC_COLUMNS)


def upsert_post(cur: sqlite3.Cursor, row: tuple) -> None:
    cur.execute(
        """
        INSERT INTO tiktok_posts (
            video_id, platform, account_id, account_name, video_type,
            caption, permalink_url, thumbnail_url, duration_seconds,
            published_at, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(video_id) DO UPDATE SET
            platform=excluded.platform,
            account_id=excluded.account_id,
            account_name=excluded.account_name,
            video_type=excluded.video_type,
            caption=excluded.caption,
            permalink_url=excluded.permalink_url,
            thumbnail_url=excluded.thumbnail_url,
            duration_seconds=excluded.duration_seconds,
            published_at=excluded.published_at,
            status=excluded.status,
            updated_at=datetime('now')
        """,
        row,
    )


def upsert_metric(cur: sqlite3.Cursor, row: tuple) -> None:
    cur.execute(
        """
        INSERT INTO tiktok_post_metrics (
            video_id, snapshot_date, views, likes, comments, shares, saves,
            total_play_time_seconds, avg_watch_time_seconds, completion_rate,
            profile_visits, new_viewers, returning_viewers_pct, non_followers_pct,
            followers_gained, traffic_for_you_pct, traffic_personal_profile_pct,
            traffic_search_pct, traffic_following_pct, traffic_sound_pct,
            traffic_other_pct, estimated_revenue_jpy
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(video_id, snapshot_date) DO UPDATE SET
            views=excluded.views,
            likes=excluded.likes,
            comments=excluded.comments,
            shares=excluded.shares,
            saves=excluded.saves,
            total_play_time_seconds=excluded.total_play_time_seconds,
            avg_watch_time_seconds=excluded.avg_watch_time_seconds,
            completion_rate=excluded.completion_rate,
            profile_visits=excluded.profile_visits,
            new_viewers=excluded.new_viewers,
            returning_viewers_pct=excluded.returning_viewers_pct,
            non_followers_pct=excluded.non_followers_pct,
            followers_gained=excluded.followers_gained,
            traffic_for_you_pct=excluded.traffic_for_you_pct,
            traffic_personal_profile_pct=excluded.traffic_personal_profile_pct,
            traffic_search_pct=excluded.traffic_search_pct,
            traffic_following_pct=excluded.traffic_following_pct,
            traffic_sound_pct=excluded.traffic_sound_pct,
            traffic_other_pct=excluded.traffic_other_pct,
            estimated_revenue_jpy=excluded.estimated_revenue_jpy,
            fetched_at=datetime('now')
        """,
        row,
    )


def import_payload(payload: dict, conn: sqlite3.Connection) -> tuple[int, int]:
    post_items = payload.get("posts", [])
    metric_items = payload.get("metrics", [])
    if not isinstance(post_items, list) or not isinstance(metric_items, list):
        raise ValueError("'posts' and 'metrics' must be arrays")

    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    posts_count = 0
    for index, item in enumerate(post_items, start=1):
        try:
            upsert_post(cur, normalize_post(item))
        except Exception as exc:
            raise ValueError(f"posts[{index}] failed: {exc}") from exc
        posts_count += 1

    metrics_count = 0
    for index, item in enumerate(metric_items, start=1):
        try:
            upsert_metric(cur, normalize_metric(item))
        except Exception as exc:
            raise ValueError(f"metrics[{index}] failed: {exc}") from exc
        metrics_count += 1

    conn.commit()
    return posts_count, metrics_count


def main() -> None:
    args = parse_args()
    payload = load_payload(Path(args.input))

    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        posts_count, metrics_count = import_payload(payload, conn)
        print(f"imported posts={posts_count} metrics={metrics_count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
