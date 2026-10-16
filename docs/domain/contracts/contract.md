# 契約 Contract — Agent Contract

**版:** 0.1.0（草案、2026-10-16）  
**語彙:** `docs/domain/glossary.md`（契約・バージョン・リリース）。下位種別のゲート契約の所有も契約とする（owner決定 2026-10-16）。

## Purpose and domain vocabulary

境界を越えて渡されるデータ／振る舞いについて、版（＝バージョン）を持ち機械検証可能な形で宣言した合意を束ねる総称。実体はスキーマ契約・レジストリ文書・インターフェース契約・ゲート契約・判断記録と唯一の台帳。

## Owned paths (advisory ownership)

- `metadata/`（queries / windows / studies / measurements / artifacts / taxonomy / schema / provenance / publication envelopes）
- `config/`（sources / collectors / storage-policies 等のレジストリ文書）
- `src/validation/schemas/`＋`schema_registry.py`（`SCHEMA_REGISTRY` / `SCHEMA_VERSIONS`）
- `src/validation/contract_ledger.py`（`GATE_CONTRACTS`、`_interface_contracts()`）
- `docs/specs/contracts.md`（正本）、`docs/audits/contract-ledger.json`（生成物）

## Invariants and acceptance criteria

- 新規スキーマ登録時は owner / group を省略できない（§4規則3。`test_contract_ledger.py` が強制）。
- 未宣言は推測で補わない。`version: None` はギャップ（G1/G2）として記録する（§10）。
- 契約 ID は `<domain>-<object>-v<major>` 形式。CLI サブコマンド 1 つ＝判定 1 つ（ゲート契約、§6）。
- 監査レポートと台帳は再生成一致する（付録A4・A5）。

## Public interfaces / integration events

- 唯一の一覧：`contract-ledger.json`（宣言から導出。手書きしない、§8）。
- 登録口：`REGISTRY_FILES` / `METADATA_REGISTRY_FILES`（検証対象化の登録）、`SCHEMA_REGISTRY`＋`SCHEMA_VERSIONS`、`GATE_CONTRACTS`。
- 証拠の記録（evidence registry）、公開判断（publication decision）は判断記録としてここに載る。

## Allowed dependencies

- 全コンテキストがここに宣言する（宣言場所の提供が責務）。
- 台帳生成が各宣言元を読むこと（導出方向のみ。逆方向の手書き同期はしない）。

## Forbidden dependencies

- 台帳 JSON の手書き編集（§8。宣言を直せば消えるギャップは宣言側で直す）。
- G 別名（G1〜G7 / P6）の改名（別名として保持。§7）。
- 版の推測付与（G1/G2。必要になった時点で付与し、付与時は台帳＋context-map を同時更新。U4）。

## Cross-context change protocol

- スキーマ追加は §9 の 6 手順（登録＋`SCHEMA_SCOPE`＋Contract Test＋台帳再生成＋テスト＋版上げ時は framework §9 準拠）。
- ゲート契約に版を付与する日は、定数＋台帳列＋一致検査の 1 組を新設し、`context-map.md` §5 を同時更新する。付与の再判断トリガー（T1 意味変更／T2 並存／T3 引用）は Escalation の U4 決定を参照する。
- U2 の正本同期は 2026-10-16 に完了（`contracts.md` §2・§2.1・§3.2・§4規則4、台帳 `GATE_CONTRACTS` の owner を `contract` に更新し `contract-ledger.json` を再生成）。

## Required tests and CI checks

- `tests/validation/test_contract_ledger.py`、`test_schema_coverage.py`、`test_audit_report_freshness.py`
- `make gates`（registries valid）、`make audit-publication`（record-only の記録更新）。
- CI: `research-validation.yml` の registry 検証ステップ。

## Escalation and human approval triggers

- 新規スキーマ登録の owner / group 決定（テストが落ち続ける設計。決定なき登録は通さない）。
- G1 の版付与判断（owner決定 2026-10-16:案C「未宣言維持 + トリガー条件を正式化」を採用。版は未宣言のまま維持し、G1 は意図的に open の既知ギャップとして残す。正式トリガー T1 意味変更／T2 並存／T3 引用のいずれかが成立した場合に owner が版付与を再判断する。全文は `docs/domain/decision-briefs/U4-gate-contract-version.md` §3）。G2 の版付与判断は人間の認定事項として残る。U3 は隣接 protocol として owner決定済み（2026-10-16。詳細は `docs/domain/decision-briefs/U3-validation-storage-dependency.md` §4。allowlist test は実装済み（`tests/domain/test_storage_validation_adjacency.py`））。
- 判断記録の作成・承認（公開承認・証拠フラグ。`gate-publication` の人間 reviewer）。
