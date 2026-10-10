#!/bin/bash
# YouTube Data API 日付範囲指定データ取得スクリプト
#
# 使い方:
#   bash scripts/debug/youtube-api-date-range.sh [search_term] [published_after] [published_before] [max_results]
#
# 例:
#   bash scripts/debug/youtube-api-date-range.sh "CBD リキッド" "2026-01-01" "2026-04-01" 50

set -e

# 設定
DB_PATH="${DB_PATH:-datasets/youtube-consistency/data/trends.db}"
YOUTUBE_ENV="${YOUTUBE_ENV:-/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env}"

# パラメータ
SEARCH_TERM="${1:-CBD リキッド}"
PUBLISHED_AFTER="${2:-2026-01-01}"
PUBLISHED_BEFORE="${3:-2026-04-01}"
MAX_RESULTS="${4:-50}"

# YouTube API キー読み込み
source "$YOUTUBE_ENV"

echo "========================================="
echo "YouTube Data API 日付範囲指定データ取得"
echo "========================================="
echo ""
echo "検索クエリ: $SEARCH_TERM"
echo "開始日: $PUBLISHED_AFTER"
echo "終了日: $PUBLISHED_BEFORE"
echo "maxResults: $MAX_RESULTS"
echo "データベース: $DB_PATH"
echo ""

# 実行 ID 生成
RUN_ID="yt_api_$(date -u +"%Y%m%dT%H%M%SZ")"
echo "Run ID: $RUN_ID"
echo ""

# Step 1: API 実行
echo "【Step 1】API 実行中..."

# 日付を RFC 3339 形式に変換
PUBLISHED_AFTER_RFC3339="${PUBLISHED_AFTER}T00:00:00Z"
PUBLISHED_BEFORE_RFC3339="${PUBLISHED_BEFORE}T00:00:00Z"

R=$(curl -s "https://www.googleapis.com/youtube/v3/search" \
  -H "Authorization: Bearer $YOUTUBE_API_KEY" \
  --data-urlencode "part=snippet" \
  --data-urlencode "q=${SEARCH_TERM}" \
  --data-urlencode "type=video" \
  --data-urlencode "publishedAfter=${PUBLISHED_AFTER_RFC3339}" \
  --data-urlencode "publishedBefore=${PUBLISHED_BEFORE_RFC3339}" \
  --data-urlencode "maxResults=${MAX_RESULTS}" \
  --data-urlencode "order=date")

# エラーチェック
ERROR=$(echo "$R" | jq -r '.error.message // empty')
if [ -n "$ERROR" ]; then
  echo "❌ API エラー: $ERROR"
  echo "$R" | jq .
  exit 1
fi

# 結果をファイルに保存
echo "$R" > "/tmp/${RUN_ID}_raw.json"

ITEM_COUNT=$(echo "$R" | jq '.items | length')
NEXT_PAGE_TOKEN=$(echo "$R" | jq -r '.nextPageToken // empty')

echo "  取得件数: $ITEM_COUNT"
echo "  次ページトークン: ${NEXT_PAGE_TOKEN:-なし}"
echo ""

# Step 2: videoId 抽出
echo "【Step 2】videoId 抽出中..."
jq -r '.items[].id.videoId' "/tmp/${RUN_ID}_raw.json" | sort > "/tmp/${RUN_ID}_ids.txt"
jq -r '.items[].id.videoId' "/tmp/${RUN_ID}_raw.json" | sort -u > "/tmp/${RUN_ID}_unique.txt"

TOTAL_LINES=$(wc -l < "/tmp/${RUN_ID}_ids.txt")
UNIQUE_COUNT=$(wc -l < "/tmp/${RUN_ID}_unique.txt")
DUPLICATE_COUNT=$((TOTAL_LINES - UNIQUE_COUNT))

echo "  総行数: $TOTAL_LINES"
echo "  ユニークID数: $UNIQUE_COUNT"
echo "  重複数: $DUPLICATE_COUNT"
echo ""

# Step 3: 日付範囲確認
echo "【Step 3】日付範囲確認..."
jq -r '.items[].snippet.publishedAt' "/tmp/${RUN_ID}_raw.json" | sort | head -1 | xargs -I {} echo "  最古: {}"
jq -r '.items[].snippet.publishedAt' "/tmp/${RUN_ID}_raw.json" | sort | tail -1 | xargs -I {} echo "  最新: {}"
echo ""

# Step 4: SQLite 格納
echo "【Step 4】SQLite 格納中..."

# Run 情報を格納
sqlite3 "$DB_PATH" << EOF
INSERT OR REPLACE INTO runs (run_id, search_term, max_videos, apify_dataset_id, collection_timestamp, record_count, unique_count, collector, collector_version)
VALUES ('${RUN_ID}', '${SEARCH_TERM}', ${MAX_RESULTS}, 'youtube-data-api', datetime('now'), ${ITEM_COUNT}, ${UNIQUE_COUNT}, 'youtube-api', 'data-api-v3');
EOF

# 動画情報を格納
jq -r '.items[] | "\(.id.videoId)\t\(.snippet.title)\t\(.snippet.channelTitle)\t\(.snippet.publishedAt)"' "/tmp/${RUN_ID}_raw.json" | \
while IFS=$'\t' read -r vid title channel published; do
  sqlite3 "$DB_PATH" << EOF
INSERT OR IGNORE INTO videos (video_id, first_seen_run, first_seen_at)
VALUES ('${vid}', '${RUN_ID}', datetime('now'));

INSERT OR IGNORE INTO run_videos (run_id, video_id)
VALUES ('${RUN_ID}', '${vid}');
EOF
done

echo "  ✅ 格納完了"
echo ""

# Step 5: 一致率計算
echo "【Step 5】一致率計算..."
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

# Step 6: 結果サマリー
echo "========================================="
echo "結果サマリー"
echo "========================================="
echo ""
echo "【Run 情報】"
echo "  Run ID: $RUN_ID"
echo "  検索クエリ: $SEARCH_TERM"
echo "  開始日: $PUBLISHED_AFTER"
echo "  終了日: $PUBLISHED_BEFORE"
echo "  maxResults: $MAX_RESULTS"
echo ""

echo "【取得結果】"
echo "  取得件数: $ITEM_COUNT"
echo "  次ページトークン: ${NEXT_PAGE_TOKEN:-なし}"
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
