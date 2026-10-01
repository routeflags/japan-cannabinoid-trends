# CBX Social Media Trends

**Study ID:** cbx-social-trends
**Created:** 2026-09-18
**Last Updated:** 2026-10-01
**Status:** ACTIVE
**Scope:** 複数 SNS プラットフォームの CBX トレンドを横断的に収集

---

## 概要

X (Twitter)、YouTube、Instagram、TikTok における CBX 関連コンテンツのトレンドを収集・分析する研究。

## 研究質問

> 2026年の日本国内において、複数 SNS プラットフォーム上で CBX に言及する投稿の量・内容・時間的推移は何か？

## データソース

| ソース | Actor ID | 件数 | 備考 |
|--------|----------|------|------|
| X (Twitter) — 日別 | `cPYLH3QT9GyzKhB4S` | 2,376 (raw) / 147 (processed) | 2026-08-01~09-08 |
| X (Twitter) — 26週 | `cPYLH3QT9GyzKhB4S` | 381 (raw) | 2026-03-19~09-17 |
| YouTube | `gJvjeCYNraSfhIaNd` | **24件 (フィルタ後、CBX関連: 24件)** | ✅ 再取得成功 2026-10-01 |
| Instagram | `TxU0ZBQIHdR20dr9C` | 6 (CBX関連: 0) | 要再取得 |
| TikTok | `jQfZ1h9FrcWcliKZX` | 20 (description空) | 要再取得 |

## ディレクトリ構造

```
datasets/cbx-social-trends/
├── README.md           ← このファイル
├── methodology.md      ← 収集方法の詳細
├── data/
│   ├── raw/
│   │   ├── x/          ← X (Twitter) 生データ
│   │   ├── youtube/    ← YouTube 生データ
│   │   ├── instagram/  ← Instagram 生データ
│   │   └── tiktok/     ← TikTok 生データ
│   ├── interim/
│   └── processed/
├── metadata/
└── analysis/
```

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cbx-liquid-online-trend` | X のみ、`CBX リキッド` クエリに特化 | 下位（詳細） |
| `cbx-search-trends` | GSC 検索データ | 補完 |
| `cbx-product-coa` | COA 分析結果 | 補完 |

## 既知の問題

| 問題 | 影響 | 対策 | 状態 |
|------|------|------|------|
| ~~YouTube が CBX 非関連~~ | ~~クロスプラットフォーム分析不可~~ | クエリ修正で再取得 | ✅ **解決済み** (2026-10-01) |
| Instagram が CBX 非関連 | クロスプラットフォーム分析不可 | クエリ修正で再取得 | ⏳ 未対応 |
| TikTok description 空 | データ品質低下 | クエリ修正で再取得 | ⏳ 未対応 |
| 26週データに空週多数 | 長期トレンド分析困難 | 空週の再取得 | ⏳ 未対応 |

## 現在のリリース

- v1.2.1 (2026-10-01): YouTube 全件取得（26件ユニーク → フィルタ後24件）
- v1.2.0 (2026-10-01): YouTube 再取得成功（CBX リキッド クエリ、19/20件がCBX関連）
- v1.1.0 (2026-10-01): Study ID を `cbx-x-trends` → `cbx-social-trends` に改名。GSC/COA データを分離。
- v1.0.0 (2026-09-18): 初期データ収集
