# Issue: 候補形式 27 形式の検索トピック登録 — 概念・canonical query・未収集の明示

**ID:** ISS-20261115-TAX-045
**優先度:** P2 (Medium)
**ステータス:** OPEN
**実装状態:** 登録変更はローカル scope-split commit 済み。owner review pending、未push。
**対象:** `datasets/cannabinoid-raw-collection/README.md`（形式辞書・crosswalk・登録バッチ節・term-to-query map・被覆表）、
`metadata/taxonomy/compound-taxonomy.skos.jsonld`（27 概念と管理カテゴリの scopeNote）、
`metadata/queries/query-registry.json`（54 canonical query）、
`metadata/taxonomy/iptc-mapping.yaml`（deliberately_unmapped の新群・件数）、
`exports/taxonomy/*`（再生成）、
`docs/data-dictionary.md` §6.4、`docs/provenance/compound-taxonomy.md`、`docs/provenance/query-inventory.md`、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`、`project.json`（`queryDesign.compounds`）、
`metadata/provenance/evidence-registry.json`、`docs/audits/g6-git-tracking-inventory.json`、
`tests/validation/test_candidate_form_registration.py`（新規）ほか登録件数を固定するテスト
**関連:** `ISS-20261115-TAX-044`（候補表の作成と精度基準。本 issue がその 27 行を登録する）、
`ISS-20261111-TAX-042`（異性体別根拠レビュー）、`ISS-20261115-TAX-043`（外部識別子 crosswalk）、
`ISS-20261111-TAX-041`（THCA / THCB の個別検索トピック登録の先例）、
`ISS-20261111-TAX-040`（管理カテゴリ `compound_identity_unverified` の新設）

## 概要

2026-11-15、owner は `datasets/cannabinoid-raw-collection/README.md` の
「未登録・未収集の候補形式」に棚卸しした **27 行を検索トピックとして登録すること**を明示した。本 issue はその登録を記録する。

**登録は検索文字列の固定であり、収集・採用・公開・release の許可ではない。** 本 issue は raw data、run metadata、
catalog、collection declaration、source coverage observation、release slice、公開状態を変更していない。scope split のローカル commit は作成済みだが、push・公開・release は行っていない。

登録対象は候補表の 27 行そのものであり、行の追加・削除・言い換えはしていない。

## 決定したこと

1. **候補表の 27 行を登録した。** 内訳は (a) THC の位置異性体 6 形式、(b) THCP / THCJD / THCPO /
   THCB-O-acetate / THCH / THCV の個別異性体と `THCJD-O-acetate`（異性体未指定）の 13 形式、(c) HHC の
   立体異性体 8 形式（`9(R)-HHC` / `9(S)-HHC` と WHO が示す他の 6 配置）。6 + 13 + 8 = 27 である。各行は 1 つの taxonomy
   concept と 2 本の canonical query（`<term>` = `compound_general`、`<term> リキッド` = `product_liquid`、
   いずれも `active`）を持つ。
2. **配置は管理カテゴリ。** 27 概念は `jptr:compound-identity-unverified` に置き、カテゴリの
   `skos:scopeNote` に「配置ごとの registry record も製品同定も無い特定の立体配置」と「個々の位置異性体の
   構造を列挙していない異性体未指定アセテート」の 2 ケースを追加した。配置は経路／由来、天然存在、
   化学クラス、構造、別名、規制状態を主張しない。
3. **識別子は概念に付けない。** 先行レビューが記録した registry record（PubChem CID・CAS・UNII・ChEBI・
   Wikidata）は `docs/provenance/compound-taxonomy.md` に保持し、**本変更では外部 registry に対して
   再検証していない**ため概念には付けない。不在の断定ではない。`skos:related` も張らず、棚卸し上の親語
   との関係は整理上の対応であることを各 scopeNote に記す。
4. **証拠の種類を混ぜない。** registry record、法令の構造グループ（令和6年厚生労働省令第81号の別紙、
   消費者庁の THCH 指定薬物資料）、命名標準と知識グラフ、WHO 47th ECDD (2024) §2C の可能な配置の
   レビュー、製品分析（文献）を区別した。**法令の構造グループ該当は製品検出ではなく、WHO のレビューは
   配置ごとの registry record でも製品同定でもない。**
5. **`THCJD-O-acetate` は異性体未指定のまま登録した。** Δ8 / Δ9 の別個の構造は本リポジトリで確認して
   おらず、本変更で分割しない。
6. **既存の query / run の割当ては不変。** 総称 `THC` / `THCA` / `THCB`、ファミリー `THCP` / `THCJD` /
   `THCPO` / `THCB-O-acetate` / `THCV` / `THCH` / `HHC` の query ID・canonical_text・status・run は
   変更せず、総称 `THC` の series をどの位置異性体へも帰属させない。既存 75 本の general+liquid query は
   すべて `active` のまま。
7. **未収集を明示した。** 27 語はいずれも run を持たない。README の term-to-query map は各行に
   「未収集」を記し、登録バッチ節にも run が無いことを明記した。**0 観測でも欠測でも収集失敗でもない。**

## 登録した 27 語（term / concept / query base）

| # | 検索語（canonical_text） | `compound_id` | query ID base |
|---|---|---|---|
| 1 | `Δ8-THCP` | `compound_delta8_thcp` | `delta8-thcp` |
| 2 | `Δ9-THCP` | `compound_delta9_thcp` | `delta9-thcp` |
| 3 | `Δ8-THCJD` | `compound_delta8_thcjd` | `delta8-thcjd` |
| 4 | `Δ9-THCJD` | `compound_delta9_thcjd` | `delta9-thcjd` |
| 5 | `Δ8-THCP-O-acetate` | `compound_delta8_thcp_o_acetate` | `delta8-thcp-o-acetate` |
| 6 | `Δ9-THCP-O-acetate` | `compound_delta9_thcp_o_acetate` | `delta9-thcp-o-acetate` |
| 7 | `Δ8-THCB-O-acetate` | `compound_delta8_thcb_o_acetate` | `delta8-thcb-o-acetate` |
| 8 | `Δ9-THCB-O-acetate` | `compound_delta9_thcb_o_acetate` | `delta9-thcb-o-acetate` |
| 9 | `Δ8-THC` | `compound_delta8_thc` | `delta8-thc` |
| 10 | `Δ6a(10a)-THC` | `compound_delta6a_10a_thc` | `delta6a-10a-thc` |
| 11 | `Δ6a(7)-THC` | `compound_delta6a_7_thc` | `delta6a-7-thc` |
| 12 | `Δ7-THC` | `compound_delta7_thc` | `delta7-thc` |
| 13 | `Δ10-THC` | `compound_delta10_thc` | `delta10-thc` |
| 14 | `Δ9(11)-THC` | `compound_delta9_11_thc` | `delta9-11-thc` |
| 15 | `Δ9-THCV` | `compound_delta9_thcv` | `delta9-thcv` |
| 16 | `Δ8-THCV` | `compound_delta8_thcv` | `delta8-thcv` |
| 17 | `THCJD-O-acetate` | `compound_thcjd_o_acetate` | `thcjd-o-acetate` |
| 18 | `Δ8-THCH` | `compound_delta8_thch` | `delta8-thch` |
| 19 | `Δ9-THCH` | `compound_delta9_thch` | `delta9-thch` |
| 20 | `9(R)-HHC` | `compound_9_r_hhc` | `9r-hhc` |
| 21 | `9(S)-HHC` | `compound_9_s_hhc` | `9s-hhc` |
| 22 | `(6aS,9S,10aS)-HHC` | `compound_6as_9s_10as_hhc` | `6as-9s-10as-hhc` |
| 23 | `(6aS,9R,10aS)-HHC` | `compound_6as_9r_10as_hhc` | `6as-9r-10as-hhc` |
| 24 | `(6aS,9S,10aR)-HHC` | `compound_6as_9s_10ar_hhc` | `6as-9s-10ar-hhc` |
| 25 | `(6aS,9R,10aR)-HHC` | `compound_6as_9r_10ar_hhc` | `6as-9r-10ar-hhc` |
| 26 | `(6aR,9S,10aS)-HHC` | `compound_6ar_9s_10as_hhc` | `6ar-9s-10as-hhc` |
| 27 | `(6aR,9R,10aS)-HHC` | `compound_6ar_9r_10as_hhc` | `6ar-9r-10as-hhc` |

各 query base に `-general-ja` と `-liquid-ja` を付けた 2 本が登録される（27 × 2 = 54 本）。

## 命名規則

`skos:notation` は `compound_` + 語を小文字化し `Δ`→`delta`、非英数字の**連続**を 1 つの `_` に置換し
前後の `_` を除いたもの。`@id` は notation の `_` を `-` にした `jptr:compound-…`。query ID の slug は
語を小文字化し `Δ`→`delta` としたうえで、既存の 27 語で実際に使った次の規則で作る。

1. 立体配置を囲む先頭の括弧と C-9 エピマーの括弧は外す（`(6aS,9S,10aS)-HHC` → `6as-9s-10as-hhc`、
   `9(R)-HHC` → `9r-hhc`）。
2. 位置番号を囲む括弧は、内側の locant の前に `-` を置く（`Δ6a(10a)-THC` → `delta6a-10a-thc`、
   `Δ6a(7)-THC` → `delta6a-7-thc`、`Δ9(11)-THC` → `delta9-11-thc`）。
3. `,` と既存の `-` は `-` とし、連続する `-` を 1 つに畳み、前後の `-` を除く。既存のハイフンは
   保持する（`Δ8-THCP-O-acetate` → `delta8-thcp-o-acetate`）。

これに `-general-ja` / `-liquid-ja` を付ける。既存の `compound_delta9_thca_a` / `compound_10_oh_hhc` /
`compound_thc_o` と同じく、notation 側の連続置換の明示だけを明確化した（`Δ6a(10a)-THC` で二重 `_` を
作らない）。**既存の安定した query ID は改名しない。**

## 被覆・比較設計への影響

- **Google Trends** の分母は 36 → 63 語。新規 27 語は 5年・12ヶ月とも 0/27（**未収集**）。
- **YouTube** の required primary は 37 → **64 本**。30 本に adopted run があり、未被覆は
  `thca-liquid-ja` の `NO_VIDEOS`、6 検索トピックの 6 本、本バッチの 27 本（計 34 本）。
  `audit-youtube-coverage` は `compounds=29/63`、`queries=30/64`、`missing_compounds=34` を報告する。
- **共通スケール policy**（5年・12ヶ月・3ヶ月）は、27 本の active `compound_general` により required 集合が
  それぞれ 27 件増え、本バッチで **81 件**の設計上の required entry が加わる。既存 6 検索トピックの 18 件と
  合わせた**累積 99 件**は、policy ごとの有効な general 化合物の総数ではない（各 policy は既存 6 語 + 新規 27 語ずつ増える）。
  policy 数は 3 のままで、`excluded_compound_ids` に 27 語を加えていない（除外で欠測を隠さない）。
- **X（Twitter）** は 27 語のクエリを設計していない（`X 設計外`）。`project.json` の `queryDesign.compounds` も、この 27 形式（既存の `Δ8-THC` を含む）に `x` 宣言を持たない。既存の 7 化合物（CBD・THC・CBG・HHC・THCV・THC-O・THCH）の X 設計は変更していない。

## 変更した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`: 27 概念の追加、管理カテゴリの `skos:narrower` 43 件化、
  同カテゴリ `skos:scopeNote`（en/ja）への 2 ケース追記。27 概念とカテゴリの scopeNote は、識別子プロパティも
  `skos:exactMatch` も割り当てないことを明示し、注記に引用した識別子値は台帳の記録であって概念の識別子ではないと
  書き分けた（値は削除せず、`exactMatch` にも変換しない）。
- `metadata/queries/query-registry.json`: 54 canonical query の追加（active、run なし）。
- `metadata/taxonomy/iptc-mapping.yaml`: `deliberately_unmapped` への新群 27 概念（理由つき）、
  coverage 件数（compound 45→72、全体 61→88、末端 52→79、未対応 28→55）、version 1.10.0→1.11.0。
- `exports/taxonomy/*`: `bash scripts/export/export-taxonomy.sh` で再生成（hand-edit なし）。
- `docs/data-dictionary.md` §6.4: 管理カテゴリの成员 43 件と注記。
- `docs/provenance/compound-taxonomy.md`: 本変更の節（命名規則、配置、形式ごとの根拠と限界、
  識別子の所在、非主張、未決事項）。
- `docs/provenance/query-inventory.md`: 54 行の追加、件数 76→130、版 1.7.8。
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`: `registration_basis` 1 群（27 語、
  `identity_state: compound_identity_unverified`）と `identity_caveat` の追記。**run state は追加していない。**
- `datasets/cannabinoid-raw-collection/README.md`: 概要・登録数 63、構造形式辞書 40 行（26 形式を追加）、
  crosswalk 63 行、登録バッチ節（27 行・未収集）、辞書全体の注記、term-to-query map 63 行、被覆表
  （27 行分の未収集行と分母 63・required 64）、収集したキーワード、関連。
- `datasets/cannabinoid-raw-collection/methodology.md`: 登録語数と required primary の件数、63 トピックの registered-topic/query/coverage 表（canonical general/liquid、未収集、X 設計外）、12ヶ月分子の既知限界。
- `datasets/cannabinoid-raw-collection/data/README.md` と `data/raw/google_trends/README.md`: 登録 63 トピック・required 64 本・未被覆 34 本への現行件数整合。
- `project.json`: `queryDesign.compounds` に 26 件追加、既存 `Δ8-THC` に `identityNote` / `note` を追加、27 形式（`Δ8-THC` を含む）から `x` 宣言を削除、`lastUpdated`。`japaneseName` は確認済みの和名がある場合を除き登録語そのもの（`Δ8-THCA` の先例）。
- `metadata/provenance/evidence-registry.json`: `ev-compound-taxonomy` / `ev-query-registry` の新 hash・
  `observed_at` と、既存 note への追記（過去 hash は改変しない）。
- `docs/audits/g4-storage-inventory.json`: 変更した 2 つの data README の hash を再生成で更新。
- `docs/audits/g6-git-tracking-inventory.json`: README・methodology・query-design・data README 2 件の tracked hash を更新した。checkout-local な `count` / `extra_count` / `state_summary` / `extras` は再生成していない。
- テスト: `tests/validation/test_candidate_form_registration.py`（新規、27 語の identity・query・未収集・
  既存保持を固定）、`test_dictionary_form_precision.py`（行数と登録済み状態へ更新）、
  `test_taxonomy_consistency.py`（export 72）、`test_compound_rare_membership.py`（管理カテゴリの成员）、
  `test_registration_state_batch.py`（design の registration_basis）。

## 変更しないもの

- raw data、run metadata、`metadata/data-catalog.json`、`metadata/provenance/declarations/`、
  source coverage observation、release slice、公開状態。
- 既存 query の ID / canonical_text / status / run 割当て、`query-variants.json`（variant を pre-create しない）。
- 既存概念の label・notation・分類・`exactMatch`、`compound_rare`（空のまま）、`compound_cbdp`（未登録）。
- `ISS-20261115-TAX-043` の crosswalk 修正とそのテスト。

## 未決事項

1. **管理カテゴリからの移動**: 27 概念はいずれも単一の検証済み外部レコードを選択していない。
   `Δ9-THCV` / `Δ9-THCP` / `9(R)-HHC` / `9(S)-HHC` などに識別子を付けるかは別作業である（live registry の再検証が必要）。
2. **`THCJD-O-acetate` の Δ8/Δ9 分割**: 法令の別個の構造が確認できれば分割できるが、owner の追加判断を要する。
3. **`Δ8` エステル体の製品分析証拠**（`Δ8-THCP-O-acetate` / `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate`）は未確認。
4. **収集**: 27 語はいずれも未収集であり、収集には別の owner 承認を要する。
5. **`project.json` mirror の既知の不一致**: `CBX` は registry にあるが mirror に無い（本変更では触れていない）。

## 検証

```sh
bash scripts/export/export-taxonomy.sh
.venv/bin/python -m pytest -q tests/            # 1736 passed, 4 skipped, 10 failed（checkout-local raw と committed audit snapshots の retained-view mismatch）
make gates GATE=registries                     # valid (18 targets)
make gates GATE=comparison                     # OK, policies=3, failures=0
make audit-raw-completeness
make audit-raw-retention
make audit-youtube-coverage
make audit-comparison-scale
make audit-distribution-scope
git diff --check
```

raw payload / run metadata の可視性は checkout-local である。この checkout では Git 非追跡の追加 run metadata が見えるため、committed audit snapshots の retained view と freshness tests が一致しない。**その状態を 0 観測として扱わない。** ローカル run を公開・採用する代わりに snapshot を再生成せず、`docs/audits/**` の run-derived data を変更していない。

`docs/audits/g6-git-tracking-inventory.json` の tracked-entry hashes は変更した 5 ファイルに合わせて更新し、
checkout-local の件数・extras・state summary は更新前の記録を保持した。freshness 比較は tracked-entry hashes を検証し、
checkout-local fields は比較対象から除外する。

## 出所

- 2026-11-15 の owner 指示（候補表 27 行の検索トピック登録。収集・公開・commit は許可しない）。
- リポジトリ内: `datasets/cannabinoid-raw-collection/README.md`（候補表 27 行）、`ISS-20261115-TAX-044`、
  `ISS-20261111-TAX-042`、`ISS-20261115-TAX-043`、`metadata/taxonomy/compound-taxonomy.skos.jsonld`、
  `metadata/queries/query-registry.json`、`docs/specs/thc-nomenclature-standard.md`、
  `metadata/taxonomy/thc-regulatory-knowledge-graph.json`、`research/regulatory-status/THCH.md`、
  `research/regulatory-status/THCV.md`、`research/regulatory-status/HHC.md`。
- 外部（先行レビューの記録であり、本変更では再照会していない）: 令和6年厚生労働省令第81号の別紙、
  消費者庁の THCH 指定薬物資料、WHO 47th ECDD (2024) critical review §2C、Tanaka & Kikura-Hanajiri 2024
  （DOI 10.1248/yakushi.24-00029）、Linciano et al. 2020（DOI 10.1021/acs.jnatprod.9b00876）、
  Citti et al. 2019、Tanaka et al. 2025（DOI 10.1002/dta.3883）、ChEBI / Wikidata / PubChem の記録。
