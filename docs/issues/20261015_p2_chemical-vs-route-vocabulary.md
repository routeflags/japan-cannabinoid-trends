# Issue: 化学クラスと製造経路クラスの 2 語彙が併存している

**ID:** ISS-20261015-TAX-026  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/taxonomy/content-taxonomy.skos.jsonld`, `docs/specs/validation-framework.md` §23.4

## 概要

taxonomy は**製造経路**（半合成・水素化等）で分類しているが、研究文書側には**化学クラス**
（水素化カンナビノイド等）の語彙が併存している。同じ概念が 2 通りのクラスで表現され得る。

## 確認された観測

- `compound-taxonomy.skos.jsonld` の 6 カテゴリは製造経路ベース。
- §23.4 に「化学クラスを taxonomy の第 2 次元として持つか、研究文書側の語彙として残すかは
  未判断」と記載。

## 影響

- 分類結果の再現性・移植性が下がる（同じ化合物が経路によって別クラスになり得る）。
- 外部標準（IPTC / ChEBI / Wikidata）との対応付けの基準が曖昧になる。

## 対応方針

- (a) 化学クラスを taxonomy の第 2 次元として持つ、(b) 研究文書側の語彙に寄せる、の選択。
- 判断後、SKOS の構造と `iptc-mapping.yaml` の対応を整合させる。
- 既存の分類済みデータへの影響を確認する。

## 完了条件

- [ ] 判断と理由の記録
- [ ] taxonomy / mapping の更新と整合テスト
- [ ] 既存分類データへの影響確認
