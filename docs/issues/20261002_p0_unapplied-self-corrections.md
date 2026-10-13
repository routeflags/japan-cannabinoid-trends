# Issue: 自己検出済み文書エラーの未修正

**ID:** ISS-20261002-002
**優先度:** P0 (Critical)
**検出日:** 2026-10-02
**検出方法:** 独立検証 (Cannabinoid Trend Whitepaper Validator)
**ステータス:** RESOLVED (2026-10-13)

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

---

## 解決 (2026-10-13)

4 件を現物確認した。3 件は既に修正済みで、1 件が残っていたため修正した。

| # | 対象 | 確認結果 |
|---|------|----------|
| 1 | X シャドウバン主張（未検証） | **修正済み**。`cbx_x_data_integrity.md` L48 は「シャドウバンによるものとは限らない」、L53 は「未検証」、L75 に修正注記あり |
| 2 | 過去データ遡及不可の主張 | **修正済み**。同ファイル L61 に「誤り」と修正注記、L125 / L160 にも反映 |
| 3 | 古いデータ件数「101件」 | **修正済み**。`cbx_data_collection_report.md` L51/L64 が 147件、L65 に修正注記あり |
| 4 | 26週レポートの古いデータ | **未修正だったため今回修正**（下記） |

### 項目 4 の詳細

対象ファイルの記載パスが誤っていた（本 issue は
`datasets/cbx-social-trends/analysis/x_26week_trend_report.md` としていたが、実際は
`datasets/x-26week-trends/analysis/x_26week_trend_report.md`）。

`datasets/x-26week-trends/analysis/x_26week_trend_report.md` は W23 / W26 を 0 件、
総件数を 251件 / 重複排除後 231件 としていたが、2026-10-01 に W23=33件 / W26=37件 が
再収集されている（`cbx-social-trends/methodology.md` §2.1 / §7.3）。更新した値:

| 項目 | 旧 | 新 | 根拠 |
|------|----|----|------|
| W23 | 0件 | 33件 | methodology §7.3（再収集 2026-10-01） |
| W26 | 0件 | 37件 | 同上 |
| 総取得件数 | 251件 | 321件 | methodology §2.1 の 321件と一致 |
| 重複排除後 | 231件 | 291件 | methodology §2.1 の 291件と一致 |
| 2026年8月 | 105件 | 138件 | W23 は 08/20-08/27 で全期間が8月 |
| 2026年9月（〜9/17） | 44件 | 81件 | W26 は 09/10-09/17 で全期間が9月 |

**導出の検算:** 週次表の合計も月次表の合計も 321 で一致する（2+100+138+81 = 321、
週次 26 週の合計 = 321）。再収集の事実と旧値は同ファイルの日付付き注記に記録した。

### 施行（再発防止）

`docs/issues/` の状態を機械検査する `validation.cli audit-issues` を追加した。issue の
ステータス・優先度の形式、終端ステータスの日付、ID の重複、そして **OPEN の P0 が
存在すれば CI を落とす**。本 issue が 11 日間 OPEN のまま誰にも気づかれなかったのは、
状態を読む仕組みが無かったためである。
