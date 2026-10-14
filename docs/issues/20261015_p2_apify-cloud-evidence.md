# Issue: Apify クラウド側の実行記録・dataset ID が未取得

**ID:** ISS-20261015-PRV-013  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `config/collectors.json`（`x-apify-twitter-search` / `youtube-apify-scraper` / `youtube-apify-search` / `tiktok-apify-search` ほか）, `datasets/*/data/raw/**`, `docs/specs/validation-framework.md` §18.3

## 概要

Apify クラウド側の証拠（actor run ID・dataset ID・実行時の input・開始終了時刻）は
リポジトリに保存されていない。このため X / YouTube の旧 run の実行条件は引き続き `unknown`
であり、2026-10-14 にダウンロードされた YouTube dataset の CSV も、どの run の出力かは
ファイル名以上の根拠を持たない。

## 確認された観測

- `collector.version` は `unknown`、capability は全項目 `unknown`（4 collector）。
- 2026-10-14 のダウンロード（`~/Downloads/dataset_youtube-scraper_*.csv` 7 件）には
  run ID / dataset ID が含まれず、CSV 自身には `input`（検索クエリ）のみがある。
- `datasets/youtube-consistency/data/trends.db` の `runs.apify_dataset_id` が唯一の
  候補だが、Git 管理外のローカル DB であり CI から参照できない。

## 影響

- 収集条件（maxResults / pagination / retry / 実行時刻）を契約の形で記録できない。
- 同一クエリの反復収集を区別する情報が不足し、非決定性の評価が人手に依存する。

## 対応方針

- 取得依頼リスト（run ID / dataset ID / input / 開始・終了時刻）を作る。
- 取得元（Apify コンソール / API）と権限を確認し、**推測で埋めない**（欠損は欠損として記録）。
- 取得できた証拠は evidence registry に登録し、collector の capability 昇格判断に使う。

## 完了条件

- [ ] 取得依頼リストの作成
- [ ] 取得した証拠の登録（証拠ハッシュの扱いを含む）
- [ ] capability 昇格判断（昇格しない項目はその理由を記録）
