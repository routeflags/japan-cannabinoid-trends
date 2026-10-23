# G7 Study Inventory（§16）— 既存 Study の非破壊監査

**日付:** 2026-10-13  
**仕様:** `docs/plans/20261013g.md` §16（ローカル計画書。履歴外）  
**機械可読版:** [`g7-study-inventory.json`](./g7-study-inventory.json)（再生成: `python -m research.cli --repo-root . --datasets-root datasets audit-studies --output docs/audits/g7-study-inventory.json`）  
**非破壊:** read-only 走査。study ディレクトリの移動・統合・編集なし（P1・P2）。raw・旧 metadata への書込みなし。走査前後の raw sha256 一致（`raw_modified: false`）。

---

## 1. 対象と方法

- 対象: `datasets/` 直下の 9 study ディレクトリ。
- study ごとの事実は観測ファイルからのみ取得: `README.md`（表題・研究質問は引用のみ）・`methodology.md` 有無・`run_metadata.json` 件数・`data/` 配下ファイル件数・research catalog の索引（compound/query/timeframe/measurement/window）。
- 未登録 study は「未登録」として報告し、自動登録しない。`derived_from` の推測補完なし。
- 実測値: raw ファイル **101 件**（`data/raw` 配下）を走査前後で sha256 ハッシュ化。一致を確認。

## 2. 一覧

| study_id | 登録 | runs | data ファイル | data/raw | README | methodology | sources（catalog 索引） | compounds（索引） |
|---|---|---|---|---|---|---|---|---|
| `cannabinoid-raw-collection` | ✅ | 25 | 86 | 84 | ✅ | ✅ | google-trends | compound_cbd, compound_cbx, compound_crdp, compound_hhc |
| `cbx-search-trends` | ✅ | 4 | 15 | 15 | ✅ | ✅ | google-trends | compound_cbd, compound_cbx |
| `cannabinoid-social-trends` | ❌ | 0 | 0 | — | ✅ | ✅ | — | — |
| `cbx-liquid-online-trend` | ❌ | 0 | 2 | — | ✅ | ✅ | — | — |
| `cbx-product-coa` | ❌ | 0 | 0 | — | ✅ | — | — | — |
| `cbx-social-trends` | ❌ | 0 | 7 | 1 | ✅ | ✅ | — | — |
| `x-26week-trends` | ❌ | 0 | 2 | 1 | ✅ | ✅ | — | — |
| `x-consistency` | ❌ | 0 | 1 | — | ✅ | — | — | — |
| `youtube-consistency` | ❌ | 0 | 1 | — | ✅ | — | — | — |

- runs は `run_metadata.json` の件数（G1 以前の study は別レイアウトのため 0。欠落ではなく規約前の形式）。

> **2026-10-13 注記（鮮度）:** 上の表の「登録」はこのスライス時点の記録（2 study）。その後
> `metadata/studies/study-registry.json` に全 9 study を登録し、同日に JSON を再生成した。
> **現在は全 study が `registered: true`。** 現在の状態は JSON を参照すること。本 `.md` は
> 日付付きの記録として残し、自動検証の対象外としている。
- compounds は query-registry への**完全一致**で索引化できたもののみ。一致しない term は索引化しない（推測なし）。
- 全 study の境界は不変。巨大データセットへの統合なし。

## 3. 所見（破壊的変更なし・判断は親へ）

1. **study_id を持たない run が 3 件**: `20261005T100000Z-google-trends-common-scale-expansion`、`20261008T093228Z-google-trends-5y-baseline`、`common-scale-missing-20261009`（いずれも `datasets/cannabinoid-raw-collection/` 配下だが `study_id` フィールドなし）。catalog は `study_id: null` で索引化。P7 により補完しない。登録・補完の要否は親判断。
2. **THC / CBG 等の term が compound に索引化されない**: query-registry に単体クエリ（例: `THC`）が未登録のため `no_match`。catalog は空のまま（推測で対応付けない）。必要なら G2 側で query-registry 拡充後に再生成する。
3. **未登録 7 study の run が将来 strict 検証で `REFERENCE_STUDY_UNREGISTERED` になる**: G7-T02 の意図どおりの契約動作。登録は study ごとに README ベースで段階追加する（本スライスは 2 study）。
4. **coverage は全 study で `unevidenced`**（G3 manifest なし）。comparable 判定の上限が conditional である根拠のひとつ。
5. **公開状態は全件 `private_by_default`**（承認なし）。公開はしない。

## 4. 横断の重なりと代表ペア判定（発見 ≠ 比較可能性）

- 化合物の重なり（索引レベル）: `compound_cbd` と `compound_cbx` が 2 study にまたがる。
- 代表ペア判定（`representative_pair_verdicts` 参照）: いずれも `conditional`（レビュー条件付き）または `not_comparable`。`comparable` はなし。
- 詳細な判定例は research view の `comparability-report.json`（`research_views/cbd-rikiddo-gt-weekly-parallel/`）を参照。

## 5. 非破壊の証跡

- `raw_modified: false`（走査前後 101 件の sha256 一致。結合ダイジェストは JSON 側に記録）。
- 本ファイル・JSON 以外の書込みなし。`git add` なし（親が検証してコミット）。
