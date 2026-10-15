# Issue: Evidence Registry と run 監査の突合 pass が未実装

**ID:** ISS-20261015-PRV-011
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `metadata/provenance/evidence-registry.json`, `src/validation/provenance.py`, `docs/specs/validation-framework.md` §18.3

## 概要

Evidence Registry の語彙と参照形式は用意されているが、run 監査が `unknown` と判定した項目を
証拠引用で `observed` / `inferred` へ昇格させる pass が無い。

## 確認された観測

- `validate-registries` は evidence-registry を検証するが、7 件すべてに
  `EVIDENCE_HASH_UNRECORDED`（info、ハッシュ未記録 = 完全性不明）が付く。
- 検証フレームワークは `inferred` の自動付与をしない方針を明記している。

## 影響

- 「証拠があるのに unknown のまま」の項目を人手で追うことになる。
- 旧 run の capability / 実行条件の昇格判断が場当たりになる。

## 対応方針

- 監査の unknown 項目と evidence エントリを突き合わせ、引用とともに昇格候補を出す pass を用意する（自動で `inferred` を埋めない）。
- evidence のハッシュ記録方針（何をハッシュするか）を決める。

## 完了条件

- [x] 突合 pass の実装とテスト
- [x] evidence ハッシュ記録方針の決定
- [x] 現行 7 件の info の扱いを決着（6 件は所有者指示に基づく現在時刻の立会い観測として hash pin、1 件は `regenerated_output` として pin しない）

## 実装メモ（2026-10-15）

突合 pass とハッシュ方針は実装済み。7 件の `EVIDENCE_HASH_UNRECORDED` は
下表の方針で扱う。6 件は owner 指示による現在時刻の観測として pin 済み、
1 件は再生成物のため pin 留めしない。
`unknown` → `observed` / `inferred` の自動昇格は一切行っていない。

- 突合 pass: `src/validation/evidence_reconciliation.py`
 （`reconcile_evidence`。run 監査の `unknown` と evidence エントリを突き合わせ、
  引用つき `candidate` または `no_covering_evidence` を出す。read-only、入力無変異。
  既知フィールド対応表を持つ `registry_definition` のみが被覆候補; taxonomy /
  audit 報告 / fixture / 外部参照は文脈扱いで被覆しない。G5 P2/P5）
- 契約テスト: `tests/validation/test_evidence_reconciliation.py`（8 件。
  昇格語彙が出力 verdict に現れないこと、実レジストリの disposition、read-only を固定）
- ハッシュ方針: `docs/provenance/evidence-hash-policy.md`（hash は立会い観測時のみ記録。
  `regenerated_output` は pin 留めしない、`needs_witnessed_observation` は所有者観測待ち、
  外部参照は検証不能のため hash 対象外。分類器は `classify_hash_status`）
- 7 件の disposition（`test_real_registry_disposition_is_explicit` が固定）:
  `ev-replay-fixture-12m` は pinned。`ev-legacy-audit-20261013` は
  `regenerated_output`（再生成で stale 化するため pin 留めしない方針で決着）。
  残り 6 件（source / collector / query / taxonomy / window / artifact の各 registry）は
  owner 指示に基づき `2026-10-15T21:32:30Z` の観測イベントとして hash pin 済み。

オーナー作業の補足: 今後、上表の 6 件の参照ファイルを変更した場合は、古い hash を
残したままにせず、新しい観測イベントとして hash・観測時刻・登録者身元を更新すること。
立会い観測なしに agent が hashes を書き換えてはならない。

### オーナー作業の具体手順（2026-10-15 追記）

対象は `docs/provenance/evidence-hash-policy.md` の
`needs_witnessed_observation` 6 件:

1. `ev-source-registry` → `config/sources.json`
2. `ev-collector-registry` → `config/collectors.json`
3. `ev-query-registry` → `metadata/queries/query-registry.json`
4. `ev-compound-taxonomy` → `metadata/taxonomy/compound-taxonomy.skos.jsonld`
5. `ev-window-2025-2026` → `metadata/windows/2025-10-12_2026-10-12.json`
6. `ev-artifact-registry` → `metadata/artifacts/artifact-registry.json`

各 entry で owner / registrar が行うこと:

- 対象ファイルをその場で開き、観測対象が意図した repo file であることを確認する。
- 同じ観測時点の bytes から SHA-256 を計算する。
- `metadata/provenance/evidence-registry.json` の当該 entry で:
  - `sha256` を計算値に置き換える。
  - `observed_at` を**実際に観測した現在時刻**へ置き換える（既存の
    `2026-10-13T05:01:38Z` へ backfill しない）。
  - 現行 schema に registrar 専用 field は無いため、`note` に
    `Registrar: <name or role>; observed for ISS-20261015-PRV-011` のように
    観測者身元と判断理由を追記する。
- `PYTHONPATH=src python3 -m validation.cli validate-registries --format json`
  を実行し、対象 entry が `EVIDENCE_HASH_UNRECORDED` から消え、
  `EVIDENCE_HASH_MISMATCH` が出ないことを確認する。

やってはいけないこと:

- agent が立会い観測なしに hash を埋めること。
- 既存 `observed_at` のまま hash だけを追加すること。
- `docs/audits/g5-legacy-runs.json`（`regenerated_output`）を hash pin すること。
- 他の audit report や過去ログに載った hash を転記すること。
- 外部 URL / cloud 証拠を local file と同じ扱いで hash 化すること。

## 解決記録（2026-10-15）

owner 指示により、`needs_witnessed_observation` の 6 件を現在時刻の
新しい観測イベントとして pin した。`metadata/provenance/evidence-registry.json`
の各 entry は、対象ファイルの現在 bytes の `sha256`、実観測時刻
`2026-10-15T21:32:30Z`、および `note` 内の registrar 記録を持つ。

pin 済み:

- `ev-source-registry` → `config/sources.json`
- `ev-collector-registry` → `config/collectors.json`
- `ev-query-registry` → `metadata/queries/query-registry.json`
- `ev-compound-taxonomy` → `metadata/taxonomy/compound-taxonomy.skos.jsonld`
- `ev-window-2025-2026` → `metadata/windows/2025-10-12_2026-10-12.json`
- `ev-artifact-registry` → `metadata/artifacts/artifact-registry.json`

`ev-legacy-audit-20261013` は policy どおり `regenerated_output` として
hash pin しない。これは未対応ではなく、再生成物を固定 hash で縛らないという
決定済みの扱いである。

したがって本 issue の実装範囲（突合 pass、hash 方針、現行 7 件の扱い）は完了。
今後 registry / taxonomy / window / artifact registry を変更した場合は、
該当 evidence entry の hash mismatch を避けるため、新しい観測イベントとして
`sha256` / `observed_at` / `note` を更新する。
