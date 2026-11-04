# Issue: THCNM を宣言化合物集合に登録したが、化学的同一性は未確認

**ID:** ISS-20261104-TAX-028  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_thcnm`）、
`metadata/taxonomy/iptc-mapping.yaml`、`metadata/queries/query-registry.json`、
`metadata/queries/query-variants.json`、`docs/data-dictionary.md` §6.4、
`docs/provenance/compound-taxonomy.md`、
`datasets/cannabinoid-raw-collection/`（`metadata/query-design.json`・README・methodology）  
**関連:** `ISS-20261024-TAX-014`（HHA / THCNM-CRD の登録可否。THCNM は本 issue で語彙登録まで進めた。HHA は保留のまま）

## 概要

`THCNM`（別名 `THA`）を `compound_thcnm` として taxonomy に登録し、研究設計の
化合物集合（`cannabinoid-raw-collection` の liquid-primary YouTube 設計）に加えた。
**収集は 2026-11-04 に開始した**（Google Trends の 12ヶ月・5年、YouTube の `THCNM リキッド` と `THA リキッド`）。収集は登録文字列に一致するコンテンツを測るもので、物質の同定ではない。

登録は可能な範囲で行い、**化学的同一性は未確認のまま**であることを concept の
`skos:scopeNote`（en / ja）に明記した。本 issue はその未確定部分と解消条件を残す。

## 出所の記載が食い違っている点

| 出所の種類 | 記載 | リポジトリでの扱い |
|---|---|---|
| 国内カンナビス市場記事（2026-10-28、供給元の発言を伝える） | 化学名は `1′-Dimethyl-Δ9-THCH`。`THA` 名で売られた製品の主精神活性成分が `THCNM`。`THA` は定義された単一物質の名称ではなく商業名・混合物名 | `1′-Dimethyl-Δ9-THCH` を altLabel として記録。`THA` は別名・商業名。同一物質の証明には使わない |
| 市場・小売情報（輸入事業者・小売ページ） | `THCNM` = `Tetrahydrocannabinol-N-methyl`。概算分子式 `C22H31NO2`（日本向け処方） | 名称のみ altLabel として記録。分子式は**検証値ではないため値として採らない** |

食い違いの内容:

1. **骨格**: 「THC の N-メチル体」と「THCH のジメチル体」は別の構造を指す。
2. **`THA` の位置づけ**: 商業名（混合物名）なのか、特定構造の別名なのか。
   本 issue は「別名・商業名」までを記録し、**同一物質とも別物質とも断定しない**。
3. **検出可能性**: `ISS-20261024-TAX-014` が記録したとおり、供給元は「THCNM は
   新物質で標準物質の登録が無く、成分検査で検出されないため COA に表示されない」
   と述べている。したがって分析で確認できるのは**そう表示された製品の流通**までで、
   物質そのものの存在ではない。
4. `THAH` は別の独自ブレンドであり、`THA` と綴りが近い。混同しない
   （concept の scopeNote に明記）。

記録しなかったもの: CAS 番号、ChEBI ID、Wikidata ID、PubChem ID、検証済み分子式、
化学クラス（`chemclass_*` への関連）。いずれもこの同一性について確認できていないため、
**推測で補わない**（`AGENTS.md`、CBX / H4CBH / HHBD の前例）。

## 分類（`skos:broader`）の扱い

`compound_semisynthetic`（半合成）に置いた。理由は、2 つの記載のいずれも
「天然カンナビノイドを化学修飾した置換誘導体」を記述しており、
`compound_synthetic` の基準（天然対応物を持たない）に当たらないため。
**恒久的な構造分類ではなく暫定**であり、その旨を scopeNote と
`docs/provenance/compound-taxonomy.md` に書いた。同一性が判明して記載と異なる
構造（例: 天然対応物を持たない新規骨格）であれば再配置が要る。

## 何が解消条件か

次のいずれかが得られた時点で、scopeNote・（必要なら）`skos:broader`・
iptc 対応・台帳を更新して本 issue を RESOLVED にする。

1. 供給元の COA / SDS に**化学名と CAS 番号**の記載がある（`THA` が混合物名なら
   その組成の記載がある）。
2. 標準物質または一次文献により構造が同定され、`THCNM` と `THA` の関係
   （同一 / 別 / 混合物）が決まる。
3. `THCNM` の権威あるレジストリ項目（ChEBI・PubChem・CAS 等）が確認できる。

逆に、`THA` が混合物名であることが確定した場合は、`THA` を化合物概念ではなく
**製品・混合物の呼称**として扱う必要があり、taxonomy の概念設計の見直しになる。

## 現在の状態（2026-11-04）

- taxonomy / iptc / registry / variants / data-dictionary / 台帳 / study 文書の
  同時更新は完了。
- **収集は 2026-11-04 に実施**（Google Trends の 12ヶ月・5年、YouTube の `THCNM リキッド` / `THA リキッド` 各 1 run）。
  `make audit-youtube-coverage` は `compound_thcnm` を 2/2 と報告し、`missing_compounds=0`。X はクエリを設計していないので未収集。
- 配布 slice（`cannabinoid-platform-trends`）には入らない。
- `compound_rare` ではなく半合成カテゴリに属する。`compound_major` / `compound_minor`
  の定義（フィトカンナビノイド）とは前提が異なる。

## 完了条件

- [ ] 上記 1〜3 のいずれかによる同一性の確認、または「未確認のまま追跡を続ける」判断の記録
- [ ] `THA` の位置づけ（別名 / 混合物名）の確定と、それに応じた taxonomy の更新
- [x] 収集を行う場合: 収集条件の宣言、run の採用、coverage 表の更新（2026-11-04。宣言は `metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`、Google Trends は計画書 + 窓）
- [ ] 解消時に scopeNote・台帳・本 issue を同時に更新

## 出所（外部情報）

- 国内カンナビス市場記事（2026-10-28、供給元の発言を伝える）。
- 国内小売・輸入事業者の製品ページ（`THCNM (Tetrahydrocannabinol-N-methyl)`、概算分子式、日本向け処方）。
- `ISS-20261024-TAX-014` に記録した出所（`THCNM-CRD Distillate`、COA 非表示の注記）。

外部ページの URL は本文に貼らない（リンク切れと販売ページの変動を避ける）。
