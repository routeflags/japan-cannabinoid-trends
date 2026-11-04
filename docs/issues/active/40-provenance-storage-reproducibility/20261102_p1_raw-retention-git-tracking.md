# Issue: raw 保持を `git_tracked` / `git_untracked` の 2 状態で分類し、意図的な非追跡を missing から分離する

**ID:** ISS-20261102-PRV-019  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `docs/specs/raw-data-policy.md` §5、`src/validation/raw_retention.py`、
`src/validation/raw_completeness.py`、`src/validation/snapshot_guard.py`、
`Makefile`、`.agents/skills/study-compound-extension/SKILL.md`、
`.github/skills/research-youtube-search/SKILL.md`

## 概要

raw の「保持」を、ローカル raw の存在ではなく **Repository Storage（Git 追跡）**
として明確化する。状態は `git_tracked` / `git_untracked` の 2 値だけとする。
著作権・再配布制約により payload を commit できない run は `git_untracked` であり、
ローカル raw が無い checkout でも「missing」ではない。リポジトリには非 content の
来歴（宣言・判断記録・catalog・集計・利用可能な SHA-256）だけを残す。

用語の注意: `retainable` / `not_retainable` は使わない。これらは「ローカル raw が
存在するか」と混同されたため（owner 用語訂正、2026-11-02）。

## 契約（`docs/specs/raw-data-policy.md` §5）

- `git_tracked`: payload を Git 追跡下の Repository Storage として保持する。
  clone で再現できること。
- `git_untracked`: payload を Git に追加しない。ローカル raw は `data/raw/` に
  存在してよい。リポジトリは非 content の来歴のみを保持する。
- 状態の解決順: ①`metadata/provenance/retention/<date>-<slug>.json`
  （`record: "raw_retention_decision"`）の明示判断、②`config/storage-policies.json`
  の raw policy × `config/sources.json` の kind、③policy 不在時は `git_tracked`
  へ fail closed。
- 明示判断には `reason` と実在する `decision_reference` を必須とする。
  `publication_status` は独立した軸であり、保持は公開許可ではない。
- 既存 run の状態は推測で決めない。判断記録が無ければ policy 既定
  （YouTube = `git_untracked`、Google Trends = `git_tracked`）。

## 実装（未コミット）

- `src/validation/raw_retention.py`: 語彙、判断記録の検証、policy 既定の解決、
  Git index との照合。
- `src/validation/raw_completeness.py`: 状態を `present` / `tracked_not_checked_out` /
  `missing_directory` / `missing_run_metadata` / `present_not_git_tracked` /
  `not_repository_retained` / `local_only_present` / `git_untracked_but_tracked`
  に分離。`git_tracked` の欠落だけを failure にする。
- `src/validation/snapshot_guard.py`: preflight は `git_untracked` の raw 不在で
  拒否しない。`git_tracked` の欠落・不整合と判断記録の不正で拒否する。
  `git_untracked` が Git index に載っている場合は warning（ハード失敗は
  `audit-raw-retention`）。postflight は `git_tracked` の消失だけを失敗とし、
  `git_untracked` の欠落を `intentionally_dropped_run_ids` として報告する。
- `src/validation/raw_completeness.py` の `build_snapshot_scope` +
  `validation.cli audit-snapshot-scope`: raw を読まず、checkout-local scope と
  `not_repository_retained_run_ids` を deterministic sidecar に書く。
- `Makefile`: `audit-raw-retention` を追加。`audit-raw-completeness` /
  `audit-snapshots` に `--retention-dir` を渡し、`audit-snapshots` の最後に
  `snapshot-scope.json` を生成する。
- スキル: 収集・adoption の前に保持を分類する手順を追加。
- テスト: `tests/validation/test_raw_retention.py`、`test_raw_completeness.py` /
  `test_snapshot_guard.py` に両状態のケースを追加。`test_audit_report_freshness.py`
  に sidecar の checkout-local 検証を追加。

## 実測（2026-11-02、この checkout）

- `audit-raw-retention`: records 0 / runs 50 / `git_tracked` 28 /
  `git_untracked` 22 / violations 0。
- `audit-raw-completeness`: claims 50 / present 28 /
  `not_repository_retained` 22 / missing 0 / retention violations 0。
- `audit-snapshot-scope`: claims 50 / `git_tracked` 28 /
  `not_repository_retained` 22 / `raw_rows_generated` false / violations 0。
- `snapshot-guard --phase preflight`（state file は `/tmp`）: expected 80 /
  present 64 / `not_repository_retained` 22 / missing 0 / warnings 0 /
  refused false。
- `make audit-snapshots`（partial checkout）: 最初の再生成で HHBD の
  raw-derived row 1 件が `intentionally_dropped` として消え（before 59 /
  after 58 / lost 0 / refused false）、以後は before 58 / after 58 /
  `intentionally_dropped` 0 で同一出力に再現する。失われた row の run id は
  sidecar の `not_repository_retained_run_ids` に残る。

## owner 確認事項

1. **policy 既定の妥当性**: `raw-social-default`（YouTube を `git_untracked`）と
   `raw-search-tracked`（Google Trends を `git_tracked`）を、run 単位の明示判断が
   無い場合の既定として維持してよいか。
2. **既存 YouTube run の扱い**: 現状は判断記録を追加していない。owner / legal が
   「commit しない」判断を記録する場合のみ、`raw_retention_decision` を追加する。
3. **snapshot postflight（決定済み、owner 2026-11-02）**: `git_untracked` の run 行が
   スナップショット再生成で消えることは許容する。snapshot は checkout-local
   inventory であり、`docs/audits/snapshot-scope.json` が
   `audit_scope: checkout_local` / `raw_visibility: partial` /
   `not_repository_retained_run_ids` を記録する。catalog / declaration が完全な
   provenance claim の正本。raw 行は生成しない。
4. **CI**: `audit-raw-retention` を CI に追加するか（判断記録と policy は repo 事実
   だけで検査できる）。

## 完了条件

- [ ] 上記 1〜2 の owner 判断が記録されている（3 は 2026-11-02 に決定済み）。
- [ ] `make audit-raw-retention` と `make audit-raw-completeness` が、raw を欠く
      checkout で 0、`git_tracked` の欠落または判断記録の不正で非 0 になる。
- [ ] 新しい run を採用するとき、保持状態と（必要なら）判断記録が同じコミットに
      含まれている。
- [ ] 行単位の video / social データを公開しない方針が維持されている。

## 関連

- `ISS-20261101-PRV-017`: 監査スナップショットを checkout-local inventory とし、
  11 スナップショット + scope sidecar を partial checkout で安全に再生成する問題。
- `ISS-20261101-PRV-018`: committed catalog / declaration と raw の対応を検査する問題。
- `ISS-20261015-COL-030` §4.1: 投稿単位データを公開しない決定。
