#!/usr/bin/env bash
# =============================================================================
# install.sh — pre-commit フックの導入
#
# リポジトリ正本（scripts/git-hooks/pre-commit）を .git/hooks/pre-commit へ
# 導入する。冪等（再実行可）。worktree でも動作するよう hooks 先は
# `git rev-parse --git-path` で解決する。
#
# 使用方法:
#   bash scripts/git-hooks/install.sh
#
# 導入後の検証は /tmp の scratch clone でのみ行うこと（実 worktree では
#   git add / commit しない）。詳細は docs/specs/validation-framework.md §2。
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

HOOK_SRC="${REPO_ROOT}/scripts/git-hooks/pre-commit"
HOOK_DST="$(git rev-parse --git-path hooks)/pre-commit"

if [ ! -f "$HOOK_SRC" ]; then
  echo "❌ 正本が見つかりません: $HOOK_SRC" >&2
  exit 1
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

# 導入確認: 内容一致＋実行権限
if ! diff -q "$HOOK_SRC" "$HOOK_DST" >/dev/null; then
  echo "❌ 導入後の内容が正本と一致しません" >&2
  exit 1
fi
if [ ! -x "$HOOK_DST" ]; then
  echo "❌ 実行権限が付与されていません: $HOOK_DST" >&2
  exit 1
fi

bash -n "$HOOK_DST"

echo "✅ pre-commit フックを導入しました: $HOOK_DST"
