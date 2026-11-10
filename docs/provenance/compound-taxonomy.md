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
（`compound_set` で未収集を宣言）、study README / methodology、`project.json` の `queryDesign`。

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
| 外部識別子 | `wikidata:Q422441` / `wikidata:Q422426` | 既存 `skos:exactMatch`。追加の照会はしていない |
| 登録 query | `cbc-general-ja` / `cbc-liquid-ja` / `cbdv-general-ja` / `cbdv-liquid-ja` | 既存規約（`<compound>-general-ja` / `<compound>-liquid-ja`）の適用 |
| 収集状態 | 未収集（run 0） | 依頼は対象集合とクエリ設計の拡張であり、収集を含まない |

### 未収集であることの扱い

- 4 query はいずれも **run 0** で、raw payload・staging declaration・catalog 登録・採用はいずれも無い。
  **0 観測でも欠測でもない**（未収集。`docs/specs/raw-data-policy.md` が区別する「非保持・未収集・欠測・0 観測」のうち未収集）。
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
（`declared_not_yet_collected` に 2 化合物）、study README / methodology、`project.json` の
`queryDesign`（写し）、`metadata/provenance/evidence-registry.json`（query registry の hash 再観測）、
本台帳、ISS-20261110-TAX-039。

## 2026-11-11 — owner 指示バッチを「登録状態（同一性未確認）」カテゴリで登録（ISS-20261111-TAX-040。TAX-027 の非登録判断を置換）

owner の明示的な scope 決定（2026-11-11 の列挙 15 語）に基づき、`cannabinoid-raw-collection`
の登録化合物集合を広げた。**この節は「何を登録し、何を登録していないか」を記録する。**
登録は検索文字列の固定であり、化学的同一性の確定ではない。

### 登録した 13 語と配置

`CBC` / `CBDV` は既存概念を再利用済み（下の 2026-11-10 節）であり、本節では扱わない。

| 語（owner 表記） | notation | `@id` | 配置（`skos:broader`） | 外部識別子 | 化学クラス | 収集状態 |
|---|---|---|---|---|---|---|
| `THCB` | `compound_thcb` | `jptr:compound-thcb` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `THCP` | `compound_thcp` | `jptr:compound-thcp` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `THCJD` | `compound_thcjd` | `jptr:compound-thcjd` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `THCPO` | `compound_thcpo` | `jptr:compound-thcpo` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `CBE` | `compound_cbe` | `jptr:compound-cbe` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `HHCPO` | `compound_hhcpo` | `jptr:compound-hhcpo` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `CBND` | `compound_cbnd` | `jptr:compound-cbnd` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `CBL` | `compound_cbl` | `jptr:compound-cbl` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `CBGa` | `compound_cbga` | `jptr:compound-cbga` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `CBP` | `compound_cbp` | `jptr:compound-cbp` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `10-OH-HHC` | `compound_10_oh_hhc` | `jptr:compound-10-oh-hhc` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `THXE` | `compound_thxe` | `jptr:compound-thxe` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |
| `THCA` | `compound_thca` | `jptr:compound-thca` | `compound_identity_unverified` | なし | 未形式化 | 未収集（run 0） |

- `skos:prefLabel` は **owner の表記をそのまま** en / ja に置いた（`CBGa` の小文字 `a`、
  `10-OH-HHC` のハイフンを保持）。コード名を化学名に置き換えない（H4CBH / HHBD / THCNM の前例）。
- `skos:altLabel` は `{term} リキッド` のみ。研究設計が `product_liquid` を required primary
  query としていることだけが根拠であり、他の綴りは根拠が無いので追加していない。
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
（`declared_not_yet_collected` に 13 化合物、`coverage_state_note` / `identity_caveat` / `limitations`）、
`docs/data-dictionary.md` §6.4、`metadata/taxonomy/iptc-mapping.yaml`
（13 語は `deliberately_unmapped`、カテゴリは `not_applicable`）、
`exports/taxonomy/*`（`bash scripts/export/export-taxonomy.sh` で再生成）、
study README / methodology、`project.json` の `queryDesign`（写し）、
`metadata/provenance/evidence-registry.json`（taxonomy と query registry の hash 再観測）、
`docs/provenance/query-inventory.md` §1、本台帳、`ISS-20261111-TAX-040`。

### 未収集であることの扱い

- 13 語の 26 query はすべて **run 0**。raw payload・staging declaration・catalog 登録・
  採用はいずれも無い。**0 観測でも欠測でもない**（未収集）。
- `make audit-youtube-coverage` は 15 化合物を `missing_compounds` として報告する
  （13 語 + CBC・CBDV）。`missing` は「採用済み run が無い」であり 0 観測ではない。
- 登録は「対象集合とクエリ設計の拡張」であり、収集・公開・release slice の拡張ではない。

### 未決事項

- 依頼文の「17 物質」と列挙 15 語の差（2 語）は未解消。**推測で補わない。**
- 13 語の同一性を何で確定するか（標準物質、供給元 SDS / COA、公的レジストリ）。
- `CBGa` / `THCA` / `10-OH-HHC` と既存概念の関係、`THCPO` / `HHCPO` の構造。
  いずれも根拠が得られるまで主張しない。

## 未修正の既知事項（本変更では触っていない）

1. `metadata/taxonomy/iptc-mapping.yaml` の `compound_mapping` は部分収載（`cbc`/`thcv`/`cbdv`/`crdh` も未収載）。
2. `THCH` の日本語名は文書間で表記ゆれがある（`THCH.md` を標準として採用）。
3. `compound_rare` は `skos:narrower` を持たない空カテゴリ（現状の登録化合物には該当なし）。

## 派生物の同期

- `exports/taxonomy/*.ttl` / `.schema.jsonld` / `iptc-mapping.yaml` は
  `bash scripts/export/export-taxonomy.sh` で taxonomy から再生成する（手で編集しない）。
  概念の件数は `tests/validation/test_taxonomy_consistency.py` が固定している。

## 次の作業

- 追加した5化合物のクエリは 2026-10-13 に `metadata/queries/query-registry.json` へ登録済み
  （10件。証拠は `docs/provenance/query-inventory.md` §1）。
- `compound_thcnm` の収集は 2026-11-04 に開始した（Google Trends の 12ヶ月・5年、YouTube の `THCNM リキッド` / `THA リキッド`）。収集は登録文字列への一致を測るものであり、同一性の確認ではない。同一性は未確認のままで、構造の確認は別作業（ISS-20261104-TAX-028）。
- 上記「未修正の既知事項」の扱いを決める。
