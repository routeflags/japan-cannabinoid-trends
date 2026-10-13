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
3. ✅ `metadata/datapackage.json` の `skos_scheme` を `jptr:compound-scheme` →
   `jptr:compound-taxonomy` に修正（実在する ConceptScheme の `@id`）。

親子対称性は機械的に確認済み（broader と narrower の非対称 0 件）。

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
