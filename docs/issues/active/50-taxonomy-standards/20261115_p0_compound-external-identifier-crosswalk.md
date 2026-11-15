# Issue: 化合物 taxonomy の外部識別子 crosswalk の P0 修正（registry 照合）

**ID:** ISS-20261115-TAX-043
**優先度:** P0 (Critical)
**ステータス:** PENDING (2026-11-15: P0 修正は候補形式登録と別のローカル commit に分離済み。owner review は pending、push は未実施)
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`（9 概念の `skos:exactMatch` と 2 概念の scopeNote）、
`metadata/taxonomy/iptc-mapping.yaml`（写しの識別子・coverage・version）、
`exports/taxonomy/*`（再生成）、`tests/validation/test_registration_state_batch.py`、
`tests/validation/test_compound_identifier_crosswalk.py`（新規）、
`docs/provenance/compound-taxonomy.md`、`metadata/provenance/evidence-registry.json`、
`docs/provenance/evidence-hash-policy.md`、`datasets/cannabinoid-raw-collection/README.md`、
`project.json`（identityNote）、`docs/provenance/query-inventory.md`（写しの QID）
**関連:** `ISS-20261110-TAX-039`（CBC / CBDV の既存概念再利用時の固定値）、
`ISS-20261111-TAX-040` / `ISS-20261111-TAX-041`（登録済み語の識別子を扱わない方針）、
`ISS-20261111-TAX-042`（異性体別根拠のレビュー。本 issue は family 概念へ個別識別子を付けない方針を維持）

## 概要

識別子監査で、化合物 taxonomy の 9 概念の `skos:exactMatch` が参照先の化合物と
一致しないことが指摘された。2026-11-15 に ChEBI と Wikidata の live record と照合し、
全 9 概念で旧値が別の実体（化合物クラス、無関係な化学物質、地名、団体、曖昧さ回避ページ、
存在しない ID）を指すことを確認した。本 issue は識別子とその写しの修正だけを記録する。

これは**事実の修正**であり、scope の拡張ではない。経路／由来の分類、検索語と概念の対応、
query / run / catalog / raw data / 被覆 / family scope / 収集設計 / 公開範囲を変えない。

## 判明した欠陥

| concept | 旧 `skos:exactMatch` | 旧値の実体 | 修正後 |
|---|---|---|---|
| `compound_cbd` | `chebi:33669` / `wikidata:Q141452` | metallacycloalkanes / Disraeli（ケベック州の都市） | `chebi:69478` / `wikidata:Q422917` |
| `compound_thc` | `chebi:32927` / `wikidata:Q141629` | nonadecane / Reifenberg（ドイツの自治体） | `chebi:66964` / `wikidata:Q190067` |
| `compound_cbg` | `chebi:32927` / `wikidata:Q422432` | nonadecane / Aktion Regen（団体） | `chebi:69477` / `wikidata:Q412122` |
| `compound_cbn` | `wikidata:Q415237` | Wikimedia の曖昧さ回避ページ | `chebi:3360` / `wikidata:Q265831` |
| `compound_cbc` | `wikidata:Q422441` | Wikimedia の曖昧さ回避ページ | `chebi:3357` / `wikidata:Q410949` |
| `compound_thcv` | `wikidata:Q422449` | mycotoxins（マイコトキシンのクラス） | なし（下記） |
| `compound_cbdv` | `wikidata:Q422426` | potassium fluoride（KF） | `wikidata:Q1104117` |
| `compound_anandamide` | `chebi:52384` / `wikidata:Q409339` | zymosteryl oleate / 存在しない ID | `chebi:2700` / `wikidata:Q410228` |
| `compound_2ag` | `chebi:64901` / `wikidata:Q295793` | mygalin / 存在しない ID | `chebi:52392` / `wikidata:Q209320` |

## 検証方法

- ChEBI の backend API（`/chebi/backend/api/public/compound/<id>/`）で accession・名称・
definition・formula・標準 InChIKey を取得した。`chebi:32927` = nonadecane、
`chebi:33669` = metallacycloalkanes、`chebi:52384` = zymosteryl oleate、
`chebi:64901` = mygalin であることを確認した。
- Wikidata の `wbgetentities` で label / description / claims を、SPARQL で P683（ChEBI ID）・
P231（CAS）・P235（InChIKey）・P662（PubChem CID）を取得した。`Q409339` と `Q295793` は
`missing` を返した（項目が存在しない）。
- 採用判定は、Wikidata の P683 が採用する ChEBI accession と一致し、標準 InChIKey が一致する
ことを条件とした。
- `compound_thcv` は OLS4 ChEBI 検索（`tetrahydrocannabivarin` 1 件、
`delta-8-tetrahydrocannabivarin` 0 件）と Wikidata `wbsearchentities`（2 件、いずれも Δ9）で
確認した。負の検索結果は不存在の証明ではなく、2026-11-15 時点の応答である。
- 証拠は `metadata/provenance/evidence-registry.json` の `ev-chebi-*` / `ev-wikidata-*` と
`docs/provenance/compound-taxonomy.md` の同日節に記録した。

## 決定

### 採用した値

- CBD / THC / CBG / CBN / CBC / anandamide / 2-AG: 検証済みの ChEBI および Wikidata レコード。
- CBDV: `wikidata:Q1104117` のみ。ChEBI の `CHEBI:182159` は `(1R,6R)` の立体化学を定義した
  レコードであり、立体化学を指定しない概念には付けない。`Q1104117` は Wikidata が
  `group of stereoisomers` と明示するレコードで、標準 InChIKey も立体化学層を持たない。

### 未対応

- `compound_thcv`: `skos:exactMatch` を削除し、概念の scopeNote に理由を記録した。概念は
  Δ8/Δ9 の位置異性体と立体化学を指定しないが、検証済みレコード（`CHEBI:755032`、
  `Q76009679`、`Q254768`）はいずれも Δ9 を指す。いずれかを付けると Δ9 を主張することになる。
  owner が概念を Δ9-THCV に狭める場合は `CHEBI:755032` と `Q76009679` の組が候補になる。

### 監査の候補範囲を超えた判断（owner レビュー対象）

- `compound_anandamide` と `compound_2ag` の Wikidata は、監査の候補には無かった
  `Q410228` / `Q209320` を採用した。既存の `Q409339` / `Q295793` が存在しないため、
  P683 と標準 InChIKey の 2 系統で一致したレコードを代わりに置いた。この 2 件だけは
  候補一覧の外にあるため、owner が別の扱いを望む場合は差し戻し対象である。

## 変更しないもの

- `compound_identity_unverified` の membership と logic。
- P1 の経路／カテゴリ評価（`CBX`、`CRDH`、`CRDP`、`H4CBH`、`HHBD`、`HHCH`、`THCNM`、
  `THC-O`、`THCP`、`THCJD`、`THCPO`、THCA / THCB の 6 個別トピック等）。
- query ID、検索語と概念の対応、run ID、catalog、raw data、source coverage、family scope、
  collection design、release scope、publication status。
- 家族（`THCP` / `THCJD` / `THCPO` / `THCB-O-acetate`）に個別異性体の識別子を付けない方針。

## 完了条件と残作業

- [x] 9 概念の registry 照合と修正／削除
- [x] IPTC 対応表の写しの更新
- [x] `bash scripts/export/export-taxonomy.sh` による exports の再生成
- [x] 固定値の更新と crosswalk の新規テスト
- [x] taxonomy ハッシュの再観測（新しい `observed_at` と note。旧観測は書き換えない）
- [x] 台帳・issue・evidence registry の記録
- [x] P0 修正を候補形式登録と別のローカル commit に分離（push 未実施）
- [ ] owner のレビュー
- [ ] `compound_thcv` の粒度決定（Δ9 に狭めるか、異性体未指定のままにするか）
- [ ] 9 概念以外の crosswalk の再監査（別 issue）

## 検証

```text
make audit-raw-completeness   # snapshot 再生成の前提确认（合格）
.venv/bin/python -m pytest -q tests/validation/test_compound_identifier_crosswalk.py \
  tests/validation/test_taxonomy.py tests/validation/test_taxonomy_consistency.py \
  tests/validation/test_registration_state_batch.py tests/validation/test_evidence_reconciliation.py
bash scripts/export/export-taxonomy.sh
make gates GATE=registries
make test
git diff --check
```

データ層・run・被覆を変えていないため、データ系 snapshot（`docs/audits/*`）は再生成していない。
README を更新したため `docs/audits/g6-git-tracking-inventory.json` の README ハッシュだけを
`python -m validation.cli audit-git-tracking` で更新した（他チェックアウトのローカル状態を表す
extras / state_summary は変更しない）。
