# research/ — 調査レポート・戦略文書

トピック別に整理した調査成果物。ファイル名の `YYYYMMDD-` 接頭辞は作成日。

| ディレクトリ | 内容 |
|--------------|------|
| [`google-trends/`](./google-trends/) | Google Trends 由来のレポート（言及開始時期・比較・5年ベースライン） |
| [`youtube/`](./youtube/) | YouTube 収集の計画・レポート・学術レビュー |
| [`x/`](./x/) | X (Twitter) データの分析・分類・規制前後比較（kappa 検証等、分析成果 JSON を含む） |
| [`strategy/`](./strategy/) | データ収集戦略・優先順位・カバレッジ計画・リリース英文サマリ |
| [`apify/`](./apify/) | Apify Actor 評価記録 |
| [`citation/`](./citation/) | 引用機会・ステークホルダーマトリクス |
| [`regulatory-status/`](./regulatory-status/) | 化合物別の規制状況調査 |
| `citation-tracker.md` | 引用トラッカー（更新 maintained ドキュメント） |

注意:

- ここに置くのは **ANALYSIS レイヤー**（統計・解釈を含む成果物）。
  source observation（RAW）は各 `datasets/<study-id>/data/raw/` に置く
- データセット由来のレポートは原則として
  `datasets/<study-id>/analysis/` が第一候補。
  `research/` はリポジトリ横断・複数 dataset にまたがる調査に使う
- 規制情報の一次整理は `research/regulatory-status/`、
  知識グラフ化は `metadata/taxonomy/thc-regulatory-knowledge-graph.json` を参照
