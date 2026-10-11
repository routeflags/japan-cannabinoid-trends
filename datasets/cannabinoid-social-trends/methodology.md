# methodology — cannabinoid-social-trends

## 1. 研究設計

本 dataset は**自然実験**（natural experiment）設計による X (Twitter) データ収集である。
各カンナビノイドの指定薬物化（または規制強化）を介入とし、
介入前後の X 上での言及量・内容を比較する。

| 要素 | 設計 |
|------|------|
| 介入 | 指定薬物化等の規制イベント（例: CBN = 2026-06-01） |
| 処置系列 | 規制対象化合物の X 検索結果（介入前窓 + 介入後窓） |
| 対照系列 | **CBG**（指定を受けていない化合物）を同一方法で同時収集 |
| 比較概念 | 差分の差分法（DiD）の概念（ただし n が小さく統計的検定は行わない） |

介入前後の各窓は同一の検索パラメータで収集し、
季節性・プラットフォーム全体の利用量変動の影響を対照系列で緩和することを狙う。

## 2. 収集手順

- **ツール**: Apify（X 検索系 Actor。run ごとに Actor ID を記録）
- **単位**: 1 run = 1 化合物 × 1 時間窓（pre / post / control）
- **上限**: 各 run 約 100 件（Actor の取得上限による）
- **run-id**: `YYYYMMDDTHHMMSSZ-<内容>` 形式で一意に振番
  （2026-10-04 の初期 2 run は規約化以前の `YYYYMMDD-<内容>` 形式）
- **成果物**: `records.json`（投稿 items リスト）+ `run_metadata.json`
  （Apify run の `id` / `status` / `usageTotalUsd` / 開始終了時刻）

収集パラメータの完全な記録は run ディレクトリ内の metadata に依存する。
`run_metadata.json` が存在しない run（例: `20261008T102022Z-crdh`）では
検索クエリ等のパラメータが後から復元できない可能性がある（既知の制限）。

## 3. 前処理・重複排除

**raw は無加工で保持する**（AGENTS.md の raw 不変原則）。
tweet_id ベースの重複排除は分析スクリプト側
（[`scripts/analysis/regulatory_comparison.py`](../../scripts/analysis/regulatory_comparison.py)）で行う。
本 dataset には interim / processed レイヤーはまだ存在しない。

## 4. 分析方法

[`scripts/analysis/regulatory_comparison.py`](../../scripts/analysis/regulatory_comparison.py) が
pre / post / control の 3 系列を読み込み、以下を算出する:

- 各系列の投稿数・平均エンゲージメント（いいね等）
- 処置化合物の post 前後差と、対照（CBG）の post 前後差の比較
  （「control_comparison」: 比率で出力）

分析結果は [`research/x/`](../../research/x/) 配下のレポート
（例: `20261006-cbn-natural-experiment.md`, `20261008-regulatory-comparison-batch2.md`）に記述される。

## 5. 制限事項

1. **サンプルサイズ**: 各系列 最大約 100 件。統計的検定は行わず、
   記述的比較にとどまる
2. **非決定的ソース**: X 検索は同一クエリでも再実行結果が変わる。
   run を跨いだ結果の単純比較には注意が必要
3. **母集団不明**: X 全投稿を網羅するものではなく、検索結果サンプルである
4. **非因果的解釈**: 規制前後の差は規制以外の要因
   （市場イベント・バズ・他の化合物の話題性）を含みうる。
   レポートでは「関連」または「時系列的並行」と記述し、因果主張はしない
5. **投稿者プライバシー**: raw には screen_name 等を含む。
   公開時は再配布権利・プライバシーのレビューが必要
   （[`docs/specs/raw-data-policy.md`](../../docs/specs/raw-data-policy.md) 参照）

## 6. 再現性

- run 単位の raw + `run_metadata.json` により、
  どのデータがどの分析に使われたかは追跡可能
- 分析スクリプトは raw パスを明示指定するため、再実行可能
  （ただし raw 再取得は非決定的ソースのため同一結果を保証しない）
