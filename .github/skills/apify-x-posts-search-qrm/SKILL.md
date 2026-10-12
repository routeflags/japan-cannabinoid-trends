---
name: apify-x-posts-search-qrm
description: |
  Apify X Posts Search スキル（新Actor版）。X (Twitter) の投稿を日付範囲＋言語指定で取得する。
  日付は timeSince/timeUntil 分離フィールド、言語は language フィールドで指定。
  「X検索（日付指定）」「期間指定X検索」「X データ収集（期間）」「X言語フィルタ」などで使う。
---

# Apify X Posts Search スキル（日付範囲＋言語指定・新Actor版）

Apify Actor `qrmKEcWmE4WGXuuvd`（outspoken_strategy/twitter-post-search-scraper）を使って、X (Twitter) の投稿を**日付範囲＋言語指定付き**で取得する。

- Actor: `qrmKEcWmE4WGXuuvd` / outspoken_strategy/twitter-post-search-scraper
- 課金: PAY_PER_EVENT（Actor Start $0.00005＋結果 $0.0004/件。1000件で約$0.45）
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` ＋ **Xセッション必須**（Cookie または使い捨てアカウント）

---

## トリガー

- 「X検索（日付指定）」
- 「期間指定X検索」
- 「X データ収集（期間）」
- 「X言語フィルタ」
- 「新しいX Actor」

---

## 旧 Actor との違い

| 項目 | apify-x-search（旧） | apify-x-posts-search（旧2） | **本スキル（新）** |
|------|---------------------|---------------------------|-------------------|
| Actor ID | `cPYLH3QT9GyzKhB4S` | `rBaTEHzveTxZPraGv` | **`qrmKEcWmE4WGXuuvd`** |
| 日付指定 | query内 `since:`/`until:`（不安定） | query内 `since:`/`until:` | **分離フィールド `timeSince`/`timeUntil`** |
| 言語指定 | query内 `lang:ja` | なし | **分離フィールド `language: "ja"`** |
| 検索タブ | `section` | なし | **`search_type`: Latest/Top** |
| 上限 | `maxPages` | `maxItems` | **`numberOfTweets`（最大5000）** |
| 認証 | 不要 | 不要 | **Xセッション必須** |
| コスト | $0.0025/件 | 要確認 | $0.0004/件 |

---

## 前提

- Apifyアカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在
- **Xセッション**: 使い捨てアカウントのCookie（`auth_token`＋`ct0`）を `/tmp/x_cookies.json` 等に用意。**個人アカウントは厳禁**
- Cookie取得: Safariは開発→Webインスペクタ→ストレージ→Cookie。Chrome/EdgeはCookie-Editor拡張

---

## 入力スキーマ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ✅ | 検索キーワード（1件。複数行で複数可） |
| `queries` | array | — | 複数キーワード（各々検索・重複排除） |
| `search_type` | string | — | Latest（既定・時系列）/ Top（engagement順） |
| `numberOfTweets` | integer | — | キーワード毎の目標（最大5000、既定100） |
| `scrapeAll` | boolean | — | 既定true。falseは1ページのみ |
| `timeSince` / `timeUntil` | string | — | `yyyy-mm-dd`。`since:`/`until:` として適用＋再検証 |
| `language` | string | — | ISO 639-1（例：`ja`）。`lang:` として適用 |
| `cookies` | array | ⚠️実質必須 | Xログインセッション（Cookie-Editor形式） |
| `twUsername`/`twPassword` | string | — | 自動ログイン用（2FA無効必須）。Cookieの代替 |
| `proxyConfiguration` | object | — | Residential推奨 |

---

## 日付・言語指定

### 分離フィールド方式（推奨）

```json
{
  "query": "CBD リキッド",
  "search_type": "Latest",
  "numberOfTweets": 50,
  "timeSince": "2026-10-01",
  "timeUntil": "2026-11-01",
  "language": "ja",
  "scrapeAll": false
}
```

### クエリ文字列方式（後方互換）

`since:`/`until:`/`lang:` をquery内に書いても通過するが、分離フィールド推奨。

---

## 実行方法

### 推奨：収集スクリプト経由

```bash
# 基本（日付範囲＋言語指定＋DB格納＋チェックポイント付き）
python3 scripts/debug/x_posts_qrm_lang.py "CBD リキッド" 2026-10-01 2026-11-01 50 --lang ja

# Topタブ・言語無指定
python3 scripts/debug/x_posts_qrm_lang.py "CBD リキッド" 2026-10-01 2026-11-01 50 --lang "" --search-type Top

# Cookie指定（環境変数でも可: X_COOKIES_FILE）
python3 scripts/debug/x_posts_qrm_lang.py "CBD リキッド" 2026-10-01 2026-11-01 50 \
  --lang ja --cookies-file /tmp/x_cookies.json
```

スクリプト仕様:
- DB: `datasets/x-consistency/data/trends.db`（`runs`/`posts`/`run_posts`、冪等）
- チェックポイント: `datasets/x-consistency/data/checkpoints/`（リジューム対応）
- 終了コード: 0=完了 / 2=課金中断（再実行で再開）/ 1=その他エラー
- 出力マッピング: `id_str`→post_id、`full_text`→text、`user.screen_name`→author等

### API直叩き（少量テスト用）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env
COOKIES=$(cat /tmp/x_cookies.json)

R=$(curl -s -m 60 -X POST "https://api.apify.com/v2/acts/qrmKEcWmE4WGXuuvd/runs" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --argjson cookies "$COOKIES" '{
    query: "CBD リキッド",
    search_type: "Latest",
    numberOfTweets: 10,
    timeSince: "2026-10-01",
    timeUntil: "2026-10-08",
    language: "ja",
    scrapeAll: false,
    cookies: $cookies
  }')")
echo "$R" | jq -r '.data | "status=\(.status) run=\(.id)"'
```

---

## 出力スキーマ（postsテーブル対応）

| Actorキー | posts列 | 備考 |
|-----------|---------|------|
| `id_str` | post_id | 主キー |
| `full_text`/`text` | text | full優先 |
| `url` | url | |
| `created_at` | created_at | ISO8601 |
| `user.name` | author_name | |
| `user.screen_name` | author_screen_name | |
| `user.id_str` | author_user_id | |
| `favorites` | favourite_count | |
| `retweets` | repost_count | |
| `replies` | reply_count | |
| `quotes` | quote_count | |
| `views`/`lang`/`hashtags`/`mentions`/`media`/`bookmarks` | —（追加取得可） | postsに列なし。必要なら拡張 |

---

## データ品質チェック

```bash
# 件数と言語・日付範囲の確認
jq -r '[.[] | .lang] | group_by(.) | map("\(.[0]): \(length)") | join(", ")' /tmp/<run>_raw.json
jq -r '[.[].created_at] | "min=\(min) max=\(max)"' /tmp/<run>_raw.json
```

---

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `numberOfTweets` を 50-100 に制限、`scrapeAll: false` で少量テスト |
| 課金確認 | 実行後に actor-run の usageTotalUsd で確認 |
| テスト | 10件（約$0.004＋Start）で起動・認証・出力を検証してから本番 |

---

## 制約・注意

- **Xセッション必須**: Cookieなしでは即FAILEDの可能性。使い捨てアカウント使用
- `timeSince`/`timeUntil` は `yyyy-mm-dd` 形式。下限・上限の両方指定可
- `language` は `lang:` 演算子として適用される（実測：10/10件ja）
- 1実行1クエリ（複数クエリは `queries` 配列で指定可）
- 日付フィルタなしの旧Actor（`cPYLH3QT9GyzKhB4S`）とは別系統。移行時は同一クエリ並行取得で一致率検証推奨

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Provide at least one keyword` で即FAILED | 入力JSONが空（jq組み立て失敗等） | `-d` の内容を確認。素JSONで再試行 |
| `token-not-provided` | APIFY_TOKEN が空 | `source`＋`export`を確認 |
| 0件・認証エラー | Cookie期限切れ・プロキシブロック | Cookie再取得、Residential検討 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |

---

## 検証実績

| 項目 | 内容 |
|------|------|
| **Actor** | `qrmKEcWmE4WGXuuvd` (outspoken_strategy/twitter-post-search-scraper) |
| **テスト日** | 2026-10-12 |
| **Run ID** | `FCAj1HyD7XxYOLgC4` |
| **クエリ** | `CBD リキッド` / 2026-10-01〜10-08 / `language: ja` |
| **取得件数** | 10/10件、全件ja、窓内 |
| **出力** | 32キー。postsテーブル互換確認済み |

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `apify-mcp` | MCP 起動・認証 |
| `apify-x-search` | 日付フィルタ不要の検索（旧Actor・認証不要） |
| `apify-x-posts-search` | 日付指定検索（旧Actor `rBaTEHzveTxZPraGv`） |
| `research-x-search` | 研究用データ収集 |
