#!/usr/bin/env bash
# =============================================================================
# validate-data-schema.sh
#
# Data Dictionary (datapackage.json) と実際のデータスキーマの一致検証
# SKOS タクソノミーの準拠検証
#
# 検証内容:
#   1. CSV ファイルのカラムが datapackage.json のスキーマと一致するか
#   2. データ型がスキーマで定義された型と整合するか
#   3. 制約（enum, pattern, minimum 等）が満たされているか
#   4. SKOS タクソノミーファイルの存在と内容
#   5. 分類フィールドの Concept ID がタクソノミーと一致するか
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
# 1. X 投稿単位データ（匿名化後も公開しない: 2026-10-15 の決定）
# =============================================================================

print_header "1. X 投稿単位データ（公開しない）"

X_CSV="datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"

# 2026-10-15 の決定（ISS-20261015-COL-030 §4.1、施行は ISS-20261015-XID-034）で、
# 投稿単位の X データは**匿名化後も公開しない**。成果物（147 行 = 147 投稿）は
# 取り下げ済み（src/processing/reproduce.py の WITHDRAWN、ISS-20261015-PUB-035）なので、
# ここでは「追跡下に無いこと」を検査する。列セットによる構造の判定は
# src/validation/x_identity.py の per_post_dataset が担当する（規則を二重実装しない）。
if git ls-files --error-unmatch -- "$X_CSV" >/dev/null 2>&1; then
  print_fail "$X_CSV が追跡下にあります（投稿単位 X データは公開しない）"
elif [ -f "$X_CSV" ]; then
  print_warn "$X_CSV は作業ツリーにありますが追跡されていません（公開対象ではない）"
else
  print_pass "X 投稿単位 CSV は取り下げ済み（${X_CSV}）"
fi

# =============================================================================
# 3. SKOS タクソノミー検証
# =============================================================================

print_header "3. SKOS タクソノミー検証"

# SKOS ファイルの存在確認
SKOS_FILES=(
  "metadata/taxonomy/content-taxonomy.skos.jsonld"
  "metadata/taxonomy/compound-taxonomy.skos.jsonld"
  "metadata/taxonomy/iptc-mapping.yaml"
  "metadata/taxonomy/classification-rules.yaml"
  "metadata/schema/socialmediaposting.jsonld"
)

for file in "${SKOS_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_pass "$file"
  else
    print_fail "$file が存在しません"
  fi
done

# SKOS ファイルの内容検証
echo ""
echo "  SKOS コンテンツ検証:"

for skos_file in "metadata/taxonomy/content-taxonomy.skos.jsonld" "metadata/taxonomy/compound-taxonomy.skos.jsonld"; do
  if [ -f "$skos_file" ]; then
    python3 << PYTHON
import json

with open("$skos_file") as f:
    data = json.load(f)

filename = "$skos_file"
graph = data.get('@graph', [])
context = data.get('@context', {})

# ConceptScheme の確認
schemes = [item for item in graph if item.get('@type') == 'skos:ConceptScheme']
concepts = [item for item in graph if item.get('@type') == 'skos:Concept']

if schemes:
    print(f"  ✅ PASS  {filename}: ConceptScheme {len(schemes)}件")
else:
    print(f"  ❌ FAIL  {filename}: ConceptScheme が見つかりません")

if concepts:
    print(f"  ✅ PASS  {filename}: Concept {len(concepts)}件")
else:
    print(f"  ❌ FAIL  {filename}: Concept が見つかりません")

# 各 Concept の必須プロパティを確認
required_props = ['skos:prefLabel', 'skos:notation']
missing_props = []

for concept in concepts:
    concept_id = concept.get('@id', 'unknown')
    for prop in required_props:
        if prop not in concept:
            missing_props.append(f"{concept_id}: {prop}")

if missing_props:
    print(f"  ⚠️  WARN  {filename}: 必須プロパティ欠落 {len(missing_props)}件")
    for mp in missing_props[:3]:
        print(f"         {mp}")
else:
    print(f"  ✅ PASS  {filename}: 全 Concept に必須プロパティあり")

# inScheme の確認
concepts_without_scheme = []
for concept in concepts:
    if 'skos:inScheme' not in concept:
        concepts_without_scheme.append(concept.get('@id', 'unknown'))

if concepts_without_scheme:
    print(f"  ⚠️  WARN  {filename}: inScheme 未定義 Concept {len(concepts_without_scheme)}件")
else:
    print(f"  ✅ PASS  {filename}: 全 Concept に inScheme あり")

PYTHON
  fi
done


# =============================================================================
# 4. ファイル存在確認
# =============================================================================

print_header "4. 必要ファイルの存在確認"

REQUIRED_FILES=(
  "metadata/datapackage.json"
  "docs/data-dictionary.md"
  "docs/provenance.md"
  "metadata/taxonomy/content-taxonomy.skos.jsonld"
  "metadata/taxonomy/compound-taxonomy.skos.jsonld"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_pass "$file"
  else
    print_fail "$file が存在しません"
  fi
done

# =============================================================================
# 5. SQLite DB 整合性（trends.db）
# =============================================================================

print_header "5. SQLite DB 整合性"

validate_trend_db() {
  local db="$1" label="$2"
  local idcol="$3" mcol="$4" reltable="$5"

  if [ ! -f "$db" ]; then
    print_warn "$label: DB が存在しません ($db)"
    return
  fi

  # unique_count と 実際のリレーション件数の一致
  # （record_count は raw 件数＝重複込み。run_videos はユニークのみなので
  #   一致するのは unique_count の側）
  local mismatch
  mismatch=$(sqlite3 "$db" "
    SELECT COUNT(*) FROM (
      SELECT r.run_id
      FROM runs r
      LEFT JOIN $reltable x ON x.run_id = r.run_id
      GROUP BY r.run_id, r.unique_count
      HAVING COALESCE(COUNT(x.$idcol), 0) != COALESCE(r.unique_count, -1)
    );" 2>/dev/null)
  if [ "$mismatch" = "0" ]; then
    print_pass "$label: runs.record_count が実リレーション件数と一致"
  else
    print_fail "$label: runs.record_count と実件数が不一致 ($mismatch run)"
  fi

  # ダングリング参照（runs に存在しない run_id）
  local dangling
  dangling=$(sqlite3 "$db" "
    SELECT COUNT(*) FROM $reltable x
    WHERE x.run_id NOT IN (SELECT run_id FROM runs);" 2>/dev/null)
  if [ "$dangling" = "0" ]; then
    print_pass "$label: ダングリング run_id なし"
  else
    print_fail "$label: 存在しない run_id への参照が $dangling 件"
  fi

  # マスタ側の初出 run 参照
  local orphan
  orphan=$(sqlite3 "$db" "
    SELECT COUNT(*) FROM $mcol m
    WHERE m.first_seen_run IS NOT NULL
      AND m.first_seen_run NOT IN (SELECT run_id FROM runs);" 2>/dev/null)
  if [ "$orphan" = "0" ]; then
    print_pass "$label: first_seen_run の参照整合 OK"
  else
    print_fail "$label: first_seen_run の dangling が $orphan 件"
  fi

  # 日付形式（ISO 8601）
  local bad_date
  bad_date=$(sqlite3 "$db" "
    SELECT COUNT(*) FROM $mcol
    WHERE $({ [ "$mcol" = "videos" ] && echo "published_at" || echo "created_at"; }) IS NOT NULL
      AND NOT $({ [ "$mcol" = "videos" ] && echo "published_at" || echo "created_at"; }) GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*';" 2>/dev/null)
  if [ "$bad_date" = "0" ]; then
    print_pass "$label: 日付形式が ISO 8601"
  else
    print_fail "$label: 日付形式が不正な行が $bad_date 件"
  fi
}

validate_trend_db "datasets/youtube-consistency/data/trends.db" "YouTube" "video_id" "videos" "run_videos"
validate_trend_db "datasets/x-consistency/data/trends.db" "X" "post_id" "posts" "run_posts"

# URL 整合（video_id が URL に含まれるか）
# Apify は &list= / &t= 等のパラメータ付き URL を返すため厳密一致は求めない
YT_DB="datasets/youtube-consistency/data/trends.db"
if [ -f "$YT_DB" ]; then
  BAD_URL=$(sqlite3 "$YT_DB" "
    SELECT COUNT(*) FROM videos
    WHERE url IS NOT NULL
      AND instr(url, video_id) = 0;" 2>/dev/null)
  if [ "$BAD_URL" = "0" ]; then
    print_pass "YouTube: url に video_id が含まれる"
  else
    print_fail "YouTube: url に video_id が含まれない行が $BAD_URL 件"
  fi
fi

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
