# Issue: `cannabinoid-raw-collection` の対象拡張依頼 — CBC・CBDV を登録、13 語は canonical identity 未登録のため保留

**ID:** ISS-20261110-TAX-039  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/queries/query-registry.json`（登録 4 件）、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`（`declared_not_yet_collected`）、
`datasets/cannabinoid-raw-collection/README.md`・`methodology.md`（被覆表と未収集状態）、
`project.json` `queryDesign`（写し）、`docs/provenance/compound-taxonomy.md`（台帳）、
`metadata/provenance/evidence-registry.json`（query registry の hash 再観測）  
**関連:** `ISS-20261015-TAX-027`（`compound_rare` の登録 gate）、`ISS-20261024-TAX-014`（identity 未確認語の保留前例）、`ISS-20261104-TAX-028`（THCNM の登録前例）

## 概要

2026-11-10 のスレッド依頼で、`datasets/cannabinoid-raw-collection` の対象集合とクエリ設計を広げる物質名の
リストが提示された。依頼の範囲は**対象集合とクエリ設計の拡張**であり、収集 API の実行・raw payload 作成・
staging 採用・公開・release slice の拡張は**含まない**。外部 URL は使用しない（依頼条件）。

- 提示された物質名は **15 語**（依頼文は「17 物質」と書いているが列挙は 15 語）。
  `THCB` / `THCP` / `THCJD` / `THCPO` / `CBE` / `HHCPO` / `CBND` / `CBL` / `CBC` / `CBDV` / `CBGa` / `CBP` /
  `10-OH-HHC` / `THXE` / `THCA`。**不足する 2 語は owner の確認が必要**（推測で補わない）。
- 登録できたのは **2 語**（`CBC` / `CBDV`）だけである。いずれも `metadata/taxonomy/compound-taxonomy.skos.jsonld`
  に既存の canonical concept があり、**ID・分類を作らずに再利用**できた。
- 残り **13 語は canonical identity がリポジトリに無い**ため保留し、query も登録していない。

## 登録したもの（scope owner と出所）

- **scope owner:** owner（2026-11-10 のスレッド依頼）。`query-design.json` の
  `compound_set.declared_not_yet_collected` に `decided: 2026-11-10` / `decided_by: owner` として記録した。
- **出所:** 2026-11-10 のスレッド依頼（物質名の列挙）。リポジトリ内の根拠は taxonomy の既存 concept のみ。
  外部ページ・外部レジストリの照会は行っていない。

| 語 | `compound_id`（既存） | 分類（既存 `skos:broader`） | 登録した `query_id` | 状態 |
|---|---|---|---|---|
| CBC | `compound_cbc` | `compound_minor` | `cbc-general-ja`（`CBC`）/ `cbc-liquid-ja`（`CBC リキッド`） | **未収集**（run 0） |
| CBDV | `compound_cbdv` | `compound_minor` | `cbdv-general-ja`（`CBDV`）/ `cbdv-liquid-ja`（`CBDV リキッド`） | **未収集**（run 0） |

- 両 concept は `skos:exactMatch`（CBC = `wikidata:Q422441`、CBDV = `wikidata:Q422426`）を既に持つ。
  今回の変更で taxonomy・IPTC 対応・data dictionary を触っていない（既登録のため）。
- **未収集は 0 観測でも欠測でもない。** raw run・adopted run・staging declaration はいずれも 0 件で、
  `data-catalog.json` にも追加していない。
- 表記ゆれ（`CBCリキッド` 等）は `query-variants.json` に登録していない。variant は観測された表記の
  記録であり（`THCO` の前例）、run の無い語の表記を先に作らない。

## 保留した 13 語と、必要な確認事項

保留の規則は依頼条件と `ISS-20261015-TAX-027` の gate に従う。すなわち「名称の根拠」「route/由来配置の根拠」
「外部識別子の検証」のいずれも無い語は登録しない。**推測で `compound_*` を作らない。**

| 語 | リポジトリ内の既存言及 | 登録に必要な確認事項 |
|---|---|---|
| `THCP` | taxonomy の `compound_rare` scopeNote の例示名、`ISS-20261015-TAX-027` の「登録しない」判断、COA パネルの ND 記録のみ | `ISS-20261015-TAX-027` の判断を覆す根拠（収集 run 又は文書化された名称・分類根拠）、外部識別子の検証 |
| `THCB` | 0 件（画像バイナリの部分一致のみ） | 名称・化学クラス・route 配置の文書化された根拠、外部識別子（CAS / ChEBI / PubChem / Wikidata）の検証 |
| `THCJD` | 0 件 | 同上。`JD` が何を指す略号かの確認（類推しない） |
| `THCPO` | 0 件 | 同上。`THCP` のアセテート体か別骨格かの確認（類推しない） |
| `CBE` | 部分一致のノイズのみ（語としての言及 0 件） | 同上 |
| `HHCPO` | 0 件 | 同上。`HHCP` のアセテート体か別骨格かの確認 |
| `CBND` | 0 件 | 同上 |
| `CBL` | 0 件（画像バイナリの部分一致のみ） | 同上 |
| `CBGa` | 0 件（`cbx-social-trends` の YouTube タイトル内 `#cbgamer` の部分一致のみ） | まず `CBGa` が何を指すか（酸性体の表記と解されるがリポジトリ内の証拠は無い）を確認し、既存 `compound_cbg` との関係（別概念 / 下位 / 別名）を決める taxonomy 判断と根拠 |
| `CBP` | 0 件（画像バイナリの部分一致のみ） | 名称・route 配置の文書化された根拠、外部識別子の検証 |
| `10-OH-HHC` | 0 件 | `compound_hhc` との関係（別概念か誘導体か）の判断と根拠 |
| `THXE` | 0 件 | 略号の展開（何の化合物を指すか）の確認。展開が確認できるまで ID を作らない |
| `THCA` | `research/regulatory-status/{CBD,CBG,CBX}.md` の測定基準「Δ9-THC + Δ9-THCA-A」のみ（化合物概念としては未登録） | まず `THCA` が何を指すか（酸性体・Δ9 体・総称のどれか）を確認し、既存 `compound_thc` との関係を決める taxonomy 判断と根拠 |

- 知識グラフ（`metadata/taxonomy/thc-regulatory-knowledge-graph.json`）は THC の位置異性体・立体異性体の
  規制整理であり、上記 13 語の `compound_*` 概念を持たない。ここから ID を導かない。
- **YouTube primary（`<compound> リキッド`）は canonical identity が確定してから登録する**（依頼条件）。
  保留語には `-liquid-ja` query も作っていない。

## 未収集・未採用・未公開の状態

- 追加した 4 query はいずれも **run 0**。Google Trends / YouTube / X のいずれでも実行していない。
- X のクエリは CBC・CBDV とも設計していない（本研究の X 収集は 7 化合物に限られる）。
- `make audit-youtube-coverage` は `compound_cbc` / `compound_cbdv` を `missing_compounds` として報告する
  （`missing` は「採用済み run が無い」であり、0 観測ではない）。
- `query-design.json` の Google Trends 共通スケールは「registry の active な `compound_general` が対象」を
  正本とするため、CBC・CBDV は 3 policy の被覆で `missing` と報告される（収集していないため）。
  **除外（`excluded_compound_ids`）には入れていない**: 比較集合から外す決定ではなく、単に未収集だから。
- release slice（`cannabinoid-platform-trends`）は広げていない。公開ページ・Zenodo・DOI への変更もない。

## 解消条件

- [ ] 依頼文の「17 物質」と列挙 15 語の差（2 語）の確認
- [ ] 保留 13 語それぞれについて「登録する / 登録しない」の判断と根拠の記録（TAX-027 gate）
- [ ] 登録した 2 化合物を収集する場合: 計画書・窓・staging declaration・L1 gate・採用（別作業）
- [x] 登録 2 語の query 登録と未収集状態の宣言（2026-11-10）
- [ ] 収集した時点で README / methodology の被覆表と catalog を更新

## 出所

- 2026-11-10 のスレッド依頼（物質名の列挙。URL は使用しない方針）。
- リポジトリ内: `metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_cbc` / `compound_cbdv`）、
  `metadata/taxonomy/thc-regulatory-knowledge-graph.json`、`metadata/queries/query-registry.json`、
  `research/regulatory-status/`（THCA-A の測定基準記載）。
- 外部レジストリ（ChEBI / PubChem / CAS / Wikidata）の照会は今回行っていない。
