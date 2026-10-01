# Issue: 自己検出済み文書エラーの未修正

**ID:** ISS-20261002-002
**優先度:** P0 (Critical)
**検出日:** 2026-10-02
**検出方法:** 独立検証 (Cannabinoid Trend Whitepaper Validator)
**ステータス:** OPEN

---

## 概要

チーム自身が収集計画で検出・修正を計画した文書エラーが、実際の文書に反映されていない。

## 影響

**既知の誤情報を含む研究アーチファクトを公開している。プロベナンスチェーン全体の信頼性を損なう。**

## 検出されたエラー

### エラー 1: X シャドウバン主張（未検証）

**ファイル:** `datasets/cbx-social-trends/analysis/cbx_x_data_integrity.md` L47

**現在の記載:**
> X は…完全にブロックしている

**問題:** 収集計画 (`x-data-collection-plan.md` L15-18) で、これは誤りまたは未検証と判明。`since:/until:` 演算子を使用した週次収集は正常に動作している。

**修正後の記載:**
> X のシャドウバンは特定されていない。過去データの遡及取得は `since:/until:` 演算子で可能。

### エラー 2: 過去データ遡及不可の主張

**ファイル:** `datasets/cbx-social-trends/analysis/cbx_x_data_integrity.md` L55

**現在の記載:**
> 過去データ…遡及取得不可

**問題:** 収集計画で `since:/until:` での取得が可能と判明。実際に 26週分のデータを収集済み。

**修正後の記載:**
> 過去データの遡及取得は `since:/until:` 演算子で可能。ただし完全な網羅性は保証されない。

### エラー 3: 古いデータ件数「101件」

**ファイル:** `datasets/cbx-social-trends/analysis/cbx_data_collection_report.md` L62

**現在の記載:** 101件

**修正後の値:** 実際の処理済みデータ件数に更新（147件）

### エラー 4: 26週レポートの古いデータ

**ファイル:** `datasets/cbx-social-trends/analysis/x_26week_trend_report.md`

**問題:**
- W23 と W26 が 0 件と記載 → 再収集済み（33件/37件）
- 総件数が 251/231 件と記載 → 実際の値と不一致

**修正:** 再収集後の値に更新し、再収集の事実を明記

## 修正手順

1. `cbx_x_data_integrity.md` L47, L55 を修正
2. `cbx_data_collection_report.md` L62 を修正
3. `x_26week_trend_report.md` の W23/W26 と総件数を更新
4. 修正内容を CHANGELOG に記録

## 関連

- 収集計画: `datasets/cbx-social-trends/analysis/x-data-collection-plan.md`
- 検証レポート: 独立検証 2026-10-02 (Critical Issue 2)
