# Issue: catalog 配置が追跡方針・事前検査パターンと一致しない（GT run が無追跡になる）

**ID:** ISS-20261015-COL-018  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `.gitignore`, `docs/specs/raw-data-policy.md` §4.1, `scripts/git-hooks/pre-commit`, `config/storage-policies.json`, `src/collection/core/pipeline.py`（`_catalog_dir`）

## 概要

pipeline が run を catalog する先は `datasets/<study>/data/raw/<run-id>/` で、**source 階層を
持たない**。一方、Google Trends の raw 追跡例外（`!**/data/raw/google_trends/**`）と
pre-commit の調査ページ検査パターン（`datasets/*/data/raw/google_trends/*`）は source 階層を
前提にしている。したがって pipeline が catalog した GT run は**無追跡**になり、追跡前提の
検査も発火しない。

## 確認された観測

```
$ git check-ignore -v --no-index datasets/cannabinoid-multi-trends/data/raw/<run-id>/payload.json
.gitignore:2:**/data/raw/*        ... （無視される）
$ git check-ignore -v --no-index datasets/cannabinoid-multi-trends/data/raw/google_trends/x/run_metadata.json
.gitignore:7:!**/data/raw/google_trends/**  ... （追跡対象）
```

- `raw-data-policy.md` §4.1 は GT の raw を「公開データのため raw を公開」としており、
  既存 29 run は `data/raw/google_trends/` 配下で追跡されている。
- YouTube 側は study の `data/.gitignore` が `*` のため、どちらの配置でも無追跡（方針どおり）。

## 影響

- 「GT の raw は公開」という方針と、pipeline が作った GT run の実際の追跡状態が乖離する。
- 追跡された raw を対象にした事前検査（調査ページ・スキーマ）が、pipeline 由来の run には
  適用されない。

## 対応方針

- (a) catalog に source 階層を導入する、または (b) gitignore / policy / hook パターンを
  catalog 配置に合わせる。どちらにするかを実装前に決める。
- 決定は raw の配置規約（`AGENTS.md` の dataset structure）と既存 29 run の互換性を同時に見て行う。
- 決定を先送りしたまま実 run を catalog しない（無追跡の raw を黙って増やさない）。

## 完了条件

- [x] (a)/(b) の決定と理由の記録 — **(a) source 階層**（オーナー決定。Q5 で YouTube への適用も確定）
- [x] 決定に応じた変更と `git check-ignore` の実測（下記「実装記録」）
- [x] 既存 run（`data/raw/google_trends/` 配置）との互換確認（44 run。flat 配置の残存ゼロ）

## 実装記録（2026-10-15、最優先対応）

- `src/collection/core/pipeline.py`: `_catalog_dir(..., source_id)`＋`_source_slug`
 （`google-trends`→`google_trends`、欠損→`unknown`）。`_finalize` と上書き禁止検査が
  plan/document の `source_id` を渡す（`collect` / `adopt_staged` / `stage_run` の全経路）。
  陳腐化 docstring 2 件（`:24`、`:129-131` の flat 配置記述）を source 階層に修正。
- 互換: ディスク上の run は 44 件（multi 36＋cbx-search 8）で全件 `google_trends/` 配下。
  `data/raw/` 直下の run 配置はゼロ。GT 境界 run（2026-10-15 採用 4 件）も同配置で正常に追跡対象。
- `git check-ignore` 実測: GT payload は非無視（終了 1＝追跡対象）、
  `youtube-consistency` 配下は study の `.gitignore`（`*`）で無視のまま（方針どおり）。
- pre-commit hook §3 の調査ページ検査パターンは source 階層済み（`x` / `youtube` / `google_trends` / `coa`）。
  新配置パスとの照合を shell の `case` で無副作用検証し 3/3 一致。hook 自体のテストは無い（既存の状態を維持）。
- 方針整合: `raw-data-policy.md` §4.1 は既に per-source 配置（`data/raw/google_trends/`、`data/raw/gsc/`）を前提。
  `AGENTS.md` の dataset structure は層名のみで配置詳細を持たないため変更不要。
- テスト: 新規 `tests/collection/test_catalog_layout.py` 4 件（slug 変換・`unknown` 退避・配置）。
  既存 e2e が `google_trends` 配置を assert。全 suite **1080 passed**（`pytest -q`）。

**ステータス: RESOLVED（2026-10-15）**。YouTube 採用（COL-033 Q5）の実装待ち条件は解消。
