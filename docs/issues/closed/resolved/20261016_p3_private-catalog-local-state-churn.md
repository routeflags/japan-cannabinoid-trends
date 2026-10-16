# Issue: g6-private-catalog 再生成がマシン固有状態を持ち込む

**ID:** ISS-20261016-MNT-002  
**優先度:** P3 (Low)  
**ステータス:** RESOLVED (2026-10-16) — owner 承認の (a) で解消。下記「対応記録」参照  
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

- owner 決定済み（2026-10-16）: 小規模な選択肢のうち (a) generator に committed 専用出力を設ける、を採用。
  (b) `audit-snapshots` から当該ファイルを外し鮮度テストのみで担保する、(c) 現状維持（再生成後に戻す運用）。
- いずれも `exists` 欄の扱いを `docs/specs/validation-framework.md` に一行で明記する。

## 完了条件

- [x] `data/private` の有無が異なる 2 checkout で `make audit-snapshots` しても当該ファイルに差分が出ない
- [x] `make test` が green のままである

## 対応記録（2026-10-16、T-H）

- `src/validation/private_catalog.py`: `build_private_catalog(repo_root, *, include_local_state=False)`。既定は committed-safe（`exists` / `present` / `absent` は `null`＋`include_local_state: false`。`exists` キーは互換のため残す）。`tracked` は index 照会のまま（§25 の `tracked_only` と同じく追跡有無はリポジトリの事実で clean checkout 間では安定）、`ignored` は従来どおり trailing-slash の規則照会（ISS-20261015-AUD-028）。
- `validation.cli audit-private-catalog` に `--include-local-state` を追加。local mode は `exists` 真偽値＋`present` / `absent` 実数＋`include_local_state: true` を返す（コミット不可。checkout の実在検査専用）。
- `Makefile`（`audit-snapshots`）・CI（`.github/workflows/research-validation.yml`）・`scripts/validation/run-gates.sh` の変更は不要: `audit-snapshots` の当該行は既定＝committed-safe を呼ぶためそのまま正しく、CI は当該 catalog を実行しておらず、`run-gates.sh` に private-catalog 経路は無い。新規スクリプトも追加しない（既存 `validation.cli` 背後のまま）。T-G / MNT-003 との編集競合なし（本作業は Makefile 等に触れない）。
- `docs/audits/g6-private-catalog.json` を既定 mode で再生成（`present: 1 / absent: 8 / exists: true` → `null` 化＋`include_local_state: false`）。
- 鮮度検査は `boundary_only` normalizer を廃止し完全一致（`identity`）に戻した。local 状態の混入は今後テストで落ちる。`tests/validation/test_g6_vertical_slice.py` は T17 を 2 件化: 既定出力の checkout 独立性（private 有無でバイト同一）と local mode の実在報告。
- 実測: `datasets/cbx-social-trends/data/private` 有り／無しで既定出力を再生成し `diff` → バイト同一。local mode は有りで `present: 1 / absent: 8`、無しで `present: 0 / absent: 9`。対象テスト 39 件 PASS（下記検証参照）。
- `exists` 欄の扱いは `docs/specs/validation-framework.md` §25.1 行 (b) と §19.2 に明記（本 issue の対応方針の要求どおり一行以上）。
