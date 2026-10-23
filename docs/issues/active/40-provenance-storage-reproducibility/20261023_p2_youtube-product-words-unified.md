# Issue: 製品語がプラットフォーム間で異なる（リキッド / オイル）

**ID:** ISS-20261023-YT-011  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`README.md` のキーワード表, `methodology.md` §2.3・§6  
**GitHub:** [#7](https://github.com/routeflags/japan-cannabinoid-trends/issues/7)

## 概要

同じ製品軸をプラットフォームごとに別の語で測っている。Google Trends は単独系列として「化合物語 + ` リキッド`」のみ（12ヶ月 13 語、5年 5 語）を収集し、YouTube は「オイル」2 語（`CBD オイル` / `THC オイル`）のみを収集している。X は製品語を持たない。提案は製品語を「化合物語 + ` リキッド`」に統一し、YouTube で不足する 13 run を追加収集すること。既存オイル 2 run の扱いは未決。raw は不変とする（除外は公開集計層のみ）。

## 実測（2026-10-23 検証）

| プラットフォーム | 製品語 | 語数 | 証拠 |
|---|---|---:|---|
| Google Trends（12ヶ月単独系列） | リキッド | 13 | phase-a 5 語 + phase-b 8 語の `run_metadata.json` |
| Google Trends（5年単独系列） | リキッド | 5 | `20261012T064246Z-...-5y-main5/run_metadata.json` |
| Google Trends（`records_*.json` 全体） | オイル | 0 | 下記コマンドで 0 件 |
| YouTube（`youtube_runs.csv`） | オイル | 2 | `20261002T064905Z-youtube-cbd-オイル`（23 件）、`20261002T064911Z-youtube-thc-オイル`（27 件） |
| YouTube（`youtube_runs.csv`） | リキッド | 0 | `grep リキッド` は 0 件 |
| X | 製品語なし | 0 | — |

検証コマンド（いずれも `PYTHONPATH=src python3` で実行、`.venv` 不使用）:

```bash
# records_*.json / comparison_*.json（79 件）中の語彙ヒット数
find datasets -path '*data/raw/google_trends*' \( -name 'records_*.json' -o -name 'comparison_*.json' \) | wc -l  # 79
grep -l 'オイル' $(find datasets -path '*data/raw/google_trends*' \( -name 'records_*.json' -o -name 'comparison_*.json' \))  # 1 件のみ
```

- `オイル` を含む唯一のファイルは `20261012T054920Z-google-trends-notation-presurvey/comparison_notation.json`（表記ゆれ事前調査）。単独系列（`records_*.json`）のクエリ語としてのオイルは 0。
- `リキッド` を含むのは 31 件（phase-a 12 件、phase-b 12 件、5y-main5 6 件、cbx variance-check 2 件を含む）。
- 12ヶ月の 13 語は `CBD / THC / CBG / CBN / HHC / THCV / THC-O / THCH / H4CBH / HHBD / HHCH / CRDP / CRDH` + ` リキッド`。5年は先頭 5 語のみ。残り 8 語の 5年未収集は `ISS-20261023-GT-008`。
- 注意（未決の材料）: presurvey は `CBD リキッド` と `CBD オイル` を直接比較し、`comparison_notation.json` 内の平均スコアは `CBD リキッド: 25` に対して `CBD オイル: 62` が最高と記録されている。リキッドへの統一は検索ボリュームではなく製品軸の一貫性を取る選択になる。原因の解釈はしない（AGENTS.md: 時間相関から因果を推論しない）。

## 前例：リキッドは同一 actor で YouTube 取得可能

CBX study が `CBX リキッド` を Apify actor `gJvjeCYNraSfhIaNd`（danek/youtube-search）で収集済み。`research/x/20261005-phase2-analysis-results.md` より引用:

> "Japanese-language YouTube data for cannabinoid keywords (CBD オイル, CBX リキッド, カンナビノイド) was collected via Apify actor gJvjeCYNraSfhIaNd, yielding 60 records per keyword with confirmed Japanese-language content."

| キーワード | 総件数 | ユニークID | 日本語コンテンツ |
|-----------|:------:|:----------:|:---------------:|
| CBD オイル | 60 | 28 | ✅ 確認 |
| CBX リキッド | 60 | 23 | ✅ 確認 |
| カンナビノイド | 60 | 24 | ✅ 確認 |

> "日本語キーワードを使用することで、日本語圏のカンナビノイド関連動画を収集可能。YouTube API のクォータ制限を Apify で回避。"

ただし不安定性の記録もある（AGENTS.md: 同一クエリでも結果は非決定論的）:

- `datasets/cbx-social-trends/methodology.md` §3.4: 2026-09-07 の `CBX リキッド`（`max_videos: 50`）は “returned 0 CBX-related” と記録。
- `datasets/cbx-social-trends/data/processed/youtube_filtered_202607/filter_metadata.json`: 別 run（`20261001T075500Z-youtube-cbx-rikiddo-v2`）は取得 26 件 → フィルタ後 24 件。

すなわち「リキッド語は YouTube でヒットする」こと自体は 2 件の独立した証拠で裏付けられるが、件数は run ごとに変動する。前例は actor `gJvjeCYNraSfhIaNd` のものであり、現行パイプラインの採用 actor（下記）とは異なる。

## オイル 2 run の除外：必要な変更（未適用）

`src/processing/youtube_export.py` の公開可否は allowlist 制。`youtube_runs.csv` / `youtube_videos.csv` に書かれるのは `PUBLISHABLE_RUNS` に載った run のみで、`EXCLUSION_REASONS` に載った run は集計から外れる（理由はコード内と operator summary に残り、データには書かれない）。raw ディレクトリには触れない。

必要なコード変更（`PUBLISHABLE_RUNS` から 2 行削除、`EXCLUSION_REASONS` に 2 行追加）:

```python
# 削除（PUBLISHABLE_RUNS から）:
#   "20261002T064905Z-youtube-cbd-オイル": "CBD オイル",
#   "20261002T064911Z-youtube-thc-オイル": "THC オイル",
# 追加（EXCLUSION_REASONS に）:
#   "20261002T064905Z-youtube-cbd-オイル": "superseded by liquid vocabulary, excluded from evidence (ISS-20261023-YT-011 / GitHub #7)",
#   "20261002T064911Z-youtube-thc-オイル": "superseded by liquid vocabulary, excluded from evidence (ISS-20261023-YT-011 / GitHub #7)",
```

再生成後（`python -m processing.cli youtube-export`）のテーブル内容:

| 成果物 | 現行 | 除外後 |
|---|---:|---:|
| `youtube_runs.csv` | 7 行 | **5 行**（オイル 2 行が消える） |
| `youtube_videos.csv` | 182 行（22+25+34+28+23+23+27） | **132 行**（オイル 50 行 = 23+27 が消える） |
| `withheld`（summary のみ、データに書かれない） | 6 run | 8 run |

これは公開集計層の変更であり、**publication gate の対象**。`make audit-publication` の再実行、件数の突合せ（processed ⇄ raw）、`methodology.md` §2.3・§6 と README キーワード表の更新、制限事項の文書化が必要。COL-030 §4.1 により、行単位の動画集計であっても公開レビュー承認までは公開しない。

## コストと経路（13 リキッド run）

単価の根拠は `.github/skills/apify-youtube-search/SKILL.md`（actor `gJvjeCYNraSfhIaNd`）: 起動 `$0.00005`/回 + `$0.0005`/件（FREE）、GOLD 以上は `$0.0002`/件。

| `max_videos` | 上限件数（13 run） | FREE 目安 | GOLD 目安 |
|---:|---:|---:|---:|
| 50 | 650 件 | **約 $0.33**（`650×0.0005 + 13×0.00005`） | 約 $0.13 |
| 100 | 1300 件 | **約 $0.65**（`1300×0.0005 + 13×0.00005`） | 約 $0.26 |

既存 YouTube 7 run の `collection-summary.md` §3.1 では `max_videos` 50（CBG/HHC/THCV/オイル2）と 100（CBD/THC）が混在。13 語の `max_videos` 方針は未決。

経路の制約:

- YouTube 収集は **`collect --live` では実行できない**。`src/collection/adapters/youtube/apify_csv.py` の `YouTubeApifyCsvAdapter.collect()` は常に `LIVE_TRANSPORT_UNIMPLEMENTED` で失敗し、`request.py` は dry-run の input 計画のみで送信しない（fail-closed）。
- 正規経路は CSV handover: 外部で actor を実行 → `build_csv_run` で `staging-declaration-v1` を作成 → `make stage DECLARATION=<file>` → `make adopt-all` → `youtube-export` 再生成。
- actor 選択は未決。前例は `gJvjeCYNraSfhIaNd`（$0.50/1,000件）だが、現行パイプラインの採用 actor は `h7sDV53CddomktSi5`（streamers/youtube-scraper、日付フィルタ対応、`config/collectors.json` 登録、**$2.40/1,000件** = 約4.8倍）。同じ 13 run（上限 50/100）なら上限目安は約 $1.56 / $3.12。どちらを使うかは owner 判断。
- いずれも Apify トークン・支払い方法・コストガード・明示的承認が前提。**本タスクでは収集を実行していない。**

## 選択肢

1. **YouTube にリキッド 13 語を追加収集し、オイル 2 run は公開集計から外す**（語彙を一本化）。新規コストは上限約 $0.33（50件）〜 $0.65（100件、FREE・danek actor）。`youtube_videos.csv` は 132 行 + 新規 13 run 分になる。除外は上記の `EXCLUSION_REASONS` 変更 + gate 再実行。
2. **リキッド 13 語を追加し、オイルは別軸として残す**（両方を公開）。新規コストは同じ。`youtube_videos.csv` は 182 行 + 新規分。ただし「オイル軸は n=2 語のみ・今後の追加なし」という偏った軸を公開物として維持する理由の文書化が必要。
3. **語彙統一はせず、現状を methodology に明記する**（収集コスト $0）。プラットフォーム間で製品語が異なることを制限事項として記録し、比較時は語彙差を明示する。

## 完了条件

- [ ] 方針の決定（owner）: （a）統一先の語彙（リキッド vs 現状維持。presurvey の `CBD オイル: 62 > CBD リキッド: 25` を踏まえる）、（b）オイル 2 run の扱い（除外 / 別軸残存。除外なら上記パッチ適用 + gate 再実行）、（c）X に製品語を追加するか（本 issue の範囲外だが owner が判断。現状 0）、（d）新規 13 run の actor（danek `gJvje...` vs scraper `h7sDV5...`）と `max_videos`（50/100）
- [ ] 実施（YouTube のリキッド収集は handover 経路 + `make stage` / `make adopt-all` + `youtube-export`、または文書の明記）
- [ ] README のキーワード表で製品語がプラットフォーム間で説明可能な状態になっている
