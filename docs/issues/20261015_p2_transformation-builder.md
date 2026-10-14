# Issue: `transformation-v1` の生成器が無い（処理成果物の導出が記録されない）

**ID:** ISS-20261015-PRV-010  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
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

- [ ] 生成器の実装とテスト
- [ ] 宣言レジストリとの関係の整理（どちらが正本か）
- [ ] 新規処理成果物 1 件以上で lineage が機械検証される
