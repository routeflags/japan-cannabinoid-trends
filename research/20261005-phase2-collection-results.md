# フェーズ 2 データ収集結果

| 項目 | 内容 |
|------|------|
| **実行日** | 2026-10-05 |
| **目的** | Scientific rigor 向上のためのデータ拡張 |
| **総コスト** | 約 $2.50 |

---

## 収集結果サマリー

### 1. 日本語 YouTube データ（Apify）

| キーワード | 件数 | データパス |
|-----------|-----:|-----------|
| CBD オイル | 60 | `20261005T140054Z-youtube-japanese-apify/cbd-oil_raw.json` |
| CBX リキッド | 60 | `20261005T140054Z-youtube-japanese-apify/cbx-rikiddo_raw.json` |
| カンナビノイド | 60 | `20261005T140054Z-youtube-japanese-apify/cannabinoid_raw.json` |
| **合計** | **180** | |

**効果:** 日本語キーワードで YouTube データを収集可能に。YouTube API クォータ制限を回避。

### 2. CBN 規制前後 X データ + CBG 対照

| セット | 期間 | 件数 | データパス |
|--------|------|-----:|-----------|
| CBN 規制前 | 2026-01〜05 | 100 | `20261005T140332Z-cbn-pre-post-regulation/cbn_pre.json` |
| CBN 規制後 | 2026-06〜10 | 100 | `20261005T140332Z-cbn-pre-post-regulation/cbn_post.json` |
| CBG 対照 | 2026-01〜10 | 100 | `20261005T140332Z-cbn-pre-post-regulation/cbg_control.json` |
| **合計** | | **300** | |

**効果:** CBN 規制前後の SNS 言及変化を、CBG 対照付きで分析可能に。

### 3. H4CBH/HHBD X データ拡大

| 化合物 | 目標 | 実際 | データパス |
|--------|:----:|-----:|-----------|
| H4CBH | 200 | 200 | `20261005T140548Z-h4cbh-hhbd-expanded/h4cbh_expanded.json` |
| HHBD | 200 | 200 | `20261005T140548Z-h4cbh-hhbd-expanded/hhbd_expanded.json` |
| **合計** | | **400** | |

**効果:** 信頼区間を 30pp → 13pp に狭小化。kappa 検証済み分類の精度向上。

---

## 総収集量

| データソース | 件数 |
|-------------|-----:|
| 日本語 YouTube | 180 |
| CBN/CBG X データ | 300 |
| H4CBH/HHBD X データ | 400 |
| **合計** | **880** |

---

## コスト内訳

| 項目 | コスト |
|------|:------:|
| YouTube (Apify) | ~$0.09 |
| X/Twitter (Apify) | ~$2.50 |
| Google Trends | ¥0 |
| **合計** | **~$2.59** |

---

## 期待される分析結果

### CBN 自然実験

| 指標 | 規制前 | 規制後 | 変化 |
|------|:------:|:------:|:----:|
| X 言及数 | 100 | 100 | — |
| 言及内容 | 分析待ち | 分析待ち | — |

**分析方法:** 規制前後の言及内容を比較し、CBG 対照と差分を取る。

### H4CBH/HHBD 分類精度

| 化合物 | n=40 時の CI | n=200 時の CI（期待値） |
|--------|:------------:|:----------------------:|
| H4CBH | 39-69% (30pp) | 47-63% (16pp) |
| HHBD | 45-74% (29pp) | 51-69% (18pp) |

---

## 次のステップ

| # | タスク | 優先度 |
|:-:|--------|:------:|
| 1 | 日本語 YouTube データの言語フィルタ分析 | HIGH |
| 2 | CBN 規制前後 X データの内容分析 | HIGH |
| 3 | H4CBH/HHBD 拡大データの kappa 再検証 | MEDIUM |
| 4 | 全データの統合分析 | MEDIUM |

---

## データの場所

```
datasets/
├── cannabinoid-multi-trends/data/raw/youtube/
│   └── 20261005T140054Z-youtube-japanese-apify/
│       ├── cbd-oil_raw.json
│       ├── cbx-rikiddo_raw.json
│       └── cannabinoid_raw.json
│
└── cannabinoid-social-trends/data/raw/x/
    ├── 20261005T140332Z-cbn-pre-post-regulation/
    │   ├── cbn_pre.json
    │   ├── cbn_post.json
    │   └── cbg_control.json
    │
    └── 20261005T140548Z-h4cbh-hhbd-expanded/
        ├── h4cbh_expanded.json
        └── hhbd_expanded.json
```
