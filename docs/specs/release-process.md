# Release Process Guide

**Purpose:** Guide for creating releases with clean archives for Zenodo DOI registration
**Date:** 2026-10-02

---

## Overview

This document describes the release process for creating clean archives suitable for Zenodo DOI registration. Clean archives exclude development files (`.github`, `.serena`, `artifacts/`, etc.) that are not relevant for research citation.

---

## Why Clean Archives?

GitHub's automatic release archives include all tracked files, including:

| Included (GitHub) | Excluded (Clean) | Reason |
|-------------------|------------------|--------|
| `.github/` | ✗ | CI/CD configs, AI agents, skills |
| `.serena/` | ✗ | IDE configuration |
| `artifacts/` | ✗ | Daily logs |
| `.opencode` | ✗ | Tool symlink |
| `datasets/` | ✓ | Research data |
| `docs/specs/` | ✓ | Methodology & policies |
| `publication/` | ✓ | Guide pages |
| `src/` | ✓ | Collection & processing code |

---

## Methods

### Method 1: Manual Script (Recommended for single releases)

```bash
# Create clean archive for current version
./scripts/release/create-clean-archive.sh

# Create clean archive for specific version
./scripts/release/create-clean-archive.sh v1.6.0
```

Output: `release-archives/japan-cannabinoid-trends-vX.Y.Z-clean.zip`

### Method 2: GitHub Actions (Automated)

The workflow `.github/workflows/release-zenodo.yml` automatically:

1. Creates a clean archive when a GitHub Release is published
2. Verifies the archive is clean
3. Uploads to Zenodo (if API key is configured)
4. Saves archive as workflow artifact

**Trigger:** Publish a GitHub Release

**Required secret:**
- `ZENODO_API_KEY`: Zenodo API key (optional - archive is created even without it)

### Method 3: Manual Zenodo Upload

1. Create clean archive using Method 1 or 2
2. Go to https://zenodo.org/upload
3. Upload the zip file
4. Fill in metadata (see below)
5. Submit

---

## Zenodo Metadata

When uploading manually, use:

| Field | Value |
|-------|-------|
| Title | CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan |
| Creators | Routeflags Co., Ltd. |
| Affiliation | Routeflags Co., Ltd. |
| Description | 日本国内におけるカンナビノイド関連トレンドを追跡するロングジューデータセット |
| Keywords | cannabinoid, CBX, H4CBH, HHBD, Google Trends, X (Twitter), YouTube, Japan |
| License | CC BY 4.0 |
| Version | (match git tag) |
| Resource Type | Dataset |

---

## Release Checklist

### Pre-release

- [ ] Update `CHANGELOG.md`
- [ ] Update version in `CITATION.cff`
- [ ] Update version in `metadata/datapackage.json`
- [ ] Update `publication/guide_cbx_rewrite.html` (dateModified, version)
- [ ] Commit all changes
- [ ] Run `./scripts/release/create-clean-archive.sh` to verify

### Release

- [ ] Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Create GitHub Release
- [ ] Upload clean archive to Zenodo (if not automated)
- [ ] Update `CITATION.cff` with new DOI
- [ ] Update `CHANGELOG.md` with DOI
- [ ] Update `README.md` badge if DOI changed

### Post-release

- [ ] Verify DOI resolves correctly
- [ ] Update citation tracker
- [ ] Announce release (optional)

---

## DOI Types

Zenodo assigns two types of DOIs:

| Type | Format | Resolves to | Usage |
|------|--------|-------------|-------|
| **Concept DOI** | `10.5281/zenodo.XXXXXXX` | Latest version | Stable citation |
| **Version DOI** | `10.5281/zenodo.XXXXXXX` | Specific version | Pin to exact release |

**Recommendation:** Use concept DOI in most citations; use version DOI when exact reproducibility is required.

---

## Current DOI

| Version | DOI | Concept DOI |
|---------|-----|-------------|
| v1.5.0 | [10.5281/zenodo.23085397](https://doi.org/10.5281/zenodo.23085397) | [10.5281/zenodo.23085396](https://doi.org/10.5281/zenodo.23085396) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Archive contains `.github/` | Use clean archive script or check INCLUDE_PATHS |
| Zenodo API key not set | Add `ZENODO_API_KEY` to repository secrets |
| Zip file too large | Check for raw data that should be excluded |
| DOI not updating | Manually upload to Zenodo or check workflow logs |

---

## Files in Clean Archive

A clean archive includes:

```
japan-cannabinoid-trends-vX.Y.Z-clean.zip
├── datasets/
│   ├── cbx-search-trends/
│   ├── cbx-social-trends/
│   ├── cbx-liquid-online-trend/
│   └── cbx-product-coa/
├── docs/
│   └── specs/
├── publication/
├── src/
│   ├── collection/
│   └── processing/
├── metadata/
│   └── datapackage.json
├── LICENSE
├── CITATION.cff
├── CHANGELOG.md
├── README.md
└── methodology.md
```

**Excluded:** `.github/`, `.serena/`, `artifacts/`, `.opencode`, credentials, raw social media data
