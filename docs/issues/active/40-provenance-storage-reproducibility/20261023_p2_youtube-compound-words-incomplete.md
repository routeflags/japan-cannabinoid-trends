# Issue: YouTube の化合物語が 5/13 語しか無い

**ID:** ISS-20261023-YT-010  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`youtube_videos.csv`, `methodology.md` §2.3  
**GitHub:** [#6](https://github.com/routeflags/japan-cannabinoid-trends/issues/6)

## 決定（owner, 2026-10-24）

**選択肢 1（8 語を追加収集）**を採用する。収集は外部 Apify 実行 → `staging-declaration-v1` → `make stage` / `make adopt-all` の経路で、
`PUBLISHABLE_RUNS` への追加は provenance レビュー後。actor と `max_videos` は既存 7 run に合わせる。

## 制約

YouTube raw ペイロードは gitignored（`.gitignore` の `**/data/raw/*`、例外は `google_trends` のみ）かつローカル限定であり、
本 worktree の `datasets/cannabinoid-raw-collection/data/raw/` には `youtube/` が存在しない。
以下は追跡対象の集計 2 表とコミット済み specs からの検証であり、raw 自体の確認は含まない。

## 検証済み事実

- `youtube_runs.csv`（8 行 = ヘッダ + 7 run、化合物語 5 + 製品語 2）:
  CBD 22 / THC 25 / CBG 34 / HHC 28 / THCV 23 / CBD オイル 23 / THC オイル 27。合計 182。
- `youtube_videos.csv` は 183 行（ヘッダ + **182 動画行**）で、run 別内訳は `youtube_runs.csv` の `video_rows` と一致する。
  確認コマンド: `PYTHONPATH=src python3 -c "import csv,collections; ..."`（`collections.Counter` で run 別集計）。
- 両表の生成器は `python -m processing.cli youtube-export`
  （`src/processing/youtube_export.py` の `build_video_export` + `write_export`。
  デフォルト `--study-dir datasets/cannabinoid-raw-collection` / `--output-dir .../data/processed`）。
  導出不能宣言は `src/processing/reproduce.py` の `NonReproducible`（raw がリポジトリ外のため clone では再導出不可。
  README も「生成は raw を要求するので、clone では再導出できない」と記載）。
- **未収集（8 語）**: THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH。
  README §対象化合物の YouTube 列はこの 8 語を「raw のみ」と記すが、raw がローカル限定のため本 worktree では検証不能。
  追跡層（2 表）に 8 語の行は存在しない。
- `EXCLUSION_REASONS` は新規 run に影響しない。新規 run id は `PUBLISHABLE_RUNS` にも
  `EXCLUSION_REASONS` にも載らないため `_status()` は `"provenance not reviewed for publication"` を返し、
  `build_video_export` はその run を **withhold（2 表のどちらにも書かない）** する
 （`tests/processing/test_youtube_export.py::test_unreviewed_and_withheld_with_a_reason` がこの規則を固定）。
  新規 8 語を追跡層に載せるには `PUBLISHABLE_RUNS` への追加（コード変更 + テスト更新 + provenance レビュー）が必須。
  `EXCLUSION_REASONS` の 6 件（10-year 不完全系列 5 件 + methodology test 1 件）は既存の除外理由であり、新規収集とは無関係。

## 収集条件（既存と同じ）

Actor `gJvjeCYNraSfhIaNd`（`danek/youtube-search`）、1 run = 1 `search_term`、`max_videos` 50〜100。
入力スキーマは当該 2 フィールドのみ（`.github/skills/apify-youtube-search/SKILL.md`）:

> `"required": ["search_term", "max_videos"]`（Input Schema、Build `lcBfQ1sbz5bx58c1X` 時点）
> `| max_videos | ✅ | \`10\` (default 10, 1-100) | 取得上限。100超は要相談 (support@) |`

`max_videos` は**件数**（ページ数ではない）。

既存 run の `max_videos` は methodology §2.3 の表が正本（CBD / THC 100、他 50）。比較可能性のため方針は既存に合わせる。

## 収集経路: パイプラインではなく外部収集 + `make stage`

新規 8 語は `collect --live` では収集できない。外部 collector（netloom 経由の Apify 実行）で取得し、
`staging-declaration-v1` 文書 → `make stage` → `make adopt-all`（L1 ゲート判定）で採用する経路になる。根拠:

- `src/collection/adapters/__init__.py`: `_FACTORIES` と `_LIVE_SESSIONS` は `google-trends` のみ。
  `get_adapter_factory('youtube')` / `get_live_session('youtube')` はいずれも `AdapterUnavailable` を送出する（本 worktree で実測）。
- `src/collection/adapters/youtube/apify_csv.py`: YouTube adapter は handover 専用。
  `collect` は常に `LIVE_TRANSPORT_UNIMPLEMENTED` で fail-closed（`returned_count=0` を発明しない）。
  `stage_csv` / `build_csv_run` は既存の宣言ドライバ（`stage_declaration` → `adopt_staged`）への薄いラッパであり、
  新規 catalog / 採用 / 件数規則を追加しない。
- actor の不一致に注意: パイプライン側 handover（`build_csv_run` の `COLLECTOR_ID`）は
  `youtube-apify-scraper`（`h7sDV53CddomktSi5`、streamers/youtube-scraper）に固定されているが、
  既存 7 run の収集 actor は `youtube-apify-search`（`gJvjeCYNraSfhIaNd`、danek/youtube-search）である。
  `youtube-apify-search` 用の handover builder は存在しない（registry エントリ + SKILL のみ）。
  既存と同じ actor で 8 語を取る場合、宣言文書は手書き（スキーマ `staging-declaration-v1`、AGENTS.md: `unknown` 不可・
  未確認値は採用ブロック）となり、`date_filter` 等の request 事実は宣言者が明示する。
  パイプラインの request/response 語彙（`dateFilter` 等）は scraper 側のものであり、danek actor の入力語彙は
  `search_term` + `max_videos` のみ。混同しないこと。

## 選択肢と帰結

### 1. 8 語を追加収集する（新規収集のため owner 承認が必要: 実費 + 新スナップショットの採用判断）

手順: ① 同一 actor（`gJvjeCYNraSfhIaNd`）で 8 語 × 1 run を外部実行（`max_videos` は既存方針に合わせる）
→ ② 1 語 1 文書の `staging-declaration-v1` で `make stage` / `make adopt-all`（request と観測範囲を分離記録）
→ ③ `PUBLISHABLE_RUNS` に 8 run を追加（provenance レビュー後、テスト更新つき）
→ ④ `youtube-export` で 2 表を再生成。
帰結: `youtube_runs.csv` は 15 行、`youtube_videos.csv` は 182+N 行になる。
新規 run は 2026-10-02 スナップショットと別時点の観測であり、run 間で窓が違えば別観測として扱う
（AGENTS.md: 同一クエリの再実行は非決定的になりうる）。README のキーワード表と methodology §2.3 は別途更新が必要
（本 issue 記録者の編集権限外のため、文案は下記「文書更新の文案」を owner / 編集者に渡す）。

### 2. YouTube は 5 語を意図的な範囲として methodology に明記する（収集なし）

手順: methodology §2.3 に範囲限定の旨と理由を追記し、README の YouTube 列の「raw のみ」表示と整合させる
（raw が実在するなら local 証跡として残し、追跡層には載せない。raw が無い語は「未収集」と読み替える）。
帰結: コード変更なし。ただし Google Trends 13 語 / X 7 語との被覆差は恒久的な制約として残り、
化合物間比較での YouTube エビデンスは 5 語に限定される。

## 文書更新の文案（README / methodology は編集権限外のため提案のみ）

- 選択肢 1 が実施された場合、README「収集したキーワード」YouTube 行を
  `| YouTube | 2026-10-02（公開集計に入る 7 run）+ 2026-10-2x（8 run 追加） | 13 語すべて | オイル 2 語 | ... |`
  の形に更新し、methodology §2.3 の表に 8 語（`max_videos` 実績値つき）を追加する。
- 選択肢 2 の場合、methodology §2.3 に `YouTube の収集範囲は化合物語 5 語 + オイル 2 語に限定する（ISS-20261023-YT-010、owner 判断 YYYY-MM-DD）。
  残り 8 語の YouTube エビデンスは存在しない。` を追記し、README の「raw のみ」8 語の扱い（local 証跡の有無）を確定させる。

## 完了条件

- [x] 方針の決定（owner: 選択肢 1、2026-10-24。`max_videos` は既存に合わせる）
- [ ] 実施: 8 run の外部収集 + stage/adopt（L1 通過）+ `PUBLISHABLE_RUNS` 追加 + `youtube-export` 再生成
- [ ] README のキーワード表・methodology §2.3・`youtube_runs.csv` の三者が一致している

## 実行準備（2026-10-24）

選択肢 1 を実行可能な状態まで確定させた記録。**実収集は `APIFY_TOKEN` 未設定のため未実施**。raw・コード・監査スナップショットには触れていない。

### ブロッカー

- `APIFY_TOKEN` が未設定（`netloom env check --source apify` で unset を確認。`.env` なし、`.env.d/` には `apify.env.example` のみ）。ゆえに Apify の実実行はできない。
- YouTube raw は Git 管理外で本 worktree に存在しない。既存 7 run の生ペイロードは見られない（以下は追跡層と specs・コードの読解による確定）。
- owner に必要な操作: Apify トークンを発行し、安全な場所に配置する（値はコミットしないことだけ守り、値の指定は owner に委ねる。配置場所と権限は各 SKILL の手順に従う）。

### 1. `staging-declaration-v1` の表現可否の結論

今回の payload（danek/youtube-search の dataset export。入力は `search_term` + `max_videos` のみ）は宣言文書で表現できる。ただし次の2点は注意が必要で、1点は表現できない。

| 宣言項目 | 可否 | 内容 |
|---|---|---|
| `run_id` | ○ | 宣言者が付与。形式は `research-youtube-search` SKILL 規定の `{TIMESTAMP}-youtube-{keyword-slug}`（小文字・空白→ハイフン。既存 7 run と同形）。衝突時は stage が `RUN_ID_ALREADY_EXISTS` で停止する。 |
| `study_id` / `source_id` / `collector_id` | ○ | `cannabinoid-raw-collection` / `youtube` / `youtube-apify-search`（registry 登録済み、`external_id: gJvjeCYNraSfhIaNd` を実測）。version は registry の `unknown` のまま（stager は collector を昇格できない）。status `unverified` は L1 で可視化されるのみで採用を止めない（rehearsal で観測済み）。 |
| `query.keyword` / `query_id` | ○ | 8 語すべて registry に active 登録あり（§3 の表。`canonical_text` を実測）。keyword → `query_id` は宣言者が明示し、driver は payload から推定しない。 |
| `purpose` | ○ | 宣言者が記載（例: 本 issue 選択肢 1 の採用）。 |
| `collection_request`（`search_term` / `max_videos`） | ○ | `submitted_parameters` は `allow_unknown` のため、actor の入力 2 項目をそのまま記録できる。L1 は値を検証しないが provenance として残る。 |
| `collection_request.date_filter` | △ 要注意 | スキーマ上 required だが、danek actor に dateFilter 概念は存在しない。何を書いても request 事実の再現にはならないため、宣言値の意味と「日付絞りなし」である旨を `temporal.limitations` に明示する。`build_csv_run` 経由では scraper 側の `DATE_FILTERS` 語彙に縛られるため使わず、手書き宣言とする。 |
| `reference_time` | ○ | Apify run の実行時刻（console Runs list / `run-status` の startedAt/finishedAt）。根拠を `timestamps.basis` に記録する。 |
| `window`（絶対窓） | △ 導出根拠の明記が必須 | danek の `timestamp` は相対表記（"3 days ago" 等）で絶対日付を返さない（SKILL 制約）。window は payload の相対 timestamp または実行時刻基準で宣言し、collector が強制した境界でない旨を `boundary_semantics` / `limitations` に書く（COL-033 前例の文言を再利用）。payload から独立検証はできない（pipeline spec §3.4 の制限）。 |
| `temporal.collector_window_type` | ○ | 日付絞りなしのため `unbounded` が相当。`exact_window_match: false`。未確証の値は書かない。 |
| `timestamps` + `basis` | ○ | `run-status` の startedAt/finishedAt + basis（例: console 表示の JST→UTC 換算）。payload 自体に収集時刻列はない。取れなければ stage 不可（捏造しない）。 |
| `execution.status` / `returned_count` | ○ | run の SUCCEEDED → `success` 等。`returned_count` 省略時は artifacts 合計から導出される。`success` + 0 件は `record_count: 0` の artifact が必須（L1-09）。`pagination_exhausted` は nullable のため不明なら省略する（推測しない）。 |
| `artifacts`（JSON 推奨） | ○ | danek dataset の JSON export を `records.json`（配列）として stage。schema `youtube-search-result-list-v1` + `json-record-reader` で件数導出可。CSV の場合は `youtube-dataset-csv-v1` + `csv-record-reader`（列名不問。header の整形式のみ検査）。`record_count` は宣言または導出（S8 が照合）。**JSON で取得すること**（§2 の理由）。 |
| dedup 情報 | ✗ 欄なし | スキーマに重複排除の欄はない。重複排除は下流の `youtube_export` が `videoId` で行う。宣言時は `records_raw.json`（排除前）と `records.json`（排除後）の両者を残すか、排除前件数を `environment` に記録する運用を宣言に書く（`research-youtube-search` SKILL が 2 ファイル保存を規定）。 |
| actor run/dataset ID・build | △ `environment` のみ | `environment` は free-form のため `actor_run_id` / `apify_dataset_id` / `actor_build` 等は記録可能（20261015 宣言の前例）。未確認値は書かない（`unknown` 捏造禁止）。 |

L1 通過のために宣言文書に書くこと（チェックリスト）: ① `query_id` は 8 語とも登録済み（実測済み。未登録は exit 2）② `collector_id: youtube-apify-search` は登録済み（実測済み）③ artifact schema は登録済み reader のもの（JSON/CSV とも登録済みを実測。未登録は S9 で隔離）④ 時刻の ISO 形式と前後関係、run_id の path 安全・衝突なし ⑤ status と artifact の整合（L1-09: `success` に artifact 必須、0 件 `success` は `record_count: 0` の artifact）⑥ secrets 混入なし（L1-10）。

埋められない必須フィールドはないが、真の値が存在しない必須項目（`date_filter`）と payload だけでは定まらない項目（`window` の絶対値・`started_at/finished_at`）は、宣言者の実行記録と `limitations` / `basis` の明示が L1 通過の条件になる。確認できない項目は「確認できず」と書く。

### 2. handover 経路の不一致と対応

- `build_csv_run` / `stage_csv`（`src/collection/adapters/youtube/apify_csv.py`）は `COLLECTOR_ID: youtube-apify-scraper`（`h7sDV53CddomktSi5`、streamers/youtube-scraper）に固定され、request 語彙も scraper 側の `DATE_FILTERS` である。**danek 用の handover builder は存在しない**（registry エントリ + SKILL のみ）。8 語は手書き宣言 → `make stage` → `make adopt-all` の経路を取る。
- 列対応表（件数照合には影響しないが、意味の混同防止のため記録する）:

| 項目 | danek/youtube-search（今回使う側） | streamers/youtube-scraper（builder 側） |
|---|---|---|
| actor | `gJvjeCYNraSfhIaNd` / `danek/youtube-search` | `h7sDV53CddomktSi5` / `streamers/youtube-scraper` |
| 入力 | `search_term` + `max_videos` のみ（日付概念なし） | `searchQueries` + `maxResults` + `dateFilter` 等 |
| 動画 ID | `id.videoId` | `id` |
| タイトル | `snippet.title` | `title` |
| チャンネル | `snippet.channelTitle` / `snippet.channelHandle` | `channelName` |
| 公開日 | `snippet.timestamp`（相対表記のみ） | `date`（ISO8601 絶対） |
| その他 | `snippet.views` / `duration` / `badges` / `chapters` / `thumbnails` | `viewCount` / `duration` / `likes` / `commentsCount` / `url`（+ `input` 列に検索語） |

- `csv-record-reader` は列名を問わない（header の整形式のみ検査）ため、どちらの形式でも S8 の件数照合は通る。しかし `youtube_export`（`src/processing/youtube_export.py`）は `data/raw/youtube/<run-id>/` の `*.json` のみを読むため、**CSV で stage した run は `video_rows: 0` になる**。8 語は danek の JSON dataset export で取得・保存し、`_item_to_row` が読める形状（`videoId` / `title` / `channel` / `snippet`）に合わせる。CSV で取る場合は export の対応が別途必要になり、本件では選ばない。
- なお `youtube_export` は公開日を追跡列に含まない（`VIDEO_COLUMNS` は run_id / video_id / channel_title / title のみ）。danek の相対 timestamp でも export は成立する。window の絶対値は宣言者が別途定める（§1 の表どおり）。

### 3. 8 run の実行仕様

- `search_term` は `metadata/queries/query-registry.json` の `canonical_text` を実測して確定（`PYTHONPATH=src python3` で読取）。
- `max_videos` は既存方針 CBD/THC=100・他=50。根拠は methodology §2.3 の表が正本であり、`youtube_runs.csv` の `video_rows`（CBD 22 / THC 25 / CBG 34 / HHC 28 / THCV 23。合計 182 を実測）が実績として整合する。8 語はすべて「他」に属するため 50。
- run-id 案: `research-youtube-search` SKILL 規定の `{TIMESTAMP}-youtube-{keyword-slug}`（小文字・空白→ハイフン）。日時部は実行時の UTC に置換する。

| 語 | `search_term` | `query_id` | `max_videos` | run-id 案（日時部は実行時 UTC） |
|---|---|---|---|---|
| THC-O | `THC-O` | `thc-o-general-ja` | 50 | `<UTC>Z-youtube-thc-o` |
| THCH | `THCH` | `thch-general-ja` | 50 | `<UTC>Z-youtube-thch` |
| CBN | `CBN` | `cbn-general-ja` | 50 | `<UTC>Z-youtube-cbn` |
| CRDH | `CRDH` | `crdh-general-ja` | 50 | `<UTC>Z-youtube-crdh` |
| CRDP | `CRDP` | `crdp-general-ja` | 50 | `<UTC>Z-youtube-crdp` |
| H4CBH | `H4CBH` | `h4cbh-general-ja` | 50 | `<UTC>Z-youtube-h4cbh` |
| HHBD | `HHBD` | `hhbd-general-ja` | 50 | `<UTC>Z-youtube-hhbd` |
| HHCH | `HHCH` | `hhch-general-ja` | 50 | `<UTC>Z-youtube-hhch` |

- 既存 7 run（2026-10-02）とは別時点の観測になる。run 間で窓が違えば別観測として扱う（AGENTS.md: 同一クエリの再実行は非決定的になりうる）。

### 4. 収集後に必要な手順（担当つき）

1. owner: トークン配置（値はコミットしない）。
2. 実行者（owner 承認済み）: 8 語 × 1 run を同一 actor で外部実行（1 実行 1 キーワード。入力は `search_term` + `max_videos` のみ）。`run-status`（status / startedAt / finishedAt）と dataset ID を控える。dataset は JSON で保存し、`videoId` で重複排除して `records_raw.json`（排除前）と `records.json`（排除後）を作る（`research-youtube-search` SKILL の手順）。
3. 実行者: `staging-declaration-v1` を 1 語 1 文書で作成（§1 のチェックリスト通り）→ `make stage DECLARATION=<file>`（`.venv` が無い場合は `PYTHONPATH=src python3 -m collection.core.cli stage --declaration <file> --workspace . --datasets-root datasets --config-dir config --metadata-dir metadata`）→ `make adopt-all`。quarantine に落ちたら理由を確認し、宣言を修正する（payload は byte 不変）。
4. owner: provenance レビュー後、`PUBLISHABLE_RUNS` 追加を承認する。
5. 実装者（コード変更・別作業）: `src/processing/youtube_export.py` の `PUBLISHABLE_RUNS` に 8 run を追加し、テスト（`tests/processing/test_youtube_export.py`）を更新する → `python -m processing.cli youtube-export` で 2 表を再生成する（Makefile に target は無い）。
6. 文書担当 / owner: README のキーワード表と methodology §2.3 を更新する（文案は「文書更新の文案」節）。
7. 実行者: 監査スナップショットを再生成する（`make audit-new-runs` / `make audit-snapshots` 等。新規 run の追加後は再生成が production 契約の手順）。本件では `docs/audits/` に触れていない。
