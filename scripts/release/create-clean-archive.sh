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

# Paths to include (research-relevant only; tests + pyproject.toml are
# included so the released dataset can reproduce the validation framework
# described in docs/specs/validation-framework.md, see P7-4).
#
# The release is Study-scoped: it carries cannabinoid-platform-trends (the
# processed release tables) and cannabinoid-raw-collection (tracked Google
# Trends raw plus the study metadata a reader needs to trace it).  Legacy X
# study outputs stay out because X is outside the release scope.
#
# The copy is built from the Git index, not the working tree: a checkout may
# hold git_untracked raw payloads (YouTube / social), and those must never
# reach a release archive (docs/specs/raw-data-policy.md §7.1).
INCLUDE_PATHS=(
  "datasets/cannabinoid-platform-trends"
  "datasets/cannabinoid-raw-collection"
  "docs/audits/gt-summary.json"
  "docs/specs"
  "docs/acceptance-criteria.md"
  "docs/migration-plan.md"
  "publication"
  "src"
  "tests"
  "pyproject.toml"
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

echo "Cleaning (Git index only)..."
# git ls-files is the source of truth: tracked files are repository-retained,
# untracked raw is local-only, and the index cannot contain a secret that was
# never added.  This is what keeps a developer checkout with local YouTube raw
# from producing an archive that redistributes it.
TRACKED_COUNT=0
while IFS= read -r -d '' file; do
  mkdir -p "${CLEAN_DIR}/$(dirname "${file}")"
  cp "${file}" "${CLEAN_DIR}/${file}"
  TRACKED_COUNT=$((TRACKED_COUNT + 1))
done < <(git ls-files -z -- "${INCLUDE_PATHS[@]}")

echo "  ✓ ${TRACKED_COUNT} tracked file(s)"
for path in "${INCLUDE_PATHS[@]}"; do
  if [ -z "$(git ls-files -- "${path}")" ]; then
    echo "  - ${path} (no tracked files, skipping)"
  fi
done

# Verify the include roots contributed something and that no raw payload
# outside the tracked Google Trends exception came along.
if [ "${TRACKED_COUNT}" -eq 0 ]; then
  echo "❌ ERROR: no tracked files matched INCLUDE_PATHS"
  exit 1
fi

# Remove unwanted files
# Tracked-only copying already keeps .github / .env / raw social payloads out;
# these removals stay as a second line of defence for tracked-but-unwanted
# paths (e.g. a project.yml that was added by mistake).
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

# Remove Python build caches (must not ship in the release archive)
find "${CLEAN_DIR}" -type d \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \) -prune -exec rm -rf {} + 2>/dev/null || true

# Create zip
ZIP_NAME="japan-cannabinoid-trends-${VERSION}-clean.zip"
ZIP_PATH="${OUTPUT_DIR}/${ZIP_NAME}"

echo ""
echo "Creating zip: ${ZIP_PATH}"
# Start from a clean file: `zip -r` updates an existing archive in place, so a
# stale entry from an earlier run would survive a removed include path.
rm -f "${ZIP_PATH}"
(
  cd "${CLEAN_DIR}"
  zip -r "${OLDPWD}/${ZIP_PATH}" . -x "*.DS_Store"
)

# Verify
echo ""
echo "=== Verification ==="
# Check path names only.  Do not match legitimate nested paths such as
# metadata/artifacts/ or tests/*artifact*.py.
if unzip -Z1 "${ZIP_PATH}" | grep -qE '^(\.github|\.serena|artifacts|\.opencode|\.env|\.env\.local|opencode\.json|project\.json|project\.yml)(/|$)|(^|/)agent\.md$'; then
  echo "❌ ERROR: Unwanted files found in archive!"
  exit 1
fi
# Raw payloads may only ship from the tracked Google Trends exception
# (docs/specs/raw-data-policy.md §4.1 / §7.1).  Directory entries end with "/"
# and carry no payload.
if unzip -Z1 "${ZIP_PATH}" | grep -vE '/$' | grep -E '(^|/)data/raw/' | grep -vE '(^|/)data/raw/(google_trends/|\.gitkeep$)'; then
  echo "❌ ERROR: raw payload outside the tracked Google Trends exception!"
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
