# Query Inventory（クエリ証拠台帳）

**版:** 1.0.0（2026-10-13）
**目的:** G2 垂直スライスで `metadata/queries/` に登録したクエリ・表記ゆれ・除外
規則の**証拠台帳**（G1 §18 Phase 1 の collector-inventory.md のクエリ版）。登録は
「実 run の記録」または「既存 keywords.yaml / taxonomy」に基づき、推測の語彙は
書かない（b.md P5）。

---

## 1. 登録済みクエリ（`query-registry.json`、7 件）

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

注: 判別クエリ（`CBX 大麻` / `CBX カンナビノイド`）の intent は compound_general
（検索意図は CBX という成分の理解であり、判別語による修飾は platform 構文ではなく
表記の一部）。

## 2. 表記ゆれ（`query-variants.json`、3 sets）

| query_id | variant_id | text | status | 証拠 |
|---|---|---|---|---|
| `cbd-general-ja` | cbd-general-primary | CBD | primary | registry canonical と一致（機械検証） |
| `cbd-general-ja` | cbd-general-en | Cannabidiol | alternative | taxonomy prefLabel（en）/ b.md §9.2 |
| `cbd-general-ja` | cbd-general-kana | カンナビジオール | alternative | taxonomy altLabel（ja） |
| `cbd-liquid-ja` | cbd-liquid-primary | CBD リキッド | primary | registry canonical と一致（機械検証） |
| `cbd-liquid-ja` | cbd-liquid-nospace | CBDリキッド | alternative | 20261012T054920Z（notation-presurvey が両表記を比較） |
| `cbx-liquid-ja` | cbx-liquid-primary | CBX リキッド | primary | registry canonical と一致（機械検証） |
| `cbx-liquid-ja` | cbx-liquid-nospace | CBXリキッド | alternative | keywords.yaml search_queries.tiktok.primary.keyword |

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

- 登録範囲は「compound-taxonomy に概念があり、29 run の記録または keywords.yaml
  に実在する」ものに限定（J3）。他成分の実クエリは
  `docs/audits/g2-query-inventory.json` で対応状態を管理し、未登録のまま自動採用
  しない（状態 `unmapped` / `ambiguous` / `semantic_match_candidate`）。
- taxonomy に概念がない成分（THC-O / THCH / CRDP / HHC / HHCH — 29 run で使用
  実績あり）は notation を参照できないため登録しない（taxonomy 側の追加が先）。
- `keywords.yaml` のみに存在し run 実績がない語（例 `CBX オイル` / `CBD ペン`）は
  候補として保留（推測で intent を確定しない）。
- 除外規則は本表に載るフレーズのみ。根拠のない語は追加しない。
