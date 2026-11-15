# Query Inventory（クエリ証拠台帳）

**版:** 1.7.6（2026-11-11）
**目的:** G2 垂直スライスで `metadata/queries/` に登録したクエリ・表記ゆれ・除外
規則の**証拠台帳**（G1 §18 Phase 1 の collector-inventory.md のクエリ版）。登録は
「実 run の記録」または「既存 keywords.yaml / taxonomy」に基づき、推測の語彙は
書かない（b.md P5）。

---

## 1. 登録済みクエリ（`query-registry.json` の化合物語 76 件。`other` intent の比較セットは本表に含めない）

compound_id は compound-taxonomy の `skos:notation`（例 `compound_cbx`）。

| query_id | compound | intent | canonical_text | status | 証拠 |
|---|---|---|---|---|---|
| `cbx-general-ja` | `compound_cbx` | compound_general | CBX | active | 3 run（20261001T115959Z / 20261001T121949Z / variance_check の terms）/ keywords.yaml keywords |
| `cbx-liquid-ja` | `compound_cbx` | product_liquid | CBX リキッド | active | 6 run（20261001T115959Z / 20261001T121949Z / variance_check / 20261012T055259Z / 060517Z / 061614Z）/ keywords.yaml（x_twitter・youtube primary） |
| `cbx-cannabinoid-ja` | `compound_cbx` | compound_general | CBX カンナビノイド | active | disambiguated_queries run / keywords.yaml discriminating_queries |
| `cbx-cannabis-ja` | `compound_cbx` | compound_general | CBX 大麻 | active | disambiguated_queries run / keywords.yaml discriminating_queries |
| `cbd-general-ja` | `compound_cbd` | compound_general | CBD | active | 2 run（20261002T063821Z / comparison-setA） |
| `cbd-liquid-ja` | `compound_cbd` | product_liquid | CBD リキッド | active | 7 run（20261001T115959Z / variance_check / 20261012T054920Z / 055259Z / 060517Z / 061614Z / 064246Z） |
| `cbd-oil-ja` | `compound_cbd` | product_oil | CBD オイル | active | 20261012T054920Z（notation-presurvey の比較）/ keywords.yaml keywords |
| `hhc-general-ja` | `compound_hhc` | compound_general | HHC | active | 20261002T064008Z |
| `hhc-liquid-ja` | `compound_hhc` | product_liquid | HHC リキッド | active | 20261012T055259Z / 060517Z / 064246Z |
| `hhch-general-ja` | `compound_hhch` | compound_general | HHCH | active | 20261002T094657Z / 094730Z |
| `hhch-liquid-ja` | `compound_hhch` | product_liquid | HHCH リキッド | active | 20261012T061614Z |
| `thch-general-ja` | `compound_thch` | compound_general | THCH | active | 20261002T064118Z |
| `thch-liquid-ja` | `compound_thch` | product_liquid | THCH リキッド | active | 20261012T061614Z |
| `thc-o-general-ja` | `compound_thc_o` | compound_general | THC-O | active | 20261002T071255Z |
| `thc-o-liquid-ja` | `compound_thc_o` | product_liquid | THC-O リキッド | active | 20261012T061614Z |
| `crdp-general-ja` | `compound_crdp` | compound_general | CRDP | active | 20261002T085022Z / 085359Z |
| `crdp-liquid-ja` | `compound_crdp` | product_liquid | CRDP リキッド | active | 20261012T061614Z |
| `thc-general-ja` | `compound_thc` | compound_general | THC | active | 3 run（20261002T063852Z / comparison-setA 20261002T064236Z / 5y-baseline 20261008T093228Z） |
| `thc-liquid-ja` | `compound_thc` | product_liquid | THC リキッド | active | 3 run（20261012T055259Z / 060517Z / 064246Z） |
| `cbg-general-ja` | `compound_cbg` | compound_general | CBG | active | 3 run（20261002T063924Z / comparison-setA 20261002T064236Z / 5y-baseline 20261008T093228Z）/ keywords.yaml keywords |
| `cbg-liquid-ja` | `compound_cbg` | product_liquid | CBG リキッド | active | 3 run（20261012T055259Z / 060517Z / 064246Z） |
| `cbn-general-ja` | `compound_cbn` | compound_general | CBN | active | 2 run（20261002T081839Z / 082000Z） |
| `cbn-liquid-ja` | `compound_cbn` | product_liquid | CBN リキッド | active | 3 run（20261012T055259Z / 060517Z / 064246Z） |
| `crdh-general-ja` | `compound_crdh` | compound_general | CRDH | active | 2 run（20261008T121338Z / common-scale-missing-20261009）/ keywords.yaml keywords |
| `crdh-liquid-ja` | `compound_crdh` | product_liquid | CRDH リキッド | active | 20261012T061614Z / keywords.yaml keywords |
| `h4cbh-general-ja` | `compound_h4cbh` | compound_general | H4CBH | active | 4 run（20261002T080652Z / common-scale-missing-20261009 / 20261001T121949Z / variance_check）/ keywords.yaml keywords |
| `h4cbh-liquid-ja` | `compound_h4cbh` | product_liquid | H4CBH リキッド | active | 20261012T061614Z / keywords.yaml keywords |
| `hhbd-general-ja` | `compound_hhbd` | compound_general | HHBD | active | 4 run（20261002T080800Z / common-scale-missing-20261009 / 20261001T121949Z / variance_check）/ keywords.yaml keywords |
| `hhbd-liquid-ja` | `compound_hhbd` | product_liquid | HHBD リキッド | active | 20261012T061614Z / keywords.yaml keywords |
| `thcv-general-ja` | `compound_thcv` | compound_general | THCV | active | 20261008T093228Z（5y-baseline） |
| `thcv-liquid-ja` | `compound_thcv` | product_liquid | THCV リキッド | active | 20261012T061614Z |
| `thcnm-general-ja` | `compound_thcnm` | compound_general | THCNM | active | Google Trends の 12ヶ月・5年（`20261104T115425Z-google-trends-thcnm-12m` / `20261104T115431Z-google-trends-thcnm-5y`）。taxonomy 概念 `compound_thcnm`（`THA` は別名・商業名。ISS-20261104-TAX-028） |
| `thcnm-liquid-ja` | `compound_thcnm` | product_liquid | THCNM リキッド | active | YouTube 1 run（`20261104T120627Z-youtube-cannabinoid-raw-collection`、30 件。2026-11-04）。`datasets/cannabinoid-raw-collection/metadata/query-design.json` の required primary query |
| `tha-liquid-ja` | `compound_thcnm` | product_liquid | THA リキッド | active | YouTube 1 run（`20261104T120805Z-youtube-cannabinoid-raw-collection`、311 件。2026-11-04）。`THA` は `compound_thcnm` の別名・商業名（ISS-20261104-TAX-028）であり、別化合物の集合ではない。同じ化合物の 2 本目の required primary query |
| `cbc-general-ja` | `compound_cbc` | compound_general | CBC | active | 登録根拠: taxonomy の既存概念 `compound_cbc`（`compound_minor`、`chebi:3357` / `wikidata:Q410949`）を根拠に 2026-11-10 に登録（ISS-20261110-TAX-039）。**run 実績は登録根拠ではない** |
| `cbc-liquid-ja` | `compound_cbc` | product_liquid | CBC リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `cbdv-general-ja` | `compound_cbdv` | compound_general | CBDV | active | 登録根拠: taxonomy の既存概念 `compound_cbdv`（`compound_minor`、`wikidata:Q1104117`）を根拠に 2026-11-10 に登録（ISS-20261110-TAX-039）。**run 実績は登録根拠ではない** |
| `cbdv-liquid-ja` | `compound_cbdv` | product_liquid | CBDV リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thcb-general-ja` | `compound_thcb` | compound_general | THCB | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thcb`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `thcb-liquid-ja` | `compound_thcb` | product_liquid | THCB リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thcp-general-ja` | `compound_thcp` | compound_general | THCP | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thcp` を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。2026-11-11 に owner が意図された範囲を tetrahydrocannabiphorol（C7）同族体ファミリー（Δ8/Δ9 未指定）と確認したが、単一物質の同定ではない（同 issue 追記）。**run 実績は登録根拠ではない** |
| `thcp-liquid-ja` | `compound_thcp` | product_liquid | THCP リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thcjd-general-ja` | `compound_thcjd` | compound_general | THCJD | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thcjd` を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。2026-11-11 に owner が意図された範囲を THC-JD / 3-octyl-THC（C8）同族体ファミリー（Δ8/Δ9 未指定）と確認したが、単一物質の同定ではない（同 issue 追記）。**run 実績は登録根拠ではない** |
| `thcjd-liquid-ja` | `compound_thcjd` | product_liquid | THCJD リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thcpo-general-ja` | `compound_thcpo` | compound_general | THCPO | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thcpo` を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。2026-11-11 に owner は確認質問「`THCPO` は THCP-O-acetate を指しますか？」に `y` と回答し、異性体を名指ししなかったため、登録を異性体未指定の THCP-O-acetate ファミリーとして扱う（単一物質の同定ではない。ファミリー扱いは回答の登録上の整理）。英語 `skos:altLabel` `THCP-O-acetate` は概念の scopeNote に根拠を記録した検索スコープの別名で、カテゴリ所属が同義を確立するものではない。両異性体が 2024 年の厚生労働省令の構造グループに該当することは、省令の「麻薬を除く」除外規定の下での法令上の構造の事実として台帳に記録した。**run 実績は登録根拠ではない** |
| `thcpo-liquid-ja` | `compound_thcpo` | product_liquid | THCPO リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は `THCPO リキッド` の文字列一致を測る |
| `cbe-general-ja` | `compound_cbe` | compound_general | CBE | active | 登録根拠: 2026-11-11 の owner 指示で `compound_cbe` を登録（ISS-20261111-TAX-040）。同日 owner が `CBE` を cannabielsoin と確認し、taxonomy は `compound_minor`・Wikidata Q22668702 / UNII 2ERD6V6652 へ更新。**run 実績は登録根拠ではなく、系列は `CBE` の文字列一致を測る** |
| `cbe-liquid-ja` | `compound_cbe` | product_liquid | CBE リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は `CBE リキッド` の文字列一致を測る |
| `hhcpo-general-ja` | `compound_hhcpo` | compound_general | HHCPO | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_hhcpo`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `hhcpo-liquid-ja` | `compound_hhcpo` | product_liquid | HHCPO リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `cbnd-general-ja` | `compound_cbnd` | compound_general | CBND | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_cbnd`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `cbnd-liquid-ja` | `compound_cbnd` | product_liquid | CBND リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `cbl-general-ja` | `compound_cbl` | compound_general | CBL | active | 登録根拠: 2026-11-11 の owner 指示で `compound_cbl` を登録（ISS-20261111-TAX-040）。同日 owner が `CBL` を cannabicyclol と確認し、taxonomy は `compound_minor`・Wikidata Q907909 へ更新（CAS 21366-63-2 / 67920-00-7 は立体化学の扱いが異なるため単一 CAS を断定しない）。**run 実績は登録根拠ではなく、系列は `CBL` の文字列一致を測る** |
| `cbl-liquid-ja` | `compound_cbl` | product_liquid | CBL リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `cbga-general-ja` | `compound_cbga` | compound_general | CBGa | active | 登録根拠: 2026-11-11 の owner 指示で `compound_cbga` を登録（ISS-20261111-TAX-040）。同日 owner が `CBGa` を cannabigerolic acid（標準表記 CBGA）と確認し、taxonomy は `compound_minor`・ChEBI 67081 / Wikidata Q27135612 / UNII 80I4ZM847Y へ更新。**run 実績は登録根拠ではなく、系列は `CBGa` の文字列一致を測る** |
| `cbga-liquid-ja` | `compound_cbga` | product_liquid | CBGa リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `cbp-general-ja` | `compound_cbp` | compound_general | CBP | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_cbp`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `cbp-liquid-ja` | `compound_cbp` | product_liquid | CBP リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `10-oh-hhc-general-ja` | `compound_10_oh_hhc` | compound_general | 10-OH-HHC | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_10_oh_hhc`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `10-oh-hhc-liquid-ja` | `compound_10_oh_hhc` | product_liquid | 10-OH-HHC リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thxe-general-ja` | `compound_thxe` | compound_general | THXE | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thxe`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `thxe-liquid-ja` | `compound_thxe` | product_liquid | THXE リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `thca-general-ja` | `compound_thca` | compound_general | THCA | active | 登録根拠: 管理カテゴリ `compound_identity_unverified` の新規概念 `compound_thca`（化学的同一性未確認）を根拠に 2026-11-11 に登録（ISS-20261111-TAX-040）。**run 実績は登録根拠ではない** |
| `thca-liquid-ja` | `compound_thca` | product_liquid | THCA リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない） |
| `delta9-thca-a-general-ja` | `compound_delta9_thca_a` | compound_general | Δ9-THCA-A | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。Moreno-Sanz 2016（DOI 10.1089/can.2016.0008）と Filer 2021（DOI 10.1089/can.2021.0003、PMCID PMC8612408）が Δ9-THCA-A / THCA-B の名称・構造上の区別を記録するが、登録文字列の単一外部レコードは未選択。**run 実績は登録根拠ではない** |
| `delta9-thca-a-liquid-ja` | `compound_delta9_thca_a` | product_liquid | Δ9-THCA-A リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「Δ9-THCA-A リキッド」の文字列一致を測る |
| `thca-b-general-ja` | `compound_thca_b` | compound_general | THCA-B | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。Filer 2021（DOI 10.1089/can.2021.0003、PMCID PMC8612408）が THCA-B を THCA-A の構造異性体として記録し、Moreno-Sanz 2016（DOI 10.1089/can.2016.0008）が 4-carboxy-THC とするが、登録文字列の単一外部レコードは未選択。**run 実績は登録根拠ではない** |
| `thca-b-liquid-ja` | `compound_thca_b` | product_liquid | THCA-B リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「THCA-B リキッド」の文字列一致を測る |
| `delta8-thca-general-ja` | `compound_delta8_thca` | compound_general | Δ8-THCA | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。構造・命名の出所は本変更で未検証（A/B のカルボキシル配置は Δ9 系列の文献に基づく記載であり、Δ8 へ推測で拡張しない）。**run 実績は登録根拠ではない** |
| `delta8-thca-liquid-ja` | `compound_delta8_thca` | product_liquid | Δ8-THCA リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「Δ8-THCA リキッド」の文字列一致を測る |
| `delta8-thcb-general-ja` | `compound_delta8_thcb` | compound_general | Δ8-THCB | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。Tanaka & Kikura-Hanajiri 2024（DOI 10.1248/yakushi.24-00029）が Δ9-THCB と別個に同定し、Linciano et al. 2020（DOI 10.1021/acs.jnatprod.9b00876）は Δ9 体を記録する。登録文字列の単一外部レコードは未選択。**run 実績は登録根拠ではない** |
| `delta8-thcb-liquid-ja` | `compound_delta8_thcb` | product_liquid | Δ8-THCB リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「Δ8-THCB リキッド」の文字列一致を測る |
| `delta9-thcb-general-ja` | `compound_delta9_thcb` | compound_general | Δ9-THCB | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。Linciano et al. 2020（DOI 10.1021/acs.jnatprod.9b00876）が単離・構造確認し、Tanaka & Kikura-Hanajiri 2024（DOI 10.1248/yakushi.24-00029）が Δ8 体と別個に同定する。登録文字列の単一外部レコードは未選択。**run 実績は登録根拠ではない** |
| `delta9-thcb-liquid-ja` | `compound_delta9_thcb` | product_liquid | Δ9-THCB リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「Δ9-THCB リキッド」の文字列一致を測る |
| `thcb-o-acetate-general-ja` | `compound_thcb_o_acetate` | compound_general | THCB-O-acetate | active | 登録根拠: 2026-11-11 の owner 確認（ISS-20261111-TAX-041）による `compound_identity_unverified` の新規概念。厚生労働省 令和6年厚生労働省令第81号の別紙が Δ9-THCB-O-acetate（n=4）と Δ8-THCB-O-acetate（n=4）を列挙するが、登録語は異性体未指定であり単一物質・単一レコードを指さない。**run 実績は登録根拠ではない** |
| `thcb-o-acetate-liquid-ja` | `compound_thcb_o_acetate` | product_liquid | THCB-O-acetate リキッド | active | 登録根拠: 同上（`product_liquid` の required primary query 設計。run 実績ではない）。系列は「THCB-O-acetate リキッド」の文字列一致を測る |

**追加 15 語（CBC・CBDV と 2026-11-11 の 13 語）の 30 行は登録根拠の記録である。** 登録時点では run 0（未収集）で、0 観測でも欠測でもない。**現在の run 結果はこの表ではなく、`datasets/cannabinoid-raw-collection/README.md`・`methodology.md`、`metadata/data-catalog.json`、`make audit-youtube-coverage` を正本とする。**

注（2026-10-13 追加分）: `HHC` / `HHCH` / `THCH` / `THC-O` / `CRDP` の 5 化合物は taxonomy に概念が無かったため登録
できずにいたものが、`compound_hhc` / `compound_hhch` / `compound_thch` / `compound_thc_o` /
`compound_crdp` の追加により可能になった。登録した文字列は**実 run に記録されたもの**
のみ（`docs/audits/g2-query-inventory.json` で再計算一致を強制）。表記ゆれ（空白なし形）
は実収集に証拠がないため `query-variants.json` には追加していない。

注: 判別クエリ（`CBX 大麻` / `CBX カンナビノイド`）の intent は compound_general
（検索意図は CBX という成分の理解であり、判別語による修飾は platform 構文ではなく
表記の一部）。

## 2. 表記ゆれ（`query-variants.json`、8 sets）

| query_id | variant_id | text | status | 証拠 |
|---|---|---|---|---|
| `cbd-general-ja` | cbd-general-primary | CBD | primary | registry canonical と一致（機械検証） |
| `cbd-general-ja` | cbd-general-en | Cannabidiol | alternative | taxonomy prefLabel（en）/ b.md §9.2 |
| `cbd-general-ja` | cbd-general-kana | カンナビジオール | alternative | taxonomy altLabel（ja） |
| `cbd-liquid-ja` | cbd-liquid-primary | CBD リキッド | primary | registry canonical と一致（機械検証） |
| `cbd-liquid-ja` | cbd-liquid-nospace | CBDリキッド | alternative | 20261012T054920Z（notation-presurvey が両表記を比較） |
| `cbx-liquid-ja` | cbx-liquid-primary | CBX リキッド | primary | registry canonical と一致（機械検証） |
| `cbx-liquid-ja` | cbx-liquid-nospace | CBXリキッド | alternative | keywords.yaml search_queries.tiktok.primary.keyword |
| `thcnm-general-ja` | thcnm-general-primary | THCNM | primary | registry canonical と一致（機械検証） |
| `thcnm-general-ja` | thcnm-general-tha-commercial-alias | THA | alternative | 市場の別名・商業名（taxonomy altLabel / ISS-20261104-TAX-028）。**別物質の証拠ではない** |
| `thcnm-liquid-ja` | thcnm-liquid-primary | THCNM リキッド | primary | registry canonical と一致（機械検証） |
| `thcnm-liquid-ja` | thcnm-liquid-nospace | THCNMリキッド | alternative | 空白のみの差。収集証拠なし（`THCNM リキッド` で収集しており、こちらは未照会） |
| `tha-liquid-ja` | tha-liquid-primary | THA リキッド | primary | registry canonical と一致（機械検証） |
| `tha-liquid-ja` | tha-liquid-nospace | THAリキッド | alternative | 空白のみの差。収集証拠なし（`THA リキッド` で収集しており、こちらは未照会） |
| `thc-o-general-ja` | thc-o-general-primary | THC-O | primary | registry canonical と一致（機械検証） |
| `thc-o-general-ja` | thc-o-general-no-hyphen | THCO | alternative | compound-taxonomy の altLabel（en）`THCO` / PubMed 37466480（tetrahydrocannabinol-O-acetate の口語名としての `THCO`）/ PubChem CID 198013（別名 `THC-O-ACETATE`）/ owner 決定（2026-11-04）。2026-11-04 の run `20261104T135330Z-google-trends-thc-o-general-thco-12m` / `20261104T135339Z-google-trends-thc-o-general-thco-5y` がこの文字列を送信（`query_provenance.submitted_query`） |
| `thc-o-liquid-ja` | thc-o-liquid-primary | THC-O リキッド | primary | registry canonical と一致（機械検証） |
| `thc-o-liquid-ja` | thc-o-liquid-no-hyphen | THCO リキッド | alternative | 登録済み製品語 `THC-O リキッド` の化合物トークンをハイフンなし表記にしたもの（owner 決定、2026-11-04）。表記の根拠は `thc-o-general-ja` の `THCO` と同じ（PubMed 37466480 / PubChem CID 198013）。2026-11-04 の run `20261104T135345Z-google-trends-thc-o-liquid-thco-12m` / `20261104T135350Z-google-trends-thc-o-liquid-thco-5y` が送信 |

THC-O の 2 つの variant は **canonical の query_id を変えない**。収集は
`query_id` = `thc-o-general-ja` / `thc-o-liquid-ja` のまま、送信語だけを variant に
する（run_metadata では `query_provenance.submitted_query` が variant 文字列）。
1 variant × 1 timeframe を 1 run とし、異なる表記の系列を合算・置換しない。
登録は「同じ意味を意図する表記候補」であり、**検索結果の同等性を主張しない**
（実測値は別々の run に残る）。

**`THCO` の証拠と同一性の留保（2026-11-04）**: `THCO` を `THC-O`（= `THC-O-acetate`）の表記ゆれとして扱う根拠は、
PubMed 37466480 が tetrahydrocannabinol-O-acetate の口語名として `THCO` を記録していること、
PubChem CID 198013 が Tetrahydrocannabinol acetate（別名 `THC-O-ACETATE`、CAS 23132-17-4、`C23H32O3`）の
レコードであること、PubMed 37381980 / 36508081 が `THC-O-Acetate` 表記を用いることである
（証拠 ID は `metadata/provenance/evidence-registry.json`）。一方、`THCO` は Δ8-THCO / Δ9-THCO
（tetrahydrocannabiorcol、CAS 22972-64-1 / 22972-65-2、`C17H22O2`、Cayman Chemical 33762 / 33763）
にも使われる**別物質の表記**であり、`THCO` は単一の CAS にも単一の構造にも対応しない。
したがってこの登録は「同じ意味を意図する検索文字列」の対応であり、物質の同定ではない。
canonical の `THC-O` の 12ヶ月 NO_DATA・5年系列は不変で、variant の観測値を合算・置換しない
（ISS-20261104-TAX-029、`docs/provenance/compound-taxonomy.md`）。

大文字小文字・全角/半角の差は variant として登録しない（正規化 NFKC + casefold で
吸収。b.md §5.3「表記が似ているだけで等価とは限らない」に従い、正規化後に同一に
なる variant は validate-registries が拒否する）。variant は同じ意味を意図する
表記候補であり、検索結果の同等性は保証しない。

## 3. 除外規則（Stage 1、rationale / evidence 付き）

| rule_id | phrase | 分類 | 根拠 |
|---|---|---|---|
| `non-compound-durban-cbd` | durban cbd | irrelevant | docs/collection-gap-analysis.md（原因 G2 行）/ b.md §8.3 |
| `non-compound-central-business-district` | central business district | irrelevant | b.md §8（CBD の多義図: Cannabidiol / Central Business District） |

- 除外はフレーズ単位・テキスト単位で行い、収集セット全体を単語 1 つで棄却しない
  （b.md §8.3）。
- registry に登録された文字列が除外規則に一致した場合は自己矛盾として
  validate-registries が拒否する（`QUERY_TEXT_EXCLUDED`）。

## 4. 範囲の線引きと限界

- 登録範囲は「compound-taxonomy に概念があり、実 run の記録または keywords.yaml
  に実在する」ものを基本とする（J3。例外は本节末尾に列挙する）。2026-10-13 の G2 増分で THC / CBG / CBN / CRDH /
  H4CBH / HHBD / THCV の 14 クエリを追加し、29 run に記録された化合物トークンは
  全て登録済みとなった（`docs/audits/g2-query-inventory.json` で再計算一致を強制。
  `ambiguous` 32 → 0、`exact_match` 41 → 73 はその正当な帰結）。未登録のまま自動採用
  しない（状態 `unmapped` / `ambiguous` / `semantic_match_candidate`）。
- 残る `semantic_match_candidate` 1 件（`THC-Oリキッド`）は空白なし表記の候補であり、
  variant への自動昇格はしない（人手レビューが必要）。登録 36 化合物はすべて notation を持つ
  （THCNM・CBC・CBDV・2026-11-11 の 13 語を含む）。CBC・CBDV は概念だけが既存で、query は 2026-11-10 に
  登録した（**登録時点で run なし**。現在の run 結果は study README / methodology / catalog /
  `make audit-youtube-coverage` を正本とする）。
- `thcnm-general-ja` / `thcnm-liquid-ja` / `tha-liquid-ja` は**実 run と keywords.yaml のいずれも根拠にせず**登録し、後に収集で実測した語である。
- `cbc-general-ja` / `cbc-liquid-ja` / `cbdv-general-ja` / `cbdv-liquid-ja`（2026-11-10、
  ISS-20261110-TAX-039）は**実 run を根拠にしない**登録である。根拠は taxonomy の既存概念
  （`compound_cbc` / `compound_cbdv`）と owner の対象拡張依頼であり、**登録時点では run 0** だった。
  登録時点の未収集を 0 観測とも欠測とも書かない。**現在の run 結果は
  `datasets/cannabinoid-raw-collection/README.md`・`methodology.md`、
  `metadata/data-catalog.json`、`make audit-youtube-coverage` を正本とする。**
- 2026-11-11 の 26 query（13 語 × `compound_general` / `product_liquid`。
  ISS-20261111-TAX-040）も**実 run を根拠にしない**登録である。根拠は owner の列挙と、
  管理カテゴリ `compound_identity_unverified` に追加した taxonomy 概念である。
  `CBE` は同日 owner が cannabielsoin と確認し、`compound_minor` へ移した
  （FDA GSRS UNII 2ERD6V6652 / CAS 52025-76-0、Wikidata Q22668702）。`CBL` も
  同日 cannabicyclol（Wikidata Q907909、FDA GSRS UNII MP5WZK8M5U）、`CBGa` も同日
  cannabigerolic acid（ChEBI 67081、Wikidata Q27135612、FDA GSRS UNII 80I4ZM847Y）
  と確認して `compound_minor` へ移した。残る 10 語の化学的同一性は未確認で、
  名称・構造・クラス・別名のいずれも根拠が無い。
  `CBE` の系列も `CBE` / `CBE リキッド` の文字列一致を測るもので、各結果の内容を保証しない。
  variant は作っていない（表記は観測の記録であり、run の無い語の綴りを先に作らない）。
  **登録時点では run 0** で、登録時点の未収集を 0 観測とも欠測とも書かない。
  現在の run 結果は上と同じ study 文書・catalog・監査を正本とする。
- 2026-11-11 の 12 query（6 語 × `compound_general` / `product_liquid`。ISS-20261111-TAX-041）は
  **実 run を根拠にしない**登録である。`THCA` / `THCB` の総称的な化学解釈を置き換える検索トピックであり、
  概念はいずれも管理カテゴリ `compound_identity_unverified` にある。`Δ9-THCA-A` / `THCA-B` は
  Moreno-Sanz 2016 / Filer 2021 が、`Δ8-THCB` / `Δ9-THCB` は Linciano et al. 2020 /
  Tanaka & Kikura-Hanajiri 2024 が分析物質として記録し、`THCB-O-acetate` の Δ8/Δ9 両異性体は
  2024 年の厚生労働省令の構造グループに列挙されている。ただし登録文字列の単一外部レコードは選択しておらず、
  `Δ8-THCA` は構造・命名の出所も未検証である。**登録時点では run 0** であり、未収集を 0 観測とも欠測とも
  書かない。現在の run 結果は study README / methodology / catalog / `make audit-youtube-coverage` を
  正本とする。
- **THCNM の登録と収集**: 登録時の根拠は taxonomy の `compound_thcnm` 概念（名称・同一性の根拠は ISS-20261104-TAX-028）と
  研究設計上の化合物集合への追加であり、その時点では収集を行っていなかった。2026-11-04 に
  `thcnm-general-ja`（Google Trends 12ヶ月・5年）と `thcnm-liquid-ja` / `tha-liquid-ja`（YouTube 各 1 run）を
  収集し、登録した文字列がそのまま送られたことを payload の `input` 列（YouTube）と
  `terms`（Google Trends）で確認している。語の実在を測ったのはこの収集であり、
  THA は別名・商業名であって別物質の証拠にはしない。
- `THA リキッド` は以前 `thcnm-liquid-ja` の alternative variant だった。owner 指示で
  `tha-liquid-ja` の canonical text として独立させたため、同じ文字列を 2 つのクエリに属させず、
  `thcnm-liquid-ja` 側の alternative からは除いた（1 テキスト 1 所有。canonical と alternative の
  重複は `VARIANT_TEXT_CONFLICTS_CANONICAL`）。`compound_thcnm` の `product_liquid` は
  **2 本の required primary query** を持ち、同一性についての主張は変わらない。
- `keywords.yaml` のみに存在し run 実績がない語（例 `CBX オイル` / `CBD ペン`）は
  候補として保留（推測で intent を確定しない）。
- **variant は note を持てない**: `query-variants.json` の variant 項目は `variant_id` / `text` / `status` の 3 フィールドのみで、未知フィールドを拒否する schema（`src/validation/schemas/query.py`）のため根拠を書き込む場所がない。表記の根拠と同一性の留保は本ファイル §2 と `docs/provenance/compound-taxonomy.md` に記録する（`THCO` の証拠は ISS-20261104-TAX-029）。
- 除外規則は本表に載るフレーズのみ。根拠のない語は追加しない。
