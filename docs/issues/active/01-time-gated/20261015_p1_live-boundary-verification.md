# Issue: ライブ収集による Google Trends の境界挙動検証がパス 2 待ち（`exact=true` 昇格条件）

**ID:** ISS-20261015-GT-001  
**優先度:** P1 (High)  
**ステータス:** PENDING (2026-10-15: owner `go` によりライブ計測は承認済み。パス 1 は実行・採用済みで、パス 2 は 2026-10-22T04:28Z 以降の time gate 待ち。オフライン計測基盤・手順・昇格規則は実装・文書化済み — `docs/specs/gt-boundary-verification.md`, `docs/reports/20261015b-gt-boundary-verification.md`)  
**対象:** `src/collection/adapters/google_trends/compiler.py`, `config/collectors.json`（`google-trends-mcp`）, `metadata/windows/`

## 概要

Google Trends の window compiler は、現時点で**すべての compile で `exact=false` /
`boundary_semantics=unverified` を返す**。実装の欠落ではなく検証の欠落で、「相対 timeframe
（`today 12-m` / `today 5-y`）が collector 側で実際にどの暦区間へ解決されるか」を
ライブ収集で実測していないため。`window.exact_required: true` の plan は全件停止する。

## 確認された観測

- `config/collectors.json` の `google-trends-mcp` は `absolute_date_range: unknown` /
  `relative_date_range: supported`。
- `metadata/windows/` の 2 件（`2025-10-12_2026-10-12` / `2021-10-10_2026-10-12`）は
  いずれも相対 timeframe にしか対応しない。
- 2026-10-15 に実記録応答（`records_cbd-rikiddo-5y.json`、262 点）でレスポンス形状の照合は
  行ったが、**窓の境界**は未検証（要求窓と観測範囲の一致を実測していない）。

## 影響

- 期間の厳密一致を要求する研究は plan として実行できない。
- 公開文書で窓を「正確な期間」として扱えない（要求窓と観測範囲を併記する必要がある）。
- capability が `unknown` のままなので、他ソースとの比較可能性判断にも波及する。

## ライブ収集の実行経路（2026-10-15 実装）

本 issue の行列（`CBX` × 4 timeframe × 2 pass）は従来 harness（`boundary`）と
外部 MCP セッションの組み合わせを前提としていた。**パイプライン側にライブ収集の経路が実装された**ので、
今後は次の 2 経路がある。

| 経路 | 実装 | 用途 |
|---|---|---|
| pipeline のライブ収集 | `collection.core.cli collect --live`（`SessionMcpTransport` + `mcp_session.McpStdioSession`）。run には **verbatim な tool result（生）** と **解析済み系列（派生）** の 2 成果物が入り、L1 を通ったものだけ catalog に入る | 研究データの収集（本 issue の 7 run はこちら） |
| boundary harness | `collection.adapters.google_trends.boundary`（capture manifest → verify → stage） | 境界計測。**計測用の窓は study window ではない**ため、登録済み window を要求する pipeline の plan とは意図的に分離している（spec §4.2） |

- 両経路は MCP サーバ（`google-trends-mcp@0.1.1`）と**同じ parser（spec §4.4）**を使う。
- 2026-10-15 のライブ計測で**実形式の差異を 2 件検出して parser を更新**した（細い空白 U+2009、年を両側に書く範囲ラベル）。
  詳細は `docs/specs/gt-boundary-verification.md` §4.4 の追記と、当該 run の生 payload（保全済み）。
- 通常の 5 年・12ヶ月系列（土曜起点ではなく日曜起点の週次）では、実測の初回ラベルは
  **2021-10-10**（登録済み 5y window の start と一致）。

### 未実施

- 本 issue の行列は pass 1（4 call）まで実行済み。残りは、参照時刻を **7 日以上**離す必要がある
  pass 2（4 call）のみ。pass 1 だけでは `eligible=true` にできない（spec §3 の昇格規則は
  2 pass の一致を要求）。
- **追記（2026-10-15、実施⑧）**: 同じ日に**研究データ用のライブ収集は 8 run 実施した**
  （`collect --live`、CBN / THC-O / H4CBH / HHBD / HHCH / CRDP / THCH / CRDH）。
  これでライブ経路（MCP stdio セッション）は end-to-end で実証されたが、
  **それらは本 issue の証拠にはならない**: 行列の run は
  `environment.measurement.protocol` を持ち `evidence class = measurement` である必要があり
  （spec §2）、pipeline の run は `recorded_legacy` と同様に昇格には使えない。
  したがって本 issue は **PENDING のまま**で、残る作業は**行列（4 timeframe × 2 pass、
  参照時刻を 7 日以上離す）のうち pass 2**だけである。

## 対応方針

- ライブ収集（別途承認）で同一クエリを複数の相対 timeframe で取得し、観測境界を記録する。
- 暦上の解決結果（基準時刻からの期間計算）と実測境界を比較し、差異を capability 昇格の
  判断材料にする。**推測で `exact=true` にしない。**
- ライブ収集が実施できない間は、`exact=false` の理由を run の `limitations` に残す運用を続ける。

## 完了条件

- [x] ライブ収集 1 回以上の実測 run（`run_metadata.json` として保存。`environment.measurement.protocol` を持つ **measurement クラス**）
      — 2026-10-15 にパス 1（4 timeframe × 1）を実行し、4 run を `cbx-search-trends` に採用
      （`docs/reports/20261015b-gt-boundary-verification.md` §15）
- [x] 要求窓と観測境界の対応表（timeframe 別）— 同 §15.2 の表 + `validation.cli boundary-report`
      の `rule` / `rows`（名目解との差は 4/4 週次 1 バケット以内 = `consistent`）
- [x] `exact` 昇格条件の文書化、または昇格しない場合の理由の記録 — 条件は
      `docs/specs/gt-boundary-verification.md` §3（timeframe ごとに 2 run、参照日が 7 日以上
      離れる、境界が再現する）。現在 `eligible=false`（timeframe あたり 1 run）で、
      理由はカレンダー（パス 2 が 7 日以上後）

## パス 1 の実行記録（2026-10-15）

行列の **パス 1**（4 timeframe）を実行し、4 run を採用した（上述の完了条件）。
計測 manifest の sha256 は `f39995eb24e3008367ee776b6763037aa704c1a5594f1c413b5bb4410bcdecd8`
（ワークスペース外の一時入力。証拠は採用済み run 側に保全されている）。
詳細・コマンド・観測値は `docs/reports/20261015b-gt-boundary-verification.md` §15。

**残りはパス 2 のみ**（同じ行列を参照時刻 7 日以上後に実行）。パス 2 まで `eligible=true` には
できない（spec §3 の昇格規則）ため、本 issue は **PENDING のまま**とする。

### 未実施（更新）

- パス 2（参照時刻を 7 日以上離す）。その後 `rule.eligible` を確認し、昇格する場合は
  `config/collectors.json` / compiler を変更として記録する（**推測で `exact=true` にしない**）。

## 経過（2026-10-15）

オフラインで可能な部分を実装・検証した後、owner `go` によりライブ境界計測の pass 1 を実行・採用した。
完了条件のうち pass 1 と昇格規則の文書化は充足済みだが、pass 2 が time-gated のため
`PENDING` のままとする。

- 実装: キャプチャ検証 / staging（`collection.adapters.google_trends.boundary`）、
  対応表と昇格規則の評価器（`validation.cli boundary-report`）、テスト 37 件。
- 文書: 実行プロトコルと昇格規則 = `docs/specs/gt-boundary-verification.md`。
  計画・レビュー・オフライン結果・**メンテナへの単一の承認質問（D1）** =
  `docs/reports/20261015b-gt-boundary-verification.md`。
- オフライン証拠: tracked な実記録 5y run（2026-10-12）は名目モデルと `consistent`
  （offset −2.28 / +5.72 日）だが `recorded_legacy` クラスであり昇格には使わない。
- 副産物: `boundary-report` が旧 run のラベル年誤りを検出
  （ISS-20261015-GT-002）。

完了条件の充足には、パス 2（2026-10-22T04:28Z 以降の 4 run）と `boundary-report` の
`eligible=true`、および証拠を伴う昇格変更が必要。
