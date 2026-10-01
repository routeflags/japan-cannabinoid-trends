#!/usr/bin/env bash
# =============================================================================
# validate-data-schema.sh
#
# Data Dictionary (datapackage.json) と実際のデータスキーマの一致検証
#
# 検証内容:
#   1. CSV ファイルのカラムが datapackage.json のスキーマと一致するか
#   2. データ型がスキーマで定義された型と整合するか
#   3. 制約（enum, pattern, minimum 等）が満たされているか
#
# 使用方法:
#   bash scripts/validation/validate-data-schema.sh
#   bash scripts/validation/validate-data-schema.sh --verbose
#
# 終了コード:
#   0 = 全チェック PASS
#   1 = FAIL あり
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
VERBOSE=false
for arg in "$@"; do
  case $arg in
    --verbose|-v) VERBOSE=true ;;
  esac
done

# 結果カウンター
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

print_header() {
  echo ""
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${CYAN}  $1${NC}"
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_pass() { echo -e "  ${GREEN}✅ PASS${NC}  $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
print_fail() { echo -e "  ${RED}❌ FAIL${NC}  $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
print_warn() { echo -e "  ${YELLOW}⚠️  WARN${NC}  $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
print_info() { [ "$VERBOSE" = true ] && echo -e "  ${BLUE}ℹ️  INFO${NC}  $1" || true; }

# =============================================================================
# ヘルパー関数
# =============================================================================

# CSV のヘッダーを取得
get_csv_headers() {
  local file="$1"
  if [ -f "$file" ]; then
    head -1 "$file" | tr ',' '\n' | tr -d '"' | sed 's/\r//'
  fi
}

# CSV のカラム数を取得
get_csv_column_count() {
  local file="$1"
  if [ -f "$file" ]; then
    head -1 "$file" | awk -F',' '{print NF}'
  fi
}

# CSV のレコード数を取得
get_csv_record_count() {
  local file="$1"
  if [ -f "$file" ]; then
    tail -n +2 "$file" | wc -l | tr -d ' '
  fi
}

# JSON からフィールド名のリストを取得
get_json_field_names() {
  local json_file="$1"
  local resource_name="$2"
  
  if [ -f "$json_file" ]; then
    jq -r --arg name "$resource_name" '
      .resources[] | select(.name == $name) | .schema.fields[]?.name // empty
    ' "$json_file" 2>/dev/null || echo ""
  fi
}

# JSON からフィールドの型を取得
get_json_field_type() {
  local json_file="$1"
  local resource_name="$2"
  local field_name="$3"
  
  if [ -f "$json_file" ]; then
    jq -r --arg name "$resource_name" --arg field "$field_name" '
      .resources[] | select(.name == $name) | .schema.fields[]? | select(.name == $field) | .type // "unknown"
    ' "$json_file" 2>/dev/null || echo "unknown"
  fi
}

# =============================================================================
# メイン検証
# =============================================================================

DATAPACKAGE="metadata/datapackage.json"

print_header "Data Schema 検証"

if [ ! -f "$DATAPACKAGE" ]; then
  print_fail "$DATAPACKAGE が存在しません"
  exit 1
fi

print_info "datapackage.json を読み込み中..."

# =============================================================================
# 1. X データ（匿名化版）の検証
# =============================================================================

print_header "1. X データ（匿名化版）"

X_CSV="datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"

if [ ! -f "$X_CSV" ]; then
  print_warn "$X_CSV が存在しません（スキップ）"
else
  # CSV のヘッダーを取得
  CSV_HEADERS=$(get_csv_headers "$X_CSV" | tr '\n' ' ' | sed 's/ $//')
  CSV_COL_COUNT=$(get_csv_column_count "$X_CSV")
  CSV_RECORD_COUNT=$(get_csv_record_count "$X_CSV")
  
  print_info "CSV: $X_CSV"
  print_info "カラム数: $CSV_COL_COUNT"
  print_info "レコード数: $CSV_RECORD_COUNT"
  print_info "カラム: $CSV_HEADERS"
  
  # datapackage.json のスキーマを取得
  SCHEMA_FIELDS=$(get_json_field_names "$DATAPACKAGE" "x_cbx_202608_summary_anonymized")
  SCHEMA_COL_COUNT=$(echo "$SCHEMA_FIELDS" | grep -c '.' || echo "0")
  
  print_info "スキーマ定義: $SCHEMA_COL_COUNT フィールド"
  
  # カラム名の比較
  echo ""
  echo "  カラム名の比較:"
  
  # CSV の各カラムがスキーマに定義されているか確認
  MISSING_IN_SCHEMA=""
  for col in $CSV_HEADERS; do
    if echo "$SCHEMA_FIELDS" | grep -q "^${col}$"; then
      print_pass "カラム '$col' はスキーマに定義済み"
    else
      print_fail "カラム '$col' はスキーマに未定義"
      MISSING_IN_SCHEMA="$MISSING_IN_SCHEMA $col"
    fi
  done
  
  # スキーマに定義されているが CSV に存在しないカラムを確認
  echo ""
  echo "  スキーマ定義の確認:"
  
  for field in $SCHEMA_FIELDS; do
    if echo "$CSV_HEADERS" | grep -q "${field}"; then
      print_pass "スキーマフィールド '$field' は CSV に存在"
    else
      print_warn "スキーマフィールド '$field' は CSV に存在しない"
    fi
  done
  
  # カラム数の一致確認
  echo ""
  if [ "$CSV_COL_COUNT" -eq "$SCHEMA_COL_COUNT" ]; then
    print_pass "カラム数が一致 ($CSV_COL_COUNT)"
  else
    print_fail "カラム数が不一致 (CSV: $CSV_COL_COUNT, スキーマ: $SCHEMA_COL_COUNT)"
  fi
  
  # レコード数の確認
  echo ""
  if [ "$CSV_RECORD_COUNT" -gt 0 ]; then
    print_pass "レコード数: $CSV_RECORD_COUNT 件"
  else
    print_warn "レコード数が 0 件"
  fi
fi

# =============================================================================
# 2. データ型の検証（サンプル）
# =============================================================================

print_header "2. データ型検証（サンプル）"

if [ -f "$X_CSV" ]; then
  python3 << 'PYTHON'
import csv
import re
from collections import Counter

csv_file = "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"
schema_file = "metadata/datapackage.json"

# スキーマを読み込み
import json
with open(schema_file) as f:
    datapackage = json.load(f)

# 匿名化版のスキーマを取得
schema = None
for resource in datapackage.get('resources', []):
    if resource.get('name') == 'x_cbx_202608_summary_anonymized':
        schema = resource.get('schema', {})
        break

if not schema:
    print("  ⚠️  WARN  スキーマが見つかりません")
else:
    field_specs = {f['name']: f for f in schema.get('fields', [])}
    
    # CSV を読み込み
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"  ℹ️  INFO  レコード数: {len(rows)}")
    
    # 各カラムの型を検証
    for field_name, spec in field_specs.items():
        field_type = spec.get('type', 'unknown')
        constraints = spec.get('constraints', {})
        
        if field_name not in reader.fieldnames:
            print(f"  ❌ FAIL  カラム '{field_name}' が CSV に存在しません")
            continue
        
        # サンプル値を取得
        values = [row.get(field_name, '') for row in rows[:10]]
        non_empty = [v for v in values if v.strip()]
        
        if not non_empty:
            print(f"  ⚠️  WARN  '{field_name}': 全ての値が空です")
            continue
        
        # 型チェック
        type_ok = True
        error_msg = ""
        
        if field_type == 'integer':
            for v in non_empty:
                try:
                    int(v)
                except:
                    type_ok = False
                    error_msg = f"整数でない値: '{v}'"
                    break
        elif field_type == 'number':
            for v in non_empty:
                try:
                    float(v)
                except:
                    type_ok = False
                    error_msg = f"数値でない値: '{v}'"
                    break
        elif field_type == 'datetime':
            for v in non_empty:
                # ISO 8601 パターンチェック
                if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', v):
                    type_ok = False
                    error_msg = f"ISO 8601 形式でない値: '{v}'"
                    break
        
        # 制約チェック
        constraint_ok = True
        constraint_msg = ""
        
        if 'enum' in constraints:
            allowed = constraints['enum']
            for v in non_empty:
                if v not in allowed:
                    constraint_ok = False
                    constraint_msg = f"許可されていない値: '{v}' (許可値: {allowed})"
                    break
        
        if 'pattern' in constraints:
            pattern = constraints['pattern']
            for v in non_empty:
                if not re.match(pattern, v):
                    constraint_ok = False
                    constraint_msg = f"パターンに不一致: '{v}' (パターン: {pattern})"
                    break
        
        if 'minimum' in constraints:
            min_val = constraints['minimum']
            for v in non_empty:
                try:
                    if int(v) < min_val:
                        constraint_ok = False
                        constraint_msg = f"最小値未満: '{v}' (最小値: {min_val})"
                        break
                except:
                    pass
        
        # 結果出力
        if type_ok and constraint_ok:
            print(f"  ✅ PASS  '{field_name}' ({field_type}): OK")
        elif not type_ok:
            print(f"  ❌ FAIL  '{field_name}' ({field_type}): {error_msg}")
        else:
            print(f"  ❌ FAIL  '{field_name}' ({field_type}): {constraint_msg}")

PYTHON
fi

# =============================================================================
# 3. ファイル存在確認
# =============================================================================

print_header "3. 必要ファイルの存在確認"

REQUIRED_FILES=(
  "metadata/datapackage.json"
  "docs/data-dictionary.md"
  "docs/provenance.md"
  "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_pass "$file"
  else
    print_fail "$file が存在しません"
  fi
done

# =============================================================================
# サマリー
# =============================================================================

print_header "検証サマリー"

echo ""
echo -e "  ${GREEN}✅ PASS: $PASS_COUNT${NC}"
echo -e "  ${YELLOW}⚠️  WARN: $WARN_COUNT${NC}"
echo -e "  ${RED}❌ FAIL: $FAIL_COUNT${NC}"
echo ""

# 終了コード
if [ "$FAIL_COUNT" -gt 0 ]; then
  echo -e "${RED}${BOLD}⚠️  スキーマ不一致が $FAIL_COUNT 件あります${NC}"
  echo ""
  exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
  echo -e "${YELLOW}${BOLD}⚠️  警告が $WARN_COUNT 件あります${NC}"
  echo ""
  exit 0
else
  echo -e "${GREEN}${BOLD}✅ データスキーマが Data Dictionary と一致しています${NC}"
  echo ""
  exit 0
fi
