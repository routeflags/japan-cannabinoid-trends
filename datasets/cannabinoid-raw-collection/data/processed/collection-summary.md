# Collection Summary

**Study ID:** cannabinoid-raw-collection
**初回収集:** 2026-10-02
**Status:** COLLECTION_COMPLETE

このファイルは収集結果のうち、**リポジトリの raw から再導出できない値**を記録する。

| ソース | 本ファイルに書くもの | 正本 |
|---|---|---|
| Google Trends | 書かない（raw が追跡されているため全て再導出できる） | `data/raw/google_trends/`、[`docs/audits/gt-summary.json`](../../../../docs/audits/gt-summary.json)、[methodology.md](../../methodology.md) §2.1.2〜§2.1.4 |
| X (Twitter) | 件数（raw は Git 管理外のローカル証跡なので、これが唯一の追跡記録） | 本ファイル |
| YouTube | 書かない。件数は追跡 CSV と一致することを確認し、内訳も CSV を参照 | [`youtube_runs.csv`](youtube_runs.csv)（生成: `python -m processing.cli youtube-export`） |

手書きのため `src/processing/reproduce.py` の `NON_REPRODUCIBLE` に
`not_reproducible_from_repository` として宣言している。

---

## 1. Google Trends

系列・窓・欠測は [methodology.md](../../methodology.md) §2.1.2〜§2.1.4 と
[`docs/audits/gt-summary.json`](../../../../docs/audits/gt-summary.json) が正本。本ファイルには転記しない。

---

## 2. X (Twitter)（記録値）

期間: `2026-09-01` 〜 `2026-10-01`。クエリは `{keyword} since:2026-09-01 until:2026-10-01`。
件数は取得時点の値であり、シャドウバンや削除の影響を受けうる。raw はリポジトリ外（ローカル証跡のみ）。

| キーワード | 件数 | maxPages |
|-----------|:----:|:--------:|
| CBD | 60 | 3 |
| THC | 60 | 3 |
| CBG | 40 | 2 |
| HHC | 40 | 2 |
| THCV | 40 | 2 |
| THC-O | 40 | 2 |
| THCH | 36 | 2 |
| **合計** | **316** | |

計画時のパラメータは [methodology.md](../../methodology.md) §2.2。

**CBD の追加 3 run（2026-10-08）**: raw はローカル証跡のみで、`run_metadata.json` に収集条件の記録が無いため、
件数をここに記録する（`records.json` の行数）。

| run | 件数 | 備考 |
|---|---:|---|
| `20261008T165031Z-x-cbd-1year` | 0 | `status: SUCCEEDED` の 0 件（observed_zero） |
| `20261008T165122Z-x-cbd-1m` | 60 | |
| `20261008T165330Z-x-cbd-latest10` | 200 | |

---

## 3. YouTube

集計物は 2026-10-29 に削除した（研究内に参照元の raw が無いため、owner 決定）。

---

## 4. 制約事項

1. Google Trends はクエリ単位の相対指数（0-100）。単独系列の平均を化合物間で比較しない（[methodology.md](../../methodology.md) §2.1.2）。
2. 低ボリューム語は閾値未満で系列が返らない。**欠測であって 0 観測ではない**（§2.1.3）。
3. X の件数は取得時点の記録値であり、再現できない。0 件でも observed_zero として扱う（§2.2）。
