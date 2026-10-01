# Issue: バージョン/DOI メタデータの全ファイル不整合

**ID:** ISS-20261002-001
**優先度:** P0 (Critical)
**検出日:** 2026-10-02
**検出方法:** 独立検証 (Cannabinoid Trend Whitepaper Validator) + validate-version-sync.sh
**ステータス:** OPEN

---

## 概要

リポジトリ内の全ファイルに記載されたバージョン番号と DOI が、実際の Zenodo リリース (v1.5.3 / 10.5281/zenodo.23087213) と一致していない。

## 影響

**第三者がリポジトリの引用指示に従うと、古いバージョンと古い DOI を引用してしまう。**

## 検出結果

検証スクリプト `scripts/validation/validate-version-sync.sh` による検出: **12件の不整合**

| ファイル | フィールド | 現在の値 | 期待値 |
|----------|-----------|---------|--------|
| CITATION.cff | version | 1.5.1 | **1.5.3** |
| CITATION.cff | preferred-citation.version | 1.5.2 | **1.5.3** |
| CITATION.cff | identifiers.doi | 10.5281/zenodo.23086803 | **10.5281/zenodo.23087213** |
| CITATION.cff | preferred-citation.doi | 10.5281/zenodo.23086803 | **10.5281/zenodo.23087213** |
| CHANGELOG.md | 最新エントリ | v1.5.2 | **v1.5.3** |
| metadata/datapackage.json | version | 1.5.0 | **1.5.3** |
| metadata/datapackage.json | citation 内 Version | 1.5.2 | **1.5.3** |
| metadata/datapackage.json | citation DOI | 10.5281/zenodo.23086803 | **10.5281/zenodo.23087213** |
| methodology.md | version | 1.5.0 | **1.5.3** |
| publication/guide_cbx_rewrite.html | 引用 Version | 1.5.0 | **1.5.3** |
| publication/guide_cbx_rewrite.html | 引用 DOI | 10.5281/zenodo.23085396 | **10.5281/zenodo.23087213** |
| README.md | DOI バッジ | 10.5281/zenodo.23086802 | **10.5281/zenodo.23087213** |

## 修正手順

### 1. CITATION.cff

```yaml
# version
version: "1.5.3"

# preferred-citation
preferred-citation:
  version: "1.5.3"
  url: "https://doi.org/10.5281/zenodo.23087213"
  doi: "10.5281/zenodo.23087213"

# identifiers
identifiers:
  - type: doi
    value: "10.5281/zenodo.23087213"
    description: "Zenodo DOI"
```

### 2. CHANGELOG.md

```markdown
## [1.5.3] - 2026-10-02

### Added
- ORCID (Kyoji KATO) を著者に追加
- Zenodo メタデータに related works を追加
- バージョン/DOI 同期検証スクリプトを追加

### Changed
- クリーンアーカイブから除外ファイルを追加 (.opencode, .serena, .gitignore, opencode.json, project.json, project.yml)
- Zenodo resource_type を software → dataset に修正
- 関連識別子の URL を動的バージョン参照に修正
```

### 3. metadata/datapackage.json

```json
{
  "version": "1.5.3",
  "modified": "2026-10-02",
  "citation": "Routeflags Co., Ltd. (2026). CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan. Version 1.5.3. Routeflags Co., Ltd. [Dataset]. DOI: 10.5281/zenodo.23087213"
}
```

### 4. methodology.md

Version 表記を 1.5.3 に更新

### 5. publication/guide_cbx_rewrite.html

引用ブロックの Version と DOI を更新:
- Version 1.5.0 → 1.5.3
- DOI 10.5281/zenodo.23085396 → 10.5281/zenodo.23087213
- dateModified を 2026-10-02 に更新

### 6. README.md

DOI バッジを Concept DOI (10.5281/zenodo.23087212) に更新

## 検証

修正後、以下を実行して全 PASS になることを確認:

```bash
bash scripts/validation/validate-version-sync.sh
```

## 関連

- 検証スクリプト: `scripts/validation/validate-version-sync.sh`
- 検証レポート: 独立検証 2026-10-02
- Zenodo DOI: https://doi.org/10.5281/zenodo.23087213
