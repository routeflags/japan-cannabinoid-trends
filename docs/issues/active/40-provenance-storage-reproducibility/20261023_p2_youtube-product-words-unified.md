# Issue: 製品語がプラットフォーム間で異なる（リキッド / オイル）

**ID:** ISS-20261023-YT-011  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`README.md` のキーワード表, `methodology.md` §2.3・§6  
**GitHub:** [#7](https://github.com/routeflags/japan-cannabinoid-trends/issues/7)

## 概要

同じ製品軸をプラットフォームごとに別の語で測っている。
Google Trends は「リキッド」13 語（12ヶ月）・「オイル」は 0 語、
YouTube は「オイル」2 語（`CBD オイル` / `THC オイル`）・「リキッド」は 0 語。
製品語を「**化合物語 + ` リキッド`**」に統一し、YouTube 側の不足分を取得する。

## 実測

| プラットフォーム | 製品語 | 語数 |
|---|---|---:|
| Google Trends（12ヶ月） | リキッド | 13（8 語が系列、5 語は no data） |
| Google Trends（5年） | リキッド | 5（残り 8 語は未収集 = `ISS-20261023-GT-008`） |
| YouTube | **オイル** | 2 |
| X | なし | 0 |

- Google Trends の `records_*.json` に「オイル」は 0 件。YouTube に「リキッド」は 0 件。
- **同じ actor でリキッドを引いた前例がある**: CBX study が `gJvjeCYNraSfhIaNd` で `CBX リキッド` を収集済み
  （`research/x/20261005-phase2-analysis-results.md`）。

## 統一の内容

- 製品語の正は「化合物語 + ` リキッド`」（Google Trends の 12ヶ月と同じ 13 語）。
- YouTube は 13 語すべて未収集なので 13 run を追加（1 語 1 run、`max_videos` は既存方針）。
  コスト目安は `$0.0005/件` + start で最大 ~$0.65。
- 既存の「オイル」2 run（raw は不変）の扱いは未決:
  (a) 公開集計から外して `EXCLUSION_REASONS` に理由を記録 / (b) 別軸として残す / (c) 残して README に旧語彙と注記。
- X は製品語を持たない。追加するかは別途判断。

## 選択肢

1. YouTube にリキッド 13 語を追加収集し、オイル 2 run は公開集計から外す（語彙を一本化）。
2. リキッド 13 語を追加し、オイルは別軸として残す（両方を公開）。
3. 語彙統一はせず、現状を methodology に明記する。

## 完了条件

- [ ] 方針の決定（owner）: 統一先の語彙、オイル 2 run の扱い、X の扱い
- [ ] 実施（YouTube のリキッド収集 + `youtube-export`、または文書の明記）
- [ ] README のキーワード表で製品語がプラットフォーム間で説明可能な状態になっている
