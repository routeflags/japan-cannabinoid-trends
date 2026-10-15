# Issue: pre-commit に cerberus 依存の検証を入れられない（stdlib 限定の方針）

**ID:** ISS-20261015-COL-020  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
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

- [ ] 方針決定（縮小検査を入れる / 入れない）
- [ ] 決定に応じたフックまたは文書の更新
