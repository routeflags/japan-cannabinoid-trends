# scripts/debug — YouTube Data API 日付範囲取得

## youtube_api_date_range.py

YouTube Data API v3 で日付範囲を指定して動画を検索取得し、SQLite (trends.db) に格納するデバッグ用スクリプト。ページネーション・中断再開（リジューム）対応。

### 必要環境

- Python 3 標準ライブラリのみ（追加パッケージ不要）
- `YOUTUBE_API_KEY` を含む env ファイル（デフォルト: `/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env`）
- `runs` / `videos` / `run_videos` テーブルを持つ SQLite DB（デフォルト: `datasets/youtube-consistency/data/trends.db`）

### 完全版コマンド

```bash
python3 scripts/debug/youtube_api_date_range.py \
  SEARCH_TERM PUBLISHED_AFTER PUBLISHED_BEFORE [MAX_RESULTS] [MAX_PAGES] \
  [--db-path PATH] [--env-file PATH] [--checkpoint-root PATH] \
  [--api-base URL] [--force-new]
```

### パラメータ

| 位置 | 名前 | デフォルト | 説明 |
|---|---|---|---|
| 1 | SEARCH_TERM | `CBD リキッド` | 検索クエリ |
| 2 | PUBLISHED_AFTER | `2026-01-01` | 取得開始日 (この日を含む) |
| 3 | PUBLISHED_BEFORE | `2026-04-01` | 取得終了日 (この日を含まない) |
| 4 | MAX_RESULTS | `50` | 1ページあたりの最大取得件数 (API上限 50) |
| 5 | MAX_PAGES | `10` | 最大取得ページ数 (50×10 = 最大500件) |

### オプション

| オプション | 環境変数 | デフォルト | 説明 |
|---|---|---|---|
| `--db-path` | `DB_PATH` | `datasets/youtube-consistency/data/trends.db` | SQLite パス |
| `--env-file` | `YOUTUBE_ENV` | 上記 youtube.env | APIキーの env ファイル |
| `--checkpoint-root` | `CHECKPOINT_ROOT` | `datasets/youtube-consistency/data/checkpoints` | チェックポイント保存先 |
| `--api-base` | `YOUTUBE_API_BASE` | `https://www.googleapis.com` | API ベースURL (テスト用) |
| `--force-new` | — | — | 既存チェックポイントを退避して最初から取得 |

### 終了コード

| コード | 意味 |
|---|---|
| 0 | 完了 |
| 2 | クォータ超過等で中断（**再実行すれば続きから再開**） |
| 1 | その他のエラー（接続エラー等。進捗は保存済み） |

### 中断再開（リジューム）

- 同一クエリ（検索語 + 日付範囲）はチェックポイントが共有される
- ページ取得ごとに `state.json` に `next_page_token` が保存される
- クォータ超過・トークン切れ・ネットワーク断の後、**翌日以降に同じコマンドを再実行**すれば取得済みページをスキップして続きから再開
- 全ページ取得済みの再実行は冪等（API を呼ばず DB 格納のみ再実行）
- ページ数を増やしたい場合は MAX_PAGES を増やして再実行

チェックポイント構成:

```
datasets/youtube-consistency/data/checkpoints/yt_<hash>/
├── state.json        # run_id, next_page_token, pages_fetched, status
├── last_error.json   # エラー時のみ保存
└── pages/
    └── page_0001.json  # API 応答 raw（イミュータブル）
```

### 実行例

```bash
# 基本
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2026-01-01 2026-02-01

# 2016年1月〜4月を1ヶ月ずつ取得
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2016-01-01 2016-02-01
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2016-02-01 2016-03-01
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2016-03-01 2016-04-01
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2016-04-01 2016-05-01

# 上記を一括実行
for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  next=$(printf "%02d" $((10#$m + 1)))
  python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" "2016-${m}-01" "2016-${next}-01" 2>&1 | tee /tmp/yt2016_${m}.log
done

# ログを残しながら実行
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2016-01-01 2016-02-01 \
  2>&1 | tee /tmp/yt2016_01.log
```

2017〜2019年を月次で取得:

```bash
# 個別実行（36ヶ月分）
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2017-01-01 2017-02-01
python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" 2017-02-01 2017-03-01
# ... 以下 2019-12-01 → 2020-01-01 まで同様

# 一括実行（年の繰り上がり対応済み: 12月は翌年01-01まで）
for y in 2017 2018 2019; do
  for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
    if [ "$m" = "12" ]; then
      next="$((y + 1))-01-01"
    else
      next="${y}-$(printf '%02d' $((10#$m + 1)))-01"
    fi
    python3 scripts/debug/youtube_api_date_range.py "CBD リキッド" "${y}-${m}-01" "$next" \
      2>&1 | tee "/tmp/yt_${y}${m}.log"
  done
done
```

### DB 格納内容

| テーブル | 内容 | 冪等性 |
|---|---|---|
| `runs` | run_id, 検索語, レコード数, ユニーク数 など | `INSERT OR REPLACE` (同一 run_id) |
| `videos` | video_id, タイトル, チャンネル, 公開日, 初出 run, 初出時刻 | `INSERT ... ON CONFLICT` (欠損メタのみ補完) |
| `run_videos` | run × video の対応 | `INSERT OR IGNORE` |

run_id 形式: `yt_api_<ジョブハッシュ12桁>_<UTCタイムスタンプ>`。
ジョブハッシュを含むため、同一秒に開始された別ジョブ（月跨ぎループ等）でも衝突しない。

### 既知の注意

- **月跨ぎループは年の繰り上がりに注意**: `for m in $(seq -w 1 12)` のようなループは 12月に `2016-13-01` を生成して失敗する。12月は `2016-12-01` → `2017-01-01` を指定すること（不正な日付は API 到達前に検出されて終了する）
- **run_id 衝突の歴史的バグ**: 2026-10-10 18:57 時点の旧版は run_id が秒精度タイムスタンプのみで、高速ループ時に同一秒の別ジョブが run_id を共有し 2016年1-3月・6-11月の runs/run_videos 混在が発生した。チェックポイントの raw 応答から月別に再構築して修正済み（修正ログ: 2026-10-10, チェックポイント raw から再構築、API消費なし）


補助ファイル（冪等・再実行で上書き）:

- `/tmp/<run_id>_raw.json` — 全ページ統合の raw データ
- `/tmp/<run_id>_ids.txt` / `_unique.txt` — videoId 一覧

### モジュールとしての再利用

```python
from youtube_api_date_range import (
    collect_pages,       # ページ取得（リジューム対応）
    aggregate_pages,     # 全ページ統合
    store_to_sqlite,     # DB 格納（冪等）
    compute_match_stats, # 既出/新規の照合
)
```

`datasets/youtube-consistency/data/checkpoints/` は収集の中間状態であり、再現性確保のため削除しないこと。取り直す場合のみ `--force-new` を使う。
