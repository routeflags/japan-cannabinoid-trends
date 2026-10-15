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
| Title | Japan Cannabinoid Platform Trends Dataset 2026: Google Trends and YouTube Evidence from Japan |
| Creators | Routeflags Co., Ltd. |
| Affiliation | Routeflags Co., Ltd. |
| Description | 日本国内における各カンナビノイド成分の国内トレンドと、Google Trends / YouTube で観測できる差異を記録するデータセット。v1.13.0 は cannabinoid-platform-trends study を追加し、Google Trends 5年サマリーと採用済み YouTube 検索結果集計を source-specific units のまま収録する。X はこのリリーススコープから除外する。 |
| Keywords | cannabinoid, CBD, CBG, CBN, CBX, CRDH, CRDP, H4CBH, HHBD, Google Trends, YouTube, Japan, platform trends |
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
- [ ] Run `gate-publication` 手動ゲートを実行し判定と証拠を記録する（公開は人の判断。現行方針: 機械は公開を止めない。例: `python -m validation.cli gate-publication --artifact <artifact.json> --decision <decision.json> --evidence <evidence.json> --output docs/audits/g6-publication-eligibility.json`。判定が BLOCKED の場合は理由を記録し公開しない。詳細は `docs/specs/validation-framework.md` §19）

### Release

- [ ] Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Create GitHub Release（release notes に Zenodo concept DOI を記載する）
- [ ] Release workflow が以下を自動実行する:
  - clean archive の作成（`metadata/artifacts/` 等の正規パスを除外判定に含めない）
  - `scripts/validation/check-release-archive.py`（アーカイブ内 CITATION /
    datapackage / README の version・concept DOI と release の一致を検証。不一致なら失敗）
  - `validate-release-manifest`（`scripts/release/make-release-manifest.py` で
    `release-manifest-v1` を生成し、required / 禁止パス / scope と上記 identity
    を検証。不一致なら Zenodo 送信前に失敗。ISS-20261015-REL-014）
  - `scripts/release/publish-zenodo.py`（`CITATION.cff` の concept DOI の
    record に newversion で公開。`related_identifiers` の GitHub Release URL が
    展開済み URL で保存されたことを公開後に照合し、不一致なら失敗）
- [ ] ワークフロー結果から DOI を確認し、必要なら `CHANGELOG.md` / 引用情報を追記する
  （concept DOI は series で固定のため、通常は変更不要）

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
| v1.13.2 | [10.5281/zenodo.23390594](https://doi.org/10.5281/zenodo.23390594) | [10.5281/zenodo.23390594](https://doi.org/10.5281/zenodo.23390594) |

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
