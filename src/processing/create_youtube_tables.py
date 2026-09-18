#!/usr/bin/env python3
"""
platform_data.db に YouTube 関連テーブルを追加する。
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "platform_data.db"

CREATE_YOUTUBE_POSTS_SQL = """
CREATE TABLE IF NOT EXISTS youtube_posts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id            TEXT NOT NULL UNIQUE,
    platform            TEXT NOT NULL DEFAULT 'youtube',
    channel_id          TEXT DEFAULT '',
    channel_name        TEXT DEFAULT '',
    video_type          TEXT DEFAULT 'video',
    title               TEXT DEFAULT '',
    description         TEXT DEFAULT '',
    permalink_url       TEXT DEFAULT '',
    thumbnail_url       TEXT DEFAULT '',
    duration_seconds    INTEGER DEFAULT 0,
    published_at        TEXT NOT NULL,
    status              TEXT DEFAULT 'published',
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now'))
);
"""

CREATE_YOUTUBE_POST_METRICS_SQL = """
CREATE TABLE IF NOT EXISTS youtube_post_metrics (
    id                                  INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id                            TEXT NOT NULL,
    snapshot_date                       TEXT NOT NULL,
    views                               INTEGER DEFAULT 0,
    watch_time_minutes                  REAL    DEFAULT 0.0,
    subscribers_gained                  INTEGER DEFAULT 0,
    subscribers_lost                    INTEGER DEFAULT 0,
    impressions                         INTEGER DEFAULT 0,
    impressions_ctr                     REAL    DEFAULT 0.0,
    unique_viewers                      INTEGER DEFAULT 0,
    views_from_impressions              INTEGER DEFAULT 0,
    watch_time_from_impressions_minutes REAL    DEFAULT 0.0,
    traffic_yt_search_pct               REAL    DEFAULT 0.0,
    traffic_external_pct                REAL    DEFAULT 0.0,
    traffic_direct_pct                  REAL    DEFAULT 0.0,
    traffic_channel_pct                 REAL    DEFAULT 0.0,
    traffic_browse_pct                  REAL    DEFAULT 0.0,
    traffic_playlist_pct                REAL    DEFAULT 0.0,
    avg_view_duration_seconds           INTEGER DEFAULT 0,
    avg_view_percentage                 REAL    DEFAULT 0.0,
    likes                               INTEGER DEFAULT 0,
    likes_rate                          REAL    DEFAULT 0.0,
    comments                            INTEGER DEFAULT 0,
    shares                              INTEGER DEFAULT 0,
    hype_points                         INTEGER DEFAULT 0,
    hypes                               INTEGER DEFAULT 0,
    end_screen_ctr                      REAL    DEFAULT 0.0,
    new_viewers_pct                     REAL    DEFAULT 0.0,
    casual_viewers_pct                  REAL    DEFAULT 0.0,
    regular_viewers_pct                 REAL    DEFAULT 0.0,
    device_mobile_pct                   REAL    DEFAULT 0.0,
    device_computer_pct                 REAL    DEFAULT 0.0,
    device_tablet_pct                   REAL    DEFAULT 0.0,
    device_tv_pct                       REAL    DEFAULT 0.0,
    estimated_revenue_jpy               REAL    DEFAULT 0.0,
    fetched_at                          TEXT DEFAULT (datetime('now')),
    UNIQUE(video_id, snapshot_date),
    FOREIGN KEY (video_id) REFERENCES youtube_posts(video_id)
);
"""

def create_tables(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(CREATE_YOUTUBE_POSTS_SQL)
    cur.execute(CREATE_YOUTUBE_POST_METRICS_SQL)
    conn.commit()
    return [
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name IN ('youtube_posts', 'youtube_post_metrics') "
            "ORDER BY name"
        ).fetchall()
    ]


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = create_tables(conn)
        print("created tables:", ", ".join(tables))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
