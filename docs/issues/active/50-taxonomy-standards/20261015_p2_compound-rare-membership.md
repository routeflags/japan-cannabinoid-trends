# Issue: `compound_rare` のメンバー概念が未登録（CBDP / THCP 等）

**ID:** ISS-20261015-TAX-027  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/queries/query-registry.json`, `docs/specs/validation-framework.md` §23.4

## 概要

`compound_rare` カテゴリは「意図的に空」として明記されているが、CBDP / THCP 等の低頻度
化合物は未登録のままで、これらを含む言及を分類できない。

ここでいう **membership** は「会員登録」ではなく、SKOS taxonomy 上のカテゴリ所属
（`compound_rare` を `skos:broader` に持つ化合物 concept を登録すること）を指す。
つまり未登録なのは人やアカウントではなく、`compound_cbdp` / `compound_thcp` のような
希少カンナビノイド概念と、その `compound_rare` への所属関係である。

## 確認された観測

- `compound-taxonomy.skos.jsonld` は 6 カテゴリ / 18 化合物 / 24 概念。`compound_rare` は空。
- クエリ registry にも対応する `query_id` は無い（`compound_rare` の化合物）。
- `compound_rare` が空であること自体は一貫しているが、CBDP / THCP 等を分類対象に含める
  運用判断をする場合、taxonomy concept・外部 ID 対応・分類規則・query registry のどこまでを
  同時に追加するかを決める必要がある。

## 影響

- 希少化合物の言及が「未分類」に落ち、出現の検知が人手に依存する。
- `compound_rare` をカテゴリとして残していても、メンバー概念が無ければ classifier /
  query design / downstream reporting は具体的な CBDP / THCP 等を参照できない。

## 対応方針

- 追加可否を判断する（追加する場合は concept ID 体系・IPTC/Wikidata 対応・分類規則のテストを
  同時に用意する）。
- 追加しない場合は「意図的に空」の理由を維持し、その判断を記録する。

## 完了条件

- [x] 追加可否の判断（2026-10-15: 追加しない。空のまま維持）
- [ ] 登録する場合の概念 ID / 外部対応 / 分類規則テスト（該当なし。未登録のため）
- [x] 登録しない場合の理由の記録（`docs/provenance/compound-taxonomy.md` TAX-027 節）

## 判断記録（2026-10-15。ステータスは OPEN のまま）

- **判断:** `compound_rare` は空のまま維持する。`compound_cbdp` / `compound_thcp` を追加しない。
- ここでいう membership は SKOS カテゴリ所属（`skos:broader` が `compound_rare` の化合物 concept）であり、
  人やアカウントの会員登録ではない（本文冒頭の注記どおり）。
- **理由（証拠不足）:** CBDP は scopeNote の例示名と本 issue 本文のみ。THCP は COA パネルの ND 記録
  （`docs/data-dictionary.md` §4.1、`docs/provenance.md` §5.3）と汎用リストの言及のみ。
  いずれも収集 run・query-registry・queryDesign・`research/regulatory-status/` 記録が無く、
  追加には日中ラベル・外部 ID（ChEBI / Wikidata）・IPTC 対応の創作が必要になるため見送る。
- **追加の gate:** 収集 run 又は staging 採用による観測＋名称・route 配置の文書化＋
  taxonomy / IPTC（`deliberately_unmapped`）/ data-dictionary §6.4 / query-registry（需要がある場合）/
  provenance 台帳の同時更新。`exactMatch` は検証済み ID がある場合のみ。
- 詳細は `docs/provenance/compound-taxonomy.md` の TAX-027 節、
  固定テストは `tests/validation/test_compound_rare_membership.py` を参照。
- 本 issue は OPEN のまま残す（希少化合物の言及が未分類に落ちる課題自体は未解消のため。閉じない）。
