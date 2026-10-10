#!/bin/bash
# YouTube「直近期間」冪等性検証スクリプト (Apify: streamers/youtube-scraper)
#
# dateFilter で直近期間に絞り込み、同一パラメータで2回独立取得して
# videoId の重複率を測る。
#
#   - danek/youtube-search (gJvjeCYNraSfhIaNd) は日付フィルタが無いため使わない
#   - streamers/youtube-scraper (h7sDV53CddomktSi5) は dateFilter で期間指定可
#     dateFilter は相対期間のみ（hour/today/week/month/year）。絶対日付は不可
#
# 使い方:
#   bash scripts/debug/youtube_idempotency_check.sh [search_term] [dateFilter]
#
# 例:
#   bash scripts/debug/youtube_idempotency_check.sh "CBD リキッド" week
#
# dateFilter の値:
#   hour  = Last hour（過去1時間）
#   today = Today（今日）
#   week  = This week（今週）  ← 既定
#   month = This month（今月）
#   year  = This year（今年）
#
# 環境変数:
#   APIFY_ENV  Apify トークンの env ファイル
#
# 判定基準（評価レポート B4 に準拠）:
#   ≥95% PASS / 80-94% CONDITIONAL / <80% FAIL
#
# 終了コード:
#   0 = 完了 / 1 = エラー

set -u

SEARCH_TERM="${1:-CBD リキッド}"
DATE_FILTER="${2:-month}"
ACTOR_ID="h7sDV53CddomktSi5"
# Actor 仕様: 3つの上限（maxResults/maxResultsShorts/maxResultStreams）のうち
# 少なくとも1つを >0 にする必要がある。schema 上の maximum は 999999。
MAX_RESULTS="${MAX_RESULTS:-20}"
APIFY_ENV="${APIFY_ENV:-/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env}"

# --- 前提チェック ---
if [ ! -f "$APIFY_ENV" ]; then
  echo "❌ env ファイルが見つかりません: $APIFY_ENV"
  exit 1
fi
# shellcheck disable=SC1090
source "$APIFY_ENV"
if [ -z "${APIFY_TOKEN:-}" ]; then
  echo "❌ APIFY_TOKEN が設定されていません ($APIFY_ENV)"
  exit 1
fi
command -v jq >/dev/null || { echo "❌ jq が必要です"; exit 1; }

case "$DATE_FILTER" in
  hour|today|week|month|year) ;;
  *) echo "❌ dateFilter は hour|today|week|month|year のいずれか"; exit 1 ;;
esac

AUTH="Authorization: Bearer $APIFY_TOKEN"
OUT1="/tmp/yt_idem_run1.txt"
OUT2="/tmp/yt_idem_run2.txt"

echo "========================================="
echo "YouTube 直近期間 冪等性検証 (Apify)"
echo "========================================="
echo "検索クエリ : $SEARCH_TERM"
echo "期間       : dateFilter=$DATE_FILTER"
echo "上限件数   : なし（全件取得）"
echo "Actor      : $ACTOR_ID (streamers/youtube-scraper)"
echo "========================================="
echo ""

search() {  # $1 = ラベル, 標準出力に videoId 一覧
  local label="$1"
  local r run ds status
  r=$(curl -s -X POST "https://api.apify.com/v2/acts/${ACTOR_ID}/runs?waitForFinish=180" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d "$(jq -n --arg q "$SEARCH_TERM" --argjson m "$MAX_RESULTS" --arg f "$DATE_FILTER" \
          '{searchQueries: [$q], maxResults: $m,
            maxResultsShorts: 0, maxResultStreams: 0,
            dateFilter: $f, sortingOrder: "date"}')")
  run=$(echo "$r" | jq -r '.data.id // empty')
  ds=$(echo "$r" | jq -r '.data.defaultDatasetId // empty')
  status=$(echo "$r" | jq -r '.data.status // "UNKNOWN"')
  echo "[$label] run=$run status=$status" >&2
  if [ -z "$ds" ]; then
    echo "❌ [$label] dataset 取得失敗: $(echo "$r" | jq -c .)" >&2
    return 1
  fi
  curl -s "https://api.apify.com/v2/datasets/${ds}/items?clean=true&format=json" \
    -H "$AUTH" | jq -r '[.[] | .id // empty] | unique | .[]'
}

# --- Step 1: 2回独立取得 ---
echo "【Step 1】RUN1 取得中..."
search "RUN1" | sort > "$OUT1" || exit 1
N1=$(wc -l < "$OUT1" | tr -d ' ')
echo "  件数: $N1"

echo "【Step 2】RUN2 取得中（5秒間隔）..."
sleep 5
search "RUN2" | sort > "$OUT2" || exit 1
N2=$(wc -l < "$OUT2" | tr -d ' ')
echo "  件数: $N2"
echo ""

# --- Step 2.5: 両方0件なら期間を広げるよう案内 ---
if [ "$N1" -eq 0 ] && [ "$N2" -eq 0 ]; then
  echo "⚠️  両runとも0件。dateFilter=$DATE_FILTER では該当動画が無い可能性。"
  echo "   month や year に広げて再実行してください:"
  echo "   bash $0 \"$SEARCH_TERM\" month"
  exit 1
fi

# --- Step 3: 重複率計算 ---
echo "【Step 3】重複率計算..."
python3 - "$OUT1" "$OUT2" << 'PY'
import sys

a = set(open(sys.argv[1]).read().split())
b = set(open(sys.argv[2]).read().split())

if not a or not b:
    print("⚠️  片方が空のため重複率は算出不可")
    print(f"    RUN1={len(a)} RUN2={len(b)}")
    raise SystemExit(1)

inter = len(a & b)
union = len(a | b)
jaccard = inter * 100 / union
recall = inter * 100 / len(a)

print(f"  RUN1        : {len(a)}")
print(f"  RUN2        : {len(b)}")
print(f"  共通 ID     : {inter}")
print(f"  和集合      : {union}")
print(f"  重複率(Jaccard)    : {jaccard:.1f}%")
print(f"  重複率(RUN1基準)   : {recall:.1f}%")
print()

verdict = ("✅ PASS (≥95%)" if jaccard >= 95
           else "⚠️ CONDITIONAL (80-94%)" if jaccard >= 80
           else "❌ FAIL (<80%)")
print(f"  判定: {verdict}")

if a - b:
    print(f"\n  RUN1 のみに存在: {len(a - b)} 件")
if b - a:
    print(f"  RUN2 のみに存在: {len(b - a)} 件")
PY

echo ""
echo "========================================="
echo "完了"
echo "  RUN1 IDs: $OUT1"
echo "  RUN2 IDs: $OUT2"
echo "========================================="
exit 0
