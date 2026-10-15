# Issue: 化学クラスと製造経路クラスの 2 語彙が併存している

**ID:** ISS-20261015-TAX-026
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/taxonomy/content-taxonomy.skos.jsonld`, `docs/specs/validation-framework.md` §23.4

## 概要

taxonomy は**製造経路**（半合成・水素化等）で分類しているが、研究文書側には**化学クラス**
（水素化カンナビノイド等）の語彙が併存している。同じ概念が 2 通りのクラスで表現され得る。

## 確認された観測

- `compound-taxonomy.skos.jsonld` の 6 カテゴリは製造経路ベース。
- §23.4 に「化学クラスを taxonomy の第 2 次元として持つか、研究文書側の語彙として残すかは
  未判断」と記載。

## 影響

- 分類結果の再現性・移植性が下がる（同じ化合物が経路によって別クラスになり得る）。
- 外部標準（IPTC / ChEBI / Wikidata）との対応付けの基準が曖昧になる。

## 対応方針

- (a) 化学クラスを taxonomy の第 2 次元として持つ、(b) 研究文書側の語彙に寄せる、の選択。
- 判断後、SKOS の構造と `iptc-mapping.yaml` の対応を整合させる。
- 既存の分類済みデータへの影響を確認する。

## 完了条件

- [x] 判断と理由の記録
- [x] taxonomy / mapping の更新と整合テスト
- [x] 既存分類データへの影響確認

## 対応記録（2026-10-15）

### 判断と理由

- オーナー選択肢 **(a)「化学クラスを taxonomy の第 2 次元として持つ」**を採用。
- 理由: 製造経路（半合成・合成等）は市場・規制の実態を反映する安定した第 1 次元であり、
  研究文書側の化学クラス語彙（水素化カンナビノイド等）を taxonomy に取り込むことで、
  HHC（経路=半合成、化学クラス=水素化）や HHCH（経路=合成、化学クラス=水素化）のような
  「同じ化学クラスに属し経路が異なる」関係を機械可読に保てる。(b) 研究文書側への寄せでは
  この関係が文書散在のまま残り、再現性・移植性の課題が解消しない。

### taxonomy / mapping の更新

- 新設 `metadata/taxonomy/chemical-class-taxonomy.skos.jsonld`（`jptr:chemical-class-taxonomy`）:
  `chemclass_hydrogenated`（HHC・HHCH・H4CBH・HHBD）と `chemclass_acetate`（THC-O のみ）。
  根拠は研究サマリーのカテゴリ列と各化合物の scopeNote。結合は対称 `skos:related` のみで、
  `skos:broader` / `skos:narrower` は次元を跨がない（notation も `chemclass_*` で分離）。
- `compound-taxonomy.skos.jsonld` の route 配置は不変。変更は `skos:related` 5 件の追加と
  半合成カテゴリ・THC-O の scopeNote への第 2 次元への言及のみ。
- 形式化しなかったもの: CRDP / CRDH の「ヒドロキシ酸類似体」（両概念の scopeNote が化学構造不明と
  記録しており矛盾するため不採用）、その他の化合物の化学クラス（文書化された語彙が無いため未形式化）。
  リンク無しは「未形式化」を意味し、「化学的実体が無い」ではない。
- `iptc-mapping.yaml`（1.0.0 → 1.1.0）: 化学クラス 2 概念を `not_applicable` として宣言。
  IPTC Media Topics はニュース主題語彙であり化学構造クラスを持たないため、推測で対応付けない。
- `docs/data-dictionary.md` §6.5 に第 2 次元の写しを追加。`docs/specs/validation-framework.md` §23.4 の
  「未判断」を判断済みに更新。`research/.../20261004-google-trends-compound-summary.md` の注記に
  第 2 次元への参照を追加（数値・観測の書き換えなし）。

### 既存分類データへの影響確認

- 変更不要。`methodology.md` の対象化合物表は route カテゴリを使用（不変）、
  `query-registry.json`・`platform_coverage.csv`・`trend_observations.csv` の `compound_*` 参照は
  全て解決可能（`compound_general` は query の `intent_id` 値であり taxonomy 参照ではない）。
  `classification-rules.yaml` は content 分類用で無関係。生データへの編集なし。

### 整合テスト

- 新規 `tests/validation/test_chemical_class_dimension.py`（7 件）: 次元の分離、所属の厳密一致と対称性、
  route 配置の不変、IPTC 非対応宣言、§6.5 写しの一致。
- 既存 `test_taxonomy_consistency.py` を 3 ファイル構成に更新（概念総数 40、export 2 件追加）。
- `pytest` 対象テスト 41 passed、`audit-issues` failures=0、`validate-registries` 全 OK、`git diff --check` OK。
- `exports/taxonomy/` を再生成し、CI の export 同期検査対象に新ファイル 2 件を追加。

### 残課題（本 issue の範囲外・別管理）

- 研究サマリー詳細節の THCH 行が「ヘキサカンナビノール類」のまま（表はマイナーに修正済み）。観測値ではなく
  ラベル表記の残存であり、本 issue の taxonomy 変更では触らない。
- CRDP / CRDH の化学クラスは化学構造の証拠が得られるまで未形式のまま。
- `compound_rare` の会員登録は ISS-20261015-TAX-027 の範囲。
