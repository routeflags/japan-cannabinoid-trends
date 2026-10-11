# x-26week-trends — CBX リキッド X 26週間トレンド調査

CBX リキッドに関する X (Twitter) 投稿を 26 週間分（2026-03-19 〜 2026-09-17）に
わたって週次取得し、言及量の推移・出現時期を調査した study。

- ステータス: **調査完了・分析レポートのみ保持**（raw レコードは本リポジトリに未収蔵）
- 収集元: Apify（X 検索）
- 成果物: [`analysis/`](./analysis/) の計画書・レポート

## 構成

```
datasets/x-26week-trends/
├── analysis/
│   ├── x_26week_trend_plan.md    # 調査計画書（2026-09-17 作成）
│   └── x_26week_trend_report.md  # 調査結果レポート（2026-09-18 取得）
├── data/
│   ├── raw/.gitkeep              # raw レコードは未収蔵（下記参照）
│   └── interim/.gitkeep
└── README.md
```

## 収集条件（レポート記載のとおり）

| 項目 | 値 |
|------|-----|
| 対象キーワード | `CBX リキッド` |
| 対象期間 | 2026-03-19 〜 2026-09-17（26 週間、週次窓） |
| Actor | `cPYLH3QT9GyzKhB4S`（patient_discovery/twitter-search） |
| section | `latest`（投稿日時降順） |
| maxPages | `5`（最大約 100 件/週） |
| 結果 | 総取得 251 件 → tweet_id 重複排除後 231 件 |

## raw データについて（重要）

本 study の raw 投稿データは**このリポジトリには保存されていない**。
収集は旧ワークスペース
（`projects/ec/research/20260917/`、リポジトリ外）で実施され、
本リポジトリには計画書と結果レポートのみが移管された。
`data/raw/` は空（`.gitkeep` のみ）であり、これは「収集失敗」ではなく
「raw 未収蔵」の状態である。

raw を将来的に収蔵する場合は、
[`docs/specs/raw-data-policy.md`](../../docs/specs/raw-data-policy.md) に基づき
再配布権利・プライバシーのレビューを完了したうえで行うこと。

## 主要な調査結果（レポートより）

- 2026 年 3〜4 月: 投稿なし / 5 月: 最初の投稿 2 件 / 7 月: 急増（100 件/月）
- 有データ期間は 2026-05 〜 2026-09。上位投稿者は販売告知系が中心
- 詳細・週次集計は [`analysis/x_26week_trend_report.md`](./analysis/x_26week_trend_report.md)

## 制約

- 取得方法が「週次 `since:`/`until:` + latest」であり、
  旧来の「日別 latest」データ（例: cbx-social-trends 202608）とは方式が異なる
  （レポート §5 の注意書き参照）
- X 検索は非決定的。再収集しても同一結果は保証されない
- 時系列の観察であり、急増の**原因**を示すものではない

## 関連

- 収集方法の詳細: [methodology.md](./methodology.md)
- 後続のカバレッジ拡張計画: [`research/strategy/20261002-keyword-coverage-expansion.md`](../../research/strategy/20261002-keyword-coverage-expansion.md)
