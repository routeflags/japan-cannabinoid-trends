# Issue: THCA / THCB を特定の検索トピックへ分割登録する — 総称概念と既存 run は維持

**ID:** ISS-20261111-TAX-041
**優先度:** P2 (Medium)
**ステータス:** OPEN
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`（6 概念）、
`metadata/taxonomy/iptc-mapping.yaml`、`metadata/queries/query-registry.json`（12 query）、
`docs/data-dictionary.md` §6.4、`docs/provenance/compound-taxonomy.md`、
`docs/provenance/query-inventory.md`、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`、
同 study の `README.md`・`methodology.md`、`project.json` の `queryDesign`（写し）、
`metadata/provenance/evidence-registry.json`、`exports/taxonomy/*`（再生成）、
`publication/research_thca.html` / `research_thcb.html`（位置づけの記述のみ）
**関連:** `ISS-20261111-TAX-040`（2026-11-11 の登録バッチ、THCP / THCJD のファミリー確認、THCPO の意味確認）、
`ISS-20261104-TAX-029`（THC-O / THCO の同一性留保）、`ISS-20261110-TAX-039`（CBC / CBDV の追加）

## 概要

2026-11-11、owner は `THCA` の総称的な化学解釈を、次の 3 つの**検索トピック概念**に置き換えることを確認した。

- `Δ9-THCA-A`
- `THCA-B`
- `Δ8-THCA`

同日、`THCB` を次の 3 つの検索トピック概念に分割すること、および `THCB-O-acetate` を登録することを確認した。

- `Δ8-THCB`
- `Δ9-THCB`
- `THCB-O-acetate`（異性体未指定。文献・法令は Δ8 / Δ9 を別物質として扱う）

本 issue の範囲は**登録と設計のみ**である。Google Trends / YouTube の新規収集、raw の変更、
staging declaration の作成、既存 run id・件数の変更、release slice の拡張、公開・承認・push は行っていない。

**owner の確認は検索トピックの範囲を確定するものであり、各検索文字列が単一の物質や単一の外部レコードを
指すことの確認ではない。** 既存の `THCA` / `THCB` run は元の文字列クエリに付いたままで、
6 つの新概念へ割り当てない。6 語の `compound_general` 登録は active なので、3 つの共通スケール policy
（5年・12ヶ月・3ヶ月）の required 集合に 6 語ずつ、計 18 件の**設計上の** required entry が加わる
（未収集は収集失敗ではない）。

## 登録した 6 概念と 12 query

| 語（owner 表記） | `compound_id` | 配置 | 外部識別子 | `compound_general` | `product_liquid` | 収集状態 |
|---|---|---|---|---|---|---|
| `Δ9-THCA-A` | `compound_delta9_thca_a` | `compound_identity_unverified` | なし | `delta9-thca-a-general-ja` = `Δ9-THCA-A` | `delta9-thca-a-liquid-ja` = `Δ9-THCA-A リキッド` | 登録時点で未収集（run 0） |
| `THCA-B` | `compound_thca_b` | `compound_identity_unverified` | なし | `thca-b-general-ja` = `THCA-B` | `thca-b-liquid-ja` = `THCA-B リキッド` | 登録時点で未収集（run 0） |
| `Δ8-THCA` | `compound_delta8_thca` | `compound_identity_unverified` | なし | `delta8-thca-general-ja` = `Δ8-THCA` | `delta8-thca-liquid-ja` = `Δ8-THCA リキッド` | 登録時点で未収集（run 0） |
| `Δ8-THCB` | `compound_delta8_thcb` | `compound_identity_unverified` | なし | `delta8-thcb-general-ja` = `Δ8-THCB` | `delta8-thcb-liquid-ja` = `Δ8-THCB リキッド` | 登録時点で未収集（run 0） |
| `Δ9-THCB` | `compound_delta9_thcb` | `compound_identity_unverified` | なし | `delta9-thcb-general-ja` = `Δ9-THCB` | `delta9-thcb-liquid-ja` = `Δ9-THCB リキッド` | 登録時点で未収集（run 0） |
| `THCB-O-acetate` | `compound_thcb_o_acetate` | `compound_identity_unverified` | なし | `thcb-o-acetate-general-ja` = `THCB-O-acetate` | `thcb-o-acetate-liquid-ja` = `THCB-O-acetate リキッド` | 登録時点で未収集（run 0） |

- すべて `status: active`、`language: ja`。語の表記は owner のものをそのまま保存する（`Δ`、数字、ハイフン）。
- 既存の `thca-general-ja` / `thca-liquid-ja` / `thcb-general-ja` / `thcb-liquid-ja` の ID・文字列・status は
  変更しない。非推奨化も、新概念への再ターゲットもしない。
- `metadata/queries/query-variants.json` は変更しない。variant は観測された表記の記録であり、
  run の無い語の別表記を先に作らない。

## 同一性の扱い（管理カテゴリに留める理由）

6 語はすべて `compound_identity_unverified` に置く。このカテゴリは**管理上の登録状態**であり、
経路／由来・化学クラス・天然存在・構造・別名・規制状態の主張ではない。

- 登録文字列について**単一の検証済み外部識別子を選択していない**ため、概念に `skos:exactMatch`・CAS・
  PubChem CID・UNII・ChEBI ID・IUPAC 名を付けない。「識別子が無い」のではなく、本変更では選択していない。
- `Δ8-THCA` は**構造・命名の出所も本変更で確認していない**。A/B のカルボキシル配置の区別は Δ9 系列の
  文献に基づく記載であり、Δ8 系列へ推測で拡張しない。
- `THCB-O-acetate` は Δ8 / Δ9 を述べないため、単一物質も単一の外部レコードも指さない。
- `skos:related` は張らない。総称概念（`compound_thca` / `compound_thcb`）・相互（Δ8/Δ9、A/B）・
  `compound_thc` との関係は scopeNote の文章に留める。
- 化学クラスは未形式化のまま。

## 記録した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| Moreno-Sanz 2016, Cannabis Cannabinoid Res 1:124-130, DOI `10.1089/can.2016.0008` | Δ9-THCA-A（2-carboxy-THC）を Δ9-THC の酸性前駆体とし、Cannabis の腺毛で生合成・蓄積されると記述。文献の `THCA` の曖昧な用法を指摘。THCA-B（4-carboxy-THC）を少量異性体として記録し、後続研究が存在を確認できなかったことも記録 | Δ9-THCA-A / THCA-B の名称・構造上の区別と、総称 `THCA` の曖昧さ。Δ8-THCA の構造、天然存在、検索結果・製品の内容は支えない |
| Filer 2021, Cannabis Cannabinoid Res 6(5):446-448, DOI `10.1089/can.2021.0003`, PMCID `PMC8612408` | THCA-B を THCA-A の構造異性体とし、1969 年の単離・特性評価と 1975 年の X 線研究を記録。脱炭酸挙動の差を議論 | THCA-A / THCA-B が別物質で、THCA-B が別名でないこと。Δ8-THCA、天然存在、内容は支えない |
| Linciano et al. 2020, J Nat Prod 83(1):88-98, DOI `10.1021/acs.jnatprod.9b00876` | medicinal Cannabis sativa 品種から Δ9-THCB を単離し、構造・絶対配置を確認 | Δ9 体の名称と構造。Δ8 体、総称 `THCB`、天然存在、製品・結果の内容は支えない |
| Tanaka & Kikura-Hanajiri 2024, 薬学雑誌 144(8):823-837, DOI `10.1248/yakushi.24-00029` | 国内でオンライン流通したオイル製品 5 点から、Δ8-THCB と Δ9-THCB をそれぞれ同定 | 両異性体が別物質であり、分析対象の製品に存在したこと。天然存在・合成経路・規制状態・結果の異性体归属は支えない |
| 厚生労働省 令和6年厚生労働省令第81号（2024-05-01 公布、2024-05-11 施行）別紙 | 物質群1（6a,7,8,10a-テトラヒドロ）と物質群2（6a,7,10,10a-テトラヒドロ）の構造定義。別紙に Δ9-THCB-O-acetate（n=4）と Δ8-THCB-O-acetate（n=4）を明記 | 両異性体が法令上の構造グループに該当すること。製品の適法性・含有量・安全性、経路、天然存在、結果の内容は支えない |

出所の登録: `metadata/provenance/evidence-registry.json` の
`ev-doi-10-1089-can-2016-0008` / `ev-doi-10-1089-can-2021-0003` /
`ev-doi-10-1021-acs-jnatprod-9b00876` / `ev-doi-10-1248-yakushi-24-00029` /
`ev-mhlw-2024-r6-81-besshi`（外部参照は `sha256: null`、`external_unverifiable`）。

## 変更しないもの

- `compound_thca` / `compound_thcb` の notation・`@id`・prefLabel・配置。両概念は総称文字列の登録として残る。
  既存 run の帰属、件数、raw、run metadata、catalog、declaration、収集計画。
- `query-variants.json`、`metadata/keywords.yaml`（後者は legacy の非正本）。
- 公開ページの `requires_review` 状態、review envelope、承認・decision / evidence hash、DOI、
  version / release status、図。6 概念はデータが無いため、空の公開ページを新設しない。
- release slice。本 issue は配布・公開を広げない。

## 未決事項

- `Δ8-THCA` の構造・命名の出所（A/B のカルボキシル配置を含む）の確認。
- Δ8-THCB / Δ9-THCB の立体化学と、各語の検証済み外部識別子（CAS / PubChem / ChEBI / UNII / Wikidata）の選択。
- THCB-O-acetate の異性体ごとのレコードの確認（本変更ではファミリーとして登録し、レコードを選択していない）。
- 6 概念を収集するか。収集する場合は、計画・窓・staging declaration・L1 gate・採用を別作業で行う。

## 出所

- 2026-11-11 の owner 確認: `THCA` = `Δ9-THCA-A` / `THCA-B` / `Δ8-THCA`、`THCB` = `Δ8-THCB` /
  `Δ9-THCB` / `THCB-O-acetate`。
- リポジトリ内: `metadata/taxonomy/compound-taxonomy.skos.jsonld`、`metadata/queries/query-registry.json`、
  `docs/provenance/compound-taxonomy.md`、`ISS-20261111-TAX-040`。
- 外部: 上表の DOI / PMCID と厚生労働省令・別紙。
