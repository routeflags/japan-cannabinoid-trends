#!/bin/bash
# TikTok 定点観測の取得スクリプト
# 使い方: fetch_tiktok.sh [slug...]  （省略時は cbx h4cbh hhbd の3件）
# 保存先: projects/automation/Apify/data/teiten_YYYYMMDD/tiktok_<slug>.json
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"
D="${TEITEN_DATE:-$(date +%Y%m%d)}"
OUTDIR="$ROOT/projects/automation/Apify/data/teiten_$D"
mkdir -p "$OUTDIR"

slug_to_kw() {
  case "$1" in
    cbx)   echo "CBXリキッド" ;;
    h4cbh) echo "H4CBH" ;;
    hhbd)  echo "HHBDリキッド" ;;
    *) echo "unknown slug: $1 (cbx/h4cbh/hhbd)" >&2; exit 1 ;;
  esac
}

# shellcheck disable=SC2086
for s in ${*:-cbx h4cbh hhbd}; do
  KW="$(slug_to_kw "$s")"
  echo "=== TikTok [$KW] ==="
  INPUT="$(jq -n --arg kw "$KW" \
    '{keyword:$kw, region:"JP", sortType:0, publishTime:"ALL_TIME", limit:20}')"
  "$DIR/apify_run.sh" "jQfZ1h9FrcWcliKZX" "$INPUT" "$OUTDIR/tiktok_${s}"
done
