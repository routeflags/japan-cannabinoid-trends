# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.5.1] - 2026-10-02

### Added
- `.github/workflows/release-zenodo.yml`: GitHub Actions workflow for clean archive release
- `scripts/release/create-clean-archive.sh`: Manual script for creating clean archives
- `docs/specs/release-process.md`: Release process guide

### Changed
- `docs/specs/zenodo-doi-guide.md`: Updated with clean archive information
- `.gitignore`: Add `.release-archives/`

### Notes
- This release tests the automated clean archive workflow
- Clean archives exclude development files (`.github`, `.serena`, `artifacts/`, etc.)

---

## [1.5.0] - 2026-10-01

**DOI:** [10.5281/zenodo.23085397](https://doi.org/10.5281/zenodo.23085397)

### Added
- LICENSE file (CC-BY-4.0)
- docs/specs/sns-redistribution-assessment.md
- docs/specs/raw-data-policy.md
- docs/specs/zenodo-doi-guide.md
- datasets/cbx-search-trends/methodology.md
- datasets/cbx-search-trends/analysis/ (HHBD peak investigation, CBX リキッド emergence analysis)

### Changed
- **publication/guide_cbx_rewrite.html**: GSC → Google Trends に主要検索データを差し替え
  - GSC を「参考データ」に降格（サイト依存のため信頼性が低い）
  - Google Trends データ（CBX / H4CBH / HHBD / CBX リキッド）を追加
  - YouTube セクションを 0件 → 24件に更新（26件から2件フィルタ）
  - CBX 多義性の注記を追加（ホンダ CBX400F 等との混在可能性）
  - COA 規制値の矛盾を修正（原料10ppm vs 成品1ppm の区別を明記）
  - 日付の不整合を修正（dateModified = 2026-10-01 に統一）
  - ORCID プレースホルダを削除
  - バージョン: 1.4 → 1.5

### Added
- **datasets/cbx-search-trends/methodology.md**: Google Trends 研究のメソドロジー文書
- **.github/skills/update-cbx-guide/**: CBX ガイドページ月次更新スキル
- **.github/skills/research-google-trends/**: Google Trends 研究用スキル
- **publication/README.md**: 公開アーティファクトの出所・統合データ文書

### Fixed
- **X 件数の定義統一**: 「147件（重複排除後101件）」→「147件（tweet_id ベースで重複排除済み）」
- **typo修正**: 「麻麻薬」→「麻薬」

### Data
- Google Trends 初回収集（2026-10-01）:
  - CBX: 単独平均 68, 比較平均 68, ピーク 100 (2026-09-13)
  - H4CBH: 単独平均 56, 比較平均 13, ピーク 100 (2026-07-26)
  - HHBD: 単独平均 33, 比較平均 7, ピーク 100 (2025-12-07)
  - CBX リキッド: 単独 44-92, 比較 0, ピーク 100 (2026-09-20)
- YouTube 再取得（2026-10-01）: 24件（26件から2件フィルタ、全件 CBX 関連）

---

## [1.4] - 2026-09-18

### Changed
- **publication/guide_cbx_rewrite.html**: X データを 101件 → 147件に更新
- X トレンドセクションを全面更新（週別推移、投稿者、エンゲージメント、コンテンツ分類）

---

## [1.3] - 2026-09-17

### Added
- Initial publication of guide_cbx_rewrite.html
- GSC データ統合（2026年7月、200クエリ）
- COA 分析結果統合（KCA + Anresco 2社）

---

## [1.0] - 2026-09-16

### Added
- Initial project structure
- Repository architecture (datasets/, src/, docs/, etc.)
