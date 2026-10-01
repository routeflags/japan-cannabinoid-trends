# Zenodo DOI Registration Guide

**Purpose:** Guide for registering the Japan Cannabinoid Trends dataset on Zenodo
**Date:** 2026-10-01
**Version:** 1.5.0

---

## 1. Prerequisites

Before starting Zenodo registration, ensure:

- [ ] LICENSE file contains CC-BY-4.0 text ✅
- [ ] CITATION.cff is populated ✅
- [ ] Creator metadata is complete ✅
- [ ] Git tag v1.5.0 exists ✅
- [ ] Counts are reconciled ✅
- [ ] Redistribution assessment completed ✅
- [ ] Raw data policy documented ✅

---

## 2. Zenodo Account Setup

### 2.1 Create Account

1. Go to https://zenodo.org
2. Click "Sign up"
3. Use a real email address
4. Consider using a GitHub account for integration

### 2.2 Complete Profile

- Add institutional affiliation (Routeflags Co., Ltd.)
- Add ORCID if available (recommended)
- Set up profile visibility

---

## 3. GitHub-Zenodo Integration (Recommended)

### 3.1 Enable Integration

1. Go to https://zenodo.org/account/settings/github/
2. Click "Connect GitHub"
3. Authorize Zenodo for the `routeflags/japan-cannabinoid-trends` repository
4. Enable integration for this repository

### 3.2 How It Works

- When you create a GitHub Release, Zenodo automatically creates a DOI
- Each release gets its own DOI
- The DOI resolves to a Zenodo page with the archived release

---

## 4. Manual Upload (Alternative)

If GitHub integration is not desired:

### 4.1 Create Release Archive

```bash
# Clone the repository
git clone https://github.com/routeflags/japan-cannabinoid-trends.git
cd japan-cannabinoid-trends

# Checkout the tag
git checkout v1.5.0

# Create archive (excluding raw data)
tar --exclude='.git' \
    --exclude='**/data/raw/*' \
    --exclude='**/node_modules/*' \
    --exclude='.env*' \
    -czf japan-cannabinoid-trends-v1.5.0.tar.gz .
```

### 4.2 Upload to Zenodo

1. Go to https://zenodo.org/upload
2. Drag and drop the archive
3. Fill in metadata (see below)
4. Submit for review

---

## 5. Zenodo Metadata

### 5.1 Required Fields

| フィールド | 値 |
|-----------|-----|
| Title | CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan |
| Creators | Routeflags Co., Ltd. |
| Publication Date | 2026-10-01 |
| Resource Type | Dataset |
| License | CC BY 4.0 |
| Version | 1.5.0 |

### 5.2 Additional Fields (Recommended)

| フィールド | 値 |
|-----------|-----|
| Description | 日本国内におけるカンナビノイド関連トレンドを追跡するロングジューデータセット。Google Trends（CBX / H4CBH / HHBD / CBX リキッド、12ヶ月週次）、X (Twitter) 147件（重複排除済み）、YouTube 24件（フィルタ済み）、COA 分析結果（ISO/IEC 17025 認定 2 社）を収録。 |
| Keywords | cannabinoid, CBX, H4CBH, HHBD, Google Trends, X (Twitter), YouTube, Japan, online trends, search interest, longitudinal data |
| Related Works | https://github.com/routeflags/japan-cannabinoid-trends |
| Notes | Raw social media data excluded per redistribution policy. Processed aggregates and run metadata included. |

### 5.3 DataCite Metadata Mapping

| DataCite Field | Value |
|---------------|-------|
| creators | Routeflags Co., Ltd. |
| titles | CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan |
| publisher | Routeflags Co., Ltd. |
| publicationYear | 2026 |
| resourceTypeGeneral | Dataset |
| url | https://github.com/routeflags/japan-cannabinoid-trends |
| rights | CC BY 4.0 |
| version | 1.5.0 |
| geoLocation | JP (Japan) |
| language | ja |

---

## 6. What to Include in the Archive

### 6.1 Include

| 項目 | パス | 理由 |
|------|------|------|
| Processed data | `datasets/*/data/processed/` | 分析可能な集計データ |
| Run metadata | `datasets/*/data/raw/google_trends/` | 収集条件の記録 |
| Methodology | `datasets/*/methodology.md` | 再現性のため |
| Documentation | `README.md`, `LICENSE`, `CITATION.cff` | 引用・ライセンス |
| Specs | `docs/specs/` | 方針・評価文書 |

### 6.2 Exclude

| 項目 | パス | 理由 |
|------|------|------|
| Raw X data | `datasets/*/data/raw/x/` | X TOS 制限 |
| Raw YouTube data | `datasets/*/data/raw/youtube/` | YouTube TOS 制限 |
| Credentials | `.env*`, `*.key` | セキュリティ |
| Node modules | `node_modules/` | 不要 |

---

## 7. After DOI Assignment

### 7.1 Update Repository

```bash
# Update CITATION.cff
# Replace "doi: Pending" with the assigned DOI

# Update CHANGELOG.md
# Add DOI to the release entry

# Update publication/guide_cbx_rewrite.html
# Replace "DOI: [Pending]" with the assigned DOI

# Commit and push
git add .
git commit -m "Add DOI: [DOI]"
git push
```

### 7.2 Update Landing Page

- Add DOI badge to the guide page
- Add DOI to the citation block
- Link to Zenodo record

---

## 8. Versioning Strategy

### 8.1 Version Numbering

| Version | Change Type | Example |
|---------|-------------|---------|
| Patch | Bug fixes, documentation | 1.5.1 |
| Minor | New data, new features | 1.6.0 |
| Major | Methodology change, schema change | 2.0.0 |

### 8.2 Release Process

1. Update data or methodology
2. Update CHANGELOG.md
3. Increment version in CITATION.cff
4. Create git tag
5. Create GitHub Release (triggers Zenodo)
6. Update landing page with new DOI

---

## 9. Citation Format

Once DOI is assigned, the citation format will be:

```
Routeflags Co., Ltd. (2026).
CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan.
Version 1.5.0.
Routeflags Co., Ltd.
[Dataset].
DOI: 10.5281/zenodo.XXXXXXX
```

---

## 10. Troubleshooting

| 問題 | 原因 | 対処 |
|------|------|------|
| Zenodo が DOI を発行しない | ライセンス未設定 | LICENSE ファイルを確認 |
| タグが検出されない | タグがリモートに未プッシュ | `git push --tags` を実行 |
| アーカイブが大きい | raw データが含まれている | `--exclude` オプションを確認 |
| メタデータが不完全 | 必須フィールドが未入力 | 本ガイドの 5 章を参照 |

---

## 11. References

- Zenodo Documentation: https://help.zenodo.org
- Zenodo-GitHub Integration: https://help.zenodo.org/docs/github/enable-integration
- DataCite Metadata Schema: https://schema.datacite.org
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
