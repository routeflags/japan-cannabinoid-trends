# Raw Data Policy

**Effective Date:** 2026-10-01
**Version:** 1.0

---

## 1. Policy Statement

本リポジトリにおける raw データ（`data/raw/` 配下）の公開方針を定義する。

---

## 2. General Rule

**Raw データは gitignore 対象であり、既定では GitHub リポジトリに含めない。**

```
.gitignore:
  **/data/raw/*
  !**/data/raw/.gitkeep
```

---

## 3. Rationale

### 3.1 Raw Data Is Immutable

Raw データは収集時点の生データであり、改変すべきでない。gitignore は意図しない変更を防ぐ。

### 3.2 Redistribution Rights

一部の raw データ（X ツイート、YouTube メタデータ等）は、プラットフォームの利用規約により再配布が制限される。

詳細: `docs/specs/sns-redistribution-assessment.md`

### 3.3 Data Size

raw データは大容量になる可能性があり、リポジトリの管理コストを増加させる。

### 3.4 Privacy

raw データには個人情報（ユーザー名、投稿文等）が含まれる場合がある。

---

## 4. What Is Published

### 4.1 Processed Data (Public)

以下の processed データは git に含める：

| データ | 場所 | 内容 |
|--------|------|------|
| X 集計統計 | `data/processed/` | 週別投稿数、投稿者別統計、コンテンツ分類 |
| YouTube フィルタ済み | `data/processed/youtube_filtered_202607/` | タイトル、チャンネル、再生数（メタデータ） |
| Google Trends | `data/raw/google_trends/` | 相対指数（公開データのため raw を公開） |
| GSC | `data/raw/gsc/` | 自社サイトの検索データ（公開済み） |

### 4.2 Run Metadata (Public)

以下の run metadata は git に含める：

- 取得日時（collection_timestamp）
- クエリ条件（query parameters）
- 取得件数（record count）
- Actor ID、MCP サーバー情報
- フィルタ基準（inclusion/exclusion criteria）

### 4.3 Raw Data (Private)

以下の raw データは git に含めない：

- X ツイート本文（raw text）
- X ユーザー名（usernames）
- YouTube 動画ファイル
- Apify レスポンス全文

---

## 5. How to Access Raw Data

### 5.1 For Research Purposes

研究者が必要な場合、以下により raw データにアクセスできる：

1. **再収集:** 収集方法論（methodology.md）に従い、同じパラメータで再収集
2. **引用:** 公開済みの集計データを引用
3. **リクエスト:** 研究目的で raw データへのアクセスをリクエスト

### 5.2 Reproducibility

Raw データが git に含まれないため、再現性は以下の要素に依存する：

- 収集方法論の詳細さ（methodology.md）
- run metadata の完全性
- 公開済み processed データとの整合性

**注意:** Google Trends は非公式エンドポイントを使用しており、同一クエリでも結果が変動する場合がある。再収集しても同一の値が得られるとは限らない。

---

## 6. Versioning and DOI

### 6.1 DOI Archive Contents

Zenodo にデプロイされる DOI アーカイブには以下を含める：

✅ **含める:**
- processed データ（集計統計、フィルタ済みメタデータ）
- run metadata
- methodology.md
- LICENSE
- CITATION.cff
- README.md

❌ **含めない:**
- raw データ（X ツイート本文、YouTube 動画ファイル等）
- 認証情報（.env、API キー等）

### 6.2 Citation

DOI を引用する際は、公開済みの集計データとメタデータを参照する。raw データの引用が必要な場合は、再収集方法論を併記する。

---

## 7. Updates to This Policy

このポリシーは、法的要件の変更、プラットフォーム TOS の変更、またはリポジトリ管理方針の変更に応じて更新される。

**更新履歴:**
- 2026-10-01: 初版作成
