# Issue: CBD Google Trends 5年系列の raw タイムラインが未収蔵

**ID:** ISS-20261012-CBD-004  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/`

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
  （`datasets/cannabinoid-multi-trends/methodology.md` §2.1.1 +
  `docs/audits/gt-summary.json` の baseline 5件 `unavailable.raw_timeline`。raw 自体には手を加えていない）
- [x] summary の 261 点・平均・ピーク値を raw で検証できるか明示する。
  （できない。記録値であり raw 系列からの独立検証は不可。下記「調査結果」）
- [ ] 新規取得する場合、既存 summary を上書きせず新しい run として保存する。
  （残件: ライブ収集が必要なため本タスクでは未実施。オーナー承認待ち。下記「残作業」）

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

## 残作業（オーナー / 外部収集の承認が必要）

- CBD（および同一 run の THC/CBG/HHC/THCV）の `today 5-y` / geo JP 系列のライブ再取得。
  `ISS-20261015-GT-003` が 8化合物に行った再取得（`collect --live` → payload + `records_*.json` の
  2成果物、L1 通過後に catalog 採用）と同じ経路で行い、取得後は `gt-summary` 再生成で平均・ピークが
  系列から算出されることを確認する。既存 summary の上書きは禁止（新規 run とする）。
- 再取得が完了し、系列から 261点・平均・ピークが再計算できたら本 issue を閉じる。
