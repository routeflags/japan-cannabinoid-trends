# CBX Search Trends

**Study ID:** cbx-search-trends
**Created:** 2026-10-01
**Status:** ACTIVE
**Scope:** Google Search Console + Google Trends による CBX 検索需要データ

---

## 概要

当社サイト（thch-vape.shop）の Google Search Console データと、Google Trends の市場全体検索データから、CBX 関連の検索需要を分析する研究。

## 研究質問

> 日本国内において、CBX 関連クエリの検索需要はどう推移しているか？
> - 自社サイト: GSC データ（クリック・インプレッション・順位）
> - 市場全体: Google Trends データ（相対興味度 0-100）

## データソース

| ソース | 期間 | 件数 | ステータス |
|--------|------|------|-----------|
| Google Search Console | 2026-07 (月次) | 200 クエリ（うち CBX 関連 6 件） | ✅ 取得済み |
| Google Trends | 2026-09-28 ~ 2026-10-03 | 週次 52 週分 | ✅ 取得済み (2026-10-01) |

## Google Trends 初回収集結果（2026-10-01）

### キーワード: 「CBX リキッド」（日本、過去12ヶ月）

| 期間 | 興味度スコア |
|------|-------------|
| 2025-09 ~ 2026-09-12 | **0**（データなし） |
| 2026-09-13 ~ 09-19 | **44** |
| 2026-09-20 ~ 09-26 | **100**（ピーク） |
| 2026-09-27 ~ 10-03 | **92** |

**考察（意見）:** CBX リキッドの検索需要は 2026年9月中旬から急上昇。販売開始（2026年7月）から2ヶ月ヶ月遅れて検索需要が顕在化した可能性。

### キーワード比較（「CBX」「CBX リキッド」「CBD リキッド」）

| キーワード | 平均興味度 | 特徴 |
|-----------|-----------|------|
| CBX | **68** | 通年で安定。9月中旬にピーク (100) |
| CBD リキッド | 13 | 低水準で安定 |
| CBX リキッド | 0（比較時） | 9月中旬から僅かにデータあり |

**注意:** Google Trends の値は相対指数。「CBX リキッド」単独クエリでは 44-100 と高く見えるが、比較クエリでは「CBX」に比べ大幅に低い。

## ディレクトリ構造

```
datasets/cbx-search-trends/
├── README.md
├── methodology.md      (未作成)
├── data/
│   └── raw/
│       ├── gsc/
│       │   └── 202607_queries.csv
│       └── google_trends/
│           └── 20261001T115959Z-google-trends-cbx-rikiddo/
│               ├── records.json
│               ├── comparison.json
│               ├── related_queries.json
│               └── run_metadata.json
├── metadata/
└── analysis/
```

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cbx-social-trends` | SNS トレンド | 補完 |
| `cbx-product-coa` | COA 分析 | 補完 |
| `cbx-liquid-online-trend` | X (Twitter) 言及 | 補完（別指標） |

## 現在のリリース

- v1.0.0 (2026-10-01): GSC データを `cbx-social-trends/` から分離
- v1.1.0 (2026-10-01): Google Trends 初回収集（CBX リキッド, 日本, 12ヶ月）
