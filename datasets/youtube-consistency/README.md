# youtube-consistency — YouTube 検索結果の一貫性・重複分析

YouTube 検索クエリに対する複数回の収集 Run の一貫性（一致率）を検証するデータセット。

- 仕様: `docs/specs/youtube-sqlite-design.md`
- 状態: スキーマ整備済み（データ収集前）

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

ビュー: `v_run_summary`（Run サマリー）, `v_video_appearance`（動画出現履歴）

一致率は保存せず都度計算する（`queries/calculate_rate.sql`, `queries/view_history.sql`）。
仕様書にあった `consistency_metrics` テーブル・`v_consistency_history` ビューは、
誰も投入・メンテナンスしないため削除済み。

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
Step 1: API 実行
        ↓
Step 2: runs に INSERT
        ↓
Step 3: videos に INSERT OR IGNORE
        ↓
Step 4: run_videos に INSERT
        ↓
Step 5: 一致率を計算（queries/calculate_rate.sql / view_history.sql、都度計算）
```
