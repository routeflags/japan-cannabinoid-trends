#!/bin/bash
# TikTok 定点観測の取得スクリプト
# 使い方: fetch_tiktok.sh [slug...]  （省略時は cbx h4cbh hhbd の3件）
#
# COL-019 (2026-10-15): 既定の保存先だった
# `projects/automation/Apify/data/teiten_YYYYMMDD/` は、リポジトリに存在しない
# side channel のため retired。既定では何も書かず exit 2 で止まる
# (fail closed)。手動 handover 用に TEITEN_OUTDIR で明示した caller-owned の
# scratch / staging への出力だけを通し、リポジトリの `datasets/` / `projects/`
# 配下は明示指定でも拒否する。採用は `collection.core.cli adopt` が行う。
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"
D="${TEITEN_DATE:-$(date +%Y%m%d)}"

# パスを字句的に正規化する（`src/collection/apify_run.sh` の同名関数と同じ規則。
# シンボリックリンクは解決しない。それが問題になる場合は呼び出し側で実パスに直すこと）。
normalize_path() {
  local p="$1" out="" part old_ifs
  case "$p" in
    /*) ;;
    *) p="$PWD/$p" ;;
  esac
  old_ifs="$IFS"; IFS=/; set -- $p; IFS="$old_ifs"
  for part in "$@"; do
    case "$part" in
      ""|.) continue ;;
      ..) out="${out%/*}" ;;
      *) out="$out/$part" ;;
    esac
  done
  printf '%s' "${out:-/}"
}

# 既定の teiten 出力先は retired (ISS-20261015-COL-019): 何も作らず止まる。
# この検査は mkdir・認証・network より前に置く（credentials 無しでも拒否できる）。
OUTDIR="${TEITEN_OUTDIR:-}"
if [ -z "$OUTDIR" ]; then
  echo "fetch_tiktok.sh: 既定の teiten 出力先 (projects/ 配下) は retired です (ISS-20261015-COL-019)。" >&2
  echo "  手動 handover は TEITEN_OUTDIR=<scratch/staging> を明示し、次で取り込んでください:" >&2
  echo "    python -m collection.core.cli adopt --staged <dir>" >&2
  exit 2
fi

# 明示指定でもリポジトリの datasets/・projects/ 配下には書かない。
# framework を迂回した run は collection-run-v1 の provenance を満たせない。
OUT_NORM="$(normalize_path "$OUTDIR")"
ROOT_NORM="$(normalize_path "$ROOT")"
case "$OUT_NORM" in
  "$ROOT_NORM"/datasets|"$ROOT_NORM"/datasets/*|"$ROOT_NORM"/projects|"$ROOT_NORM"/projects/*)
    echo "fetch_tiktok.sh: 出力先がリポジトリ管理外の side channel です: $OUTDIR" >&2
    echo "  ステージング先へ出力し、次で取り込んでください:" >&2
    echo "    python -m collection.core.cli adopt --staged <dir>" >&2
    exit 2
    ;;
esac
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
  "$DIR/../apify_run.sh" "jQfZ1h9FrcWcliKZX" "$INPUT" "$OUTDIR/tiktok_${s}"
done
