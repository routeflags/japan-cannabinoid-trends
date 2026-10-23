# Issue: CBD Google Trends 5年系列の raw タイムラインが未収蔵

**ID:** ISS-20261012-CBD-004  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15) — bare `CBD` の `today 5-y` raw 系列を新規 run として再取得し、下流検証を series 経路に切替。旧 summary-only run は未改変のまま残す
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/`（旧、未改変）+ `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261015T205048Z-google-trends-cannabinoid-multi-trends/`（新）

## 概要

CBD の Google Trends 12ヶ月データは raw タイムライン（53点）が存在する一方、
5年ベースラインは CBD の summary JSON のみで、報告上 261 点の時系列 raw がない。
そのため年次・月次の再集計やピーク値の独立検証ができない。

## 確認された記録

summary JSON の CBD 行:

- geo: JP
- timeframe: `today 5-y`
- data_points: 261
- first_value: 42
- last_value: 14
- peak_value: 100
- peak_date: 2025-08-31 to 2025-09-06
- avg_5y: 32.5

これらの値を構成する個々の日時・値は同 run の raw ファイルとして確認されていない。

## 影響

5年の peak_date、平均、長期推移を元観測値から再検証・再計算できない。
summary 値と raw observation の区別も読み手に不明確になる。

## 対応方針

- 既存 summary を raw として扱わない。
- 既存の collection log / 保存場所を確認し、raw が見つからない場合は「未収蔵」と明記する。
- 追加取得を行う場合は、Google Trends の取得日時・地域・期間・query・collector 情報を保存する。

## 完了条件

- [x] raw タイムラインが存在するか、その保管場所と来歴を確認する。（2026-10-15 調査: 下記「調査結果」）
- [x] 見つからない場合は summary-only / raw missing と dataset metadata に記録する。
  （`datasets/cannabinoid-raw-collection/methodology.md` §2.1.1 +
  `docs/audits/gt-summary.json` の baseline 5件 `unavailable.raw_timeline`。raw 自体には手を加えていない）
- [x] summary の 261 点・平均・ピーク値を raw で検証できるか明示する。
  （できない。記録値であり raw 系列からの独立検証は不可。下記「調査結果」）
- [x] 新規取得する場合、既存 summary を上書きせず新しい run として保存する。
  （2026-10-15 完了: オーナー承認のもとライブ再取得を実施。下記「再取得結果」）

## 調査結果（2026-10-15、オフライン調査）

- 対象 run `20261008T093228Z-google-trends-5y-baseline/` の内容は summary JSON 5件
  （`cbd/cbg/hhc/thc/thcv_5y_summary.json`）+ `run_metadata.json` のみ。
  週次タイムライン（`data` 配列・`records_*.json`・`payload.json`）は存在しない。
- リポジトリ全体を検索しても bare `CBD`（クエリ `CBD`、geo JP、`today 5-y`）の raw 系列は存在しない。
  - bare `CBD` の系列は 12ヶ月 run（`20261002T063821Z-google-trends-cbd/records_cbd.json`、53点）のみ。
  - `20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5年系列は「CBD リキッド」等、別クエリ・別正規化の
    プロダクトライン系列であり、bare CBD の検証には使えない
    （`src/processing/gt_statistics.py` の `find_run` も `PRODUCT_LINE_SUFFIX` で除外する）。
- よって `cbd_5y_summary.json` の data_points 261・first_value 42・last_value 14・peak_value 100・
  peak_date `2025-08-31 to 2025-09-06`・avg_5y 32.5 は**記録値（observed summary）**であり、
  raw 時系列観測から再計算・独立検証できない。欠測をゼロ観測に読み替えないこと。
- 既存の検証機構（`processing.cli gt-summary` → `docs/audits/gt-summary.json`）でこの状態を表現した:
  shape `baseline` の 5件（CBD/THC/CBG/HHC/THCV）に `unavailable.raw_timeline`
  （`raw タイムライン未収蔵（summary-only）`）を付与。`render_block` の出力は不変のため
  publication HTML・envelope hash・gate 結果への影響はない。
- 本 issue は CBD を例とするが、同一 run の THC/CBG/HHC/THCV も同じ summary-only 状態であり、
  同じ規則（baseline shape → `raw_timeline` 明示）で扱う。個別の side channel は作っていない。

## 外部利用での誤用例（2026-10-16 追記）

- 外部サイト原稿（THCV 物質辞典 v1.9）が本 run を出典として E1・E2 型の誤りを起こした。
  E1: `timeframe: today 5-y` を系列の範囲と読み替え、CBN の `data_period`
  `2021-10-10 〜 2026-10-11` を THCV の期間として記載。
  E2: summary-only の run に週次系列が含まれると記載。
  いずれも `docs/audits/gt-summary.json` の `unavailable.data_period` /
  `unavailable.raw_timeline`（shape `baseline`）を読めば回避できた型である。
- 本リポジトリ側の対応: `render_block` の出力は不変とし（publication HTML・envelope hash への影響を避ける）、
  代わりに `datasets/cannabinoid-raw-collection/methodology.md` §2.1.1 に原稿利用者向け注意を追記し、
  `tests/processing/test_gt_statistics.py` に baseline ガード群
  （端点なし・系列言及なし・他化合物の期間の流用なし）を追加した。
- 本 issue の完了条件（ライブ再取得）は変更しない。再取得が完了するまで baseline 5件は summary-only のままである。

## 再取得結果（2026-10-15、ライブ収集）

- オーナー承認のもと `collect --live` を単一クエリ（bare `CBD`、geo JP、`today 5-y`）で実行し、
  新規 run `20261015T205048Z-google-trends-cannabinoid-multi-trends/` を catalog に採用（L1 通過、既存 run は未改変）。
  plan: `datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-recollect-cbd.json`。
  成果物は verbatim payload（`payload.json`）+ 解析済み系列（`records_cbd.json`）。
  要求パラメータ（`submitted_parameters`: tool `interest_over_time` / terms `["CBD"]` / geo JP / timeframe `today 5-y`）は
  `run_metadata.json` の `temporal_provenance.submitted_parameters` に、観測範囲（`2021-10-10 〜 2026-10-11`）は
  `observed_min/max_timestamp` に分離記録している。
- 新系列 262 点の算出値: 平均 34.0229・ピーク 2025-08-31（値 100）・初出 2021-10-10（値 44）・最新値 13、
  非ゼロ 262 週 / ゼロ 0 週。旧 baseline の記録値（261 点・平均 32.5・初出値 42・最新値 14、ピーク日 `2025-08-31 to 2025-09-06`）とは
  収集窓・正規化が異なる別観測であり、一致しないことをもって旧値を訂正しない。旧値は記録値として旧 run に残す。
  ピーク初日（2025-08-31）は一致したが、これは再取得系列からの独立確認であり、旧記録の検証ではない。
- 下流切替: `processing.cli gt-summary --output docs/audits/gt-summary.json` を再生成し、CBD は shape `series`（by_shape `baseline` 4 / `series` 10）に移行。
  `publication/research_cbd.html` の5年ブロックを生成値に置換（`--compound CBD --write`）。`find_run` が最新収集を優先するため、コード変更なしに新 run が選択される。
  `methodology.md` §2.1.1 と本 issue に新旧の関係を記録し、`tests/processing/test_gt_statistics.py` の CBD 期待値と `BASELINE_COMPOUNDS` を更新した（CBD 除外、残り THC/CBG/THCV/HHC）。
- THC/CBG/HHC/THCV の4件は同一旧 run の summary-only のまま残る。本 issue は CBD を例とするが、他4件の再取得は本タスクの範囲外とする。

## 残作業

- なし（CBD の再取得は完了。本 issue を閉じる）。

## ライブ再取得の恒久ガード（2026-10-15 追記）

- Google Trends の tooling discovery / live recollection は、手作業の
  `npx google-trends-mcp --help` や `head` / `tail` 付きパイプでは実行しない。
- 事前検査は `PYTHONPATH=src python3 scripts/collection/google-trends-live-guard.py probe --timeout <秒>`
  を使う。probe は MCP `initialize` + `tools/list` のみで、`interest_over_time` を呼ばず、
  raw 観測値を書かない。
- オーナー承認後の本取得は同スクリプトの `fetch` サブコマンドで、明示 `--timeout`・新規 `--run-id`・
  pipeline `collect --live` 経由に限定する。成功時も既存
  `20261008T093228Z-google-trends-5y-baseline/` は上書きせず、新しい run として catalog / quarantine
  の判定に従う。
- ガードの診断ログは `.staging/tooling_logs/google_trends/<guard-run-id>/` に保存され、`success` /
  `timeout` / `dependency_missing` / `collector_error` / `network_or_rate_limited` /
  `invalid_config` の分類を `report.json` に残す。`.staging/` は Git 管理外であり、issue へ転記する前に
  secrets・raw payload 混入がないことをレビューする。
- 本追記はハング恒久対応であり、CBD 5年 raw タイムラインの再取得完了を意味しない。issue は OPEN のまま維持する。
