# Issue: 5年の共通スケール計測が無い（化合物間比較が成立しない）

**ID:** ISS-20261023-GT-009  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-24) — 5年の共通スケール setA〜D を収集し、アンカーの週次一致まで検証した  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/`（`common-scale-*` / `comparison-*`）,
`datasets/cannabinoid-platform-trends/data/processed/metric_dictionary.csv`,
`datasets/cannabinoid-raw-collection/methodology.md` §2.1.2  
**GitHub:** [#5](https://github.com/routeflags/japan-cannabinoid-trends/issues/5)

## 決定（owner, 2026-10-24）

**選択肢 1（5年の共通スケール run を追加収集）**を採用する。2026-10-23 に setA〜D を収集済み（上記「対応状況」）。
選択肢 2（`metric_dictionary.csv` と methodology への「化合物間でも比較不可」の追記）は選択されていないため、その項目は未対応のまま残る。

## 概要

Google Trends の共通スケール（比較セット）計測は **12ヶ月だけ**で、**5年の共通スケールは 1 本も無い**。
5年の run はすべて単独系列で、各語が自分のピーク=100 に正規化されている。
したがって **5年での化合物間比較は現状のデータでは成立しない**。

## 実測

- 比較セット / 共通スケール run は 13 本あり、**すべて `today 12-m`**:
  `comparison-setA`（5 語）、`common-scale-expansion`（3 セット）、`common-scale-crdh`、`common-scale-thch`、
  `common-scale-missing`、`ja-rikiddo-phase-a`（+ repeat）・`phase-b`（各 5 語）、CBX study の 3 本。
- **5年の comparison run は 0 本**だった。5年の run はすべて単独系列。

## 対応状況

**5年の共通スケールを取得済み（2026-10-23、option 1）**。アンカー（CBD, THC）を含む 4 セット、
窓 `2021-10-17_2026-10-18`、各 262 週。アンカー値は 4 セットで一致（CBD 33 / THC 5）し、セット間を橋渡しできる。
run: `20261023T171700Z-*setA`（CBD/THC/CBG/HHC/THCV）、`…T171709Z-*setB`（CBD/THC/THCH/CBN/CRDH）、
`…T171717Z-*setC`（CBD/THC/CRDP/H4CBH/HHBD）、`…T171726Z-*setD`（CBD/THC/HHCH/THC-O）。
成果物は verbatim `payload.json` + `comparison_<terms>.json`（`google-trends-comparison-v1`）。
方法は `methodology.md` §2.1.4。

**未対応（option 2）**: `metric_dictionary.csv` の limitations は `comparable_across_platforms: no` だけで、
「化合物間でも比較不可」をまだ書いていない。生成物の正本は `src/processing/platform_trends.py`。

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

- [x] 5年の共通スケール run の収集（2026-10-23、option 1）
- [ ] `metric_dictionary.csv` と methodology に「単独系列は化合物間でも比較不可」を明記（option 2）
- [ ] 5年の化合物間比較が「データで支えられている」か「明示的に不可」かのどちらかになっている

## 検証（2026-10-24）

独立検証（収集なし、raw・`docs/audits/` 不変）。実測値は `comparison_*.json` の `data`（262 週）からの再計算と `run_metadata.json` の記録の突き合わせである。

### setA〜D の実体

| セット | run | `submitted_query` の語集合 | 週数 | 観測範囲（`data` の先頭〜末尾） | `window_id` | `exact_window_match` |
|---|---|---|---|---|---|---|
| A | `20261023T171700Z-google-trends-5y-common-scale-setA` | CBD, THC, CBG, HHC, THCV | 262 | 2021-10-17 〜 2026-10-18 | `2021-10-17_2026-10-18` | `false` |
| B | `20261023T171709Z-google-trends-5y-common-scale-setB` | CBD, THC, THCH, CBN, CRDH | 262 | 2021-10-17 〜 2026-10-18 | `2021-10-17_2026-10-18` | `false` |
| C | `20261023T171717Z-google-trends-5y-common-scale-setC` | CBD, THC, CRDP, H4CBH, HHBD | 262 | 2021-10-17 〜 2026-10-18 | `2021-10-17_2026-10-18` | `false` |
| D | `20261023T171726Z-google-trends-5y-common-scale-setD` | CBD, THC, HHCH, THC-O | 262 | 2021-10-17 〜 2026-10-18 | `2021-10-17_2026-10-18` | `false` |

4 run とも `run_metadata.json` の `observed_min/max_timestamp` は `2021-10-17T00:00:00Z` / `2026-10-18T00:00:00Z` で、`data` の範囲と一致する。`exact_window_match=false` は相対 timeframe（`today 5-y`）の既知の制約であり、4 セット共通である。`comparison_*.json` 自体に schema フィールドはなく、schema `google-trends-comparison-v1` の表示は各 run の `artifact-manifest.json` の `schema_id` が根拠である。

### アンカーの一致

`average_interest` の CBD / THC は 4 セットとも CBD 33 / THC 5 で一致する。さらに週次系列そのものが 4 セットで完全一致する（CBD 合計 8666、THC 合計 1305、262 週すべて同値）。セット間の橋渡しは平均だけでなく週次系列の水準でも成立する。

### 平均値の突き合わせ（記録 13 語と実測）

`average_interest` の記録値はすべて再計算した厳密平均の整数丸めと一致する。切り捨てではない（THC 4.9809→5、THCH 1.9809→2、CBN 4.5458→5 が切り捨てを棄却する）。タイ（ちょうど .5）の扱いは、このデータに該当例がなく確認できない。

| 語 | セット | 記録 | 厳密平均 | `average_interest` | 判定 |
|---|---|---|---|---|---|
| CBD | A〜D | 33 | 33.076336 | 33 | 一致 |
| THC | A〜D | 5 | 4.980916 | 5 | 一致 |
| CBG | A | 1 | 1.061069 | 1 | 一致 |
| HHC | A | 2 | 2.248092 | 2 | 一致 |
| THCV | A | 0 | 0.099237 | 0 | 一致 |
| THCH | B | 2 | 1.980916 | 2 | 一致 |
| CBN | B | 5 | 4.545802 | 5 | 一致 |
| CRDH | B | 0 | 0.114504 | 0 | 一致 |
| CRDP | C | 0 | 0.103053 | 0 | 一致 |
| H4CBH | C | 0 | 0.206107 | 0 | 一致 |
| HHBD | C | 0 | 0.118321 | 0 | 一致 |
| HHCH | D | 1 | 1.041985 | 1 | 一致 |
| THC-O | D | 0 | 0.049618 | 0 | 一致 |

平均 0 の 6 語の非ゼロ週は THCV 26、CRDH 30、CRDP 27、H4CBH 54、HHBD 31、THC-O 13（いずれも全 262 週中）であり、methodology §2.1.4 の「非ゼロがごく少ない」に合う。`payload.json` の verbatim テキスト内の "Average interest scores" も同値であり、`average_interest` はツール応答の転記と再計算の双方で裏づけられる。

### methodology との一致

`methodology.md` §2.1.4 の表（セット・run・語・平均）、§1.2 の 5 年行（`2021-10-17 〜 2026-10-18` に THC・CBG・HHC・THCV および setA〜D）、§2.1.2 の「単独系列の平均値を化合物間で比較しない。化合物間比較は共通スケール（§2.1.4）でのみ行う」は、いずれも上記実測と合う。修正を要する差分はないため methodology は編集しない。

### 完了条件の判定

1. 「5年の共通スケール run の収集」→ 達成。上記 4 run が同一窓・262 週・アンカー週次一致で存在する。
2. 「`metric_dictionary.csv` と methodology に『単独系列は化合物間でも比較不可』を明記（option 2）」→ 未対応。`relative_interest_mean_5y` 行の limitations は `"Google Trends values are source-normalized relative indices, not absolute search volume."` のままで、化合物間の不可に触れない。正本は `src/processing/platform_trends.py` の `_metric_rows()`（`relative_interest_mean_5y` の limitations）が同文を固定している。
3. 「『データで支えられている』か『明示的に不可』かのどちらか」→ 前者が成立する。5 年の化合物間比較は setA〜D の共通スケール（同一窓、週次一致のアンカー）に支えられる。ただし支えられるのは共通スケール内の比較であり、単独系列の平均の横並びは支えられない（残件参照）。

### クローズ判断の残件

- `datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv` は単独系列の 5 年平均を化合物ごとに並べる（例 `gt-cbd-relative_interest_mean_5y` 34.0229、`gt-thc-relative_interest_mean_5y` 12.4084、`gt-cbg-relative_interest_mean_5y` 48.1756、`gt-cbn-relative_interest_mean_5y` 21.0687）。各行の limitations は `"not comparable to YouTube returned_count"` のみで、化合物間の不可に触れない。読み手が 5 年平均の大小を需要の大小と誤読しうる。
- 同ファイルの 5 年平均は窓が混在する（CBD・CBN 等が `2021-10-10,2026-10-11`、THC・CBG・HHC・THCV が `2021-10-17,2026-10-18`）。窓をまたいだ比較も成立しないが、その旨の表示はない。
- `methodology.md` §2.1.4 は単独系列と共通スケールの混同を禁じているが、配布物（`trend_observations.csv` + `metric_dictionary.csv`）側にその guard がない。option 2 を実施しないまま close すると、この誤読経路が残る。改善案（実施せず）：option 2 の文言を `_metric_rows()` と `trend_observations.csv` の GT 行 limitations に入れる、または 5 年共通スケールを配布物に載せる。いずれも生成コードとスナップショットの更新を伴うため owner 判断が必要。
