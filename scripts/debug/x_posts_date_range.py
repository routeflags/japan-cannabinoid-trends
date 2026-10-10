#!/usr/bin/env python3
"""X (Twitter) 投稿 日付範囲指定データ取得（リジューム対応）

YouTube 版 (youtube_api_date_range.py) と同一の設計思想で、Apify Actor
`rBaTEHzveTxZPraGv` (x-posts-search) を使って日付範囲指定で投稿を取得する。

Usage:
    python3 scripts/debug/x_posts_date_range.py SEARCH_TERM PUBLISHED_AFTER PUBLISHED_BEFORE [MAX_ITEMS]

例:
    python3 scripts/debug/x_posts_date_range.py "CBD リキッド" 2016-01-01 2016-02-01 50

再実行について:
    同一クエリ（検索語 + 日付範囲）はチェックポイントに状態が保存される。
    取得失敗・課金エラー・中断後は同じコマンドの再実行で続きから再開する。
    完了済みのジョブは API を呼ばずに DB 格納のみ再実行される（冪等）。
    --force-new で最初からやり直す。

終了コード:
    0 = 完了 / 2 = 課金・レート制限等で中断（再実行で再開可能） / 1 = その他のエラー

環境変数:
    DB_PATH          データベースパス
    APIFY_ENV        Apify トークンの env ファイル
    CHECKPOINT_ROOT  チェックポイント保存先
    APIFY_API_BASE   Apify API ベースURL（テスト用上書き可）

再利用:
    from x_posts_date_range import collect_posts, store_to_sqlite
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = "datasets/x-consistency/data/trends.db"
DEFAULT_APIFY_ENV = (
    "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env"
)
DEFAULT_CHECKPOINT_ROOT = "datasets/x-consistency/data/checkpoints"
DEFAULT_APIFY_BASE = "https://api.apify.com"
ACTOR_ID = "rBaTEHzveTxZPraGv"  # x-posts-search

# 課金・レート制限を示すエラー判定
BILLING_REASONS = re.compile(
    r"billing|insufficient|credit|plan limit|rate.?limit|too many", re.IGNORECASE
)


class BillingError(Exception):
    """課金・レート制限で中断。進捗は保存済みで、再実行すれば再開できる。"""

    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


class ApiError(Exception):
    """その他のAPIエラー。"""

    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


def utcnow_iso():
    """現在時刻を UTC の ISO 8601 で返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_apify_token(env_path):
    """env ファイルから APIFY_TOKEN を読み込む（既存環境変数を優先）。"""
    token = os.environ.get("APIFY_TOKEN")
    if token:
        return token
    path = Path(env_path)
    if not path.is_file():
        raise FileNotFoundError(f"env ファイルが見つかりません: {env_path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("APIFY_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            if token:
                return token
    raise ValueError(f"APIFY_TOKEN が設定されていません ({env_path})")


def compute_job_id(search_term, published_after, published_before):
    """検索語 + 日付範囲からジョブIDを導出（同一クエリなら常に同じID）。"""
    digest = hashlib.sha1(
        f"{search_term}|{published_after}|{published_before}".encode("utf-8")
    ).hexdigest()
    return f"x_{digest[:12]}"


def load_state(state_file):
    """チェックポイント状態を読み込む。無ければ None。"""
    path = Path(state_file)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state_file, state, status, **extra):
    """状態を更新して原子的に書き込む。"""
    state["status"] = status
    state["updated_at"] = utcnow_iso()
    state.update(extra)
    path = Path(state_file)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def _request(url, method="GET", payload=None, token=None):
    """Apify API へリクエストを送り JSON を返す。"""
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise ApiError(f"HTTP {e.code}: {body[:300]}") from None
        message = json.dumps(payload, ensure_ascii=False)[:300]
        if e.code in (402, 429) or BILLING_REASONS.search(message):
            raise BillingError(message, payload) from None
        raise ApiError(message, payload) from None
    except urllib.error.URLError as e:
        # ネットワーク断: 進捗は保存済みなので再実行すれば再開できる
        raise ApiError(f"接続エラー: {e.reason}") from None


def build_query(search_term, published_after, published_before):
    """X の検索演算子 since:/until: を付与したクエリを返す。"""
    return f"{search_term} since:{published_after} until:{published_before}"


def run_actor(api_base, token, actor_id, run_input, wait_seconds=180):
    """Actor を実行し、完了を待って run オブジェクトを返す。"""
    url = (
        f"{api_base}/v2/acts/{actor_id}/runs"
        f"?waitForFinish={int(wait_seconds)}"
    )
    run = _request(url, method="POST", payload=run_input, token=token)
    status = (run.get("data") or {}).get("status")

    # 未完了ならポーリング（最大5分）
    run_id = (run.get("data") or {}).get("id")
    deadline = time.time() + 300
    while status in ("RUNNING", "READY", "SUCCEEDED") and status != "SUCCEEDED":
        if time.time() > deadline:
            break
        time.sleep(5)
        run = _request(
            f"{api_base}/v2/actor-runs/{run_id}", method="GET", token=token
        )
        status = (run.get("data") or {}).get("status")

    if status == "FAILED":
        raise ApiError(f"Actor 実行失敗 (run_id={run_id})")
    return run.get("data") or {}


def fetch_dataset_items(api_base, token, dataset_id):
    """Dataset の全アイテムを取得してリストで返す。"""
    url = (
        f"{api_base}/v2/datasets/{dataset_id}/items"
        f"?clean=true&format=json"
    )
    return _request(url, method="GET", token=token)


def collect_posts(checkpoint_dir, state, api_base, token, max_items,
                  search_term, published_after, published_before):
    """投稿を取得して保存する。完了済みなら API を呼ばない。

    戻り値: (items, apify_run_id, apify_dataset_id)
    """
    page_dir = Path(checkpoint_dir) / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    state_file = Path(checkpoint_dir) / "state.json"

    page_file = page_dir / "page_0001.json"

    # 完了済み: 保存済み raw から復元（API を呼ばない）
    if state.get("status") == "completed" and page_file.is_file():
        items = json.loads(page_file.read_text(encoding="utf-8"))
        return items, state.get("apify_run_id"), state.get("apify_dataset_id")

    # 保存済み raw があればそれを使う（中断後の再開）
    if page_file.is_file():
        items = json.loads(page_file.read_text(encoding="utf-8"))
        save_state(state_file, state, "completed")
        return items, state.get("apify_run_id"), state.get("apify_dataset_id")

    query = build_query(search_term, published_after, published_before)
    run_input = {"query": query, "maxItems": max_items}

    try:
        run = run_actor(api_base, token, ACTOR_ID, run_input)
    except BillingError as e:
        error_path = Path(checkpoint_dir) / "last_error.json"
        if e.payload is not None:
            error_path.write_text(
                json.dumps(e.payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(f"  ❌ 課金・レート制限で中断: {e}")
        print("  → 後日、同じコマンドを再実行すると続きから再開します。")
        raise
    except ApiError:
        raise

    apify_run_id = run.get("id")
    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise ApiError(f"defaultDatasetId が返りませんでした (run_id={apify_run_id})")

    items = fetch_dataset_items(api_base, token, dataset_id)
    page_file.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_state(
        state_file, state, "completed",
        apify_run_id=apify_run_id, apify_dataset_id=dataset_id,
    )
    return items, apify_run_id, dataset_id


def to_iso(ts_ms):
    """Unix ミリ秒を UTC の ISO 8601 に変換する。"""
    if not ts_ms:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def store_to_sqlite(db_path, run_id, search_term, max_items, items,
                    apify_actor_id, apify_dataset_id):
    """runs / posts / run_posts に格納する（冪等: 再実行しても重複しない）。"""
    created_ats = [to_iso(i.get("timestamp")) for i in items if i.get("timestamp")]
    collection_ts = max(created_ats) if created_ats else utcnow_iso()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, source, search_term, max_items, apify_actor_id,
                apify_dataset_id, collection_timestamp, record_count,
                unique_count, collector, collector_version)
               VALUES (?, 'x', ?, ?, ?, ?, ?, ?, ?,
                       'apify', 'x-posts-search')""",
            (
                run_id, search_term, max_items, apify_actor_id,
                apify_dataset_id, collection_ts, len(items),
                len({i.get("postId") for i in items}),
            ),
        )
        for item in items:
            post_id = item.get("postId")
            if not post_id:
                continue
            author = item.get("author") or {}
            conn.execute(
                """INSERT INTO posts
                   (post_id, text, url, created_at, author_name,
                    author_screen_name, author_user_id, favourite_count,
                    repost_count, reply_count, quote_count,
                    first_seen_run, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(post_id) DO UPDATE SET
                     text = COALESCE(posts.text, excluded.text),
                     url = COALESCE(posts.url, excluded.url),
                     created_at = COALESCE(posts.created_at, excluded.created_at),
                     author_name = COALESCE(posts.author_name, excluded.author_name),
                     author_screen_name = COALESCE(posts.author_screen_name, excluded.author_screen_name),
                     author_user_id = COALESCE(posts.author_user_id, excluded.author_user_id),
                     favourite_count = COALESCE(posts.favourite_count, excluded.favourite_count),
                     repost_count = COALESCE(posts.repost_count, excluded.repost_count),
                     reply_count = COALESCE(posts.reply_count, excluded.reply_count),
                     quote_count = COALESCE(posts.quote_count, excluded.quote_count)""",
                (
                    post_id, item.get("postText"), item.get("postUrl"),
                    to_iso(item.get("timestamp")), author.get("name"),
                    author.get("screenName"), author.get("userId"),
                    item.get("favouriteCount"), item.get("repostCount"),
                    item.get("replyCount"), item.get("quoteCount"), run_id,
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO run_posts (run_id, post_id) VALUES (?, ?)",
                (run_id, post_id),
            )
        conn.commit()
    finally:
        conn.close()


def compute_match_stats(db_path, run_id):
    """現ランのうち累積で既出 / 新規の件数を返す (unique, already, new)。"""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """WITH cumulative AS (
                   SELECT DISTINCT rp.post_id
                   FROM run_posts rp WHERE rp.run_id != ?
               ),
               current_run AS (
                   SELECT DISTINCT post_id FROM run_posts WHERE run_id = ?
               )
               SELECT COUNT(*),
                      COALESCE(SUM(CASE WHEN c.post_id IN
                          (SELECT post_id FROM cumulative) THEN 1 ELSE 0 END), 0),
                      COALESCE(SUM(CASE WHEN c.post_id NOT IN
                          (SELECT post_id FROM cumulative) THEN 1 ELSE 0 END), 0)
               FROM current_run c""",
            (run_id, run_id),
        ).fetchone()
    finally:
        conn.close()
    return row


def cumulative_unique_count(db_path, search_term):
    """検索クエリに対する累積ユニーク投稿数を返す。"""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """SELECT COUNT(DISTINCT p.post_id)
               FROM posts p
               JOIN run_posts rp ON p.post_id = rp.post_id
               JOIN runs r ON rp.run_id = r.run_id
               WHERE r.search_term = ?""",
            (search_term,),
        ).fetchone()
    finally:
        conn.close()
    return row[0]


def build_parser():
    parser = argparse.ArgumentParser(
        description="X 投稿 日付範囲指定データ取得（リジューム対応）"
    )
    parser.add_argument("search_term", nargs="?", default="CBD リキッド")
    parser.add_argument("published_after", nargs="?", default="2026-01-01")
    parser.add_argument("published_before", nargs="?", default="2026-02-01")
    parser.add_argument("max_items", nargs="?", type=int, default=50,
                        help="取得上限件数（課金に直結。50-100推奨）")
    parser.add_argument("--db-path", default=os.environ.get("DB_PATH", DEFAULT_DB_PATH))
    parser.add_argument("--env-file",
                        default=os.environ.get("APIFY_ENV", DEFAULT_APIFY_ENV),
                        help="APIFY_TOKEN を含む env ファイル")
    parser.add_argument("--checkpoint-root",
                        default=os.environ.get("CHECKPOINT_ROOT", DEFAULT_CHECKPOINT_ROOT))
    parser.add_argument("--api-base",
                        default=os.environ.get("APIFY_API_BASE", DEFAULT_APIFY_BASE))
    parser.add_argument("--force-new", action="store_true",
                        help="既存チェックポイントを退避して最初から取得")
    parser.add_argument("--init-db", action="store_true",
                        help="スキーマを作成してから実行する")
    return parser


def init_db(db_path):
    """スキーマファイルから DB を初期化する（存在しても安全）。"""
    schema = Path("datasets/x-consistency/schema/schema.sql")
    if not schema.is_file():
        raise FileNotFoundError(f"スキーマが見つかりません: {schema}")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def main(argv=None):
    args = build_parser().parse_args(argv)

    # 日付パラメータの検証
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
        token = load_apify_token(args.env_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 1

    if args.init_db:
        init_db(args.db_path)

    if not Path(args.db_path).parent.is_dir():
        Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)

    job_id = compute_job_id(args.search_term, args.published_after,
                            args.published_before)
    checkpoint_dir = Path(args.checkpoint_root) / job_id
    state_file = checkpoint_dir / "state.json"

    print("=========================================")
    print("X 投稿 日付範囲指定データ取得 (Apify)")
    print("=========================================")
    print()
    print(f"検索クエリ: {args.search_term}")
    print(f"X演算子:    {build_query(args.search_term, args.published_after, args.published_before)}")
    print(f"maxItems:   {args.max_items}")
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
            f"(状態: {state['status']})"
        )
        if state["status"] == "completed":
            print("  → 取得済み。DB 格納フェーズのみ再実行します（API 呼び出しなし）。")
        print()

    if state is None:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        run_id = (
            f"x_api_{job_id[2:]}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        )
        state = {
            "job_id": job_id,
            "run_id": run_id,
            "search_term": args.search_term,
            "published_after": args.published_after,
            "published_before": args.published_before,
            "max_items": args.max_items,
            "apify_run_id": None,
            "apify_dataset_id": None,
            "status": "pending",
            "started_at": utcnow_iso(),
            "updated_at": utcnow_iso(),
        }
        save_state(state_file, state, "pending")
        print(f"Run ID: {run_id} (新規ジョブ)")
        print()

    run_id = state["run_id"]

    # --- Step 1: 取得 ---
    print("【Step 1】Apify で取得中...")
    try:
        items, apify_run_id, dataset_id = collect_posts(
            checkpoint_dir, state, args.api_base, token,
            args.max_items, args.search_term,
            args.published_after, args.published_before,
        )
    except BillingError:
        return 2
    except ApiError as e:
        print(f"  ❌ API エラー: {e}")
        return 1
    print(f"  取得件数: {len(items)}")
    print(f"  Apify run: {apify_run_id}")
    print()

    # --- Step 2: SQLite 格納 ---
    print("【Step 2】SQLite 格納中...")
    store_to_sqlite(
        args.db_path, run_id, args.search_term, args.max_items, items,
        ACTOR_ID, dataset_id,
    )
    print("  ✅ 格納完了")
    print()

    # --- Step 3: 一致率計算 ---
    print("【Step 3】一致率計算...")
    unique_n, already, new = compute_match_stats(args.db_path, run_id)
    print(f"    unique_count: {unique_n}")
    print(f"    already_collected: {already}")
    print(f"    new_posts: {new}")
    print()

    # --- サマリー ---
    print("=========================================")
    print("結果サマリー")
    print("=========================================")
    print(f"  Run ID: {run_id}")
    print(f"  Job ID: {job_id}")
    print(f"  検索クエリ: {args.search_term}")
    print(f"  期間: {args.published_after} → {args.published_before}")
    print(f"  取得件数: {len(items)}")
    print(f"  累積ユニーク投稿数: {cumulative_unique_count(args.db_path, args.search_term)}")
    print(f"  Checkpoint: {checkpoint_dir}")
    print("=========================================")
    print("完了")
    print("=========================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
