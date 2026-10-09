#!/usr/bin/env bash
# =============================================================================
# Search Emergence Tracker Validator
#
# Search Emergence Tracker が最新の情報と整合しているかを検証:
# 1. 化合物カバレッジ（project.json と一致するか）
# 2. 規制情報の鮮度（規制レポートとの整合）
# 3. 公開日と最終更新日の確認
#
# 使用方法:
#   bash scripts/validation/validate-search-emergence-tracker.sh
#
# 検証をスキップする場合:
#   git commit --no-verify
# =============================================================================

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

INDEX_DIR="publication/search-emergence-tracker"
INDEX_FILE="${INDEX_DIR}/index.html"
PROJECT_FILE="project.json"
REG_DIR="research/regulatory-status"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "  Search Emergence Tracker Validator"
echo "======================================================================"
echo ""

# Check if index file exists
if [ ! -f "$INDEX_FILE" ]; then
    echo -e "${RED}❌ FAIL${NC}: index.html が存在しません"
    exit 1
fi

# ========================================================================
# 1. Compound Coverage Check
# ========================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  1. 化合物カバレッジ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get compounds from project.json
PROJECT_COMPOUNDS=$(python3 -c "
import json
data = json.load(open('$PROJECT_FILE'))
compounds = list(data.get('queryDesign', {}).get('compounds', {}).keys())
# Add CBX if not in compounds
if 'CBX' not in compounds:
    compounds.append('CBX')
print(' '.join(compounds))
" 2>/dev/null || echo "")

# Get compounds from index
INDEX_COMPOUNDS=$(python3 -c "
import re
with open('$INDEX_FILE', 'r') as f:
    content = f.read()
# Find compound names in the HTML
compounds = set()
for c in ['CBD', 'THC', 'CBG', 'CBN', 'THCV', 'THCH', 'HHC', 'THC-O', 'H4CBH', 'HHBD', 'HHCH', 'CRDP', 'CRDH']:
    if c in content:
        compounds.add(c)
print(' '.join(sorted(compounds)))
" 2>/dev/null || echo "")

echo "  project.json の化合物: $(echo $PROJECT_COMPOUNDS | wc -w | xargs) 個"
echo "  index.html の化合物:   $(echo $INDEX_COMPOUNDS | wc -w | xargs) 個"

# Check for missing compounds
MISSING_COMPOUNDS=""
for compound in $PROJECT_COMPOUNDS; do
    if ! echo "$INDEX_COMPOUNDS" | grep -q "$compound"; then
        MISSING_COMPOUNDS="$MISSING_COMPOUNDS $compound"
    fi
done

if [ -n "$MISSING_COMPOUNDS" ]; then
    echo -e "  ${RED}❌ FAIL${NC}: index.html に未収載の化合物:${MISSING_COMPOUNDS}"
    COVERAGE_FAIL=true
else
    echo -e "  ${GREEN}✅ PASS${NC}: 全化合物が収載されています"
    COVERAGE_FAIL=false
fi

# ========================================================================
# 2. Regulatory Status Check
# ========================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  2. 規制情報の鮮度${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check regulatory status date in index
REG_DATE=$(grep -o 'as of [0-9-]*\|2026-[0-9]*-[0-9]*' "$INDEX_FILE" | head -1 | grep -o '2026-[0-9]*-[0-9]*' || echo "unknown")
echo "  index.html の規制情報日付: $REG_DATE"

# Check THCV status (should be 指定薬物)
if grep -q "THCV.*非規制\|THCV.*unregulated" "$INDEX_FILE" 2>/dev/null; then
    echo -e "  ${RED}❌ FAIL${NC}: THCV の規制状況が古い（非規制と記載）"
    REG_FAIL=true
elif grep -q "THCV.*指定薬物\|THCV.*scheduled" "$INDEX_FILE" 2>/dev/null; then
    echo -e "  ${GREEN}✅ PASS${NC}: THCV の規制状況は正しい（指定薬物）"
    REG_FAIL=false
else
    echo -e "  ${YELLOW}⚠️ WARN${NC}: THCV の規制状況を確認できませんでした"
    REG_FAIL=false
fi

# Check CBX status (should be 条件付き合法)
if grep -q "CBX" "$INDEX_FILE" 2>/dev/null; then
    echo -e "  ${GREEN}✅ PASS${NC}: CBX が収載されています"
else
    echo -e "  ${YELLOW}⚠️ WARN${NC}: CBX が未収載です"
fi

# ========================================================================
# 3. Publication Date Check
# ========================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  3. 公開日と更新日${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PUB_DATE=$(grep -o '"datePublished": "[^"]*"' "$INDEX_FILE" | head -1 | cut -d'"' -f4)
echo "  公開日: $PUB_DATE"

# Get file modification date
MOD_DATE=$(stat -f "%Sm" -t "%Y-%m-%d" "$INDEX_FILE" 2>/dev/null || stat -c "%y" "$INDEX_FILE" 2>/dev/null | cut -d' ' -f1)
echo "  ファイル更新日: $MOD_DATE"

# Check if index is older than latest data
LATEST_DATA_DATE=$(find datasets/ -name "*.json" -type f -newer "$INDEX_FILE" 2>/dev/null | head -1 | xargs stat -f "%Sm" -t "%Y-%m-%d" 2>/dev/null || echo "")

if [ -n "$LATEST_DATA_DATE" ]; then
    echo -e "  ${YELLOW}⚠️ WARN${NC}: 最新データ（$LATEST_DATA_DATE）が index.html より新しい"
    DATE_WARN=true
else
    echo -e "  ${GREEN}✅ PASS${NC}: index.html は最新データより新しい"
    DATE_WARN=false
fi

# ========================================================================
# Summary
# ========================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  検証サマリー${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

FAIL_COUNT=0
WARN_COUNT=0

if [ "$COVERAGE_FAIL" = true ]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

if [ "$REG_FAIL" = true ]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

if [ "$DATE_WARN" = true ]; then
    WARN_COUNT=$((WARN_COUNT + 1))
fi

echo ""
echo -e "  ${GREEN}✅ PASS${NC}: $((3 - FAIL_COUNT - WARN_COUNT))"
if [ $WARN_COUNT -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️ WARN${NC}: $WARN_COUNT"
fi
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "  ${RED}❌ FAIL${NC}: $FAIL_COUNT"
fi

echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ❌ Search Emergence Tracker が最新ではありません${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
else
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ Search Emergence Tracker は最新です${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
fi
