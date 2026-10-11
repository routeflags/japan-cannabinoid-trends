# x-consistency — X (Twitter) 収集結果の一貫性・日付範囲取得データセット

X 検索クエリに対する複数回の収集 Run を SQLite で管理し、
一貫性検証と日付範囲指定の冪等取得を行うデータセット。

- 対応スクリプト: [`scripts/debug/x_posts_date_range.py`](../../scripts/debug/x_posts_date_range.py)
- 姉妹 dataset: [`datasets/youtube-consistency`](../youtube-consistency/README.md)（同一 `trends.db` 抽象化）

## 構成（非標準構造について）

本 dataset は AGENTS.md 標準構成（`data/ metadata/ analysis/`）ではなく
`data/ queries/ schema/` 構成を採用している。理由は **SQLite を主成果物とする**
operational dataset であり、`metadata/` や `analysis/` に相当する成果物を持たないため。
この構成は `youtube-consistency` と揃えており、意図的なものである。

```
datasets/x-consistency/
├── data/
│   ├── trends.db          # SQLite データベース（Git 管理外、.gitignore で除外）
│   ├── checkpoints/       # Apify 取得のリジューム用チェックポイント（Git 管理外）
│   └── .gitignore         # data/ 配下を一律除外
├── schema/
│   └── schema.sql         # スキーマ定義（runs / posts / run_posts / v_run_summary）
├── queries/               # 一貫性計算用クエリ（必要になったら追加）
└── README.md
```

## 収集方法

**Apify Actor `rBaTEHzveTxZPraGv`（x-posts-search）** を使用し、
検索語 + 日付範囲（`PUBLISHED_AFTER` / `PUBLISHED_BEFORE`）で投稿を取得する。

```bash
python3 scripts/debug/x_posts_date_range.py "CBD リキッド" 2016-01-01 2016-02-01 50
```

- 同一クエリ（検索語 + 日付範囲）はチェックポイントに状態が保存され、
  失敗・中断後は同じコマンドの再実行で続きから再開できる（冪等）
- `--force-new` で最初からやり直す
- 終了コード: 0 = 完了 / 2 = 課金・レート制限等で中断（再実行で再開可能） / 1 = その他エラー

## データベース

SQLite データベース `data/trends.db` を使用（DB 名・抽象化方針は
`youtube-consistency` と共有。ソース種別は `runs.source` カラムで識別）。

`data/` 配下の `.db` ファイルは Git にコミットしない（`.gitignore` で除外）。
再生成可能であり、公開対象は processed データとメタデータのみ。

### テーブル

| テーブル / ビュー | 役割 |
|----------|------|
| `runs` | 収集実行の記録（run_id 単位、Raw データ不変） |
| `posts` | 投稿マスタ（post_id 一意、初回収集情報を保持） |
| `run_posts` | Run と Post の関係 |
| `v_run_summary` | Run サマリービュー |

### 制約

- `runs` / `posts` の既存行は変更しない（Raw データ不変原則）
- 日付は ISO 8601 で統一
- 同一 `run_id` の重複 INSERT は行わない

## 検証

[`scripts/validation/validate-data-schema.sh`](../../scripts/validation/validate-data-schema.sh)
が `runs` / `posts` / `run_posts` のスキーマ整合性を検証する。

## 現状（2026-10-11 時点）

- スキーマ整備済み・小規模データ格納済み（`runs` 4 件 / `posts` 6 件）
- `queries/` は空。一貫性計算クエリは必要になった時点で追加する
