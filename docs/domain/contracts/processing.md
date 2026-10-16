# 加工 Processing — Agent Contract

**版:** 0.1.0（草案、2026-10-16）  
**位置:** 生産の下位コンテキスト（owner決定 2026-10-16、`context-map.md` §4 U1）。  
**語彙:** `docs/domain/glossary.md`（加工・生産）。

## Purpose and domain vocabulary

派生成果物の導出宣言と生成値。観測（raw）から再現可能に導くことが責務。解釈は含まない。

## Owned paths (advisory ownership)

- `src/processing/`（builders / anonymize / reproduce / rulespec）
- `datasets/*/data/processed/`（出力。入力 raw は所有しない）
- `processing.cli` の build 系サブコマンド（`build-platform-trends`、`gt-summary` 等）

## Invariants and acceptance criteria

- コミット済み派生表は再導出と一致する（`contracts.md` 付録A4）。不一致は drift として申告する。
- 欠測とゼロを混同しない（`observed_zero` / `missing` / `collection_failed` 等の区別）。
- 異種ソースの数値を等価に扱わない（source-specific units を保持。metric dictionary が比較可否を宣言）。
- YouTube の video-level 行を再配布しない。X の投稿単位データを公開しない（匿名化後も不可、COL-030）。

## Public interfaces / integration events

- 入力：`docs/audits/gt-summary.json`、query registry、raw artifact。
- 出力：processed CSV 群＋`manifest.json`（row_counts を自己申告）。
- 導出宣言：`src/processing/reproduce.py` の `DERIVATIONS` / `NON_REPRODUCIBLE` / `WITHDRAWN`。

## Allowed dependencies

- 検証の再導出検査（`reproduce_artifact`、`audit-processed`）。
- 保管 reader の読み取り利用（証拠の読み。書くのは保管側）。

## Forbidden dependencies

- raw の書き換え（再導出のためであっても不可）。
- 未登録の派生 artifact のコミット（`STATUS_UNDECLARED` は失敗。`test_artifact_in_no_registry_fails_the_audit`）。
- 派生表への解釈列の混入（記録と解釈の分離）。

## Cross-context change protocol

- 新規派生表は `DERIVATIONS`（再導出可能）または `NON_REPRODUCIBLE`（欠落入力を明記）のどちらかに必ず登録する。
- 加工出力の変更は `docs/audits/g4-storage-inventory.json`・`g6-git-tracking-inventory.json` の再生成を伴う（`make audit-snapshots` を加工再構築の後に回す）。
- テストの固定期待値（row_counts 等）は再計算値への更新とし、raw を変えて辻褄合わせしない。

## Required tests and CI checks

- `tests/processing/test_platform_trends.py`、`test_processed_artifacts.py`
- `make platform-trends` の出力が `make test` の期待値と一致すること。
- CI: `research-validation.yml` の processed artifact 監査ステップ。

## Escalation and human approval triggers

- 新規公開集計の追加（privacy・再配布条件の事前審査。AGENTS.md Publication Gate 7–8）。
- 投稿単位系の扱い変更（公開可否は owner 決定。COL-030 §4.1 が正本）。
- 既存派生値の訂正（新 commit＋CHANGELOG＋新 release。 published release の書き換え禁止）。
