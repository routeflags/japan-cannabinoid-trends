#!/usr/bin/env bash
# =============================================================================
# export-taxonomy.sh
#
# SKOS タクソノミーを各種形式にエクスポートする統合スクリプト
#
# 出力形式:
#   - RDF/Turtle (.ttl)
#   - Schema.org JSON-LD (.schema.jsonld)
#
# 使用方法:
#   bash scripts/export/export-taxonomy.sh
#   bash scripts/export/export-taxonomy.sh --output-dir ./exports
#
# =============================================================================

set -euo pipefail

# リポジトリルート
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# 出力先
OUTPUT_DIR="${REPO_ROOT}/exports/taxonomy"

# 引数解析
while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir|-o)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--output-dir <dir>]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# 出力先ディレクトリ作成
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SKOS Taxonomy Export"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Output directory: $OUTPUT_DIR"
echo ""

# SKOS ファイルを検索
TAXONOMY_DIR="${REPO_ROOT}/metadata/taxonomy"
TAXONOMY_FILES=$(find "$TAXONOMY_DIR" -name "*.skos.jsonld" 2>/dev/null || true)

if [ -z "$TAXONOMY_FILES" ]; then
  echo "  ❌ No .skos.jsonld files found in metadata/taxonomy/"
  exit 1
fi

# 各ファイルをエクスポート
for TAXONOMY_FILE in $TAXONOMY_FILES; do
  FILENAME=$(basename "$TAXONOMY_FILE" .skos.jsonld)
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Processing: $FILENAME"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  
  # 1. RDF/Turtle エクスポート
  TTL_OUTPUT="${OUTPUT_DIR}/${FILENAME}.ttl"
  echo "  [1/2] Exporting to RDF/Turtle..."
  python3 scripts/export/skos-to-rdf.py "$TAXONOMY_FILE" "$TTL_OUTPUT"
  
  # 2. Schema.org JSON-LD エクスポート
  SCHEMA_OUTPUT="${OUTPUT_DIR}/${FILENAME}.schema.jsonld"
  echo "  [2/2] Exporting to Schema.org JSON-LD..."
  python3 scripts/export/skos-to-schema-jsonld.py "$TAXONOMY_FILE" "$SCHEMA_OUTPUT"
  
  echo ""
done

# IPTC マッピングもコピー
IPTC_MAPPING="${TAXONOMY_DIR}/iptc-mapping.yaml"
if [ -f "$IPTC_MAPPING" ]; then
  cp "$IPTC_MAPPING" "$OUTPUT_DIR/"
  echo "  Copied: iptc-mapping.yaml"
fi

# 分類ルールもコピー
CLASSIFICATION_RULES="${TAXONOMY_DIR}/classification-rules.yaml"
if [ -f "$CLASSIFICATION_RULES" ]; then
  cp "$CLASSIFICATION_RULES" "$OUTPUT_DIR/"
  echo "  Copied: classification-rules.yaml"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Export Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Output files:"
ls -la "$OUTPUT_DIR" | grep -E "\.(ttl|jsonld|yaml)$" | awk '{print "    " $NF}'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
