# Issue: `THCO` は `THC-O` の表記ゆれとして確認済みだが、化学的同一性は未確定

**ID:** ISS-20261104-TAX-029
**優先度:** P2 (Medium)
**ステータス:** OPEN
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`（`compound_thc_o` の `skos:scopeNote`）、
`metadata/queries/query-variants.json`、`docs/provenance/query-inventory.md`、
`metadata/provenance/evidence-registry.json`、`docs/provenance/compound-taxonomy.md`、
`datasets/cannabinoid-raw-collection/`（README・methodology）
**関連:** `ISS-20261104-TAX-028`（THCNM の同一性未確認。同じ「クエリ表記は確認済み / 同一性は未確認」の型）

## 概要

`THCO` を `THC-O` の**検索語の表記ゆれ**として `query-variants.json` に登録し、2026-11-04 に
canonical の `query_id`（`thc-o-general-ja` / `thc-o-liquid-ja`）のまま 4 run を収集した。
canonical の `THC-O`（12ヶ月 `NO_DATA`・5年系列）と `THC-O リキッド`（no data）は不変で、
variant の run は置換・統合しない。

本 issue が残すのは**化学的同一性の未確定**である。`THCO` という文字列は単一の CAS にも
単一の構造にも対応しない。

## 確認できた証拠

| 出所（evidence ID） | 内容 | 支える主張 |
|---|---|---|
| `ev-pubmed-37466480` | tetrahydrocannabinol-O-acetate が口語で `THCO` と呼ばれる | 表記ゆれとしての登録 |
| `ev-pubchem-cid-198013` | Tetrahydrocannabinol acetate（delta9-）、別名 `THC-O-ACETATE`、CAS 23132-17-4、`C23H32O3` | `THC-O` がアセテート体を指すこと |
| `ev-pubmed-37381980` / `ev-pubmed-36508081` | 学術文献の `THC-O-Acetate` / `THC-O Acetate` 表記 | 表記の実在 |
| `ev-cayman-33763-delta9-thco` | Δ9-THCO、CAS 22972-65-2、`C17H22O2` | `THCO` が別物質（tetrahydrocannabiorcol）にも使われること |
| `ev-cayman-33762-delta8-thco` | Δ8-THCO、CAS 22972-64-1、`C17H22O2` | Δ8 / Δ9 の 2 異性体があること |

出所の URL は `metadata/provenance/evidence-registry.json` が保持する（本 issue は ID で参照する）。
外部参照のためハッシュは記録しない（`docs/provenance/evidence-hash-policy.md`）。

## 何が未決か

1. **taxonomy の概念設計**: `compound_thc_o` を総称概念のままにするか、
   `Δ8-THC-O-acetate` / `Δ9-THC-O-acetate`（アセテート体）と `Δ8-THCO` / `Δ9-THCO`
   （tetrahydrocannabiorcol）を別概念として登録するか。現状は総称概念 1 つで、
   `exactMatch`・CAS・分子式を持たない。
2. **規制記載の対応**: `research/regulatory-status/THC-O.md` は「THC-O」を指定薬物として記録するが、
   その指定がアセテート体のどの異性体を指すかは本 issue では確認していない。推測で補わない。
3. **観測の意味**: Google Trends の `THCO` / `THCO リキッド` 観測値は送信文字列の検索需要であり、
   製品の含有物質の同定ではない。`THCO` は tetrahydrocannabiorcol の話題も拾い得るため、
   canonical 系列との差を「表記だけの違い」と解釈しない。

## 現在の扱い（変更しないもの）

- canonical の `query_id`・canonical text（`THC-O` / `THC-O リキッド`）は不変。
- `THCO` / `THCO リキッド` の 4 run は variant の別観測として raw に残す。合算・平均・置換をしない。
- `compound_thc_o` に CAS / ChEBI / Wikidata / PubChem の `exactMatch` を追加しない。
  クエリ表記の証拠から識別子を導かない。
- `docs/audits/gt-summary.json`・公開ページ・被覆数は再生成していない。

## 解消条件

次のいずれかが得られた時点で、scopeNote・台帳・本 issue を同時に更新する。

1. 異性体ごとの標準品・一次文献・規制記載により、`THC-O` / `THCO` が指す構造が決まる。
2. owner が概念分割（アセテート体と tetrahydrocannabiorcol を別概念にするか）を決める。
3. 総称のまま追跡する判断を記録する（その場合も、識別子を付けない理由を scopeNote に残す）。

## 出所（外部情報）

- PubMed 37466480 / 37381980 / 36508081、PubChem CID 198013、Cayman Chemical 33763 / 33762。
  内容と URL は `metadata/provenance/evidence-registry.json` の `ev-*` エントリが正本。
