# Issue: owner 指示による登録状態バッチ — 13 語を管理カテゴリ `compound_identity_unverified` で登録し、THCP の非登録判断を置換

**ID:** ISS-20261111-TAX-040  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`（管理カテゴリ 1 + 化合物 13）、
`metadata/taxonomy/iptc-mapping.yaml`、`docs/data-dictionary.md` §6.4、
`docs/provenance/compound-taxonomy.md`、`docs/provenance/query-inventory.md`、
`metadata/queries/query-registry.json`（26 query）、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`、
`datasets/cannabinoid-raw-collection/README.md`・`methodology.md`、
`project.json` `queryDesign`（写し）、`metadata/provenance/evidence-registry.json`、
`exports/taxonomy/*`（再生成）  
**関連:** `ISS-20261015-TAX-027`（本 issue が THCP の非登録判断を置換）、
`ISS-20261110-TAX-039`（15 語のうち CBC・CBDV を先行登録し、13 語を保留した記録）、
`ISS-20261024-TAX-014`・`ISS-20261104-TAX-028`（同一性未確認語の登録前例）

## 概要

2026-11-11、owner は `cannabinoid-raw-collection` の登録化合物集合を**列挙 15 語**で
広げることを明示的に指示した。owner の指示原文:

> 「ほかのHHBDなどと同じく対応、いちいち保留しなくていい」

あわせて **Google Trends と YouTube の収集**を許可した（課金を伴う収集の承認を含む。
金額は本 issue にも他の追跡文書にも記録しない。[`AGENTS.md`](../../../../AGENTS.md) の
Scope Exclusion: Cost）。

**本 issue の範囲は登録と設計のみである。** 収集・raw payload 作成・staging 採用・
公開・release slice の拡張・push・release は行っていない。13 語の query は **run 0** で
未収集である。

これは **per-term の identity 承認を求めない**という明示的な scope 決定であり、
2026-10-15 の `ISS-20261015-TAX-027`（`compound_rare` を空に保ち `compound_thcp` を
登録しない）のうち **THCP の非登録判断を置換する**。

## 登録した 15 語

依頼文は「17 物質」としているが、**列挙は 15 語**である。**列挙された 15 語を登録し、
不足する 2 語は推測で補わない**（後述の未決事項）。

| # | 語（owner 表記） | `compound_id` | concept | 登録カテゴリ | query（`compound_general` / `product_liquid`） | 状態 |
|---:|---|---|---|---|---|---|
| 1 | `CBC` | `compound_cbc` | 既存を再利用 | `compound_minor`（既存） | `cbc-general-ja` / `cbc-liquid-ja`（2026-11-10 登録済み） | 未収集（run 0） |
| 2 | `CBDV` | `compound_cbdv` | 既存を再利用 | `compound_minor`（既存） | `cbdv-general-ja` / `cbdv-liquid-ja`（同上） | 未収集（run 0） |
| 3 | `THCB` | `compound_thcb` | 新規 | `compound_identity_unverified` | `thcb-general-ja` / `thcb-liquid-ja` | 未収集（run 0） |
| 4 | `THCP` | `compound_thcp` | 新規 | `compound_identity_unverified` | `thcp-general-ja` / `thcp-liquid-ja` | 未収集（run 0） |
| 5 | `THCJD` | `compound_thcjd` | 新規 | `compound_identity_unverified` | `thcjd-general-ja` / `thcjd-liquid-ja` | 未収集（run 0） |
| 6 | `THCPO` | `compound_thcpo` | 新規 | `compound_identity_unverified` | `thcpo-general-ja` / `thcpo-liquid-ja` | 未収集（run 0） |
| 7 | `CBE` | `compound_cbe` | 新規 | `compound_identity_unverified` | `cbe-general-ja` / `cbe-liquid-ja` | 未収集（run 0） |
| 8 | `HHCPO` | `compound_hhcpo` | 新規 | `compound_identity_unverified` | `hhcpo-general-ja` / `hhcpo-liquid-ja` | 未収集（run 0） |
| 9 | `CBND` | `compound_cbnd` | 新規 | `compound_identity_unverified` | `cbnd-general-ja` / `cbnd-liquid-ja` | 未収集（run 0） |
| 10 | `CBL` | `compound_cbl` | 新規 | `compound_identity_unverified` | `cbl-general-ja` / `cbl-liquid-ja` | 未収集（run 0） |
| 11 | `CBGa` | `compound_cbga` | 新規 | `compound_identity_unverified` | `cbga-general-ja` / `cbga-liquid-ja` | 未収集（run 0） |
| 12 | `CBP` | `compound_cbp` | 新規 | `compound_identity_unverified` | `cbp-general-ja` / `cbp-liquid-ja` | 未収集（run 0） |
| 13 | `10-OH-HHC` | `compound_10_oh_hhc` | 新規 | `compound_identity_unverified` | `10-oh-hhc-general-ja` / `10-oh-hhc-liquid-ja` | 未収集（run 0） |
| 14 | `THXE` | `compound_thxe` | 新規 | `compound_identity_unverified` | `thxe-general-ja` / `thxe-liquid-ja` | 未収集（run 0） |
| 15 | `THCA` | `compound_thca` | 新規 | `compound_identity_unverified` | `thca-general-ja` / `thca-liquid-ja` | 未収集（run 0） |

- **登録文字列は owner の表記をそのまま**使う（`CBGa` の小文字 `a`、`10-OH-HHC` のハイフン、
  `THCJD` / `THCPO` / `THXE` / `CBND` の綴り）。canonical text は `<term>` と `<term> リキッド`。
- `CBC` / `CBDV` は **taxonomy の既存概念を再利用**し、ID・ラベル・分類・`exactMatch` を
  変えていない（2026-11-10 の `ISS-20261110-TAX-039`）。本 issue は両語をバッチの件数に含める。

## 管理カテゴリ `compound_identity_unverified`

13 語は既存の 6 カテゴリ（経路／由来の分類）のどれにも置かない。置けば根拠の無い
経路・化学分類の主張になるため、**管理上の登録状態カテゴリ**を 1 つ追加した。

- このカテゴリと各 member の `skos:scopeNote`（en / ja）は、**経路・由来、天然存在、
  化学クラス、構造、別名関係、規制状態について何も主張しない**ことを明記している。
- 希少・マイナー・半合成・合成のいずれの判断でもなく、既存カテゴリの代替でもない。
  語が別個の物質を指すことや、その背後に物質が存在することの主張でもない。
- `skos:exactMatch`・CAS・PubChem / IUPAC 名・化学クラスへのリンクは付けない。
  外部レジストリの照会は行っていない（依頼条件）。**識別子が無いのではなく、確認していない。**
- 移す条件は、検証済み外部識別子を伴う文書化された化学名、または物質名と経路／由来を
  記録した出所が得られた場合。
- 詳細と根拠は [`docs/provenance/compound-taxonomy.md`](../../../../docs/provenance/compound-taxonomy.md)
  の 2026-11-11 節。

## TAX-027 の置換（日付付き）

- `ISS-20261015-TAX-027` は 2026-10-15 に「`compound_rare` を空のまま維持し、
  `compound_cbdp` / `compound_thcp` を登録しない」と判断した。
- **2026-11-11 の owner 指示が、THCP についてこの非登録判断を置換する。**
- **置換したのは THCP の非登録判断だけである。** `compound_rare` の空維持、
  `compound_cbdp` を登録しない判断、希少メンバーに収集級の根拠を要求する gate は有効なまま。
  THCP は `compound_rare` に入れていない。
- 固定テスト `tests/validation/test_compound_rare_membership.py` は、新しい決定
  （rare は空、CBDP は未登録、THCP は管理カテゴリ、置換が scopeNote と台帳に記録）を
  検査するよう更新した。テストは削除・緩和していない。

## 未収集・未採用・未公開の状態

- 26 query はすべて **run 0**。Google Trends / YouTube / X のいずれでも実行していない。
  **0 観測でも欠測でもない**（未収集）。
- `metadata/queries/query-variants.json` に variant を追加していない（run の無い語の
  綴りを先に作らない）。
- raw run・staging declaration・catalog 登録・採用はいずれも無い。
- `make audit-youtube-coverage` は 15 化合物（13 語 + CBC・CBDV）を `missing_compounds`
  として報告する。`missing` は「採用済み run が無い」であり 0 観測ではない。
- release slice（`cannabinoid-platform-trends`）は広げていない。公開ページ・Zenodo・DOI
  への変更もない。
- `excluded_compound_ids` には入れていない（未収集は比較集合からの除外判断ではない）。

## 未決事項

- 依頼文の「17 物質」と列挙 15 語の差（2 語）。**不足語は推測で補わない。**
- 13 語それぞれの同一性を何で確定するか（標準物質、供給元 SDS / COA、公的レジストリ）。
- `CBGa` / `THCA` / `10-OH-HHC` と既存概念（`compound_cbg` / `compound_thc` / `compound_hhc`）
  の関係、`THCPO` / `HHCPO` の構造。根拠が得られるまで主張しない。
- `THCJD` / `THXE` / `CBE` / `CBND` / `CBL` / `CBP` の略号の展開。
- Google Trends の共通スケール（`compound_general` を対象とする policy）は、13 語の登録により
  被覆対象が広がる。比較集合に入れるかは別の比較設計の判断であり、本 issue では決めない。

## 解消条件

- [x] owner 指示による 15 語の登録と 26 query の登録（2026-11-11）
- [x] 管理カテゴリの追加と、主張しない範囲の明記（2026-11-11）
- [x] TAX-027 の THCP 非登録判断の置換記録とテスト更新（2026-11-11）
- [x] 未収集状態の宣言（2026-11-11）
- [ ] 依頼文の「17 物質」と列挙 15 語の差（2 語）の確認
- [ ] 13 語の同一性の確定と、根拠が支えるカテゴリへの移動
- [ ] 収集する場合: 計画書・窓・staging declaration・L1 gate・採用（別作業）

## 出所

- 2026-11-11 の owner 指示（「ほかのHHBDなどと同じく対応、いちいち保留しなくていい」、
  15 語の列挙、Google Trends / YouTube 収集の許可）。外部 URL の照会は行っていない。
- リポジトリ内: `metadata/taxonomy/compound-taxonomy.skos.jsonld`、
  `metadata/queries/query-registry.json`、`docs/provenance/compound-taxonomy.md`、
  `ISS-20261015-TAX-027`、`ISS-20261110-TAX-039`。
- 外部レジストリ（ChEBI / PubChem / CAS / Wikidata）の照会は行っていない。

---

## 追記（2026-11-11）: `CBE` の意図確認

上の登録表・未決事項は**登録時点の履歴**として保持する。2026-11-11、owner は
`CBE` が cannabielsoin を指すかという確認に `y` と回答した。これにより
`compound_cbe` の化学的同一性は未確認ではなく **cannabielsoin** となった。

- 検証した識別子: FDA GSRS の承認済み CANNABIELSOIN 記録（UNII `2ERD6V6652`、
  CAS `52025-76-0`、PubChem CID `162113`、分子式 `C21H30O3`）、Wikidata `Q22668702`。
- 出所: PubMed 3254981（1988）/ 2614640（1989）/ 1806944（1991）、
  DOI `10.1055/s-2007-969870`（1983）、PubMed 39062125 / PMC11275175 /
  DOI `10.3390/biomedicines12071551`（2024）。2024 年論文は CBE を
  非酵素的フィトカンナビノイドと記述し、Cannabis sativa への天然存在が
  確立しているとする。
- taxonomy: `compound_cbe` の prefLabel を `Cannabielsoin (CBE)` /
  `カンナビエルソイン (CBE)` とし、`skos:broader` を `compound_minor` へ移した。
  `compound_identity_unverified` の members は 13 語から 12 語になる。
  化学クラスは未形式化のまま（CBE 型クラスは `chemical-class-taxonomy` に無い）。
- **変更しないもの**: `cbe-general-ja` / `cbe-liquid-ja` の canonical_text、
  raw 観測、件数、CBE 331 件・CBL 269 件の partial 状態、収集計画、
  公開ページの `requires_review` 状態。公開 review envelope・decision / evidence
  hash・DOI・version / release status・図は作成・変更していない。
- **クエリの限界**: Google Trends / YouTube の系列は `CBE` / `CBE リキッド` の
  文字列一致を測るものであり、各結果が cannabielsoin を扱うことの確認ではない。
  既存サンプルは文字列一致の観測であって、内容の関連性の証明ではない。
- 根拠の詳細は `docs/provenance/compound-taxonomy.md` の 2026-11-11 節
  「owner の意図確認: CBE = cannabielsoin」に記録した。元の未決事項のうち
  「CBE の略号の展開」はこの追記で解消する。他の 12 語の同一性確認は未解決のまま。

---

## 追記（2026-11-11）: `CBL` と `CBGa` の意図確認

上の登録表・未決事項と CBE 追記は**履歴として保持する**。2026-11-11、owner は
`CBL` が cannabicyclol を指すかという確認に `go`、`CBGa` が cannabigerolic acid
（標準表記 `CBGA`）を指すかという確認に `y` と回答した。これにより両語の化学的同一性は
未確認ではなくなった。

- **CBL = cannabicyclol**。検証した識別子: Wikidata `Q907909`、FDA GSRS の UNII
  `MP5WZK8M5U` 記録（`substanceClass: chemical`、`definitionLevel: COMPLETE`、名称
  CANNABICYCLOL / CANNABIPINOL / PENTYLCANNABICYCLOL）、PubChem CID `30607`
  （立体未指定 / `(+/-)`）と `59444380`（立体指定）、分子式 `C21H30O2`。
  **CAS は 21366-63-2（立体指定）と 67920-00-7（立体未指定の別名）が併存するため、
  単一の CAS を識別子として断定しない**。
- **CBGa = cannabigerolic acid（CBGA）**。検証した識別子: ChEBI `67081`、Wikidata
  `Q27135612`、FDA GSRS の UNII `80I4ZM847Y` 記録（名称 CANNABIGEROLIC ACID /
  CBGA）、PubChem CID `6449999`、CAS `25555-57-1`、分子式 `C22H32O4`。CBG は
  CBGA の脱炭酸体であり、別名ではない。
- taxonomy: `compound_cbl` / `compound_cbga` の prefLabel を `Cannabicyclol (CBL)` /
  `カンナビシクロール (CBL)`、`Cannabigerolic acid (CBGA)` / `カンナビゲロール酸 (CBGA)`
  とし、`skos:broader` を `compound_minor` へ移した。
  `compound_identity_unverified` の members は 12 語から 10 語になった。化学クラスは
  未形式化のまま（CBL 型・CBGA 型クラスは `chemical-class-taxonomy` に無い）。
- **`skos:related` は張らない**。`CBGa` と `compound_cbg`（酸性前駆体 / 脱炭酸体）、
  `CBL` と `compound_cbc`（CBC からの変換）は候補の関係として scopeNote と台帳に
  文章で記録し、構造化はしない。`compound_cbg` の ChEBI `exactMatch` に既知の不一致が
  あり、別の issue で修正する。
- 出所: PubMed 39811943（Haghdoost et al. 2025, J Nat Prod, DOI
  `10.1021/acs.jnatprod.4c00977`。CBL を minor phytocannabinoid と記述し、CBC からの
  酸触媒変換を報告）、PubMed 33839545（押収大麻等で cannabicyclol と cannabigerolic
  acid を定量）、PubMed 31686510（CBGA をフィトカンナビノイド酸として列挙）、
  PubMed 35887277（CBG は CBGA の非酵素的脱炭酸で生成する）、厚生労働科学研究の報告書
  （2023。日本語表記「カンナビシクロール」「カンナビゲロール酸」）、J-GLOBAL
  （カンナビゲロール酸）。
- **変更しないもの**: `cbl-general-ja` / `cbl-liquid-ja` / `cbga-general-ja` /
  `cbga-liquid-ja` の canonical_text（`CBL` / `CBL リキッド` / `CBGa` /
  `CBGa リキッド`。`CBGa` の小文字 `a` を保持し、正規化しない）、raw 観測、run
  metadata、catalog、件数、CBL 269 件の partial 状態、CBGa の NO_DATA、収集計画、
  公開ページの `requires_review` 状態。公開 review envelope・承認・decision / evidence
  hash・DOI・version / release status・図は作成・変更していない。
- **クエリの限界**: Google Trends / YouTube の系列は `CBL` / `CBL リキッド`、`CBGa` /
  `CBGa リキッド` の文字列一致を測るものであり、意図された同一性が確認されても、各結果が
  その物質を扱うことの確認ではない。既存サンプルは文字列一致の観測である。
- 根拠の詳細は `docs/provenance/compound-taxonomy.md` の 2026-11-11 節
  「owner の意図確認: CBL = cannabicyclol, CBGa = cannabigerolic acid」に記録した。
  元の未決事項のうち「`CBGa` の略号の展開」と「`CBL` の略号の展開」はこの追記で
  解消する。同一性が未確認のまま残るのは THCB / THCP / THCJD / THCPO / HHCPO /
  CBND / CBP / 10-OH-HHC / THXE / THCA の 10 語である。

---

## 追記（2026-11-11）: `THCP` と `THCJD` の意図確認（同族体ファミリー、Δ8/Δ9 未指定）

上の登録表・未決事項と CBE / CBL / CBGa の追記は**履歴として保持する**。2026-11-11、
owner は登録語の意図された意味を次のように確認した。

- `THCP` = **tetrahydrocannabiphorol（C7）同族体ファミリー、Δ8/Δ9 未指定**
- `THCJD` = **THC-JD / 3-octyl-THC（C8）同族体ファミリー、Δ8/Δ9 未指定**

これは**検索トピックのファミリー範囲の確認**であり、個々の Google Trends / YouTube 結果が
どちらの異性体を扱うかの確認ではない。Δ8 体と Δ9 体は別物質であり、ハイフンなしの `THCJD`
は owner の検索文字列であって権威ある登録名ではない（名称と Δ8/Δ9 の 3-octyl-THC の同定は
Tanaka & Kikura-Hanajiri 2024、DOI `10.1248/yakushi.24-00029`）。

### taxonomy の扱い（新しいカテゴリは作らない）

- 両語は **`compound_identity_unverified` のまま**置く。単一物質としての化学的同一性は
  未確認であり、ファミリーを経路／由来カテゴリへ置くと根拠の無い経路・天然存在の主張になる。
- 管理カテゴリの scopeNote に「owner が異性体未指定の同族体ファミリーとしてのみ確認した語も
  ここに置き、ファミリー範囲は当該概念の scopeNote に記録する」という一文を加え、
  「単一物質としての」化学的同一性という表現に揃えた。**カテゴリ ID・階層・membership は変えない。**
- `compound_thcp` / `compound_thcjd` の scopeNote（en / ja）に、owner の確認、Δ8/Δ9 が
  別物質であること、単一レコードが無いこと、変化しない限界（天然存在・合成経路・安全性・
  臨床効果・規制状態を推定しない）を記録した。
- **`skos:exactMatch` は張らない。** Δ9-THCP（CAS `54763-99-4`、PubChem CID `6453074`、
  Wikidata `Q85806080`、FDA GSRS UNII `WTK87HN3LG`）と Δ8-THCP（CAS `51768-60-6`、
  PubChem CID `44307335`、Wikidata `Q141317106`）は**異性体の識別子**であり、登録語の
  識別子ではない。`THCJD` も Δ9（PubChem CID `155318984`）・Δ8（PubChem CID `102024084`）
  の各レコードを持ち、ファミリーの単一 ID は無い。識別子は
  `docs/provenance/compound-taxonomy.md` にのみ記録した。
- `compound_minor` / `compound_rare` / `compound_semisynthetic` / `compound_synthetic` へは
  **移さない**。`compound_minor` はフィトカンナビノイドという経路／由来の主張であり、
  Δ8/Δ9 未指定の検索語全体の天然存在を支えない。`compound_rare` は「微量にのみ存在する」
  という天然存在の主張を含み、意図的に空のまま維持している（TAX-027）。

### 記録した出所と限界

- Citti et al. 2019（DOI `10.1038/s41598-019-56785-1`）は Δ9-THCP を C7 同族体として
  報告する。**「33 倍」は CB1 結合親和性の比であり、ヒトでの効力ではない。**
- 規制状態は主張しない。規制資料は本追記では評価していない（規制状態を推定しない）。
- Munger et al. 2026（DOI `10.26828/cannabis/2026/000348`）は販売製品の表示と内容の
  重大な不一致を報告し、「19 倍」を業界の主張として扱う。**効力の測定値ではない。**
- **推定しないもの**: 天然存在、合成経路、安全性、臨床効果、規制状態、個々の結果の
  異性体归属。

### 変更した層

`metadata/taxonomy/compound-taxonomy.skos.jsonld`（2 概念の scopeNote、管理カテゴリの
scopeNote、scheme description の単一物質表現）、`docs/provenance/compound-taxonomy.md`、
`docs/provenance/query-inventory.md`（証拠欄、版 1.7.3）、`docs/data-dictionary.md` §6.4、
`docs/specs/validation-framework.md` §23.4、
`metadata/taxonomy/iptc-mapping.yaml`（版 1.7.0）、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`（`identity_caveat` /
`limitations` / `distribution.reason`）、同 study の `README.md`・`methodology.md`、
`project.json` の `queryDesign`（写し）、`metadata/provenance/evidence-registry.json`
（taxonomy hash の再観測）、`exports/taxonomy/*`（再生成）、
`publication/research_thcp.html`・`publication/research_thcjd.html`（同一性の記述のみ）、
`tests/validation/test_registration_state_batch.py`（ファミリー範囲の固定テスト追加）。

### 変更しないもの

- `thcp-general-ja` / `thcp-liquid-ja` / `thcjd-general-ja` / `thcjd-liquid-ja` の
  canonical_text（`THCP` / `THCP リキッド` / `THCJD` / `THCJD リキッド`）と status。
- 管理カテゴリの membership（10 語）、`registration_basis` の `identity_state`
  （`compound_identity_unverified`）、raw 観測、run metadata、catalog、件数、収集計画。
- 公開ページの `requires_review` 状態。review envelope・承認・decision / evidence hash・
  DOI・version / release status・図は作成・変更していない。

### 残る曖昧さ・未決

- 個々の検索結果・動画が Δ8 体と Δ9 体のどちらを扱うかは未確認である。
- 異性体未指定の同族体ファミリーを形式化する taxonomy の state（カテゴリ）を持つかは
  design decision であり、本追記では決めない（台帳 2026-11-11 節の未決事項）。
- Δ8 体の天然存在・合成経路・安全性・臨床効果は未評価である。
- 元の未決事項のうち「`THCP` / `THCJD` の略号の展開」は、両語が権威ある単一物質名ではなく
  それぞれ C7・C8 同族体ファミリーを指す検索語である、という範囲で解消する。
  同一性が未確認のまま残るのは THCB / THCPO / HHCPO / CBND / CBP / 10-OH-HHC / THXE /
  THCA の 8 語である。


---

## 追記（2026-11-11）: `THCPO` の意図確認（THCP-O-acetate、異性体の指定なし）

上の登録表・未決事項と CBE / CBL / CBGa / THCP / THCJD の追記は**履歴として保持する**。2026-11-11、owner は確認質問「`THCPO` は THCP-O-acetate を指しますか？」に `y` と回答し、**Δ8 体・Δ9 体のいずれの異性体も名指ししなかった**。したがって本登録は **異性体未指定の THCP-O-acetate ファミリー**として扱う。このファミリー扱いは回答の登録上の整理であり、**owner がファミリーを明示的に確認したものではない**。二つの異性体は別物質として区別し、個々の Google Trends / YouTube 結果がどちらの異性体を扱うかは確認しない。

`THCPO` と他の概念との関係は主張しない。`compound_thc_o` は別に登録された市場・総称の概念で、独自の同一性留保を持ち（単一の検証済み構造ではない）、本追記はそこへ特定の構造を割り当てない。`THCP-O-butanoate` は Tanaka et al. 2025 が Δ9-THCP-O-acetate と並んで同定した別のエステルであり、本概念の別名ではない。`HHCPO` は別に登録された語で、化学的同一性は未確認である。本概念との別名・`skos:related`・`exactMatch` は張らない。

### 検証した出所

- **厚生労働省**「指定薬物を指定する省令が公布されました」（2024-05-01 公布、2024-05-11 施行。令和6年厚生労働省令第81号）: 物質群1（6a,7,8,10a-テトラヒドロ）と物質群2（6a,7,10,10a-テトラヒドロ）は、1位に水酸基又はアセトキシ基が一つ、3位に直鎖 C3–C8 アルキル、他の置換基なしの構造を包括する（**麻薬を除く**）。別紙は n=7 として Δ9-THCP-O-acetate / Δ8-THCP-O-acetate を列挙する。両異性体が当該構造グループに該当することは、**省令の「麻薬を除く」除外規定の下での法令上の構造の事実**であり、個々の製品・検索結果の分類でも、規制判断でも、owner の同一性確認の一部でもない。
- **Tanaka et al. 2025**（Drug Test Anal 17(9):1795-1802、DOI `10.1002/dta.3883`、PMID 40075559）: オンライン流通のオイル製品 7 点とハーブ製品 1 点から Δ9-THCP-O（アセテート）と Δ9-THCP-O-butanoate を同定した。同論文は **Δ8-THC-O（アセテート、C5 同族体）** も同定しており、これは **Δ8-THCP-O-acetate ではない**。Δ8-THCP-O-acetate は同定していない。
- **レジストリ**: PubChem は Δ9 体 CID `172677450`（`C25H36O3`、InChIKey `OXMUZNKOOOITQD-NHCUHLMSSA-N`、別名に CAS `2829292-82-0`）と Δ8 体 CID `172874392`（`C25H36O3`、InChIKey `FDKCGSRFVKINQD-NHCUHLMSSA-N`、CAS の別名なし）を別レコードで持つ。Wikidata `Q122689235` は en label `THCP-O-acetate` だが、InChIKey と PubChem CID は Δ9 レコードに対応する（ja label なし、CAS の主張なし）。**記録した ChEBI 検索語は `THCP` のみで、その検索は該当なし**だった。これはアセテート体・ファミリーの ChEBI レコードが無いことの証明ではなく、ファミリーに対する `exactMatch` も割り当てていない。FDA GSRS の名称検索 `Tetrahydrocannabiphorol` では親化合物（UNII `WTK87HN3LG`）のみで、THCP-O-acetate のレコードは得られなかった。

### taxonomy の扱い（配置は変えない）

- `compound_thcpo` は **`compound_identity_unverified` のまま**置く。単一物質としての化学的同一性は未確認であり、ファミリーを経路／由来カテゴリへ置くと根拠の無い経路・天然存在の主張になる。
- `skos:altLabel` に `THCP-O-acetate`（en）を追加し、`THCPO リキッド`（ja）を維持した。`skos:prefLabel`（`THCPO` en/ja）と `skos:notation`（`compound_thcpo`）は変更しない。この別名は owner が確認した意図された意味を表す**概念レベルの検索スコープ別名**で、根拠は当該概念の scopeNote にある。**カテゴリ所属自体は同義関係を確立せず**、ファミリーが単一の化学構造であるという主張ではない。
- **`skos:exactMatch` は張らない。** ファミリー全体を表す単一レコードが無く、Δ9 体・Δ8 体のレコードは異性体の識別子である。識別子は `docs/provenance/compound-taxonomy.md` にのみ記録した。
- **規制状態**: 両異性体が 2024 年の厚生労働省令の構造グループに該当することを、省令の**「麻薬を除く」除外規定の下での法令上の構造の事実**として scopeNote と台帳に記録した。個々の製品・検索結果の分類ではなく、規制判断でも、owner の同一性確認の一部でもない。
- **推定しないもの**: 天然存在、合成経路、薬理、安全性、臨床効果、個々の結果の異性体归属。
- 管理カテゴリの scopeNote に、異性体未指定のエステル（アセテート）体ファミリーもここに置くこと、ファミリーの scopeNote が法令上の構造グループ該当を記録する場合があることを追記した。あわせて、**カテゴリ所属自体は同義関係を確立しない**ことと、member の `skos:altLabel` は概念レベルの記録で当該概念の scopeNote に独自の根拠を要することを明記した。カテゴリ ID・階層・membership（10 語）は変えない。

### 変更しないもの

- `thcpo-general-ja` / `thcpo-liquid-ja` の canonical_text（`THCPO` / `THCPO リキッド`）と status。
- raw 観測、run metadata、catalog、件数（Google Trends 5年 262 週、YouTube 33 件）、収集計画。**本追記は収集を伴わない。**
- 公開ページ `publication/research_thcpo.html` は `requires_review` のまま。review envelope・承認・decision / evidence hash・DOI・version / release status・図は作成・変更していない。
- `compound_thc_o` / `compound_hhcpo` 等の既存概念の識別子・分類・scopeNote。

### 残る曖昧さ・未決

- Δ8-THCP-O-acetate を同定した分析文献は確認していない。Tanaka et al. 2025 が同定した Δ8 アセテートは **Δ8-THC-O（アセテート、C5 同族体）** であり、Δ8-THCP-O-acetate ではない。Δ8-THCP-O-acetate の存在・天然存在・合成経路は未評価である。
- CAS `2829292-82-0` は PubChem の Δ9 レコードの別名であり、CAS Registry の独立照会は認証を要求したため実施していない。Δ8 体の CAS は確認していない。
- Wikidata の `THCP-O-acetate` 項目はラベルがファミリー名だが、構造キーは Δ9 レコードに対応する。ラベルだけを根拠にファミリーの識別子として使わない。
- 異性体未指定のファミリーを形式化する taxonomy の state（カテゴリ）を持つかは design decision であり、本追記では決めない。
- 元の未決事項のうち「`THCPO` の構造」は、THCP-O-acetate という意味と、異性体の指定が無いため Δ8/Δ9 ファミリーとして扱う範囲で解消する。同一性が未確認のまま残るのは THCB / HHCPO / CBND / CBP / 10-OH-HHC / THXE / THCA の 7 語である。`THCP` / `THCJD` はファミリー範囲のみ確認済み、`THCPO` は意味（THCP-O-acetate）のみ確認済みで異性体の指定が無く、いずれも単一物質の同定ではない。

### 変更した層

`metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_thcpo` の altLabel・scopeNote、管理カテゴリの scopeNote）、`metadata/taxonomy/iptc-mapping.yaml`（10 語群の理由、版 1.9.1）、`docs/data-dictionary.md` §6.4、`docs/provenance/compound-taxonomy.md`、`docs/provenance/query-inventory.md`（版 1.7.6）、`datasets/cannabinoid-raw-collection/metadata/query-design.json`（`registration_basis` / `identity_caveat` / `limitations`）、同 study の `README.md`・`methodology.md`、`project.json` の `queryDesign`（写し）、`metadata/provenance/evidence-registry.json`（taxonomy hash の再観測）、`exports/taxonomy/*`（再生成）、`publication/research_thcpo.html`（同一性の記述のみ）、`tests/validation/test_registration_state_batch.py`。
