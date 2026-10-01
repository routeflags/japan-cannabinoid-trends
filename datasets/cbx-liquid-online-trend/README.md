# CBX Liquid Online Trend

**Study ID:** cbx-liquid-online-trend
**Created:** 2026-10-01
**Status:** PLANNED
**Scope:** X (Twitter) のみ、クエリ `CBX リキッド` に特化

---

## 概要

CBX リキッドという単一製品カテゴリに特化して、X (Twitter) 上の言及を週次で追跡する研究。

## 研究質問

> 2026年の日本国内において、X (Twitter) 上で「CBX リキッド」に言及する投稿の量・内容・時間的推移は何か？

## データソース

| ソース | Actor ID | 収集頻度 |
|--------|----------|---------|
| X (Twitter) Search | `cPYLH3QT9GyzKhB4S` | 週次 |

## ディレクトリ構造

```
datasets/cbx-liquid-online-trend/
├── README.md           ← このファイル
├── methodology.md      ← 収集方法の詳細
├── data/
│   ├── raw/x/          ← 収集生データ（run-id ごと）
│   ├── interim/        ← 中間変換データ
│   └── processed/      ← 分析用データ
├── metadata/
│   └── runs/           ← 収集実行メタデータ
└── analysis/           ← 分析結果
```

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cbx-social-trends` | 複数 SNS の CBX トレンド | 上位（参考） |
| `cbx-search-trends` | GSC 検索データ | 補完 |
| `cbx-product-coa` | COA 分析結果 | 補完 |

## 現在のリリース

- v1.0.0 (2026-10-01): 研究計画書作成、ディレクトリ構築
