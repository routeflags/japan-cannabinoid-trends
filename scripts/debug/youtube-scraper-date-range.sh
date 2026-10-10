#!/bin/bash
# YouTube 日付範囲指定データ取得スクリプト
#
# 使い方:
#   bash scripts/debug/youtube-scraper-date-range.sh [search_term] [oldest_date] [max_results]
#
# 例:
#   bash scripts/debug/youtube-scraper-date-range.sh "CBD リキッド" "2026-01-01" 100

set -e

# 設定
DB_PATH="${DB_PATH:-datasets/youtube-consistency/data/trends.db}"
APIFY_ENV="${APIFY_ENV:-/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env}"
ACTOR_ID="h7sDV53CddomktSi5"

# パラメータ
SEARCH_TERM="${1:-CBD リキッド}"
OLDEST_DATE="${2:-2026-01-01}"
MAX_RESULTS="${3:-100}"

# Apify トークン読み込み
source "$APIFY_ENV"

echo "========================================="
echo "YouTube 日付範囲指定データ取得"
echo "========================================="
echo ""
echo "Actor: $ACTOR_ID"
echo "検索クエリ: $SEARCH_TERM"
echo "開始日: $OLDEST_DATE"
echo "maxResults: $MAX_RESULTS"
echo "データベース: $DB_PATH"
echo ""

# 実行 ID 生成
RUN_ID="yt_range_$(date -u +"%Y%m%dT%H%M%SZ")"
echo "Run ID: $RUN_ID"
echo ""

# Step 1: API 実行（URL使用で日付範囲指定）
echo "【Step 1】API 実行中..."
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SEARCH_TERM'))")

R=$(curl -s -X POST "https://api.apify.com/v2/acts/${ACTOR_ID}/runs" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"startUrls\": [{\"url\": \"https://www.youtube.com/results?search_query=${ENCODED_QUERY}\"}],
    \"maxResults\": ${MAX_RESULTS},
    \"maxResultsShorts\": 0,
    \"maxResultStreams\": 0,
    \"oldestPostDate\": \"${OLDEST_DATE}\",
    \"sortVideosBy\": \"NEWEST\"
  }")

APIFY_RUN_ID=$(echo "$R" | jq -r '.data.id')
DATASET_ID=$(echo "$R" | jq -r '.data.defaultDatasetId')

echo "  Apify Run ID: $APIFY_RUN_ID"
echo "  Dataset ID: $DATASET_ID"
echo "  実行を待機中..."
echo ""

# Step 1.5: 完了まで待機
MAX_WAIT=300
WAITED=0
STATUS="RUNNING"

while [ "$STATUS" != "SUCCEEDED" ] && [ "$STATUS" != "FAILED" ] && [ "$WAITED" -lt "$MAX_WAIT" ]; do
  sleep 10
  WAITED=$((WAITED + 10))
  
  STATUS=$(curl -s "https://api.apify.com/v2/actor-runs/${APIFY_RUN_ID}" \
    -H "Authorization: Bearer $APIFY_TOKEN" | jq -r '.data.status')
  
  echo "  経過時間: ${WAITED}秒 | ステータス: $STATUS"
done

echo ""

if [ "$STATUS" != "SUCCEEDED" ]; then
  echo "❌ API 実行失敗（ステータス: $STATUS）"
  exit 1
fi

echo "  ✅ 実行完了"

sleep 3

# Step 2: データ取得
echo "【Step 2】データ取得中..."
curl -s "https://api.apify.com/v2/datasets/${DATASET_ID}/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "/tmp/${RUN_ID}_raw.json"

RECORD_COUNT=$(jq 'length' "/tmp/${RUN_ID}_raw.json")
echo "  取得件数: $RECORD_COUNT"
echo ""

# Step 3: videoId 抽出
echo "【Step 3】videoId 抽出中..."
jq -r '.[].id' "/tmp/${RUN_ID}_raw.json" | sort > "/tmp/${RUN_ID}_ids.txt"
jq -r '.[].id' "/tmp/${RUN_ID}_raw.json" | sort -u > "/tmp/${RUN_ID}_unique.txt"

TOTAL_LINES=$(wc -l < "/tmp/${RUN_ID}_ids.txt")
UNIQUE_COUNT=$(wc -l < "/tmp/${RUN_ID}_unique.txt")
DUPLICATE_COUNT=$((TOTAL_LINES - UNIQUE_COUNT))

echo "  総行数: $TOTAL_LINES"
echo "  ユニークID数: $UNIQUE_COUNT"
echo "  重複数: $DUPLICATE_COUNT"
echo ""

# Step 4: 日付範囲確認
echo "【Step 4】日付範囲確認..."
python3 << EOF
import json
from datetime import datetime

with open(f"/tmp/${RUN_ID}_raw.json") as f:
    data = json.load(f)

dates = [item.get('date') for item in data if item.get('date')]
if dates:
    min_date = min(dates)
    max_date = max(dates)
    print(f"  最古: {min_date[:10]}")
    print(f"  最新: {max_date[:10]}")
    
    # 指定期間内の動画数
    oldest = datetime.fromisoformat("${OLDEST_DATE}")
    in_range = sum(1 for d in dates if datetime.fromisoformat(d.replace('Z', '+00:00')) >= oldest)
    print(f"  指定期間内: {in_range}件")
    
    # 年別分布
    years = {}
    for d in dates:
        year = d[:4]
        years[year] = years.get(year, 0) + 1
    print(f"  年別分布: {years}")
else:
    print("  ⚠️ 日付データなし")
EOF
echo ""

# Step 5: SQLite 格納
echo "【Step 5】SQLite 格納中..."

# Run 情報を格納
sqlite3 "$DB_PATH" << EOF
INSERT OR REPLACE INTO runs (run_id, search_term, max_videos, apify_dataset_id, collection_timestamp, record_count, unique_count, collector, collector_version)
VALUES ('${RUN_ID}', '${SEARCH_TERM}', ${MAX_RESULTS}, '${DATASET_ID}', datetime('now'), ${RECORD_COUNT}, ${UNIQUE_COUNT}, 'apify', 'youtube-scraper-date-range');
EOF

# 動画情報を格納
while IFS= read -r vid; do
  sqlite3 "$DB_PATH" << EOF
INSERT OR IGNORE INTO videos (video_id, first_seen_run, first_seen_at)
VALUES ('${vid}', '${RUN_ID}', datetime('now'));

INSERT OR IGNORE INTO run_videos (run_id, video_id)
VALUES ('${RUN_ID}', '${vid}');
EOF
done < "/tmp/${RUN_ID}_unique.txt"

echo "  ✅ 格納完了"
echo ""

# Step 6: 結果サマリー
echo "========================================="
echo "結果サマリー"
echo "========================================="
echo ""
echo "【Run 情報】"
echo "  Run ID: $RUN_ID"
echo "  Apify Run ID: $APIFY_RUN_ID"
echo "  検索クエリ: $SEARCH_TERM"
echo "  開始日: $OLDEST_DATE"
echo "  maxResults: $MAX_RESULTS"
echo ""

echo "【累積統計】"
sqlite3 "$DB_PATH" << EOF
SELECT 
    '総ユニーク動画数: ' || COUNT(DISTINCT v.video_id)
FROM videos v
JOIN run_videos rv ON v.video_id = rv.video_id
JOIN runs r ON rv.run_id = r.run_id
WHERE r.search_term = '${SEARCH_TERM}';
EOF

echo ""
echo "【ファイルパス】"
echo "  Raw: /tmp/${RUN_ID}_raw.json"
echo "  IDs: /tmp/${RUN_ID}_ids.txt"
echo "  Unique: /tmp/${RUN_ID}_unique.txt"
echo ""
echo "========================================="
echo "完了"
echo "========================================="
