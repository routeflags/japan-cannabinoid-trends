#!/usr/bin/env python3
"""YouTube 取得データを SQLite に格納する（Apify: streamers/youtube-scraper）

dateFilter（相対期間）で検索し、結果を datasets/youtube-consistency の DB に格納する。
チェックポイント・再開機能は無い単発実行。

使い方:
    python3 scripts/debug/youtube_apify_store.py [search_term] [dateFilter]

例:
    python3 scripts/debug/youtube_apify_store.py "CBD リキッド" month

dateFilter: hour | today | week | month | year（相対期間のみ・絶対日付は不可）

環境変数:
    APIFY_ENV   Apify トークンの env ファイル
    DB_PATH     データベースパス
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ACTOR_ID = "h7sDV53CddomktSi5"
APIFY_BASE = "https://api.apify.com"
DEFAULT_DB_PATH = "datasets/youtube-consistency/data/trends.db"
DEFAULT_APIFY_ENV = (
    "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env"
)
DATE_FILTERS = ("hour", "today", "week", "month", "year")


def load_token(env_path):
    """env ファイルから APIFY_TOKEN を読む（環境変数を優先）。"""
    tok = os.environ.get("APIFY_TOKEN")
    if tok:
        return tok
    p = Path(env_path)
    if not p.is_file():
        raise FileNotFoundError(f"env ファイルが見つかりません: {env_path}")
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("APIFY_TOKEN="):
            tok = line.split("=", 1)[1].strip().strip('"').strip("'")
            if tok:
                return tok
    raise ValueError(f"APIFY_TOKEN が設定されていません ({env_path})")


def api_request(url, method="GET", payload=None, token=None):
    """Apify API へリクエストし JSON を返す。"""
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"接続エラー: {e.reason}") from None


def fetch_items(token, query, date_filter):
    """Apify で検索し items リストを返す。"""
    run = api_request(
        f"{APIFY_BASE}/v2/acts/{ACTOR_ID}/runs?waitForFinish=180",
        method="POST",
        payload={
            "searchQueries": [query],
            "dateFilter": date_filter,
            "maxResults": 999999,
            "maxResultsShorts": 0,
            "maxResultStreams": 0,
            "sortingOrder": "date",
        },
        token=token,
    )
    data = run.get("data") or {}
    run_id = data.get("id")
    status = data.get("status")
    dataset_id = data.get("defaultDatasetId")
    if status == "FAILED":
        raise RuntimeError(f"Actor 実行失敗: {data.get('statusMessage')}")
    if not dataset_id:
        raise RuntimeError("defaultDatasetId が返りませんでした")
    items = api_request(
        f"{APIFY_BASE}/v2/datasets/{dataset_id}/items?clean=true&format=json",
        token=token,
    )
    return run_id, dataset_id, (items if isinstance(items, list) else [])


def duration_to_seconds(dur):
    """'HH:MM:SS' を秒数に変換する。"""
    if not dur or not isinstance(dur, str):
        return None
    try:
        parts = [int(p) for p in dur.split(":")]
    except ValueError:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def store(db_path, search_term, apify_run_id, dataset_id, items):
    """runs / videos / run_videos に格納する（冪等）。"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    unique = len({it.get("id") for it in items if it.get("id")})
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, source, search_term, max_videos, apify_dataset_id,
                collection_timestamp, record_count, unique_count,
                collector, collector_version)
               VALUES (?, 'youtube', ?, ?, ?, ?, ?, ?, 'apify', 'youtube-scraper')""",
            (apify_run_id, search_term, len(items), dataset_id,
             now, len(items), unique),
        )
        for it in items:
            vid = it.get("id")
            if not vid:
                continue
            conn.execute(
                """INSERT INTO videos
                   (video_id, title, channel, url, views, duration, published_at,
                    first_seen_run, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(video_id) DO UPDATE SET
                     title = COALESCE(videos.title, excluded.title),
                     channel = COALESCE(videos.channel, excluded.channel),
                     url = COALESCE(videos.url, excluded.url),
                     views = COALESCE(videos.views, excluded.views),
                     duration = COALESCE(videos.duration, excluded.duration),
                     published_at = COALESCE(videos.published_at, excluded.published_at)""",
                (
                    vid, it.get("title"), it.get("channelName"), it.get("url"),
                    it.get("viewCount"), duration_to_seconds(it.get("duration")),
                    it.get("date"), apify_run_id, now,
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO run_videos (run_id, video_id) VALUES (?, ?)",
                (apify_run_id, vid),
            )
        conn.commit()
    finally:
        conn.close()
    return unique


def main(argv=None):
    ap = argparse.ArgumentParser(description="Apify YouTube 取得 → SQLite 格納")
    ap.add_argument("search_term", nargs="?", default="CBD リキッド")
    ap.add_argument("date_filter", nargs="?", default="month", choices=DATE_FILTERS)
    ap.add_argument("--db-path", default=os.environ.get("DB_PATH", DEFAULT_DB_PATH))
    ap.add_argument("--env-file",
                    default=os.environ.get("APIFY_ENV", DEFAULT_APIFY_ENV))
    ap.add_argument("--init-db", action="store_true",
                    help="スキーマ作成を試みてから実行")
    args = ap.parse_args(argv)

    try:
        token = load_token(args.env_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 1

    if args.init_db:
        schema = Path("datasets/youtube-consistency/schema/schema.sql")
        if schema.is_file():
            conn = sqlite3.connect(args.db_path)
            try:
                conn.executescript(schema.read_text(encoding="utf-8"))
                conn.commit()
            finally:
                conn.close()

    Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)

    # 検索クエリ。YouTube 検索演算子に lang: は存在しないので付けない
    query = args.search_term

    print(f"python3 scripts/debug/youtube_apify_store.py \"{args.search_term}\" {args.date_filter}")
    print(f"  → query={query!r} dateFilter={args.date_filter} db={args.db_path}")

    apify_run_id, dataset_id, items = fetch_items(token, query, args.date_filter)
    unique = store(args.db_path, query, apify_run_id, dataset_id, items)

    conn = sqlite3.connect(args.db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    finally:
        conn.close()

    print(f"  ✅ 取得 {len(items)} 件 / ユニーク {unique} 件 / DB 動画総数 {total} / run={apify_run_id}")
    print()
    print("取得一覧:")
    for it in sorted(items, key=lambda x: x.get("date") or ""):
        print(f"  [{(it.get('date') or '')[:10]}] {it.get('title')}")
        print(f"    URL: {it.get('url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
