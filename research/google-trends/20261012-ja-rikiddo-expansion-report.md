# 日本語リキッド・クエリー拡張 取得レポート

- 調査ID: GTJA-20261012
- 作成日: 2026-10-12
- 対象: 日本語「○○ リキッド」13語（スペースあり表記）＋比較クエリー JA-1〜JA-4
- 収集源: Google Trends（google-trends-mcp v0.1.1）、geo=JP
- 研究: cannabinoid-raw-collection

## 1. 対象クエリー

Phase A（主要5語、12ヶ月）: CBD / THC / CBG / CBN / HHC ＋「リキッド」
Phase B（残り8語、12ヶ月）: THCV / THC-O / THCH / H4CBH / HHBD / HHCH / CRDP / CRDH ＋「リキッド」
5年系列（主要5語）: CBD / THC / CBG / CBN / HHC ＋「リキッド」
比較クエリー: JA-1（CBX・CBD・THC・CBG・CBN）、JA-2（CBX・CBD・HHC・THCV・THC-O）、JA-3（CBX・CBD・THCH・H4CBH・HHBD）、JA-4（CBX・CBD・HHCH・CRDP・CRDH）

## 2. 表記ゆれプレ調査（notation-presurvey）

- 「CBD リキッド」（スペースあり）vs「CBDリキッド」（スペースなし）: 平均 58 vs 58 で同等。週次推移は連動し、どちらか一方が 0 になる週が散発（低ボリューム語特有の断続表示）。本調査ではスペースあり表記を維持する。
- 「THC-O リキッド」vs「THC-Oリキッド」: 両表記とも no-data。表記ゆれの判定不能（需要の有無自体が閾値以下）。
- 「CBD リキッド」vs「CBD オイル」: 平均 25 vs 62 でオイルが優勢。ただしこれは表記ゆれではなく製品カテゴリ差（オイル製品とリキッド製品は別商材）のため、リキッド軸の需要として合算しない。

## 3. Phase A 結果（12ヶ月・単独取得）

| 語 | 平均 | ピーク | ゼロ週数（/53週） | JA-1 比較値 |
|---|---:|---:|---:|---:|
| CBD リキッド | 64.02 | 100 | 3 | 64.0 |
| THC リキッド | 3.51 | 100 | 51 | 0.4 |
| CBG リキッド | 3.60 | 100 | 51 | 0.2 |
| CBN リキッド | 5.96 | 100 | 48 | 2.5 |
| HHC リキッド | no-data | — | — | 0.0（JA-2 でも 0.0） |
| CBX リキッド（JA-1 のみ） | — | — | — | 3.1 |

- 単独取得のピーク 100 は各語の系列内正規化によるもので、語間比較には JA-1 比較値を用いる。
- JA-1 では CBD が一貫して最高（平均 64.0）、CBX 3.1、CBN 2.5、THC 0.4、CBG 0.2。
- THC・CBG・CBN の単独系列は大半の週が 0 で、非ゼロ週に 95〜100 のスパイクが立つ断続型（低ボリューム語の典型）。

## 4. 非決定性（再取得）結果

Phase A を約12分後に同一条件で再取得し差分を計算（repeat_diff.json）。

- 単独4語（CBD・THC・CBG・CBN）: 履歴週は完全一致。変動は最新週のみ（CBD 1週、差 +3）。THC・CBG・CBN は 53週すべて一致。
- JA-1 比較: 265セル中 2セルが変動。いずれも最新週（Oct 11–17, 2026）で CBX 31→23、CBD 59→64。
- HHC リキッド: 両 run とも no-data を再現。zero_status を unknown → below_threshold に確定。

## 5. Phase B 結果（12ヶ月・単独取得＋JA-2〜JA-4）

| 語 | 平均 | ピーク | ゼロ週数（/53週） | 状態 |
|---|---:|---:|---:|---|
| THCH リキッド | 2.32 | 100 | 50 | low_volume |
| H4CBH リキッド | 4.17 | 100 | 50 | low_volume |
| HHBD リキッド | 3.72 | 100 | 51 | low_volume |
| HHCH リキッド | 1.89 | 100 | 52 | low_volume |
| THCV リキッド | no-data | — | — | unknown |
| THC-O リキッド | no-data | — | — | unknown |
| CRDP リキッド | no-data | — | — | unknown |
| CRDH リキッド | no-data | — | — | unknown |

| 比較 | CBX | CBD | その他 |
|---|---:|---:|---|
| JA-2 | 3.0 | 64.0 | HHC 0.0、THCV 0.0、THC-O 0.0 |
| JA-3 | 3.0 | 64.0 | THCH 1.0、H4CBH 0.0、HHBD 0.0 |
| JA-4 | 3.0 | 64.0 | HHCH 1.0、CRDP 0.0、CRDH 0.0 |

- 取得済み4語はいずれも断続型の低ボリューム系列。JA-3/JA-4 で THCH・HHCH が 1.0 を記録し、比較スケール上でも微弱ながら検出された。
- no-data 4語は単独・比較の双方でゼロのため unknown とし、ゼロ需要とは断定しない。

## 6. 5年系列結果（主要5語）

| 語 | 週数 | 平均 | ピーク | 初出（初非ゼロ週） |
|---|---:|---:|---:|---|
| CBD リキッド | 262 | 36.53 | 100 | 2021-10-10 |
| THC リキッド | 262 | 8.55 | 100 | 2021-10-10 |
| CBN リキッド | 262 | 4.40 | 100 | 2021-10-10 |
| HHC リキッド | 262 | 2.99 | 100 | 2021-12-05 |
| CBG リキッド | 262 | 0.68 | 100 | 2024-02-04 |

- CBD-004（CBD 5年 raw 未収蔵）の解消: 本 run で CBD リキッド 5年 262点の raw タイムラインを取得・保存した。既存 summary は上書きしていない。
- CBG は 2024-02-04 が初出で、5語中最も遅い立ち上がり。HHC は 2021-12-05 に初出。
- 取得時に CBD の初回試行で HTTP 429 が発生し、約5分 backoff 後の再試行で全系列を取得。run_metadata.json に記録済み。

## 7. 日本語需要の所見（今回取得値のみ）

- 12ヶ月・日本語単独取得では CBD（平均 64.02）が突出し、CBN（5.96）・CBG（3.60）・THC（3.51）が一桁台で追随する構造。JA-1 比較でも順位は同一（CBD 64.0 > CBX 3.1 > CBN 2.5 > THC 0.4 > CBG 0.2）。
- 英語クエリーの取得は本調査の範囲外であり、言語間の直接比較は行わない。Google Trends の指数は取得条件ごとに正規化される相対値のため、別 run・別言語の数値との大小比較には使えない。
- 5年平均では CBD 36.53 に対し THC 8.55、CBN 4.40、HHC 2.99、CBG 0.68。長期でも CBD 中心の構造は変わらない。

## 8. 限定事項

- すべての値は Google Trends の相対指数（0–100）であり、絶対検索数ではない。単独取得と比較取得のスケールは異なる。
- no-data 4語（THCV・THC-O・CRDP・CRDH、12ヶ月）は unknown とし、需要ゼロとは解釈しない。HHC のみ 2 run 再現により below_threshold を確定。
- 低ボリューム語は断続表示（ゼロ週とスパイク週の混在）となり、平均値はスパイク位置に強く依存する。週次値の再現性は履歴週で確認済みだが、最新週は変動しうる。
- 相対指数のため、因果の推論には使わない（時系列の前後関係からの原因断定を避ける）。

## 9. run-id 一覧と保存パス

| run-id | 内容 | 保存パス |
|---|---|---|
| 20261012T054920Z-google-trends-notation-presurvey | 表記ゆれ3比較 | datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T054920Z-google-trends-notation-presurvey/ |
| 20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m | Phase A 主要5語＋JA-1 | datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m/ |
| 20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m | Phase A 再取得＋差分 | datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m/ |
| 20261012T061614Z-google-trends-ja-rikiddo-phase-b-12m | Phase B 8語＋JA-2〜JA-4 | datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T061614Z-google-trends-ja-rikiddo-phase-b-12m/ |
| 20261012T064246Z-google-trends-ja-rikiddo-5y-main5 | 5年 主要5語 | datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T064246Z-google-trends-ja-rikiddo-5y-main5/ |

各 run は run_metadata.json（source・collection_timestamp・query・filters・collector・retry・run identifier・raw 件数）を含む。raw は immutable とし、派生値は downstream で扱う。
