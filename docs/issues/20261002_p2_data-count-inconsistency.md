# Issue: ドキュメント間のデータ件数の不整合

**ID:** ISS-20261002-008
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-02)
**対応:** メソドロジーを更新し、各集計値の意味を明確化

---

## 概要

X データ件数がドキュメント間で不一致だった。

## 解決策

メソドロジーに「X データ件数の説明」セクションを追加し、各集計値の意味を明確化した。

## 修正後の件数一覧

| 集計値 | 意味 | 場所 |
|--------|------|------|
| **2,376** | 日別収集の raw データ（重複多数） | `data/raw/x/202608/` |
| **147** | 日別収集の processed データ（tweet_id で重複排除済み） | `data/processed/x_cbx_202608_summary.csv` |
| **321** | 26週収集の主要週別ファイル合計（W01-W26） | `data/raw/x/26week/W*.json` |
| **451** | 26週収集の全ファイル合計（detail/full 含む） | `data/raw/x/26week/` |
| **291** | 26週収集のユニーク tweet_id 数（重複排除後） | 算出値 |

## 修正ファイル

- `datasets/cbx-social-trends/methodology.md`
  - §2 Data Sources: 件数を明確化
  - §2.1 X データ件数の説明: 新規追加
  - §4 Deduplication: 件数を修正
  - §8 Cost Tracking: 件数を修正

## 関連ファイル

- `datasets/cbx-social-trends/methodology.md`
