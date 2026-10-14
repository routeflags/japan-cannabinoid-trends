# Issue: Provenance Graph（グラフ化 / PROV-O 変換）が未実装

**ID:** ISS-20261015-PRV-012  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/storage/lineage.py`, `docs/specs/validation-framework.md` §18.3

## 概要

lineage 辺（run → artifact → transformation）は JSON の参照としてのみ表現されている。
グラフ DB・PROV-O 変換は未実装（仕様上も初期は JSON で足りるという判断）。

## 確認された観測

- manifest の `derived_from` と lineage 検査（`check_manifest_lineage`）は存在する。
- legacy 29 run は manifest が無く `lineage: unknown` として明示される。

## 影響

- 横断的な系譜の問い合わせ（どの研究が同じ raw に依存しているか等）が手作業になる。

## 対応方針

- 外部標準（PROV-O）への変換が必要になった時点で実装する。不要と判断するなら、その判断をここに記録して issue を閉じる。

## 完了条件

- [ ] グラフ化の要否判断の記録
- [ ] 実装する場合は JSON lineage → グラフ / PROV-O の変換と検証
