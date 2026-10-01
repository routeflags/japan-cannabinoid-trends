# Issue: TikTok が「一次データ」ラベルで品質問題を抱えている

**ID:** ISS-20261002-005
**優先度:** P1 (High)
**検出日:** 2026-10-02
**検出方法:** 独立検証 (Cannabinoid Trend Whitepaper Validator)
**ステータス:** RESOLVED (2026-10-02)
**対応:** Option A — ラベルを「参考データ」に変更

---

## 概要

ガイドページが TikTok を「一次データ」としてラベル付けしているが、CBX 関連度が不明であり、品質が不十分である。

## 影響

**「一次データ」というラベルが、データの信頼性を過大に印象づける可能性がある。**

## 検出された問題

### ファイル: `datasets/cbx-social-trends/methodology.md` L24-25

- Instagram: CBX 関連結果 **0件**
- TikTok: キャプションが空、「要再取得」

### ファイル: `publication/guide_cbx_rewrite.html` L1050-1053

```
一次データ: TikTok
...CBX 関連度は不明です
```

> 「CBX 関連度は不明」と明記しながら「一次データ」とラベル付けするのは矛盾。

## 修正手順

### Option A: ラベルを変更する

```
一次データ → 参考データ（品質未確認）
```

### Option B: セクションを一時的に非表示にする

- CBX 関連データが収集できるまで TikTok セクションを非表示
- 再収集後に有効化

### Option C: 再収集する

- キーワードを変更して再収集（例: `CBX カンナビノイド`, `H4CBH リキッド`）
- 収集成功後に「一次データ」ラベルを付与

## 推奨

**Option A を即座に実施、Option C を中期的対応として実施**
- 現状のラベルは不正確
- 再収集で品質が確認できた場合のみ「一次データ」に戻す

## 関連

- ガイドページ: `publication/guide_cbx_rewrite.html` L1050-1053
- メソドロジー: `datasets/cbx-social-trends/methodology.md` L24-25
- 検証レポート: 独立検証 2026-10-02 (High-Risk Issue 5)
