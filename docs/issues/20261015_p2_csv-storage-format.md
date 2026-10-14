# Issue: CSV 形式の storage reader と artifact schema が未登録

**ID:** ISS-20261015-ART-009  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `metadata/artifacts/artifact-registry.json`, `src/storage/readers/`, `src/storage/sniff.py`, `src/validation/storage_contract.py`

## 概要

外部 collector がクラウドからダウンロードした CSV（例: Apify dataset のエクスポート）を
raw payload として保全したい場合、L1 の storage contract が
`ARTIFACT_READER_UNREGISTERED`（S9）で隔離する。`storage/sniff.py` は拡張子 `.csv` を
`csv` と判定するが、format `csv` をカバーする reader と `record_count_mode` が registry に
無いため、宣言できる schema が存在しない。

## 確認された観測

- `metadata/artifacts/artifact-registry.json` の `readers` は json / sqlite のみ
  （`formats: ["csv"]` を持つ reader は 0 件）。
- `sniff_path()` は `.csv` に対して `SniffResult("csv", "partial")` を返す。
  `_format_matches()` は `csv` を「比較しない形式」に含めないため、宣言 format は `csv` で
  なければ S6（`ARTIFACT_FORMAT_MISMATCH`）になる。
- このため 2026-10-15 時点で、CSV をそのまま raw にする経路は存在しない。

## 影響

- CSV でしか保持していない収集結果を、現行契約の raw として採用できない。
- JSON へ変換して保存すると、それは「受け取ったものと同一の保全」ではなくなる
  （変換規則を別途文書化する必要がある）。

## 対応方針

- `src/storage/readers/` に CSV reader を実装し、`READER_CLASSES` に登録する
  （手順は同パッケージ `__init__.py` の docstring）。
- `artifact-registry.json` に reader + artifact schema（例 `<source>-dataset-csv-v1`、
  `record_count_mode: data_rows`）を追加する。
- ヘッダ行とデータ行の境界、BOM、空行の扱いをテストで固定する。

## 完了条件

- [x] CSV reader の実装と契約テスト（`tests/storage/`）
- [x] registry 登録（reader / schema）と `validate-registries` の green 維持
- [x] 実 CSV を L1 に通した検収（storage contract の S6-S9 が error 0）

## 対応記録（2026-10-15）

- 実装: `src/storage/readers/csv.py`（`csv-record-reader`、read mode
  `records`）。UTF-8（BOM 許容）/ CRLF・LF・CR、引用符内改行・カンマ・二重引用符
  を保持、空行は record にしない、ragged・空列名・重複列名は拒否。`count` は
  physical line ではなく **CSV record 数**（実 export は引用符内改行のため
  約 55 倍差 — `dataset_youtube-scraper_*.csv` の実測で確認）。
- 登録: `metadata/artifacts/artifact-registry.json` に reader と schema
  `youtube-dataset-csv-v1`（`format: csv`, `artifact_types: [raw_records]`,
  `record_count_mode: data_rows`）。`validate-registries` は 11 target valid
  （維持）。
- 契約テスト: `tests/storage/test_csv_reader.py`（synthetic fixture。
  `tests/storage/fixtures/dataset_export_synthetic.csv` は `synthetic-*` /
  `example.invalid` のみで、実メタデータを持たない）。S6 / S8 / S9 が
  非空虚（format 不一致・件数不一致・未登録 schema をそれぞれ検出）であることも
  テストで固定。
- 実 CSV の検収: 実 export 7 件（`~/Downloads/dataset_youtube-scraper_*.csv`）を
  リポジトリ外 scratch workspace で stage → adopt → `validate_full
  (verify_artifacts=True)` 厳格 valid（S6-S9 含め error 0）。記録:
  `docs/reports/20261015b-youtube-csv-staging-driver.md`。
