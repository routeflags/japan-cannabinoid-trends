# CBX Search Trends

**Study ID:** cbx-search-trends
**Created:** 2026-10-01
**Status:** PLANNED
**Scope:** Google Search Console による CBX 検索需要データ

---

## 概要

当社サイト（thch-vape.shop）の Google Search Console データから、CBX 関連の検索クエリを抽出・分析する研究。

## 研究質問

> 日本国内の当社サイトにおいて、CBX 関連クエリの検索需要・クリック率・順位はどう推移しているか？

## データソース

| ソース | 期間 | 件数 |
|--------|------|------|
| Google Search Console | 2026-07 (月次) | 200 クエリ（うち CBX 関連 6 件） |

## ディレクトリ構造

```
datasets/cbx-search-trends/
├── README.md
├── methodology.md      (未作成)
├── data/
│   └── raw/
│       └── gsc/
│           └── 202607_queries.csv
├── metadata/
└── analysis/
```

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cbx-social-trends` | SNS トレンド | 補完 |
| `cbx-product-coa` | COA 分析 | 補完 |

## 現在のリリース

- v1.0.0 (2026-10-01): GSC データを `cbx-social-trends/` から分離
