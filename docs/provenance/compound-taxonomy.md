# Compound Taxonomy — 追加記録と根拠

`metadata/taxonomy/compound-taxonomy.skos.jsonld` の変更履歴と、各概念を追加した根拠を記録する。
タクソノミー本体が正本であり、このファイルは**なぜその値を書いたか**を残すための台帳である。

---

## 2026-10-13 — 収集済みだが未登録だった5化合物を追加

対象: `HHC` / `HHCH` / `THCH` / `THC-O` / `CRDP`。
`datasets/cannabinoid-raw-collection/data/raw/google_trends/` に run が存在するのに
タクソノミーに概念が無く、検証済みクエリレジストリへ登録できない状態だった。

| notation | 配置（broader） | 名称の根拠 | カテゴリの根拠 |
|---|---|---|---|
| `compound_hhc` | `compound-semisynthetic` | `research/regulatory-status/HHC.md`、`project.json` | `methodology.md`、`docs/data-dictionary.md`、EWI CSV、`first-mention-timeline.md` |
| `compound_hhch` | `compound-synthetic` | `research/regulatory-status/HHCH.md` | EWI CSV、`first-mention-timeline.md` |
| `compound_thch` | `compound-minor` | `research/regulatory-status/THCH.md` | `methodology.md`、`docs/data-dictionary.md`、EWI CSV、`first-mention-timeline.md` |
| `compound_thc_o` | `compound-semisynthetic` | `research/regulatory-status/THC-O.md`、`project.json`（別名） | `methodology.md`、`docs/data-dictionary.md`、EWI CSV、`first-mention-timeline.md` |
| `compound_crdp` | `compound-synthetic` | **コードのみ**（`CRDP.md` に「未詳/仮称」と記載） | EWI CSV、`first-mention-timeline.md`、`CRDP.md` |

- `notation` の記法はリポジトリ内の既存規約（`THC-O → compound_thc_o`、`h4cbh`/`hhbd`/`crdh` の小文字化）を適用した。
  `compound_hhc` / `compound_thch` / `compound_thc_o` は `methodology.md` 等に**明文記載あり**。
  `compound_hhch` / `compound_crdp` は記法の適用（明文記載なし）。
- カテゴリは**文書化された分類**を優先した。参考までに、既存の `compound_h4cbh` / `compound_hhbd` は
  タクソノミー上 `compound-minor` だが EWI/timeline は Semi-Synthetic としており、この不一致は**未修正**（下記参照）。

### 意図的に省略したプロパティ

- `skos:exactMatch`（ChEBI / Wikidata）: リポジトリ内に検証済み ID が無い。また HHC/HHCH/THCH/THC-O は
  立体異性体・Δ8/Δ9 体の総称であり、単一の `exactMatch` は混同を招く。**外部 Web 検証は未実施。**
- CAS 番号・IUPAC 名・自然存在性: 既存の化合物概念にこれらのキーが無いため、キー自体を追加していない。
- 規制情報（scopeNote 等）: 根拠は `research/regulatory-status/*.md` にあるが、既存スタイルに前例が無く可変性が高いため見送り。

> **2026-11-04 注記（THC-O）:** PubMed / PubChem / Cayman の外部記録を確認した（下記 2026-11-04 節）。
> それでも `compound_thc_o` に `exactMatch` を付けない判断は変わらない。同じ略号 `THCO` が
> アセテート体と tetrahydrocannabiorcol（Δ8 / Δ9）の双方に使われ、単一の CAS を持たないため。

---

## 修正した既知事項（2026-10-13）

1. ✅ `compound-synthetic` の `skos:narrower` に `compound-crdh` を追加（親子関係の非対称を解消）。
2. ✅ `compound_h4cbh` / `compound_hhbd` を `compound-minor` から `compound-semisynthetic` へ移動。
   根拠: `datasets/cannabinoid-raw-collection/data/processed/early-warning-index-v1.csv`
   の `classification` 列が両方とも `Semi-Synthetic`（`source_run_ids=EXP-20261002`）、
   および `research/google-trends/20261002-first-mention-timeline.md`。
   `docs/data-dictionary.md` §6.4 のカテゴリ表には両者とも掲載が無く、矛盾しない。
   > **2026-10-15 注記:** 上に引用した `early-warning-index-v1.csv` は公開取り下げに
   > なった（`src/processing/reproduce.py` の `WITHDRAWN`）。分類自体は
   > `metadata/taxonomy/compound-taxonomy.skos.jsonld` の `compound_semisynthetic` が
   > 正本で、`docs/data-dictionary.md` §6.4 の写しとの一致を
   > `tests/validation/test_taxonomy_consistency.py` が検査している。
3. ✅ `metadata/datapackage.json` の `skos_scheme` を `jptr:compound-scheme` →
   `jptr:compound-taxonomy` に修正（実在する ConceptScheme の `@id`）。

親子対称性は機械的に確認済み（broader と narrower の非対称 0 件）。

---

## 2026-10-15 — 化学クラスを taxonomy の第 2 次元として形式化（ISS-20261015-TAX-026 判断 (a)）

- 製造経路・由来の次元は `compound-taxonomy.skos.jsonld` に残し、化学クラスは新設の
  `metadata/taxonomy/chemical-class-taxonomy.skos.jsonld`（`jptr:chemical-class-taxonomy`）に置いた。
  結合は対称 `skos:related` のみ。`skos:broader` / `skos:narrower` は次元を跨がない。
- 形式化したのは根拠のある 2 クラスのみ（notation は `chemclass_*` で route 次元と名前空間を分離）:
  - `chemclass_hydrogenated`（水素化カンナビノイド）: `compound_hhc` / `compound_hhch` /
    `compound_h4cbh` / `compound_hhbd`。根拠は `research/google-trends/20261004-google-trends-compound-summary.md`
    のカテゴリ列と `compound-hhc` / `compound-h4cbh` の scopeNote。HHCH は route=合成だが化学クラスは水素化であり、
    この不一致の保持こそ第 2 次元の目的である。
  - `chemclass_acetate`（アセテート体カンナビノイド）: `compound_thc_o` のみ。根拠は同概念の scopeNote
   （semi-synthetic cannabinoid acetate）。
- `compound-taxonomy.skos.jsonld` 側の変更は `skos:related` 5 件の追加と、半合成カテゴリ・THC-O の scopeNote への
  第 2 次元への言及のみ。route の `broader` 配置は不変（既存の分類済みデータへの影響なし）。
- 意図的に形式化しなかったもの:
  - CRDP / CRDH の「ヒドロキシ酸類似体」: 両概念の scopeNote が化学構造不明と記録しており、研究文書側の
    ラベルは記録と矛盾するため不採用。
  - その他の化合物（CBD 等）の化学クラス: リポジトリ内に文書化された語彙が無いため未形式化。リンク無しは
    「化学的実体が無い」ではなく「未形式化」を意味する（scheme の description に明記）。
- `iptc-mapping.yaml` は化学クラス 2 概念を `not_applicable` として宣言（IPTC Media Topics はニュース主題語彙で
  あり化学構造クラスを持たない。推測で対応付けない）。`version` 1.0.0 → 1.1.0。
- 2 次元の分離は `tests/validation/test_chemical_class_dimension.py` が検査し、`docs/data-dictionary.md` §6.5 が
  写しを持つ（`test_taxonomy_consistency.py` の §6.4 と同じ方式）。

## 2026-10-15 — TAX-027判断: `compound_rare` は空のまま維持（ISS-20261015-TAX-027）

- **判断:** `compound_cbdp` / `compound_thcp` を追加しない。`compound_rare` は
  `skos:narrower` を持たない空カテゴリのまま、`skos:scopeNote` の
  「INTENTIONALLY EMPTY」の宣言を維持する。issue は OPEN のまま残す
  （希少化合物の言及が未分類に落ちる課題自体は解消していないため）。
- **確認したリポジトリ内の証拠（2026-10-15、外部照会なし）:**
  - CBDP: `compound-taxonomy.skos.jsonld` の scopeNote の例示名と TAX-027 issue 本文のみ。
    raw run・`query-registry.json`・`project.json` queryDesign・`research/regulatory-status/`
    記録・`metadata/keywords.yaml`・知識グラフのいずれにも存在しない。
  - THCP: 上記に加え、COA パネルの分析対象として ND 記録あり
    （`docs/data-dictionary.md` §4.1、`docs/provenance.md` §5.3、COA 掲載値）および
    汎用スキル内の列挙（`.github/skills/academic-research/SKILL.md`）に言及あり。
    ただし収集 run・query-registry・queryDesign・`regulatory-status/THCP.md` は無く、
    COA の ND は当該検体の未検出（`observed_zero` 相当）であって route/由来配置の根拠ではない。
- **見送りの理由:** 2026-10-13 の追加前例（名称の根拠＋カテゴリの根拠の両方が必要）に照らし、
  名称・配置のいずれも文書化された根拠が無い。追加には日中ラベル・`exactMatch`
  （ChEBI / Wikidata）・IPTC 対応・クエリの創作が必要になり、リポジトリ規則
  （推測での対応付け禁止、外部 ID の捏造禁止）に反する。
- **追加の gate（将来 CBDP / THCP 等を登録する場合の条件）:**
  1. 収集 run（`data/raw/<source>/<run-id>/`）又は `staging-declaration-v1` 採用による観測、
     もしくは `research/regulatory-status/` 等の文書化された名称の根拠。
  2. route/由来配置（希少フィトカンナビノイド等）の文書化された根拠。
     化学クラスは別次元（`chemical-class-taxonomy`）で扱い、`skos:broader` では結合しない。
  3. 全層の同時更新: taxonomy concept（notation は既存規約 `compound_*` 小文字化）＋
     `iptc-mapping.yaml` は `deliberately_unmapped`（理由付き。IPTC に化合物単位の主題の
     証拠が無い限り推測で対応付けない）＋ `docs/data-dictionary.md` §6.4 の写し更新 ＋
     収集需要がある場合のみ `query-registry.json` 登録（G2 検証付き）＋本台帳への追記。
     `exactMatch` は検証済み ID がある場合のみ付与し、無い場合は省略する（CBX / H4CBH 前例）。
- **検査:** `tests/validation/test_compound_rare_membership.py` が空・説明付きの状態を固定する。
  将来メンバーを追加する際は本テストを更新し、上記 gate の同時更新を満たすこと。

## 2026-11-04 — `compound_thcnm`（THCNM / 別名 THA）を追加（ISS-20261104-TAX-028）

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| notation | `compound_thcnm` | 既存規約（`THC-O → compound_thc_o`、`h4cbh` / `hhbd` / `crdh` の小文字化）の適用 |
| `@id` | `jptr:compound-thcnm` | 同上 |
| prefLabel | en `THCNM` / ja `THCNM` | H4CBH / HHBD と同じくコード名をそのままラベルにする（確定した化学名が無い） |
| altLabel | `THA`, `Tetrahydrocannabinol-N-methyl`, `1′-Dimethyl-Δ9-THCH`, `THCNM リキッド`, `THA リキッド` | 2 つの名称形式は出所の記載をそのまま記録したもので、どちらが正しいかを決めていない |
| `skos:broader` | `jptr:compound-semisynthetic`（暫定） | 下記「分類の根拠」 |
| `skos:related` | `jptr:compound-thc`, `jptr:compound-thch` | 2 つの名称形式がそれぞれ THC の N-メチル体 / Δ9-THCH のジメチル体を示すため |
| 外部識別子 | **なし**（`exactMatch` を書かない） | CAS / ChEBI / Wikidata / PubChem のいずれもこの同一性について検証された値が無い |
| 化学クラス | **未形式化**（`chemclass` への `skos:related` を書かない） | N-メチル体・ジメチル体というクラスは taxonomy に無く、推測で第 2 次元を作らない |

### 分類の根拠（semisynthetic か synthetic か）

出所の記載は 2 通りに分かれるが、**どちらも「天然カンナビノイドを化学修飾した置換誘導体」**を記述している。

- `Tetrahydrocannabinol-N-methyl`: THC の N-メチル体 → 天然物の修飾体。
- `1′-Dimethyl-Δ9-THCH`: THCH（マイナーなフィトカンナビノイド）のジメチル体 → 天然物の修飾体。

`compound_synthetic` の scopeNote は「天然に対応物を持たない」（HHCH / CRDP / CRDH）を基準にしており、
上記のいずれの記載もこれに当たらない。したがって **route 次元では半合成**に置いた。
ただしこれは同一性が未確認のままの**暫定配置**であり、構造の検証結果ではない。
どちらの記載も誤っていた場合（例: 天然対応物を持たない新規骨格であった場合）は再配置が要る。
この但し書きは concept の scopeNote（en / ja）と `compound_semisynthetic` の scopeNote に書いた。

### 同一性が未確認であることの扱い

- `THA` は**別名・商業名**として記録する。THCNM と同一の物質であるとも、別の物質であるとも書かない。
  国内市場記事（2026-10-28）は供給元の発言として「THA は定義された単一物質の名称ではなく商業名・混合物名」
  と伝えており、この記載は「別名」登録とは両立するが「同一物質の証明」にはならない。
- `THAH`（別の独自ブレンド）との混同を scopeNote で明示的に禁止した。
- 出所の衝突（化学名 2 説、分子式の概算値）と、それを解消する条件は issue に記録した。
  本台帳は決定した値とその理由だけを持ち、未確定の化学データ（CAS・分子式）を値としては持たない。

### 同時に更新した層

`iptc-mapping.yaml`（`compound_mapping` に `mapping_type: none`、IPTC 主題は与えない）、
`docs/data-dictionary.md` §6.4 の写し、`query-registry.json`（`thcnm-general-ja` / `thcnm-liquid-ja`）、
`query-variants.json`（THA を別名 variant として）、`datasets/cannabinoid-raw-collection/metadata/query-design.json`
（required primary query と安定した被覆ルール）、study README / methodology、`project.json` の `queryDesign`。

## 2026-11-04 — `compound_thc_o` の同一性留保（`THCO` 表記の証拠を登録、ISS-20261104-TAX-029）

`compound_thc_o` の `skos:scopeNote`（en / ja）に、**この概念が単一構造の同定ではない**ことを
追記した。外部識別子（`exactMatch`）・CAS・分子式は taxonomy に追加していない。クエリ表記の証拠は
「検索文字列が同じ意味を意図している」ことを支えるが、「単一の化学構造を指す」ことは支えないため。

| 出所 | 記録されている内容 | 何を支えるか（何を支えないか） |
|---|---|---|
| PubMed 37466480（Cannabis Cannabinoid Res, 2024） | tetrahydrocannabinol-O-acetate が口語で `THCO` と呼ばれる | `THCO` を `THC-O` の表記ゆれとして登録する根拠。物質の同定ではない |
| PubChem CID 198013 | Tetrahydrocannabinol acetate（`delta9-` 体）。別名 `THC-O-ACETATE`、CAS 23132-17-4、`C23H32O3` | `THC-O` がアセテート体を指す名称であること。単一構造の同定ではない |
| PubMed 37381980 / 36508081 | 学術文献が `THC-O-Acetate` / `THC-O Acetate` の表記を用いる | 表記の実在 |
| Cayman Chemical 33763（Δ9-THCO 標準品） | Δ9-THCO、CAS 22972-65-2、`C17H22O2` | 同じ `THCO` 表記が**別物質**（tetrahydrocannabiorcol）にも使われること |
| Cayman Chemical 33762（Δ8-THCO 標準品） | Δ8-THCO、CAS 22972-64-1、`C17H22O2` | Δ8 / Δ9 の 2 異性体があり、`THCO` だけでは一意に決まらないこと |

- **`THCO` は単一の CAS にも単一の構造にも対応しない。** アセテート体（`C23H32O3`）と
  tetrahydrocannabiorcol（`C17H22O2`、Δ8 / Δ9）は別物質である。市場語では `THC-O` が
  曖昧に使われ得る。したがって `compound_thc_o` に `exactMatch` を付けない
  （PubChem CID 198013 は Δ9 アセテート体のレコードであり、総称概念そのものではない）。
- クエリ層の扱いは変えない。`THCO` は `query-variants.json` の variant であり、
  canonical の `query_id`（`thc-o-general-ja` / `thc-o-liquid-ja`）と canonical text は不変。
  variant の run は canonical の run を置換・統合しない（`docs/provenance/query-inventory.md` §2、
  `datasets/cannabinoid-raw-collection/methodology.md` §2.1.5）。
- `Δ8-THC-O-acetate` / `Δ9-THC-O-acetate` や `Δ8-THCO` / `Δ9-THCO` を**別概念**として
  登録するかは未決。決めるには異性体ごとの標準品・規制記載など、クエリ表記以外の根拠が要る
  （ISS-20261104-TAX-029）。
- 証拠の登録: `metadata/provenance/evidence-registry.json` の `ev-pubmed-37466480` /
  `ev-pubmed-37381980` / `ev-pubmed-36508081` / `ev-pubchem-cid-198013` /
  `ev-cayman-33763-delta9-thco` / `ev-cayman-33762-delta8-thco`。外部参照のため
  `sha256` は `null`（`external_unverifiable`。`docs/provenance/evidence-hash-policy.md`）。
- `metadata/taxonomy/iptc-mapping.yaml` は変更しない。`compound-thc-o` は既に
  `deliberately_unmapped` で、理由に「立体異性体・Δ体の総称であり単一 exactMatch は混同を招く」
  と記録済みであり、今回の留保はその理由の範囲内である（新しい識別子を足すわけではない）。
- 派生物: `bash scripts/export/export-taxonomy.sh` と同じエクスポータで
  `exports/taxonomy/compound-taxonomy.ttl` / `.schema.jsonld` を再生成した（概念・ラベルの数は不変）。

## 2026-11-10 — `cannabinoid-raw-collection` の対象集合に CBC・CBDV を追加（ISS-20261110-TAX-039）

**taxonomy は変更していない。** 両語は既に concept として登録済みで、今回の変更は study の対象集合、
query registry、study 文書の層に限る。

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| `compound_id` | `compound_cbc` / `compound_cbdv` | 既存 `skos:notation`。新設していない |
| 名称 | Cannabichromene (CBC) / Cannabidivarin (CBDV) | 既存 `skos:prefLabel`（en / ja） |
| 分類 | `compound_minor` | 既存 `skos:broader`。新しい分類判断をしていない |
| 外部識別子 | `wikidata:Q422441` / `wikidata:Q422426` | 既存 `skos:exactMatch`。追加の照会はしていない。**2026-11-15 注記:** この 2 値は識別子監査で誤りと判明し、CBC = `chebi:3357` / `wikidata:Q410949`、CBDV = `wikidata:Q1104117` に修正した（本台帳 2026-11-15 節、ISS-20261115-TAX-043）。登録判断自体は変えない |
| 登録 query | `cbc-general-ja` / `cbc-liquid-ja` / `cbdv-general-ja` / `cbdv-liquid-ja` | 既存規約（`<compound>-general-ja` / `<compound>-liquid-ja`）の適用 |
| 登録時の収集状態 | 未収集（run 0） | 依頼は対象集合とクエリ設計の拡張であり、収集を含まない |

### 登録時点で未収集だったことの扱い

- 登録時点では 4 query はいずれも **run 0** で、raw payload・staging declaration・catalog 登録・採用はいずれも無かった。
  **これは登録時点の状態であり、現在のカバレッジではない。** 現在の run 結果は
  [`datasets/cannabinoid-raw-collection/README.md`](../../datasets/cannabinoid-raw-collection/README.md)・
  [`methodology.md`](../../datasets/cannabinoid-raw-collection/methodology.md)、
  [`metadata/data-catalog.json`](../../datasets/cannabinoid-raw-collection/metadata/data-catalog.json)、
  `make audit-youtube-coverage` を正本とする。登録時点の未収集は **0 観測でも欠測でもない**
  （`docs/specs/raw-data-policy.md` が区別する「非保持・未収集・欠測・0 観測」のうち未収集）。
- `metadata/queries/query-variants.json` は変更していない。variant は観測された表記の記録であり
  （`THCO` の前例）、run の無い語の表記（`CBCリキッド` 等）を先に作らない。
- `metadata/keywords.yaml` は変更していない。THCNM 追加時にも更新していない legacy の辞書で、
  正本ではない（正本は query registry と study の `query-design.json`）。
- `iptc-mapping.yaml` と `docs/data-dictionary.md` §6.4 は変更していない。`jptr:compound-cbc` /
  `jptr:compound-cbdv` は既に `deliberately_unmapped`（理由付き）で、§6.4 の `compound_minor` 行にも
  列挙済みである。
- `CBC` はカナダ放送協会などドメイン外の略号と衝突する。登録文字列は物質の同定ではないことを
  study の `query-design.json`（`limitations`）と methodology に書いた。

### 保留した語

依頼の列挙 15 語のうち 13 語（`THCB` / `THCP` / `THCJD` / `THCPO` / `CBE` / `HHCPO` / `CBND` / `CBL` /
`CBGa` / `CBP` / `10-OH-HHC` / `THXE` / `THCA`）は、リポジトリに canonical concept が無いため
**登録も query 作成もしていない**。名称・route 配置・外部識別子のいずれも文書化された根拠が無く、
2026-10-15 の TAX-027 gate（名称の根拠 / 分類の根拠 / 全層同時更新）を満たさない。
各語に必要な確認事項は ISS-20261110-TAX-039 に語ごとに記録した。
`THCP` は TAX-027 が「登録しない」と判断済みであり、その判断を変えるには新しい根拠が要る。

### 同時に更新した層

`query-registry.json`（4 query）、`datasets/cannabinoid-raw-collection/metadata/query-design.json`
（登録時点の未収集宣言に 2 化合物）、study README / methodology、`project.json` の
`queryDesign`（写し）、`metadata/provenance/evidence-registry.json`（query registry の hash 再観測）、
本台帳、ISS-20261110-TAX-039。

## 2026-11-11 — owner 指示バッチを「登録状態（同一性未確認）」カテゴリで登録（ISS-20261111-TAX-040。TAX-027 の非登録判断を置換）

owner の明示的な scope 決定（2026-11-11 の列挙 15 語）に基づき、`cannabinoid-raw-collection`
の登録化合物集合を広げた。**この節は「何を登録し、何を登録していないか」を記録する。**
登録は検索文字列の固定であり、化学的同一性の確定ではない。

### 登録した 13 語と配置

`CBC` / `CBDV` は既存概念を再利用済み（下の 2026-11-10 節）であり、本節では扱わない。

| 語（owner 表記） | notation | `@id` | 配置（`skos:broader`） | 外部識別子 | 化学クラス | 登録時の収集状態 |
|---|---|---|---|---|---|---|
| `THCB` | `compound_thcb` | `jptr:compound-thcb` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCP` | `compound_thcp` | `jptr:compound-thcp` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCJD` | `compound_thcjd` | `jptr:compound-thcjd` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCPO` | `compound_thcpo` | `jptr:compound-thcpo` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `CBE` | `compound_cbe` | `jptr:compound-cbe` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `HHCPO` | `compound_hhcpo` | `jptr:compound-hhcpo` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `CBND` | `compound_cbnd` | `jptr:compound-cbnd` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `CBL` | `compound_cbl` | `jptr:compound-cbl` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `CBGa` | `compound_cbga` | `jptr:compound-cbga` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `CBP` | `compound_cbp` | `jptr:compound-cbp` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `10-OH-HHC` | `compound_10_oh_hhc` | `jptr:compound-10-oh-hhc` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THXE` | `compound_thxe` | `jptr:compound-thxe` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCA` | `compound_thca` | `jptr:compound-thca` | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |

- `skos:prefLabel` は **owner の表記をそのまま** en / ja に置いた（`CBGa` の小文字 `a`、
  `10-OH-HHC` のハイフンを保持）。コード名を化学名に置き換えない（H4CBH / HHBD / THCNM の前例）。
- `skos:altLabel` は `{term} リキッド` のみ。研究設計が `product_liquid` を required primary
  query としていることだけが根拠であり、他の綴りは根拠が無いので追加していない。
  （登録時点の規則。2026-11-11 の THCPO 追記で `compound_thcpo` に限り、owner が確認した
  意図された意味を当該概念の scopeNote に根拠として記録したうえで英語の別名を追加した。
  カテゴリ所属は同義関係を確立しない。下の該当節）
- `skos:related` は付けない。`CBGa` と `compound_cbg`、`THCA` と `compound_thc`、
  `10-OH-HHC` と `compound_hhc`、`THCPO` / `HHCPO` と他の語の関係は、リポジトリ内に
  根拠が無いため**主張しない**（別概念・下位・別名のいずれとも決めていない）。

### 新カテゴリ `compound_identity_unverified`（管理上の登録状態）

- 既存 6 カテゴリは**経路／由来**の分類である。13 語をどれかに置くと、根拠の無い経路・
  化学分類の主張になる。そこで「登録状態」を表す管理カテゴリを 1 つ追加し、13 語をそこに置いた。
- このカテゴリと各 member の `skos:scopeNote`（en / ja）は、**経路・由来、天然存在、
  化学クラス、構造、別名関係、規制状態について何も主張しない**ことを明記している。
  希少・マイナー・半合成・合成のいずれの判断でもなく、既存カテゴリの代替でもない。
  語が別個の物質を指すことや、文字列の背後に物質が存在することの主張でもない。
- `skos:exactMatch`・CAS・PubChem / IUPAC 名・化学クラスへのリンクは付けない。
  外部レジストリの照会は行っていない（依頼条件）。**識別子が無いのではなく、確認していない。**
- 移す条件: 検証済み外部識別子を伴う文書化された化学名、または物質名と経路／由来を
  記録した出所が得られた場合。そのときは本台帳に根拠を追記してカテゴリを移す。
- `compound_rare` は**空のまま**維持する。管理カテゴリは rare の受け皿ではない。
  `compound_cbdp` は owner が名指ししていないため登録しない。

### TAX-027 との関係（置換の記録）

- 2026-10-15 の `ISS-20261015-TAX-027` は「`compound_rare` を空のまま維持し、
  `compound_cbdp` / `compound_thcp` を登録しない」と判断した。
- 2026-11-11 の owner 指示は **THCP についてこの非登録判断を置換する**。
  置換は日付付きの決定記録（`ISS-20261111-TAX-040`）と taxonomy の `skos:scopeNote`・
  本節に記録し、`tests/validation/test_compound_rare_membership.py` を新しい決定を
  検査する内容に更新した（テストを削除・緩和していない）。
- **置換したのは THCP の非登録判断だけである。** `compound_rare` の空維持、
  `compound_cbdp` の非登録、希少メンバーに収集級の根拠を要求する gate は維持する。
- 根拠は owner の明示的な列挙のみで、収集 run・文書化された名称根拠・外部識別子の
  検証は無い。**それゆえ経路カテゴリではなく管理カテゴリに置いた。**

### 同時に更新した層

`metadata/queries/query-registry.json`（26 query = 13 語 × `compound_general` / `product_liquid`）、
`datasets/cannabinoid-raw-collection/metadata/query-design.json`
（登録時点の未収集宣言、`identity_caveat` / `limitations`）、
`docs/data-dictionary.md` §6.4、`metadata/taxonomy/iptc-mapping.yaml`
（13 語は `deliberately_unmapped`、カテゴリは `not_applicable`）、
`exports/taxonomy/*`（`bash scripts/export/export-taxonomy.sh` で再生成）、
study README / methodology、`project.json` の `queryDesign`（写し）、
`metadata/provenance/evidence-registry.json`（taxonomy と query registry の hash 再観測）、
`docs/provenance/query-inventory.md` §1、本台帳、`ISS-20261111-TAX-040`。

### 登録時点の収集状態と現在の被覆

- 13 語の 26 query は**登録時点では run 0** だった（raw payload・staging declaration・catalog 登録・採用はいずれも無い）。これは登録の根拠が run 実績ではなく owner 列挙と taxonomy 概念だったことの記録であり、**現在のカバレッジではない**。
- 現在の run 結果は [`datasets/cannabinoid-raw-collection/README.md`](../../datasets/cannabinoid-raw-collection/README.md)・[`methodology.md`](../../datasets/cannabinoid-raw-collection/methodology.md)、[`metadata/data-catalog.json`](../../datasets/cannabinoid-raw-collection/metadata/data-catalog.json)、`make audit-youtube-coverage` を正本とし、ここに run 表を複製しない。
- `missing` は「採用済み run が無い」であり 0 観測ではない。
- 登録は「対象集合とクエリ設計の拡張」であり、登録自体が収集・公開・release slice を広げるものではない。
- `datasets/cannabinoid-raw-collection/metadata/query-design.json` records registration basis and points to the query registry / `make audit-youtube-coverage` for current coverage; it does not duplicate per-run state. This keeps query design distinct from the observed run record.

### 未決事項

- 依頼文の「17 物質」と列挙 15 語の差（2 語）は未解消。**推測で補わない。**
- 13 語の同一性を何で確定するか（標準物質、供給元 SDS / COA、公的レジストリ）。
- `CBGa` / `THCA` / `10-OH-HHC` と既存概念の関係、`THCPO` / `HHCPO` の構造。
  いずれも根拠が得られるまで主張しない。

## 2026-11-11 — owner の意図確認: `CBE` = cannabielsoin（ISS-20261111-TAX-040 追記）

owner は 2026-11-11、`CBE` が cannabielsoin を指すかという確認に `y` と回答した。
これは `compound_cbe` の化学的同一性を「未確認」から **cannabielsoin** へ更新する
明示的な決定である。登録時の履歴（本台帳の 2026-11-11 節と
ISS-20261111-TAX-040 の元の登録表・未決事項）は**書き換えず**、この節と issue の
追記に新しい決定と根拠を記録する。

### 検証した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| FDA GSRS 承認済み CANNABIELSOIN 記録（UNII 2ERD6V6652） | `substanceClass: chemical`、`definitionLevel: COMPLETE`、version 7。名称 CANNABIELSOIN / CANNABIELSOIN A / CANNABIELSOIN I / CBE。コード CAS 52025-76-0、PubChem 162113、UNII 2ERD6V6652。分子式 C21H30O3 | 化学的同一性と識別子を支える。天然存在・経路／由来・国内市場の存在は支えない |
| Wikidata Q22668702 | en label `cannabielsoin`、ja label `カンナビエルソイン`、別名 `cannabielsoin A`。CAS 52025-76-0、UNII 2ERD6V6652、PubChem 162113、分子式 C21H30O3 | ラベルと `skos:exactMatch` を支える。天然存在の独立した根拠ではない |
| PubMed 3254981（Yamamoto et al. 1988, J Pharmacobiodyn 11:833-838） | guinea pig の肝ミクロソームで CBD から CBE が新規代謝物として生成。CBE は pentobarbital 睡眠・体温への活性がほとんどない | CBE = cannabielsoin と、CBD からの代謝生成を支える。植物体内の天然存在やクエリ結果の内容は支えない |
| PubMed 2614640（Yamamoto et al. 1989, J Pharmacobiodyn 12:488-494） | CBE の生物学的生成機構。肝ミクロソーム、NADPH・分子状酸素要求、P-450 阻害剤で抑制、種差（guinea pig > mouse ≧ rabbit ≧ rat） | CBD からの代謝生成経路を支える |
| PubMed 1806944（Yamamoto et al. 1991, Pharmacol Biochem Behav 40:541-546） | CBE が哺乳類で CBD の新規代謝物として同定されたこと、CBE 型代謝物の生成 | 哺乳類代謝物としての CBE を支える |
| DOI 10.1055/s-2007-969870（Hartsel et al. 1983, Planta Med 48:17-19） | Cannabis sativa と Saccharum officinarum の懸濁培養が CBD を CBE へ生物変換し、C-1 の両立体異性体を生成 | 植物培養系での生成を支える。intact plant における天然存在の証明ではない |
| PubMed 39062125 / PMC11275175 / DOI 10.3390/biomedicines12071551（Haghdoost et al. 2024, Biomedicines 12:1551） | 序文: CBE は「非酵素的フィトカンナビノイド」で、Cannabis sativa への天然存在が確立している。CBE は CBD の酸化生成物・哺乳類の minor metabolite でもある。in-vitro で S-CBE が CB1 の cAMP アゴニスト（EC50 3.7 µM）、β-arrestin アゴニスト活性は 12 µM までなし | `compound_minor`（主要フィトカンナビノイド以外のフィトカンナビノイド）の配置を支える。in-vitro 薬理は国内市場・検索結果の内容を支えない |

### 決定した値

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| `skos:prefLabel` | en `Cannabielsoin (CBE)` / ja `カンナビエルソイン (CBE)` | GSRS・Wikidata の名称。既存の CBD / CBG と同じ「名称 (略号)」形式 |
| `skos:altLabel` | `CBE`, `Cannabielsoin A`（en）/ `カンナビエルソイン`, `CBE リキッド`（ja） | CBE は owner の登録語。Cannabielsoin A は GSRS / PubChem の別名。`CBE リキッド` は study の `product_liquid` クエリ表記 |
| `skos:exactMatch` | `wikidata:Q22668702`、`https://identifiers.org/unii:2ERD6V6652` | Wikidata と FDA UNII。CAS 52025-76-0、PubChem CID 162113、C21H30O3 は scopeNote に記録 |
| `skos:broader` | `jptr:compound-minor` | カテゴリ定義は「主要な2化合物以外のフィトカンナビノイド」。2024 年論文が CBE を非酵素的フィトカンナビノイドと明記し、天然存在が確立しているとするため |
| 化学クラス | **リンクしない**（未形式化） | `chemical-class-taxonomy` には水素化・アセテートの 2 クラスしかなく、CBE 型クラスは無い。推測で第 2 次元を作らない |
| 規制状態 | **主張しない** | 本変更は規制資料を収集・評価していない |

- `compound_identity_unverified` の移動条件（「検証済み外部識別子を伴う文書化された化学名、
  または物質名と経路／由来を記録した出所」）を満たしたため、`compound_cbe` を
  同カテゴリの `skos:narrower` から外した。members は 13 → 12 語になる。
- `compound_minor` の `skos:scopeNote` の列挙と `skos:narrower` に CBE を追加した。
  これは新しいクラスの創設ではなく、既存カテゴリ定義に合致するメンバーの追加である。
- `skos:related` は張らない。CBD との関係は scopeNote に文章で記録するが、
  「同一」「下位」「別名」のいずれの構造的主張もしない。
- `compound_cbe` の scopeNote（en / ja）に、owner の確認、GSRS / Wikidata の識別子、
  2024 年論文のフィトカンナビノイド記述、CBD 代謝物・酸化生成物という別の由来、
  化学クラス未形式化、そして**クエリ文字列の限界**を記録した。

### 変更しないもの

- `metadata/queries/query-registry.json` の `cbe-general-ja` / `cbe-liquid-ja` の
  canonical_text と status は変更しない。Google Trends / YouTube が測るのは
  `CBE` / `CBE リキッド` の文字列一致であり、各結果が cannabielsoin を扱うことの
  確認ではない。
- raw 観測、run metadata、catalog、件数、CBE 331 件・CBL 269 件の partial 状態、
  収集計画は変更しない。
- 公開ページ `publication/research_cbe.html` は `requires_review` のままとする。
  review envelope、承認・decision / evidence hash、DOI、version / release status、
  図、外部 release は作成・変更しない。
- 本変更は収集を伴わない。

### 限界と再検討条件

- 2024 年論文の「天然存在が確立している」という記述は二次的な序文の記述であり、
  一次分離文献の再確認は行っていない。1983 年論文は Cannabis の懸濁培養による
  生物変換を支えるが、intact plant からの単離を直接には支えない。
- したがって `compound_minor` の配置は上記の出所が支える範囲での判断である。
  一次分離記録または公的レジストリが天然存在を否定・修正した場合は、本節を
  更新して配置を再検討する。
- `CBE` は短い略号であり、無関係な語とも一致し得る。既存の検索需要・YouTube
  サンプルは文字列一致の観測であって、内容が cannabielsoin であることの証明ではない。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（CBE のラベル・識別子・scopeNote・
  `skos:broader`、minor / identity-unverified の membership）
- `metadata/taxonomy/iptc-mapping.yaml`（CBE を 12 語群から分離し、識別子はあるが
  IPTC 主題は未対応の別群に記録。version 1.5.0）
- `docs/data-dictionary.md` §6.4（写し）
- `docs/provenance/query-inventory.md`（CBE の 2 query の根拠）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（registration_basis /
  identity_caveat）
- `datasets/cannabinoid-raw-collection/methodology.md`（対象化合物表・限界）
- `project.json` の `queryDesign`（写し）
- `metadata/provenance/evidence-registry.json`（外部出所と taxonomy hash）
- `exports/taxonomy/*`（再生成）
- テスト: `tests/validation/test_registration_state_batch.py` /
  `tests/validation/test_compound_rare_membership.py`
- `ISS-20261111-TAX-040` の追記（元の本文は履歴として保持）

## 2026-11-11 — owner の意図確認: `CBL` = cannabicyclol, `CBGa` = cannabigerolic acid（ISS-20261111-TAX-040 追記）

owner は 2026-11-11、`CBL` が cannabicyclol を指すかという確認に `go`、`CBGa` が
cannabigerolic acid（標準表記 `CBGA`）を指すかという確認に `y` と回答した。これは
`compound_cbl` / `compound_cbga` の化学的同一性を「未確認」から確定へ更新する明示的な
決定である。登録時の履歴（本台帳の 2026-11-11 節と ISS-20261111-TAX-040 の元の登録表・
未決事項）と CBE の節は**書き換えず**、この節と issue の追記に新しい決定と根拠を記録する。

### 検証した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| Wikidata Q907909 | en `cannabicyclol`、ja `カンナビシクロ`、CAS 21366-63-2、PubChem CID 30607、C21H30O2 | 名称と `skos:exactMatch` を支える。立体化学と CAS の一意性は支えない |
| FDA GSRS の UNII `MP5WZK8M5U` 記録 | `substanceClass: chemical`、`definitionLevel: COMPLETE`、version 10。名称 CANNABICYCLOL / CANNABIPINOL / PENTYLCANNABICYCLOL、CAS 21366-63-2、PubChem 59444380、C21H30O2 | 化学的同一性と識別子を支える。天然存在・経路／由来・規制状態は支えない |
| PubChem CID 30607 | 立体未指定の `(+/-)-Cannabicyclol`、CAS 様の別名 67920-00-7、C21H30O2 | 立体未指定の識別子を支える。単一 CAS での同定は支えない |
| PubChem CID 59444380 | `Cannabicyclol`、立体指定の IUPAC 名、CAS 21366-63-2、UNII MP5WZK8M5U | 立体指定記録の識別子を支える |
| PubMed 39811943（Haghdoost et al. 2025, J Nat Prod, DOI 10.1021/acs.jnatprod.4c00977） | 要旨が CBL を「a minor phytocannabinoid」と記述。CBC から酸触媒（モンモリロナイト K30）で CBL への変換（収率 60%）、X 線結晶構造で構造確認。in vitro の 5-HT1A PAM | `compound_minor` の配置と名称を支える。酵素的な生合成・植物体内の存在量・規制状態・検索結果の内容は支えない |
| PubMed 33839545（Forensic Sci Int 2021） | 押収大麻・医療用大麻等で 16 種のフィトカンナビノイド（cannabicyclol、cannabigerolic acid を含む）を定量 | CBL・CBGA が植物材料で検出されるフィトカンナビノイドであることを支える。収穫後変換や製造工程は排除しない |
| Wikidata Q27135612 | en `cannabigerolic acid`、CAS 25555-57-1、PubChem CID 6449999、ChEBI 67081、C22H32O4 | 名称と `skos:exactMatch` を支える |
| ChEBI 67081 | `cannabigerolic acid`（olivetolic acid の 3 位に geranyl）。定義は「Δ9-THC の生合成前駆体」 | 同一性・前駆体の記述・`skos:exactMatch` を支える。CBG への脱炭酸はこの定義では支えない |
| FDA GSRS の UNII `80I4ZM847Y` 記録 | `substanceClass: chemical`、`definitionLevel: COMPLETE`、version 10。名称 CANNABIGEROLIC ACID / CBGA、CAS 25555-57-1、PubChem 6449999、C22H32O4 | 同一性と識別子を支える。天然存在量・経路／由来・規制状態は支えない |
| PubChem CID 6449999 | `Cannabigerolic Acid`、C22H32O4、CAS 25555-57-1、ChEBI:67081、UNII 80I4ZM847Y | 同一性と識別子を支える |
| PubMed 31686510（J Nat Prod 2019） | フィトカンナビノイドは中性体と酸性前駆体として存在し、酸性体が植物中で dominant。CBGA をフィトカンナビノイド酸として列挙 | `compound_minor` の配置を支える。国内市場・検索結果の内容は支えない |
| PubMed 35887277（Int J Mol Sci 2022） | CBG は CBGA の非酵素的脱炭酸で生成する。CBGA はフィトカンナビノイド生合成の鍵となる前駆体 | CBGA と CBG が別概念であることを支える。`skos:related` の根拠にはしない |
| 厚生労働科学研究の報告書（2023、`mhlw-grants.niph.go.jp`） | 日本語で「カンナビシクロール（CBL）」「カンナビエルソイン（CBE）」と表記し、カンナビゲロール酸を CBD/THC 経路の起点として図示 | 日本語ラベルを支える。規制状態は支えない |
| J-GLOBAL（JST） | `カンナビゲロール酸 / Cannabigerolic acid`、C22H32O4、InChIKey、別名 CBGA | 日本語ラベルと識別子を支える |

### 決定した値

| 項目 | `compound_cbl` | `compound_cbga` |
|---|---|---|
| `skos:prefLabel` | en `Cannabicyclol (CBL)` / ja `カンナビシクロール (CBL)` | en `Cannabigerolic acid (CBGA)` / ja `カンナビゲロール酸 (CBGA)` |
| `skos:altLabel` | en `CBL` / ja `CBL リキッド` | en `CBGA`, `CBGa` / ja `CBGa リキッド` |
| `skos:exactMatch` | `wikidata:Q907909` | `chebi:67081`, `wikidata:Q27135612`, `https://identifiers.org/unii:80I4ZM847Y` |
| `skos:broader` | `jptr:compound-minor` | `jptr:compound-minor` |
| 化学クラス | リンクしない（CBL 型クラスは taxonomy に無い） | リンクしない（CBGA 型クラスは taxonomy に無い） |
| 規制状態 | 主張しない | 主張しない |

- CBL は CAS 21366-63-2（GSRS / Wikidata / 立体指定 PubChem）と 67920-00-7（立体未指定
  PubChem の別名）が併存するため、`skos:exactMatch` に CAS を採らず、scopeNote に
  両方と立体化学の差を記録した。単一 CAS を本概念の識別子として断定しない。
- CBL の ja ラベルは日本語の科学技術報告での表記（カンナビシクロール）に従った。
  Wikidata の ja ラベルは `カンナビシクロ` であり、表記が異なることを scopeNote に記した。
- CBGA は `CBGa` を owner の表記として altLabel に残し、登録クエリ文字列（`CBGa` /
  `CBGa リキッド`）と raw / query 記録は変更しない。大文字小文字の正規化は行わない。
- `compound_identity_unverified` の members は 12 語から 10 語になった。`compound_minor`
  の `skos:narrower` と scopeNote の列挙に両語を追加した。新しいクラスは作っていない。
- `skos:related` は張らない。CBL と `compound_cbc`（CBC からの変換）、CBGA と
  `compound_cbg`（酸性前駆体 / 脱炭酸体）の関係は scopeNote の文章に留める。CBG の
  外部識別子の対応は未解決であり、関係を構造化する前に別途修正する（下記の既知事項）。

### 変更しないもの

- `metadata/queries/query-registry.json` の `cbl-general-ja` / `cbl-liquid-ja` /
  `cbga-general-ja` / `cbga-liquid-ja` の canonical_text と status。
- raw 観測、run metadata、catalog、件数、CBL 269 件・CBE 331 件の partial 状態、CBGa の
  NO_DATA、収集計画。**本変更は収集を伴わない。**
- 公開ページ `publication/research_cbl.html` / `publication/research_cbga.html` は
  `requires_review` のまま。review envelope、承認、decision / evidence hash、DOI、
  version / release status、図、外部 release は作成・変更しない。
- 既存の `compound_cbg` / `compound_thc` 等の外部識別子は修正しない（下記の既知事項）。

### 限界と再検討条件

- CBL の立体化学と CAS の対応は一意でない。一次分離文献または公的レジストリが対応を
  訂正した場合は、本節と scopeNote を更新して再検討する。
- 2025 年論文は酸触媒による CBC→CBL 変換を示すが、生体内の酵素合成や intact な植物での
  存在を確立しない。`compound_minor` の配置は「フィトカンナビノイドであり主要 2 化合物
  以外」という範囲の判断である。
- CBGA と CBG の前駆体／脱炭酸体の関係は文章で記録し、`skos:related` は張らない。
  構造化するには taxonomy の関係規則と CBG 側の識別子修正が必要である。
- `CBL` と `CBGa` は短い略号である。Google Trends / YouTube の系列は文字列一致の観測で
  あり、意図された同一性が確認されても各結果がその物質を扱うことの証明ではない。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（両語のラベル・識別子・scopeNote・
  `skos:broader`、minor / identity-unverified の membership）
- `metadata/taxonomy/iptc-mapping.yaml`（両語を 10 語群から分離し、識別子はあるが IPTC
  主題は未対応の別群に記録。version 1.6.0）
- `docs/data-dictionary.md` §6.4（写し）
- `docs/provenance/query-inventory.md`（両語の 2 query の根拠）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（registration_basis /
  identity_caveat）
- `datasets/cannabinoid-raw-collection/README.md`・`methodology.md`（対象化合物表・限界）
- `project.json` の `queryDesign`（写し）
- `metadata/provenance/evidence-registry.json`（外部出所と taxonomy hash）
- `exports/taxonomy/*`（再生成）
- 公開ページ `publication/research_cbl.html` / `publication/research_cbga.html`（同一性の
  記述のみ。`requires_review` は維持）
- テスト: `tests/validation/test_registration_state_batch.py` /
  `tests/validation/test_compound_rare_membership.py`
- `ISS-20261111-TAX-040` の追記（元の本文は履歴として保持）

## 2026-11-11 — owner の意図確認: `THCP` = C7 同族体ファミリー、`THCJD` = C8 同族体ファミリー（Δ8/Δ9 未指定。ISS-20261111-TAX-040 追記）

owner は 2026-11-11、登録語の意図された意味を次のように確認した。

- `THCP` = **tetrahydrocannabiphorol（C7）同族体ファミリー、Δ8/Δ9 未指定**
- `THCJD` = **THC-JD / 3-octyl-THC（C8）同族体ファミリー、Δ8/Δ9 未指定**

これは**検索トピックのファミリー範囲の確認**であり、個々の Google Trends / YouTube 結果が
どちらの異性体を扱うかの確認ではない。Δ8 体と Δ9 体は別物質であり、ハイフンなしの `THCJD`
は owner の検索文字列であって権威ある登録名ではない。登録文字列（`THCP` / `THCP リキッド`、
`THCJD` / `THCJD リキッド`）は変更しない。

### 検証した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| Citti et al. 2019, Sci Rep, DOI `10.1038/s41598-019-56785-1` | Cannabis sativa から Δ9-THCP を分離し、C7 同族体（tetrahydrocannabiphorol）として同定。CB1 結合親和性は Δ9-THC の約 33 倍 | `THCP` が C7 同族体ファミリーを含むこと、Δ9 体の名称と結合親和性。ファミリー全体の天然存在、Δ8 体の天然存在、ヒトでの効力、国内市場の存在は支えない |
| FDA GSRS レコード UNII `WTK87HN3LG`（Δ9-THCP） | CAS `54763-99-4`、PubChem CID `6453074` | Δ9 体の識別子。登録語 `THCP` の識別子ではない |
| Wikidata `Q85806080`（Δ9-THCP） | 上記識別子を持つ項目 | Δ9 体の項目。ファミリーの識別子ではない |
| PubChem CID `44307335` / Wikidata `Q141317106`（Δ8-THCP） | CAS `51768-60-6` を持つ Δ8 体の独立レコード | Δ8 体が Δ9 体と別物質であること。登録語の識別子ではない |
| Tanaka & Kikura-Hanajiri 2024, 薬学雑誌, DOI `10.1248/yakushi.24-00029` | Δ8/Δ9 の 3-octyl-THC を "THCjd" として扱う | `THCJD` の C8 同族体ファミリーとしての範囲と名称。単一異性体の同定、天然存在、規制状態は支えない |
| Munger et al. 2026, DOI `10.26828/cannabis/2026/000348` | 販売製品の表示と内容の重大な不一致。「19 倍」は業界の主張 | ラベル・内容不一致という限界。効力の測定値、規制状態、天然存在は支えない |

### 決定した値

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| taxonomy 配置 | `compound_identity_unverified`（変更なし） | ファミリーは単一物質ではなく、経路／由来の分類を支持する根拠が無い |
| `skos:prefLabel` / `skos:altLabel` / `skos:notation` | 変更なし（`THCP` / `THCJD` と `{term} リキッド`） | owner の登録表記と study の `product_liquid` 設計 |
| `skos:exactMatch` | **張らない** | ファミリー全体を表す単一レコードが無い。Δ9 体・Δ8 体のレコードは異性体の識別子であり、登録語の識別子ではない |
| 外部識別子の記載箇所 | 本台帳のみ（taxonomy の概念には書かない） | 管理カテゴリの member は識別子を持たない規則。ファミリーに単一識別子は無い |
| 化学クラス | リンクしない | 同族体ファミリーは `chemical-class-taxonomy` の形式化されたクラスではない |
| 天然存在・合成経路・安全性・臨床効果・規制状態 | **主張しない** | owner の確認は検索トピックの範囲であり、これらの根拠ではない |
| 単一物質としての化学的同一性 | **未確認** | 異性体が指定されていないため、単一物質を同定できない |

### `compound_minor` / `compound_rare` へ移さない理由

- `compound_minor` は「主要 2 化合物以外の**フィトカンナビノイド**」という経路／由来の分類である。
  Δ9-THCP が Cannabis sativa から報告されていることは Δ9 体についての根拠であり、**Δ8/Δ9 未指定の
  検索語全体**の天然存在を支えない。さらに登録文字列はファミリー外の製品・内容とも一致する
  （Munger et al. 2026 の表示・内容不一致）。したがって配置は根拠を超える。
- `compound_rare` は「微量にのみ存在する」という天然存在の主張を含み、意図的に空のまま維持している
  （ISS-20261015-TAX-027）。THCP を入れるとその判断と固定テストを壊す。
- `chemical-class-taxonomy` にも同族体ファミリーのクラスは無く、推測で第 2 次元を作らない。
- したがって、ファミリー範囲は**管理カテゴリ内の文書化された検索語の範囲**として scopeNote に記録し、
  経路・化学クラス・天然存在の主張は行わない。

### 変更しないもの

- `metadata/queries/query-registry.json` の canonical_text（`THCP` / `THCP リキッド`、`THCJD` /
  `THCJD リキッド`）と status。系列が測るのは文字列一致である。
- `query-design.json` の `registration_basis` の `identity_state`（`compound_identity_unverified`）。
  単一物質の同一性が未確認であることに変わりはない。
- raw 観測、run metadata、catalog、件数、収集計画。
- 公開ページ `publication/research_thcp.html` / `publication/research_thcjd.html` は `requires_review`
  のまま。review envelope、承認・decision / evidence hash、DOI、version / release status、図は
  作成・変更しない。
- 分類（`skos:broader`）とカテゴリの membership。`compound_identity_unverified` の members は 10 語のまま。

### 限界と再検討条件

- 個々の Google Trends / YouTube 結果の異性体归属は未確認である。系列は登録文字列の一致を測る。
- ファミリーの存在は公表文献に依拠し、本変更は一次分離を再確認していない。Δ8 体の天然存在・合成経路・
  安全性・臨床効果は未評価である。
- 「33 倍」は CB1 結合親和性の比、「19 倍」は業界の主張（Munger et al. 2026）であり、いずれも
  ヒトでの効力の測定値ではない。
- 規制状態は本変更の対象外である。規制資料は本変更で評価していない。2023 年の厚生労働省の
  構造グループが C8 側鎖を含むという指摘は一次資料を確認していないため、根拠欄にも taxonomy にも
  記載しない（必要なら別作業で確認する）。
- ファミリーを形式化する taxonomy の state（カテゴリ）を持つかは design decision であり、本変更では
  決めない。現状は管理カテゴリ内の文書化された範囲として扱う。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_thcp` / `compound_thcjd` の
  scopeNote、管理カテゴリの scopeNote、scheme description の単一物質表現）
- `docs/data-dictionary.md` §6.4（写し）
- `docs/specs/validation-framework.md` §23.4（TAX-027 の引き継ぎ記述を THCP の現状に合わせる）
- `docs/provenance/query-inventory.md`（両語の 2 query の証拠欄）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（`identity_caveat` /
  `limitations` / `distribution.reason`）
- `datasets/cannabinoid-raw-collection/README.md`・`methodology.md`（対象化合物表・注記）
- `project.json` の `queryDesign`（写し）
- `metadata/taxonomy/iptc-mapping.yaml`（10 語群の理由を 8 語 + 2 語に分けて記述。version 1.7.0）
- `metadata/provenance/evidence-registry.json`（taxonomy hash の再観測）
- `exports/taxonomy/*`（再生成）
- 公開ページ `publication/research_thcp.html` / `research_thcjd.html`（同一性の記述のみ。
  `requires_review` は維持）
- テスト: `tests/validation/test_registration_state_batch.py`
- `ISS-20261111-TAX-040` の追記（元の本文は履歴として保持）

## 2026-11-11 — owner の意図確認: `THCPO` = THCP-O-acetate（異性体の指定なし。登録は異性体未指定ファミリーとして扱う。ISS-20261111-TAX-040 追記）

2026-11-11、owner は確認質問「`THCPO` は THCP-O-acetate を指しますか？」に `y` と回答し、**Δ8 体・Δ9 体のいずれの異性体も名指ししなかった**（ISS-20261111-TAX-040 追記）。したがって本登録は **異性体未指定の THCP-O-acetate ファミリー**として扱う。このファミリー扱いは回答の登録上の整理であり、**owner がファミリーを明示的に確認したものではない**。二つの異性体は別物質として区別し、個々の Google Trends / YouTube 結果がどちらの異性体を扱うかは確認しない。登録文字列（`THCPO` / `THCPO リキッド`）は変更しない。

`THCPO` と他の概念との関係は主張しない。`compound_thc_o` は別に登録された市場・総称の概念で、独自の同一性留保を持ち（単一の検証済み構造ではない）、本節はそこへ特定の構造を割り当てない。`THCP-O-butanoate` は Tanaka et al. 2025 が Δ9-THCP-O-acetate と並んで同定した別のエステルであり、本概念の別名ではない。`compound_hhcpo` は別に登録された語で、化学的同一性は未確認である。本概念との別名・関連（`skos:related`）・`exactMatch` は張らない。

### 検証した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| 厚生労働省「指定薬物を指定する省令が公布されました」（2024-05-01 公布、2024-05-11 施行。令和6年厚生労働省令第81号） | 物質群1 = 6a,7,8,10a-テトラヒドロ-6,6,9-トリメチル-6H-ジベンゾ[b,d]ピランの1位に水酸基又はアセトキシ基が一つ、3位に直鎖 C3–C8 アルキル、他の置換基なし（麻薬を除く）。物質群2 = 同じ定義（麻薬を除く）の 6a,7,10,10a-テトラヒドロ（Δ8）系列。別紙は n=7 として Δ9-THCP-O-acetate / Δ8-THCP-O-acetate を列挙 | 両異性体が省令の「麻薬を除く」除外規定の下で 2024 年の構造グループに該当すること（法令上の構造の事実）。個々の製品・検索結果の分類ではなく、規制判断でも、owner の同一性確認の一部でもない。経路、天然存在、薬理、安全性は支えない |
| Tanaka et al. 2025, Drug Test Anal 17(9):1795-1802, DOI `10.1002/dta.3883`, PMID 40075559 | オンライン流通のオイル製品 7 点とハーブ製品 1 点を GC-MS / LC-PDA-MS / NMR で分析し、Δ9-THCP-O（アセテート）と Δ9-THCP-O-butanoate を同定した。あわせて **Δ8-THC-O（アセテート、C5 同族体）** も同定しており、これは Δ8-THCP-O-acetate ではない | Δ9 アセテートと butanoate が分析対象の製品に存在すること、および両者が別のエステルであること。Δ8-THCP-O-acetate、ファミリー全体、検索結果の内容は支えない |
| PubChem CID `172677450`（Δ9-THCP acetate） | `C25H36O3`、IUPAC 名 `[(6aR,10aR)-3-heptyl-6,6,9-trimethyl-6a,7,8,10a-tetrahydrobenzo[c]chromen-1-yl] acetate`、InChIKey `OXMUZNKOOOITQD-NHCUHLMSSA-N`、別名に CAS `2829292-82-0` | Δ9 体の独立レコードと識別子。ファミリーの識別子ではない |
| PubChem CID `172874392`（delta8-THCP acetate） | `C25H36O3`、InChIKey `FDKCGSRFVKINQD-NHCUHLMSSA-N`、CAS の別名なし | Δ8 体が Δ9 体と別レコードであること。CAS は確認していない |
| Wikidata `Q122689235` | en label `THCP-O-acetate`、ja label なし。InChIKey `OXMUZNKOOOITQD-NHCUHLMSSA-N`、PubChem CID `172677450`。CAS の主張なし | Δ9 体に対応する項目であること。ラベルはファミリー名だが、ファミリーの識別子ではない |
| ChEBI | 記録した検索語は `THCP` のみで、該当なし | その検索で該当が無かったこと。アセテート体・ファミリーの ChEBI レコードの不在の証明ではなく、ファミリーに対する `exactMatch` も割り当てていない |
| FDA GSRS | 名称検索 `Tetrahydrocannabiphorol` で親化合物（UNII `WTK87HN3LG`）のみ。THCP-O-acetate のレコードは得られず | その名称検索で THCP-O-acetate の識別子を確認していないこと。不在の証明ではない |

- MHLW: <https://www.mhlw.go.jp/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/yakubuturanyou/oshirase/20240807-1.html>、別紙 <https://www.mhlw.go.jp/content/11126000/001250830.pdf>
- PubChem: <https://pubchem.ncbi.nlm.nih.gov/compound/172677450>、<https://pubchem.ncbi.nlm.nih.gov/compound/172874392>
- Wikidata: <https://www.wikidata.org/wiki/Q122689235>

### 決定した値

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| taxonomy 配置 | `compound_identity_unverified`（変更なし） | ファミリーは単一物質ではなく、経路／由来の分類を支持する根拠が無い |
| `skos:prefLabel` / `skos:notation` | 変更なし（`THCPO` en/ja、`compound_thcpo`） | owner の登録表記。テストが owner 表記を固定している |
| `skos:altLabel` | `THCP-O-acetate`（en）を追加、`THCPO リキッド`（ja）を維持 | owner が確認した意図された意味を記録する**検索スコープの別名**。根拠は当該概念の scopeNote にあり、カテゴリ所属から導かれる同義でも、ファミリーが単一構造であるという主張でもない（`THCPO リキッド` は study の `product_liquid` 設計） |
| `skos:exactMatch` | **張らない** | ファミリー全体を表す単一レコードが無い。Δ9・Δ8 のレコードは異性体の識別子であり、登録語の識別子ではない |
| 外部識別子の記載箇所 | 本台帳のみ（taxonomy の概念には書かない） | 管理カテゴリの member は単一物質の識別子を持たない規則 |
| 化学クラス | リンクしない | アセテートは `chemical-class-taxonomy` の `chemclass-acetate` に構造クラスとして存在するが、本概念は単一物質ではなく、クラスへのリンクは経路・分類の主張になる。`skos:related` も張らない |
| 規制状態 | **両異性体が 2024 年の厚生労働省令の構造グループに該当**すると記録（省令の**「麻薬を除く」除外規定の下での法令上の構造の事実**） | MHLW の省令・別紙。個々の製品・検索結果の分類ではなく、規制判断でも、owner の同一性確認の一部でもない |
| 天然存在・合成経路・薬理・安全性・臨床効果 | **主張しない** | owner の確認と上記出所はこれらの根拠ではない |
| 単一物質としての化学的同一性 | **未確認** | 異性体が指定されていないため、単一物質を同定できない |

### `compound_minor` / `compound_rare` / `compound_semisynthetic` へ移さない理由

- `compound_minor` は「主要 2 化合物以外のフィトカンナビノイド」という経路／由来の分類である。Δ9 アセテートが分析対象の製品から同定されたことは Δ9 体についての分析結果であり、Δ8/Δ9 未指定の検索語全体の天然存在を支えない。
- `compound_semisynthetic` は「天然対応物を化学修飾した」という経路の主張を含む。アセテート構造は owner の確認と文献に記録されているが、本変更は合成経路・原料を検証していないため、経路分類へ移さない。
- `compound_rare` は「微量にのみ存在する」という天然存在の主張を含み、意図的に空のまま維持している（ISS-20261015-TAX-027）。`compound_thcpo` は owner が名指しした語であり、rare の受け皿ではない。
- したがって、ファミリー範囲と規制上の構造グループ該当は**管理カテゴリ内の文書化された事実**として scopeNote と本台帳に記録し、経路・化学クラス・天然存在の主張は行わない。

### `compound_identity_unverified` の移動条件との関係

- カテゴリの移動条件は「検証済み外部識別子を伴う文書化された化学名、または単一物質名と経路／由来を記録した出所」。本語は**化学名と異性体ごとの識別子**を持つが、**単一物質を指さない**ため条件を満たさない。THCP / THCJD と同じ扱いである。
- カテゴリの scopeNote に、異性体未指定のエステル（アセテート）体ファミリーもここに置くこと、ファミリーの scopeNote が法令上の構造グループ該当を記録する場合があることを追記した。あわせて、**カテゴリ所属自体は同義関係を確立しない**こと、member の `skos:altLabel` は概念レベルの記録で当該概念の scopeNote に独自の根拠を要することを明記した。`compound_thcpo` の英語別名はこの規則に従う。カテゴリ ID・階層・membership は変えない。

### 変更しないもの

- `metadata/queries/query-registry.json` の `thcpo-general-ja` / `thcpo-liquid-ja` の canonical_text（`THCPO` / `THCPO リキッド`）と status。系列が測るのは文字列一致である。
- `query-design.json` の `registration_basis` の `identity_state`（`compound_identity_unverified`）。単一物質の同一性が未確認であることに変わりはない。
- raw 観測、run metadata、catalog、件数（Google Trends 5年 262 週、YouTube 33 件）、収集計画。**本変更は収集を伴わない。**
- 公開ページ `publication/research_thcpo.html` は `requires_review` のまま。review envelope、承認・decision / evidence hash、DOI、version / release status、図は作成・変更しない。
- `compound_thc_o` / `compound_hhcpo` 等の既存概念の識別子・分類・scopeNote は変更しない。

### 限界と再検討条件

- 個々の Google Trends / YouTube 結果の異性体归属は未確認である。系列は登録文字列の一致を測る。
- Δ8-THCP-O-acetate を同定した分析文献は本変更では確認していない。Tanaka et al. 2025 が同定した Δ8 アセテートは **Δ8-THC-O（アセテート、C5 同族体）** であり、Δ8-THCP-O-acetate ではない（同論文は Δ9-THCP-O-acetate と Δ9-THCP-O-butanoate を同定）。Δ8-THCP-O-acetate の存在・天然存在・合成経路は未評価である。
- Wikidata の `THCP-O-acetate` 項目はラベルがファミリー名だが、構造キーと PubChem CID は Δ9 レコードに対応する。ラベルだけを根拠にファミリーの識別子として使わない。
- CAS `2829292-82-0` は PubChem の Δ9 レコードの別名として記録されている。CAS Registry の独立照会（Common Chemistry）は認証を要求したため実施しておらず、Δ8 体の CAS は確認していない。
- 2024 年の厚生労働省令の構造グループ該当は、省令の**「麻薬を除く」除外規定の下での、物質の構造に基づく法令上の事実**である。個々の製品の適法性、含有量、安全性、薬理作用を判定するものではなく、owner の同一性確認の一部でもない。
- ファミリーを形式化する taxonomy の state（カテゴリ）を持つかは design decision であり、本変更では決めない。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_thcpo` の altLabel・scopeNote、管理カテゴリの scopeNote）
- `metadata/taxonomy/iptc-mapping.yaml`（10 語群の理由と coverage の記述、THCPO の記述の修正。version 1.9.1）
- `docs/data-dictionary.md` §6.4（写し）
- `docs/provenance/query-inventory.md`（`thcpo-general-ja` / `thcpo-liquid-ja` の証拠欄、版 1.7.6）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（`registration_basis` / `identity_caveat` / `limitations`）
- 同 study の `README.md`・`methodology.md`（対象化合物表・注記）
- `project.json` の `queryDesign`（写し）
- `metadata/provenance/evidence-registry.json`（taxonomy hash の再観測）
- `exports/taxonomy/*`（再生成）
- 公開ページ `publication/research_thcpo.html`（同一性の記述のみ。`requires_review` は維持）
- テスト: `tests/validation/test_registration_state_batch.py`（THCPO の登録範囲・カテゴリ所属と非マッピング、カテゴリ所属が同義を確立しないこと、別名の根拠を固定）
- `ISS-20261111-TAX-040` の追記（元の本文は履歴として保持）

## 2026-11-11 — owner の意図確認: `THCA` と `THCB` をそれぞれ 3 つの検索トピックへ分割（ISS-20261111-TAX-041）

owner は 2026-11-11、`THCA` の総称的な化学解釈を **Δ9-THCA-A / THCA-B / Δ8-THCA** の 3 つの検索トピックに、
`THCB` を **Δ8-THCB / Δ9-THCB / THCB-O-acetate** の 3 つの検索トピックに置き換えることを確認した。
これは**検索トピックの範囲の確認**であり、各登録文字列が単一の物質・単一の外部レコードを指すことの確認ではない。
`compound_thca` / `compound_thcb` は総称文字列の登録として残り、既存の `thca-*` / `thcb-*` クエリと run は付け替えない。
本変更は登録のみで、収集・raw・declaration・run id・件数・release slice を変更しない。

### 登録した 6 概念

| 語（owner 表記） | notation | `@id` | prefLabel | 配置（`skos:broader`） | 外部識別子 | 化学クラス | 登録時の収集状態 |
|---|---|---|---|---|---|---|---|
| `Δ9-THCA-A` | `compound_delta9_thca_a` | `jptr:compound-delta9-thca-a` | `Δ9-THCA-A`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCA-B` | `compound_thca_b` | `jptr:compound-thca-b` | `THCA-B`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `Δ8-THCA` | `compound_delta8_thca` | `jptr:compound-delta8-thca` | `Δ8-THCA`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `Δ8-THCB` | `compound_delta8_thcb` | `jptr:compound-delta8-thcb` | `Δ8-THCB`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `Δ9-THCB` | `compound_delta9_thcb` | `jptr:compound-delta9-thcb` | `Δ9-THCB`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |
| `THCB-O-acetate` | `compound_thcb_o_acetate` | `jptr:compound-thcb-o-acetate` | `THCB-O-acetate`（en / ja） | `compound_identity_unverified` | なし | 未形式化 | 登録時点で未収集（run 0） |

- `skos:prefLabel` は **owner の表記をそのまま** en / ja に置いた。`Δ` と数字・ハイフンを保持し、
  ASCII 表記（`Delta9-...` 等）への正規化は行わない。
- `skos:altLabel` は `{term} リキッド` のみ。研究設計が `product_liquid` を required primary query と
  していることだけが根拠であり、他の綴りは追加しない。
- `skos:related` は付けない。総称概念（`compound_thca` / `compound_thcb`）・相互（Δ8/Δ9、A/B）・
  `compound_thc` との関係は scopeNote の文章に留め、構造化した関係は主張しない。
  Δ9-THCA-A が Δ9-THC の酸性前駆体であることは文献に記録があるが、方向性のある関係を
  対称な `skos:related` で表さない（CBGA/CBG と同じ扱い）。
- 6 語はすべて管理カテゴリ `compound_identity_unverified` に置く。単一の検証済み外部識別子を
  選択していないため、`exactMatch`・CAS 番号・PubChem CID・UNII・IUPAC 名を概念に付けない。
  異性体ごとのレコードを確認した場合は本台帳にのみ記録し、概念の識別子として代用しない。

### 検証した出所と、支える範囲

| 出所 | 記録されている内容 | 支える主張 / 支えない主張 |
|---|---|---|
| Moreno-Sanz 2016, Cannabis Cannabinoid Res 1:124-130, DOI `10.1089/can.2016.0008` | Δ9-THCA-A（2-carboxy-THC）を Δ9-THC の酸性前駆体とし、Cannabis の腺毛で生合成・蓄積されると記述。文献が `THCA` を複数の酸性誘導体に曖昧に用いてきたことを指摘。THCA-B（4-carboxy-THC）を THCA-A の少量異性体として記録し、後続研究がその存在を確認できなかったことも記録 | Δ9-THCA-A と THCA-B の名称・構造上の区別、総称 `THCA` の曖昧さを支える。Δ8-THCA の構造、天然存在、国内市場、検索結果・製品の内容は支えない |
| Filer 2021, Cannabis Cannabinoid Res 6(5):446-448, DOI `10.1089/can.2021.0003`, PMCID `PMC8612408` | THCA-B を THCA-A の構造異性体とし、1969 年の単離・特性評価と 1975 年の X 線研究を記録。両者の脱炭酸挙動の差を議論 | THCA-A と THCA-B が別物質であり、THCA-B が THCA-A の別名でないことを支える。Δ8-THCA、天然存在、内容は支えない |
| Linciano et al. 2020, J Nat Prod 83(1):88-98, DOI `10.1021/acs.jnatprod.9b00876` | medicinal Cannabis sativa 品種から Δ9-THCB（Δ9-THC のブチル同族体）を単離し、分光分析と立体選択的合成の比較で構造・絶対配置を確認 | Δ9 体の名称と構造を支える。Δ8 体、総称 `THCB`、天然存在、製品・検索結果の内容は支えない |
| Tanaka & Kikura-Hanajiri 2024, 薬学雑誌 144(8):823-837, DOI `10.1248/yakushi.24-00029` | 2022〜2023 年に国内でオンライン流通したオイル製品 5 点から、C-3 位のアルキル鎖長が異なる Δ8/Δ9 THC アナログとして Δ8-THCB と Δ9-THCB をそれぞれ同定 | 両異性体が別物質であり、分析対象の製品に存在したことを支える。天然存在、合成経路、規制状態、個々の検索結果の異性体归属は支えない |
| 厚生労働省 令和6年厚生労働省令第81号（2024-05-01 公布、2024-05-11 施行）別紙「新たに指定された指定薬物の名称」 | 物質群1（6a,7,8,10a-テトラヒドロ）と物質群2（6a,7,10,10a-テトラヒドロ）は、1 位の水酸基又はアセトキシ基、3 位の直鎖 C3–C8 アルキル、他の置換基なしを範囲とする。別紙は物質群1 に Δ9-THCB-O-acetate（n=4）、物質群2 に Δ8-THCB-O-acetate（n=4）を明記 | 両異性体が法令上の構造グループに該当することを支える。個々の製品の適法性・含有量・安全性、経路、天然存在、検索結果の内容は支えない |
| `Δ8-THCA` の出所 | 本変更では構造・命名の出所を確認していない。A/B のカルボキシル配置の区別は Δ9 系列の文献に基づく記載であり、Δ8 系列へ推測で拡張しない | `Δ8-THCA` が単一構造を指すことは支えない。識別子を推測しない |

### 決定した値

| 項目 | 記録した値 | 根拠 |
|---|---|---|
| taxonomy 配置 | 6 語すべて `compound_identity_unverified`（変更なしの管理カテゴリ） | 単一物質の同定ではなく、経路・化学クラス・天然存在の根拠が無いため |
| `skos:prefLabel` | owner 表記そのまま（en / ja） | 登録語の表記を保存する既存規約 |
| `skos:altLabel` | `{term} リキッド`（ja）のみ | study の `product_liquid` 設計 |
| `skos:exactMatch` / 概念の識別子 | **張らない**。CAS・PubChem CID・UNII・ChEBI ID・Wikidata QID を概念に書かない | 登録文字列について単一の検証済みレコードを選択していない。Δ8-THCA は構造・命名の出所も未検証。異性体ごとの事実は本台帳のみ |
| `skos:related` | 張らない | 総称・相互・`compound_thc` との関係は文章に留める。方向性のある前駆体関係を対称リンクで表さない |
| 化学クラス | リンクしない | 同族体・位置異性体・アセテートは `chemical-class-taxonomy` の形式化されたクラスではない |
| 単一物質としての化学的同一性 | **未確認**（Δ9-THCA-A / THCA-B / Δ8-THCB / Δ9-THCB は文献名を持つが、登録文字列の単一レコードは未確認。Δ8-THCA は構造・命名の出所も未検証。THCB-O-acetate は異性体未指定） | 上記の出所。文献が分析対象の物質を記録しても、検索文字列の内容や単一レコードを確定しない |
| 規制状態 | THCB-O-acetate の Δ8/Δ9 両異性体が 2024 年省令の構造グループに該当することのみ記録。その他の規制状態は主張しない | 厚生労働省令・別紙。個々の製品・結果の判断ではない |

### 総称概念と既存 run の扱い

- `compound_thca` / `compound_thcb` の `skos:notation`・`@id`・prefLabel・`skos:broader` は変更しない。
  scopeNote に、owner が総称の化学解釈を 6 つの検索トピックへ置き換えたこと、総称概念は文字列の登録として
  残ること、既存 run を付け替えないことを追記した。
- `thca-general-ja` / `thca-liquid-ja` / `thcb-general-ja` / `thcb-liquid-ja` の `query_id`・
  `canonical_text`・`status` は変更しない。非推奨化も再ターゲットも行わない。
- 既存の `THCA` / `THCB` の Google Trends / YouTube run は元の文字列クエリに付いたままで、
  6 つの新概念へ割り当てない。公開ページ `research_thca.html` / `research_thcb.html` は
  総称文字列のページとして残し、サンプルが新概念へ割り当てられていないことを明記した。

### 変更しないもの

- 既存の query registry エントリ（`thca-*` / `thcb-*`）の ID・文字列・status。新規 12 query のみ追加。
- raw 観測、run metadata、catalog、`staging-declaration`、run id、件数、収集計画。
  **本変更は収集を伴わない。**
- 公開ページの `requires_review` 状態、review envelope、承認・decision / evidence hash、DOI、
  version / release status、図。新概念用の空ページは作成しない（データが無いため）。
- release slice。6 概念は登録のみで、いずれの配布物にも追加しない。
- `compound_thcp` / `compound_thcjd` / `compound_thcpo` の owner 確認済みの記述（本節はそれらを変更しない）。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（6 概念、管理カテゴリの narrower と scopeNote、
  総称 2 概念の scopeNote）
- `metadata/taxonomy/iptc-mapping.yaml`（6 概念を `deliberately_unmapped` の別群に追加。version 1.9.0）
- `metadata/queries/query-registry.json`（12 query）
- `docs/data-dictionary.md` §6.4（写し）
- `docs/provenance/query-inventory.md`（6 語の 2 query の証拠欄）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（`registration_basis` /
  `identity_caveat` / `limitations` / `distribution.reason`）
- 同 study の `README.md`・`methodology.md`（対象化合物表・被覆件数・未収集の注記）
- `project.json` の `queryDesign`（写し）と `dataCoverage.auditNote`
- `metadata/provenance/evidence-registry.json`（出所 5 件の追加、taxonomy / query registry の hash 再観測）
- `exports/taxonomy/*`（再生成）
- 公開ページ `publication/research_thca.html` / `research_thcb.html`（位置づけの記述のみ。
  `requires_review` は維持）
- `tests/validation/test_registration_state_batch.py` と新規テスト
- `ISS-20261111-TAX-041`（新規 issue）

### 限界と再検討条件

- 個々の Google Trends / YouTube 結果を Δ8 体・Δ9 体、THCA-A・THCA-B のどちらかに帰属させられない。
  系列は登録文字列の一致を測る。
- Δ8-THCA は構造・命名の出所を本変更で確認していない。Δ8 系列の A/B 配置、Δ8-THCB の立体化学、
  各語の CAS は未検証である。
- 天然存在、合成経路、薬理、安全性、臨床効果は主張しない。THCB-O-acetate の構造グループ該当は
  法令上の構造定義であり、それらの主張ではない。
- 各語について検証済み外部識別子が得られた場合は、本台帳に根拠を追記し、その根拠が支えるカテゴリへ
  移すかどうかを判断する。Δ8-THCA は構造・命名の出所の確認が先である。
- 6 概念の収集は別作業であり、計画・窓・staging declaration・L1 gate・採用を必要とする。

---

## 2026-11-15 — 化合物の外部識別子 crosswalk を registry 照合で修正（ISS-20261115-TAX-043）

識別子監査で指摘された 9 概念（`compound_cbd` / `compound_thc` / `compound_cbg` /
`compound_cbn` / `compound_cbc` / `compound_thcv` / `compound_cbdv` /
`compound_anandamide` / `compound_2ag`）の `skos:exactMatch` を、2026-11-15 に ChEBI と
Wikidata の live record と照合した。9 概念すべてで旧値は参照先の化合物と一致しなかった。
本節は修正後の値、旧値の実体、検証方法、未決の範囲を記録する。対象は化合物識別子と
その写し（IPTC 対応表）だけで、経路／由来の分類、query、run、被覆、公開状態は変えていない。

### 旧値が実際に指していたもの

| concept | 旧 `skos:exactMatch` | 旧値の実体（2026-11-15 照会） | 修正後 |
|---|---|---|---|
| `compound_cbd` | `chebi:33669` / `wikidata:Q141452` | metallacycloalkanes（金属を環員とする化合物クラス。構造なし）/ Disraeli（ケベック州の都市） | `chebi:69478` / `wikidata:Q422917` |
| `compound_thc` | `chebi:32927` / `wikidata:Q141629` | nonadecane（C19H40）/ Reifenberg（ラインラント＝プファルツ州の自治体） | `chebi:66964` / `wikidata:Q190067` |
| `compound_cbg` | `chebi:32927` / `wikidata:Q422432` | nonadecane / Aktion Regen（開発協力団体） | `chebi:69477` / `wikidata:Q412122` |
| `compound_cbn` | `wikidata:Q415237` | Wikimedia の曖昧さ回避ページ | `chebi:3360` / `wikidata:Q265831` |
| `compound_cbc` | `wikidata:Q422441` | Wikimedia の曖昧さ回避ページ | `chebi:3357` / `wikidata:Q410949` |
| `compound_thcv` | `wikidata:Q422449` | mycotoxins（マイコトキシンのクラス、ChEBI 25442） | なし（下記） |
| `compound_cbdv` | `wikidata:Q422426` | potassium fluoride（KF、ChEBI 66872） | `wikidata:Q1104117` |
| `compound_anandamide` | `chebi:52384` / `wikidata:Q409339` | zymosteryl oleate（C45H76O2）/ Wikidata が `missing` を返す（項目なし） | `chebi:2700` / `wikidata:Q410228` |
| `compound_2ag` | `chebi:64901` / `wikidata:Q295793` | mygalin（C21H27N3O6）/ Wikidata が `missing` を返す（項目なし） | `chebi:52392` / `wikidata:Q209320` |

`chebi:32927`（nonadecane）は CBG と THC の 2 概念が共有していた。`Q409339` と
`Q295793` は存在しない ID であり、監査では独立検証されていなかった。

### 採用したレコードと交差確認

ChEBI の accession・名称・標準 InChIKey と、Wikidata の label・P683（ChEBI ID）・
標準 InChIKey が同一構造を指すことを確認した。Wikidata の P683 が採用した ChEBI
accession と一致し、InChIKey が一致するものを採用した。

| concept | 採用レコード（evidence_id） | 名称 | 標準 InChIKey | 交差確認 |
|---|---|---|---|---|
| `compound_cbd` | `ev-chebi-69478` / `ev-wikidata-q422917` | cannabidiol | `QHMBSVQNZZTUGM-ZWKOTPCHSA-N` | Q422917 の P683 = 69478、PubChem CID 644019 |
| `compound_thc` | `ev-chebi-66964` / `ev-wikidata-q190067` | Δ9-tetrahydrocannabinol | `CYQFCXCEBYINGO-IAGOWNOFSA-N` | Q190067 の P683 = 66964、PubChem CID 16078 |
| `compound_cbg` | `ev-chebi-69477` / `ev-wikidata-q412122` | cannabigerol | `QXACEHWTBCFNSA-SFQUDFHCSA-N` | Q412122 の P683 = 69477、PubChem CID 5315659 |
| `compound_cbn` | `ev-chebi-3360` / `ev-wikidata-q265831` | Cannabinol | `VBGLYOIFKLUMQG-UHFFFAOYSA-N` | Q265831 の P683 = 3360、PubChem CID 2543 |
| `compound_cbc` | `ev-chebi-3357` / `ev-wikidata-q410949` | Cannabichromene | `UVOLYTDXHDXWJU-UHFFFAOYSA-N` | Q410949 の P683 = 3357、PubChem CID 30219 |
| `compound_cbdv` | `ev-wikidata-q1104117` | cannabidivarin（description が `group of stereoisomers`） | `REOZWEGFPHTFEI-UHFFFAOYSA-N` | CAS 24274-48-4、PubChem CID 91158 |
| `compound_anandamide` | `ev-chebi-2700` / `ev-wikidata-q410228` | anandamide | `LGEQQWMQCRIYKG-DOFZRALJSA-N` | Q410228 の P683 = 2700、PubChem CID 5281969 |
| `compound_2ag` | `ev-chebi-52392` / `ev-wikidata-q209320` | 2-arachidonoylglycerol | `RCRCTBLIHCHWDZ-DOFZRALJSA-N` | Q209320（label `glyceryl 2-arachidonate`）の P683 = 52392、PubChem CID 5282280 |

**粒度の扱い。** CBN と CBC のレコードは標準 InChIKey に立体化学層を持たず、立体化学を
指定しない概念と粒度が一致する。CBD・THC・CBG のレコードは天然の立体異性体を指すが、
レコードの名称自体が修飾なしの物質名（`cannabidiol` / `Δ9-tetrahydrocannabinol` /
`cannabigerol`）であり、taxonomy の概念名と一致する。CBD と THC の概念名が特定の
立体異性体を指すという主張ではなく、registry の修飾なしレコードとの対応である。

**anandamide / 2-AG の Wikidata 値。** `Q409339` / `Q295793` は存在しないため削除した。
採用した `Q410228` / `Q209320` は監査の候補一覧には無かったが、Wikidata の P683 と
標準 InChIKey の 2 系統で ChEBI レコードと一致したため採用した。この 2 件の採用は
監査の候補範囲を超える判断であり、owner のレビュー対象として issue に明記する。

### 未決の範囲: `compound_thcv`

`compound_thcv` は `skos:exactMatch` を持たない。概念は「Tetrahydrocannabivarin (THCV)」
という修飾なしの名称で、Δ8/Δ9 の位置異性体も立体化学も指定していない。検証した
レコードはいずれも Δ9 を指す:

- `ev-chebi-755032` tetrahydrocannabivarin: 標準 InChIKey `ZROLHBHDLIHEMS-HUUCEWRRSA-N`（Δ9、立体化学定義あり）。
- `ev-wikidata-q76009679` Tetrahydrocannabivarin: 同じ InChIKey。CAS 31262-37-0、PubChem CID 93147。
- `ev-wikidata-q254768` tetrahydrocannabivarin: `ZROLHBHDLIHEMS-UHFFFAOYSA-N`（Δ9 の骨格、立体化学未指定）。CAS 28172-17-0、PubChem CID 34180（6a,7,8,10a-tetrahydro-6,6,9-trimethyl-3-propyl-6H-dibenzo(b,d)pyran-1-ol）。

いずれかを付けると概念が Δ9 を指すという主張になる（ChEBI と Q76009679 はさらに
立体化学も固定する）ため、対応を削除して概念の scopeNote に理由を記録した。
2026-11-15 の OLS4 ChEBI 検索は `tetrahydrocannabivarin` に 1 件、
`delta-8-tetrahydrocannabivarin` に 0 件、Wikidata の `wbsearchentities` は 2 件
（Q254768 / Q76009679）を返した。これはその時点の応答であり、不在の証明ではない。
owner が概念を Δ9-THCV に狭める場合は `chebi:755032` と `Q76009679` の組が候補になる。
異性体未指定のファミリーのままにする場合は、Δ8 側を含む単一レコードが無いため
未対応を維持する。

### `compound_cbdv` を立体異性体グループにした理由

CBDV の ChEBI レコードは 1 件だけで、`CHEBI:182159` は `(1R,6R)` の立体化学を定義した
レコードである（`REOZWEGFPHTFEI-JKSUJKDBSA-N`、Wikidata `Q76421750` が同じ構造）。
概念は立体化学を指定しないため、立体異性体のグループとして明示された
`Q1104117`（`REOZWEGFPHTFEI-UHFFFAOYSA-N`）を `skos:exactMatch` とし、ChEBI の
立体特異的レコードと `Q76421750` は付けない。この判断は「概念の粒度と一致する
グループが検証できた場合はグループを使う」という規則による。

### 変更しないもの

- `compound_identity_unverified` の membership と logic、および P1 の経路／カテゴリ評価
  （`CBX`、`CRDH`、`CRDP`、`H4CBH`、`HHBD`、`HHCH`、`THCNM`、`THC-O`、`THCP`、`THCJD`、
  `THCPO`、THCA / THCB の 6 個別トピック等）。
- query ID、検索語と概念の対応、run ID、catalog、raw data、source coverage、family scope、
  collection design、release scope、publication status。
- `compound_thcv` の label・altLabel・query。scopeNote の追加と exactMatch の削除だけを行う。
- `compound_cbdv` の label・altLabel・query。

### 限界と再検討条件

- 確認したのは ChEBI と Wikidata の record だけである。CAS は Wikidata の P231 経由で
  参照した値であり、CAS Registry を直接照会していない。PubChem は Wikidata の P662 と
  PubChem PUG REST の応答で確認した。
- レコードの名称・構造が一致しても、検索結果や製品の内容を同定する根拠にはならない。
  系列が測るのは登録文字列への一致だけである。
- 今回は 9 概念の外部識別子だけを対象とした。他の概念の crosswalk の再監査は別作業である。
- `compound_thcv` の粒度（Δ9 に狭めるか、異性体未指定ファミリーを維持するか）は owner の
  scope 判断であり、本変更では決めていない。
- registry は更新されるため、再検証の時期と対象は issue に残す。

### 同時に更新した層

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（9 概念の `skos:exactMatch`、
  `compound_thcv` / `compound_cbdv` の scopeNote、scheme の `dct:modified`）
- `metadata/taxonomy/iptc-mapping.yaml`（写しの識別子、coverage の理由、version 1.10.0）
- `exports/taxonomy/*`（`bash scripts/export/export-taxonomy.sh` で再生成）
- `tests/validation/test_registration_state_batch.py`（CBC / CBDV の固定値を更新）
- `tests/validation/test_compound_identifier_crosswalk.py`（新規）
- `datasets/cannabinoid-raw-collection/README.md`、`project.json` の identityNote、
  `docs/provenance/query-inventory.md`（写しの QID）
- `metadata/provenance/evidence-registry.json`（ChEBI / Wikidata の record と taxonomy の再観測）
- `ISS-20261115-TAX-043`

---

## 2026-11-15 — 辞書全体の形式精度を標準化（ISS-20261115-TAX-044）

2026-11-15、owner は study の辞書全体（登録 36 検索トピック）に精度基準を一貫適用することを指示した。
各辞書項目は証拠が支える個別の構造形式を表し、位置異性体（Δ8 / Δ9、A / B）、酸／中性／エステル、立体化学は
出所が支える粒度までしか区別しない。総称語・ファミリー語・市場語は個別形式と分け、証拠が形式を支えても owner が
登録語として列挙していないものは未登録・未収集の候補として明示する。既存 raw run と query / run の割当ては保持する。

**本節は文書と台帳の記録である。** taxonomy の概念・分類・label・`exactMatch`、query registry、raw、catalog、被覆、
release slice、公開状態を変更していない。新しい概念・query・run も作成していない。

### 分離した軸

1. **検索語** — owner が登録した文字列。系列はその文字列への一致を測る。
2. **構造形式** — 位置異性体・酸／中性／エステル・立体化学。出所が支える粒度まで。
3. **被覆状態** — adopted run の有無。形式・同一性の状態と同じ列に置かない。

README は「構造形式辞書」（概念が表す 40 形式）、「検索語 → 形式 crosswalk」（63 行、語の範囲 5 値）、
「term-to-query map」（concept・query・被覆のみ）、「未登録・未収集の候補形式」（初期 27 行、後続の ISS-20261115-TAX-045 で登録済み）に分かれた。
term-to-query map から `skos:broader` 列を外したが、行の語・concept・query ID・被覆状態は変更していない。

### 形式辞書の粒度

個別形式として載せたのは、検証済み外部レコードに対応する 9 形式（`Δ9-THC` / `CBD` / `CBG` / `CBGA` / `CBN` / `CBC` /
`CBE` / `CBL` / `CBDV`）と、owner が検索トピックとして形式名を登録した 5 形式（`Δ9-THCA-A` / `THCA-B` / `Δ8-THCA` /
`Δ8-THCB` / `Δ9-THCB`）である。後者は単一の外部レコードを選択していないため「同一性未確認」とし、`Δ8-THCA` は
A/B カルボキシル配置の出所が無いため「部分指定」とした。

異性体未指定のファミリー（`THCP` / `THCJD` / `THCPO` / `THCB-O-acetate`）と `THCV` / `THCH`、市場語・未確認語は形式辞書に
載せていない。形式が確定しない語を形式の一覧に混ぜないためである。`THCB-O-acetate` は 2 つの異性体を包含する
family であり、個別形式ではない。

立体化学は、レコードが天然の立体異性体を指す場合でも概念名が特定の立体異性体を指定する主張ではない、という
2026-11-15 節「粒度の扱い」の判断を維持した。CBN・CBC はレコードに立体化学層が無いため未指定、CBDV は
立体異性体グループ（Q1104117）、CBL は立体化学の扱いが異なる 2 CAS が併存するため未指定とした。
`compound_thcv` の粒度（Δ9 に狭めるか）は未決のままである（同節、ISS-20261115-TAX-043）。

### TAX-044 時点の未登録候補インベントリ（TAX-045 で 27 行を登録済み）

2026-11-15 の初期棚卸し時点では未登録だった 27 形式と証拠根拠を記録する。その後の owner 指示 ISS-20261115-TAX-045 により、
27 形式すべてを taxonomy concept / query として登録した。以下の表の「候補」は初期棚卸し時の状態を指し、現行状態は後続節に記す。
既存系列をこれらの形式へ帰属させない。

| 親の登録語 | 候補形式 | 記録済みの根拠（再掲） |
|---|---|---|
| `THCP` | `Δ8-THCP` / `Δ9-THCP` | Δ9: PubChem CID 6453074 / CAS 54763-99-4 / UNII WTK87HN3LG / Wikidata Q85806080。Δ8: PubChem CID 44307335 / CAS 51768-60-6 / UNII Q6P6W9SNR2 / Wikidata Q141317106。Δ9 は植物からの単離（Citti et al. 2019）、Δ8 は 2026 年の製品検出（TAX-042） |
| `THCJD` | `Δ8-THCJD` / `Δ9-THCJD` | Δ9: PubChem CID 155318984 / CAS 2552798-63-5。Δ8: PubChem CID 102024084 / CAS 431041-39-3 / Wikidata Q114242092。国内流通製品から NMR 同定（Tanaka & Kikura-Hanajiri 2024、TAX-042） |
| `THCPO` | `Δ8-THCP-O-acetate` / `Δ9-THCP-O-acetate` | 両形式とも令和6年厚生労働省令第81号の別添に構造グループとして列挙。Δ9: PubChem CID 172677450 / CAS 2829292-82-0 / Wikidata Q122689235（製品同定あり、Tanaka et al. 2025）。Δ8: PubChem CID 172874392（CAS / GSRS / Wikidata 未確認、製品同定は未確認）（TAX-042） |
| `THCB-O-acetate` | `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` | PubChem CID 172871934 / 172875699。令和6年厚生労働省令第81号の別添に列挙。製品中の分析同定は未確認。Tanaka et al. 2025 の `Δ9-THCB-O-butanoate` は別エステルで、acetate 行に含めない（TAX-042） |
| `THC` | `Δ8-THC` | 命名標準の位置異性体（`docs/specs/thc-nomenclature-standard.md` の 7 分類）。2024 年厚生労働省令は Δ9 系列（6a,7,8,10a-テトラヒドロ）と Δ8 系列（6a,7,10,10a-テトラヒドロ）を別の構造グループとして定義する（麻薬を除く）。知識グラフは CAS 5957-75-7 と天然存在 confirmed を記録するが、form-level の外部 record は taxonomy に未選択 |
| `THC` | `Δ6a(10a)-THC` / `Δ6a(7)-THC` / `Δ7-THC` / `Δ10-THC` / `Δ9(11)-THC` | 命名標準の 7 分類（WHO Annex 1）。`metadata/taxonomy/thc-regulatory-knowledge-graph.json` は各形式に規制区分「麻薬」・天然存在未確認を記録し、Δ10 のみ CAS 50554-36-6。他の 4 形式は form-level 外部識別子を未選択。法令・規制の記録で、製品分析同定ではない |
| `THCV` | `Δ9-THCV` / `Δ8-THCV` | Δ9: ChEBI 755032 / Wikidata Q76009679（CAS 31262-37-0、PubChem CID 93147）、立体化学未指定の Q254768。Δ8: 規制資料の列挙のみで registry record 未確認（TAX-043） |
| `THCJD`（C8） | `THCJD-O-acetate` | MHLW 資料（2024 年の指定薬物関連資料）に記載。法令の構造グループで、製品同定ではない。Δ8/Δ9 の別個の構造は確認しておらず、TAX-045 で異性体未指定の検索トピックとして登録した。今後 Δ8/Δ9 を分割する場合は追加の owner 決定を要する |
| `THCH` | `Δ8-THCH` / `Δ9-THCH` | `research/regulatory-status/THCH.md` §1 が消費者庁資料に基づき Δ8/Δ9 を指定薬物の対象として記録（個別指定 2023-08-04、包括指定 2023-09-10）。法令の構造グループで、製品分析同定ではない。form-level 外部識別子は未選択 |
| `HHC` | `9(R)-HHC` | PubChem CID 11067065 / CAS 36403-90-4、立体配置 (6aR,9R,10aR)。WHO 47th ECDD (2024) §2C が CBD 由来製品の主要エピマーの一つとして記録。特定製品の分析同定ではない |
| `HHC` | `9(S)-HHC` | PubChem CID 14378541 / CAS 36403-91-5、立体配置 (6aR,9S,10aR)。WHO 47th ECDD (2024) §2C が CBD 由来製品の主要エピマーの一つとして記録。特定製品の分析同定ではない |
| `HHC` | `(6aS,9S,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=S / 10a=S。(6aR,9R,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9R,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=R / 10a=S。(6aR,9S,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9S,10aR)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=S / 10a=R。(6aR,9R,10aS)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9R,10aR)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=R / 10a=R。(6aR,9S,10aS)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aR,9S,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=R / 9=S / 10a=S。(6aS,9R,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aR,9R,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=R / 9=R / 10a=S。(6aS,9S,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |

この表は、今回のレビュー範囲で証拠が支える候補を列挙する。THC の他の位置異性体 5 形式は命名標準・知識グラフの記録で、form-level の外部識別子を検証していない。
THCH の Δ8/Δ9 は法令の構造グループの記録で、製品同定ではない。HHC は 9(R)/9(S) の 2 エピマーに加え、WHO が可能な配置として図示する他の 6 立体異性体も
各 1 行で列挙し、各配置とエナンチオマー関係を明記した上で、製品成分としての証拠が無いことを記す。**列挙は登録・収集・公開の許可ではない。**

### HHC 立体異性体の外部確認（2026-11-15）

リポジトリ内の [`research/regulatory-status/HHC.md`](../../research/regulatory-status/HHC.md) は HHC を指定薬物としてグループ単位で記録し、
化学名を示すが、立体異性体の配置・数・個別 record は列挙しない。`compound_hhc` の scopeNote もグループ単位である。
このため、候補表の HHC 行は次の外部資料で確認した。

- **WHO 47th ECDD (2024) critical review, “Hexahydrocannabinol” §2C Stereoisomers**（Geneva, 14–18 October 2024、advance copy、
  https://cdn.who.int/media/docs/default-source/controlled-substances/47th-ecdd/hexahydrocannabinol-47th-ecdd-critical-review-public-version.pdf）。
  HHC は 3 個の立体中心（6a, 9, 10a）を持ち、8 立体異性体（4 対のエナンチオマー）が可能である。6a/10a を (−)-trans-Δ9-THC と同じ
  (6aR,10aR) に保つ 2 エピマー、(6aR,9R,10aR)（9R / 9β-HHC）と (6aR,9S,10aR)（9S / 9α-HHC）が CBD 由来製品の主要成分とされる。
  WHO の同 review は市販品の平均 9R:9S 比を 1.4:1 と記録する（Executive summary）。CAS 36403-90-4（9R）、36403-91-5（9S）。他の 6 配置は
  (6aS,9S,10aS) / (6aS,9R,10aS) / (6aS,9S,10aR) / (6aS,9R,10aR) / (6aR,9S,10aS) / (6aR,9R,10aS) で、
  可能な立体異性体として図示されるが、製品成分としての記載はない。
- **PubChem PUG REST（2026-11-15 観測）**: name query `9(R)-hexahydrocannabinol` → CID 11067065、
  IUPAC `(6aR,9R,10aR)-6,6,9-trimethyl-3-pentyl-6a,7,8,9,10,10a-hexahydrobenzo[c]chromen-1-ol`、InChIKey `XKRHRBJLCLXSGE-DJIMGWMZSA-N`。
  `9(S)-hexahydrocannabinol` → CID 14378541、IUPAC `(6aR,9S,10aR)-...`、InChIKey `XKRHRBJLCLXSGE-USXIJHARSA-N`。
  CAS 36403-90-4 / 36403-91-5 の name query も同じ CID を返した。C9 未指定の PubChem CID 16050328（CAS 946512-74-9、
  IUPAC `(6aR,10aR)-...`、C9 未指定）は候補行に使っていない。
- **証拠レベルの区別**: WHO の記述は化学・市販品組成に関する review であり、本 study が収集・分析した製品の同定ではない。
  PubChem は registry record であり、市場流通・製品含量の証拠ではない。法令・規制記録（HHC.md の指定薬物指定）は構造グループの規制状態で、
  立体異性体の同定ではない。候補表の「製品分析」列は、文献が特定製品を分析した場合だけその事実を書き、WHO の市販品組成記述を
  本 study の製品同定に読み替えない。
- **限界**: 他の 6 配置の個別 CAS / PubChem record は選択していない。WHO の図示は可能な配置の列挙であり、市場製品での存在証明ではない。
  初期インベントリでは他の 6 配置を 1 グループ行にまとめたが、owner 指示 ISS-20261115-TAX-045 により各配置を個別の concept/query として登録し、README でも 1 配置 1 行に分けた。外部 record は 2026-11-15 の応答で、将来の変更を監視しない。

### ISS-044 の変更対象外

- `metadata/taxonomy/compound-taxonomy.skos.jsonld` の概念・分類・label・`exactMatch`・scopeNote、`exports/taxonomy/*`。
- `metadata/queries/query-registry.json` / `query-variants.json` の query ID・canonical_text・status・variant。
- raw run、run metadata、catalog、declaration、被覆状態、収集計画、release slice、公開状態。
- `ISS-20261115-TAX-043` の crosswalk 修正とその evidence / テスト。
- P1（TAX-040）の経路／カテゴリ評価。

### ISS-044 終了時点の未決事項

- `compound_thcv` の粒度（Δ9 に狭めるか、異性体未指定のままか）。
- `Δ8-THCA` の A/B カルボキシル配置を確定する構造・命名の出所。
- `Δ8-THCP-O-acetate` / `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` の製品中の分析同定。
- `THCJD-O-acetate` は後続の ISS-20261115-TAX-045 で異性体未指定の検索トピックとして登録済み。Δ8/Δ9 に分割するかは別判断である。
- `Δ8-THC` / `Δ8-THCV` の外部識別子の検証。`Δ8-THC` は知識グラフの CAS 5957-75-7 を記載したが外部 record は未再検証。
- **新たに列挙した候補の未解決点**: THC の他の位置異性体 5 形式は form-level 外部識別子を検証していない（Δ10 は知識グラフの CAS 50554-36-6 のみ）。
  THCH の Δ8/Δ9 は法令の構造グループの記録で、製品分析同定ではない。HHC の他の 6 立体異性体は WHO が可能な配置として図示するが、
  製品成分としての証拠・個別 registry record は無い。9(R)/9(S) および他の 6 配置は ISS-20261115-TAX-045 で個別 concept/query として登録済みだが、登録は製品同定や収集を意味しない。
- **既知の mirror 不一致**: `project.json` の `queryDesign.compounds` に `CBX` が無く、registry との不一致が残る。
  `Δ8-THC` は ISS-20261115-TAX-045 で登録され、mirror の既存記載にも query ID と未収集状態の注記を加えた。27 語の登録により `CBX` 以外の scope 同期は行った。

### 同時に更新した層

- `datasets/cannabinoid-raw-collection/README.md`（概要の四層化、形式辞書、crosswalk、初期候補表（27 行、後続 ISS-045 で登録）、注記、被覆表の列整理、関連）
- `docs/provenance/query-inventory.md`（台帳の対象範囲の 1 文）
- `tests/validation/test_dictionary_form_precision.py`（新規、候補表の 27 行・重複なし・証拠種別を固定）
- `docs/audits/g6-git-tracking-inventory.json`（README ハッシュのみ）
- `ISS-20261115-TAX-044`

## 未修正の既知事項

1. `metadata/taxonomy/iptc-mapping.yaml` の `compound_mapping` は部分収載（`cbc`/`thcv`/`cbdv`/`crdh` も未収載）。
2. `THCH` の日本語名は文書間で表記ゆれがある（`THCH.md` を標準として採用）。
3. `compound_rare` は `skos:narrower` を持たない空カテゴリ（現状の登録化合物には該当なし）。
4. `compound_thcv` は外部識別子が未対応である。概念が Δ8/Δ9 と立体化学を指定せず、
   検証済みレコードがいずれも Δ9 のため（本台帳 2026-11-15 節、ISS-20261115-TAX-043）。
   CBGA の `chebi:67081` は 2026-11-11 に検証済み（cannabigerolic acid）。

## 派生物の同期

- `exports/taxonomy/*.ttl` / `.schema.jsonld` / `iptc-mapping.yaml` は
  `bash scripts/export/export-taxonomy.sh` で taxonomy から再生成する（手で編集しない）。
  概念の件数は `tests/validation/test_taxonomy_consistency.py` が固定している。

## 次の作業

- 追加した5化合物のクエリは 2026-10-13 に `metadata/queries/query-registry.json` へ登録済み
  （10件。証拠は `docs/provenance/query-inventory.md` §1）。
- `compound_thcnm` の収集は 2026-11-04 に開始した（Google Trends の 12ヶ月・5年、YouTube の `THCNM リキッド` / `THA リキッド`）。収集は登録文字列への一致を測るものであり、同一性の確認ではない。同一性は未確認のままで、構造の確認は別作業（ISS-20261104-TAX-028）。
- 上記「未修正の既知事項」の扱いを決める。
- `compound_thcp` / `compound_thcjd` / `compound_thcpo` の「異性体未指定のファミリー（同族体、およびそのエステル体）」を taxonomy の
  独立した state として形式化するかを決める（本台帳 2026-11-11 節の未決事項）。現状は管理
  カテゴリ内の文書化された検索語の範囲として扱っており、新しいカテゴリは作っていない。

## 2026-11-15 — 候補形式 27 形式の登録（ISS-20261115-TAX-045）

owner は 2026-11-15、study README の「未登録・未収集の候補形式」に棚卸しした **27 行を検索トピックとして登録する**ことを明示した。本節は登録の根拠と限界を台帳に固定する。登録は検索文字列の固定であり、物質の同定でも収集の許可でもない。

### 命名規則

`skos:notation` は `compound_` + owner の語を小文字化し `Δ`→`delta`、非英数字の**連続**を 1 つの `_` に置換し前後の `_` を除いたもの。既存の `compound_delta9_thca_a` / `compound_10_oh_hhc` / `compound_thc_o` と同じ規則で、連続置換の明示だけが追加の明確化である（`Δ6a(10a)-THC` のような括弧とハイフンが隣接する語で二重 `_` を作らない）。`@id` は notation の `_` を `-` にした `jptr:compound-…`。query ID の slug は語を小文字化し `Δ`→`delta` としたうえで、既存の 27 語で実際に使った次の規則で作る。

1. 立体配置を囲む先頭の括弧と C-9 エピマーの括弧は外す（`(6aS,9S,10aS)-HHC` → `6as-9s-10as-hhc`、`9(R)-HHC` → `9r-hhc`）。
2. 位置番号を囲む括弧は、内側の locant の前に `-` を置く（`Δ6a(10a)-THC` → `delta6a-10a-thc`、`Δ6a(7)-THC` → `delta6a-7-thc`、`Δ9(11)-THC` → `delta9-11-thc`）。
3. `,` と既存の `-` は `-` とし、連続する `-` を 1 つに畳み、前後の `-` を除く。既存のハイフンは保持する（`Δ8-THCP-O-acetate` → `delta8-thcp-o-acetate`）。

これに `-general-ja` / `-liquid-ja` を付ける。**安定した既存 query ID は改名しない。**

### 配置

27 概念はすべて `jptr:compound-identity-unverified`（管理上の登録状態カテゴリ）に置き、カテゴリの `skos:scopeNote` に「配置ごとの registry record も製品同定も無い特定の立体配置」と「個々の位置異性体の構造を列挙していない異性体未指定アセテート」の 2 ケースを追加した。配置は経路／由来・天然存在・化学クラス・構造・別名・規制状態を主張しない。27 概念には識別子プロパティも `skos:exactMatch` も割り当てず、`skos:related` も張らない。scopeNote に引用した CAS・PubChem CID・UNII・ChEBI ID・Wikidata QID・IUPAC 名は台帳の記録であり、概念の識別子ではない。棚卸し上の親語（`THC` / `THCP` / `THCJD` / `THCPO` / `THCB-O-acetate` / `THCH` / `HHC` / `THCV`）との関係は候補表の整理であり、構造・同義の主張ではない。

### 形式ごとの根拠の種類と限界

先行レビューが記録した識別子は以下に保持するが、**本変更で外部 registry に対して再検証していない**。したがって概念には付けない（不在の断定ではない）。

| 形式 | 根拠の種類 | 先行レビューが記録した識別子（本変更では未再検証） | 残る未確認 |
|---|---|---|---|
| `Δ8-THCP` | registry record + 製品検出（文献） | PubChem CID 44307335 / CAS 51768-60-6 / UNII Q6P6W9SNR2 / Wikidata Q141317106 | 単一レコードの選択、本研究の製品分析 |
| `Δ9-THCP` | registry record + 植物単離（Citti et al. 2019） | PubChem CID 6453074 / CAS 54763-99-4 / UNII WTK87HN3LG / Wikidata Q85806080 | 単一レコードの選択 |
| `Δ8-THCJD` / `Δ9-THCJD` | registry record + 製品分析（Tanaka & Kikura-Hanajiri 2024） | CID 102024084 / CAS 431041-39-3 / Wikidata Q114242092；CID 155318984 / CAS 2552798-63-5 | 単一レコードの選択、本研究の観測 |
| `Δ8-THCP-O-acetate` | 法令の構造グループ（令和6年厚生労働省令第81号 別紙、麻薬を除く）+ registry record | PubChem CID 172874392 | CAS / GSRS / Wikidata、製品同定 |
| `Δ9-THCP-O-acetate` | 同上 + 製品分析（Tanaka et al. 2025、DOI 10.1002/dta.3883） | PubChem CID 172677450 / CAS 2829292-82-0 / Wikidata Q122689235 | 単一レコードの選択 |
| `Δ8-THCB-O-acetate` | 法令の構造グループ + registry record | PubChem CID 172871934 | CAS / GSRS / Wikidata、製品同定 |
| `Δ9-THCB-O-acetate` | 法令の構造グループ + registry record | PubChem CID 172875699 | CAS / GSRS / Wikidata、製品同定（同定済みの `Δ9-THCB-O-butanoate` は**別エステル**で本項の対象外） |
| `Δ8-THC` | 命名標準 + 知識グラフ + 法令の構造グループ（Δ8 系列 6a,7,10,10a-テトラヒドロ） | 知識グラフの CAS 5957-75-7 | form-level 外部レコードの選択 |
| `Δ6a(10a)-THC` / `Δ6a(7)-THC` / `Δ7-THC` / `Δ9(11)-THC` | 命名標準（7 分類）+ 知識グラフ | なし（CAS 未記録） | form-level 外部識別子、製品分析 |
| `Δ10-THC` | 命名標準 + 知識グラフ | 知識グラフの CAS 50554-36-6（**未再検証**） | 外部レコードの再検証、製品分析 |
| `Δ9-THCV` | registry record（TAX-043 が検証） | ChEBI 755032 / Wikidata Q76009679（CAS 31262-37-0、PubChem CID 93147）。立体化学未指定の Q254768 もある | `compound_thcv` の粒度（owner 判断） |
| `Δ8-THCV` | 規制資料（指定薬物の列挙） | なし（2026-11-15 の ChEBI 検索は 0 件） | registry record |
| `THCJD-O-acetate` | 法令の構造グループ（MHLW の指定薬物関連資料） | なし | Δ8/Δ9 の構造の列挙、製品同定 |
| `Δ8-THCH` / `Δ9-THCH` | 法令の構造グループ（消費者庁の THCH 資料。個別指定 2023-08-04・包括指定 2023-09-10） | なし | registry record、製品同定 |
| `9(R)-HHC` / `9(S)-HHC` | registry record + WHO 47th ECDD (2024) §2C（主要 2 エピマー） | CID 11067065 / CAS 36403-90-4 / InChIKey `XKRHRBJLCLXSGE-DJIMGWMZSA-N`；CID 14378541 / CAS 36403-91-5 / InChIKey `XKRHRBJLCLXSGE-USXIJHARSA-N` | 単一レコードの選択、特定製品の同定 |
| 他の 6 立体配置 | WHO 47th ECDD (2024) §2C（8 立体異性体の図示） | 個別に選択していない | 配置ごとの registry record、製品同定 |

### 証拠の種類を混ぜない

- 法令の構造グループへの該当は**法令上の構造の事実**であり、製品検出でも、本研究の観測でも、検索結果の分類でもない。
- WHO 47th ECDD (2024) §2C は**可能な配置の集合を示すレビュー**であり、配置ごとの registry record でも製品同定でもない。
- 知識グラフの記載は規制・命名の記録であり、form-level の構造同定ではない。
- 製品分析（文献）は特定製品についての報告であり、本研究の製品分析でも、任意の検索結果についての主張でもない。

### 変更しない層

既存 query の `query_id`・`canonical_text`・`status`・run 割当ては変更していない。総称 `THC` / `THCA` / `THCB`、ファミリー `THCP` / `THCJD` / `THCPO` / `THCB-O-acetate`、`THCV` / `THCH` / `HHC` の概念・分類・query も据え置く。`compound_thcv` の粒度、`compound_hhc` の立体異性体粒度は本変更の対象外である。raw・catalog・declaration・被覆状態・release slice・公開状態は変更していない。

### 未決事項

1. **管理カテゴリからの移動条件**: 27 概念はいずれも単一の検証済み外部レコードを選択していない。候補は (a) `Δ9-THCV` / `Δ9-THCP` / `9(R)-HHC` / `9(S)-HHC` に検証済み識別子を付けるか、(b) 管理カテゴリのまま検索語の記録に留めるか。識別子の選択は別作業である。
2. **`THCJD-O-acetate` の Δ8/Δ9 分割**: 法令の別個の構造が確認できれば分割は可能だが、本変更では分割せず、owner の追加判断を要する。
3. **`Δ8-THCA` の構造・命名の出所**（TAX-044 からの継続）と、`Δ8` エステル体の製品分析証拠（`Δ8-THCP-O-acetate` / `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate`）は引き続き未確認である。
4. **`project.json` mirror の既知の不一致**: `CBX` は registry にあるが mirror に無い（本変更では触れていない）。`Δ8-THC` は本変更で query を得たため「mirror にあるが query が無い」状態は解消した。
