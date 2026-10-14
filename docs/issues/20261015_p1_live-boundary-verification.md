# Issue: ライブ収集による Google Trends の境界挙動検証が未実施（`exact=true` 昇格条件）

**ID:** ISS-20261015-GT-001  
**優先度:** P1 (High)  
**ステータス:** OPEN  
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

## 対応方針

- ライブ収集（別途承認）で同一クエリを複数の相対 timeframe で取得し、観測境界を記録する。
- 暦上の解決結果（基準時刻からの期間計算）と実測境界を比較し、差異を capability 昇格の
  判断材料にする。**推測で `exact=true` にしない。**
- ライブ収集が実施できない間は、`exact=false` の理由を run の `limitations` に残す運用を続ける。

## 完了条件

- [ ] ライブ収集 1 回以上の実測 run（`run_metadata.json` として保存）
- [ ] 要求窓と観測境界の対応表（timeframe 別）
- [ ] `exact` 昇格条件の文書化、または昇格しない場合の理由の記録
