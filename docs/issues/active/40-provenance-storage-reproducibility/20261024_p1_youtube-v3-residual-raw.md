# Issue: YouTube Data API v3 由来の raw run 3 件の扱い（方針は「削除済み」と記録）

**ID:** ISS-20261024-PRV-005  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `datasets/*/data/raw/youtube/`（Git 管理外・ローカルのみ）、`datasets/youtube-consistency/README.md`、`publication/research_cbx.html`、`datasets/cbx-social-trends/README.md`  
**GitHub:** [#1](https://github.com/routeflags/japan-cannabinoid-trends/issues/1)

## 決定（owner, 2026-10-24）

**選択肢 1（3 件とも削除）**を採用する。削除は一次 checkout でのみ実行できる（YouTube raw は Git 管理外）。
削除前の記録項目と再スキャン手順は下の (a) をそのまま使う。追跡ファイルの変更は不要。

## 検証制約

YouTube raw は `.gitignore:2`（`**/data/raw/*`）の対象であり、Git 追跡層に存在しない。本 worktree にも複製されない。以下で確認済み：

```text
git ls-files 'datasets/*/data/raw/youtube/*'  →  0 件
ls datasets/cbx-social-trends/data/raw/youtube/  →  No such file or directory
ls datasets/cannabinoid-raw-collection/data/raw/youtube/  →  No such file or directory
git check-ignore -v .../20261004T135232Z-youtube-cbx-12months/records.json  →  .gitignore:2:**/data/raw/*
```

したがって下記 3 run の存在・内容・削除状態は本 worktree から検証できない。存在確認・削除・再スキャンは一次 checkout の所有者が行う。本記録は追跡層から検証できる事実と、一次側でのみ確認できる事項を分けて書く。

## 追跡層から検証できる事実

- 2026-10-12 の方針決定と「v3 由来 run の削除」は `datasets/youtube-consistency/README.md:32-45`（`collector='youtube-api'` 55 件と `run_videos` を DB から削除、集計のみ derived として `research/youtube/20261012-...md` に記録）と `research/youtube/20261012-youtube-consistency-and-cbd-timeline.md:19` に記録されている。対象は youtube-consistency の DB であり、ファイル raw 3 件への言及は無い。
- 公開ページ 13 件は同一マーカー文で「当時の raw は削除済み」と書く（`docs/reports/20261015c-publication-refresh-plan.md:366`、契約 PC-3 の検査対象）。該当行：`publication/research_cbx.html:354`（CBX 600/232 節）、`publication/research_cbx.html:553`（CBX リキッド 125 節）、`publication/research_cbd.html:613` ほか `research_cbg/cbn/crdh/crdp/h4cbh/hhbd/hhc/hhch/thc-o.html` の対応行。
- 公開 CBX 数値は追跡ドキュメントに記録済み：600 件・関連 232 件・月次内訳は `research/youtube/20261004-cbx-youtube-12months-report.md:15-42` と `publication/research_cbx.html:300-351`、125 件・月次内訳は `research/youtube/20261004-cbx-rikiddo-youtube-12months-report.md:14-41` と `publication/research_cbx.html:385-410`。パス・手法・件数の対応表は `research/youtube/20261005-academic-research-youtube-review.md:53-54,553-554,601-602`。
- 追跡集計に 3 run は含まれない：`datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv` は Apify 7 runs のみで `20261004T*` を含まず、`datasets/cbx-social-trends/data/processed/youtube_filtered_202607/filter_metadata.json` の `source_run` は `20261001T075500Z-youtube-cbx-rikiddo-v2`（Apify）で v3 ではない。
- `scripts/analysis/batch_update_pages.py:28` が `datasets/cannabinoid-raw-collection/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/records.json` を参照する。これは当該パスが執筆時に存在した痕跡であり、現在の存在を証明しない。
- `datasets/cbx-social-trends/README.md` と `methodology.md` は YouTube 出所を Apify（Actor `gJvjeCYNraSfhIaNd`、2026-10-01 フィルタ 24 件）としてのみ記述し、v3 由来 2 run の保持に触れていない。

## 一次 checkout でのみ確認できる事項（報告内容、本 worktree では未検証）

| run | 場所（一次側パス） | 報告内容 |
|---|---|---|
| `20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01` | `datasets/cannabinoid-raw-collection/data/raw/youtube/`（旧 multi-trends） | `run_metadata.json` に `api_key_name: YouTube Data API`。公開集計（youtube_*.csv）には入っていない |
| `20261004T135232Z-youtube-cbx-12months` | `datasets/cbx-social-trends/data/raw/youtube/` | 公開レポート（CBX 600 件 / 関連 232 件）の数値の出所 |
| `20261004T135457Z-youtube-cbx-rikiddo-12months` | `datasets/cbx-social-trends/data/raw/youtube/` | 同上（CBX リキッド 125 件） |

追加の未検証点：2026-10-24 に削除されたとされる `*-dated` 14 run の run ID 一覧は追跡層に記録が無く、本 worktree からは削除の事実も再スキャン結果も確認できない。

## 対応選択肢と正確な帰結

### (a) 3 件とも削除

- 一次側で削除するローカルディレクトリ（`.gitignore` 対象、追跡層への変更なし）：
  - `datasets/cannabinoid-raw-collection/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/`
  - `datasets/cbx-social-trends/data/raw/youtube/20261004T135232Z-youtube-cbx-12months/`
  - `datasets/cbx-social-trends/data/raw/youtube/20261004T135457Z-youtube-cbx-rikiddo-12months/`
- 削除前に本 issue へ記録すること：各 run の `run_metadata.json` の主要項目（source / collection_timestamp / query / parameters / raw record count）、月次 JSON の件数、`all_records.json`・`monthly_summary.json` の有無と sha256。公開数値（600/232/125 と月次内訳）は上記追跡レポートに既に記録されており、削除で失われない。
- 削除後に一次側で再スキャンし、`*-dated` 残存 0 件と `youtube/v3`・`YouTube Data API` 痕跡の有無を本 issue に記録する。
- 追跡ファイルの変更は不要：既存の「削除済み」記述（`research_cbx.html:354,553`、`research_cbd.html:613` ほか）は実体と一致する。

### (b) cbx 2 件を削除前証跡として保持し、記述を訂正

- 一次側で削除するのは CBN run 1 件のみ（(a) の 1 件目）。cbx 2 件はローカル保管のまま、再配布・公開の対象外とする。
- 追跡ファイルに必要な変更（いずれも本 worktree では行わない。文案は所有者への報告を参照）：
  - `publication/research_cbx.html:354`：「当時の raw は削除済みである」を、cbx 2 run が一次 checkout にローカル保管されている事実と derived 値である旨に訂正。
  - `publication/research_cbx.html:553`：同上（125 節）。
  - `datasets/cbx-social-trends/README.md`「既知の問題」等に v3 由来 2 run の保持事実・理由・非公開扱いを追記。現行 README・methodology は Apify 出所のみを記述しているため、追記が無いと保持の根拠が追跡層に残らない。
  - `research_cbd.html:613` ほか 11 ページのマーカー文は CBN run の削除後に実体と一致する（変更不要）。ただし 13 ページ共通文言の一括置換を行う場合は CBX 2 ページ分を除外する。

## 完了条件

- [x] `*-dated` 14 run の削除（2026-10-24、一次側での報告。本 worktree 未検証。run ID 一覧の追記が残作業）
- [x] 残り 3 件の扱いの決定（選択肢 1 = 3 件とも削除、2026-10-24）
- [ ] 実施（一次側で削除、削除前記録と再スキャンを含む）
- [ ] 実施内容（削除時の事前記録、または保持の根拠追記）の本 issue への記録
- [ ] 公開ページ・README の記述と実体の一致確認
