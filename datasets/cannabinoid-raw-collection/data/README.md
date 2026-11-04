# data

この研究のデータ置き場。raw は不変の原記録、interim は補正作業、processed は再現可能な集計成果物。

raw は machine-local（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）であり、clone によっては `raw/youtube/` が存在しない。catalog / declaration は committed な事実、payload はその checkout の証跡として分けて読む。

| ディレクトリ | 内容 |
|---|---|
| [`raw/google_trends/`](raw/google_trends/) | 追跡する Google トレンド raw 58 run |
| [`raw/youtube/`](raw/youtube/) | YouTube raw 18 run（非追跡・公開対象外）。primary は liquid 17 run / 15 化合物、裸の `HHC` 1 run は保持するが primary 外。クエリ設計は [`metadata/query-design.json`](../metadata/query-design.json)、宣言は [`metadata/provenance/declarations/`](../../../metadata/provenance/declarations/) |
| [`interim/google_trends/`](interim/google_trends/) | 作業中の補正ファイル |
| [`processed/youtube_monthly_counts.csv`](processed/youtube_monthly_counts.csv) | YouTube 検索結果の月別件数（公開承認済み。raw は公開対象外） |
