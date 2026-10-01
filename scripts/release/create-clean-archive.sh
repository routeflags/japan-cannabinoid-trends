#!/bin/bash
# Create clean archive for Zenodo release
# Usage: ./scripts/release/create-clean-archive.sh [version]
# Example: ./scripts/release/create-clean-archive.sh v1.5.1

set -euo pipefail

# Determine version
if [ $# -eq 0 ]; then
  # Use latest tag or current branch
  VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --abbrev-ref HEAD)
else
  VERSION="$1"
fi

echo "=== Creating Clean Archive ==="
echo "Version: ${VERSION}"
echo ""

# Paths to include (research-relevant only)
INCLUDE_PATHS=(
  "datasets"
  "docs/specs"
  "docs/acceptance-criteria.md"
  "docs/migration-plan.md"
  "publication"
  "src"
  "metadata"
  "LICENSE"
  "CITATION.cff"
  "CHANGELOG.md"
  "README.md"
  "methodology.md"
)

# Create output directory
OUTPUT_DIR="release-archives"
mkdir -p "${OUTPUT_DIR}"

# Create clean directory
CLEAN_DIR=$(mktemp -d)
trap 'rm -rf "${CLEAN_DIR}"' EXIT

echo "Cleaning..."
for path in "${INCLUDE_PATHS[@]}"; do
  if [ -e "${path}" ]; then
    mkdir -p "${CLEAN_DIR}/$(dirname "${path}")"
    cp -r "${path}" "${CLEAN_DIR}/"
    echo "  ✓ ${path}"
  else
    echo "  - ${path} (not found, skipping)"
  fi
done

# Remove unwanted files
echo ""
echo "Removing unwanted files..."
rm -rf "${CLEAN_DIR}/.github" \
       "${CLEAN_DIR}/.serena" \
       "${CLEAN_DIR}/artifacts" \
       "${CLEAN_DIR}/.opencode" \
       "${CLEAN_DIR}/.gitignore" \
       "${CLEAN_DIR}/.env" \
       "${CLEAN_DIR}/.env.local" \
       "${CLEAN_DIR}/opencode.json" \
       "${CLEAN_DIR}/project.json" \
       "${CLEAN_DIR}/project.yml" 2>/dev/null || true

# Remove DS_Store and project.yml files
find "${CLEAN_DIR}" -name ".DS_Store" -delete 2>/dev/null || true
find "${CLEAN_DIR}" -name "*.DS_Store" -delete 2>/dev/null || true
find "${CLEAN_DIR}" -name "project.yml" -delete 2>/dev/null || true

# Create zip
ZIP_NAME="japan-cannabinoid-trends-${VERSION}-clean.zip"
ZIP_PATH="${OUTPUT_DIR}/${ZIP_NAME}"

echo ""
echo "Creating zip: ${ZIP_PATH}"
(
  cd "${CLEAN_DIR}"
  zip -r "${OLDPWD}/${ZIP_PATH}" . -x "*.DS_Store"
)

# Verify
echo ""
echo "=== Verification ==="
if unzip -l "${ZIP_PATH}" | grep -qE "\.github|\.serena|artifacts|\.opencode|agent\.md"; then
  echo "❌ ERROR: Unwanted files found in archive!"
  exit 1
fi
echo "✅ Archive is clean"

# Summary
echo ""
echo "=== Summary ==="
echo "Name: ${ZIP_NAME}"
echo "Size: $(ls -lh "${ZIP_PATH}" | awk '{print $5}')"
echo "Path: ${ZIP_PATH}"
echo ""
echo "=== Contents ==="
unzip -l "${ZIP_PATH}" | tail -20
echo ""
echo "✅ Done!"
echo ""
echo "Upload to Zenodo:"
echo "  https://zenodo.org/upload"
echo ""
echo "Or add to existing deposition:"
echo "  https://zenodo.org/deposit"
