# Issue: 製品語がプラットフォーム間で異なる（リキッド / オイル）

**ID:** ISS-20261023-YT-011  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`README.md` のキーワード表, `methodology.md` §2.3・§6  
**GitHub:** [#7](https://github.com/routeflags/japan-cannabinoid-trends/issues/7)

## 決定（owner, 2026-10-24）

**選択肢 1（リキッド 13 語を追加収集し、オイル 2 run を公開集計から外す）**を採用する。
オイル 2 run の除外は、**置換となる 13 リキッド run が採用されてから**適用する（それまでは公開集計に残す）。
actor と `max_videos` は既存 7 run に合わせる（`gJvjeCYNraSfhIaNd`、CBD/THC 100・他 50）。別 actor を使う場合は別途指示が必要。

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

## 経路（13 リキッド run）

既存 YouTube 7 run の `collection-summary.md` §3 では `max_videos` 50（CBG/HHC/THCV/オイル2）と 100（CBD/THC）が混在。13 語の `max_videos` 方針は未決。

経路の制約:

- YouTube 収集は **`collect --live` では実行できない**。`src/collection/adapters/youtube/apify_csv.py` の `YouTubeApifyCsvAdapter.collect()` は常に `LIVE_TRANSPORT_UNIMPLEMENTED` で失敗し、`request.py` は dry-run の input 計画のみで送信しない（fail-closed）。
- 正規経路は CSV handover: 外部で actor を実行 → `build_csv_run` で `staging-declaration-v1` を作成 → `make stage DECLARATION=<file>` → `make adopt-all` → `youtube-export` 再生成。
- actor 選択は未決。前例は `gJvjeCYNraSfhIaNd`（danek/youtube-search。入力は `search_term` + `max_videos` のみ）だが、現行パイプラインの採用 actor は `h7sDV53CddomktSi5`（streamers/youtube-scraper、日付フィルタ対応、`config/collectors.json` 登録）。**日付フィルタを取るか、入力の単純さを取るか**が選択の分岐で、どちらを使うかは owner 判断。
- いずれも Apify トークンと明示的承認が前提。**本タスクでは収集を実行していない。**

## 選択肢

1. **YouTube にリキッド 13 語を追加収集し、オイル 2 run は公開集計から外す**（語彙を一本化）。`youtube_videos.csv` は 132 行 + 新規 13 run 分になる。除外は上記の `EXCLUSION_REASONS` 変更 + gate 再実行。
2. **リキッド 13 語を追加し、オイルは別軸として残す**（両方を公開）。`youtube_videos.csv` は 182 行 + 新規分。ただし「オイル軸は n=2 語のみ・今後の追加なし」という偏った軸を公開物として維持する理由の文書化が必要。
3. **語彙統一はせず、現状を methodology に明記する**。プラットフォーム間で製品語が異なることを制限事項として記録し、比較時は語彙差を明示する。

## 完了条件

- [x] 方針の決定（owner）: 選択肢 1（リキッド 13 語を収集し、オイル 2 run を公開集計から外す、2026-10-24）
- [ ] 実施（YouTube のリキッド 13 run 収集 + `youtube-export` 再生成 + オイル 2 run の除外）
- [ ] README のキーワード表で製品語がプラットフォーム間で説明可能な状態になっている

## 実行準備（2026-10-24）

選択肢 1 を実行可能な状態まで確定させた記録。**実収集は `APIFY_TOKEN` 未設定のため未実施**。コード・raw・`docs/audits/` には触れていない。`staging-declaration-v1` の表現可否・`date_filter` の注意点・`youtube_export` が `*.json` しか読まない点（CSV で stage すると 0 件）・`max_videos` の根拠の考え方・run-id 規約・収集後の手順の枠組みは `20261023_p2_youtube-compound-words-incomplete.md`「実行準備（2026-10-24）」節（#6）に確定済みであり、ここでは繰り返さない。以下は #7 固有の差分である。

### ブロッカー

- `APIFY_TOKEN` が未設定（空変数であることを確認。値は読んでいない。`.env.d/` には `apify.env.example` のみ）。ゆえに Apify の実実行はできない。
- YouTube raw は Git 管理外で本 worktree に存在しない。既存 7 run の生ペイロードは見られない（以下は追跡層 2 表と specs・コードの読解による確定）。
- owner に必要な操作: Apify トークンを発行し、安全な場所に配置する（値はコミットしないことだけ守り、値の指定は owner に委ねる。配置場所と権限は各 SKILL の手順に従う）。

### 1. 13 語の実行仕様

- `search_term` は `metadata/queries/query-registry.json` の `*-liquid-ja`（CBX を除く 13 件）の `canonical_text` を実測して確定。13 件すべて `status: active`。
- `max_videos` は owner 決定（「CBD/THC 100・他 50」）を化合物語幹に適用する。`CBD リキッド` / `THC リキッド` は 100、他の 11 語は 50。根拠は methodology §2.3 の表が正本であり、既存 7 run（CBD/THC 100・他 50）と同じ基準を語幹で引き継ぐため。13 語は別時点の別観測になる（AGENTS.md: 同一クエリの再実行は非決定的になりうる）。
- run-id は YouTube 層の既存規約（日本語スラグ、例 `20261002T064905Z-youtube-cbd-オイル`）に寄せる: `<UTC>-youtube-<lower>-リキッド`。理由: (1) `PUBLISHABLE_RUNS` の値（日本語 `search_term`）との対応が一目瞭然、(2) `research-youtube-search` SKILL の生成式（`tr ' ' '-'` + 小文字化）に `CBD リキッド` を通すと `cbd-リキッド` になり一致する（SKILL 内の `cbd-liquid` は例示に過ぎない）、(3) GT 層の `rikiddo` ローマ字は GT run-id 規約（source + phase 情報を含む別層）のもので YouTube 層には適用されない、(4) 日本語 run-id の path 安全性は既存 7 run で実証済み。`THC-O` は registry の `thc-o` と整合させ `thc-o-リキッド` とする。日時部は実行時の UTC に置換する。

| 語 | `search_term`（`canonical_text`） | `query_id` | `max_videos` | run-id 案（日時部は実行時 UTC） |
|---|---|---|---|---|
| CBD リキッド | `CBD リキッド` | `cbd-liquid-ja` | 100 | `<UTC>-youtube-cbd-リキッド` |
| THC リキッド | `THC リキッド` | `thc-liquid-ja` | 100 | `<UTC>-youtube-thc-リキッド` |
| CBG リキッド | `CBG リキッド` | `cbg-liquid-ja` | 50 | `<UTC>-youtube-cbg-リキッド` |
| CBN リキッド | `CBN リキッド` | `cbn-liquid-ja` | 50 | `<UTC>-youtube-cbn-リキッド` |
| HHC リキッド | `HHC リキッド` | `hhc-liquid-ja` | 50 | `<UTC>-youtube-hhc-リキッド` |
| THCV リキッド | `THCV リキッド` | `thcv-liquid-ja` | 50 | `<UTC>-youtube-thcv-リキッド` |
| THC-O リキッド | `THC-O リキッド` | `thc-o-liquid-ja` | 50 | `<UTC>-youtube-thc-o-リキッド` |
| THCH リキッド | `THCH リキッド` | `thch-liquid-ja` | 50 | `<UTC>-youtube-thch-リキッド` |
| CRDH リキッド | `CRDH リキッド` | `crdh-liquid-ja` | 50 | `<UTC>-youtube-crdh-リキッド` |
| CRDP リキッド | `CRDP リキッド` | `crdp-liquid-ja` | 50 | `<UTC>-youtube-crdp-リキッド` |
| H4CBH リキッド | `H4CBH リキッド` | `h4cbh-liquid-ja` | 50 | `<UTC>-youtube-h4cbh-リキッド` |
| HHBD リキッド | `HHBD リキッド` | `hhbd-liquid-ja` | 50 | `<UTC>-youtube-hhbd-リキッド` |
| HHCH リキッド | `HHCH リキッド` | `hhch-liquid-ja` | 50 | `<UTC>-youtube-hhch-リキッド` |

- 13 run は 1 バッチ・逐次実行（1 実行 1 キーワード。SKILL 推奨の `wait` 45 秒 + 1 秒間隔）。分割の必要はない。429・失敗時は待機して再試行し、リトライ番号を宣言に記録する。失敗は `collection_failed` として残し、`observed_zero` に読み替えない（#6 と同一方針）。

### 2. オイル 2 run の除外: 適用可能な最小差分（未適用）

`src/processing/youtube_export.py` を読解して確定。`_status()` / `build_video_export()` 自体の変更は不要（allowlist 駆動のため）。必要なのは `PUBLISHABLE_RUNS` から 2 行削除し、`EXCLUSION_REASONS` に 2 行追加することだけである。**適用してはいけない**（置換となる 13 リキッド run が存在しないため。先に外すと公開表が 7 run → 5 run / 182 行 → 132 行に縮み、置換なしに証拠が減る）。

```python
# 削除（PUBLISHABLE_RUNS から）:
#   "20261002T064905Z-youtube-cbd-オイル": "CBD オイル",
#   "20261002T064911Z-youtube-thc-オイル": "THC オイル",
# 追加（EXCLUSION_REASONS に）:
#   "20261002T064905Z-youtube-cbd-オイル": "superseded by liquid vocabulary, excluded from evidence (ISS-20261023-YT-011 / GitHub #7)",
#   "20261002T064911Z-youtube-thc-オイル": "superseded by liquid vocabulary, excluded from evidence (ISS-20261023-YT-011 / GitHub #7)",
```

適用後の変化（追跡層 2 表を実測して算出。`youtube_runs.csv` 7 行 = CBD 22 / THC 25 / CBG 34 / HHC 28 / THCV 23 / CBD オイル 23 / THC オイル 27、合計 182 行）:

| 成果物 | 現行 | 除外適用後 |
|---|---:|---:|
| `youtube_runs.csv` | 7 行 | **5 行**（オイル 2 行が消える） |
| `youtube_videos.csv` | 182 行 | **132 行**（オイル 50 行 = 23+27 が消える） |
| `withheld`（summary のみ、データに書かれない） | 6 run（`EXCLUSION_REASONS` 6 件） | 8 run |

テストへの影響: `tests/processing/test_youtube_export.py` は tmp fixture のみで構成され、オイル run-id・7 run・182 行の固定期待値を**持たない**（唯一の件数 assertion は `runs[0]["video_rows"] == "1"`）。ゆえにこの除外差分だけでは既存テストは壊れない。他に `182` / オイル run-id を参照するのは `youtube_export.py` のコメントと `src/processing/reproduce.py` の `NonReproducible` notes（`22+25+34+28+23+23+27 = 182 rows` / `the 7 reviewed 2026-10-02 runs`）のみで、テストではない。ただし除外適用時は `reproduce.py` の文言更新が同時に必須になる（最小差分の 4 行だけでは不完全）。#6 の前例どおり、`PUBLISHABLE_RUNS` 変更時はテスト更新を同梱する運用とする。

除外と同時に必要な作業（適用順序つき）:

1. 13 リキッド run の採用（§4 の手順）。
2. 上記 4 行のコード変更 + `reproduce.py` notes の更新 + テスト更新。
3. `python -m processing.cli youtube-export` で 2 表を再生成（Makefile に target は無い）。
4. `make audit-publication` の再実行と件数の突合せ（processed ⇄ raw）。
5. README のキーワード表・methodology §2.3（YouTube 表にリキッド 13 語を追加し、オイル 2 語を除外済みとして記載）・`collection-summary.md` §3（7 run / 182 行の更新）の更新。
6. 監査スナップショットの再生成（`make audit-new-runs` / `make audit-snapshots` 等）。

### 3. リキッド run の公開可否と GT no-data 5 語の扱い

- 新規 run は `PUBLISHABLE_RUNS` に載るまで `_status()` が `"provenance not reviewed for publication"` を返し、2 表のどちらにも書かれない（#6 と同じ規則。`test_unreviewed_and_withdrawn_runs_are_withheld_with_a_reason` が固定）。13 run を採用する際の追加差分の形（run-id は収集時に確定するため現時点ではキー未定のプレースホルダ。値は `canonical_text`）:

```python
# PUBLISHABLE_RUNS に追加（13 行。provenance レビュー後）:
#   "<UTC>-youtube-cbd-リキッド": "CBD リキッド",
#   "<UTC>-youtube-thc-リキッド": "THC リキッド",
#   ...（§1 の表の 13 語ぶん。値は search_term と同一）
```

- 12ヶ月 GT で no data の 5 語（`HHC / CRDH / CRDP / THC-O / THCV リキッド`。`records_*.json` の `data` 長 0 を実測。残り 8 語は系列あり）は、YouTube 側の収集対象から外さない。GT の有無から YouTube の有無は推定できない（別現象: 検索需要 vs 動画存在。AGENTS.md: プラットフォーム間で指標を同等とみなさない）。YouTube で 0 件なら `observed_zero`（`record_count: 0` の artifact が L1-09 で必須）、失敗なら `collection_failed` であり、GT の no-data はどちらの根拠にもならない。

### 4. 収集後に必要な手順（担当つき。#6 と同一枠組み）

1. owner: トークン配置（値はコミットしない）。
2. 実行者（owner 承認済み）: 13 語 × 1 run を同一 actor（`gJvjeCYNraSfhIaNd`）で外部実行（1 実行 1 キーワード。入力は `search_term` + `max_videos` のみ）。`run-status`（status / startedAt / finishedAt）と dataset ID を控える。dataset は JSON で保存し、`videoId` で重複排除して `records_raw.json`（排除前）と `records.json`（排除後）を作る。**CSV で取らない**（`youtube_export` は `*.json` しか読まない）。
3. 実行者: `staging-declaration-v1` を 1 語 1 文書で作成（#6 §1 のチェックリスト通り。`date_filter` は danek actor に概念が無い旨を `limitations` に明示し、手書き宣言とする）→ `make stage DECLARATION=<file>` → `make adopt-all`。quarantine に落ちたら理由を確認し、宣言を修正する（payload は byte 不変）。
4. owner: provenance レビュー後、`PUBLISHABLE_RUNS` への 13 run 追加を承認する。
5. 実装者（コード変更・別作業）: §3 の差分で `PUBLISHABLE_RUNS` に 13 run を追加し、テスト更新つき → `youtube-export` で 2 表を再生成。
6. 実装者: §2 の差分でオイル 2 run を除外（**§5 の前には適用しない**）+ `reproduce.py` notes 更新 + テスト更新 → 2 表を再生成。
7. 文書担当 / owner: README のキーワード表と methodology §2.3・`collection-summary.md` §3・§4 を更新する。
8. 実行者: 監査スナップショットを再生成する（`make audit-new-runs` / `make audit-snapshots` 等）。本件では `docs/audits/` に触れていない。

適用順序の原則: **リキッド 13 run 採用 → オイル 2 run 除外 → gate 再実行**。除外が先行してはならない。

### #6 の確定内容との関係

- 矛盾はない。経路（外部実行 → 手書き宣言 → `make stage` / `make adopt-all`）、JSON 取得の要請、`max_videos` の正本（methodology §2.3）、run-id 規約の式、担当分担は #6 の確定内容をそのまま使う。
- 追加で分かった落とし穴: (1) SKILL 内に run-id slug の表記が 3 通り併存する（日本語スラグの既存 run / `rikiddo` ローマ字の GT run / SKILL 例示の `cbd-liquid`）。本件は YouTube 層の既存規約（日本語）に寄せると決めて解消した。(2) #7 記録の既存「除外パッチ案」（2 行削除・2 行追加）だけでは適用が不完全で、`reproduce.py` の `182 rows` / `7 reviewed runs` 文言の更新が同時に要る。(3) 除外差分だけでは既存テストは壊れない（固定期待値なし）。「影響を受けるテスト」は「なし」が実測結果であり、テスト更新は #6 前例の運用として同梱するものである。
