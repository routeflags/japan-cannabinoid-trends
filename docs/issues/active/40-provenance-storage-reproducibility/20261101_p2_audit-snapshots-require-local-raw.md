# Issue: 監査スナップショット（11 ファイル）が raw 不在の checkout で再生成できず、run 行を失う

**ID:** ISS-20261101-PRV-017  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `docs/audits/` の 11 スナップショット、`Makefile` の `audit-snapshots`、
`validation.cli snapshot-guard`、`validation.cli audit-raw-completeness`

## 概要

`make audit-snapshots` はローカルの raw tree を走査して **11 ファイル**を上書きする。
raw は Git 管理外（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）であり、
YouTube raw は特定の checkout にしか存在しない。そのため raw を持たない checkout で
この target を実行すると、**存在しないだけの run の行がスナップショットから消える**。

書き込み対象（Makefile の順）:

1. `docs/audits/contract-ledger.json`
2. `docs/audits/g2-query-inventory.json`
3. `docs/audits/gt-summary.json`
4. `docs/audits/publication-contract.json`
5. `docs/audits/g3-temporal-inventory.json`
6. `docs/audits/g4-storage-inventory.json`
7. `docs/audits/g5-legacy-runs.json`
8. `docs/audits/g5-provenance-assessment.json`
9. `docs/audits/g6-git-tracking-inventory.json`
10. `docs/audits/g6-private-catalog.json`
11. `docs/audits/g7-study-inventory.json`

## この checkout の実測（2026-11-01）

- `datasets/cannabinoid-raw-collection/data/raw/youtube/` は**存在しない**。
  採用済み YouTube 8 run（liquid 7 + 保留 HHC 1）は 0/8 しか見えない。
- `datasets/cannabinoid-raw-collection/metadata/data-catalog.json` は 8 run を
  catalog 済みとして名指す。committed catalog と raw の不一致は
  `ISS-20261101-PRV-018` で扱う。
- この checkout では `make audit-snapshots` を実行していない（指示どおり）。
  以前の実測は、HHC 2 run だけを持つ別 checkout（YouTube raw 2/8）で `/tmp` へ
  出力して追跡ファイルと比較したものである。7 ファイルがバイト一致しなかった。

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

## 影響

- `tests/validation/test_audit_report_freshness.py` のスナップショット、`test_query_semantics`、
  `test_storage_inventory_audit`、`test_temporal_inventory` が raw を欠く checkout では
  解消できない（2026-11-01 時点の実測は 10 failed / 1493 passed）。
- 監査スナップショットは「採用済み run の一覧」としても読まれるため、欠落は provenance の
  可視性を下げる。
- 誤った削除は Git の差分として残るが、気づかないままコミットされ得る。

## 必須の対策

1. **preflight**: `make audit-snapshots` は最初の書き込みの前に、committed catalog・
   committed staging declaration・既存スナップショットが名指す run id を集め、
   それぞれの raw directory と `run_metadata.json` がこの checkout にあることを確認する。
   1 つでも欠ければ**何も書かずに停止**する。
2. **expected full raw state の明示**: preflight は「何を完全状態と見なすか」を
   `--expected-run-ids`（JSON 配列）で追加できる。既定は catalog ∪ declaration ∪
   既存スナップショット。件数と欠落 ID を出力する。
3. **postflight**: 書き込み後に、preflight が記録した run id と新しいスナップショットを
   比較し、**既存 run id が 1 つでも消えたら失敗**する。追加は報告のみ。
4. **catalog→raw completeness**: `make audit-raw-completeness` が catalog / declaration の
   run id と raw の対応を別途検査する（`ISS-20261101-PRV-018`）。

## 実装（未コミット）

- `src/validation/snapshot_guard.py` + `validation.cli snapshot-guard --phase preflight|postflight`。
  状態ファイルは `.staging/audit-snapshot-guard.json`（gitignore 対象）。
- `Makefile` の `audit-snapshots` が preflight → 11 ファイル → postflight の順で実行する。
- `src/validation/raw_completeness.py` + `validation.cli audit-raw-completeness`。
- テスト: preflight が欠落で拒否する / 完全なら通る / postflight が消失を検出する。

## 完了条件

- [ ] raw の揃った環境で `make audit-snapshots` を実行し、preflight / postflight が通り、
      11 スナップショットが「追加のみ」の差分になることを確認する。
- [ ] partial checkout で `make audit-snapshots` が**書き込み前に**非 0 で停止することを確認する。
- [ ] `pytest tests/validation/test_audit_report_freshness.py` が全件通過する。
- [ ] 恒久対策（生の run を追跡または検証可能なアーカイブに載せる等）を決め、契約として
      記述するか、採らない理由を記録する。
- [ ] 同種の再発（raw を欠く checkout での再生成）を検出する手順を runbook か監査に追加する。
