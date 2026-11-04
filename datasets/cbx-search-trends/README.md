# CBX Search Trends

**Study ID:** cbx-search-trends
**Created:** 2026-10-01
**Status:** ACTIVE
**Scope:** Google Search Console + Google Trends による CBX / H4CBH / HHBD 検索需要データ

---

## 概要

当社サイト（thch-vape.shop）の Google Search Console データと、Google Trends の市場全体検索データから、CBX / H4CBH / HHBD 関連の検索需要を分析する研究。

## 研究質問

> 日本国内において、CBX / H4CBH / HHBD 関連クエリの検索需要はどう推移しているか？
> - 自社サイト: GSC データ（クリック・インプレッション・順位）
> - 市場全体: Google Trends データ（相対興味度 0-100）

## データソース

本 study が今もつ raw は **Google Search Console だけ**。**CBX の YouTube 観測（`CBX リキッド`）は 2026-11-01 の owner 決定**により、**CBX の Google Trends raw は 2026-11-04 の owner 決定**により、それぞれ [`datasets/cannabinoid-raw-collection/`](../cannabinoid-raw-collection/) が所有する。Google Trends の移管は run id と payload バイトを変えずに行い、観測のやり直しではない（[`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)、[cannabinoid-raw-collection/methodology.md §2.1.6](../cannabinoid-raw-collection/methodology.md)）。**本 study は Google Trends の二重の正本を持たない。**

| ソース | 期間 | 件数 | ステータス |
|--------|------|------|-----------|
| Google Search Console | 2026-07 (月次) | 200 クエリ（うち CBX 関連 6 件） | ✅ 取得済み（本 study の raw） |
| Google Trends (CBX リキッド) | 2025-09 ~ 2026-10 | 週次 52 週分 | ✅ 取得済み (2026-10-01)。raw は cannabinoid-raw-collection |
| Google Trends (H4CBH) | 2025-09 ~ 2026-10 | 週次 52 週分 | ✅ 取得済み (2026-10-01)。同上 |
| Google Trends (HHBD) | 2025-09 ~ 2026-10 | 週次 52 週分 | ✅ 取得済み (2026-10-01)。同上 |

## Google Trends 収集結果（2026-10-01）

### 1. キーワード別サマリー

| キーワード | 単独平均 | 比較平均 | ピーク | データ開始 | 特徴 |
|-----------|---------|---------|--------|-----------|------|
| **CBX** | 68 | **68** | 100 (2026-09-13週) | 通年 | 通年安定、9月中旬に急騰 |
| **H4CBH** | 56 | 13 | 100 (2026-07-26週) | 通年 | 通年データあり、夏にピーク |
| **HHBD** | 33 | 7 | 100 (2025-12-07週) | 2025-12 | 2025年12月に初出、以降断続的 |
| **CBX リキッド** | 44-92 | 0 | 100 (2026-09-20週) | 2026-09 | 9月中旬から急上昇 |

### 2. CBX リキッド（日本、過去12ヶ月）

| 期間 | 興味度スコア |
|------|-------------|
| 2025-09 ~ 2026-09-12 | **0**（データなし） |
| 2026-09-13 ~ 09-19 | **44** |
| 2026-09-20 ~ 09-26 | **100**（ピーク） |
| 2026-09-27 ~ 10-03 | **92** |

**考察（意見）:** CBX リキッドの検索需要は 2026年9月中旬から急上昇。販売開始（2026年7月）から2ヶ月遅れて検索需要が顕在化した可能性。

### 3. H4CBH（日本、過去12ヶ月）

| 項目 | 値 |
|------|-----|
| 単独クエリ平均 | **56** |
| 比較クエリ平均 | **13** |
| ピーク | **100**（2026-07-26 ~ 08-01） |
| データあり週 | 44 / 52 週 |
| 0 の週 | 8 週（閾値未満） |

**月別傾向（意見）:**
- 2025-10~12: 40-78 で安定
- 2026-01~03: 0 が混在するが概ね 50-80
- 2026-04~06: 50-91 で上昇傾向
- 2026-07~08: 55-100 でピーク
- 2026-09: 40-77 でやや低下

### 4. HHBD（日本、過去12ヶ月）

| 項目 | 値 |
|------|-----|
| 単独クエリ平均 | **33** |
| 比較クエリ平均 | **7** |
| ピーク | **100**（2025-12-07 ~ 12-13） |
| データ開始 | **2025-11-30** |
| データあり週 | 38 / 52 週 |

**考察（意見）:** HHBD は 2025年12月上旬に急騰（初出荷・話題化か）し、以降は 30-60 で推移。2026年8月以降は 0 の週が増加。

### 5. キーワード比較（CBX / H4CBH / HHBD / CBX リキッド）

| 順位 | キーワード | 平均興味度 | 評価 |
|------|-----------|-----------|------|
| 1 | **CBX** | **68** | 圧倒的に高い。通年安定 |
| 2 | H4CBH | 13 | 中程度。夏にやや上昇 |
| 3 | HHBD | 7 | 低い。2025-12 のピークのみ突出 |
| 4 | CBX リキッド | 0 | 比較では検出限界。9月から僅か |

**注意:** Google Trends の値は相対指数。「H4CBH」「HHBD」単独クエリでは 30-100 と高く見えるが、比較クエリでは「CBX」に比べ大幅に低い。

## ディレクトリ構造

```
datasets/cbx-search-trends/
├── README.md
├── methodology.md
├── data/
│   └── raw/
│       └── gsc/
│           └── 202607_queries.csv
├── metadata/
└── analysis/
```

Google Trends の run（`20261001T115959Z-google-trends-cbx-rikiddo` など 8 件）は
2026-11-04 に `datasets/cannabinoid-raw-collection/data/raw/google_trends/` へ移管した。

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cannabinoid-raw-collection` | 成分横断の Google Trends / X / YouTube raw | CBX の YouTube（`CBX リキッド`）と **Google Trends raw 8 run は同 study が所有**（本 study は Google Trends の正本を持たない） |
| `cbx-social-trends` | SNS トレンド | 補完 |
| `cbx-product-coa` | COA 分析 | 補完 |
| `cbx-liquid-online-trend` | X (Twitter) 言及 | 補完（別指標） |

## 現在のリリース

- v1.0.0 (2026-10-01): GSC データを `cbx-social-trends/` から分離
- v1.1.0 (2026-10-01): Google Trends 初回収集（CBX リキッド, 日本, 12ヶ月）
- v1.2.0 (2026-10-01): Google Trends 収集拡張（H4CBH, HHBD, 4キーワード比較）
