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
