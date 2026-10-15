# Issue: coverage manifest が永続化されない（オンデマンド評価のみ）

**ID:** ISS-20261015-COV-004  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `src/validation/coverage.py`, `validation.cli coverage-run`, `docs/specs/validation-framework.md` §16.3

## 概要

coverage manifest は `coverage-run` のオンデマンド評価としてしか得られず、run ディレクトリ
に保存されない。評価時点のコードと暗黙の前提に依存した結果が記録として残らない。

## 確認された観測

- `coverage-run` は常に exit 0 のレポート（採用可否のゲートではない）。
- run 側に coverage の派生物は保存されていない（29 legacy run も、今回 staging した GT
  rehearsal run も同様）。

## 影響

- ある時点の「この run は部分的」という判断を後から再現・比較できない。
- 公開時の完全性主張の根拠が、その時実行したコマンド出力に依存する。

## 対応方針

- coverage manifest の保存先と schema ID を決定し、run の派生物として生成する経路を用意する。
- raw へ書き戻さない（`raw` 不変）。既存 run への遡及変換はしない。
- 生成器は既存の評価関数を再利用し、同じ規則を 2 実装しない。

## 完了条件

- [x] 保存先・形式・schema ID の決定と文書化
- [x] 生成器 + 検証テスト
- [x] 遡及変換しない方針の明記

## 実装記録（2026-10-15）

保存先（決定）: `<run-dir>/coverage-manifest.json`（1 run 1 ファイル）。派生
メタデータとして扱い、raw は変更しない。既存 run への遡及生成はしない。仕様は
`docs/specs/validation-framework.md` §10（schema 一覧）・§16.1（決定は変更なし）・
§16.2（実装済みに追加）・§16.3（未実装項目から除外）に記録した。

変更ファイル:

- `src/validation/schemas/coverage.py`（新規）: `COVERAGE_MANIFEST_SCHEMA`
  （`schema_id` / `schema_version` 必須、`run_id` / `window_id` は nullable、
  coverage の interval / state / reason / evidence フィールドと任意 `label_gap_days`）。
  `states` は term 名をキーとする `valuesrules`（term 名はデータであり契約ではない）。
- `src/validation/schema_registry.py`: `coverage-manifest-v1` を登録
 （`SCHEMA_VERSIONS` は 1.0.0。CV-20）。
- `src/validation/contract_ledger.py`: `SCHEMA_SCOPE` に
  `coverage-manifest-v1: (validation, G3)` を宣言（owner = 産出コンテキストは
  validation。`docs/specs/contracts.md` §9 手順どおり）。
- `src/validation/coverage.py`: `evaluate_coverage()` が `schema_id` /
  `schema_version` を付与（既存フィールドは後方互換）。`COVERAGE_MANIFEST_FILENAME` /
  `coverage_manifest_path_for_run()` / `dump_coverage_manifest()`（決定論的
  シリアライザ。`--output` と byte 互換）/ `write_coverage_manifest()`
  （同 dir tmp → `os.replace` の atomic 置換。失敗時は tmp を除去し既存を保持）を
  追加。`coverage-manifest.json` を非 payload（`_NON_PAYLOAD_FILES`）に加え、
  永続化後の再評価を byte-identical にした。併せて `ValueError` 分岐の潜在例外
  （未定義 `reasons` への追加でクラッシュ）を修正し、`coverage["reasons"]` への
  安全な追加に変更（`expected_buckets_undetermined` は欠測証拠であり
  `observed_zero` 化しない）。
- `src/validation/cli.py`: `coverage-run --persist` を追加。`--persist` は
  正規ファイルのみに書き `--output` と排他（併用は exit 2）。対象不在は
  exit 3、書込み失敗は exit 3。`--persist` 無しは従来どおり読取専用。
- `tests/validation/test_schema_coverage.py`: `coverage-manifest-v1` の Contract Test
  を `test_coverage.py` に割当て。
- `tests/validation/test_coverage.py`: 永続化 12 件を追加（schema 適合
  ［synthetic／legacy 2 件／metadata 欠落］、決定論的 dump の byte 一致、
  bucket 化不能 provenance の `expected_buckets_undetermined` 非クラッシュ、
  `--persist` 無しの read-only、`--persist` の正規パス生成・raw 不変・再実行一致、
  metadata ファイル指定、排他違反の exit 2・無書込み、対象不在の exit 3、
  失敗時の tmp 除去）。既存の status／missingness 意味論は不変（既存テスト全件維持）。
- `docs/audits/contract-ledger.json`: 台帳を再生成（28 契約／schema 19。gap 7 は不変）。
- `docs/specs/contracts.md` §8: 契約数を更新。

検証:

- `tests/validation/test_coverage.py` + `test_schema_coverage.py`: 29 passed。
- `validation.cli validate-registries`: 11 ターゲット全 valid。
- `validation.cli audit-issues --format json`: failures=0。
- 注: `.venv` は当環境に存在しないため `PYTHONPATH=src python3`（3.14.6、
  cerberus 1.3.8／pytest 9.1.1）で実行。`make test` 全体は本作業の検証後に実行し記録する。
- `release-archives/`・公開判断・release メタデータ・Zenodo には触れていない。
  実 dataset への永続化（backfill）は未実行。

残務・リスク:

- 永続化 manifest の `target` は呼出し時パスをそのまま記録する（従来の報告互換）。
  相対／絶対の表記差は byte 差になるため、監査引用時は同一呼出し形での再生成一致で確認する。
- 既存 29 run への `coverage-manifest.json` 付与は未実施（方針どおり遡及しない）。
  必要になった run ごとに同コマンドで生成する。
