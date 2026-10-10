#!/usr/bin/env python3
"""YouTube Data API 日付範囲指定データ取得（ページネーション & リジューム対応）

Usage:
    python3 scripts/debug/youtube_api_date_range.py SEARCH_TERM PUBLISHED_AFTER PUBLISHED_BEFORE [MAX_RESULTS] [MAX_PAGES]

例:
    python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2026-01-01 2026-04-01 50 10

再実行について:
    同一クエリ（検索語 + 日付範囲）はチェックポイントに状態が保存される。
    APIクォータ超過やトークン切れで中断しても、翌日以降に同じコマンドを再実行すれば
    取得済みページをスキップして続き（nextPageToken）から再開する。
    全ページ取得済みの場合は DB 格納のみ再実行される。--force-new で最初からやり直す。

終了コード:
    0 = 完了 / 2 = クォータ超過等で中断（再実行で再開可能） / 1 = その他のエラー

環境変数:
    DB_PATH          データベースパス
    YOUTUBE_ENV      APIキーの env ファイル
    CHECKPOINT_ROOT  チェックポイント保存先
    YOUTUBE_API_BASE API ベースURL（テスト用上書き可）

再利用:
    from youtube_api_date_range import collect_pages, aggregate_pages, store_to_sqlite
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = "datasets/youtube-consistency/data/trends.db"
DEFAULT_YOUTUBE_ENV = (
    "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env"
)
DEFAULT_CHECKPOINT_ROOT = "datasets/youtube-consistency/data/checkpoints"
DEFAULT_API_BASE = "https://www.googleapis.com"

QUOTA_REASONS = re.compile(
    r"quotaExceeded|dailyLimitExceeded|rateLimitExceeded|userRateLimitExceeded"
)


class QuotaExceededError(Exception):
    """APIクォータ超過・レート制限。進捗は保存済みで、再実行すれば再開できる。"""

    def __init__(self, reason, payload):
        super().__init__(f"quota exceeded: {reason}")
        self.reason = reason
        self.payload = payload


class ApiError(Exception):
    """その他のAPIエラー。"""

    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


def utcnow_iso():
    """現在時刻を UTC の ISO 8601 で返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_api_key(env_path):
    """env ファイルから YOUTUBE_API_KEY を読み込む（既存環境変数を優先）。"""
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key
    path = Path(env_path)
    if not path.is_file():
        raise FileNotFoundError(f"env ファイルが見つかりません: {env_path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("YOUTUBE_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise ValueError(f"YOUTUBE_API_KEY が設定されていません ({env_path})")


def compute_job_id(search_term, published_after, published_before):
    """検索語 + 日付範囲からジョブIDを導出（同一クエリなら常に同じID）。"""
    digest = hashlib.sha1(
        f"{search_term}|{published_after}|{published_before}".encode("utf-8")
    ).hexdigest()
    return f"yt_{digest[:12]}"


def load_state(state_file):
    """チェックポイント状態を読み込む。無ければ None。"""
    path = Path(state_file)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state_file, state, next_page_token, pages_fetched, status):
    """状態を更新して原子的に書き込む（ページ完了ごとに呼ぶ）。"""
    state["next_page_token"] = next_page_token or None
    state["pages_fetched"] = pages_fetched
    state["status"] = status
    state["updated_at"] = utcnow_iso()
    path = Path(state_file)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def fetch_page(api_base, api_key, params, endpoint="search"):
    """YouTube Data API へ GET リクエストを実行して JSON を返す。

    クォータ超過は QuotaExceededError、その他のAPIエラーは ApiError。
    """
    url = (
        f"{api_base}/youtube/v3/{endpoint}"
        f"?{urllib.parse.urlencode(params)}&key={api_key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise ApiError(f"HTTP {e.code}: {body[:200]}") from None
        reasons = [
            err.get("reason", "")
            for err in payload.get("error", {}).get("errors", [])
        ]
        reason_str = " ".join(reasons)
        if QUOTA_REASONS.search(reason_str):
            raise QuotaExceededError(reason_str, payload) from None
        message = payload.get("error", {}).get("message", body[:200])
        raise ApiError(message, payload) from None
    except urllib.error.URLError as e:
        # ネットワーク切断・DNS失敗等: 進捗は保存済みなので再実行すれば再開できる
        raise ApiError(f"接続エラー: {e.reason}") from None


def collect_pages(
    checkpoint_dir,
    state,
    api_base,
    api_key,
    max_results,
    max_pages,
    published_after,
    published_before,
    search_term,
):
    """全ページを取得して保存する。取得済みページはスキップして再開する。

    戻り値: (pages_fetched, next_page_token)
    中断時（クォータ超過）は QuotaExceededError 送出前に状態は保存済み。
    """
    page_dir = Path(checkpoint_dir) / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    state_file = Path(checkpoint_dir) / "state.json"

    pages_fetched = state["pages_fetched"]
    next_page_token = state.get("next_page_token")

    while True:
        if pages_fetched >= max_pages:
            print(
                f"  ⚠️  最大ページ数 ({max_pages}) に到達。中断します"
                "（--max-pages を増やして再実行すれば続きから再開）。"
            )
            break

        page_num = pages_fetched + 1
        page_file = page_dir / f"page_{page_num:04d}.json"

        if page_file.is_file():
            print(f"  ページ {page_num:04d}: 取得済み（スキップ）")
        else:
            params = {
                "part": "snippet",
                "q": search_term,
                "type": "video",
                "publishedAfter": f"{published_after}T00:00:00Z",
                "publishedBefore": f"{published_before}T00:00:00Z",
                "maxResults": max_results,
                "order": "date",
                "relevanceLanguage": "ja",
                "regionCode": "JP",
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                payload = fetch_page(api_base, api_key, params)
            except QuotaExceededError as e:
                error_path = Path(checkpoint_dir) / "last_error.json"
                error_path.write_text(
                    json.dumps(e.payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(f"  ❌ API クォータ超過 ({e.reason}). 進捗を保存しました。")
                print("  → 翌日以降に同じコマンドを再実行すると続きから再開します。")
                raise
            except ApiError as e:
                error_path = Path(checkpoint_dir) / "last_error.json"
                if e.payload is not None:
                    error_path.write_text(
                        json.dumps(e.payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                raise

            page_file.write_text(
                json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8"
            )

        pages_fetched += 1
        page = json.loads(page_file.read_text(encoding="utf-8"))
        next_page_token = page.get("nextPageToken")
        item_count = len(page.get("items", []))

        # ページ完了ごとに状態を永続化（ここでトークン切れても安全）
        save_state(state_file, state, next_page_token, pages_fetched, "pending")
        print(f"  ページ {page_num:04d}: {item_count} 件 (累計 {pages_fetched} ページ)")

        if not next_page_token:
            break

    return pages_fetched, next_page_token


def aggregate_pages(checkpoint_dir, run_id):
    """全ページの応答を統合し raw / ids / unique ファイルを /tmp に書き出す。

    戻り値: (raw_path, ids_path, unique_path, items)
    """
    page_dir = Path(checkpoint_dir) / "pages"
    items = []
    for page_file in sorted(page_dir.glob("page_*.json")):
        items.extend(json.loads(page_file.read_text(encoding="utf-8")).get("items", []))

    raw_path = Path(f"/tmp/{run_id}_raw.json")
    ids_path = Path(f"/tmp/{run_id}_ids.txt")
    unique_path = Path(f"/tmp/{run_id}_unique.txt")

    raw_path.write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    video_ids = [item["id"]["videoId"] for item in items]
    ids_path.write_text("\n".join(sorted(video_ids)) + "\n", encoding="utf-8")
    unique_path.write_text(
        "\n".join(sorted(set(video_ids))) + "\n", encoding="utf-8"
    )
    return raw_path, ids_path, unique_path, items


def store_to_sqlite(db_path, run_id, search_term, max_videos, items):
    """runs / videos / run_videos に格納する（冪等: 再実行しても重複しない）。"""
    unique_count = len({item["id"]["videoId"] for item in items})
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, search_term, max_videos, apify_dataset_id,
                collection_timestamp, record_count, unique_count,
                collector, collector_version)
               VALUES (?, ?, ?, 'youtube-data-api', datetime('now'), ?, ?,
                       'youtube-api', 'data-api-v3')""",
            (run_id, search_term, max_videos, len(items), unique_count),
        )
        for item in items:
            video_id = item["id"]["videoId"]
            snippet = item.get("snippet", {})
            conn.execute(
                """INSERT INTO videos
                   (video_id, title, channel, published_at, first_seen_run, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(video_id) DO UPDATE SET
                     title = COALESCE(videos.title, excluded.title),
                     channel = COALESCE(videos.channel, excluded.channel),
                     published_at = COALESCE(videos.published_at, excluded.published_at)""",
                (
                    video_id,
                    snippet.get("title"),
                    snippet.get("channelTitle"),
                    snippet.get("publishedAt"),
                    run_id,
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO run_videos (run_id, video_id) VALUES (?, ?)",
                (run_id, video_id),
            )
        conn.commit()
    finally:
        conn.close()
    return unique_count


def compute_match_stats(db_path, run_id):
    """現ランのうち累積で既出 / 新規の件数を返す (unique, already_collected, new)。"""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """WITH cumulative AS (
                   SELECT DISTINCT rv.video_id
                   FROM run_videos rv
                   WHERE rv.run_id != ?
               ),
               current_run AS (
                   SELECT DISTINCT video_id
                   FROM run_videos
                   WHERE run_id = ?
               )
               SELECT COUNT(*),
                      COALESCE(SUM(CASE WHEN c.video_id IN
                          (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END), 0),
                      COALESCE(SUM(CASE WHEN c.video_id NOT IN
                          (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END), 0)
               FROM current_run c""",
            (run_id, run_id),
        ).fetchone()
    finally:
        conn.close()
    return row


def cumulative_unique_count(db_path, search_term):
    """検索クエリに対する累積ユニーク動画数を返す。"""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """SELECT COUNT(DISTINCT v.video_id)
               FROM videos v
               JOIN run_videos rv ON v.video_id = rv.video_id
               JOIN runs r ON rv.run_id = r.run_id
               WHERE r.search_term = ?""",
            (search_term,),
        ).fetchone()
    finally:
        conn.close()
    return row[0]


def build_parser():
    parser = argparse.ArgumentParser(
        description="YouTube Data API 日付範囲指定データ取得（リジューム対応）"
    )
    parser.add_argument("search_term", nargs="?", default="CBD リキッド")
    parser.add_argument("published_after", nargs="?", default="2026-01-01")
    parser.add_argument("published_before", nargs="?", default="2026-04-01")
    parser.add_argument("max_results", nargs="?", type=int, default=50,
                        help="1ページあたりの最大取得件数 (<=50)")
    parser.add_argument("max_pages", nargs="?", type=int, default=10,
                        help="最大取得ページ数（再実行時に増やせば続きから再開）")
    parser.add_argument("--db-path", default=os.environ.get("DB_PATH", DEFAULT_DB_PATH))
    parser.add_argument("--env-file",
                        default=os.environ.get("YOUTUBE_ENV", DEFAULT_YOUTUBE_ENV),
                        help="YOUTUBE_API_KEY を含む env ファイル")
    parser.add_argument("--checkpoint-root",
                        default=os.environ.get("CHECKPOINT_ROOT", DEFAULT_CHECKPOINT_ROOT))
    parser.add_argument("--api-base",
                        default=os.environ.get("YOUTUBE_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--force-new", action="store_true",
                        help="既存チェックポイントを退避して最初から取得")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    # 日付パラメータの検証（例: 2016-13-01 のような月溢れをAPI到達前に検出）
    try:
        after = date.fromisoformat(args.published_after)
        before = date.fromisoformat(args.published_before)
        if after >= before:
            raise ValueError(
                f"published_after ({args.published_after}) が published_before "
                f"({args.published_before}) 以降になっています"
            )
    except ValueError as e:
        print(f"❌ 日付パラメータが不正: {e}")
        print("   例: 2016-12-01 2017-01-01 （12月は翌年01-01まで）")
        return 1

    try:
        api_key = load_api_key(args.env_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 1

    job_id = compute_job_id(args.search_term, args.published_after,
                            args.published_before)
    checkpoint_dir = Path(args.checkpoint_root) / job_id
    state_file = checkpoint_dir / "state.json"

    print("=========================================")
    print("YouTube Data API 日付範囲指定データ取得")
    print("=========================================")
    print()
    print(f"検索クエリ: {args.search_term}")
    print(f"開始日: {args.published_after}")
    print(f"終了日: {args.published_before}")
    print(f"maxResults/ページ: {args.max_results}")
    print(f"最大ページ数: {args.max_pages}")
    print(f"データベース: {args.db_path}")
    print(f"チェックポイント: {checkpoint_dir}")
    print()

    # --- 状態読み込み ---
    state = load_state(state_file)
    if state is not None and args.force_new:
        archived = checkpoint_dir.with_name(
            f"{checkpoint_dir.name}_replaced_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        )
        shutil.move(str(checkpoint_dir), str(archived))
        print(f"⚠️  --force-new: 既存チェックポイントを退避しました → {archived}")
        state = None

    if state is not None:
        print(
            f"🔄 既存チェックポイントを検出 → Run ID: {state['run_id']} "
            f"(取得済み {state['pages_fetched']} ページ, 状態: {state['status']})"
        )
        if state["status"] == "completed":
            print("  → 全ページ取得済み。DB 格納フェーズのみ再実行します。")
        elif state.get("next_page_token"):
            print("  → 次トークンあり。続きから再開します。")
        else:
            print("  → 次トークンなし。集計・DB 格納に進みます。")
        print()

    # 新規ジョブの初期化
    if state is None:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        # run_id にジョブハッシュを含める: 高速ループで同一秒に開始された別ジョブでも衝突しない
        run_id = (
            f"yt_api_{job_id[3:]}_"
            f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        )
        state = {
            "job_id": job_id,
            "run_id": run_id,
            "search_term": args.search_term,
            "published_after": args.published_after,
            "published_before": args.published_before,
            "max_results_per_page": args.max_results,
            "next_page_token": None,
            "pages_fetched": 0,
            "status": "pending",
            "started_at": utcnow_iso(),
            "updated_at": utcnow_iso(),
        }
        save_state(state_file, state, None, 0, "pending")
        print(f"Run ID: {run_id} (新規ジョブ)")
        print()

    run_id = state["run_id"]

    # --- Step 1: API 実行（ページネーション + リジューム） ---
    print("【Step 1】API 実行中...")
    if state["status"] != "completed":
        try:
            pages_fetched, next_page_token = collect_pages(
                checkpoint_dir,
                state,
                args.api_base,
                api_key,
                args.max_results,
                args.max_pages,
                args.published_after,
                args.published_before,
                args.search_term,
            )
        except QuotaExceededError:
            return 2
        except ApiError as e:
            print(f"  ❌ API エラー: {e}")
            return 1
    else:
        print("  【Step 1】API 実行スキップ（全ページ取得済み）")
        pages_fetched = state["pages_fetched"]
        next_page_token = state.get("next_page_token")
    print()

    # --- Step 2: 全ページ統合 + videoId 抽出 ---
    print("【Step 2】videoId 抽出中...")
    raw_path, ids_path, unique_path, items = aggregate_pages(checkpoint_dir, run_id)
    total = len(items)
    unique_ids = {item["id"]["videoId"] for item in items}
    unique_count = len(unique_ids)
    print(f"  総行数: {total}")
    print(f"  ユニークID数: {unique_count}")
    print(f"  重複数: {total - unique_count}")
    print()

    # --- Step 3: 日付範囲確認 ---
    print("【Step 3】日付範囲確認...")
    published_dates = sorted(
        item["snippet"]["publishedAt"] for item in items if "snippet" in item
    )
    if published_dates:
        print(f"  最古: {published_dates[0]}")
        print(f"  最新: {published_dates[-1]}")
    print()

    # --- Step 4: SQLite 格納 ---
    print("【Step 4】SQLite 格納中...")
    store_to_sqlite(
        args.db_path,
        run_id,
        args.search_term,
        args.max_results * pages_fetched,
        items,
    )
    print("  ✅ 格納完了")
    print()

    # --- Step 5: 一致率計算 ---
    print("【Step 5】一致率計算...")
    unique_n, already, new = compute_match_stats(args.db_path, run_id)
    print(f"    unique_count: {unique_n}")
    print(f"    already_collected: {already}")
    print(f"    new_videos: {new}")
    print()

    # 状態を完了に更新
    save_state(state_file, state, None, pages_fetched, "completed")

    # --- Step 6: 結果サマリー ---
    print("=========================================")
    print("結果サマリー")
    print("=========================================")
    print()
    print("【Run 情報】")
    print(f"  Run ID: {run_id}")
    print(f"  Job ID: {job_id}")
    print(f"  検索クエリ: {args.search_term}")
    print(f"  開始日: {args.published_after}")
    print(f"  終了日: {args.published_before}")
    print(f"  取得ページ数: {pages_fetched}")
    print()
    print("【取得結果】")
    print(f"  取得件数: {total}")
    if next_page_token:
        print("  次ページトークン: あり（最大ページ数到達による中断）")
    else:
        print("  次ページトークン: なし（全件取得）")
    print()
    print("【累積統計】")
    print(f"  総ユニーク動画数: {cumulative_unique_count(args.db_path, args.search_term)}")
    print()
    print("【ファイルパス】")
    print(f"  Raw: {raw_path}")
    print(f"  IDs: {ids_path}")
    print(f"  Unique: {unique_path}")
    print(f"  Checkpoint: {checkpoint_dir}")
    print()
    print("=========================================")
    print("完了")
    print("=========================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
