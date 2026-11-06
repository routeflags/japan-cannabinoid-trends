# CBD の Google Trends 推移（現行 5年共通スケール、setA）

このディレクトリは、CBD の検索関心度を **1 つの共通スケール要求**から取り出して
系列と図にした分析成果物である。`publication/` ではなく study の `analysis/` に置く。

## 出所（1 source / 1 run / 1 request）

| 項目 | 値 |
|---|---|
| source | Google Trends（`google-trends-mcp`） |
| run_id | `20261104T195126Z-google-trends-cannabinoid-raw-collection` |
| query_id | `comparison-5y-setA` |
| 要求語 | `CBD`・`THC`・`CBG`・`HHC`・`THCV`（同じ `compare_terms` 要求） |
| geo / timeframe | `JP` / `today 5-y` |
| 窓 | `2021-10-31_2026-11-08`（`metadata/windows/2021-10-31_2026-11-08.json`） |
| 観測範囲 | 2021-10-31 〜 2026-11-01（262 週、返却点の範囲） |
| input | `data/raw/google_trends/<run_id>/comparison_cbd-thc-cbg-hhc-thcv.json` |

`provenance.json` に input 4 ファイル（comparison / run_metadata / payload /
artifact-manifest）の SHA-256 と、窓・要求語・正規化・統計を記録する。

## 数値（comparison artifact から再計算）

| 指標 | CBD |
|---|---|
| 週次点 | 262 |
| 平均 | **33.0916** |
| 中央値 | 33 |
| 最大 | 100（2025-08-31） |
| 非ゼロ週 / ゼロ週 | 262 / 0 |

同じ要求に入っている他 4 語も `series.csv` に併記する（同じ run・同じ要求の値で
あり、出所は CBD と同一）。図に描くのは CBD のみ。

## 読み方と制約

- 共通スケールの値は**その要求の中の最大点 = 100** で正規化されている。同じ
  化合物でも単独系列（`THCNM` の 12ヶ月・5年節など）とは別の物差しで、
  **換算できない**（`publication/research_thcnm.html` の「用語の定義」と同じ規則）。
- 0 は相対指数の最小値（閾値未満）であり、検索が無かったことや欠測ではない。
  CBD は 262 週すべて非ゼロである。
- 絶対検索数ではない。他 source（X、YouTube、GSC 等）の値と合成・比較しない
  （source separation）。
- 窓は要求条件であり、観測範囲は返却点の範囲である。両者を混同しない。
- 反復実行はしていない（単発 run）。同一条件の再取得による安定性は未測定。

## 再生成

```bash
python3 scripts/analysis/cbd_common_scale_plot.py
```

stdlib のみで動く（matplotlib 等の描画依存を追加しない）。出力は
`series.csv`・`cbd-common-scale-5y.svg`・`provenance.json` の 3 点で、入力が
同じなら同じ内容になる（SVG に生成時刻を埋め込まない）。

## 公開スコープ

- `publication/` の成果物ではない。公開ページから参照しない。
- 配布物 `datasets/cannabinoid-platform-trends/`（release slice）には含めない。
  `metadata/data-catalog.json` にも追加しない（catalog は採用済み raw の台帳で
  あり、この分析成果物はそこに属さない）。
