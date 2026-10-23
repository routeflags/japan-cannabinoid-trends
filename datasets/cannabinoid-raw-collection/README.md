# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`（2026-10-23 に改名）。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
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

**追跡される形（集計のみ）**: raw は Git 管理外（`**/data/raw/*`、例外は `google_trends` のみ）で、**ローカル証跡のみ**。代わりに次の 2 表を追跡する（生成: `python -m processing.cli youtube-export`、実装 [`src/processing/youtube_export.py`](../../src/processing/youtube_export.py)）。

| ファイル | 行 | 内容 |
|---|---|---|
| `data/processed/youtube_videos.csv` | 182 | 1 行 = 1 動画（`run_id` / `video_id` / `channel_title` / `title`）。**説明文は出力しない** |
| `data/processed/youtube_runs.csv` | 7 | 1 行 = 1 公開 run（検索語 / 収集時刻 / 動画行数 / error payload 数） |

- 上の **182 件**は `youtube_videos.csv` の行数と一致する（22+25+34+28+23+23+27）。表に出る run も同じ 7 つ。
- **説明文（`description`）は公開しない**: チャンネル運営者の連絡先メールが埋め込まれている事例があったため、追跡対象は ID・タイトル・チャンネル名だけにした（2026-10-23 の owner 判断）。
- **公開日は含まれない**: この収集ペイロードに投稿日が無いので、空列を作らずに落とした。
- **公開しない run は 2 表のどちらにも載せない**（2026-10-23）。除外した run には、本リポジトリが方針上使わない収集手段に由来するものや不完全系列が含まれるため、データ成果物の勘定に入れない。除外の判定と理由はコード（`src/processing/youtube_export.py` の `EXCLUSION_REASONS`）に閉じる。
- 生成は raw を要求するので、clone では再導出できない（`processing.cli audit-processed` は `not_reproducible_from_repository` と記録する。ルールはコードとテストで固定済み）。

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
