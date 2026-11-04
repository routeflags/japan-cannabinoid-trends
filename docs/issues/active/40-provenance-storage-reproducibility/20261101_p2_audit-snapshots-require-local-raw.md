# Issue: 監査スナップショット（11 スナップショット + scope sidecar）が raw 不在の checkout でも安全に再生成できるようにする

**ID:** ISS-20261101-PRV-017  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `docs/audits/` の 11 スナップショットと `snapshot-scope.json`、
`Makefile` の `audit-snapshots`、`validation.cli snapshot-guard`、
`validation.cli audit-raw-completeness`、`validation.cli audit-snapshot-scope`

## 概要

`make audit-snapshots` はローカルの raw tree を走査して **11 スナップショット**を上書きする。
raw は Git 管理外（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）であり、
YouTube raw は特定の checkout にしか存在しない。そのため raw を持たない checkout で
この target を実行すると、**存在しないだけの run の行がスナップショットから消える**。

## 決定（owner, 2026-11-02）

1. `make audit-snapshots` は `git_untracked` の raw 不在では停止しない。
2. スナップショットは **checkout-local inventory** として生成する。完全な研究状態を
   再構成する必要はない。
3. 出力（sidecar `docs/audits/snapshot-scope.json`）に
   `audit_scope: checkout_local` / `raw_visibility: partial` /
   `not_repository_retained_run_ids` を記録する。既存 11 スナップショットの schema は
   変えない。
4. 見えない `git_untracked` YouTube run はスナップショットから消えてよいが、
   未収集・0 観測とは解釈しない。完全な provenance claim の正本は catalog と
   declaration である。
5. preflight が失敗するのは `git_tracked` raw の欠落・不整合と保持判断の不正だけ。
   postflight も `git_tracked` run の消失だけを失敗とする。
6. raw rows は生成しない。raw 依存の件数・hash は
   `not_repository_retained` / `unavailable` と記録する。

この決定により、「raw の揃った環境で完全なスナップショットを作る」という当初の
完了条件は採らない。スナップショットはこの checkout で見える範囲を正直に記録し、
その scope と保持状態を sidecar で宣言する。

書き込み対象（Makefile の順）:

1. `docs/audits/snapshot-scope.json`（deterministic scope sidecar。raw を読まない）
2. `docs/audits/contract-ledger.json`
3. `docs/audits/g2-query-inventory.json`
4. `docs/audits/gt-summary.json`
5. `docs/audits/publication-contract.json`
6. `docs/audits/g3-temporal-inventory.json`
7. `docs/audits/g4-storage-inventory.json`
8. `docs/audits/g5-legacy-runs.json`
9. `docs/audits/g5-provenance-assessment.json`
10. `docs/audits/g6-git-tracking-inventory.json`
11. `docs/audits/g6-private-catalog.json`
12. `docs/audits/g7-study-inventory.json`

## この checkout の実測（2026-11-01）

- `datasets/cannabinoid-raw-collection/data/raw/youtube/` は**存在しない**。
  採用済み YouTube 8 run（liquid 7 + 保留 HHC 1）は 0/8 しか見えない。
- `datasets/cannabinoid-raw-collection/metadata/data-catalog.json` は 8 run を
  catalog 済みとして名指す。committed catalog と raw の不一致は
  `ISS-20261101-PRV-018` で扱う。
- 2026-11-01 時点では、この checkout で `make audit-snapshots` を実行していない
  （当時の指示）。以前の実測は、HHC 2 run だけを持つ別 checkout（YouTube raw 2/8）で
  `/tmp` へ出力して追跡ファイルと比較したものである。7 ファイルがバイト一致しなかった。

| スナップショット | 追跡中 | その checkout での再生成 |
|---|---|---|
| g2-query-inventory | `exact_match` 106 | 107 |
| g4-storage-inventory | run 62 | 63（HHBD を失い、HHC 2 run を追加） |
| g5-provenance-assessment | `ready` 33 / `not_ready` 29 | 34 / 29 |
| g3 / g5-legacy / g6-git-tracking / g7-study | — | いずれも不一致 |

`g4` の増減を run 単位で見ると、原因が 2 種類に分かれる。

- **失う行**: `20261010T141947Z-youtube-cannabinoid-raw-collection`（HHBD。raw が無い）
- **加わる行**: `20261101T085920Z-…`、`20261101T091646Z-…`（2026-11-01 の HHC 2 run）

すなわち単純な再生成は「正しい追加」と「誤った削除」を同時に行う。この checkout では
さらに 6 run（liquid 5 + HHBD）を失う。

## 2026-11-02 の実測（決定後）

- preflight: expected 80 / present 64 / `not_repository_retained` 22 /
  missing 0 / retention warnings 0 / refused false。
- `make audit-snapshots`（旧 11 スナップショットから再生成）: preflight →
  `snapshot-scope.json` → 11 スナップショット → postflight の順で完走。
  postflight: before 59 / after 58 / lost 0 / `intentionally_dropped` 1 /
  added 0 / refused false。
- 失われた raw-derived row は HHBD YouTube run
  （`20261010T141947Z-youtube-cannabinoid-raw-collection`）の 1 行だけ。
  `docs/audits/snapshot-scope.json` の `not_repository_retained_run_ids` に残り、
  0 観測・未収集には変換しない。
- `tests/validation/test_audit_report_freshness.py` は 20 passed。
  `test_query_semantics` / `test_storage_inventory_audit` / `test_temporal_inventory`
  は 47 passed。`PYTHONPATH=src python3 -m pytest tests/validation -q` は
  928 passed。

## 影響

- `tests/validation/test_audit_report_freshness.py` のスナップショット、`test_query_semantics`、
  `test_storage_inventory_audit`、`test_temporal_inventory` が raw を欠く checkout では
  解消できなかった（2026-11-01 時点の実測は 10 failed / 1493 passed）。
  2026-11-02 の決定後は、この checkout で再生成した 11 スナップショットと
  scope sidecar に対して 67 tests が通過する。
- 監査スナップショットは「採用済み run の一覧」としても読まれるため、欠落は provenance の
  可視性を下げる。
- 誤った削除は Git の差分として残るが、気づかないままコミットされ得る。

## 必須の対策（2026-11-02 改訂）

1. **preflight**: `git_tracked` の run を Git index の追跡ファイルまたはローカル raw +
   `run_metadata.json` で確認できない場合、および保持判断が不正な場合だけ、書き込み前に
   停止する。`git_untracked` の raw 不在では停止しない。
2. **scope sidecar**: 11 スナップショットの後に
   `validation.cli audit-snapshot-scope --output docs/audits/snapshot-scope.json` を実行する。
   sidecar は raw を読まず、committed な catalog / declaration / retention decision から
   `audit_scope` / `raw_visibility` / `git_tracked_run_ids` /
   `not_repository_retained_run_ids` を決定論的に記録する。
3. **postflight**: 書き込み後に、preflight が `git_tracked` と記録した run id が消えた
   場合だけ失敗する。`git_untracked` の raw-derived row の欠落は
   `intentionally_dropped_run_ids` として報告する。
4. **catalog→raw completeness**: `make audit-raw-completeness` が catalog / declaration の
   run id と raw の対応を別途検査する（`ISS-20261101-PRV-018`）。`git_untracked` の不在は
   `not_repository_retained`、0 ではない。

## 実装（未コミット）

- `src/validation/snapshot_guard.py` + `validation.cli snapshot-guard --phase preflight|postflight`。
  状態ファイルは `.staging/audit-snapshot-guard.json`（gitignore 対象）。
  `git_untracked` の raw 不在は missing にせず、`not_repository_retained_run_ids` に記録する。
- `src/validation/raw_completeness.py` + `validation.cli audit-raw-completeness`。
  `git_tracked` の欠落だけを failure にし、`git_untracked` の不在は
  `not_repository_retained` として報告する。
- `src/validation/raw_completeness.py` の `build_snapshot_scope` +
  `validation.cli audit-snapshot-scope`。raw を読まず、checkout-local scope と
  `not_repository_retained_run_ids` を sidecar に書く。
- `Makefile` の `audit-snapshots` が preflight → scope sidecar → 11 スナップショット →
  postflight の順で実行する。
- テスト: preflight が `git_tracked` 欠落で拒否する / `git_untracked` 欠落では拒否しない /
  postflight が `git_tracked` 消失だけを検出する / sidecar が checkout-local で
  決定論的であることを検査する。

## 完了条件（2026-11-02 改訂）

- [x] partial checkout で `make audit-snapshots` が preflight / postflight を通り、
      `git_untracked` の raw 不在で停止しないことを確認する。
- [x] `docs/audits/snapshot-scope.json` が `audit_scope: checkout_local` /
      `raw_visibility: partial` / `raw_rows_generated: false` /
      `not_repository_retained_run_ids` を持ち、同一 checkout で再現する。
- [x] `pytest tests/validation/test_audit_report_freshness.py` が同一 checkout で全件通過する。
- [x] catalog / declaration が complete provenance claim の正本であることを docs に記録する。
- [x] `git_tracked` の run を欠く checkout では preflight が書き込み前に非 0 で停止することを確認する。
- [x] スナップショットに現れない run を未収集・0 観測として解釈しないことを docs に記録する。

## 関連

- `ISS-20261102-PRV-019`: 保持を `git_tracked` / `git_untracked` に分離し、
  `git_untracked` の run は raw 不在でも preflight が拒否しないようにした。
