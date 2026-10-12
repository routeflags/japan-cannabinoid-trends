# Validation Framework (Cerberus) — セットアップと運用

研究データ契約（G1〜G7）の構造検証フレームワーク。
仕様書: `docs/plans/20261013h.md`（ローカル計画書。`docs/plans/` はgitignore対象のため
リポジトリ履歴には含まれない）。

## 現状（2026-10-13 更新）

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | 既存環境監査 | 完了（監査結果は下記 §8） |
| Phase 2 | 依存導入・共通Validator・G5スキーマ・Contract Tests | 実装済み（コミット 654b5b9） |
| Phase 3 | Schema Registry 拡充（G1〜G7・running profile・バージョン管理） | **実装済み**（15 スキーマ登録。P3-10 は対象不存在のため §11 の決定により終結） |
| Phase 4 | Semantic / Integrity / Lineage / Git Policy / Comparability / Publication / Secret Scan | **実装済み** |
| Phase 5 | CLI・JSON Validation Report・Exit Code | **実装済み** |
| Phase 6 | 収集パイプライン統合 | 一部（ゲートライブラリ `gates.py` + `run-gates.sh`。`src/collection/*` 本体への配線は未実施） |
| Phase 7 | CI | 実装済み（`research-validation.yml` 新設。GitHub 上での実行は未検証＝push 後に確認） |
| Phase 8 | Legacy Audit | 実装済み（24件を非破壊監査。`docs/audits/g5-legacy-runs.json`、raw sha256 前後一致） |

## 1. 依存管理

`pyproject.toml` がリポジトリ唯一の Python 依存宣言。

- 実行時依存: `cerberus==1.3.8`（本リポジトリ初の第三者依存）
- 開発時依存（`dev` extra）: `pytest==9.1.1`
- `requires-python = ">=3.12"`（互換性の下限。開発機と CI は 3.14 で検証する）

`requirements.txt` は作成しない（依存の正本を1ファイルに集約し、ドリフトを避ける）。

## 2. セットアップ（初回のみ）

```bash
cd <repo>
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

- システムPythonには何もインストールしない（`.venv` を使用）。
- `.venv/`・`*.egg-info/`・`.pytest_cache/` は `.gitignore` 済み。
- editable install により `python -m validation.<module>` と `import validation` が
  リポジトリルートから動作する。

## 3. テスト

```bash
.venv/bin/python -m pytest
```

- Contract Tests: `tests/validation/`（2026-10-13 時点: **363件**）。
- 新しいスキーマを登録したら、対応する Contract Test を必ず追加する
  （20261013h.md §9 / §16）。`tests/validation/test_schema_coverage.py` が
  「登録済みスキーマIDを参照するテストファイルの存在」を機械的に検査するため、
  テスト不在の登録は pytest 失敗として検出される。
- スキーマ一覧と契約バージョンは §10 を参照。

## 4. ライブラリとしての利用

```python
from validation.core import validate_document
from validation.pipeline import validate_full
from validation.schema_registry import get_schema

# 構造検証のみ
result = validate_document(document, get_schema("collection-run-v1"))

# 構造 + 意味検証 + レポート（層順序: 構造失敗時は意味検証を実行しない）
outcome = validate_full(
    document, schema_id="collection-run-v1", target="run_metadata.json"
)
report = outcome.to_report().to_dict()
```

モジュール構成:

| module | 役割 |
|---|---|
| `core.py` | Cerberus 共通インターフェース（`cerberus` を import してよい唯一の場所） |
| `schema_registry.py` | スキーマID → スキーマ文書 + 契約バージョン（15件） |
| `semantic.py` | 意味検証: 日時、execution 整合、Registry 参照、Capability Gate、秘密情報スキャン |
| `integrity.py` | SHA-256 / byte_length / ファイル存在 / Lineage（読取専用） |
| `comparability.py` | L2 / G3 / G7 比較可能性ゲート |
| `storage_policy.py` | Git 追跡検証（read-only git）/ Publication Gate / policy 選択 |
| `pipeline.py` | 層順序つき統合実行（構造→意味→Artifact） |
| `reporting.py` | Issue 正規化と JSON Validation Report（安定形式） |
| `gates.py` | 収集前/後ゲート（Phase 6） |
| `legacy.py` | Legacy Audit Profile・凍結 run_id リスト（Phase 8） |
| `cli.py` | CLI（下記 §5） |

- `cerberus` を import してよいのは `src/validation/core.py` のみ（維持）。
- 共通設定: `allow_unknown=False` / `purge_unknown=False` / `normalize=False`。
  検証は入力ドキュメントを変更しない（raw不変原則）。
- スキーマ側で意図的に許可した拡張領域のみ `allow_unknown=True`
  （`environment`、`temporal_provenance.submitted_parameters`、`transformation.parameters`）。

## 5. CLI（Phase 5 実装済み）

```bash
# 単一ファイル（構造 + 意味検証。Registry があれば参照検証も実行）
.venv/bin/python -m validation.cli validate \
  --schema collection-run-v1 \
  --file datasets/<study>/.../run_metadata.json \
  [--format text|json] [--output report.json] [--profile strict|legacy] \
  [--verify-artifacts] [--config-dir config --metadata-dir metadata]

# Study 単位（配下の run_metadata.json を再帰検証、Artifact manifest も検証）
.venv/bin/python -m validation.cli validate-study --study cbx-search-trends

# 存在する Registry ファイルのみ検証（未実装の間は「対象なし」で exit 0）
.venv/bin/python -m validation.cli validate-registries

# 全 Study + Registry の統合レポート（CI 向け）
.venv/bin/python -m validation.cli validate-all --format json --output validation-report.json

# 収集前ゲート（Phase 6 P6-1）: proceed / stop
.venv/bin/python -m validation.cli gate-plan --file plan.json

# G5 Legacy 監査（非破壊。--output 省略時は stdout）
.venv/bin/python -m validation.cli audit-legacy --output docs/audits/g5-legacy-runs.json
```

- Exit Code: 0=成功 / 1=データ検証失敗 / 2=スキーマ・設定エラー /
  3=ファイルI/Oエラー（20261013h.md §13）。
  1回の実行で複数種が発生した場合の優先順位は **2 > 3 > 1 > 0**。
- 出力先: 機械可読 JSON は stdout（`--format json`）または `--output`。
  人間向けメッセージは stderr。
- `--profile legacy` は凍結済み legacy run_id にのみ許可（§12）。新規 run へ
  適用しようとすると exit 2（bypass 防止、P8-3）。
- JSON Validation Report 形式（安定形式）:
  `{validation_version, schema_id, target, profile, valid, issues[]}`。
  issue は `{code, path, severity, message, rule, schema_version}`。
  legacy は `run_id / status / missing_fields` を追加。validate-study / validate-all /
  validate-registries は `reports[]` のバンドル形式。
- 既存の bash 検証（`scripts/validation/validate-*.sh`）は置き換えない。
- 収集フローからの利用は `scripts/validation/run-gates.sh {registries|plan|run}`
  経由（P6-5。検証処理の分散禁止: h.md §6）。

## 6. CI（Phase 7 実装済み — GitHub 実行は未検証）

`.github/workflows/research-validation.yml` を新設した。

- トリガ: `pull_request` / `push (main)`。
- 環境: Python **3.14**、`python -m pip install -e ".[dev]"`（`pyproject.toml` が
  依存の正本。`requirements.txt` は作らない）。CI では `.venv` を作らない。
- 手順: `python -m pytest` → `python -m validation.cli validate-registries`。
- 非公開 raw を CI へアップロードしない（workflow は raw を読み書きしない）。
- JSON Schema × Cerberus 差分検出（h.md §17 / P7-3）は、JSON Schema 正本が
  存在しないため**未実装**（方針は §11）。
- ローカルで実施した検証: YAML 構文パース（ruby yaml）・`bash -n`。
  **GitHub Actions 上での実行は未検証（push 後に確認が必要）**。
- **決定（2026-10-13）**: CI の Python は **3.14**（開発機と同一）。ローカルと CI の
  環境差を減らすことを優先する。`requires-python` の下限 3.12 は互換性表示として維持する。
- リリースアーカイブ（P7-4）: 検証フレームワークの再現に必要な `pyproject.toml` と
  `tests/` を INCLUDE_PATHS に追加し、`__pycache__` / `*.egg-info` / `.pytest_cache`
  を除外する（`scripts/release/create-clean-archive.sh` と `release-zenodo.yml` に反映済み）。

## 7. 責務分離（重要）

Cerberus は**構造検証のみ**を担当する。

| 検証対象 | 担当 |
|---|---|
| 必須項目・型・値域・列挙値・ネスト・余分なフィールド | Cerberus（本フレームワーク） |
| Compound / Query / Source / Collector の Registry 存在 | Registry Validator（実装済み: `semantic.check_registry_references`） |
| 日時・期間境界の前後関係 | Temporal / Semantic Validator（実装済み: `semantic.check_temporal_semantics`） |
| Query と Source の整合性・Capability | Semantic Validator（実装済み: `semantic.check_capability_gate`） |
| ファイルハッシュ | Integrity Validator（実装済み: `integrity`） |
| Artifact 参照関係 | Lineage Validator（実装済み: `integrity.check_*_lineage`） |
| Git 追跡状態 | Git Policy Validator（実装済み: `storage_policy.check_git_tracking`、read-only） |
| 公開承認・研究上の比較可能性 | Publication / Comparability Gate（実装済み: `storage_policy.check_publication` / `comparability`） |

- Cerberus は JSON Schema Draft 2020-12 の実装ではない。既存の JSON Schema を
  そのまま Cerberus へ渡してはならない。
- Cerberus で検証できない内容を「検証済み」として報告しない。

## 8. 既存環境の監査要約（Phase 1）

| 項目 | 結果 |
|---|---|
| Python | 3.14.6（Homebrew）/ pip 26.1.2 |
| 依存管理ファイル | 導入前は存在しなかった（本 `pyproject.toml` が最初） |
| 既存 Python コード | 全17ファイルが標準ライブラリのみ |
| 既存検証資産 | `scripts/validation/*.sh`（3本）+ `validate-research-pages.py`（stdlib） |
| pytest | 導入前は未導入・`tests/` なし |
| JSON Schema Draft 2020-12 | 存在しない |
| GitHub Actions | `release-zenodo.yml` のみ（PR/push 検証なし） |

## 9. スキーマ更新ルール

1. `schema_version` を更新し、変更内容を記録する。
2. 既存 Fixture で回帰テストを実行する。
3. 互換性への影響を評価し、必要なら Migration Plan を作成する。
4. Registry に新スキーマを登録した場合は Contract Test を追加する
   （`test_schema_coverage.py` が機械的に強制する）。
5. 既存 raw・旧 metadata・Git 履歴を変更しない。
6. 契約バージョンは `schema_registry.SCHEMA_VERSIONS` と文書の
   `schema_version` の両方を更新する（CV-20: 不一致は検出される）。

## 10. スキーマ一覧（15件、契約バージョンはいずれも 1.0.0）

| Schema ID | 契約 | 主な内容 |
|---|---|---|
| `collection-run-v1` | G5 | run_metadata（finalized） |
| `collection-run-v1-running` | G5 | 実行中 profile。`status=running` のみ許容、`collection_finished_at` は未知フィールド扱い（復帰ラベルによる回避を検出） |
| `source-registry-v1` | G1 | `config/sources.json` |
| `collector-registry-v1` | G1 | `config/collectors.json`（capability 三値・status 五値） |
| `query-registry-v1` | G2 | `metadata/queries/query-registry.json` |
| `query-variants-v1` | G2 | 表記ゆれブロック |
| `temporal-window-v1` | G3 | 単独 window 文書 |
| `artifact-manifest-v1` | G4 | Artifact manifest（sha256 は 64桁小文字 hex） |
| `transformation-v1` | G5 | 変換来歴（input/output 参照は非空） |
| `storage-policy-registry-v1` | G6 | `config/storage-policies.json` |
| `publication-decision-v1` | G6 | 公開判断記録 |
| `study-registry-v1` | G7 | `metadata/studies/study-registry.json` |
| `measurement-registry-v1` | G7 | `metadata/measurements/measurement-registry.json` |
| `research-view-v1` | G7 | 研究 view 定義（合算モード禁止） |
| `collection-plan-v1` | P6 | 収集前ゲート入力（初期契約。G1 Adapter Contract 確定時に整合を取る） |

各スキーマの未包含事項（意味検証側の担当）は各モジュールの docstring に明記してある。

## 11. JSON Schema 共存（P3-10）— 決定: Cerberus を構造検証の正本とする

Phase 1 監査のとおり、リポジトリには**実在する JSON Schema ファイルがない**
（`project.json` の `$schema` は dangling 参照）。そのため h.md §17 の
「両 Validator 実行・差分で CI 失敗」は対象が存在せず、本項目は
**該当なし（no-op）として終結**する。

**決定（2026-10-13）**:

1. 実行時の構造検証の正本は **Cerberus スキーマ（`src/validation/schemas/`）** とする。
2. 各仕様書（G3/G5 等）内の JSON Schema 例は**仕様記述**として扱い、実行時の
   検証器としては実装しない。
3. 将来 `schemas/*.schema.json` を公開契約として導入する場合は、次のいずれかを
   **同時に**導入する。片方だけの導入は禁止（手動二重管理はドリフトの原因）。
   - 単一の正本（JSON Schema）から Cerberus スキーマを生成する、または
   - 同一 fixture を両 Validator へ通す二重実行テストを追加する。
4. 導入時には `jsonschema` の依存追加が必要（現時点の依存は `cerberus` のみ）。
   CI の差分ゲートも導入と同時に有効化する（`research-validation.yml` の
   ヘッダコメントを参照）。

## 12. Legacy Audit（Phase 8 実装済み）

- 対象: `datasets/**/run_metadata.json` 全 24 件（G5 契約以前の形式）。
- 凍結リスト: `src/validation/legacy.py` の `LEGACY_RUN_IDS`（24件）。監査結果
  `docs/audits/g5-legacy-runs.json` と一致することをテストで強制する。
- 実行: `.venv/bin/python -m validation.cli audit-legacy`（非破壊・読取専用）。
  各ファイルの sha256 を監査前後で比較し、`unchanged: true` を記録する。
- `--profile legacy` は凍結リストの run_id にのみ許可（新規 run の回避を拒否）。
- 命名対応表（旧 → 新）:

| 旧フィールド | 新フィールド |
|---|---|
| `source` | `source_id` |
| `collection_timestamp` | `collection_started_at` |
| `queries` | `query_provenance` |
| `mcp_server` / `mcp_version` | `collector.collector_id` / `collector.version` |
| （なし） | `schema_version` / `purpose` / `temporal_provenance` / `execution` |

- 監査上の注意: ディレクトリ名と `run_id` が一致しない run が 3 件存在する
  （例: `.../20261008T164651Z-google-trends-common-scale-missing/` の run_id は
  `common-scale-missing-20261009`）。監査は run_id を正とする。
- 限界: 不足項目は報告のみで推定補完しない。`status` は
  `complete` / `incomplete` / `unreadable` のみを記録する。

## 13. 収集パイプライン統合（Phase 6）— 一部実装

- 実装済み: `validation/gates.py` の `pre_collection_gate` / `post_collection_gate`
  と CLI `gate-plan`、ラッパー `scripts/validation/run-gates.sh`。
- 未実装: `src/collection/*`（apify_run.sh 等）への配線と Quarantine 領域の運用
  （アクセス制御・保持ポリシー）。コレクタ本体は別開発ラインのため、無断で
  書き換えない方針とした。
- 暫定運用: 収集実行時は `run-gates.sh run <run_metadata.json>` の exit 0 を
  確認してから採用し、非 0 の場合は既存 raw をそのまま保持して隔離扱いとする。

## 14. ローカル検証の再現手順

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m validation.cli validate-registries
.venv/bin/python -m validation.cli audit-legacy --output docs/audits/g5-legacy-runs.json
```

- 実データへの end-to-end: `validate --profile legacy`（監査）と
  strict（不合格 exit 1）を既存 run_metadata で確認済み（2026-10-13）。
- CI ワークフローは YAML 構文検証のみ実施。GitHub 上での実行は未検証。
