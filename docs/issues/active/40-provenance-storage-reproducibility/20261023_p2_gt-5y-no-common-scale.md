# Issue: 5年の共通スケール計測が無い（化合物間比較が成立しない）

**ID:** ISS-20261023-GT-009  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/`（`common-scale-*` / `comparison-*`）,
`datasets/cannabinoid-platform-trends/data/processed/metric_dictionary.csv`,
`datasets/cannabinoid-raw-collection/methodology.md` §2.1.2  
**GitHub:** [#5](https://github.com/routeflags/japan-cannabinoid-trends/issues/5)

## 概要

Google Trends の共通スケール（比較セット）計測は **12ヶ月だけ**で、**5年の共通スケールは 1 本も無い**。
5年の run はすべて単独系列で、各語が自分のピーク=100 に正規化されている。
したがって **5年での化合物間比較は現状のデータでは成立しない**。

## 実測

- 比較セット / 共通スケール run は 13 本あり、**すべて `today 12-m`**:
  `comparison-setA`（5 語）、`common-scale-expansion`（3 セット）、`common-scale-crdh`、`common-scale-thch`、
  `common-scale-missing`、`ja-rikiddo-phase-a`（+ repeat）・`phase-b`（各 5 語）、CBX study の 3 本。
- **5年の comparison run は 0 本**。5年の run はすべて単独系列。

## 何が問題か

1. 単独系列の平均（例 CBD 34.02 / THC 12.41）は、それぞれ自分のピークを 100 とした値なので、
   大小は需要の大小を意味しない。
2. `datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv` は 5 年平均を化合物ごとに並べる。
   `metric_dictionary.csv` は `comparable_across_platforms: no` を持つが、**「化合物間でも比較不可」とは書いていない**。
3. `methodology.md` §2.1.2 の「化合物間の比較は共通スケール比較 run が担う」は、その run が 12ヶ月にしか無いため
   5年では成り立たない（本 issue で記述を修正）。

## 選択肢

1. 5年の共通スケール run を追加収集する（12ヶ月の common-scale に倣い、アンカー語 CBD/THC を含む 3〜5 語セットを複数。
   窓は現行の `2021-10-17_2026-10-18`）。新規収集なので owner 判断。
2. 5年は化合物間比較をしないと明記する（`metric_dictionary.csv` の limitations と methodology）。
   生成物の正本は `src/processing/platform_trends.py` なので、コードとスナップショットの更新を伴う。
3. 1 と 2 の両方。

## 完了条件

- [ ] 方針の決定（owner）
- [ ] 決定に応じた実施（収集 run / メトリクス辞書と methodology の明記）
- [ ] 5年の化合物間比較が「データで支えられている」か「明示的に不可」かのどちらかになっている
