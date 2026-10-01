# Issue: 機械可読キーワード辞書が存在しない

**ID:** ISS-20261002-013
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-02)

## 概要

検証フレームワークは機械可読キーワード辞書を要求しているが、キーワードは散文形式のメソドロジー内にのみ存在。

## 修正手順

1. `metadata/keywords.yaml` を作成
2. 各カンナビノイド（CBX, H4CBH, HHBD, CBD 等）のキーワードを定義
3. 多義性フラグと包含/除外注記を追加

## 例

```yaml
CBX:
  keywords:
    - "CBX"
    - "CBX リキッド"
    - "CBX カンナビノイド"
  polysemy_warning: "ホンダ CBX400F バイクと混同される可能性あり"
  discriminating_queries:
    - "CBX 大麻"
    - "CBX カンナビノイド"
```

## 関連ファイル

- `datasets/cbx-search-trends/methodology.md`
