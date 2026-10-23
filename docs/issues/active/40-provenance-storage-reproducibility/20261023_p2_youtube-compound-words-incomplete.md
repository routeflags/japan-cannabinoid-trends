# Issue: YouTube の化合物語が 5/13 語しか無い

**ID:** ISS-20261023-YT-010  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`methodology.md` §2.3  
**GitHub:** [#6](https://github.com/routeflags/japan-cannabinoid-trends/issues/6)

## 概要

YouTube は化合物語 5 語（CBD / THC / CBG / HHC / THCV）しか収集していない。
Google Trends は 12ヶ月・5年とも 13 語、X は 7 語そろっているので、**YouTube だけ 8 語欠けている**。

## 実測

- 収集済み（`youtube_runs.csv`、7 run = 化合物語 5 + 製品語 2）: CBD 22 / THC 25 / CBG 34 / HHC 28 / THCV 23。
- **未収集（8 語）**: THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH。

## 収集条件（既存と同じ）

Actor `gJvjeCYNraSfhIaNd`（`danek/youtube-search`）、1 run = 1 `search_term`、`max_videos` 50〜100、
コストは `$0.0005/件` + start（8 語 × 100 件で最大 ~$0.40）。
比較可能性のため actor と `max_videos` の方針は既存に合わせる。

## 選択肢

1. 8 語を追加収集する（1 語 1 run、`youtube-export` で 2 表を再生成）。新規収集なので owner 判断。
2. YouTube は 5 語を意図的な範囲として methodology に明記する。

## 完了条件

- [ ] 方針の決定（owner）
- [ ] 実施（8 run の収集 + `youtube-export`、または文書の明記）
- [ ] README のキーワード表と `youtube_runs.csv` が一致している
