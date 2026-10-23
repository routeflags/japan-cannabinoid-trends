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
- 公開ページ 14 ファイル・15 箇所は同一マーカー文で「当時の raw は削除済み」と書く（`docs/reports/20261015c-publication-refresh-plan.md:366`、契約 PC-3 の検査対象）。該当行：`publication/research_cbx.html:354`（CBX 600/232 節）、`publication/research_cbx.html:553`（CBX リキッド 125 節）、`publication/research_cbd.html:613`、`publication/research_cbg.html:580`、`publication/research_cbn.html:558`、`publication/research_crdh.html:570`、`publication/research_crdp.html:486`、`publication/research_h4cbh.html:421`、`publication/research_hhbd.html:421`、`publication/research_hhc.html:509`、`publication/research_hhch.html:486`、`publication/research_thc.html:505`、`publication/research_thc-o.html:520`、`publication/research_thch.html:444`、`publication/research_thcv.html:366`。
- 公開 CBX 数値は追跡ドキュメントに記録済み：600 件・関連 232 件・月次内訳は `research/youtube/20261004-cbx-youtube-12months-report.md:15-42` と `publication/research_cbx.html:300-351`、125 件・月次内訳は `research/youtube/20261004-cbx-rikiddo-youtube-12months-report.md:14-41` と `publication/research_cbx.html:385-410`。パス・手法・件数の対応表は `research/youtube/20261005-academic-research-youtube-review.md:53-54,553-554,601-602`。
- 追跡集計に 3 run は含まれない：`datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv` は Apify 7 runs のみで `20261004T*` を含まず、`datasets/cbx-social-trends/data/processed/youtube_filtered_202607/filter_metadata.json` の `source_run` は `20261001T075500Z-youtube-cbx-rikiddo-v2`（Apify）で v3 ではない。
- `scripts/analysis/batch_update_pages.py:28` が `datasets/cannabinoid-raw-collection/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/records.json` を参照する。これは当該パスが執筆時に存在した痕跡であり、現在の存在を証明しない。
- `datasets/cbx-social-trends/README.md` と `methodology.md` は YouTube 出所を Apify（Actor `gJvjeCYNraSfhIaNd`、2026-10-01 フィルタ 24 件）としてのみ記述し、v3 由来 2 run の保持に触れていない。
- 削除対象 3 件の追跡外実測：3 パス指定の `git ls-files` で 0 件、`git ls-files 'datasets/*/data/raw/youtube/*'` で 0 件。`git check-ignore -v` は 3 パスとも `.gitignore:2:**/data/raw/*` を返す。現 worktree に該当ディレクトリは存在しない。追跡 raw は `google_trends/` のみ（`.gitignore` の再包含規則による）。
- 削除が追跡層を壊さないことの実測：`src/processing/youtube_export.py` の `build_video_export` は `raw.is_dir()` ガード（`:129-133`）で存在しない raw を空として扱い、残存 3 件は `PUBLISHABLE_RUNS`（`:54-62`）外のため `_status`（`:116-124`）で withheld 扱いとなり tracked 成果物（182 行）に含まれない（`tests/processing/test_youtube_export.py` 4 件が通過）。`scripts/analysis/batch_update_pages.py` の読込は `os.path.isfile` ガード（`:64-84`）で存在しないパスを読み飛ばす。当該 16 パスは現 worktree ですべて不在であり、削除前後で挙動は変わらない。詳細は下の「参照箇所の洗い出しと判定」を参照。

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
  - `research_cbd.html:613` ほか 12 ページのマーカー文は CBN run の削除後に実体と一致する（変更不要）。ただし 14 ファイル・15 箇所の共通文言を一括置換する場合は CBX の 2 箇所（`research_cbx.html:354`・`:553`）を除外する。

## 一次 checkout での削除手順

一次 checkout のリポジトリ直下で実行する。削除対象は Git 管理外のため `git rm` は使わず、通常の `rm -rf` で行う（`git status` に現れないのが正常）。

```bash
RUN1=datasets/cannabinoid-raw-collection/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01
RUN2=datasets/cbx-social-trends/data/raw/youtube/20261004T135232Z-youtube-cbx-12months
RUN3=datasets/cbx-social-trends/data/raw/youtube/20261004T135457Z-youtube-cbx-rikiddo-12months
```

1. 削除前記録（下の雛形を埋める。出力は本 issue に貼付し、リポジトリには書き込まない）。

```bash
for R in "$RUN1" "$RUN2" "$RUN3"; do
  echo "===== $R ====="
  ls -la "$R"
  echo "--- run_metadata.json ---"
  cat "$R/run_metadata.json"
done
for R in "$RUN1" "$RUN2" "$RUN3"; do
  echo "===== $R ====="
  sha256sum "$R"/*
done
for R in "$RUN1" "$RUN2" "$RUN3"; do
  echo "===== $R ====="
  for f in "$R"/*.json; do
    echo -n "$(basename "$f"): "
    PYTHONPATH=src python3 -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print(len(d) if isinstance(d,list) else 'dict keys='+str(len(d)) if isinstance(d,dict) else type(d).__name__)" "$f"
  done
done
```

2. 削除。

```bash
rm -rf "$RUN1" "$RUN2" "$RUN3"
```

3. 再スキャンし、結果を本 issue に記録する。

```bash
echo "--- 残存 youtube raw ---"
ls -d datasets/*/data/raw/youtube/*/ 2>&1
echo "--- *-dated 残存数（0 を期待） ---"
find datasets -type d -name "*-dated" 2>/dev/null | wc -l
echo "--- YouTube Data API 痕跡（有無を記録） ---"
grep -rln "YouTube Data API" datasets/cannabinoid-raw-collection/data/raw/youtube/ datasets/cbx-social-trends/data/raw/youtube/ 2>/dev/null
echo "--- git status（上記削除では変化しないのが正常。Git 管理外のため） ---"
git --no-optional-locks status --short
```

## 削除前記録の雛形

1 run につき 1 表。値は推測で埋めず、空欄または `<記入>` のまま残す。公開数値（600/232/125 と月次内訳）は追跡レポートに記録済みであり、削除で失われない（追跡層の事実を参照）。

### run 1: `20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01`

| 項目 | 記録値 |
|---|---|
| 配置（一次側） | `datasets/cannabinoid-raw-collection/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/` |
| source | `<記入>` |
| collection_timestamp | `<記入>` |
| observation_period | `<記入>` |
| query | `<記入>` |
| filters / parameters | `<記入>` |
| raw record count | `<記入>` |
| 月次 JSON の件数 | `<記入>` |
| `all_records.json` の有無と sha256 | `<記入>` |
| `monthly_summary.json` の有無と sha256 | `<記入>` |

### run 2: `20261004T135232Z-youtube-cbx-12months`

| 項目 | 記録値 |
|---|---|
| 配置（一次側） | `datasets/cbx-social-trends/data/raw/youtube/20261004T135232Z-youtube-cbx-12months/` |
| source | `<記入>` |
| collection_timestamp | `<記入>` |
| observation_period | `<記入>` |
| query | `<記入>` |
| filters / parameters | `<記入>` |
| raw record count | `<記入>` |
| 月次 JSON の件数 | `<記入>` |
| `all_records.json` の有無と sha256 | `<記入>` |
| `monthly_summary.json` の有無と sha256 | `<記入>` |

### run 3: `20261004T135457Z-youtube-cbx-rikiddo-12months`

| 項目 | 記録値 |
|---|---|
| 配置（一次側） | `datasets/cbx-social-trends/data/raw/youtube/20261004T135457Z-youtube-cbx-rikiddo-12months/` |
| source | `<記入>` |
| collection_timestamp | `<記入>` |
| observation_period | `<記入>` |
| query | `<記入>` |
| filters / parameters | `<記入>` |
| raw record count | `<記入>` |
| 月次 JSON の件数 | `<記入>` |
| `all_records.json` の有無と sha256 | `<記入>` |
| `monthly_summary.json` の有無と sha256 | `<記入>` |

チェックリスト：

- [ ] `run_metadata.json` の主要項目を転記した
- [ ] 月次 JSON の件数を記録した
- [ ] `all_records.json`・`monthly_summary.json` の有無と sha256 を記録した
- [ ] 公開数値（run 2・3 は 600/232/125 と月次内訳）が追跡レポートに残ることを確認した
- [ ] 上記を本 issue に貼付した

## 参照箇所の洗い出しと判定

run id（`20261004T132844Z`・`20261004T135232Z`・`20261004T135457Z`）および `data/raw/youtube` の追跡層（`git grep`） sweep 結果。判定は削除後の成立性による。

| 参照箇所 | 参照内容 | 削除後の成立性 | 要修正 |
|---|---|---|---|
| `scripts/analysis/batch_update_pages.py:28`（同種パス計 16 件） | CBN run の `records.json` を `YOUTUBE_PATHS` に列挙 | 読込は `os.path.isfile` ガード（`:64-84`）で不存在時読飛ばし・空→節なし。現 worktree で 16 件全不在のため挙動不変 | 不要 |
| 公開ページ 14 ファイル・15 箇所（上記行番号） | 「当時の raw は削除済み」マーカー | 削除により実体と一致 | 不要 |
| `datasets/cbx-social-trends/README.md`・`methodology.md` | YouTube 出所を Apify のみとして記述 | v3 残存に言及なし、削除後も成立 | 不要 |
| `src/processing/youtube_export.py`（`PUBLISHABLE_RUNS`・`EXCLUSION_REASONS`・`V3_DERIVED_MARKER`・`build_video_export`） | run 単位分類・集計 | 残存 3 件は withheld 扱いで成果物外。`build` は欠損耐性あり（試験通過） | 不要 |
| `src/processing/reproduce.py:395,413`・`src/processing/cli.py` | ディレクトリ単位の `missing_inputs` 記述 | run 固有名なし | 不要 |
| `project.json:467-667`・`docs/data-dictionary.md:274` | ディレクトリ単位の出所記述 | run 固有名なし | 不要 |
| `research/youtube/*`（収集レポート・レビュー） | 収集時点の記録 | 歴史的収集記録として成立 | 不要 |
| `tests/processing/test_youtube_export.py`・`tests/validation/test_release_archive_check.py:75` | 合成 fixture・別 dataset | 実 raw 非依存 | 不要 |
| `scripts/git-hooks/pre-commit:81`・`scripts/collect-youtube-*.sh`・`.github/skills/research-youtube-search`・`docs/specs/youtube-*-setup-guide.md` | 検証トリガ・新規収集用パス | 削除対象に非依存 | 不要 |
| `docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_study-rename-followups.md:25` | 旧 study 名の dir 言及 | 追跡外パス、dir 単位 | 不要 |

要修正：無し（0 件）。

## `*-dated` 14 run の一覧復元

復元可能。追跡層に残る記録から 14 件の run id を再構成できる。ただし削除実行時の対象ログ自体は追跡層に無いため、一次側での照合が残る。

根拠：

- `b8ea780` 時点の `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv` に 14 件が `*-dated` かつ status `derived from YouTube Data API v3, withdrawn 2026-10-12` として列挙されている。
- `13b8afe` のメッセージは `fourteen named *-dated runs` の削除と再スキャンでの `*-dated` 残存 0 件を記録しており、件数・命名規則・削除理由が一致する。
- うち 2 件（`20261009T065307Z`・`20261009T160738Z` の `youtube-cbd-dated`、各 24・30 件）は `docs/reports/20261015d-cbd-page-provenance-reconciliation.md:80-81` に件数つきで記録されている。
- `37e1528` で現行 `youtube_runs.csv` は公開 7 runs のみに縮小されており、現行追跡層に一覧は無い。

一覧（`b8ea780:datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv` より。status は全件 `derived from YouTube Data API v3, withdrawn 2026-10-12`）：

1. `20261009T065307Z-youtube-cbd-dated`
2. `20261009T160738Z-youtube-cbd-dated`
3. `20261009T160738Z-youtube-cbg-dated`
4. `20261009T160738Z-youtube-cbn-dated`
5. `20261009T160738Z-youtube-crdh-dated`
6. `20261009T160738Z-youtube-crdp-dated`
7. `20261009T160738Z-youtube-h4cbh-dated`
8. `20261009T160738Z-youtube-hhbd-dated`
9. `20261009T160738Z-youtube-hhc-dated`
10. `20261009T160738Z-youtube-hhch-dated`
11. `20261009T160738Z-youtube-thc-dated`
12. `20261009T160738Z-youtube-thc-o-dated`
13. `20261009T160738Z-youtube-thch-dated`
14. `20261009T160738Z-youtube-thcv-dated`

不確実性：上記は件数・命名・理由の一致による再構成であり、削除コマンドの対象ログでは無い。一次側にシェル履歴・バックアップが残っていれば照合すること。照合できなければこの一覧を確定記録として扱い、新たな推測で補わない。

## 完了条件

- [x] `*-dated` 14 run の削除（2026-10-24、一次側での報告。本 worktree 未検証。run ID 一覧は「`*-dated` 14 run の一覧復元」に記録。削除実行ログ自体は追跡層に無いため一次側での照合が残作業）
- [x] 残り 3 件の扱いの決定（選択肢 1 = 3 件とも削除、2026-10-24）
- [ ] 実施（一次側で削除、削除前記録と再スキャンを含む）
- [ ] 実施内容（削除時の事前記録、または保持の根拠追記）の本 issue への記録
- [ ] 公開ページ・README の記述と実体の一致確認
