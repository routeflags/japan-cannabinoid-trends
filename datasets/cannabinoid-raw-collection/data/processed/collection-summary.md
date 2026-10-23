# Collection Summary

**Study ID:** cannabinoid-raw-collection
**初回収集:** 2026-10-02
**Status:** COLLECTION_COMPLETE

このファイルは収集結果のうち、**リポジトリの raw から再導出できない値**を記録する。

| ソース | 本ファイルに書くもの | 正本 |
|---|---|---|
| Google Trends | 書かない（raw が追跡されているため全て再導出できる） | `data/raw/google_trends/`、[`docs/audits/gt-summary.json`](../../../../docs/audits/gt-summary.json)、[methodology.md](../../methodology.md) §2.1.2〜§2.1.4 |
| X (Twitter) | 件数・費用（raw は Git 管理外のローカル証跡なので、これが唯一の追跡記録） | 本ファイル |
| YouTube | 費用。件数は追跡 CSV と一致することを確認するだけにし、内訳は CSV を参照 | [`youtube_runs.csv`](youtube_runs.csv)（生成: `python -m processing.cli youtube-export`） |

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

| キーワード | 件数 | maxPages | 費用（請求実績） |
|-----------|:----:|:--------:|----------------:|
| CBD | 60 | 3 | $0.152 |
| THC | 60 | 3 | $0.152 |
| CBG | 40 | 2 | $0.102 |
| HHC | 40 | 2 | $0.102 |
| THCV | 40 | 2 | $0.102 |
| THC-O | 40 | 2 | $0.102 |
| THCH | 36 | 2 | $0.092 |
| **合計** | **316** | | **~$0.80** |

計画時の目安は [methodology.md](../../methodology.md) §2.2。

---

## 3. YouTube

- 公開集計は 7 run / 182 動画行（`youtube_runs.csv` の `video_rows` 合計と一致、error payload 0・unreadable 0）。
  run 別の内訳・収集時刻は [`youtube_runs.csv`](youtube_runs.csv)、動画行は
  [`youtube_videos.csv`](youtube_videos.csv)。
- 費用（請求実績）: CBD $0.011 / THC $0.013 / CBG $0.017 / HHC $0.014 / THCV $0.012 /
  CBD オイル $0.012 / THC オイル $0.014。**合計 ~$0.09**。
  計画時の目安は [methodology.md](../../methodology.md) §2.3。

---

## 4. コスト実績

| ソース | 予算 | 実績 |
|--------|------|------|
| Google Trends | 無料 | 無料 |
| X (Twitter) | $0.64 | ~$0.80 |
| YouTube | $0.23 | ~$0.09 |
| **合計** | **$0.87** | **~$0.89** |

---

## 5. 制約事項

1. Google Trends はクエリ単位の相対指数（0-100）。単独系列の平均を化合物間で比較しない（[methodology.md](../../methodology.md) §2.1.2）。
2. 低ボリューム語は閾値未満で系列が返らない。**欠測であって 0 観測ではない**（§2.1.3）。
3. X の件数は取得時点の記録値であり、再現できない。0 件でも observed_zero として扱う（§2.2）。
4. YouTube はページング重複があるため、ユニーク `videoId` で重複排除している（§3.1）。
