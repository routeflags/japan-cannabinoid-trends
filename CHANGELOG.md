# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.6.1] - 2026-10-02

**DOI:** [10.5281/zenodo.23090163](https://doi.org/10.5281/zenodo.23090163)

### Fixed
- **P2 Issue 一括修正** (検証レポート対応)
  - ISS-006: X データに小基数効果の警告を追加
  - ISS-007: ユニーク著者時系列を追加（W1:7人 → W3:22人 → W6:8人）
  - ISS-009: データ完全率を公開（全フィールド100%）
  - ISS-012: .gitignore に Google Trends raw データの例外を追加
  - ISS-014: README の古い「未作成」記載を修正

### Added
- **ISS-013:** `metadata/keywords.yaml` — カンナビノイドキーワード辞書
- **ISS-015:** `research/citation-tracker.md` — 引用トラッカー

### Notes
- ISS-004 (コンテンツ分類の検証) は保留
- ISS-008 (データ件数の不整合) と ISS-010 (バリアンス評価の拡張) は追加分析が必要

---

## [1.6.0] - 2026-10-02

**DOI:** [10.5281/zenodo.23089140](https://doi.org/10.5281/zenodo.23089140)

### Fixed
- **バージョン/DOI メタデータの全ファイル同期** (ISS-001)
  - CITATION.cff: version, DOI, preferred-citation を v1.6.0 に更新
  - datapackage.json: version, citation, modified を更新
  - methodology.md: Version 表記を更新
  - guide_cbx_rewrite.html: 引用ブロックの Version/DOI を更新
  - README.md: DOI バッジを Concept DOI に更新
- **自己検出済み文書エラーの修正** (ISS-002)
  - cbx_x_data_integrity.md: シャドウバン主張を「未検証」に変更
  - cbx_x_data_integrity.md: 遡及取得不可の主張を「取得可能」に変更
  - cbx_data_collection_report.md: 古い「101件」参照を147件に修正
- **COI 開示の矛盾解消** (ISS-003)
  - 「商品販売が目的ではなく」という否定文言を削除
  - 商業関係の開示と商品導線の共存を可能に

### Added
- バージョン/DOI 同期検証スクリプト (`scripts/validation/validate-version-sync.sh`)
- 検証 Issue 一覧 (`docs/issues/`)

---

## [1.5.3] - 2026-10-02

**DOI:** [10.5281/zenodo.23087213](https://doi.org/10.5281/zenodo.23087213)

### Added
- ORCID (Kyoji KATO, 0009-0007-5131-0374) を著者に追加
- Zenodo メタデータに related works (publication + dataset) を追加
- バージョン/DOI 同期検証スクリプト (`scripts/validation/validate-version-sync.sh`)
- 検証 Issue 一覧 (`docs/issues/`)

### Changed
- クリーンアーカイブから除外ファイルを追加: `.opencode/`, `.serena/`, `.gitignore`, `opencode.json`, `project.json`, `project.yml`
- Zenodo resource_type を `software` → `dataset` に修正
- 関連識別子の URL を動的バージョン参照に修正 (`releases/tag/${VERSION}`)

### Fixed
- X データ整合性ドキュメントの自己検出エラーを修正:
  - シャドウバン主張を「未検証」に変更（実際には `since:`/`until:` で取得可能）
  - 遡及取得不可の主張を「取得可能」に変更
  - 9月データの実件数（20件）を追記
- データ収集レポートの古い「101件」参照を修正（実際は147件）

### Notes
- v1.5.3 は自動リリースワークフローのテストリリース
- Zenodo メタデータに ORCID と related works が正しく設定されることを確認

---

## [1.5.2] - 2026-10-02

**DOI:** [10.5281/zenodo.23086803](https://doi.org/10.5281/zenodo.23086803)

### Fixed
- Zenodo file upload endpoint (PUT → POST)
- Improved error handling and logging in release workflow

### Notes
- This release successfully tested the automated clean archive workflow
- Clean archive uploaded to Zenodo with DOI

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
