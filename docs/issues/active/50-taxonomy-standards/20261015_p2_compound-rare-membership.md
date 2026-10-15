# Issue: `compound_rare` の会員が未登録（CBDP / THCP 等）

**ID:** ISS-20261015-TAX-027  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/queries/query-registry.json`, `docs/specs/validation-framework.md` §23.4

## 概要

`compound_rare` カテゴリは「意図的に空」として明記されているが、CBDP / THCP 等の低頻度
化合物は未登録のままで、これらを含む言及を分類できない。

## 確認された観測

- `compound-taxonomy.skos.jsonld` は 6 カテゴリ / 18 化合物 / 24 概念。`compound_rare` は空。
- クエリ registry にも対応する `query_id` は無い（`compound_rare` の化合物）。

## 影響

- 希少化合物の言及が「未分類」に落ち、出現の検知が人手に依存する。

## 対応方針

- 追加可否を判断する（追加する場合は concept ID 体系・IPTC/Wikidata 対応・分類規則のテストを
  同時に用意する）。
- 追加しない場合は「意図的に空」の理由を維持し、その判断を記録する。

## 完了条件

- [ ] 追加可否の判断
- [ ] 登録する場合の概念 ID / 外部対応 / 分類規則テスト
- [ ] 登録しない場合の理由の記録
