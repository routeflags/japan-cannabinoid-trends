# Issue: pre-commit に cerberus 依存の検証を入れられない（stdlib 限定の方針）

**ID:** ISS-20261015-COL-020
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `scripts/git-hooks/pre-commit`, `.github/workflows/research-validation.yml`, `docs/specs/validation-framework.md` §22.4

## 概要

pre-commit フックは stdlib のみで動く検証（スキーマ・版同期・調査ページ・emergence
tracker・processed 再現性・X 識別情報）に限定されている。cerberus を要する検証
（`validate-registries` / `audit-new-runs` / `audit-issues` の一部）はフックに入らず、
CI 実行まで検出されない。

## 確認された観測

- フック 6 検証は `python3`（venv 無し）で動く設計。
- CI（`.github/workflows/research-validation.yml`）は pytest と各 audit を実行する。
- 新規収集 run の契約適合をローカルで確認する手段は、手動の pytest / audit 実行のみ。

## 影響

- 契約不適合の run をコミットしてしまい、CI で初めて検出される。
- フックと CI で「どこまで止められるか」の差が文書化されていない。

## 対応方針

- 依存を追加しない方針を維持するなら、stdlib で書ける範囲（run_metadata の必須キー存在・
  ハッシュ一致など）の縮小検査を検討する。
- 現状を確定とするなら、その判断と限界（CI で検出する項目）を文書化する。

## 完了条件

- [x] 方針決定（縮小検査を入れる / 入れない） — **縮小検査を入れる**（2026-10-15）
- [x] 決定に応じたフックまたは文書の更新 — フック §7 追加＋§22.4 更新（下記「実装記録」）

## 実装記録（2026-10-15）

- 方針: 縮小検査を入れる。stdlib 限定方針は維持し、cerberus 依存の完全検証は
  CI / `audit-new-runs` に残す（`docs/specs/validation-framework.md` §22.4 に分担を記録）。
- `src/validation/staged_runs.py`（新規、stdlib のみ）: staged の
  `datasets/*/data/raw/*/*/run_metadata.json` を Git index（`git show :<path>`）から
  読み、JSON 可読・`run_id`（非空文字列）・新規 run の最小 provenance キー存在
  （`study_id` / `source_id` / `collector.collector_id` / `collector.adapter_id` /
  `collection_started_at` / `query_provenance.query_id` / `execution.status` /
  `execution.returned_count` / `execution.errors`）を確認する。凍結 legacy は
  `validation.legacy.LEGACY_RUN_IDS` を正本として免除する（`run_id` 不明時は免除なし）。
  エラー出力はパス＋不足 dotted path / `malformed JSON` のみ（payload・秘密情報は出さない）。
- `scripts/git-hooks/pre-commit`: §7 追加。`datasets/*/data/raw/*` の staged が
  あるときだけ発火し、出力に軽量検査である旨と CI（`audit-new-runs`）の権威性を明示。
  無関係のコミットは従来どおり早期 exit 0。
- `tests/validation/test_staged_runs.py`（新規 17 件）: 正常系・不足キー・不正 JSON・
  凍結免除・index 読み（worktree 改変の無視）・cerberus ブロック下の実行・フック発火。
  実 `datasets/**/data/raw` には触れない（tmp git リポジトリのみ）。
- 検証: 新規テスト 17 passed、`audit-issues` failures=0、`audit-new-runs` 実施。
  raw 観測・公開物・release・Zenodo・`release-archives/`・実収集には触れていない。

**ステータス: RESOLVED（2026-10-15）**。
