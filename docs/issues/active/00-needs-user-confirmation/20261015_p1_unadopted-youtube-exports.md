# Issue: 未採用の YouTube dataset export 7 件の実採用判断が未了

**ID:** ISS-20261015-COL-033  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `docs/reports/20261015b-youtube-csv-staging-driver.md`、
`src/collection/core/staging.py`（`staging-declaration-v1`）、
`datasets/youtube-consistency/data/raw/`、`ISS-20261015-COL-017`（RESOLVED）、
`ISS-20261015-COL-018`、`ISS-20261015-PRV-013`

## 概要

2026-10-14 にダウンロードした実 YouTube dataset export 7 件（Apify `youtube-scraper`、
`~/Downloads/dataset_youtube-scraper_*.csv`）は、**stage → adopt → 厳格検証までの rehearsal は済んでいるが、
実採用は未実施**である。採用判断には宣言事実の確認が 6 点必要で、それが先
（`docs/reports/20261015b-youtube-csv-staging-driver.md` §5）。

`ISS-20261015-COL-017`（staging ドライバ + `stage` CLI）は RESOLVED だが、
その完了条件のうち「実採用」が残っており、追跡先が無かった。

## 確認された観測（rehearsal の記録）

- rehearsal はリポジトリ外 scratch workspace（`/tmp/yt-staging-rehearsal-20261015/`）で
  7/7 stage → 7/7 adopt → `validate_full(verify_artifacts=True)` valid →
  `audit-new-runs` new=7 / failures=0。payload は `~/Downloads` 原本と byte 一致。
- **リポジトリの `datasets/` は未変更**（本採用はしていない）。
- 宣言値（窓 / `date_filter` / status / 時刻）は確認前の placeholder。
  5 件は `date_filter: all` と矛盾しないが、2 件（`13-50-24` / `19-19-00`）は
  bounded の可能性を排除できない。

## 影響

- 取得済みで検証可能な YouTube データが公開物に反映されない
  （`publication/research_*.html` の YouTube 節は 2026-10-08〜09 の値のまま）。
- 「取得したが未採用」の状態が続き、何が未了かが issue から見えない。

## 対応方針

確認する 6 点（同レポート §5）:

1. 各 export の actor run ID / dataset ID（`ISS-20261015-PRV-013` の取得依頼リスト）
2. 各 run の `dateFilter`（`13-50-24` / `19-19-00` は要確認）
3. 実行 status（SUCCEEDED か）と startedAt / finishedAt
4. ファイル名 stamp の意味と timezone（run 時刻 / export 時刻、UTC / JST）
5. 実採用の可否（配置先は方針上無追跡。`ISS-20261015-COL-018` の
   「決定先送り中は実 run を catalog しない」を YouTube にも適用するか）
6. 宣言の絶対窓（研究側観測区間）の確定

採用する場合は `staging-declaration-v1` の宣言ファイルを commit して `stage` → `adopt`。
採用しない場合は理由を記録する（**失敗を 0 件に変換しない**）。

## 完了条件

- [ ] 上記 6 点の確認記録（日付付き）
- [ ] 宣言ファイルの commit と `stage` → `adopt`（または不採用理由の記録）
- [ ] 監査スナップショットの再生成と `audit-new-runs` / `audit-publication` の確認

## 依存

- `ISS-20261015-COL-018`（無追跡 raw の catalog 方針）の決定。
- 公開物への反映は公開契約 PC-2 / PC-8 の範囲（run_id を持たない旧契約の収集とは別扱い）。
