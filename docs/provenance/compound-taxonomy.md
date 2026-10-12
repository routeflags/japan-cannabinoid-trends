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

## 未修正の既知事項（本変更では触っていない）

1. `compound-synthetic` の `skos:narrower` に `compound-crdh` が未掲載（`broader` のみ存在する非対称）。
2. `compound_h4cbh` / `compound_hhbd` のカテゴリが、タクソノミー（minor）と EWI/timeline（Semi-Synthetic）で不一致。
3. `metadata/datapackage.json` の `skos_scheme` が `jptr:compound-scheme` を参照しているが、実在するのは `jptr:compound-taxonomy`。
4. `exports/taxonomy/*.ttl` / `.schema.jsonld` は 2026-10-02 生成のままで、`compound-crdh` および本追加分が未反映
   （`bash scripts/export/export-taxonomy.sh` で再生成可能。release アーカイブの `INCLUDE_PATHS` に `exports/` は含まれない）。
5. `metadata/taxonomy/iptc-mapping.yaml` の `compound_mapping` は部分収載（`cbc`/`thcv`/`cbdv`/`crdh` も未収載）。
6. `THCH` の日本語名は文書間で表記ゆれがある（`THCH.md` を標準として採用）。

## 次の作業

- 追加した5化合物のクエリを `metadata/queries/query-registry.json` へ登録する（G2 の増分）。登録後、
  `docs/audits/g2-query-inventory.json` の該当16文字列は `ambiguous` から `exact_match`/`variant_match` へ移行する。
- 上記「未修正の既知事項」1〜6 の扱いを決める。
