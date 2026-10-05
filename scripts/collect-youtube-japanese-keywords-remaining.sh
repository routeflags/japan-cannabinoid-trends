#!/bin/bash
# 残りキーワード再収集スクリプト
# 対象: CBN オイル, カンナビジェロール
# 実行予定: 2026-10-06 16:30 JST

set -e

cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends

source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env

BASE_DIR="datasets/cannabinoid-multi-trends/data/raw/youtube/20261006T073000Z-youtube-japanese-keywords-remaining"
mkdir -p "$BASE_DIR"

echo "=== 日本語キーワード YouTube データ再収集開始 ==="
echo "開始日時: $(date)"
echo "保存先: $BASE_DIR"
echo "対象: CBN オイル, カンナビジェロール"
echo ""

# キーワードと年リスト
KEYWORDS=("CBN オイル" "カンナビジェロール")
YEARS=(2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

SUCCESS_COUNT=0
ERROR_COUNT=0

for KEYWORD in "${KEYWORDS[@]}"; do
  echo "--- $KEYWORD ---"
  
  KEYWORD_SLUG=$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
  KEYWORD_DIR="$BASE_DIR/$KEYWORD_SLUG"
  mkdir -p "$KEYWORD_DIR"
  
  for YEAR in "${YEARS[@]}"; do
    # クエリ構築
    QUERY="$KEYWORD since:$YEAR-01-01 until:$YEAR-12-31"
    ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")
    
    # YouTube Data API v3 search
    RESPONSE=$(curl -s "https://www.googleapis.com/youtube/v3/search?part=id&q=${ENCODED_QUERY}&maxResults=50&order=date&type=video&publishedAfter=${YEAR}-01-01T00:00:00Z&publishedBefore=${YEAR}-12-31T23:59:59Z&key=$YOUTUBE_API_KEY")
    
    # エラー確認
    ERROR=$(echo "$RESPONSE" | jq -r '.error.message // empty')
    
    if [ -n "$ERROR" ]; then
      echo "  $YEAR: ERROR - $ERROR"
      echo "$YEAR: ERROR" >> "$KEYWORD_DIR/collection.log"
      ((ERROR_COUNT++))
    else
      # 件数取得
      COUNT=$(echo "$RESPONSE" | jq '.items | length')
      echo "  $YEAR: ${COUNT}件"
      echo "$YEAR: ${COUNT}件" >> "$KEYWORD_DIR/collection.log"
      
      # データ保存
      echo "$RESPONSE" > "$KEYWORD_DIR/${YEAR}.json"
      
      ((SUCCESS_COUNT++))
    fi
    
    # クォータ消費を抑えるため待機
    sleep 2
  done
done

echo ""
echo "=== 収集完了 ==="
echo "成功: ${SUCCESS_COUNT}件"
echo "エラー: ${ERROR_COUNT}件"
echo "完了日時: $(date)"

# メタデータ保存
cat > "$BASE_DIR/run_metadata.json" << EOF
{
  "collection_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "keywords": ["CBN オイル", "カンナビジェロール"],
  "years": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  "success_count": $SUCCESS_COUNT,
  "error_count": $ERROR_COUNT,
  "note": "Residual collection for keywords that hit quota limit on 2026-10-05"
}
EOF

echo "メタデータを保存しました: $BASE_DIR/run_metadata.json"
