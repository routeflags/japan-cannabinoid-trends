#!/bin/bash
# YouTube relevanceLanguage=ja テスト
# 英語キーワード + relevanceLanguage=ja で日本語コンテンツを取得できるかテスト

set -e

cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends

source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env

SAVE_DIR="datasets/cannabinoid-multi-trends/data/raw/youtube/$(date -u +"%Y%m%dT%H%M%SZ")-youtube-relevance-language-test"
mkdir -p "$SAVE_DIR"

echo "=== relevanceLanguage=ja テスト ==="
echo "開始日時: $(date)"
echo "保存先: $SAVE_DIR"
echo ""

# テストクエリ（英語キーワード + relevanceLanguage=ja）
declare -A TEST_QUERIES=(
  ["CBD"]="CBD"
  ["CBG"]="CBG"
  ["CBN"]="CBN"
)

SUCCESS_COUNT=0
ERROR_COUNT=0

for KEYWORD in "${!TEST_QUERIES[@]}"; do
  QUERY="${TEST_QUERIES[$KEYWORD]}"
  echo "--- $QUERY (relevanceLanguage=ja) ---"
  
  # YouTube Data API v3 search with relevanceLanguage=ja
  RESPONSE=$(curl -s "https://www.googleapis.com/youtube/v3/search?part=id&q=${QUERY}&maxResults=50&order=date&type=video&regionCode=JP&relevanceLanguage=ja&key=$YOUTUBE_API_KEY")
  
  # エラー確認
  ERROR=$(echo "$RESPONSE" | jq -r '.error.message // empty')
  
  if [ -n "$ERROR" ]; then
    echo "  ERROR: $ERROR"
    ((ERROR_COUNT++))
  else
    COUNT=$(echo "$RESPONSE" | jq '.items | length')
    echo "  件数: ${COUNT}件"
    
    # 保存
    echo "$RESPONSE" > "${SAVE_DIR}/${KEYWORD}_relevance_ja.json"
    
    # 日本語コンテンツの確認（タイトルで判定）
    JAPANESE_COUNT=$(echo "$RESPONSE" | jq -r '.items[]?.id.videoId' | while read vid; do
      if [ -n "$vid" ]; then
        # タイトルを取得して日本語判定
        TITLE_RESPONSE=$(curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${vid}&key=$YOUTUBE_API_KEY")
        TITLE=$(echo "$TITLE_RESPONSE" | jq -r '.items[0].snippet.title // empty')
        if echo "$TITLE" | grep -q '[ぁ-んァ-ヶ一-龠]'; then
          echo "1"
        fi
      fi
    done | wc -l | tr -d ' ')
    
    echo "  日本語タイトル: ${JAPANESE_COUNT}件 / ${COUNT}件"
    
    ((SUCCESS_COUNT++))
  fi
  
  sleep 2
done

echo ""
echo "=== テスト結果サマリー ==="
echo "成功: ${SUCCESS_COUNT}クエリ"
echo "エラー: ${ERROR_COUNT}クエリ"
echo "完了日時: $(date)"

# メタデータ保存
cat > "${SAVE_DIR}/run_metadata.json" << EOF
{
  "run_id": "$(basename "$SAVE_DIR")",
  "test_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "purpose": "Test relevanceLanguage=ja parameter for Japanese content discovery",
  "parameters": {
    "regionCode": "JP",
    "relevanceLanguage": "ja",
    "maxResults": 50,
    "order": "date",
    "type": "video"
  },
  "success_count": $SUCCESS_COUNT,
  "error_count": $ERROR_COUNT,
  "note": "English keywords with relevanceLanguage=ja - testing if this parameter improves Japanese content yield"
}
EOF

echo ""
echo "メタデータを保存しました: ${SAVE_DIR}/run_metadata.json"
