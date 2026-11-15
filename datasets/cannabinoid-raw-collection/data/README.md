# data

この研究のデータ置き場。raw は不変の原記録、interim は補正作業、processed は再現可能な集計成果物。

raw は machine-local（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）であり、clone によっては `raw/youtube/` が存在しない。catalog / declaration は committed な事実、payload はその checkout の証跡として分けて読む。

| ディレクトリ | 内容 |
|---|---|
| [`raw/google_trends/`](raw/google_trends/) | 追跡する Google トレンド raw **100 run ディレクトリ**（catalog 採用 68、manifest を持たない 32）。登録 63 トピックのうち 5年 29/63・12ヶ月 21/63 に adopted 系列がある（2026-11-11 登録の 6 検索トピックと 2026-11-15 登録の 27 形式は未収集。21/63 は既存の被覆記録を引き継ぐ既存値）。内訳は [`README.md`](raw/google_trends/README.md) と [`metadata/data-catalog.json`](../metadata/data-catalog.json) |
| [`raw/youtube/`](raw/youtube/) | YouTube raw **catalog / declaration 上 32 run**（primary 31 + retained 1。非追跡・公開対象外、公開承認なし）。primary は liquid-only で **29/63 化合物・30/64 required query** を被覆し、欠けるのは `compound_thca` の `NO_VIDEOS`、2026-11-11 登録の 6 検索トピック 6 本、2026-11-15 登録 27 形式の 27 本（計 34 本）。CBE 331（3/354 actor requests 失敗）と CBL 269（5/296 失敗）は partial。**payload の有無は checkout ごとに異なる**。追加 14 run（CBC・CBDV + 追加 12 クエリ）の raw は machine-local の一次 checkout にあり、歴史的 18 run の payload は Git 非追跡のため clone には含まれない（catalog / declaration は committed）。クエリ設計は [`metadata/query-design.json`](../metadata/query-design.json)、宣言は [`metadata/provenance/declarations/`](../../../metadata/provenance/declarations/) |
| [`interim/google_trends/`](interim/google_trends/) | 作業中の補正ファイル |
| [`processed/youtube_monthly_counts.csv`](processed/youtube_monthly_counts.csv) | YouTube 検索結果の月別件数（HHBD リキッド run のみ。公開承認済み。raw は公開対象外） |

Google Trends の値は run ごとの相対指数（0-100）、YouTube の値は検索結果として返された動画件数であり、単位が異なる。両者を比較・合算しない。Google Trends の追加 15 語は 12ヶ月・5年とも相対 timeframe の宣言窓で収集しており、窓は近似である（[`methodology.md`](../methodology.md) §2.1.2・§2.1.3）。
