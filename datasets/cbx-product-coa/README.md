# CBX Product COA

**Study ID:** cbx-product-coa
**Created:** 2026-10-01
**Status:** PLANNED
**Scope:** CBX 製品の COA（分析証明書）データ

---

## 概要

当店で販売している CBX 配合製品の原料について、米国の第三者分析機関による COA（分析証明書）を収集・分析する研究。

## 研究質問

> 市流通している CBX 配合製品の原料の純度・成分・THC 残留量はどうなっているか？

## データソース

| ソース | 分析機関 | ロット | 分析日 |
|--------|---------|--------|--------|
| Concentrate-Distillate | KCA Laboratories (KY, USA) | X-PPM-001 | 2026-05~06 |
| Concentrate-Distillate | Anresco Laboratories (CA, USA) | X-PPM-001 | 2026-05~06 |

## ディレクトリ構造

```
datasets/cbx-product-coa/
├── README.md
├── methodology.md      (未作成)
├── data/
│   └── raw/
│       └── coa/
│           ├── CBX1.pdf
│           └── CBX2.pdf
├── metadata/
└── analysis/
```

## 関連研究

| Study ID | 内容 | 関係 |
|----------|------|------|
| `cbx-social-trends` | SNS トレンド | 補完 |
| `cbx-search-trends` | GSC 検索データ | 補完 |

## 現在のリリース

- v1.0.0 (2026-10-01): COA データを `cbx-social-trends/` から分離
