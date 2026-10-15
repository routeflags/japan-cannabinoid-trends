# Issue: GT 境界計測のパス 2（参照時刻を 7 日以上離した再計測）

**ID:** ISS-20261015-GT-004  
**優先度:** P1 (High)  
**ステータス:** PENDING (2026-10-15: パス 1 を実行済み。パス 2 は参照時刻の隔たりが必要で、最速 2026-10-22 以降)  
**対象:** `docs/specs/gt-boundary-verification.md` §3/§4、`collection.adapters.google_trends.boundary`、
`ISS-20261015-GT-001`（PENDING）、`docs/reports/20261015b-gt-boundary-verification.md` §15

## 概要

境界計測の行列（CBX / geo JP / 4 timeframe）は**パス 1 だけ実行済み**
（2026-10-15、4 run を `cbx-search-trends` に採用、`boundary-report` 4/4 `consistent`）。
昇格規則（spec §3）は「timeframe ごとに 2 run、参照日が 7 日以上離れ、境界が再現する」ことを
要求するため、**パス 2 が無いと `eligible=true` にならない**。

パス 1 の参照時刻は 2026-10-15T04:28Z なので、パス 2 は **2026-10-22T04:28Z 以降**に実行する
（それ以前の実行は隔たり不足で証拠にならない）。

## 確認された観測（パス 1、2026-10-15）

- 行列: term `CBX`（登録クエリ `cbx-general-ja`）/ geo `JP` /
  `today 1-m`（31 点）、`today 3-m`（93 点）、`today 12-m`（53 点）、`today 5-y`（262 点）。
- 429 / retry / `isError` なし。`verify` 4/4 parsed。
- 4 run は `environment.measurement.protocol` を持ち、`boundary-report` で
  `measurement` クラス / `consistent`。
- `rule.eligible` は false: コホートが 4 run（timeframe あたり 1）で規則の最小数（2）に届かない。
- 採用 run: `20261015T04284{5,9}Z-…-1m/3m`、`20261015T04285{3,7}Z-…-12m/5y`
  （`datasets/cbx-search-trends/data/raw/google_trends/`）。

## 影響

- 現状 `exact=false` のまま: `window.exact_required: true` の plan は停止し続ける。
- パス 2 の期日を逃すと、パス 1 の参照時刻から起算して「7 日以上」が事実上リセットされる
  （新しいパス 1 が要るわけではないが、2 回目の参照が 7 日後のものになる）。

## 対応方針

パス 1 と同じ手順を参照時刻 7 日以上後に繰り返す
（手順は `docs/reports/20261015b-gt-boundary-verification.md` §15 の §15.5。
manifest は実行中の入力で、証拠の正本は採用済み run）:

1. MCP セッション（`google-trends-mcp@0.1.1`）で 4 timeframe を各 1 回計測し、
   verbatim の tool result を capture manifest に書く
   （`capture_version: 1.0.0`、run_id は `<UTC時刻>-google-trends-boundary-<timeframe slug>`）。
2. `boundary verify --manifest` で形式検証（不一致なら行列を止めて parser を更新。spec §4.4）。
3. `boundary stage --study cbx-search-trends` → `adopt`（L1 通過のみ catalog）。
4. `boundary-report` で `rule.eligible` を確認する。
5. **昇格判断**: eligible なら `config/collectors.json` と compiler の `exact` / capability を
   **変更として**記録する（推測で `exact=true` にしない）。eligible でなければ理由を記録する。

## 完了条件

- [ ] パス 2 の 4 run の採用（参照時刻がパス 1 から 7 日以上後、verbatim 保全）
- [ ] `boundary-report` の `rule.eligible` の確認記録
- [ ] 昇格する / しないの判断と、その変更（または理由）の記録
- [ ] `ISS-20261015-GT-001` の PENDING 解消と監査スナップショットの再生成

## 依存

- `ISS-20261015-GT-001`（親 issue。本件はパス 2 の実行記録）。
- 実行は承認後に限る（spec §4.1）。本件はパス 1 と同じ承認の継続とみなすかどうかを
  メンテナが確認する。
