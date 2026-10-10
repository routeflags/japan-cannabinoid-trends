# youtube-consistency — YouTube 検索結果の一貫性・重複分析

YouTube 検索クエリに対する複数回の収集 Run の一貫性（一致率）を検証するデータセット。

- 仕様: `docs/specs/youtube-sqlite-design.md`
- 状態: スキーマ整備済み・データ収集中

## 収集方法

**Apify Actor `h7sDV53CddomktSi5`（streamers/youtube-scraper）** を使用する。

```bash
python3 scripts/debug/youtube_apify_store.py "CBD リキッド" month
python3 scripts/debug/youtube_apify_store.py "HHBD リキッド" all
```

| dateFilter | 意味 |
|------------|------|
| `all` | 全期間（`dateFilter` を送らない） |
| `month` | 直近30日（ローリング窓） |
| `week` / `today` / `hour` | 直近7日 / 24時間 / 1時間 |

制約:
- **絶対日付は指定できない**（相対期間のみ）。`all` は関連度ベースの全期間取得
- `maxResults` は上限。3つの動画上限が全て0だと Actor が失敗する
- `lang:ja` は **YouTube 検索演算子として存在しない**（付けない）
- Actor の完了（`SUCCEEDED`）をポーリングで待ってから dataset を取得する

**YouTube Data API v3 は利用規約の観点から使用しない**（計画から除外）。

## データベース

SQLite データベース `data/trends.db` を使用。

**DB 名について**: 将来の複数ソース（X, TikTok, Instagram 等）拡張に備えて
`trends.db` として抽象化してある。ソース種別は `runs.source` カラム
（デフォルト `'youtube'`）で識別する。新規ソース追加時は
`schema/schema.sql` に対応テーブル群を追加し、テーブル名にソース接頭辞を付けるか、
`source` カラムで区別する方針を検討すること。

`data/` 配下の `.db` ファイルは Git にコミットしない（`.gitignore` で除外）。
再生成可能であり、公開対象は processed データとメタデータのみ。

## 構成

```
datasets/youtube-consistency/
├── data/
│   └── trends.db          # SQLite データベース（Git 管理外）
├── schema/
│   └── schema.sql         # スキーマ定義（テーブル・インデックス・ビュー）
├── queries/
│   ├── insert_run.sql     # Run / videos / run_videos 挿入
│   ├── calculate_rate.sql # Run 間の一致率計算
│   └── view_history.sql   # 一致率履歴取得
└── README.md
```

## 初期化

```bash
sqlite3 datasets/youtube-consistency/data/trends.db \
  < datasets/youtube-consistency/schema/schema.sql
```

## テーブル

| テーブル | 役割 |
|----------|------|
| `runs` | 収集実行の記録（run_id 単位、Raw データ不変） |
| `videos` | 動画マスタ（video_id 一意、初回収集情報を保持） |
| `run_videos` | Run と Video の関係（検索順位・重複フラグ） |

`runs` の主要カラム:

| カラム | 意味 |
|--------|------|
| `max_videos` | 取得上限（Actor に指定した値） |
| `record_count` | 実取得件数 |
| `unique_count` | ユニーク件数 |
| `apify_dataset_id` | Apify の dataset ID（Raw の追跡用） |

`videos` の主要カラム:

| カラム | 意味 |
|--------|------|
| `url` | 動画 URL（`https://www.youtube.com/watch?v=<video_id>`） |
| `published_at` | 公開日時（ISO 8601 / UTC） |
| `duration` | 長さ（秒） |

ビュー: `v_run_summary`（Run サマリー）, `v_video_appearance`（動画出現履歴）

一致率は保存せず都度計算する（`queries/calculate_rate.sql`, `queries/view_history.sql`）。
仕様書にあった `consistency_metrics` テーブル・`v_consistency_history` ビューは、
誰も投入・メンテナンスしないため削除済み。

## 冪等性・再現性

- **冪等性**: 同一 video_id は `INSERT OR IGNORE` / `ON CONFLICT DO UPDATE` で保護。
  再実行しても重複しない
- **再現性の実測**: `dateFilter: month` では重複率 100%（4回独立取得で全ペア一致）。
  `all` は関連度ベースのため結果が揺れる可能性があり **要検証**
- **`observed_zero` と失敗の区別**: Actor が `SUCCEEDED` で0件なら真の0件。
  ポーリングにより未完了 dataset を0件として格納しない

## 制約

- `runs` / `videos` の既存行は変更しない（Raw データ不変原則）
- 日付は ISO 8601 で統一
- 同一 `run_id` の重複 INSERT は行わない
- `INSERT OR IGNORE` により既存 video_id は保護される

## 既知の仕様差分

- 仕様 §3.4 / §5.2 の `consistency_metrics` および `v_consistency_history` は削除済み。
  一致率は `run_videos` から都度計算する（無人管理の事前集計テーブルは持たない方針）。
- 仕様 §6.1 の一致率クエリは `consistency_metrics` の run_number 依存をやめ、
  `runs.collection_timestamp` の前後関係で直前 Run 群を判定する実装に変更。

## データフロー

```
Step 1: Apify Actor 実行（完了をポーリングで待つ）
        ↓
Step 2: dataset から items を取得（リスト形式でない場合はエラー）
        ↓
Step 3: runs に INSERT OR REPLACE
        ↓
Step 4: videos に INSERT ... ON CONFLICT DO UPDATE（欠損メタのみ補完）
        ↓
Step 5: run_videos に INSERT OR IGNORE
        ↓
Step 6: 一致率を計算（queries/calculate_rate.sql / view_history.sql、都度計算）
```

途中で失敗しても Raw（Apify dataset）は追跡可能なため、再実行すれば冪等に復旧する。

## YouTube Data API v3

### YouTube Data Provenance and Usage

YouTube video metadata in this dataset was collected using the third-party [YouTube Scraper](https://apify.com/streamers/youtube-scraper) Actor on the Apify platform, rather than through direct use of the official YouTube Data API.

The collected metadata may include video IDs, titles, channel names, publication dates, and view counts. These records are used to study the emergence and temporal distribution of cannabinoid-related topics in Japan.

The research team has not identified a 30-day retention requirement in the applicable Apify Actor Terms. This does not constitute a representation that YouTube's platform terms, third-party rights, or applicable laws impose no additional restrictions.

The dataset is independently compiled and is not affiliated with or endorsed by YouTube, Google, or Apify.

**Licensing note:** The repository's CC BY 4.0 license applies only to original research materials and datasets to the extent that the authors have the rights to license them. It does not override third-party rights in source metadata or content.

For collection methodology and provenance details, see [`Data Provenance`](../../docs/provenance.md).
