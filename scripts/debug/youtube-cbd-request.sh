#!/bin/bash
# CBD リキッド YouTube リクエスト デバッグスクリプト
#
# 使い方:
#   bash scripts/debug/youtube-cbd-request.sh [max_videos] [search_term]
#
# 例:
#   bash scripts/debug/youtube-cbd-request.sh 100
#   bash scripts/debug/youtube-cbd-request.sh 100 "CBD リキッド"

set -e

# 設定
DB_PATH="${DB_PATH:-datasets/youtube-consistency/data/trends.db}"
APIFY_ENV="${APIFY_ENV:-/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env}"
ACTOR_ID="gJvjeCYNraSfhIaNd"

# パラメータ
MAX_VIDEOS="${1:-100}"
SEARCH_TERM="${2:-CBD リキッド}"

# Apify トークン読み込み
source "$APIFY_ENV"

echo "========================================="
echo "YouTube リクエスト デバッグスクリプト"
echo "========================================="
echo ""
echo "検索クエリ: $SEARCH_TERM"
echo "max_videos: $MAX_VIDEOS"
echo "データベース: $DB_PATH"
echo ""

# 実行 ID 生成
RUN_ID="debug_$(date -u +"%Y%m%dT%H%M%SZ")"
echo "Run ID: $RUN_ID"
echo ""

# Step 1: API 実行
echo "【Step 1】API 実行中..."
R=$(curl -s -X POST "https://api.apify.com/v2/acts/${ACTOR_ID}/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"search_term\":\"${SEARCH_TERM}\",\"max_videos\":${MAX_VIDEOS}}")

APIFY_RUN_ID=$(echo "$R" | jq -r '.data.id')
DATASET_ID=$(echo "$R" | jq -r '.data.defaultDatasetId')
STATUS=$(echo "$R" | jq -r '.data.status')

echo "  Apify Run ID: $APIFY_RUN_ID"
echo "  Dataset ID: $DATASET_ID"
echo "  Status: $STATUS"
echo ""

if [ "$STATUS" != "SUCCEEDED" ]; then
  echo "❌ API 実行失敗"
  exit 1
fi

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
jq -r '.[].id.videoId' "/tmp/${RUN_ID}_raw.json" | sort > "/tmp/${RUN_ID}_ids.txt"
jq -r '.[].id.videoId' "/tmp/${RUN_ID}_raw.json" | sort -u > "/tmp/${RUN_ID}_unique.txt"

TOTAL_LINES=$(wc -l < "/tmp/${RUN_ID}_ids.txt")
UNIQUE_COUNT=$(wc -l < "/tmp/${RUN_ID}_unique.txt")
DUPLICATE_COUNT=$((TOTAL_LINES - UNIQUE_COUNT))

echo "  総行数: $TOTAL_LINES"
echo "  ユニークID数: $UNIQUE_COUNT"
echo "  重複数: $DUPLICATE_COUNT"
echo ""

# Step 4: 重複分析
echo "【Step 4】重複分析..."
echo "  重複回数の分布:"
sort "/tmp/${RUN_ID}_ids.txt" | uniq -c | awk '{print $1}' | sort | uniq -c | sort -rn | while read count freq; do
  echo "    ${freq}回重複: ${count}件"
done
echo ""

# Step 5: SQLite 格納
echo "【Step 5】SQLite 格納中..."

# Run 情報を格納
sqlite3 "$DB_PATH" << EOF
INSERT OR REPLACE INTO runs (run_id, search_term, max_videos, apify_dataset_id, collection_timestamp, record_count, unique_count, collector, collector_version)
VALUES ('${RUN_ID}', '${SEARCH_TERM}', ${MAX_VIDEOS}, '${DATASET_ID}', datetime('now'), ${RECORD_COUNT}, ${UNIQUE_COUNT}, 'apify', 'debug_script');
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

# Step 6: 一致率計算
echo "【Step 6】一致率計算..."
sqlite3 "$DB_PATH" << EOF
WITH cumulative AS (
    SELECT DISTINCT rv.video_id
    FROM run_videos rv
    JOIN runs r ON rv.run_id = r.run_id
    WHERE r.run_id != '${RUN_ID}'
),
current_run AS (
    SELECT DISTINCT video_id
    FROM run_videos
    WHERE run_id = '${RUN_ID}'
)
SELECT 
    COUNT(*) as unique_count,
    SUM(CASE WHEN c.video_id IN (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END) as already_collected,
    SUM(CASE WHEN c.video_id NOT IN (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END) as new_videos
FROM current_run c;
EOF

echo ""

# Step 7: 結果サマリー
echo "========================================="
echo "結果サマリー"
echo "========================================="
echo ""
echo "【Run 情報】"
echo "  Run ID: $RUN_ID"
echo "  Apify Run ID: $APIFY_RUN_ID"
echo "  検索クエリ: $SEARCH_TERM"
echo "  max_videos: $MAX_VIDEOS"
echo ""

echo "【取得結果】"
echo "  総行数: $TOTAL_LINES"
echo "  ユニークID数: $UNIQUE_COUNT"
echo "  重複数: $DUPLICATE_COUNT"
echo ""

echo "【累積統計】"
sqlite3 "$DB_PATH" << EOF
SELECT 
    '総ユニーク動画数: ' || COUNT(*) 
FROM videos;
EOF

sqlite3 "$DB_PATH" << EOF
SELECT 
    '総Run数: ' || COUNT(*)
FROM runs;
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
