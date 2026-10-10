# scripts/debug — 収集・検証スクリプト

カンナビノイド関連データの収集と、その品質検証を行うスクリプト集。

| スクリプト | 用途 |
|---|---|
| [`youtube_apify_store.py`](./youtube_apify_store.py) | **YouTube 収集本体**（Apify）→ SQLite 格納 |
| [`x_posts_date_range.py`](./x_posts_date_range.py) | **X (Twitter) 収集**（Apify）→ SQLite 格納 |
| [`youtube_idempotency_check.sh`](./youtube_idempotency_check.sh) | YouTube の冪等性（再現性）検証 |
| `youtube_api_date_range.py` | ⚠️ **旧: YouTube Data API v3 版。利用規約の観点から計画から除外済み** |

> **YouTube Data API v3 は使用しない。** 利用規約上の判断により計画から除外。
> 収集はすべて Apify 経由で行う。

---

## youtube_apify_store.py

Apify Actor `h7sDV53CddomktSi5`（streamers/youtube-scraper）で YouTube を検索し、
SQLite (`datasets/youtube-consistency/data/trends.db`) に格納する。

### 使い方

```bash
python3 scripts/debug/youtube_apify_store.py [SEARCH_TERM] [DATE_FILTER] \
  [--db-path PATH] [--env-file PATH] [--init-db]

# 例
python3 scripts/debug/youtube_apify_store.py "CBD リキッド" month
python3 scripts/debug/youtube_apify_store.py "HHBD リキッド" all
```

### DATE_FILTER

| 値 | 意味 |
|---|---|
| `all` | **全期間**（`dateFilter` を送らない） |
| `hour` | 直近1時間 |
| `today` | 直近24時間 |
| `week` | 直近7日 |
| `month` | 直近30日 |

> **絶対日付は指定できない**（相対期間のみ）。`all` は関連度ベースの全期間取得。

### オプション

| オプション | 環境変数 | デフォルト |
|---|---|---|
| `--db-path` | `DB_PATH` | `datasets/youtube-consistency/data/trends.db` |
| `--env-file` | `APIFY_ENV` | symphony_workspaces の `.env.d/apify.env` |
| `--init-db` | — | `schema/schema.sql` から DB を初期化してから実行 |

### 出力

実行したコマンド、取得件数、DB 動画総数、run_id、取得一覧（タイトル + URL）のみを出力する。

### 仕様上の要点

- **冪等**: 同一 video_id は `ON CONFLICT DO UPDATE` で欠損メタのみ補完。再実行しても重複しない
- **ポーリング**: Actor の完了 (`SUCCEEDED`) を最大15分待ってから dataset を取得する。
  未完了の空 dataset を「0件」として格納しない
- **失敗と0件を区別**: dataset がリスト形式でなければエラー。`SUCCEEDED` で0件なら真の `observed_zero`
- **`lang:ja` は使えない**: YouTube 検索演算子に `lang:` は存在しない。付けると検索が壊れる

### Apify 仕様（検証済み）

- 3つの動画上限（`maxResults` / `maxResultsShorts` / `maxResultStreams`）が**全て0**だと Actor が失敗する
- `maxResults` の maximum は **999999**
- `dateFilter` は **ローリング窓**（`month` = 直近30日）。暦月ではない
- `oldestPostDate` は **channel URL 専用**。指定すると `sortVideosBy` は `NEWEST` に自動リセット
- `sortVideosBy: OLDEST` は `oldestPostDate` 併用時に効かない（実測で不規則な順）

---

## x_posts_date_range.py

Apify Actor `rBaTEHzveTxZPraGv`（x-posts-search）で X 投稿を検索し、
SQLite (`datasets/x-consistency/data/trends.db`) に格納する。

```bash
python3 scripts/debug/x_posts_date_range.py [SEARCH_TERM] [PUBLISHED_AFTER] [PUBLISHED_BEFORE] [MAX_ITEMS] \
  [--db-path PATH] [--env-file PATH] [--init-db]

# 例
python3 scripts/debug/x_posts_date_range.py "CBD リキッド" 2016-01-01 2016-02-01 50
```

### 日付指定

X の検索演算子 `since:` / `until:` を `query` に付与する（Actor 側の仕様）。

```
CBD リキッド since:2016-01-01 until:2016-02-01
```

### 出力テーブル

`runs` / `posts` / `run_posts`。`posts` には postId・本文・URL・投稿日時・作者・エンゲージメントを格納。

### 冪等性（実測）

同一クエリを4回独立取得し、**全ペア 100% の重複率**を確認済み
（2016-01、投稿6件）。期間指定があるため安定する。
ただし件数が上限に達する月は未検証。

---

## youtube_idempotency_check.sh

同一パラメータで2回独立取得し、videoId の重複率で再現性を測る。

```bash
bash scripts/debug/youtube_idempotency_check.sh [SEARCH_TERM] [DATE_FILTER]

# 例
bash scripts/debug/youtube_idempotency_check.sh "CBD リキッド" month
```

### 判定基準（評価レポート B4 準拠）

| 重複率 | 判定 |
|---|---|
| ≥95% | ✅ PASS |
| 80–94% | ⚠️ CONDITIONAL |
| <80% | ❌ FAIL |

### 実測結果

| 条件 | 重複率 | 判定 |
|---|---|---|
| `dateFilter: month` | **100.0%** | ✅ PASS |
| 日付フィルタなし（旧 danek Actor） | 55–76% | ❌ FAIL |

**日付で期間を絞ると再現性が確保される**。絞らないと関連度アルゴリズムが毎回揺れる。

---

## 関連資料

- データセット仕様: [`datasets/youtube-consistency/README.md`](../../datasets/youtube-consistency/README.md)
- Actor 評価記録: [`research/apify/actor-evaluations.md`](../../research/apify/actor-evaluations.md)
- Apify スキル: [`.github/skills/apify-youtube-scraper/SKILL.md`](../../.github/skills/apify-youtube-scraper/SKILL.md)
