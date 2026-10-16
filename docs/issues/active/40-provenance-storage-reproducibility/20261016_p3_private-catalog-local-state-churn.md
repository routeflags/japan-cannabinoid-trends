# Issue: g6-private-catalog 再生成がマシン固有状態を持ち込む

**ID:** ISS-20261016-MNT-002  
**優先度:** P3 (Low)  
**ステータス:** OPEN  
**対象:** `docs/audits/g6-private-catalog.json`, `src/validation/private_catalog.py`, `tests/validation/test_audit_report_freshness.py`（`boundary_only` normalizer）, `Makefile`（`audit-snapshots`）

## 概要

`make audit-snapshots` が `docs/audits/g6-private-catalog.json` を毎回書き換えるが、
差分は実行マシンのローカル状態（gitignored の `datasets/*/data/private` の有無）だけであり、
リポジトリの事実は変わらない。鮮度テストは `boundary_only` normalizer で当該欄を除外している
（ISS-20261015-AUD-028）ためテストは通るが、コミットするとコミッターの checkout 状態が
正本として混入する。

## 確認された観測

- 2026-10-16 の保守で再生成すると `present: 1 → 0` / `absent: 8 → 9` /
  `datasets/cbx-social-trends/data/private` の `exists: true → false` になった。
- 当該 checkout に `data/private` が無いためのみであり、宣言境界（count / entries の
  `exists` 以外）には差分が無い。
- 上記理由により当該ファイルは committed 版のまま戻し、保守コミットには含めていない。

## 影響

- 現状の実害は無い（テストは normalizer で吸収）。
- `make audit-snapshots` のたびに人手で戻す必要があり、誤ってコミットすると無意味な churn になる。

## 対応方針

- owner 決定待ち。小規模な選択肢: (a) generator に committed 専用出力を設ける、
  (b) `audit-snapshots` から当該ファイルを外し鮮度テストのみで担保する、(c) 現状維持（再生成後に戻す運用）。
- いずれも `exists` 欄の扱いを `docs/specs/validation-framework.md` に一行で明記する。

## 完了条件

- [ ] `data/private` の有無が異なる 2 checkout で `make audit-snapshots` しても当該ファイルに差分が出ない
- [ ] `make test` が green のままである
