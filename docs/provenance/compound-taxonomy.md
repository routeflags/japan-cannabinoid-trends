# Compound Taxonomy — 追加記録と根拠

`metadata/taxonomy/compound-taxonomy.skos.jsonld` の変更履歴と、各概念を追加した根拠を記録する。
タクソノミー本体が正本であり、このファイルは**なぜその値を書いたか**を残すための台帳である。

---

## 2026-10-13 — 収集済みだが未登録だった5化合物を追加

対象: `HHC` / `HHCH` / `THCH` / `THC-O` / `CRDP`。
`datasets/cannabinoid-multi-trends/data/raw/google_trends/` に run が存在するのに
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

---

## 修正した既知事項（2026-10-13）

1. ✅ `compound-synthetic` の `skos:narrower` に `compound-crdh` を追加（親子関係の非対称を解消）。
2. ✅ `compound_h4cbh` / `compound_hhbd` を `compound-minor` から `compound-semisynthetic` へ移動。
   根拠: `datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv`
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

## 未修正の既知事項（本変更では触っていない）

1. `docs/data-dictionary.md` §6.4 の化合物カテゴリ表が不完全（`synthetic` 行が無く、
   `h4cbh` / `hhbd` / `crdh` / `crdp` / `hhch` が未掲載）。taxonomy を正本として表を
   補完するか要判断。
2. `exports/taxonomy/*.ttl` / `.schema.jsonld` は 2026-10-02 生成のままで、`compound-crdh`、
   本追加分5概念、および今回のカテゴリ移動が未反映
   （`bash scripts/export/export-taxonomy.sh` で再生成可能。release アーカイブの
   `INCLUDE_PATHS` に `exports/` は含まれない）。
3. `metadata/taxonomy/iptc-mapping.yaml` の `compound_mapping` は部分収載（`cbc`/`thcv`/`cbdv`/`crdh` も未収載）。
4. `THCH` の日本語名は文書間で表記ゆれがある（`THCH.md` を標準として採用）。
5. `compound_rare` は `skos:narrower` を持たない空カテゴリ（現状の登録化合物には該当なし）。

## 次の作業

- 追加した5化合物のクエリは 2026-10-13 に `metadata/queries/query-registry.json` へ登録済み
  （10件。証拠は `docs/provenance/query-inventory.md` §1）。
- 上記「未修正の既知事項」の扱いを決める。
