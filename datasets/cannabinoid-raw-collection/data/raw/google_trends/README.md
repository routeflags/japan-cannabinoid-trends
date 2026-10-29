# data/raw/google_trends

この研究で追跡する Google トレンド raw（56 run）。1 ディレクトリ = 1 run。run-id 形式は `<UTC>Z-google-trends-<slug>`（AGENTS.md "Run Identity"）。

このディレクトリだけが追跡対象なのは `.gitignore` の例外による（`data/raw/*` は原則 untracked、`google_trends/` のみ追跡）。X・YouTube の raw は一次 checkout の旧 study 名側（`datasets/cannabinoid-multi-trends/data/raw/{x,youtube}/`）にだけあり、ここには無い。YouTube の集計物は [`../processed/`](../../../data/processed) にある。

## 内訳（56 run）

| 収集日 | run 数 | 内容 | 状態 |
|---|---|---|---|
| 10-02 | 16 | 化合物語の 12ヶ月・5年単独系列、比較 setA、nodata 確認 | 凍結 legacy（`validation.legacy.LEGACY_RUN_IDS`）。契約適合性は `audit-new-runs` の対象外 |
| 10-05 | 1 | common-scale 拡張 | 同上 |
| 10-08 | 6 | 5年 baseline、CRDH 5年、common-scale 不足分 | うち 3 件（`20261008T102022Z-google-trends-crdh`、`20261008T125719Z-google-trends-common-scale-crdh` / `-thch`）に `run_metadata.json` が無い → [#12](https://github.com/routeflags/japan-cannabinoid-trends/issues/12) |
| 10-12 | 5 | 表記 presurvey、リキッド phase-a / a-repeat / phase-b、5年 main5 | pipeline 収集。現行契約の対象 |
| 10-14/15 | 9 | 5年単独系列の再取得（10-02 が系列未保存だった分） | 同上 |
| 10-23 | 18 | 5年再取得 4、12ヶ月再取得 3、共通スケール setA–D、5年リキッド 7 | 同上 |
| 10-24 | 1 | CRDH 12ヶ月再取得 | 同上 |

## 照合

- 現行契約の適合：`make audit-new-runs`（凍結以外は全適合が必須）
- 宣言待ちの棚卸し：`make audit-adoption`（このディレクトリに `run_metadata.json` が無い 3 件が出る）
- 目録：[`../../metadata/data-catalog.json`](../../metadata/data-catalog.json)
- 収集条件の正本：[`../../methodology.md`](../../methodology.md)、[`../../README.md`](../../README.md)
