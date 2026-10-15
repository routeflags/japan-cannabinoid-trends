# Issue: `transformation-v1` の生成器が無い（処理成果物の導出が記録されない）

**ID:** ISS-20261015-PRV-010
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `src/processing/`, `src/validation/schemas/provenance.py`（`TRANSFORMATION_SCHEMA`）, `docs/specs/validation-framework.md` §18.3

## 概要

`transformation-v1` の schema・lineage 検査・監査配線は済んでいるが、processed / interim を
生成する側が transformation record を出力しない。処理成果物の導出（何から何をどう作ったか）が
契約の形では記録されていない。

## 確認された観測

- `src/processing/reproduce.py` は導出可能 / 再現不能を**宣言**で表し、`audit-processed` が
  それを検査する（2026-10-13 実装）。
- 宣言は導出規則の存在を示すが、`transformation-v1` に準拠した記録は生成されていない。

## 影響

- 処理成果物の lineage を機械的に辿れない（宣言レジストリと実生成の二重管理になり得る）。
- 公開時の「導出が再現可能」の主張が、宣言とコードの対応に依存する。

## 対応方針

- `src/processing/` に `transformation-v1` 準拠の生成器を追加し、成果物生成と同じ経路で
  record を出力する。
- 既存の宣言レジストリ（`DERIVATIONS` / `NON_REPRODUCIBLE`）との重複管理を避ける。
- 既存成果物への遡及生成はしない（新規分から）。

## 完了条件

- [x] 生成器の実装とテスト
- [x] 宣言レジストリとの関係の整理（どちらが正本か）
- [x] 新規処理成果物 1 件以上で lineage が機械検証される

## 解決記録（2026-10-15）

**正本の判断**: `processing.reproduce.DERIVATIONS` / `NON_REPRODUCIBLE` が
導出の正本（何の導出が存在しどう実行されるかの宣言）。生成される
`transformation-v1` record は生成時に添える派生 view であり、第二のレジストリでは
ない。手編集・遡及生成はしない（新規生成分のみ）。施行は従来どおり
`audit-processed` が担う。

**実装内容**:

- 生成器: `src/processing/transformations.py`（`build_transformation_record` =
  registry 1 件の描画、`build_platform_trends_records` = 1 回の
  `build_platform_trends` 実行の描画。既存 `TRANSFORMATION_SCHEMA` と既存
  `check_transformation_lineage` を再利用し、規則の二重実装なし。未登録成果物は
  `KeyError`、構造不正は `ValueError` で fail closed。`executed_at` は必須引数で
  デフォルト時刻を持たないため履歴の遡及捏造ができない）
- 契約テスト: `tests/processing/test_transformations.py`（9 件。全 `DERIVATIONS`
  件の描画・lineage 解決、未登録の拒否、fail closed、決定性、無変異、
  platform-trends 新規実行 5 成果物との lineage 連結）
- 仕様: `docs/specs/validation-framework.md` §18.4 に正本規則と slice を記録。

**証拠**（全て offline。外部 API・raw 変更なし）:

- `PYTHONPATH=src python3 -m pytest tests/processing/test_transformations.py -q` — 9 passed
- `PYTHONPATH=src python3 -m validation.cli audit-issues --format json` — failures=0
- `PYTHONPATH=src python3 -m validation.cli validate-registries --format json` — 全 valid

**残存する owner 側の動作**: 本番 `make platform-trends` 実行時に生成記録を添えて
置く運用にするか（置き場所・追跡可否の方針判断）。添えない間も監査は
`audit-processed` で担保される。
