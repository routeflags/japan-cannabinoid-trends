# youtube-consistency — YouTube 検索結果の一貫性・重複分析

YouTube 検索クエリに対する複数回の収集 Run の一貫性（一致率）を検証するデータセット。
一貫性検証に加えて、**5 化合物の全期間スナップショット**と
**CBD リキッドの 2016–2019 月次系列**を保持する YouTube データの main store としても機能する。

- 仕様: `docs/specs/youtube-sqlite-design.md`
- 状態: 一貫性検証は完了（同一クエリ 6 回取得で 39/39 = 100% 一致）。スナップショット 5 化合物格納済み
- 関連レポート: [`research/youtube/20261012-youtube-consistency-and-cbd-timeline.md`](../../research/youtube/20261012-youtube-consistency-and-cbd-timeline.md)

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

## 収集ツールの経緯（v3 API データの削除について）

本 dataset の開発過程では日付範囲指定の必要性から一時的に
**YouTube Data API v3** 版の収集スクリプト（`youtube_api_date_range.py`、削除済み）を導入し、
2016-01〜2019-12 の月次ウィンドウ 48 件分のデータを取得した。

しかし [README かつての方針]「YouTube Data API v3 は利用規約の観点から使用しない」に照らし、
**2026-10-12 に方針決定を行い、v3 由来の全 run（`collector='youtube-api'`、55 件）と
関連 run_videos を DB から削除した**。削除前のバックアップは
`data/trends.db.bak-20261011T1511Z`（Git 管理外・ローカル保持）。

削除済みデータの集計結果（月次件数・公開年分布）は
上記リサーチレポートに derived data として記録した。
raw レコードの再取得は行わない。

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

## ローカル検証（read-only）

`data/trends.db` は Git 管理外のため CI では検証しない。ローカルでは
以下の読み取り専用コマンドで schema 整合・表の存在・件数を確認する
（DB を作成・変更しない。`record_lineage` の扱いは次節参照）。

```bash
PYTHONPATH=src python3 -m storage.cli verify-trends-db
# 既定 DB: datasets/youtube-consistency/data/trends.db
# 別コピーの検査: python3 -m storage.cli verify-trends-db --db <path>
```

DB が無い checkout では優雅に失敗する（traceback なし、exit 3）:

```text
database not found: datasets/youtube-consistency/data/trends.db (local-only store; ...)
```

DB が有る場合の出力形式（値は環境依存。以下は形式例であり観測値ではない）:

```json
{
  "db": "datasets/youtube-consistency/data/trends.db",
  "read_only": true,
  "tables": {
    "expected": ["run_videos", "runs", "videos"],
    "present": ["run_videos", "runs", "videos"],
    "missing": [],
    "row_counts": {"runs": "<int>", "videos": "<int>", "run_videos": "<int>"}
  },
  "views": {
    "expected": ["v_run_summary", "v_video_appearance"],
    "present": ["v_run_summary", "v_video_appearance"],
    "missing": []
  },
  "lineage": {
    "table": "record_lineage",
    "present": false,
    "row_count": null,
    "status": "deferred_absent"
  },
  "ok": true,
  "problems": []
}
```

exit コード: 0 = 正常（`record_lineage` 不在を含む）/ 1 = 表・ビュー不足 /
3 = DB 不在・非 DB・読み取り不可。テストは合成 DB のみを用い、実 DB を
要求しない（`tests/storage/test_verify_trends_db.py`）。

## `record_lineage` の扱い（決定: 導入見送り）

- **決定**: `record_lineage` テーブルは現時点では導入しない（deferred）。
  `schema.sql` は変更しない。検証コマンドは不在を `deferred_absent` と
  報告し、失敗にしない。
- **理由**:
  1. 空の lineage テーブルを作ると来歴が存在するかのような誤読を招く
     （推測で埋めない方針）。
  2. backfill の材料である Apify クラウド証拠（actor input・run 対応、
     ISS-20261015-PRV-013）が未取得のため、行対応を機械的に埋められない。
  3. raw との対応（run ↔ DB 行）の暫定キーとして
     `runs.apify_dataset_id` と採用宣言の `payload_sha256` を用いる方針は
     決めたが、機械検証はクラウド証拠の取得待ち。
- **将来の migration 形**（クラウド証拠の取得後に schema 変更として実施）:

```sql
CREATE TABLE IF NOT EXISTS record_lineage (
    record_id TEXT NOT NULL,
    source_run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_artifact_id TEXT NOT NULL,
    source_record_id TEXT,
    PRIMARY KEY (record_id, source_run_id, source_artifact_id)
);
```

  形状は `storage.readers.sqlite.SqliteReader.lineage_table` の概念テーブル
  と一致させる。backfill は `runs.apify_dataset_id` ↔ 採用宣言の
  `environment.apify_dataset_id` ↔ `payload_sha256` の突合を原則とし、
  実施時は `schema.sql` の更新として記録する。

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
