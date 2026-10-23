# Issue: GT 5年系列の再取得（2026-10-23）後に残った owner 判断 4 件

**ID:** ISS-20261023-GT-005  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/windows/`, `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261023T*`,
`datasets/cannabinoid-platform-trends/data/processed/`, `publication/research_{thc,cbg,hhc,thcv}.html`,
`metadata/publication/research-{thc,cbg,hhc,thcv}/`  
**GitHub:** [#2](https://github.com/routeflags/japan-cannabinoid-trends/issues/2)

## 概要

2026-10-23 に、summary-only だった THC・CBG・HHC・THCV の 5年系列を週次 raw として再収集した
（`52df20d`、報告書 [`docs/reports/20261023-gt-5y-recollection.md`](../../reports/20261023-gt-5y-recollection.md)）。
13 化合物すべてが週次系列を持ち、`ISS-20261015-GT-003` の残作業は解消した。

その一方で、**方針が決まっていない項目が 4 つ残った**。データと実装は入っている。

## 判断待ち・残作業

### 1. 化合物間で 5年の窓が 1 週ずれている

- 2026-10-02〜10-15 収集分は `2021-10-10_2026-10-12`（観測 `2021-10-10 〜 2026-10-11`）、
  2026-10-23 収集分（THC・CBG・HHC・THCV）は `2021-10-17_2026-10-18`。
- 原因: `today 5-y` は収集時刻で解決され、登録窓との照合は 7 日許容。
  既存窓は 13/11 日ずれて `no_registered_timeframe_matches` で拒否された（P6 = 期間の無断切替の禁止）。
- 影響: `platform_coverage.csv` / `trend_observations.csv` が同一データセット内で 2 つの窓を持つ。
- 選択肢: (a) 現状維持＋「同一窓内でのみ比較」を methodology に明記 / 
  (b) 全 13 化合物を同一窓で取り直す（絶対窓リクエストの実装が前提 = `GT-001` / `GT-004`） /
  (c) `window_id` を比較キーに含める（下流スキーマ変更）。

### 2. 反復収集をしていない（non-determinism 未測定）

- 1 化合物 1 run。同一クエリでも結果が変わりうることは未測定（AGENTS.md「Repeated Collection」）。
- 選択肢: (a) 1 化合物だけ repeat して差を記録 / (b) 回さず limitations に明記（現状そうしている） /
  (c) 全 4 化合物で repeat。

### 3. 再生成した公開 4 ページの内容審査

- 5年ブロックが「過去 5 年（週次）・261 週」→「2021-10-17 〜 2026-10-18（262 週）」に変わった。
- hash は再ピン済みだが `decision.status` は `requires_review` のまま。
  `PUB-10` は `approved` かつ同一 sha256 を要求するため、**この 4 ページは公開不可のまま**。

### 4. 12ヶ月系列の THCV / THC-O は引き続き「データなし」

- 5年では THCV の系列が返った（262 週中 45 週が非ゼロ）が、12ヶ月は閾値未満で系列なし。
  欠測が期間・正規化に依存することの実例。0 観測ではない扱いは既存のまま。
- 12ヶ月側の「データなし」注記を公開表に入れるかは未決。

## 補足（関連 issue の time gate）

`ISS-20261015-GT-004`（境界計測パス 2）の time gate（2026-10-22T04:28Z 以降）は経過している。
2026-10-15 と 2026-10-23 の 2 組の観測が raw にあるので、パス 2 の材料は揃った。

## 完了条件

- [ ] 1〜4 それぞれの方針決定（owner）
- [ ] 決定に基づく実施（収集・スキーマ・文書のいずれか）
- [ ] 4 ページの公開承認または見送りの記録（`decision.status` の更新）
