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

- 対象ソースと着手順を決める（研究上の優先度と、Apify 生レスポンスの確保可能性で決まる）。
- adapter は共通 Contract（`collection.core.contracts`）を実装し、契約テストを追加する
  （架空ソーステストと同じ型で検証する）。
- capability は実測後に registry を更新する（推測で `supported` にしない）。

## 完了条件

- [ ] 対象ソースと着手順の決定
- [ ] adapter 実装 + 契約テスト
- [ ] capability の実測と registry 更新（未確認は `unknown` のまま）
