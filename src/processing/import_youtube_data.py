#!/usr/bin/env python3
"""
JSON ファイルから YouTube 動画データと日次メトリクスを platform_data.db に投入する。
"""

import argparse
import json
import sqlite3
from pathlib import Path

from create_youtube_tables import DB_PATH, create_tables


POST_COLUMNS = [
    "video_id",
    "platform",
    "channel_id",
    "channel_name",
    "video_type",
    "title",
    "description",
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
    "watch_time_minutes",
    "subscribers_gained",
    "subscribers_lost",
    "impressions",
    "impressions_ctr",
    "unique_viewers",
    "views_from_impressions",
    "watch_time_from_impressions_minutes",
    "traffic_yt_search_pct",
    "traffic_external_pct",
    "traffic_direct_pct",
    "traffic_channel_pct",
    "traffic_browse_pct",
    "traffic_playlist_pct",
    "avg_view_duration_seconds",
    "avg_view_percentage",
    "likes",
    "likes_rate",
    "comments",
    "shares",
    "hype_points",
    "hypes",
    "end_screen_ctr",
    "new_viewers_pct",
    "casual_viewers_pct",
    "regular_viewers_pct",
    "device_mobile_pct",
    "device_computer_pct",
    "device_tablet_pct",
    "device_tv_pct",
    "estimated_revenue_jpy",
]

POST_DEFAULTS = {
    "platform": "youtube",
    "channel_id": "",
    "channel_name": "",
    "video_type": "video",
    "title": "",
    "description": "",
    "permalink_url": "",
    "thumbnail_url": "",
    "duration_seconds": 0,
    "status": "published",
}

METRIC_DEFAULTS = {
    "views": 0,
    "watch_time_minutes": 0.0,
    "subscribers_gained": 0,
    "subscribers_lost": 0,
    "impressions": 0,
    "impressions_ctr": 0.0,
    "unique_viewers": 0,
    "views_from_impressions": 0,
    "watch_time_from_impressions_minutes": 0.0,
    "traffic_yt_search_pct": 0.0,
    "traffic_external_pct": 0.0,
    "traffic_direct_pct": 0.0,
    "traffic_channel_pct": 0.0,
    "traffic_browse_pct": 0.0,
    "traffic_playlist_pct": 0.0,
    "avg_view_duration_seconds": 0,
    "avg_view_percentage": 0.0,
    "likes": 0,
    "likes_rate": 0.0,
    "comments": 0,
    "shares": 0,
    "hype_points": 0,
    "hypes": 0,
    "end_screen_ctr": 0.0,
    "new_viewers_pct": 0.0,
    "casual_viewers_pct": 0.0,
    "regular_viewers_pct": 0.0,
    "device_mobile_pct": 0.0,
    "device_computer_pct": 0.0,
    "device_tablet_pct": 0.0,
    "device_tv_pct": 0.0,
    "estimated_revenue_jpy": 0.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import YouTube post and metrics JSON into platform_data.db"
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
        raise ValueError("post.video_id is required")
    if not merged.get("published_at"):
        raise ValueError(f"published_at is required: {merged['video_id']}")
    if not merged.get("permalink_url"):
        merged["permalink_url"] = f"https://www.youtube.com/watch?v={merged['video_id']}"
    return tuple(merged[column] for column in POST_COLUMNS)


def normalize_metric(item: dict) -> tuple:
    merged = {**METRIC_DEFAULTS, **item}
    if not merged.get("video_id"):
        raise ValueError("metrics[].video_id is required")
    if not merged.get("snapshot_date"):
        raise ValueError(f"snapshot_date is required: {merged['video_id']}")
    return tuple(merged[column] for column in METRIC_COLUMNS)


def upsert_post(cur: sqlite3.Cursor, row: tuple) -> None:
    cur.execute(
        """
        INSERT INTO youtube_posts (
            video_id, platform, channel_id, channel_name, video_type,
            title, description, permalink_url, thumbnail_url, duration_seconds,
            published_at, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(video_id) DO UPDATE SET
            platform=excluded.platform,
            channel_id=excluded.channel_id,
            channel_name=excluded.channel_name,
            video_type=excluded.video_type,
            title=excluded.title,
            description=excluded.description,
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
        INSERT INTO youtube_post_metrics (
            video_id, snapshot_date, views, watch_time_minutes,
            subscribers_gained, subscribers_lost, impressions, impressions_ctr,
            unique_viewers, views_from_impressions, watch_time_from_impressions_minutes,
            traffic_yt_search_pct, traffic_external_pct, traffic_direct_pct,
            traffic_channel_pct, traffic_browse_pct, traffic_playlist_pct,
            avg_view_duration_seconds, avg_view_percentage, likes, likes_rate,
            comments, shares, hype_points, hypes, end_screen_ctr,
            new_viewers_pct, casual_viewers_pct, regular_viewers_pct,
            device_mobile_pct, device_computer_pct, device_tablet_pct,
            device_tv_pct, estimated_revenue_jpy
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(video_id, snapshot_date) DO UPDATE SET
            views=excluded.views,
            watch_time_minutes=excluded.watch_time_minutes,
            subscribers_gained=excluded.subscribers_gained,
            subscribers_lost=excluded.subscribers_lost,
            impressions=excluded.impressions,
            impressions_ctr=excluded.impressions_ctr,
            unique_viewers=excluded.unique_viewers,
            views_from_impressions=excluded.views_from_impressions,
            watch_time_from_impressions_minutes=excluded.watch_time_from_impressions_minutes,
            traffic_yt_search_pct=excluded.traffic_yt_search_pct,
            traffic_external_pct=excluded.traffic_external_pct,
            traffic_direct_pct=excluded.traffic_direct_pct,
            traffic_channel_pct=excluded.traffic_channel_pct,
            traffic_browse_pct=excluded.traffic_browse_pct,
            traffic_playlist_pct=excluded.traffic_playlist_pct,
            avg_view_duration_seconds=excluded.avg_view_duration_seconds,
            avg_view_percentage=excluded.avg_view_percentage,
            likes=excluded.likes,
            likes_rate=excluded.likes_rate,
            comments=excluded.comments,
            shares=excluded.shares,
            hype_points=excluded.hype_points,
            hypes=excluded.hypes,
            end_screen_ctr=excluded.end_screen_ctr,
            new_viewers_pct=excluded.new_viewers_pct,
            casual_viewers_pct=excluded.casual_viewers_pct,
            regular_viewers_pct=excluded.regular_viewers_pct,
            device_mobile_pct=excluded.device_mobile_pct,
            device_computer_pct=excluded.device_computer_pct,
            device_tablet_pct=excluded.device_tablet_pct,
            device_tv_pct=excluded.device_tv_pct,
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
    for item in post_items:
        upsert_post(cur, normalize_post(item))
        posts_count += 1

    metrics_count = 0
    for item in metric_items:
        upsert_metric(cur, normalize_metric(item))
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
