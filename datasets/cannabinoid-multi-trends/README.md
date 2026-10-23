# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-multi-trends`（ID とディレクトリ名は安定識別子。raw の `run_metadata.json` が参照する）
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

既存の CBX/H4CBH/HHBD データに加え、主要カンナビノイド化合物の市場トレンド・SNS 言及・動画コンテンツの**原記録を集める研究**。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本国内において、主要カンナビノイド化合物（CBD, THC, CBG, HHC, THCV, THC-O, THCH）の検索需要・SNS 言及・動画コンテンツはどう推移しているか？

## 対象化合物

| # | キーワード | カテゴリ | Google Trends | X | YouTube |
|---|-----------|---------|:------------:|:-:|:-------:|
| 1 | CBD | Major Phytocannabinoid | ✅ | ✅ | ✅ |
| 2 | THC | Major Phytocannabinoid | ✅ | ✅ | ✅ |
| 3 | CBG | Minor Phytocannabinoid | ✅ | ✅ | ✅ |
| 4 | HHC | Semi-Synthetic | ✅ | ✅ | ✅ |
| 5 | THCV | Minor Phytocannabinoid | ❌ | ✅ | ✅ |
| 6 | THC-O | Semi-Synthetic | ❌ | ✅ | ❌ |
| 7 | THCH | Minor Phytocannabinoid | ✅ | ✅ | ❌ |

> 上の表は **2026-10-02 の初回収集（12ヶ月）の範囲**。その後、5年を中心に収蔵範囲が広がっており、現在の raw（37 runs）には次も含む。範囲の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。
>
> - 5年系列（週次）: THC-O, H4CBH, HHBD, CBN, CRDH, CRDP, HHCH, CBD（CBD は 2026-10-15 再取得）
> - 5年 baseline（サマリーのみ）: CBD, THC, CBG, HHC, THCV — 週次系列を収蔵していないため raw から検算できない
> - 比較セットと共通スケール比較（`common-scale-*`）、表記事前調査、および「リキッド」系クエリの 12ヶ月 / 5年
>
> THCV と THC-O の Google Trends は上表で ❌ だが、THCV は 5年 baseline、THC-O は 5年系列で存在する（12ヶ月単独の取得がないだけ）。

## データソース

| ソース | ツール | コスト | 状態 |
|--------|--------|--------|------|
| Google Trends | google-trends-mcp | 無料 | ✅ 収集完了 |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ~$0.80 | ✅ 収集完了 |
| YouTube | Apify `gJvjeCYNraSfhIaNd` | ~$0.09 | ✅ 収集完了 |

> **関連データセットとの役割分担**: 本データセットは**トレンド分析**（複数プラットフォームの出現・時系列分布）が目的。
> YouTube 検索結果の**一貫性・再現性検証**は [`datasets/youtube-consistency/`](../youtube-consistency/) が担当しており、
> そちらは別の Actor（`h7sDV53CddomktSi5` / streamers/youtube-scraper）を使う。両者は目的・ Actor・格納形式（本件は raw ファイル、同件は SQLite）が異なるため重複ではなく分業である。

## 収集結果（2026-10-02）

### Google Trends

| キーワード | 週数 | 平均スコア | 備考 |
|-----------|:----:|:---------:|------|
| CBD | 52 | 47 | 比較セットで最高 |
| THC | 52 | 62 | 単独では高値 |
| CBG | 52 | 60 | 中程度 |
| HHC | 52 | 40 | 低ボリューム |
| THCH | 52 | 5 | 極低ボリューム |
| THCV | — | — | データなし |
| THC-O | — | — | データなし |

### X (Twitter)

| キーワード | 件数 |
|-----------|:----:|
| CBD | 60 |
| THC | 60 |
| CBG | 40 |
| HHC | 40 |
| THCV | 40 |
| THC-O | 40 |
| THCH | 36 |
| **合計** | **316** |

### YouTube

| キーワード | 件数 |
|-----------|:----:|
| CBD | 22 |
| THC | 25 |
| CBG | 34 |
| HHC | 28 |
| THCV | 23 |
| CBD オイル | 23 |
| THC オイル | 27 |
| **合計** | **182** |

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE | 2026-10-02 |
| COMPLETED | — |

## 関連

- 計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 収集サマリー: `data/processed/collection-summary.md`
- 既存研究: `datasets/cbx-search-trends/`, `datasets/cbx-social-trends/`
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
