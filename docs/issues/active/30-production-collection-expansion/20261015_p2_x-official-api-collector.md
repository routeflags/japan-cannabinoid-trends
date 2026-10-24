# Issue: X 公式 API v2 の collector / adapter が無い（Apify 依存の解消含む）

**ID:** ISS-20261015-COL-031  
**優先度:** P2 (Medium)
**ステータス:** OPEN  
**対象:** `config/collectors.json`, `config/sources.json`, `src/collection/adapters/`（X 用 adapter は未作成 = COL-016）, `metadata/queries/query-registry.json`, `metadata/windows/`, `src/collection/x/*.md`, `.github/skills/apify-*x*/SKILL.md`, `datasets/cbx-social-trends/methodology.md`

## 概要

`ISS-20261015-COL-030`（X公式API移行指示書）§3 は、X の取得を Apify の第三者 Actor から
X API v2（`GET /2/tweets/search/all`）へ移行することを求めるが、現状 X の収集は
Apify 経由の運用知識（skill / notes）だけがあり、パイプライン側の collector / adapter は
存在しない。

## 確認された観測

- `X_BEARER_TOKEN` / `api.x.com` を参照する記述はリポジトリに **0 件**（実測）。
- `config/collectors.json` の X は `x-apify-twitter-search`（`adapter_id: x-apify-twitter-search@1`,
  status `unverified`）のみ。`absolute_date_range` / `relative_date_range` はともに `unknown`。
- X 用の collection adapter は未実装（`src/collection/adapters/` に X は無い。COL-016 の範囲）。
- X の窓語彙は `metadata/windows/` にも registry にも無い（WIN-002 の範囲）。
- 運用知識は `.github/skills/apify-*search*/SKILL.md` と `src/collection/x/{apify-x-search.md,
  punch-pattern-apify-date-filter.md}` に散在し、機械可読な registry には無い。

## 影響

- 指示書の完了条件のうち「X公式APIで過去投稿を取得できる」「非公式スクレイピングへの依存が
  なくなっている」「ページネーションとエラー処理が動作する」が満たせない。
- 収集手段を変えると観測コーパスと来歴（collector_id / adapter_id）が変わるため、後から
  既存 run と混ぜると来歴が崩れる。

## 対応方針

- **owner 決定（2026-10-15）:** X は live request へ進まない。当面は mock / dry-run と
  request-only evidence の実装に限定し、外部への実リクエストや X 元投稿データのリポジトリ保存を伴う経路は
  禁止する。
- `collection.core.contracts` の adapter 契約に従う X 用 adapter（transport = 公式 API）を実装し、
  `config/collectors.json` に新しい collector（例 `x-api-v2`）を **`unverified` で追加**する
  （registry が正本。実測後に status を上げる）。
- 窓は公式 API の `start_time` / `end_time`（絶対期間）を使えるため、X の window compiler で
  `absolute_date_range: supported` を宣言できるか実測で確定する（WIN-002 の一部を先に解く）。
- 検索語・対象成分・期間は `metadata/queries/query-registry.json` の既存定義（`cbx-liquid-ja` 等）
  を再利用し、変更しない（指示書 §2 / §6）。
- 既存 Apify 資産の扱いを記録する: registry の旧 collector は履歴参照として残す（`legacy` /
  `deprecated` 相当）、skill / notes には「公式 API へ移行済み」の日付付き注記を入れる。
- 実取得で得た X 元投稿データはリポジトリ artifact にしない。既存 core に接続する場合も、採用対象は機密除去済み request-only evidence と派生集計に限り、raw を手書きしない。
- 件数上限と実行制御は `ISS-20261015-COL-032`、証跡は `ISS-20261015-PRV-033` が受け持つ。

## 完了条件

- [ ] X 公式 API v2 の adapter + collector 登録（`validate-registries` green を維持）
- [ ] ページネーション・レート制限・エラー処理のモックテスト（外部への実リクエストを発生させない。指示書 §8）
- [ ] 絶対期間（`start_time` / `end_time`）の可否を実測で registry に反映
- [ ] 既存 Apify X 資産の扱い（履歴参照 / 注記）の記録
- [ ] 1 run 以上の dry-run / mock / request-only evidence 経路を現行契約で検証（X 元投稿データはリポジトリに保存しない）

## 依存

- `ISS-20261015-COL-032`（live request 制御なしでは実取得に進まない）
- `ISS-20261015-PRV-033`（request-only evidence なしの実取得は完了条件を満たさない）
- owner 決定済み: `ISS-20261015-COL-030` U2 の当面値は **live request 禁止**。
- 未確定: `ISS-20261015-COL-030` U3（サンプリング条件）。live 実行は別途 owner 承認まで行わない。

## 対応記録（2026-10-15）

- owner 指示: 「Xはまだいい。youtube, gtの品質をたかめてから対応する」。
  これにより優先度を P1 から P2 へ下げる。X live request 禁止と X 元投稿データの
  リポジトリ保存禁止は維持する。
