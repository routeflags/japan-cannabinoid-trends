# YouTube dataset export（CSV）の staging 導線 — COL-017 / ART-009 実装と rehearsal

| 項目 | 値 |
|------|-----|
| 日付 | 2026-10-15 |
| 対象 issue | `ISS-20261015-COL-017`（staging ドライバ + `stage` CLI）、`ISS-20261015-ART-009`（CSV reader + artifact schema） |
| 起点 commit | `f425385`（実装はこの上に追加） |
| payload | `~/Downloads/dataset_youtube-scraper_*.csv` 7 件（Apify `youtube-scraper` dataset export、2026-10-14 ダウンロード） |
| 判断 | payload は **CSV のまま**（JSON 再エクスポートしない。メンテナの決定） |
| rehearsal | リポジトリ外の scratch workspace（`/tmp/yt-staging-rehearsal-20261015/`）で stage → adopt → 厳格検証 → `audit-new-runs`。**リポジトリの `datasets/` は未変更** |
| 実採用 | **未実施**（§5 の確認項目が先） |

粒度: この記録は observed / derived / interpretation を区別して書く。

---

## 1. 決定事項と根拠

| # | 決定 | 根拠（証拠） |
|---|------|------|
| D1 | payload は CSV のまま登録する | メンテナの決定。変換規則を別途文書化せず「受け取ったものの保存」を保つ（ART-009 の趣旨） |
| D2 | ART-009 を本作業に含め、`csv-record-reader` + schema `youtube-dataset-csv-v1`（`record_count_mode: data_rows`）を登録 | `sniff_path()` は `.csv` を `csv` と判定するのに registry に reader が無く、S9 `ARTIFACT_READER_UNREGISTERED` で CSV は採用不能だった（観測） |
| D3 | 宣言入力は CLI 引数ではなく **1 つの JSON ファイル**（`staging-declaration-v1`） | run ごとに query 対応・窓・時刻・実行結果・artifact を持つ（7 run で ~15 項目×7）。引数ではレビュー不能。宣言は「どの payload がどの検索か」を人間が明示する唯一の場所 |
| D4 | keyword → `query_id` は宣言。unregistered は exit 2 で拒否 | ドライバは payload の `input` 列を読んで検索を推定しない（実装で不使用、テストで固定）。G2 準拠エントリの追加は別作業 |
| D5 | 窓は「絶対窓 + 相対要求（`date_filter` / `reference_time`）」を宣言し、相対解決の不確かさを `limitations` に記録。compile はしない | YouTube search は `dateFilter`（相対のみ）で絶対日付不可（`.github/skills/apify-youtube-scraper/SKILL.md` 実測記載）。compiler は WIN-002 の範囲。payload 自身は窓を支持しない（`input` 列は検索語のみ） |
| D6 | started_at / finished_at は **export ファイル名の timestamp のみ**を根拠に宣言し、basis を `environment.handover.timestamp_basis` に記録 | 観測: CSV に収集時刻列は無い（`date` は動画の公開時刻。7 件すべて）。ファイル名は `dataset_youtube-scraper_YYYY-MM-DD_HH-MM-SS-mmm.csv`。skill も API 記録（startedAt/finishedAt）と CSV export が別物であることを示す |
| D7 | Apify run ID / dataset ID は payload から記録できない（宣言時は任意項目、無いまま記録） | 観測: CSV に id 列なし。`ISS-20261015-PRV-013` の記載どおり。唯一の候補 `trends.db` は Git 管理外 |
| D8 | 7 件は **rehearsal のみ**（実採用はしない） | 窓・date_filter・実行 status の宣言事実が未確認。無追跡 raw を黙って増やさない（COL-018 の精神）。実採用は宣言値を確認後に 1 コマンド |
| D9 | `stage` Exit code: 0 = 全 run staged / 1 = stopped あり / 2 = 宣言・設定エラー / 3 = 読取不可 | 既存 3 コマンドの番号体系を踏襲。採用判定は `adopt`（producer / verdict 分離 = §3.3） |
| D10 | ドライバは `src/collection/core/staging.py`（プラットフォーム名ゼロ） | P1（コアにソース知识を置かない）。ソース固有情報は宣言ファイルのみ。adapter（COL-016）は不要（`stage_run` は registry から collector を読む） |

## 2. 実装（変更ファイル）

- `src/collection/core/staging.py`（新規）: 宣言の構造検証（Cerberus、`validation.core.validate_document` 経由）→ query registry 照合 → plan / `CollectedArtifact[]` / execution / temporal / environment 組立 → `stage_run`。宣言レベル失敗は何も staging せず、`stage_run` 拒否は run 単位で報告。
- `src/collection/core/cli.py`（追加のみ）: `stage --declaration` サブコマンド + `cmd_stage` / `_emit_stage`。
- `src/storage/readers/csv.py`（新規）: `csv-record-reader`。UTF-8/BOM、CRLF/LF/CR、引用符内改行・カンマ・二重引用符保持、空行は record にしない、ragged / 空列名 / 重複列名は拒否、`count` は CSV record 数。
- `src/storage/readers/__init__.py`: `READER_CLASSES` へ登録。
- `metadata/artifacts/artifact-registry.json`: reader + schema `youtube-dataset-csv-v1`（`raw_records`, `data_rows`）。
- `src/collection/core/provenance.py`: `_temporal_provenance()` のコピー対象に `reference_time` / `limitations` を追加（collector が相対期間を解決した事実を外部 staging 経路でも記録するため。compiler 経路が優先）。
- `src/validation/schemas/artifact_registry.py`: `data_rows` の説明に delimited-text を追記。
- テスト: `tests/storage/test_csv_reader.py`、`tests/collection/test_staging_driver.py`、CLI（`tests/collection/test_collection_cli.py` に stage 5 件）、fixture `tests/storage/fixtures/dataset_export_synthetic.csv`（合成・`README.md` で明示）。
- 仕様: `docs/specs/collection-pipeline.md`（0.4.0、§3.4 新設、§8 exit）、`docs/specs/validation-framework.md`（§10 件数、§17.2/17.3）。

## 3. 実データ rehearsal（観測）

### 3.1 宣言の値（メンテナ確認前の rehearsal placeholder。§5）

観測した CSV record 数は physical line 数ではない（引用符内改行のため約 55 倍差）。

| export ファイル | CSV records | `input`（観測） | 宣言 query_id | run_id（ファイル名 stamp から） |
|---|---:|---|---|---|
| `..._2026-10-10_13-50-24-566.csv` | 24 | CBD リキッド | `cbd-liquid-ja` | `20261010T135024Z-youtube-youtube-consistency` |
| `..._2026-10-10_14-19-47-693.csv` | 224 | HHBD リキッド | `hhbd-liquid-ja` | `20261010T141947Z-youtube-youtube-consistency` |
| `..._2026-10-10_14-34-29-080.csv` | 395 | H4CBH リキッド | `h4cbh-liquid-ja` | `20261010T143429Z-youtube-youtube-consistency` |
| `..._2026-10-10_14-44-21-126.csv` | 456 | CBD リキッド | `cbd-liquid-ja` | `20261010T144421Z-youtube-youtube-consistency` |
| `..._2026-10-10_14-57-27-682.csv` | 468 | CBN リキッド | `cbn-liquid-ja` | `20261010T145727Z-youtube-youtube-consistency` |
| `..._2026-10-10_16-49-15-671.csv` | 352 | CRDH リキッド | `crdh-liquid-ja` | `20261010T164915Z-youtube-youtube-consistency` |
| `..._2026-10-11_19-19-00-950.csv` | 393 | CBD リキッド | `cbd-liquid-ja` | `20261011T191900Z-youtube-youtube-consistency` |

共通宣言: `date_filter: "all"`、`reference_time` = ファイル名 stamp、窓 = `2014-01-01T00:00:00Z` 〜 stamp、`granularity: month` / `timezone: UTC`、`collector_window_type: unbounded`、`exact_window_match: false`、execution `status: success`（basis を environment に記録）。

窓・date_filter の追加根拠（derived）: 7 件中 5 件は「month/week/today/year のいずれの bounded filter とも矛盾する公開日」（2008〜2022 の動画を含む）→ 残る一貫 filter は `all`。残り 2 件（13-50-24、19-19-00）は `all` と矛盾しないが bounded の可能性を排除できない（要確認）。

### 3.2 コマンドと結果

```bash
# 1) 宣言 → staged run（7 件）
.venv/bin/python -m collection.core.cli stage \
  --declaration /tmp/yt-staging-rehearsal-20261015/declaration.json \
  --workspace /tmp/yt-staging-rehearsal-20261015/workspace \
  --datasets-root /tmp/yt-staging-rehearsal-20261015/workspace/datasets \
  --config-dir config --metadata-dir metadata \
  --format json --output /tmp/yt-staging-rehearsal-20261015/stage-report.json
# → exit 0。stage: 7 staged / 0 stopped of 7

# 2) adopt（各 run）
for d in /tmp/yt-staging-rehearsal-20261015/workspace/.staging/*/; do
  .venv/bin/python -m collection.core.cli adopt --staged "$d" \
    --workspace /tmp/yt-staging-rehearsal-20261015/workspace \
    --datasets-root /tmp/yt-staging-rehearsal-20261015/workspace/datasets \
    --config-dir config --metadata-dir metadata
done
# → 7 件すべて ADOPTED（exit 0）。L1 は info の COLLECTOR_LEGACY_REFERENCE のみ
#   （collector status unverified = 意図どおり可視）

# 3) 厳格検証（validate_full, verify_artifacts=True）
#   7/7: valid=True、error/warning 0、payload は ~/Downloads 原本と byte 一致

# 4) audit-new-runs（scratch root を cwd にして実行）
.venv/bin/python -m validation.cli audit-new-runs --datasets-root datasets \
  --config-dir <repo>/config --metadata-dir <repo>/metadata
# → 7 run(s), new=7, failures=0

# 5) リポジトリの audit-new-runs（不変確認）
.venv/bin/python -m validation.cli audit-new-runs
# → 29 run(s), frozen_legacy_seen=29, new=0, failures=0
```

各 run の `run_metadata.json` は query_provenance（registry 照合済み `query_id` / `compound_id` / `intent_id`）、temporal_provenance（絶対窓 + `reference_time` + `limitations`）、`environment.handover`（宣言ファイル名/SHA-256/timestamp basis/record_count basis）を記録する。

### 3.3 追加の観測（derived）

- 456 件 export（14-44-21）は `research/youtube/20261012-...md` §3.3 の Apify run `4sp0DTonaTlGihAfc`（CBD リキッド 456 件）と公開年ヒストグラムが完全一致（2014:1/2015:3/2016:12/2017:13/2018:24/2019:55/2020:27/2021:152/2022:59/2023:31/2024:19/2025:33/2026:27）。**相関は導出**であり、run ID は run メタデータには記録していない（PRV-013: 推測で埋めない）。
- 各 `input` 列の値は宣言 keyword と一致（相関確認）。ドライバはこの列を使っていない。

## 4. 観測 / 派生 / 解釈

- **observed**: ファイル名、CSV record 数、列構成、`input` 列の値、BOM/CRLF、stage/adopt/検証の結果、payload hash。
- **derived**: 窓の `all` 整合性、456 件の run ID 相関、record_count / returned_count（登録 reader による導出）。
- **interpretation**: bounded filter 排除の前提（skill の month 実測（ローリング 30 日）から extrapolate。year/week の実測は未実施）。

注記（検証の強さの区別）: 宣言された `record_count` は L1 が独立に照合する
（`tests/collection/test_staging_driver.py::test_declared_record_count_is_passed_through_and_verified_by_l1`
が誤った宣言値の隔離を固定）。一方、ドライバが導出した count は L1 と同じ
registered reader を使う（数え方の実装は 1 つ、という設計どおり）ため、この経路の
S8 は「宣言値の誤り」の検出ではなく「壊れた payload」の拒否として働く
（reader の解釈は synthetic fixture の契約テストで固定）。

## 5. メンテナへの確認依頼（実採用の前提）

1. 各 export の **actor run ID / dataset ID**（PRV-013 の取得依頼リスト）
2. 各 run の **dateFilter**（特に 13-50-24 と 19-19-00 は bounded の可能性を排除できない）
3. 実行 **status**（SUCCEEDED か）と run の startedAt/finishedAt
4. ファイル名 stamp の**意味と timezone**（run 時刻 / export 時刻、UTC / JST）
5. 実採用の可否: `datasets/youtube-consistency/data/raw/<run-id>/` への配置は方針上無追跡（`config/storage-policies.json` social raw + study `.gitignore` `*`）。COL-018 の「決定先送り中は実 run を catalog しない」を YouTube にも適用するか
6. 宣言の **絶対窓**（研究側観測区間）の確定

## 6. 未検証範囲

- ライブ収集経路（従来から未検証。GT-001 の範囲）。
- `stage` の並行実行・部分書込み復帰（§3.3 の受容限界と同じ）。
- 実 export の **実採用**（本記録は rehearsal のみ。リポジトリ `datasets/` は未変更）。
