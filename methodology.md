# Japan Cannabinoid Trends — Methodology

**Project:** Japan Cannabinoid Trends
**Repository:** https://github.com/routeflags/japan-cannabinoid-trends
**Last Updated:** 2026-10-01

---

## 1. Project Overview

This repository maintains reproducible longitudinal datasets concerning cannabinoid-related trends in Japan. The project collects, processes, and analyzes data from multiple sources to track public interest in cannabinoids.

---

## 2. Research Question

> 日本国内におけるカンナビノイド関連トレンドを、複数データソースから縦断的に追跡する。

---

## 3. Data Sources

| ソース | 種別 | Study ID | ステータス |
|--------|------|----------|-----------|
| Google Trends | 市場全体検索 | `cbx-search-trends` | ACTIVE |
| Google Search Console | 自社サイト検索 | `cbx-search-trends` | ACTIVE |
| X (Twitter) | ソーシャル | `cbx-social-trends` | ACTIVE |
| YouTube | 動画 | `cbx-social-trends` | ACTIVE |
| COA | 製品分析 | `cbx-product-coa` | PLANNED |

---

## 4. Study Structure

各研究は `datasets/<study-id>/` 配下に独立して存在する。

```
datasets/
├── cbx-search-trends/     # Google Trends + GSC
├── cbx-social-trends/     # X + YouTube
├── cbx-liquid-online-trend/ # X 週次（PLANNED）
└── cbx-product-coa/       # COA 分析（PLANNED）
```

---

## 5. Methodology Principles

### 5.1 Reproducibility

- 収集パラメータを完全に記録
- run metadata を保存
- 方法論を公開

### 5.2 Provenance

- raw データは改変しない
- 処理パイプラインを明確に区別
- 変換ルールを文書化

### 5.3 Separation of Observation and Interpretation

- 事実（observed）と解釈（interpretation）を明確に分離
- 「所見」ラベルで解釈を表示
- 因果関係を主張しない

### 5.4 Limitations Disclosure

- データの制約を明記
- 不確実性を記載
- 代替解釈を検討

---

## 6. Data Collection

### 6.1 Google Trends

- **ツール:** google-trends-mcp (npm, v0.1.1)
- **エンドポイント:** 非公式（trends.google.com 内部 API）
- **パラメータ:** geo=JP, timeframe=today 12-m
- **注意:** 相対指数 (0-100)、低ボリュームクエリは閾値未満になる可能性

### 6.2 X (Twitter)

- **ツール:** Apify Actor `cPYLH3QT9GyzKhB4S`
- **パラメータ:** query, section, maxPages
- **注意:** シャドウバンの可能性、過去データ遡及不可

### 6.3 YouTube

- **ツール:** Apify Actor `gJvjeCYNraSfhIaNd`
- **パラメータ:** search_term, max_videos
- **注意:** 検索結果の非決定性、ページング重複

---

## 7. Data Processing

### 7.1 Pipeline Stages

```
SOURCE → COLLECTION → RAW → VALIDATION → INTERIM → PROCESSED → ANALYSIS
```

### 7.2 Deduplication

| ソース | キー | 方法 |
|--------|------|------|
| X | tweet_id | ユニーク ID で重複排除 |
| YouTube | videoId | ユニーク ID で重複排除 |
| Google Trends | date | 週次データで重複なし |

---

## 8. Quality Assurance

### 8.1 Validation Checklist

- [ ] スキーマ検証
- [ ] 日付範囲確認
- [ ] 件数整合性
- [ ] 欠損値確認
- [ ] メタデータ完全性

### 8.2 Variance Assessment

Google Trends は非決定的なため、同一日内で複数回収集してばらつきを記録する。

実績: ±3 ポイント（2026-10-01）

---

## 9. Limitations

### 9.1 Platform Limitations

| プラットフォーム | 制約 |
|-----------------|------|
| Google Trends | 非公式エンドポイント、相対指数、閾値 |
| X | シャドウバン、過去遡及不可 |
| YouTube | 検索非決定性、ページング重複 |

### 9.2 Research Limitations

- 慣習的サンプル（convenience sample）
- 単一クエリ（低ボリューム）
- 非ピアレビュー
- 商業的関連（利益相反あり）

---

## 10. Conflict of Interest

本プロジェクトの発行者（Routeflags Co., Ltd.）は、カンナビノイド製品を販売するEC事業を運営しています。この商業的関係は、データ選択・解釈に影響を及ぼす可能性があります。本リポジトリのデータ・方法論・制約は、独立した評価を可能にするために記載しています。

---

## 11. Citation

Citation format is defined in `CITATION.cff`.

Dataset: CBX Online Trend Dataset 2026
Version: 1.6.1
DOI: 10.5281/zenodo.23090163
License: CC-BY-4.0

---

## 12. Related Documentation

| ファイル | 内容 |
|---------|------|
| `datasets/*/methodology.md` | 各研究の詳細な方法論 |
| `docs/specs/raw-data-policy.md` | raw データ公開方針 |
| `docs/specs/sns-redistribution-assessment.md` | SNS 再配布権評価 |
| `CHANGELOG.md` | 変更履歴 |
| `CITATION.cff` | 引用メタデータ |
