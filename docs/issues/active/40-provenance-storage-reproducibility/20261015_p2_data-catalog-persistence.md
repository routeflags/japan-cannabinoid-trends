# Issue: Data Catalog の永続化先が未確定（オンデマンド生成のみ）

**ID:** ISS-20261015-ART-008  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/storage/catalog.py`, `storage.cli catalog`, `docs/specs/validation-framework.md` §17.3

## 概要

Data Catalog は `storage.cli catalog --output` で都度生成するのみで、保存先（例:
`datasets/<study>/metadata/data-catalog.json`）が決まっていない。棚卸し結果がリポジトリの
記録として残らない。

## 確認された観測

- `docs/audits/g4-storage-inventory.json` は監査出力であり、catalog 本体の永続化先は未定。
- `docs/audits/*.json` は鮮度テストの登録対象なので、代用にはできない。

## 影響

- artifact の棚卸しが時点依存で、過去の判断を再現できない。
- study 単位の成果物一覧を publication ときに参照できない。

## 対応方針

- 保存先と形式を決定し、生成器を配線する（既存の catalog 実装を再利用）。
- 既存 raw を変更しない。生成物は派生物として扱う。

## 完了条件

- [ ] 保存先・形式の決定と文書化
- [ ] 生成器の配線とテスト
- [ ] 鮮度検査への登録要否の判断
