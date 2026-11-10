# Query Inventory（クエリ証拠台帳）

**版:** 1.6.0（2026-11-10）
**目的:** G2 垂直スライスで `metadata/queries/` に登録したクエリ・表記ゆれ・除外
規則の**証拠台帳**（G1 §18 Phase 1 の collector-inventory.md のクエリ版）。登録は
「実 run の記録」または「既存 keywords.yaml / taxonomy」に基づき、推測の語彙は
書かない（b.md P5）。

---

## 1. 登録済みクエリ（`query-registry.json` の化合物語 38 件。`other` intent の比較セットは本表に含めない）

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
| `cbc-general-ja` | `compound_cbc` | compound_general | CBC | active | **run なし**。taxonomy の既存概念 `compound_cbc`（`compound_minor`、`wikidata:Q422441`）を根拠に 2026-11-10 に登録（ISS-20261110-TAX-039）。未収集であり 0 観測ではない |
| `cbc-liquid-ja` | `compound_cbc` | product_liquid | CBC リキッド | active | **run なし**。同上。`datasets/cannabinoid-raw-collection/metadata/query-design.json` の required primary query だが、宣言済み未収集 |
| `cbdv-general-ja` | `compound_cbdv` | compound_general | CBDV | active | **run なし**。taxonomy の既存概念 `compound_cbdv`（`compound_minor`、`wikidata:Q422426`）を根拠に 2026-11-10 に登録（ISS-20261110-TAX-039）。未収集であり 0 観測ではない |
| `cbdv-liquid-ja` | `compound_cbdv` | product_liquid | CBDV リキッド | active | **run なし**。同上。required primary query だが、宣言済み未収集 |

注（2026-10-13 追加分・表の下 10 行）: 下の5化合物は taxonomy に概念が無かったため登録
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
  variant への自動昇格はしない（人手レビューが必要）。taxonomy に概念がない成分は
  現時点で存在しない（この study の登録 17 化合物がすべて notation を持つ。
  THCNM・CBC・CBDV を含む。CBC・CBDV は概念だけが既存で、query は 2026-11-10 に
  登録したが run は 0 本）。
- `thcnm-general-ja` / `thcnm-liquid-ja` / `tha-liquid-ja` は**実 run と keywords.yaml のいずれも根拠にせず**登録し、後に収集で実測した語である。
- `cbc-general-ja` / `cbc-liquid-ja` / `cbdv-general-ja` / `cbdv-liquid-ja`（2026-11-10、
  ISS-20261110-TAX-039）は**実 run を根拠にしない**登録である。根拠は taxonomy の既存概念
  （`compound_cbc` / `compound_cbdv`）と owner の対象拡張依頼で、run は 0 本。
  未収集を 0 観測とも欠測とも書かない（`datasets/cannabinoid-raw-collection/metadata/query-design.json`
  の `declared_not_yet_collected`）。
  登録時の根拠は taxonomy の `compound_thcnm` 概念（名称・同一性の根拠は ISS-20261104-TAX-028）と
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
