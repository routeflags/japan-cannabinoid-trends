# Issue: Evidence Registry と run 監査の突合 pass が未実装

**ID:** ISS-20261015-PRV-011  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
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
- [ ] 現行 7 件の info の扱いを決着（扱いは記録済み。解消は所有者の立会い観測待ちのため OPEN のまま）

## 実装メモ（2026-10-15、OPEN のまま）

突合 pass とハッシュ方針は実装済み。7 件の `EVIDENCE_HASH_UNRECORDED` は
オフラインで解消できない（下表）ため、明示記録の上で本 issue は OPEN のまま残す。
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
  `needs_witnessed_observation`: 現在の `observed_at`（2026-10-13）のまま hash を
  書き込むのは観測の捏造になるため `null` を維持する。

残りのオーナー作業: 上表の 6 件 each について、ファイルを観測して hash・観測時刻・
登録者身元を記録するか、pin 留めしない理由を登録すること。立会い観測なしに agent が
 hashes を書き込んではならない。
