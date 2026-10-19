#!/bin/bash
# Apify Actor を実行し、結果データセットを保存する共通ヘルパー
# 使い方: apify_run.sh <actor_id> <input_json> <out_base>
#   <out_base>_run.json（run 応答）と <out_base>.json（取得データ）を保存する
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# 引数検証を認証より先に行う（credentials 無しでも不正な出力先は弾ける）。
ACTOR="${1:?actor_id を指定}"
INPUT_JSON="${2:?input_json を指定}"
OUT_BASE="${3:?out_base を指定}"

# パスを字句的に正規化する（`./datasets/x` や `a/../datasets/x` を素通りさせない）。
# シンボリックリンクは解決しない。それが問題になる場合は呼び出し側で実パスに直すこと。
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

# 生データを datasets/ へ直接書かない。framework を迂回した run は
# collection-run-v1 の provenance を満たせないため、CI の
# `validation.cli audit-new-runs` で落ちる（fail closed）。
# ステージング先へ出力し、`collection.core.cli adopt` に渡すこと。
OUT_NORM="$(normalize_path "$OUT_BASE")"
ROOT_NORM="$(normalize_path "$ROOT")"
case "$OUT_NORM" in
  "$ROOT_NORM"/datasets|"$ROOT_NORM"/datasets/*)
    echo "apify_run.sh: 出力先が datasets/ 配下です: $OUT_BASE" >&2
    echo "  framework を迂回した run は契約を満たせません。" >&2
    echo "  ステージング先へ出力し、次で取り込んでください:" >&2
    echo "    python -m collection.core.cli adopt --staged <dir>" >&2
    exit 2
    ;;
esac

if [ -f "$ROOT/.env.d/apify.env" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env.d/apify.env"
fi
if [ -z "${APIFY_TOKEN:-}" ]; then
  echo "APIFY_TOKEN が未設定 (.env.d/apify.env を確認)" >&2
  exit 1
fi
command -v jq >/dev/null 2>&1 || { echo "jq が必要" >&2; exit 1; }
NETLOOM_BIN="${NETLOOM_BIN:-/Users/bookair18/.local/bin/netloom}"
if [ ! -x "$NETLOOM_BIN" ]; then
  NETLOOM_BIN="$(command -v netloom || true)"
fi
[ -n "$NETLOOM_BIN" ] || { echo "netloom が必要" >&2; exit 1; }

RESP="$("$NETLOOM_BIN" apify run --actor "$ACTOR" --input "$INPUT_JSON" --wait 120)"
echo "$RESP" > "${OUT_BASE}_run.json"

# netloom apify run は Apify run 応答を返す想定だが、envelope は live 未検証。
# そのため {"data": {...}} と直下 run オブジェクトの両方を読む。疑義があれば
# `netloom apify run-status --run-id "$RUNID"` で確認する。
ERR="$(echo "$RESP" | jq -r '.data.error.message // .error.message // empty')"
if [ -n "$ERR" ]; then
  echo "Apify API エラー: $ERR" >&2
  exit 1
fi
STATUS="$(echo "$RESP" | jq -r '.data.status // .status // "UNKNOWN"')"
DS="$(echo "$RESP" | jq -r '.data.defaultDatasetId // .defaultDatasetId // empty')"
RUNID="$(echo "$RESP" | jq -r '.data.id // .id // empty')"
echo "run: id=${RUNID:-?} status=${STATUS:-UNKNOWN} dataset=${DS:-none}"
if [ "${STATUS:-UNKNOWN}" != "SUCCEEDED" ]; then
  echo "警告: status=${STATUS:-UNKNOWN}（取得は続行）" >&2
fi
if [ -z "${DS:-}" ]; then
  echo "datasetId 取得失敗" >&2
  exit 1
fi

"$NETLOOM_BIN" apify dataset --dataset-id "$DS" --as json --out "${OUT_BASE}.json"
COUNT="$(jq 'length' "${OUT_BASE}.json")"
echo "saved: ${OUT_BASE}.json (${COUNT}件)"
