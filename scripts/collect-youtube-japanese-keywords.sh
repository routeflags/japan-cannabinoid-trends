#!/bin/bash
# YouTube 日本語キーワードデータ収集スクリプト
# 実行日時: 2026-10-05 09:00 JST 以降
# 目的: 日本語キーワードで YouTube データを10年分収集

set -e

# 認証情報読み込み
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env

# パラメータ設定
STUDY_ID="cannabinoid-multi-trends"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
SAVE_DIR="datasets/${STUDY_ID}/data/raw/youtube/${TIMESTAMP}-youtube-japanese-keywords-10years"
mkdir -p "$SAVE_DIR"

# キーワードリスト
KEYWORDS=("CBD オイル" "カンナビノイド" "CBN オイル" "カンナビジェロール")

echo "=== 日本語キーワード YouTube データ収集開始 ==="
echo "開始日時: $(date)"
echo "保存先: ${SAVE_DIR}"
echo ""

# 年次データを収集する関数
collect_yearly() {
    local KEYWORD=$1
    local YEAR=$2
    
    # 期間の定義
    local START="${YEAR}-01-01T00:00:00Z"
    local END="$((YEAR+1))-01-01T00:00:00Z"
    
    # キーワードのスラッグを生成
    local SLUG=$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
    
    # YouTube Data API 呼び出し
    RESPONSE=$(curl -s "https://www.googleapis.com/youtube/v3/search" \
      -G \
      --data-urlencode "part=snippet" \
      --data-urlencode "q=${KEYWORD}" \
      --data-urlencode "type=video" \
      --data-urlencode "maxResults=50" \
      --data-urlencode "publishedAfter=${START}" \
      --data-urlencode "publishedBefore=${END}" \
      --data-urlencode "regionCode=JP" \
      --data-urlencode "relevanceLanguage=ja" \
      --data-urlencode "key=${YOUTUBE_API_KEY}")
    
    # エラーチェック
    ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.code // empty' 2>/dev/null)
    if [ -n "$ERROR_CODE" ]; then
        echo "  エラー: ${ERROR_CODE} - $(echo "$RESPONSE" | jq -r '.error.message // empty' 2>/dev/null)"
        echo "${SLUG} ${YEAR}: ERROR ${ERROR_CODE}" >> "${SAVE_DIR}/collection_log.txt"
        return 1
    fi
    
    # 件数を取得
    COUNT=$(echo "$RESPONSE" | jq '.items | length' 2>/dev/null || echo "0")
    
    # ページネーションが必要かチェック
    PAGE_TOKEN=$(echo "$RESPONSE" | jq -r '.nextPageToken // empty' 2>/dev/null)
    
    # データを保存
    echo "$RESPONSE" > "${SAVE_DIR}/records_${SLUG}_${YEAR}.json"
    
    # クォータ消費を記録
    echo "${SLUG} ${YEAR}: ${COUNT}件" >> "${SAVE_DIR}/collection_log.txt"
    
    # ページネーションが必要な場合、追加取得
    if [ -n "$PAGE_TOKEN" ]; then
        PAGE=2
        while [ -n "$PAGE_TOKEN" ]; do
            RESPONSE_PAGE=$(curl -s "https://www.googleapis.com/youtube/v3/search" \
              -G \
              --data-urlencode "part=snippet" \
              --data-urlencode "q=${KEYWORD}" \
              --data-urlencode "type=video" \
              --data-urlencode "maxResults=50" \
              --data-urlencode "pageToken=${PAGE_TOKEN}" \
              --data-urlencode "publishedAfter=${START}" \
              --data-urlencode "publishedBefore=${END}" \
              --data-urlencode "regionCode=JP" \
              --data-urlencode "relevanceLanguage=ja" \
              --data-urlencode "key=${YOUTUBE_API_KEY}")
            
            PAGE_COUNT=$(echo "$RESPONSE_PAGE" | jq '.items | length' 2>/dev/null || echo "0")
            echo "$RESPONSE_PAGE" > "${SAVE_DIR}/records_${SLUG}_${YEAR}_page${PAGE}.json"
            
            echo "${SLUG} ${YEAR}_page${PAGE}: ${PAGE_COUNT}件" >> "${SAVE_DIR}/collection_log.txt"
            
            COUNT=$((COUNT + PAGE_COUNT))
            PAGE_TOKEN=$(echo "$RESPONSE_PAGE" | jq -r '.nextPageToken // empty' 2>/dev/null)
            PAGE=$((PAGE + 1))
            
            # API レート制限対策
            sleep 1
        done
    fi
    
    echo "  ${KEYWORD} ${YEAR}年: ${COUNT}件"
    return 0
}

# 収集実行
echo "収集開始..."
echo ""

SUCCESS_COUNT=0
ERROR_COUNT=0

for KEYWORD in "${KEYWORDS[@]}"; do
    echo "--- ${KEYWORD} ---"
    for YEAR in $(seq 2016 2025); do
        if collect_yearly "$KEYWORD" $YEAR; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
        sleep 1
    done
    echo ""
done

echo "=== 収集完了 ==="
echo "成功: ${SUCCESS_COUNT}件"
echo "エラー: ${ERROR_COUNT}件"
echo ""
echo "=== 収集ログ ==="
cat "${SAVE_DIR}/collection_log.txt"
echo ""
echo "=== メタデータ保存 ==="

# メタデータを保存
cat > "${SAVE_DIR}/run_metadata.json" << EOF
{
  "run_id": "${TIMESTAMP}-youtube-japanese-keywords-10years",
  "study_id": "${STUDY_ID}",
  "collection_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "keywords": ["CBD オイル", "カンナビノイド", "CBN オイル", "カンナビジェロール"],
  "period": "2016-01-01 to 2025-12-31",
  "region_code": "JP",
  "relevance_language": "ja",
  "success_count": ${SUCCESS_COUNT},
  "error_count": ${ERROR_COUNT},
  "source": "youtube-data-api-v3"
}
EOF

echo "メタデータを保存しました: ${SAVE_DIR}/run_metadata.json"
echo ""
echo "=== 完了日時: $(date) ==="
