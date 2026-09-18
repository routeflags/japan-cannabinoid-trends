#!/bin/bash
# Apify Actor を実行し、結果データセットを保存する共通ヘルパー
# 使い方: apify_run.sh <actor_id> <input_json> <out_base>
#   <out_base>_run.json（run 応答）と <out_base>.json（取得データ）を保存する
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ -f "$ROOT/.env.d/apify.env" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env.d/apify.env"
fi
if [ -z "${APIFY_TOKEN:-}" ]; then
  echo "APIFY_TOKEN が未設定 (.env.d/apify.env を確認)" >&2
  exit 1
fi
command -v jq >/dev/null 2>&1 || { echo "jq が必要" >&2; exit 1; }

ACTOR="${1:?actor_id を指定}"
INPUT_JSON="${2:?input_json を指定}"
OUT_BASE="${3:?out_base を指定}"

RESP="$(curl -s -X POST "https://api.apify.com/v2/acts/${ACTOR}/runs?waitForFinish=120" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d "$INPUT_JSON")"
echo "$RESP" > "${OUT_BASE}_run.json"

# Apify API は run オブジェクトを {"data": {...}} で包む。失敗時は {"error": {...}}
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

curl -s "https://api.apify.com/v2/datasets/${DS}/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" -o "${OUT_BASE}.json"
COUNT="$(jq 'length' "${OUT_BASE}.json")"
echo "saved: ${OUT_BASE}.json (${COUNT}件)"
