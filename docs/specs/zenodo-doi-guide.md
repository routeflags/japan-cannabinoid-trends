# Zenodo DOI Registration Guide

**Purpose:** Guide for registering the Japan Cannabinoid Trends dataset on Zenodo
**Date:** 2026-10-02
**Version:** 1.5.0

---

## Important: Clean Archives

GitHub's automatic release archives include development files (`.github`, `.serena`, etc.) that are not suitable for research citation.

**Use clean archives instead.** See `docs/specs/release-process.md` for details.

### Quick Start

```bash
# Create clean archive
./scripts/release/create-clean-archive.sh

# Or let GitHub Actions do it automatically
# (publish a GitHub Release)
```

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
- Zenodo-GitHub Integration: https://help.zenodo.org/docs/github/enabl
e-integration
- DataCite Metadata Schema: https://schema.datacite.org
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

---

## 12. 投稿単位 X データの取り下げ（2026-10-15、オーナー決定）

### 12.1 背景

このリポジトリの Zenodo アーカイブは GitHub Release からの自動アーカイブで作られる。
以下の 2 ファイルは公開済みバージョンに含まれており、2026-10-15 の決定
（`ISS-20261015-COL-030` §4.1: 匿名化後も投稿単位の X データは公開しない）により
取り下げ対象になった（リポジトリ側の取り下げは `ISS-20261015-PUB-035` で完了）。

対象の特定はエージェントが Zenodo 公開 API＋ZIP 実体の照合で完了した（2026-10-15）。
注意点:

- 各リリースは1つの concept の versions ではなく、**独立した record が 12 件**ある
  （GitHub 連携の紐付け不備。将来の新規リリースも同様に独立 record になる見込み）。
  削除は record ごとに1回ずつ、計 12 回の操作が必要。
- 各 record は clean ZIP 1 ファイルのみ。ZIP 内の実測で以下を確認した
  （`unzip -l` 全 12 件。v1.12.0 は実ダウンロードでも確認）。
- `x_cbx_202608_summary.csv` は現在の git タグ tree には存在しないが、**ZIP 実体には含まれる**
  （リリース作業ツリー由来とみられる。provenance 上の注意として記録）。
- 全 12 record の created は 2026-10-01〜10-09 で、**全件 30 日以内**（オーナー確認と一致）。
  自力削除可。古いものから先に（v1.5.2 系の期限が最も近い）。

| record | version | created | summary.csv | anonymized.csv | 削除期限の目安 |
|---|---|---|---|---|---|
| https://zenodo.org/records/23086803 | v1.5.2 | 10-01 | あり | なし | 10-31 |
| https://zenodo.org/records/23087213 | v1.5.3 | 10-01 | あり | なし | 10-31 |
| https://zenodo.org/records/23089140 | v1.6.0 | 10-01 | あり | なし | 10-31 |
| https://zenodo.org/records/23090163 | v1.6.1 | 10-01 | あり | なし | 10-31 |
| https://zenodo.org/records/23091163 | v1.6.2 | 10-01 | あり | あり | 10-31 |
| https://zenodo.org/records/23095153 | v1.7.0 | 10-02 | あり | あり | 11-01 |
| https://zenodo.org/records/23097769 | v1.7.1 | 10-02 | あり | あり | 11-01 |
| https://zenodo.org/records/23101318 | v1.8.0 | 10-02 | あり | あり | 11-01 |
| https://zenodo.org/records/23164973 | v1.9.0 | 10-05 | あり | あり | 11-04 |
| https://zenodo.org/records/23240245 | v1.10.0 | 10-08 | あり | あり | 11-07 |
| https://zenodo.org/records/23243495 | v1.11.0 | 10-08 | あり | あり | 11-07 |
| https://zenodo.org/records/23253840 | v1.12.0 | 10-09 | あり | あり | 11-08 |

GitHub 側は対応済み（Release のアセット 0 件、タグ書き換えで自動生成アーカイブは
クリーン。`validation-framework.md` §21.6）。残る露出は **Zenodo 側の独立コピー**のみ。

### 12.2 制約（事前に理解すること）

- **公開済みバージョンのファイルは Web UI から削除できない**（イミュータブル）。
  削除・制限には Zenodo サポートへの依頼が必要で、可否はサポートの判断になる。
- タグの書き換え・GitHub Release の削除は、**既に公開された Zenodo バージョンには波及しない**
  （Zenodo は公開時点で独立コピーを保持する）。
- 新規リリースは既にクリーン（取り下げ済みファイルは追跡下に無い）なので、
  将来の配布は止まっている。以下は**過去バージョン**の扱いである。

### 12.3 手順（メンテナの操作。Zenodo アカウントが必要）

公式ドキュメントの確認結果（2026-10-15。`help.zenodo.org/docs/deposit/manage-records/`、
`manage-files/`）:

- **完全な削除（版ごと）を所有者が自力で行えるのは公開後 30 日以内のみ**。
  対象版は 30 日以内であることをオーナーが確認（2026-10-15）のため、**自力削除が可能**。
  期限を過ぎた版・削除に失敗した版のみサポート依頼（個人データの露出は正当事由として認められうる）。
- **ファイルの公開アクセス制限・公開ノート追加は、公開後も所有者が Edit で自力実行できる**
  （Files の visibility 変更＋公開。サポートを待たずに実質の露出を止められる）。
- **GitHub 連携の解除・リセットは過去版に波及しない**（公開時点で Zenodo が独立コピーを保持する）。
  連携解除の効果は将来の自動アーカイブ停止のみ。
- API での公開済み版の削除・ファイル変更は不可（削除 API は未公開ドラフトのみ）。

1. §12.1 の表の record を上から順に開く（特定作業は済み。オーナーは開いて消すだけ）。
2. **自力削除（30 日以内のため可能。古い版から先に）**: 該当バージョンごとに
   レコードページ → Manage record → Delete record → 削除理由を選択 → Delete immediately。
   削除後は引用保存用の tombstone ページに遷移する（DOI 自体は残る）。
   対象は 2 ファイルのいずれかを含む全バージョン（`x_cbx_202608_summary.csv` を含む約 14 版と
   `x_cbx_202608_summary_anonymized.csv` を含む v1.6.2〜v1.12.0 の 8 版の和集合）。
3. 削除できなかった版がある場合のみ: ファイルの公開アクセス制限（Edit → visibility 変更）で
   実質配布を止め、完全削除のサポート依頼（依頼文の雛形は §12.4）。
4. 並行して、新規バージョンを上記 2 ファイルなしで公開する手も取れる
   （将来の参照先をクリーンにする。古いバージョンのファイルは残る）。
5. 実行後、以下を更新する:
   - `src/processing/reproduce.py` の `WITHDRAWN` 2 件の `exposure`
     （「取り下げ済み」へ。日付付き）
   - `ISS-20261015-XID-035` の C1 → RESOLVED（日付付き）

### 12.4 依頼文の雛形

```text
件名: Removal/restriction request for files in published versions (personal data)

本文:
Record: [concept DOI]
Affected versions: [version DOIs]
Files:
- datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv
- datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv
Reason: row-level social media data (post timestamps and per-post engagement for
147 posts). Our policy changed on 2026-10-15 to not publish post-level data even
anonymized (ISS-20261015-COL-030 4.1). We have withdrawn the files from the
repository and stopped distributing them in new releases; we ask that the files
in the published versions above be removed or restricted.
```

