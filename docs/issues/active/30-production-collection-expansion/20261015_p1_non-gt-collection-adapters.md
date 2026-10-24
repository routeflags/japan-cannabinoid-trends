# Issue: Google Trends 以外のソースに collection adapter が無い

**ID:** ISS-20261015-COL-016  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `src/collection/adapters/__init__.py`（`_FACTORIES`）, `src/collection/{x,tiktok,instagram}/`, `src/collection/apify_run.sh`, `docs/specs/validation-framework.md` §22.4

## 概要

framework が自前で収集できるソースは Google Trends（`google-trends-mcp`）のみ。
X / YouTube / TikTok / Instagram は adapter 未実装で、収集は既存 shell（framework 外）のまま。
§22.2 のゲートは「迂回を検知して止める」側であり、「迂回せずに収集できるようにする」側が無い。

## 確認された観測

- `src/collection/adapters/__init__.py` の `_FACTORIES` は `google-trends` の 1 件。
- `config/collectors.json` の非 GT collector は `status: unverified`、capability は全項目
  `unknown`。
- `src/collection/apify_run.sh` は（ガード追加後）`datasets/` 直書きを拒否するが、これは
  「止める」側の実装で、代替の収集経路にはなっていない。

## 影響

- 非 GT ソースの新規収集を現行契約の経路で行えない。
- shell → staged → `adopt` の移行は adapter を前提とするため、未実装の間は移行できない。
- X / YouTube の旧 run の実行条件が `unknown` のまま固定される。

## 対応方針

- **owner 決定（2026-10-15）:** 着手順は (1) 採用済み YouTube Apify CSV pattern の
  declaration-driven adapter / driver wrapper、(2) X の mock / dry-run + request-only evidence、
  (3) X live request は live request 制御（`ISS-20261015-COL-032`）と証跡が通った後の別途明示承認、とする。
- adapter は共通 Contract（`collection.core.contracts`）を実装し、契約テストを追加する
  （架空ソーステストと同じ型で検証する）。
- capability は実測後に registry を更新する（推測で `supported` にしない）。

## 実装記録（2026-10-15: YouTube Apify CSV MVP）

owner 承認 item 2。COL-033 の採用済み YouTube Apify CSV パターンを
offline の declaration-driven adapter/driver として `src/collection/adapters/youtube/apify_csv.py`
（+ `tests/collection/test_youtube_apify_csv_adapter.py` 21 tests）に実装した。

- 範囲: staged CSV handover のみ。live Apify API 呼び出し・token 保管・既存 raw 変更・
  publication・per-post 行公開は対象外。既存 `stage_declaration` / `adopt_staged` を再利用し、
  catalog/adoption/count/quarantine ルールの重複実装は無い。
- `build_csv_run` / `stage_csv`: query/filter は宣言必須で payload 推測しない、
  CSV は byte-for-byte、count は `csv-record-reader`（quoted newline 対応）に一任、
  宣言 count は L1（`ARTIFACT_RECORD_COUNT_MISMATCH`）に pass-through、
  `dateFilter` と観測窓は分離記録、既存 run_id は `RUN_ID_ALREADY_EXISTS` で上書き禁止、
  欠損/失敗は `returned_count=0` に変換しない。
- `YouTubeApifyCsvAdapter` は共通 Contract 形状を満たすが handover 専用:
  `collect` は live 未実装で fail closed（`LIVE_TRANSPORT_UNIMPLEMENTED`）、
  `extract_observations` は行抽出しない。`youtube` は `_FACTORIES` /
  `_WINDOW_COMPILERS` に未登録（収集可能に見せないため意図的）。
- registry は不変: `youtube-apify-scraper` は `status: unverified` /
  capability 全 `unknown` のまま。`config/collectors.json` の変更は無い。
- 残件（本 issue は OPEN のまま）: live Apify transport（token/pagination/件数上限の設計が別途必要）、
  `dateFilter` window compiler（WIN-002 は未着手）、X / TikTok / Instagram 用 adapter は未実装。
  上の完了条件のうち満たしたのは YouTube CSV handover の adapter 実装 + 契約テストのみであり、
  「対象ソースと着手順の決定」「capability の実測と registry 更新」は未了。

## 完了条件

- [x] 対象ソースと着手順の決定（2026-10-15 owner `go 1,2`: YouTube Apify CSV pattern を先行）
- [ ] adapter 実装 + 契約テスト
- [ ] capability の実測と registry 更新（未確認は `unknown` のまま）

## 実装記録（2026-10-15: X dry-run / request-planning slice）

owner 着手順 item 2 の安全側 slice。live request・認証情報・response body・
per-post レコードは一切扱わない（COL-030 §4.1/§4.2 遵守）。
`src/collection/adapters/x/`（+ `tests/collection/test_x_dry_run.py` 30 tests）:

- `request.py`: X API v2 search の request planner（純粋関数）。宣言済み
  query text＋絶対 UTC bounds を request parameters（endpoint/method/params）
  にするだけで、送信しない。endpoint/method は COL-030 §3.2 の repo 内仕様。
  naive・非 UTC・前後逆転は拒否（変換しない）。`max_results` は正整数の
  pass-through のみ（page-size bounds は未検証。sampling 方針は COL-032）。
  `tweet.fields` は意図的に無し（response field を request-only evidence に
  入れないため。field 選定は COL-031 の product 決定）。
- `dry_run.py`: 共通 Contract 形状の dry-run adapter。`collect` は live 未実装で
  fail closed（`LIVE_TRANSPORT_UNIMPLEMENTED`、YouTube と同一コード＝同一規則）、
  `extract_observations` は行抽出しない。identity は placeholder
 （`x-api-v2@1` / `unregistered`）であり registry 証拠ではない。
  COL-031 の登録時に registry 値と一致させること。
- `x` は `_FACTORIES` に未登録（収集可能に見せないため意図的。YouTube と同じ
  方針）。capability は全 `unknown` のまま。`config/collectors.json` の変更は無い。
- 残件（本 issue は OPEN のまま）: live transport（COL-031。COL-032 の live request 制御と
  PRV-033 の request-only evidence＋別途明示承認が先行条件）、TikTok / Instagram 用
  adapter、capability の実測と registry 更新。

## 実装記録（2026-10-15: YouTube Apify request-planning slice）

owner 指示により X / TikTok / Instagram adapter 作業は on hold。本 slice は
YouTube のみ。live 呼び出し・token 保管・response body・per-video 行は一切扱わ
ない（COL-030 §4.1 遵守）。PRV-013 の別 subagent とは重複しない: cloud 証拠の
取得・捏造は行わず、`actor_input` / `evidence_source` が `missing` のままである
ことを前提に fail-closed 設計とした。

`src/collection/adapters/youtube/request.py`
（+ `tests/collection/test_youtube_apify_request.py` 40 tests）:

- `build_actor_input` / `plan_actor_input`: 宣言済み query text＋`date_filter` を
  `youtube-apify-scraper`（`h7sDV53CddomktSi5`）の actor input
 （`searchQueries` / `dateFilter` / `maxResults` / `maxResultsShorts` /
  `maxResultStreams` / `sortingOrder`）にするだけの純粋関数。送信しない、環境変数
  を読まない、response／per-video field を含まない。actor ID・input 語彙は repo 内
  証拠のみ（`config/collectors.json` の `external_id`、skill の input schema、
  `apify_csv.DATE_FILTERS` を単一 source of truth として再利用・重複定義なし）。
- `date_filter="all"` は `dateFilter` を省略する（unbounded 形状。skill の filter-less
  例に準拠。actor に `all` 値は存在しないため `dateFilter="all"` の送信は捏造になる）。
- plan の絶対 window は観測範囲であり input に使わない（`plan_actor_input` は window
  なしでも計画できるし、window の違いは input を変えないことを test で固定）。
  keyword＋絶対範囲は当該 actor では実現不可（skill: `startUrls` は `searchQueries`
  を上書き、`oldestPostDate` は channel-URL 専用）のため、channel-URL mode の
  `startUrls` / `oldestPostDate` / `sortVideosBy` は never emit。
- `max_results` 系は正整数（Shorts/streams は非負）の pass-through のみ。件数上限の
  強制・示唆はしない（上限の適用は COL-032 の範囲）。`sortingOrder` は skill 語彙のみ
  受け付け、意味論は unverified のまま。
- live transport は未実装のまま: `YouTubeApifyCsvAdapter.collect` は
  `LIVE_TRANSPORT_UNIMPLEMENTED` で fail closed（X と同一コード＝同一規則）。`youtube`
  は `_FACTORIES` / `_LIVE_SESSIONS` に未登録（収集可能に見せないため意図的）。
  registry は不変: `youtube-apify-scraper` は `status: unverified` / capability 全
  `unknown` / `version: unknown` のまま。`config/collectors.json` の変更は無い。

## 残件整理（2026-10-15: YouTube / on-hold 分離。本 issue は OPEN のまま）

- implemented offline（本 issue で完了）: YouTube Apify CSV handover adapter／driver
  wrapper＋契約テスト、`dateFilter=year` window compiler、YouTube Apify actor-input
  request planner＋契約テスト（request-only evidence、per-video 行なし、送信なし）。
- blocked by Apify evidence（PRV-013）: actor run ID／dataset ID／actor input／開始終了
  の cloud 照合と evidence registry 登録。`actor_input` と `evidence_source` が全 run
  で `missing` の間は capability 昇格なし（`unknown` 維持）。PRV-013 完了後に昇格要否を
  判断する。
- blocked by owner token/access: owner 支給 token、件数上限と承認フロー（COL-032）、live
  送信の別途明示承認。3 点が揃うまで `collect` は fail-closed のまま。live transport
  の pagination／retry 設計は未着手。
- on hold（owner 決定 2026-10-15）: X／TikTok／Instagram 用 adapter 作業は着手しない。
  既存の X dry-run slice（`src/collection/adapters/x/`）は変更なし。未実装を実装済み
  として扱わない。

完了条件のうち満たしたのは YouTube の offline slice（handover adapter＋契約テスト、
request planner＋契約テスト）のみであり、「capability の実測と registry 更新」は未了
（PRV-013 待ち）。X／TikTok／Instagram は on hold のため対象外。本 issue は OPEN
のまま残す。
