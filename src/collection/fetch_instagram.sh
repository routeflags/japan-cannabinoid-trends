#!/bin/bash
# Instagram 定点観測の取得スクリプト
# 使い方: fetch_instagram.sh [slug...]  （省略時は cbx h4cbh hhbd の3件）
# 保存先: projects/automation/Apify/data/teiten_YYYYMMDD/ig_<slug>.json
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
    hhbd)  echo "HHBD" ;;
    *) echo "unknown slug: $1 (cbx/h4cbh/hhbd)" >&2; exit 1 ;;
  esac
}

# shellcheck disable=SC2086
for s in ${*:-cbx h4cbh hhbd}; do
  KW="$(slug_to_kw "$s")"
  echo "=== Instagram [$KW] ==="
  INPUT="$(jq -n --arg kw "$KW" '{query:$kw, limit:15}')"
  "$DIR/apify_run.sh" "TxU0ZBQIHdR20dr9C" "$INPUT" "$OUTDIR/ig_${s}"
done
