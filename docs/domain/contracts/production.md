# 生産 Production — Agent Contract

**版:** 0.1.0（草案、2026-10-16）  
**語彙:** `docs/domain/glossary.md`（生産・出荷・加工）。本契約は作業調整のためのもので、ファイルシステムの強制ではない。

## Purpose and domain vocabulary

契約準拠の記録（run / artifact / 加工成果物 / 生成値）を産出する側。収集・加工を内包する。契約に含まれる検収条件・検証項目を評価し、契約に沿って成果物を保管先へ出荷する。判定ルール・判定理由・可否の意味は独自所有しないが、契約遵守のために検証ゲートを呼び、結果をワークフロー制御として執行する（`contracts.md` §3.1、`context-map.md` U5）。

## Owned paths (advisory ownership)

- `src/collection/`（pipeline / staging / adapters）
- `src/processing/`（実装の置き場所。境界上の扱いは `processing.md`）
- `Makefile` の生産ターゲット（`collect` / `stage` / `adopt-all` / `platform-trends`）
- `.staging/`（作業域。gitignored、公開しない）

## Invariants and acceptance criteria

- 生産は契約に含まれる検収条件・検証項目を評価する。判定ルール・判定理由・可否の意味は契約／ゲート側に従い、生産側で独自所有しない。
- 生産は契約に従って実行されなければならない。契約遵守のために検証ゲートを呼び、失敗時は開始・採用・出荷・公開相当の遷移を停止または隔離する。
- 出荷は、検収条件・検証項目・保管条件を満たした成果物を、指定された保管先（local / repository / remote）へ引き渡す工程であり、リリース（配布単位・配布行為）とは区別する。
- 生産の出力は記録であって解釈ではない（§3.1規則3）。
- raw は不変。修正・正規化は下流層で行う（AGENTS.md Raw Data Rule）。
- producer は採用を決めない（staging 宣言駆動。AGENTS.md 生産入口点）。

## Public interfaces / integration events

- `run_metadata.json`（`collection-run-v1`）：収集実行の確定イベント。
- `artifact-manifest.json`：成果物の登録イベント。
- staging 宣言（`staging-declaration-v1`）：外部取得ペイロードの持込口。宣言なく `datasets/` に直書きしない。
- `data/processed/*`＋`manifest.json`：加工成果物（導出宣言と対になる）。

## Allowed dependencies

- 検証への形状適合（run 記録がスキーマ契約を満たすこと。判定される側として）。
- 検証ゲートの呼び出しと執行（`pre_collection_gate` / `post_collection_gate` 等）。これは契約違反の生産・出荷を防ぐワークフロー制御であり、判定ルールの所有ではない（U5）。
- 保管への受け渡し（artifact descriptor。読むのは検証側）。

## Forbidden dependencies

- 採用・隔離の判定ロジックを生産側に持つこと（gate が自分の入力を生成するコードに依存しない。P5）。
- 検証ゲートの迂回、または失敗したゲート結果の無視。
- 既存 raw の上書き・現場正規化。
- 判定ゲートの迂回（framework 外 shell からの `datasets/` 直書き）。

## Cross-context change protocol

- 新規 run の追加後は監査スナップショットを再生成する（freshness registry 対象）。
- 新規 source / collector は capability を実測後に registry へ記録する（推測で `supported` にしない）。
- adapter 追加は共通 Contract（`collection.core.contracts`）実装＋契約テストが対になる。

## Required tests and CI checks

- `tests/collection/test_adapter_contract.py`、`test_staging_driver.py`
- `tests/domain/test_production_verification_separation.py`（生産・検証境界 T1–T4。U5）
- `make audit-new-runs`（failures=0）、`make gates`（registries valid）
- CI: `research-validation.yml` の collection 関連ステップ。

## Escalation and human approval triggers

- 新規 source の live 収集開始（X official API は owner 明示承認が別途必要）。
- 新規 adapter の capability 宣言（`unverified`→実測値への変更は記録を伴う）。
- 収集条件の変更（query / window / filter）は run として区別し、仮説に有利な run の黙示選択をしない（AGENTS.md Repeated Collection）。
