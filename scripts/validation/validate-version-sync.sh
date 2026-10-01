#!/usr/bin/env bash
# =============================================================================
# validate-version-sync.sh
#
# バージョン/DOI 同期検証スクリプト
#
# リポジトリ内の全ファイルに記載されたバージョン番号と DOI が
# 実際のリリースと整合しているかを検証する。
#
# 使用方法:
#   bash scripts/validation/validate-version-sync.sh
#   bash scripts/validation/validate-version-sync.sh --fix
#   bash scripts/validation/validate-version-sync.sh --json
#
# 検証対象:
#   1. CITATION.cff
#   2. CHANGELOG.md
#   3. metadata/datapackage.json
#   4. methodology.md
#   5. publication/guide_cbx_rewrite.html
#   6. README.md
#   7. Git tag
# =============================================================================

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# リポジトリルート
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# フラグ
FIX_MODE=false
JSON_MODE=false

for arg in "$@"; do
  case $arg in
    --fix) FIX_MODE=true ;;
    --json) JSON_MODE=true ;;
    --help|-h)
      echo "Usage: $0 [--fix] [--json]"
      exit 0
      ;;
  esac
done

# 結果カウンター
ISSUE_COUNT=0
WARN_COUNT=0
PASS_COUNT=0

print_header() {
  echo ""
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${CYAN}  $1${NC}"
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_pass() { echo -e "  ${GREEN}✅ PASS${NC}  $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
print_fail() { echo -e "  ${RED}❌ FAIL${NC}  $1"; ISSUE_COUNT=$((ISSUE_COUNT + 1)); }
print_warn() { echo -e "  ${YELLOW}⚠️  WARN${NC}  $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
print_info() { echo -e "  ${BLUE}ℹ️  INFO${NC}  $1"; }

# =============================================================================
# 実際のリリース情報を取得
# =============================================================================

print_header "実際のリリース情報の取得"

# 最新 Git タグ
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
LATEST_TAG_VERSION="${LATEST_TAG#v}"

# GitHub Release から DOI を取得
GITHUB_DOI=""
if command -v gh &>/dev/null && [ -n "$LATEST_TAG" ]; then
  GITHUB_DOI=$(gh release view "$LATEST_TAG" --json body -q .body 2>/dev/null | grep -oE '10\.5281/zenodo\.[0-9]+' | head -1 || echo "")
fi

# Zenodo API から DOI を検索
ZENODO_DOI=""
ZENODO_VERSION=""
ZENODO_CONCEPT_DOI=""

# リポジトリ名で検索
REPO_NAME="japan-cannabinoid-trends"
ZENODO_RESULT=$(curl -s "https://zenodo.org/api/records?q=metadata.title:%22CBX+Online+Trend%22&sort=mostrecent&size=3" 2>/dev/null || echo "")

if [ -n "$ZENODO_RESULT" ]; then
  ZENODO_DOI=$(echo "$ZENODO_RESULT" | jq -r '.hits.hits[0].doi // empty' 2>/dev/null || echo "")
  ZENODO_CONCEPT_DOI=$(echo "$ZENODO_RESULT" | jq -r '.hits.hits[0].conceptdoi // empty' 2>/dev/null || echo "")
  ZENODO_VERSION=$(echo "$ZENODO_RESULT" | jq -r '.hits.hits[0].metadata.version // empty' 2>/dev/null || echo "")
  ZENODO_TITLE=$(echo "$ZENODO_RESULT" | jq -r '.hits.hits[0].metadata.title // empty' 2>/dev/null || echo "")
fi

# 基準値を決定
# 優先順位: Git タグ > Zenodo version
BASELINE_VERSION="${LATEST_TAG_VERSION:-$ZENODO_VERSION}"
BASELINE_DOI="${ZENODO_DOI:-$GITHUB_DOI}"

# v プレフィックスを正規化
BASELINE_VERSION="${BASELINE_VERSION#v}"

echo ""
echo -e "  ${BOLD}最新 Git タグ:${NC}   ${LATEST_TAG:-N/A} (v$BASELINE_VERSION)"
echo -e "  ${BOLD}Zenodo DOI:${NC}     ${ZENODO_DOI:-N/A}"
echo -e "  ${BOLD}Concept DOI:${NC}    ${ZENODO_CONCEPT_DOI:-N/A}"
echo -e "  ${BOLD}Zenodo Version:${NC} ${ZENODO_VERSION:-N/A}"
echo -e "  ${BOLD}GitHub Release:${NC} ${GITHUB_DOI:-N/A}"
echo ""
echo -e "  ${BOLD}基準バージョン:${NC} $BASELINE_VERSION"
echo -e "  ${BOLD}基準 DOI:${NC}       ${BASELINE_DOI:-N/A}"

# =============================================================================
# 1. CITATION.cff
# =============================================================================

print_header "1. CITATION.cff"

CITATION_FILE="CITATION.cff"

if [ -f "$CITATION_FILE" ]; then
  # version (値のみ抽出)
  CITATION_VERSION=$(grep -E '^version:' "$CITATION_FILE" | head -1 | awk -F'"' '{print $2}')
  if [ "$CITATION_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "version: $CITATION_VERSION"
  else
    print_fail "version: $CITATION_VERSION → $BASELINE_VERSION"
  fi

  # preferred-citation version
  PREF_VERSION=$(sed -n '/preferred-citation:/,/^[a-z]/p' "$CITATION_FILE" | grep 'version:' | awk -F'"' '{print $2}' | head -1)
  if [ "$PREF_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "preferred-citation.version: $PREF_VERSION"
  else
    print_fail "preferred-citation.version: $PREF_VERSION → $BASELINE_VERSION"
  fi

  # identifiers DOI
  CITATION_DOI=$(grep -A5 'identifiers:' "$CITATION_FILE" | grep 'value:' | head -1 | awk -F'"' '{print $2}')
  if [ -n "$BASELINE_DOI" ]; then
    if [ "$CITATION_DOI" = "$BASELINE_DOI" ]; then
      print_pass "identifiers.doi: $CITATION_DOI"
    else
      print_fail "identifiers.doi: $CITATION_DOI → $BASELINE_DOI"
    fi
  fi

  # preferred-citation DOI
  PREF_DOI=$(sed -n '/preferred-citation:/,$p' "$CITATION_FILE" | grep 'doi:' | awk -F'"' '{print $2}' | head -1)
  if [ -n "$BASELINE_DOI" ]; then
    if [ "$PREF_DOI" = "$BASELINE_DOI" ]; then
      print_pass "preferred-citation.doi: $PREF_DOI"
    else
      print_fail "preferred-citation.doi: $PREF_DOI → $BASELINE_DOI"
    fi
  fi

  # date-released
  DATE_RELEASED=$(grep -E '^date-released:' "$CITATION_FILE" | awk -F'"' '{print $2}')
  print_info "date-released: $DATE_RELEASED"
else
  print_fail "$CITATION_FILE が存在しません"
fi

# =============================================================================
# 2. CHANGELOG.md
# =============================================================================

print_header "2. CHANGELOG.md"

CHANGELOG_FILE="CHANGELOG.md"

if [ -f "$CHANGELOG_FILE" ]; then
  LATEST_CHANGELOG_VERSION=$(grep -E '^## \[' "$CHANGELOG_FILE" | head -1 | sed 's/## \[\(.*\)\].*/\1/' | tr -d ' ')
  
  if [ "$LATEST_CHANGELOG_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "最新エントリ: $LATEST_CHANGELOG_VERSION"
  else
    print_fail "最新エントリ: $LATEST_CHANGELOG_VERSION → $BASELINE_VERSION"
  fi
else
  print_fail "$CHANGELOG_FILE が存在しません"
fi

# =============================================================================
# 3. metadata/datapackage.json
# =============================================================================

print_header "3. metadata/datapackage.json"

DATAPACKAGE_FILE="metadata/datapackage.json"

if [ -f "$DATAPACKAGE_FILE" ]; then
  DP_VERSION=$(jq -r '.version // empty' "$DATAPACKAGE_FILE" 2>/dev/null || echo "")
  DP_MODIFIED=$(jq -r '.modified // empty' "$DATAPACKAGE_FILE" 2>/dev/null || echo "")
  DP_CITATION=$(jq -r '.citation // empty' "$DATAPACKAGE_FILE" 2>/dev/null || echo "")

  # version
  if [ "$DP_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "version: $DP_VERSION"
  else
    print_fail "version: $DP_VERSION → $BASELINE_VERSION"
  fi

  # citation 内の Version
  CITATION_VERSION_IN_DP=$(echo "$DP_CITATION" | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || echo "")
  if [ "$CITATION_VERSION_IN_DP" = "$BASELINE_VERSION" ]; then
    print_pass "citation 内 Version: $CITATION_VERSION_IN_DP"
  else
    print_fail "citation 内 Version: $CITATION_VERSION_IN_DP → $BASELINE_VERSION"
  fi

  # DOI (citation 内)
  DP_DOI=$(echo "$DP_CITATION" | grep -oE '10\.5281/zenodo\.[0-9]+' | head -1 || echo "")
  if [ -n "$BASELINE_DOI" ]; then
    if [ "$DP_DOI" = "$BASELINE_DOI" ]; then
      print_pass "citation DOI: $DP_DOI"
    else
      print_fail "citation DOI: $DP_DOI → $BASELINE_DOI"
    fi
  fi

  print_info "modified: $DP_MODIFIED"
else
  print_fail "$DATAPACKAGE_FILE が存在しません"
fi

# =============================================================================
# 4. methodology.md
# =============================================================================

print_header "4. methodology.md"

METHODOLOGY_FILE="methodology.md"

if [ -f "$METHODOLOGY_FILE" ]; then
  METH_VERSION=$(grep -iE '^.*version.*[0-9]+\.[0-9]+' "$METHODOLOGY_FILE" | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' || echo "")
  
  if [ -z "$METH_VERSION" ]; then
    print_warn "バージョン記載が見つかりません"
  elif [ "$METH_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "version: $METH_VERSION"
  else
    print_fail "version: $METH_VERSION → $BASELINE_VERSION"
  fi
else
  print_warn "$METHODOLOGY_FILE が存在しません"
fi

# =============================================================================
# 5. publication/guide_cbx_rewrite.html
# =============================================================================

print_header "5. publication/guide_cbx_rewrite.html"

GUIDE_FILE="publication/guide_cbx_rewrite.html"

if [ -f "$GUIDE_FILE" ]; then
  # 引用ブロックのバージョン（最後の Version 表記）
  GUIDE_VERSION=$(grep -oE 'Version\s*[0-9]+\.[0-9]+(\.[0-9]+)?' "$GUIDE_FILE" | tail -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' || echo "")
  GUIDE_DOI=$(grep -oE '10\.5281/zenodo\.[0-9]+' "$GUIDE_FILE" | tail -1 || echo "")
  GUIDE_DATE=$(grep -oE 'dateModified["\s:]+[0-9]{4}-[0-9]{2}-[0-9]{2}' "$GUIDE_FILE" | head -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "")

  if [ "$GUIDE_VERSION" = "$BASELINE_VERSION" ]; then
    print_pass "引用 Version: $GUIDE_VERSION"
  else
    print_fail "引用 Version: $GUIDE_VERSION → $BASELINE_VERSION"
  fi

  if [ -n "$BASELINE_DOI" ]; then
    if [ "$GUIDE_DOI" = "$BASELINE_DOI" ]; then
      print_pass "引用 DOI: $GUIDE_DOI"
    else
      print_fail "引用 DOI: $GUIDE_DOI → $BASELINE_DOI"
    fi
  fi

  print_info "dateModified: $GUIDE_DATE"
else
  print_fail "$GUIDE_FILE が存在しません"
fi

# =============================================================================
# 6. README.md
# =============================================================================

print_header "6. README.md"

README_FILE="README.md"

if [ -f "$README_FILE" ]; then
  README_DOI=$(grep -oE '10\.5281/zenodo\.[0-9]+' "$README_FILE" | head -1 || echo "")
  
  if [ -n "$BASELINE_DOI" ]; then
    if [ "$README_DOI" = "$BASELINE_DOI" ]; then
      print_pass "DOI バッジ: $README_DOI"
    else
      print_fail "DOI バッジ: $README_DOI → $BASELINE_DOI"
    fi
  else
    print_warn "DOI バッジ: $README_DOI (基準 DOI 未特定)"
  fi
else
  print_fail "$README_FILE が存在しません"
fi

# =============================================================================
# 7. Git タグ
# =============================================================================

print_header "7. Git タグ"

print_info "最新タグ: ${LATEST_TAG:-N/A}"
print_info "タグ数: $(git tag -l 'v*' | wc -l | tr -d ' ')"

# リモートタグ
REMOTE_TAG_COUNT=$(git ls-remote --tags origin 2>/dev/null | grep -c 'refs/tags/v' || echo "0")
LOCAL_TAG_COUNT=$(git tag -l 'v*' | wc -l | tr -d ' ')
print_info "ローカル: $LOCAL_TAG_COUNT / リモート: $REMOTE_TAG_COUNT"

if [ "$LOCAL_TAG_COUNT" != "$REMOTE_TAG_COUNT" ]; then
  print_warn "タグ数がローカルとリモートで異なります"
else
  print_pass "タグ数がローカルとリモートで一致"
fi

# =============================================================================
# サマリー
# =============================================================================

print_header "検証サマリー"

echo ""
echo -e "  ${GREEN}✅ PASS: $PASS_COUNT${NC}"
echo -e "  ${YELLOW}⚠️  WARN: $WARN_COUNT${NC}"
echo -e "  ${RED}❌ FAIL: $ISSUE_COUNT${NC}"
echo ""

# 終了コード
if [ "$ISSUE_COUNT" -gt 0 ]; then
  echo -e "${RED}${BOLD}⚠️  バージョン/DOI の不整合が $ISSUE_COUNT 件あります${NC}"
  echo ""
  exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
  echo -e "${YELLOW}${BOLD}⚠️  警告が $WARN_COUNT 件あります${NC}"
  echo ""
  exit 0
else
  echo -e "${GREEN}${BOLD}✅ すべてのバージョン/DOI が同期されています${NC}"
  echo ""
  exit 0
fi
