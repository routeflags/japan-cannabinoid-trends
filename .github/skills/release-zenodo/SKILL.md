---
name: release-zenodo
description: |
  CBX データセットのリリースと Zenodo DOI 登録フロー。
  「リリース作成」「Zenodo に公開」「vX.Y.Z 作成」「DOI 取得」などで使う。
---

# Release Zenodo リリーススキル

CBX データセットのリリースと Zenodo DOI 登録を一括で実行するスキル。

GitHub Release 公開 → GitHub Actions 自動実行 → クリーンアーカイブ作成 → Zenodo アップロード → DOI 発行。

---

## トリガー

- 「リリース作成」
- 「Zenodo に公開」
- 「vX.Y.Z 作成」
- 「DOI 取得」
- 「データセットをリリース」
- 「新バージョンを公開」

---

## 前提

- GitHub リポジトリへの push 権限
- Zenodo API キーが `ZENODO_API_KEY` としてリポジトリ secrets に設定済み
- 作業ディレクトリ: `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends`

---

## フロー概要

```text
Step 1: バージョン更新
        ↓
Step 2: CHANGELOG 更新
        ↓
Step 3: コミット
        ↓
Step 4: git タグ作成
        ↓
Step 5: GitHub Release 公開
        ↓
Step 6: Actions 実行確認
        ↓
Step 7: DOI 確認
        ↓
Step 8: CITATION.cff 更新
        ↓
Step 9: コミット・プッシュ
```

---

## Step 1: バージョン更新

### 更新対象ファイル

| ファイル | 更新箇所 |
|---------|---------|
| `CITATION.cff` | `version`, `date-released`, `preferred-citation.version` |
| `metadata/datapackage.json` | `version`, `modified`, `citation` |

### 更新例

```yaml
# CITATION.cff
version: "1.6.0"
date-released: "2026-11-01"
```

```json
// metadata/datapackage.json
"version": "1.6.0",
"modified": "2026-11-01"
```

---

## Step 2: CHANGELOG 更新

`CHANGELOG.md` に新しいバージョンのエントリを追加。

```markdown
## [1.6.0] - 2026-11-01

### Added
- （追加した機能・データ）

### Changed
- （変更した内容）

### Fixed
- （修正した内容）
```

---

## Step 3: コミット

```bash
cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends

git add CITATION.cff CHANGELOG.md metadata/datapackage.json
git commit -m "Bump version to X.Y.Z"
git push
```

---

## Step 4: git タグ作成

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z

（リリースの内容を簡潔に）"
git push origin vX.Y.Z
```

---

## Step 5: GitHub Release 公開

```bash
gh release create vX.Y.Z \
  --title "CBX Online Trend Dataset 2026 vX.Y.Z" \
  --notes "## Release vX.Y.Z

**Release Date:** YYYY-MM-DD

### Changes
- （変更内容）

### DOI
This release will be automatically uploaded to Zenodo." \
  --verify-tag
```

---

## Step 6: Actions 実行確認

```bash
# 実行結果を確認（20秒待機）
sleep 20
gh run list --limit 2
```

**期待される結果:**

| ステータス | 内容 |
|-----------|------|
| `completed/success` | 成功 |
| `completed/failure` | 失敗（ログ確認） |

### 失敗時のログ確認

```bash
gh run view <run-id> --log-failed
gh run view <run-id> --log 2>&1 | grep -E "✅|❌|DOI|Error"
```

---

## Step 7: DOI 確認

```bash
gh run view <run-id> --log 2>&1 | grep -E "DOI:|Concept DOI:"
```

**期待される出力:**

```
🎉 Zenodo Upload Complete!
DOI: 10.5281/zenodo.XXXXXXX
Concept DOI: 10.5281/zenodo.XXXXXXX
```

### Zenodo レコードの検証

```bash
curl -s "https://zenodo.org/api/records/<record-id>" | jq '{
  doi: .doi,
  title: .metadata.title,
  creators: .metadata.creators,
  version: .metadata.version,
  related_identifiers: .metadata.related_identifiers
}'
```

---

## Step 8: CITATION.cff 更新

取得した DOI で `CITATION.cff` を更新。

```yaml
# identifiers
identifiers:
  - type: doi
    value: "10.5281/zenodo.XXXXXXX"
    description: "Zenodo DOI"

# preferred-citation
preferred-citation:
  version: "X.Y.Z"
  url: "https://doi.org/10.5281/zenodo.XXXXXXX"
  doi: "10.5281/zenodo.XXXXXXX"
```

### README.md の DOI バッジも更新

```markdown
[![DOI](https://zenodo.org/badge/1375618430.svg)](https://doi.org/10.5281/zenodo.XXXXXX)
```

> **注:** バッジの URL は Concept DOI を使う

---

## Step 9: コミット・プッシュ

```bash
git add CITATION.cff README.md metadata/datapackage.json
git commit -m "Update DOI for vX.Y.Z: 10.5281/zenodo.XXXXXXX"
git push
```

---

## Zenodo メタデータ設定（ワークフロー内）

GitHub Actions が自動で設定するメタデータ：

| フィールド | 値 |
|-----------|-----|
| Title | CBX Online Trend Dataset 2026: Google Trends, Social Media, and COA Data from Japan |
| Creators | KATO, Kyoji (ORCID: 0009-0007-5131-0374) |
| Resource type | dataset |
| License | CC BY 4.0 |
| Version | （git タグ） |
| Related: publication | https://www.thch-vape.shop/guide/substance/what-is-cbx |
| Related: dataset | https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/vX.Y.Z |

---

## クリーンアーカイブ内容

GitHub Actions が作成する zip に含まれるもの：

```
japan-cannabinoid-trends-vX.Y.Z-clean.zip
├── datasets/
│   ├── cbx-search-trends/
│   ├── cbx-social-trends/
│   ├── cbx-liquid-online-trend/
│   └── cbx-product-coa/
├── docs/specs/
├── publication/
├── src/
├── metadata/
├── LICENSE
├── CITATION.cff
├── CHANGELOG.md
├── README.md
└── methodology.md
```

**除外されるファイル:**

| ファイル/ディレクトリ | 理由 |
|----------------------|------|
| `.github/` | CI/CD・エージェント定義 |
| `.serena/` | IDE 設定 |
| `.opencode/` | ツール設定 |
| `artifacts/` | 日報 |
| `.gitignore` | 開発用 |
| `opencode.json` | ツール設定 |
| `project.json` / `project.yml` | プロジェクト設定 |
| `.env*` | 認証情報 |
| raw social data | TOS 制限 |

---

## バージョニング規則

| 種類 | 例 | 使用場面 |
|------|-----|---------|
| Patch | 1.5.2 → 1.5.3 | バグ修正、ドキュメント |
| Minor | 1.5.3 → 1.6.0 | 新データ、新機能 |
| Major | 1.6.0 → 2.0.0 | メソドロジー変更、スキーマ変更 |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| Actions 失敗: 405 error | Zenodo API エンドポイント | PUT → POST を確認 |
| DOI が発行されない | API キー無効 | `ZENODO_API_KEY` を再設定 |
| クリーン zip に不要ファイル | 除外リスト漏れ | `release-zenodo.yml` の除外リストを確認 |
| ORCID が表示されない | creators メタデータ | ワークフローの creators 設定を確認 |
| 関連リンクが古い | ハードコード | `${VERSION}` 変数を使用 |

---

## コスト

| 項目 | コスト |
|------|--------|
| Zenodo | **無料** |
| GitHub Actions | 無料（公開リポジトリ） |
| タグ・Release 作成 | 無料 |

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `.github/workflows/release-zenodo.yml` | 自動リリースワークフロー |
| `scripts/release/create-clean-archive.sh` | 手動クリーンアーカイブ作成 |
| `docs/specs/release-process.md` | リリースプロセス詳細 |
| `docs/specs/zenodo-doi-guide.md` | Zenodo 登録ガイド |
| `CITATION.cff` | 引用メタデータ |
| `CHANGELOG.md` | 変更履歴 |

---

## 使用例

### 例: v1.6.0 リリース

```
1. CITATION.cff の version を 1.6.0 に更新
2. CHANGELOG.md に 1.6.0 エントリを追加
3. コミット: "Bump version to 1.6.0"
4. タグ: git tag -a v1.6.0 -m "Release v1.6.0"
5. リリース: gh release create v1.6.0
6. Actions 実行確認
7. DOI 確認: 10.5281/zenodo.XXXXXXX
8. CITATION.cff を DOI で更新
9. コミット・プッシュ
```
