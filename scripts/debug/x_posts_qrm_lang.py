#!/usr/bin/env python3
"""X (Twitter) 投稿 日付範囲＋言語指定データ取得（リジューム対応）

Apify Actor `qrmKEcWmE4WGXuuvd` (outspoken_strategy/twitter-post-search-scraper)
を使って日付範囲＋言語指定で投稿を取得する。

x_posts_date_range.py (Actor rBaTEHzveTxZPraGv) との差分:
- 日付は timeSince/timeUntil 分離フィールド（yyyy-mm-dd）で指定
- language フィールドで lang: 相当の言語フィルタを指定可能
- search_type Latest/Top を選択可能
- Xセッション認証が必要（cookies / TW_COOKIES / twUsername+twPassword）
- 出力キー名が異なるため posts テーブルへのマッピングを変更

Usage:
    python3 scripts/debug/x_posts_qrm_lang.py SEARCH_TERM PUBLISHED_AFTER PUBLISHED_BEFORE [MAX_ITEMS] [--lang ja] [--search-type Latest]

例:
    python3 scripts/debug/x_posts_qrm_lang.py "CBD リキッド" 2026-10-01 2026-10-08 10 --lang ja

再実行について:
    同一クエリ（検索語 + 日付範囲 + 言語）はチェックポイントに状態が保存される。
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
    X_COOKIES_FILE   XセッションCookie JSONのパス（Cookie-Editor形式の配列）

再利用:
    from x_posts_qrm_lang import collect_posts, store_to_sqlite
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
ACTOR_ID = "qrmKEcWmE4WGXuuvd"  # outspoken_strategy/twitter-post-search-scraper
POLL_TIMEOUT = 900     # Actor 完了待ちの最大秒数 (15分)
POLL_INTERVAL = 10     # ポーリング間隔 (秒)

# 課金・レート制限を示すエラー判定
BILLING_REASONS = re.compile(
    r"billing|insufficient|credit|plan limit|rate.?limit|too many", re.IGNORECASE
)


class BillingError(Exception):
    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


class ApiError(Exception):
    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


def utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_apify_token(env_path):
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


def load_cookies(cookies_file):
    """XセッションCookie JSONを読み込む。なければ None（Actor側の認証解決に委ねる）。"""
    if not cookies_file:
        cookies_file = os.environ.get("X_COOKIES_FILE")
    if not cookies_file:
        return None
    p = Path(cookies_file)
    if not p.is_file():
        print(f"  ⚠️ Cookie ファイルが見つかりません: {cookies_file}（認証なしで続行）")
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ⚠️ Cookie ファイルが不正なJSON: {e}（認証なしで続行）")
        return None
    if not isinstance(data, list):
        print("  ⚠️ Cookie ファイルは配列形式である必要があります（認証なしで続行）")
        return None
    names = {c.get("name") for c in data if isinstance(c, dict)}
    if "auth_token" not in names or "ct0" not in names:
        print("  ⚠️ auth_token/ct0 が含まれていません（認証なしで続行）")
        return None
    return data


def compute_job_id(search_term, published_after, published_before, lang,
                   search_type):
    return "x_" + hashlib.sha256(
        f"{search_term}|{published_after}|{published_before}|{lang}|{search_type}".encode("utf-8")
    ).hexdigest()[:12]


def load_state(state_file):
    p = Path(state_file)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_state(state_file, state, status, **extra):
    state = dict(state)
    state["status"] = status
    state["updated_at"] = utcnow_iso()
    state.update(extra)
    Path(state_file).write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _request(url, method="GET", payload=None, token=None):
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
        if BILLING_REASONS.search(body):
            raise BillingError(f"HTTP {e.code}: {body[:300]}",
                               {"status": e.code, "body": body[:2000]})
        raise ApiError(f"HTTP {e.code}: {body[:300]}",
                       {"status": e.code, "body": body[:2000]})
    except urllib.error.URLError as e:
        raise ApiError(f"接続エラー: {e.reason}")


def run_actor(api_base, token, actor_id, run_input, wait_seconds=180):
    """Actor を非同期起動し、完了までポーリングして run を返す。"""
    run = _request(f"{api_base}/v2/acts/{actor_id}/runs",
                   method="POST", payload=run_input, token=token)
    data = (run.get("data") or {})
    run_id = data.get("id")
    status = data.get("status")
    if not run_id:
        raise ApiError(f"run_id が返りませんでした: {str(data)[:300]}")
    deadline = time.time() + POLL_TIMEOUT
    while status in ("READY", "RUNNING"):
        if time.time() > deadline:
            raise ApiError(
                f"Actor 完了待ちがタイムアウト (status={status}, "
                f"{POLL_TIMEOUT}秒, run_id={run_id})"
            )
        time.sleep(POLL_INTERVAL)
        run = _request(f"{api_base}/v2/actor-runs/{run_id}", token=token)
        data = run.get("data") or {}
        status = data.get("status")
    if status != "SUCCEEDED":
        msg = str(data.get("statusMessage", ""))[:300]
        body = json.dumps(data, ensure_ascii=False)[:1000]
        if BILLING_REASONS.search(msg + body):
            raise BillingError(f"Actor 実行中断: status={status} msg={msg}",
                               data)
        raise ApiError(f"Actor 実行失敗: status={status} msg={msg}", data)
    return data


def fetch_dataset_items(api_base, token, dataset_id):
    items = _request(
        f"{api_base}/v2/datasets/{dataset_id}/items?clean=true&format=json",
        token=token,
    )
    if not isinstance(items, list):
        raise ApiError(f"dataset がリスト形式でありません: {str(items)[:200]}")
    return items


def build_run_input(search_term, published_after, published_before, max_items,
                    lang, search_type, cookies):
    """新Actor用の入力JSONを組み立てる。日付・言語は分離フィールド。"""
    run_input = {
        "query": search_term,
        "search_type": search_type,
        "numberOfTweets": max_items,
        "timeSince": published_after,
        "timeUntil": published_before,
        "scrapeAll": False,
    }
    if lang:
        run_input["language"] = lang
    if cookies:
        run_input["cookies"] = cookies
    return run_input


def collect_posts(checkpoint_dir, state, api_base, token, max_items,
                  search_term, published_after, published_before,
                  lang, search_type, cookies):
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

    run_input = build_run_input(
        search_term, published_after, published_before, max_items,
        lang, search_type, cookies,
    )

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


def store_to_sqlite(db_path, run_id, search_term, max_items, items,
                    apify_actor_id, apify_dataset_id):
    """runs / posts / run_posts に格納する（冪等: 再実行しても重複しない）。

    新Actorの出力キー (id_str/text/url/created_at/user/favorites/retweets/
    replies/quotes) を posts テーブル列にマッピングする。
    """
    created_ats = [i.get("created_at") or i.get("createdTime")
                   for i in items if i.get("created_at") or i.get("createdTime")]
    collection_ts = max(created_ats) if created_ats else utcnow_iso()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, source, search_term, max_items, apify_actor_id,
                apify_dataset_id, collection_timestamp, record_count,
                unique_count, collector, collector_version)
               VALUES (?, 'x', ?, ?, ?, ?, ?, ?, ?,
                       'apify', 'twitter-post-search-scraper')""",
            (
                run_id, search_term, max_items, apify_actor_id,
                apify_dataset_id, collection_ts, len(items),
                len({i.get("id_str") or i.get("id") for i in items}),
            ),
        )
        for item in items:
            post_id = item.get("id_str") or item.get("id")
            if not post_id:
                continue
            user = item.get("user") or {}
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
                    post_id,
                    item.get("full_text") or item.get("text"),
                    item.get("url") or item.get("twitterUrl"),
                    item.get("created_at") or item.get("createdTime"),
                    user.get("name"),
                    user.get("screen_name") or item.get("username"),
                    user.get("id_str"),
                    item.get("favorites"),
                    item.get("retweets"),
                    item.get("replies"),
                    item.get("quotes"),
                    run_id,
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
        description="X 投稿 日付範囲＋言語指定データ取得（リジューム対応）"
    )
    parser.add_argument("search_term", nargs="?", default="CBD リキッド")
    parser.add_argument("published_after", nargs="?", default="2026-01-01")
    parser.add_argument("published_before", nargs="?", default="2026-02-01")
    parser.add_argument("max_items", nargs="?", type=int, default=50,
                        help="取得上限件数（課金に直結。50-100推奨）")
    parser.add_argument("--lang", default=os.environ.get("X_LANG", "ja"),
                        help="言語フィルタ (ISO 639-1)。空文字で無指定")
    parser.add_argument("--search-type", default="Latest",
                        choices=["Latest", "Top"],
                        help="検索タブ (既定: Latest)")
    parser.add_argument("--cookies-file", default=os.environ.get("X_COOKIES_FILE"),
                        help="XセッションCookie JSONのパス")
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

    cookies = load_cookies(args.cookies_file)

    if args.init_db:
        init_db(args.db_path)

    if not Path(args.db_path).parent.is_dir():
        Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)

    job_id = compute_job_id(args.search_term, args.published_after,
                            args.published_before, args.lang,
                            args.search_type)
    checkpoint_dir = Path(args.checkpoint_root) / job_id
    state_file = checkpoint_dir / "state.json"

    print("=========================================")
    print("X 投稿 日付範囲＋言語指定データ取得 (Apify)")
    print("=========================================")
    print()
    print(f"Actor:       {ACTOR_ID} (twitter-post-search-scraper)")
    print(f"検索クエリ: {args.search_term}")
    print(f"期間:        {args.published_after} → {args.published_before}")
    print(f"言語:        {args.lang or '(無指定)'}")
    print(f"検索タブ:   {args.search_type}")
    print(f"認証:        {'Cookieあり' if cookies else 'Cookieなし（Actor側解決に委譲）'}")
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
            f"x_qrm_{job_id[2:]}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        )
        state = {
            "job_id": job_id,
            "run_id": run_id,
            "search_term": args.search_term,
            "published_after": args.published_after,
            "published_before": args.published_before,
            "lang": args.lang,
            "search_type": args.search_type,
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
            args.lang, args.search_type, cookies,
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
    print(f"  言語: {args.lang or '(無指定)'}")
    print(f"  取得件数: {len(items)}")
    print(f"  累積ユニーク投稿数: {cumulative_unique_count(args.db_path, args.search_term)}")
    print(f"  Checkpoint: {checkpoint_dir}")
    print("=========================================")
    print("完了")
    print("=========================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
