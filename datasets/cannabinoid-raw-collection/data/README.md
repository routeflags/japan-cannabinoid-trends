# data

この研究のデータ置き場。raw は不変の原記録、interim は補正作業、processed は再現可能な集計成果物。

raw は machine-local（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）であり、clone によっては `raw/youtube/` が存在しない。catalog / declaration は committed な事実、payload はその checkout の証跡として分けて読む。

| ディレクトリ | 内容 |
|---|---|
| [`raw/google_trends/`](raw/google_trends/) | 追跡する Google Trends raw **109 run directories**（catalog採用77、manifestなし32）。登録63トピックの被覆は5年29/63・12ヶ月30/63。候補27形式は12ヶ月9 adopted /18 `NO_DATA`、5年0 adopted（窓guard停止後に1 queryをHTTP 429で3回、26 query未試行）。12ヶ月21/63のinherited baselineは既存値。2026-11-11登録6検索topicは未収集。詳細は[`README.md`](raw/google_trends/README.md)と[`metadata/data-catalog.json`](../metadata/data-catalog.json) |
| [`raw/youtube/`](raw/youtube/) | YouTube raw **catalog / declaration上51 adopted run**（primary50 + retained1。rawは`git_untracked`・公開対象外）。primaryはliquid-onlyで**48/63 compounds・49/64 required queries**を被覆。未被覆15は`compound_thca`の`NO_VIDEOS`、2026-11-11登録6 query、候補形式の8 `NO_VIDEOS`。候補27 queryは19 adopted、全27試行済み。CBE331（3/354 actor requests失敗）とCBL269（5/296失敗）はpartial。payloadの有無はcheckoutごとに異なり、11-10追加14 runと候補形式19 runのrawはこのcheckout、歴史的18 runのpayloadはcloneに含まれない（declarations / catalogはtracked）。query designは[`metadata/query-design.json`](../metadata/query-design.json)、declarationsは[`metadata/provenance/declarations/`](../../../metadata/provenance/declarations/) |
| [`interim/google_trends/`](interim/google_trends/) | 作業中の補正ファイル |
| [`processed/youtube_monthly_counts.csv`](processed/youtube_monthly_counts.csv) | YouTube 検索結果の月別件数（HHBD リキッド run のみ。公開承認済み。raw は公開対象外） |

Google Trends の値は run ごとの相対指数（0-100）、YouTube の値は検索結果として返された動画件数であり、単位が異なる。両者を比較・合算しない。Google Trends の追加 15 語は 12ヶ月・5年とも相対 timeframe の宣言窓で収集しており、窓は近似である（[`methodology.md`](../methodology.md) §2.1.2・§2.1.3）。
