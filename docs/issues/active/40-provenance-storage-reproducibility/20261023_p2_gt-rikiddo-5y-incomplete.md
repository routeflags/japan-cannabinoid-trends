# Issue: 5年の「○○ リキッド」が 5/13 語しか無い

**ID:** ISS-20261023-GT-008  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T064246Z-google-trends-ja-rikiddo-5y-main5/`,
`README.md` のキーワード表  
**GitHub:** [#4](https://github.com/routeflags/japan-cannabinoid-trends/issues/4)

## 概要

「リキッド」系クエリは **12ヶ月は 13 化合物語すべてを照会**しているが、**5年は 5 語だけ**。
5年の「○○ リキッド」は `20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 1 run のみで、
**8 語（THCV / THC-O / THCH / CRDH / CRDP / H4CBH / HHBD / HHCH リキッド）が未収集**。

## 実測

- 5年（main5、262 週 / `2021-10-10 〜 2026-10-11`）: CBD リキッド（平均 36.527）・CBG リキッド（0.683）・
  CBN リキッド（4.401）・HHC リキッド（2.992）・THC リキッド（8.550）。
- 12ヶ月（phase-a / phase-b、各 53 週 / `2025-10-12 〜 2026-10-11`）: 系列あり 8 語（CBD / CBG / CBN / THC /
  H4CBH / HHBD / HHCH / THCH リキッド）、系列なし 5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）。

## 12ヶ月の有無から 5年の有無は推定できない

**HHC リキッドは 12ヶ月で系列なし、5年では 262 週の系列がある**（平均 2.992）。
閾値は期間と正規化に依存するため、未収集の 8 語は**照会するまで分からない**。

## 選択肢

1. 8 語を 5年で収集する（窓は現在の `2021-10-17_2026-10-18` になるため、既存 main5 の
   `2021-10-10 〜 2026-10-11` とは 1 週ずれる = 別窓の観測）。新規収集なので owner 判断。
2. 5 語を意図的な範囲として methodology / README に明記する（13 語の 5年カバレッジは 5/13 のまま）。
3. 12ヶ月で系列がある 4 語（H4CBH / HHBD / HHCH / THCH リキッド）だけ先行して収集する。

## 補足

- CBX リキッドの 5年系列はこのリポジトリに無い（CBX study の 5年は bare `CBX` のみ）。
- main5 は legacy 形状（`payload.json` 無し、`metadata/windows/` の窓を持たない）。

## 完了条件

- [ ] 方針の決定（owner）
- [ ] 決定に応じた実施（8 語の収集 run、または文書の明記）
- [ ] `README.md` のキーワード表から「未収集」の注記が解消（または恒久的な注記になる）
