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
  (3) X live request は費用 guard と証跡が通った後の別途明示承認、とする。
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
- 残件（本 issue は OPEN のまま）: live Apify transport（token/pagination/cost 設計が別途必要）、
  `dateFilter` window compiler（WIN-002 は未着手）、X / TikTok / Instagram 用 adapter は未実装。
  上の完了条件のうち満たしたのは YouTube CSV handover の adapter 実装 + 契約テストのみであり、
  「対象ソースと着手順の決定」「capability の実測と registry 更新」は未了。

## 完了条件

- [x] 対象ソースと着手順の決定（2026-10-15 owner `go 1,2`: YouTube Apify CSV pattern を先行）
- [ ] adapter 実装 + 契約テスト
- [ ] capability の実測と registry 更新（未確認は `unknown` のまま）
