#!/usr/bin/env python3
"""
platform_data.db に TikTok 関連テーブルを追加する。
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "platform_data.db"

CREATE_TIKTOK_POSTS_SQL = """
CREATE TABLE IF NOT EXISTS tiktok_posts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id            TEXT NOT NULL UNIQUE,
    platform            TEXT NOT NULL DEFAULT 'tiktok',
    account_id          TEXT DEFAULT '',
    account_name        TEXT DEFAULT '',
    video_type          TEXT DEFAULT 'video',
    caption             TEXT DEFAULT '',
    permalink_url       TEXT DEFAULT '',
    thumbnail_url       TEXT DEFAULT '',
    duration_seconds    INTEGER DEFAULT 0,
    published_at        TEXT NOT NULL,
    status              TEXT DEFAULT 'published',
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now'))
);
"""

CREATE_TIKTOK_POST_METRICS_SQL = """
CREATE TABLE IF NOT EXISTS tiktok_post_metrics (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id                        TEXT NOT NULL,
    snapshot_date                   TEXT NOT NULL,
    views                           INTEGER DEFAULT 0,
    likes                           INTEGER DEFAULT 0,
    comments                        INTEGER DEFAULT 0,
    shares                          INTEGER DEFAULT 0,
    saves                           INTEGER DEFAULT 0,
    total_play_time_seconds         REAL    DEFAULT 0.0,
    avg_watch_time_seconds          REAL    DEFAULT 0.0,
    completion_rate                 REAL    DEFAULT 0.0,
    profile_visits                  INTEGER DEFAULT 0,
    new_viewers                     INTEGER DEFAULT 0,
    returning_viewers_pct           REAL    DEFAULT 0.0,
    non_followers_pct               REAL    DEFAULT 0.0,
    followers_gained                INTEGER DEFAULT 0,
    traffic_for_you_pct             REAL    DEFAULT 0.0,
    traffic_personal_profile_pct    REAL    DEFAULT 0.0,
    traffic_search_pct              REAL    DEFAULT 0.0,
    traffic_following_pct           REAL    DEFAULT 0.0,
    traffic_sound_pct               REAL    DEFAULT 0.0,
    traffic_other_pct               REAL    DEFAULT 0.0,
    estimated_revenue_jpy           REAL    DEFAULT 0.0,
    fetched_at                      TEXT DEFAULT (datetime('now')),
    UNIQUE(video_id, snapshot_date),
    FOREIGN KEY (video_id) REFERENCES tiktok_posts(video_id)
);
"""


def create_tables(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(CREATE_TIKTOK_POSTS_SQL)
    cur.execute(CREATE_TIKTOK_POST_METRICS_SQL)
    conn.commit()
    return [
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name IN ('tiktok_posts', 'tiktok_post_metrics') "
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
