# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.11.0] - 2026-10-09

### Fixed
- CRDP/CRDH regulation status: corrected from "regulated" to "conditional legal" (条件付き合法)
- THCV regulation status: corrected to scheduled substance (指定薬物) since 2023-09-10
- Removed subjective language ("要注意") throughout all files
- Unified regulation terminology to "条件付き合法" for all non-regulated cannabinoids

### Added
- COA sections for H4CBH, HHBD, HHCH, CRDP with analysis summary tables
- COA analysis summary tables for CBG, CBN, THC-O
- CRDH YouTube statistics (views, channels, top videos)
- Downloaded COA files: H4CBH.pdf, HHBD.JPG, HHCH.pdf, CRDP.png, wing-cbg.jpg, cbn.jpeg, THCO-COA.pdf

### Changed
- All non-regulated compounds now consistently use "条件付き合法" terminology
- Regulation status reports updated with accurate information


## [1.10.0] - 2026-10-08

### Added
- **CRDH 化合物追加**
  - SKOS タクソノミー: compound_crdh
  - Google Trends: 12ヶ月 + 5年 + 共通スケール
  - X (Twitter): 200件
  - YouTube: 21件
  - COA: KCA Laboratories (ND結果)
  - 規制レポート: 非規制（要注意）
  - 調査ページ: publication/research_crdh.html

- **X コンテンツ分類拡張 (Batch 1: A2+A3)**
  - 13化合物に分類を拡張（4→13）
  - Wilson 95% 信頼区間を全比率に適用
  - 再現可能スクリプト: scripts/analysis/classify_x_data.py

- **規制前後比較分析 (Batch 2: B2+B3)**
  - HHC (2022-03-17): 平均いいね -36.8%
  - THC-O (2023-03-20): 平均いいね -31.6%
  - THCH (2023-08-04): 平均いいね +287.5%
  - CBG 対照付き: 再現可能スクリプト

- **CBX 規制レポート**
  - 化学構造不明のため分類不能
  - 製品中 THC 残留量で判断

- **YouTube データ拡張**
  - HHC: 27件, THCH: 20件, THC-O: 30件
  - H4CBH: 24件, HHBD: 22件, HHCH: 20件
  - CRDP: 27件, CRDH: 21件

### Changed
- **カバレッジ率改善**
  - YouTube: 50% → 100%
  - X: 79% → 100%
  - GT 5年: 86% → 100%
  - GT 共通Scale: 79% → 93%
  - COA: 57% → 64%
  - 調査ページ: 93% → 100%

- **引用トラッカー更新**
  - v1.9.0 DOI: 10.5281/zenodo.23164973
  - アラート設定手順を追加

### Fixed
- マトリックスのカバレッジ表を最新状態に更新

---

## [1.9.0] - 2026-10-05

### Added
- **12化合物ガイドページ** (substance-dictionary 準拠)
  - CBD, CBG, CBN, THC (flagship tier)
  - HHC, HHCH, THCH, THC-O, THCV, CRDP, H4CBH, HHBD (standard tier)
  - Evidence Ladder (L0-L4) と Claim Labels 適用
  - 薬機法/YMYL コンプライアンス対応

- **Google Trends common-scale 拡張**
  - 比較セット B: CBN, CRDP, HHCH, THC-O, THCV
  - 比較セット C: CBN, CBG, CBD
  - 比較セット D: H4CBH, HHBD, CRDP
  - 共通スケール比較を 5→12 化合物に拡張

- **Inter-rater Reliability (kappa) 検証**
  - H4CBH: kappa = 0.596 (Moderate)
  - HHBD: kappa = 0.804 (Almost perfect)
  - 分類信頼性の定量化

- **Phase 2 データ収集**
  - 日本語 YouTube データ (Apify): 180件
  - CBN 規制前後 X データ + CBG 対照: 300件
  - H4CBH/HHBD X データ拡大 (n=200): 400件

- **Compound Guide Generation スキル**
  - `.github/skills/generate-compound-guide/`
  - substance-dictionary 準拠のガイドページ生成

### Changed
- **Google Trends ランキング修正**
  - 個別正規化データの誤用を修正
  - 共通スケール比較データを使用
  - CBD > THC > CBG > HHC > THCH の順序に修正

- **CBN 表現の修正**
  - 「規制効果」→「時系列的関連」に変更
  - 因果関係の非主張を明確化

- **Evidence Ladder ガイドページ適用**
  - 全12ガイドページに L0-L4 バッジ追加
  - Claim Labels (OBSERVED/DERIVED/INTERPRETATION) 追加

- **H4CBH/HHBD/CRDP 規制表現の緩和**
  - 「極めて高い」→「可能性がある」に変更

- **Early Warning Index 方法論の文書化**
  - データ辞書セクション追加
  - 正規化の注意事項を明記

- **SNS 分類手法の文書化**
  - 分類プロセス・カテゴリ定義を文書化
  - 信頼区間 (Wilson score) を追加

### Fixed
- **バージョン/DOI 同期**
  - datapackage.json, methodology.md, guide_cbx, README の不整合を修正
  - pre-commit hook にバージョン同期検証を追加

- **Google Trends 比較の順位矛盾**
  - Section 1 と Section 5 の整合性を修正

- **YouTube データ文書の修正**
  - API クォータ: 10,000 → 100/日
  - 日本語 CBD 件数: 653 → 423 (11%)
  - 日本語キーワード収集の失敗を明記

### Research Outputs
- `research/20261004-google-trends-comparison.md` (修正版)
- `research/20261004-h4cbh-hhbd-sns-analysis.md` (CI 追加)
- `research/20261005-kappa-analysis.md`
- `research/20261005-phase2-collection-results.md`
- `research/20261005-phase2-analysis-results.md`
- `research/20261005-academic-research-youtube-review.md`

---

## [1.8.0] - 2026-10-02

### Added
- **Early Warning Index v1** (JCEI-20261002)
  - 新規データセット: `early-warning-index-v1.csv`
  - 12化合物の出現追跡と規制状況
  - Emergence Score システム (ES 0-4)
  - Finding ID システム (JCEI-F001〜F007)
  - Baseline/Emerging コホート分類
  - 英語ランディングページ (`publication/early-warning-index/`)
  - 方法論・制約事項ドキュメント

- **規制状況調査** (REG-20261002)
  - 12化合物の日本法規制を調査
  - `research/regulatory-status/` に個別レポート作成
  - HHC: 2022-03-17 指定薬物化
  - THC-O: 2023-03-20 指定薬物化
  - THCH: 2023-08-04 個別指定 + 2023-09-10 包括指定
  - HHCH: 2023-12-02 指定薬物化
  - CBN: 2026-06-01 指定薬物化

- **HHCH キーワード調査**
  - Google Trends データ収集 (12ヶ月 + 5年)
  - 初出時期: 2023-03-26
  - 規制効果のケーススタディ (post-regulation decline)

- **スキル: research-keyword-trends**
  - 任意のキーワードで Google Trends 調査を再利用可能に

### Changed
- **Citation Tracker 更新**
  - Asset Register に Early Warning Index v1 を追加
  - Citation Unit Log テーブルを追加
  - Citation Health Funnel を追加
  - 監視クエリを拡張

- **規制データの正確性修正**
  - THC-O: 麻薬 → 指定薬物 (2023-03-20)
  - THCH: 包括指定日を追加 (2023-09-10)
  - THC: 規制モデルを3列に分割

---

## [1.7.1] - 2026-10-02

**DOI:** [10.5281/zenodo.23097769](https://doi.org/10.5281/zenodo.23097769)

### Added
- **キーワードカバレッジ拡張** (EXP-20261002)
  - 新 Study: `cannabinoid-multi-trends`
  - 主要カンナビノイド7化合物を追加: CBD, THC, CBG, HHC, THCV, THC-O, THCH
  - Google Trends: 5キーワード × 52週 + 比較セット + 5年データ
  - X (Twitter): 7キーワード × 316件
  - YouTube: 7キーワード × 182件
- **言及開始時期調査** (MNT-20261002)
  - 各成分の Google Trends 初出時期を特定
  - 5年データ (2021-09 〜 2026-10) を収集
  - THC-O 初出: 2022-03-13
  - データの限界を明確化 (Google Trends 5年制限)

### Changed
- **ドキュメント更新**
  - `metadata/datapackage.json`: 新 Study のリソース追加、キーワード更新
  - `docs/data-dictionary.md`: 新カラム定義追加 (Section 6)
  - `CITATION.cff`: キーワード更新、バージョン 1.7.1
- **エージェント更新**
  - research-pipeline, research-data-librarian, doi-validator, research-chair
  - AGENTS.md: 技術標準セクション追加

---

## [1.7.0] - 2026-10-02

**DOI:** [10.5281/zenodo.23095153](https://doi.org/10.5281/zenodo.23095153)

### Added
- **技術標準対応** (W3C SKOS, IPTC, Schema.org)
  - `metadata/taxonomy/content-taxonomy.skos.jsonld`: コンテンツ分類タクソノミー (W3C SKOS)
  - `metadata/taxonomy/compound-taxonomy.skos.jsonld`: 化合物タクソノミー (W3C SKOS)
  - `metadata/taxonomy/iptc-mapping.yaml`: IPTC Media Topics 対応表
  - `metadata/taxonomy/classification-rules.yaml`: 分類ルール定義
  - `metadata/schema/socialmediaposting.jsonld`: Schema.org マッピング
- **コンテンツ分類** (ISS-004 解決)
  - X データに topic_id, intent_id, format_id, platform, language フィールドを追加
  - ルールベース分類器で 147 件を分類
  - 分類結果: 配合/成分 67.3%, 情報提供 64.6%, テキスト 98.0%
- **エクスポートスクリプト**
  - `scripts/export/skos-to-rdf.py`: RDF/Turtle エクスポート
  - `scripts/export/skos-to-schema-jsonld.py`: Schema.org JSON-LD エクスポート
  - `scripts/export/export-taxonomy.sh`: 統合エクスポート
- **検証スクリプト更新**
  - SKOS タクソノミー検証
  - Concept ID 妥当性検証
  - プロパティ完全性検証
- **技術標準対応スキル** (`.github/skills/standards-compliance/SKILL.md`)

### Changed
- データスキーマを 11 カラム → 16 カラムに拡張
- 検証スクリプトを SKOS 準拠検証に対応

### Notes
- 分類器はルールベース（キーワードマッチ）— 将来的に LLM / BERT へ交換可能
- Concept ID は固定のため、分類器の交換時も Taxonomy を維持
- ISS-004 (コンテンツ分類の未検証) を実質的に解決

---

## [1.6.2] - 2026-10-02

**DOI:** [10.5281/zenodo.23091163](https://doi.org/10.5281/zenodo.23091163)

### Added
- **Data Dictionary** (`docs/data-dictionary.md`): 全カラム定義（型、単位、欠損値）
- **Provenance** (`docs/provenance.md`): データ来歴（raw → 公開値の対応表）
- **匿名化版 X データ** (`x_cbx_202608_summary_anonymized.csv`): 個人情報を除去した公開用データ
- **Frictionless スキーマ** (`datapackage.json`): 各リソースのフィールド定義・制約
- **スキーマ検証スクリプト** (`scripts/validation/validate-data-schema.sh`)
- **Git pre-commit hook**: コミット前にスキーマ一致を自動検証

### Changed
- `.gitignore`: private データディレクトリを除外
- FAIR 原則の Interoperability スコアが向上（2.7 → 3.5+）

### Security
- X データの個人情報を匿名化（username → author_id, text → text_length）
- 匿名化マッピングはローカル専用（gitignore 対象）

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
