# Issue: IPTC Media Topics 未対応の 17 概念

**ID:** ISS-20261015-TAX-025  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/iptc-mapping.yaml`, `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/taxonomy/content-taxonomy.skos.jsonld`, `docs/specs/validation-framework.md` §23.4

## 概要

IPTC Media Topics への対応付けが未完了の末端概念が 17 件ある（化合物 9 / intent 4 / format 4）。
現状は `iptc-mapping.yaml` の `coverage` 宣言で `deliberately_unmapped` / `not_applicable`
として明示され、全概念を被覆している。

## 確認された観測

- 2026-10-13 に `coverage` 宣言（mapped / deliberately_unmapped / not_applicable）を追加し、
  全概念が分類されていることを機械検証可能にした。
- 「対応可能だが未対応」と「IPTC 語彙上対応が無い」の区別は、判断待ちのまま。

## 影響

- 外部標準との対応表が不完全なのか、完了なのかを第三者が判定できない。

## 対応方針

- IPTC 語彙を確認したうえで、各概念の対応可否を判断する。
- **推測で対応付けない**（対応不可ならその理由を `coverage` の区分で示す）。

## 完了条件

- [ ] IPTC 語彙の確認記録
- [ ] 対応可能概念の追加とテスト更新
- [ ] 対応不可概念の理由の記録
