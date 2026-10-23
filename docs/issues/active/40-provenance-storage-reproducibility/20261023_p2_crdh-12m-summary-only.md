# Issue: CRDH の 12ヶ月系列が summary-only（`avg_12m` 1.9 が raw から検算できない）

**ID:** ISS-20261023-GT-007  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261008T102022Z-google-trends-crdh/`,
`datasets/cannabinoid-raw-collection/methodology.md` §2.1.3  
**GitHub:** [#3](https://github.com/routeflags/japan-cannabinoid-trends/issues/3)

## 概要

12ヶ月系列は 11 化合物が週次 raw を持ち、THC-O は Google Trends が系列を返さない。
残る CRDH だけが **summary-only**（週次系列を収蔵していない）。
5年側は `20261014T215738Z-google-trends-cannabinoid-multi-trends` に系列があるため、**12ヶ月のみの欠落**。

## 事実（実測）

- `records_crdh_12m.json` は `data` 配列を持たず、`data_points` 53・`first_value` 0・`last_value` 0・
  `peak_value` 100・`peak_date` 2025-11-09 to 2025-11-15・`avg_12m` 1.9・`nonzero_weeks` 2 の**記録値**だけ。
  同じ run ディレクトリには `run_metadata.json` も無い（legacy 形状）。
- したがって `avg_12m` 1.9・ピーク日・非ゼロ週数は raw から検算できない。
- **公開ページはこの値を使っていない**: `publication/research_crdh.html` の 12ヶ月ブロックは
  「共通スケール」表（CRDH 0 / CBD 47 / THC 12）で、根拠は
  `20261008T125719Z-google-trends-common-scale-crdh/comparison.json` にある。ページの数値自体は問題ない。

## 何が問題か

原稿や下流が `avg_12m = 1.9` やピーク日を引用すると出所不明の数値になる
（`ISS-20261015-GT-003` と同型）。12ヶ月の他 3 化合物（THCV・H4CBH・HHBD）は系列を取得済みで、
CRDH だけが取り残されている。

## 選択肢

1. 12ヶ月を 1 run 再取得（`today 12-m` / geo JP、窓 `2025-10-19_2026-10-18`、`crdh-general-ja`）。
   既存 summary は残し、新しい系列を正本にする（`ISS-20261012-CBD-004` と同じ扱い）。新規収集なので owner 判断。
2. summary-only のまま維持し、`avg_12m` を引用しないことを methodology に明記する。
3. 12ヶ月の単独系列は使わず、共通スケール比較（raw あり）だけを 12ヶ月の根拠にする。

## 完了条件

- [ ] 方針の決定（owner）
- [ ] 決定に応じた実施（収集 1 run / 文書の明記 / 共通スケールへの一本化）
- [ ] `methodology.md` §2.1.3 の表の「サマリーのみ」が解消、または恒久的な注記になる
