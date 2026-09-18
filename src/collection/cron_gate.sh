#!/bin/bash
# cron から毎時起動される前提のゲート。通過時のみ取得スクリプトを実行する。
# 使い方: cron_gate.sh
#   - 当日分の取得ファイルがあればスキップ（日内重複排除）
#   - なければ 1/TEITEN_DENOM の確率で実行（既定 24 → 毎時1/24）
#   - 確率は環境変数 TEITEN_DENOM で変更可
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"
D="$(date +%Y%m%d)"
OUTDIR="$ROOT/projects/automation/Apify/data/teiten_$D"
N="${TEITEN_DENOM:-24}"

if ls "$OUTDIR"/tiktok_*.json "$OUTDIR"/ig_*.json >/dev/null 2>&1; then
  echo "skip: $D は取得済み"
  exit 0
fi
if [ "$((RANDOM % N))" -ne 0 ]; then
  echo "skip: 確率ゲート (1/$N)"
  exit 0
fi
TEITEN_DATE="$D" "$DIR/fetch_tiktok.sh"
TEITEN_DATE="$D" "$DIR/fetch_instagram.sh"
