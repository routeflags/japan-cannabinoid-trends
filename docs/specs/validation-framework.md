# Validation Framework (Cerberus) — セットアップと運用

研究データ契約（G1〜G7）の構造検証フレームワーク。
仕様書: `docs/plans/20261013h.md`（ローカル計画書。`docs/plans/` はgitignore対象のため
リポジトリ履歴には含まれない）。

## 現状（2026-10-13 更新）

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | 既存環境監査 | 完了（監査結果は下記 §8） |
| Phase 2 | 依存導入・共通Validator・G5スキーマ・Contract Tests | 実装済み（コミット 654b5b9） |
| Phase 3 | Schema Registry 拡充（G1〜G7・running profile・バージョン管理） | **実装済み**（18 スキーマ登録。P3-10 は対象不存在のため §11 の決定により終結） |
| Phase 4 | Semantic / Integrity / Lineage / Git Policy / Comparability / Publication / Secret Scan | **実装済み** |
| Phase 5 | CLI・JSON Validation Report・Exit Code | **実装済み** |
| Phase 6 | 収集パイプライン統合 | **G1 垂直スライス実装済み**（registries / capability gate / adapter contract / L1 + quarantine / L2。ライブ収集は未実施、既存 shell・skill への適用は親判断待ち — §13）。**G3 垂直スライス実装済み**（Temporal Contract / Window Compiler / Coverage / Temporal Comparability / 旧 run 監査 — §16）。**G4 垂直スライス実装済み**（Artifact Registry / Reader Contract / Storage Integrity / Storage Inventory / Data Catalog — §17）。**G5 垂直スライス実装済み**（Provenance Contract / Evidence Registry / Audit Trail。重複整理・完全性評価・P01/P17・旧 run 監査 — §18） |
| Phase 7 | CI | 実装済み（`research-validation.yml` 新設。初回実行成功: 2026-10-13 push `324cd55`） |
| Phase 8 | Legacy Audit | 実装済み（29件を非破壊監査。`docs/audits/g5-legacy-runs.json`、raw sha256 前後一致） |
| G7 垂直スライス | Study Registry / Research Catalog / Comparability Gate / Research View | **実装済み（2-study: `cbx-search-trends` + `cannabinoid-multi-trends`）**（Study/Measurement Registry 新設＋CI 検証11件。Catalog は派生索引（P2）。Gate は CS01-CS13、`comparable` は完全証拠時のみで実データ上限は `conditional`。View は `parallel_timeseries` 派生（合算なし）。9 study 非破壊監査は `docs/audits/g7-study-inventory.*`、raw sha256 前後一致） |

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

- Contract Tests: `tests/validation/`（609件）+ `tests/collection/`（77件）
  + `tests/storage/`（57件）+ `tests/research/`（46件）＝ **789件**（2026-10-13 G7 垂直スライス後。
  `.venv/bin/python -m pytest` で実測（Python 3.14＋editable install）。G6 直後は 743 件）。
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
| `schema_registry.py` | スキーマID → スキーマ文書 + 契約バージョン（18件） |
| `semantic.py` | 意味検証: 日時、execution 整合、Registry 参照、Registry 版追跡（G5 P17。warning/info のみ）、Capability Gate、秘密情報スキャン |
| `integrity.py` | SHA-256 / byte_length / ファイル存在 / Lineage（読取専用） |
| `storage_contract.py` | G4: manifest の内容契約（S1/S6-S12）・reader 解決・ページング整合・SQLite lineage・registry 内部整合 |
| `comparability.py` | L2 / G3 / G7 比較可能性ゲート |
| `windows.py` | G3 Temporal Contract プリミティブ（半開区間変換・相対期間の名目解決・バケット生成・CompiledWindow・window レジストリ整合） |
| `coverage.py` | G3 Coverage Validation（§9 manifest・§11 欠測状態・§15 旧 run 時系列棚卸し） |
| `storage_policy.py` | Git 追跡検証（read-only git）/ Publication Gate / policy 選択 |
| `pipeline.py` | 層順序つき統合実行（構造→意味→Artifact） |
| `reporting.py` | Issue 正規化と JSON Validation Report（安定形式） |
| `gates.py` | 収集前/後ゲート（Phase 6。後ゲート = L1: 欠測/完全性/artifact 検証込み） |
| `legacy.py` | Legacy Audit Profile・凍結 run_id リスト（Phase 8） |
| `provenance.py` | G5 来歴評価: Completeness / Confidence / Integrity / Readiness（読取専用。`inferred` 自動付与なし）・Evidence Registry 検査・run_id 一意性・`audit-provenance` 集計 |
| `cli.py` | CLI（下記 §5） |
| `research/catalog.py` | G7: 派生 Research Catalog（発見索引。Manifest/Registry から再生成、決定的。P2/P4） |
| `research/comparability.py` | G7: CS01-CS13 横断ゲート（測定/時間サブセットは `validation.comparability` に委譲。`comparable` は完全証拠時のみ） |
| `research/views.py` | G7: Research View 生成（`parallel_timeseries` のみ。合算なし。P6/P8） |
| `research/dedup.py` | G7: 重複使用の派生追跡（raw 不変。§12） |
| `research/policy.py` | G7: Internal/Public Catalog 分離（宣言のみ。公開しない。§15） |
| `research/audit.py` | G7: 既存 Study 非破壊監査（§16。raw sha256 前後一致） |
| `research/cli.py` | G7: `catalog-find` / `compare` / `build-view` / `audit-studies` |

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

# Registry ファイルの検証（config/sources.json・config/collectors.json が実在）
.venv/bin/python -m validation.cli validate-registries

# 全 Study + Registry の統合レポート（CI 向け）
.venv/bin/python -m validation.cli validate-all --format json --output validation-report.json

# 収集前ゲート（Phase 6 P6-1）: proceed / stop
.venv/bin/python -m validation.cli gate-plan --file plan.json

# 収集後 L1 ゲート（Phase 6 P6-2）: catalog / quarantine
.venv/bin/python -m validation.cli gate-run --file datasets/<study>/.../run_metadata.json

# L2 比較可能性（G1 §12、C1-C3。`--coverage-a`/`--coverage-b` で G3 T6/T7 も）: 常に exit 0、判定はレポートで
.venv/bin/python -m validation.cli compare-runs --a a.json --b b.json

# G3 §9 Coverage manifest（読み取り専用レポート。常に exit 0）
.venv/bin/python -m validation.cli coverage-run --file <run_dir or run_metadata.json>

# G3 §15 旧 run 時系列棚卸し（非破壊。sha256 前後比較。既定出力は docs/audits/）
.venv/bin/python -m validation.cli audit-temporal --output docs/audits/g3-temporal-inventory.json

# G5 Legacy 監査（非破壊。--output 省略時は stdout）
.venv/bin/python -m validation.cli audit-legacy --output docs/audits/g5-legacy-runs.json

# G2 Stage-1 分類: exit 0 = 登録済み active クエリとして採用可 / 1 = 採用不可
.venv/bin/python -m validation.cli classify-query --text "Durban CBD"

# G2 クエリ定義の比較可能性（Q1-Q5 部分。判定は常に exit 0、未登録 ID は 2）
.venv/bin/python -m validation.cli compare-queries --a cbd-general-ja --b cbd-liquid-ja

# G2 旧 run クエリ棚卸し（非破壊。b.md §13 の 5 状態。既定出力は docs/audits/）
.venv/bin/python -m validation.cli audit-queries --output docs/audits/g2-query-inventory.json
```

- Exit Code: 0=成功 / 1=データ検証失敗 / 2=スキーマ・設定エラー /
  3=ファイルI/Oエラー（20261013h.md §13）。
  1回の実行で複数種が発生した場合の優先順位は **2 > 3 > 1 > 0**。
- G2 追加コマンド: `classify-query` は 0=登録済み active クエリとして採用可 /
  1=採用不可（irrelevant・ambiguous・unknown・非 active）/ 2=設定エラー。
  `compare-queries` は「判定であってデータ不採用ではない」ため常に 0
  （未登録 query_id は 2）。`audit-queries` は非破壊（読取専用、sha256 前後比較）。
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
  経由（P6-5。検証処理の分散禁止: h.md §6）。`run` は `gate-run`（L1）を呼ぶ。
- G1 収集コア（registry → adapter → staging → L1 → catalog/quarantine）は
  `python -m collection.core.cli {collect|adopt}`。詳細は
  `docs/specs/collection-pipeline.md`。
- G3 Window Compiler のドライランは `python -m collection.core.cli compile-window`
  （exit 0 = 表現可能 / 1 = 拒否 / 2 = 設定エラー）。`collect` に
  `--now <ISO 8601>`（基準時刻の固定。決定論的リプレイ用）を追加した（§16）。

```bash
# G4 §16 旧成果物の非破壊棚卸し（sha256 前後比較。既定出力は docs/audits/）
.venv/bin/python -m validation.cli audit-artifacts \
  --output docs/audits/g4-storage-inventory.json

# G4 storage CLI（reader / 内容判定 / catalog。いずれも read-only）
.venv/bin/python -m storage.cli read --path <artifact> [--mode points] [--limit 10]
.venv/bin/python -m storage.cli inspect --path <artifact>
.venv/bin/python -m storage.cli catalog --datasets-root datasets [--check-lineage]
```

```bash
# G5 §9/§10 来歴の完全性評価と旧 run 監査（非破壊。sha256 前後比較。既定出力は docs/audits/）
.venv/bin/python -m validation.cli audit-provenance \
  --output docs/audits/g5-provenance-assessment.json
```

- G5 追加検査: `validate-study` は strict run 横断で `run_id` 重複を
  `RUN_ID_DUPLICATE`（error）として検出する（P01。legacy profile は対象外）。
  `validate_full` は `query_registry_version` の追跡可能性を報告する
  （P17。一致=沈黙、不一致=info、欠落=warning の判定不能。既存 strict 合格を
  FAIL に変えない）。`validate-registries` は Evidence Registry
  （`metadata/provenance/evidence-registry.json`）を構造＋参照存在＋hash＋
  secret scan で検証する（§18）。

## 6. CI（Phase 7 実装済み — 初回実行成功）

`.github/workflows/research-validation.yml` を新設した。

- トリガ: `pull_request` / `push (main)`。
- 環境: Python **3.14**、`python -m pip install -e ".[dev]"`（`pyproject.toml` が
  依存の正本。`requirements.txt` は作らない）。CI では `.venv` を作らない。
- 手順: `python -m pytest` → `python -m validation.cli validate-registries`。
- 非公開 raw を CI へアップロードしない（workflow は raw を読み書きしない）。
- JSON Schema × Cerberus 差分検出（h.md §17 / P7-3）は、JSON Schema 正本が
  存在しないため**未実装**（方針は §11）。
- ローカルで実施した検証: YAML 構文パース（ruby yaml）・`bash -n`。
- **初回実行（2026-10-13、push `324cd55`）: 全ステップ成功**
  （Checkout → Python 3.14 → `pip install -e ".[dev]"` → pytest → validate-registries）。
  https://github.com/routeflags/japan-cannabinoid-trends/actions/runs/38293484480
- **G1 垂直スライス後（push `0c36ce0`）も全ステップ成功**（461 tests、`config/`
  レジストリ2件の実検証を含む）。
  https://github.com/routeflags/japan-cannabinoid-trends/actions/runs/38298367946
- CI は `validate-all` を実行しない。既存の legacy run が strict 不適合で
  全件失敗するため、現時点のゲートは Contract Tests と Registry 検証である。
  legacy の扱い（凍結リストの更新要否）は §12 を参照。
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
| G2 Query Registry の内部整合（重複 ID・重複文字列・taxonomy 参照・variant 束） | Query Semantics（実装済み: `query_semantics.check_query_registry` / `check_query_variants`。`validate-registries` が実行） |
| Query 文字列の Stage-1 分類・定義比較可能性（Q1-Q5 部分） | Query Semantics（実装済み: `classify_query_text` / `compare_query_definitions`。Stage 2/3・compiler は未実装 → §15） |
| 日時・期間境界の前後関係 | Temporal / Semantic Validator（実装済み: `semantic.check_temporal_semantics`） |
| 絶対 window の正本性・相対期間の変換（G3 Window Compiler） | `validation.windows` + collector 別 compiler（実装済み: `collection.adapters.google_trends.compiler`。GT 1 ソース） |
| 要求期間と観測期間の分離・coverage 評価（G3 §9/§11） | `validation.coverage`（実装済み: `coverage-run` / 監査）。欠測と観測ゼロを区別する |
| Query と Source の整合性・Capability | Semantic Validator（実装済み: `semantic.check_capability_gate`） |
| 欠測とゼロの区別・終端 run の raw 証拠（L1-09） | Semantic Validator（実装済み: `semantic.check_missingness_consistency`。`post_collection_gate` 経由） |
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

## 10. スキーマ一覧（18件、契約バージョンはいずれも 1.0.0）

| Schema ID | 契約 | 主な内容 |
|---|---|---|
| `collection-run-v1` | G5 | run_metadata（finalized） |
| `collection-run-v1-running` | G5 | 実行中 profile。`status=running` のみ許容、`collection_finished_at` は未知フィールド扱い（復帰ラベルによる回避を検出） |
| `source-registry-v1` | G1 | `config/sources.json` |
| `collector-registry-v1` | G1 | `config/collectors.json`（capability 三値・status 五値） |
| `query-registry-v1` | G2 | `metadata/queries/query-registry.json` |
| `query-variants-v1` | G2 | 表記ゆれブロック |
| `query-variants-registry-v1` | G2 | `metadata/queries/query-variants.json`（variant 束。ブロック形状は `query-variants-v1` を再利用） |
| `temporal-window-v1` | G3 | 単独 window 文書 |
| `artifact-manifest-v1` | G4 | Artifact manifest（sha256 は 64桁小文字 hex。G4 垂直スライスで `contains_full_timeseries` / `page_index` / `artifact_group_id` / `database` / `artifact_groups` を任意追加 — §17） |
| `artifact-registry-v1` | G4 | `metadata/artifacts/artifact-registry.json`（readers / artifact_schemas の対応表 — §17） |
| `transformation-v1` | G5 | 変換来歴（input/output 参照は非空） |
| `evidence-registry-v1` | G5 | `metadata/provenance/evidence-registry.json`（証拠 ID / 種別 / 参照 / 任意 sha256 / 観測時刻 — §18） |
| `storage-policy-registry-v1` | G6 | `config/storage-policies.json` |
| `publication-decision-v1` | G6 | 公開判断記録 |
| `study-registry-v1` | G7 | `metadata/studies/study-registry.json` |
| `measurement-registry-v1` | G7 | `metadata/measurements/measurement-registry.json` |
| `research-view-v1` | G7 | 研究 view 定義（合算モード禁止） |
| `collection-plan-v1` | P6 | 収集前ゲート入力（初期契約。G1 垂直スライスで adapter 向けの任意フィールド `query` / `window.granularity|week_start|timezone|window_id` を追加 — §13。G3 で `window.exact_required` を追加 — §16） |

G5 `collection-run-v1` には G3 で `temporal_provenance.reference_time` /
`temporal_provenance.limitations` を**任意フィールド**として追加した（後方互換。
contract version は 1.0.0 のまま — G2 の plan 拡張と同じ手順）。

各スキーマの未包含事項（意味検証側の担当）は各モジュールの docstring に明記してある。

### 10.1 レジストリファイルの実在状況（2026-10-13）

| 想定位置 | スキーマ | 実在 |
|---|---|---|
| `config/sources.json` | source-registry-v1 | **あり**（6 source。`validate-registries` と CI が実検証する） |
| `config/collectors.json` | collector-registry-v1 | **あり**（6 collector。active は `google-trends-mcp` のみ） |
| `metadata/queries/query-registry.json` | query-registry-v1 | **あり**（G2 垂直スライス: 17 queries。`validate-registries` と CI が実検証する） |
| `metadata/queries/query-variants.json` | query-variants-registry-v1 | **あり**（3 variant sets） |
| `metadata/windows/*.json` | temporal-window-v1 | **あり**（G3 垂直スライス: 2 windows。`validate-registries` と CI が実検証する） |
| `metadata/artifacts/artifact-registry.json` | artifact-registry-v1 | **あり**（G4 垂直スライス: 7 readers / 10 artifact schemas。`validate-registries` と CI が実検証する） |
| `metadata/provenance/evidence-registry.json` | evidence-registry-v1 | **あり**（G5 垂直スライス: 8 証拠。`validate-registries` と CI が実検証する — §18） |
| `metadata/studies/study-registry.json` | study-registry-v1 | なし（G7 の作業） |
| `metadata/measurements/measurement-registry.json` | measurement-registry-v1 | なし（G7 の作業） |
| `config/storage-policies.json` | storage-policy-registry-v1 | なし（G6 の作業） |

`validate-registries` は存在するファイルのみを検証する（現在 **8 ターゲット**）。
上記 G6/G7 のファイルが置かれれば、CI が自動的に検証対象に含める。G2 の 2 ファイルは検証
対象に含まれ、taxonomy（`metadata/taxonomy/compound-taxonomy.skos.jsonld`）が
存在する場合は compound 参照の意味検証も実行される（無い場合は該当チェック
のみ無効になる）。G3 の `metadata/windows/*.json` も検証対象に含まれ、
`temporal-window-v1` + 時系列意味検証に加えて、重複 `window_id` と
ファイル名不一致（`WINDOW_ID_DUPLICATE` / `WINDOW_FILE_STEM_MISMATCH`）を
機械的に検出する（ファイル名 = window_id は§16 の規則）。G4 の
artifact registry は `artifact-registry-v1` + 内部整合（重複 ID・未登録 reader
参照・active だが実装なしの reader・format 被覆）を検証する（§17）。

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

- 対象: `datasets/**/run_metadata.json` 全 29 件（G5 契約以前の形式。24→29 の経緯は §12.1）。
- 凍結リスト: `src/validation/legacy.py` の `LEGACY_RUN_IDS`（29件）。監査結果
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

### 12.1 凍結リストとファイル実体の整合（2026-10-13 決定・解消済み）

- `origin/main` の取り込みで、フレームワーク導入前（2026-10-12 収集）の run が
  **5 件** 追加され、ファイル実体は **29 件**となった。
- **決定（2026-10-13）**: 5 件を凍結リストへ**追加**した。いずれも 2026-10-12 収集
  （導入前）で `schema_version` を持たず、「legacy」の定義に合致する。
  監査を再生成済み（`docs/audits/g5-legacy-runs.json`、29件、`raw_modified: false`）。
- 現在の挙動:
  - strict: `validate-all` は 29 件を対象とし、全件不適合で exit 1。
  - legacy: `validate-all --profile legacy` は凍結リストの 29 件を対象とし exit 0。
- **bypass 防止の不変条件（`tests/validation/test_legacy.py` で強制）**:
  1. 凍結された run_id は実在し、`schema_version` を持たない（導入前であること）。
  2. 凍結されていない run は現行契約の必須項目を満たす。
     どちらでもない run が現れた場合、テストが失敗し、人が「修正」か「監査付きの凍結」
     を判断する。
  3. 監査成果物は凍結リストを包含する（スナップショットなので完全一致は要求しない）。
- フレームワーク導入後の新規収集 run を凍結リストへ追加してはならない
  （bypass 防止の意味が失われる）。追加時は収集日が導入前であることを確認する。

## 13. 収集パイプライン統合（Phase 6）— G1 垂直スライス実装済み

2026-10-13、G1 を 1 ソース（Google Trends）で貫通させた。
詳細な運用契約は **`docs/specs/collection-pipeline.md`** を参照。

- **実装済み**:
  - Source / Collector Registry の実体（`config/sources.json` /
    `config/collectors.json`）と CLI 検証（`validate-registries`、CI）。
  - Capability / Selection Gate（`collection.core.selection`。未登録・非
    active・unknown capability は fail closed。複数候補の自動選択はしない）。
  - Adapter Contract（`src/collection/core/contracts.py`）と Google Trends
    adapter（`src/collection/adapters/google_trends/`。live と recorded
    replay を transport で分離）。**ライブ収集は未実施**。
  - L1 ゲート（`gate-run`）と Quarantine 移動（`collection.core.pipeline`。
    上書き禁止・自動削除なし・secret 検出時 chmod 700）。
  - L2 最小実装（`compare-runs`、C1-C3。`comparability.compare_runs`）。
  - `collection-plan-v1` への adapter 向け任意フィールド追加（後方互換。
    既存 plan 文書の判定は不変 — `test_collection_plan.py`）。
- **未実施（親・ユーザーの判断事項）**:
  - ライブ収集（課金・レート制限・資格情報）の実行と実レスポンスでの契約照合。
  - 既存 shell（`apify_run.sh` 等）・skill（`research-google-trends` 等）の
    G1 フローへの移行（移行パスは `collection.core.cli adopt`）。
  - Quarantine の正式な運用（保持期間・アクセス制御・レビュー手順）。
    暫定規約は `docs/specs/collection-pipeline.md` §6。
- 暫定運用: 収集実行時は `run-gates.sh run <run_metadata.json>`（= `gate-run`）の
  exit 0 を確認してから採用し、非 0 の場合は既存 raw をそのまま保持して隔離扱いとする。

## 14. ローカル検証の再現手順

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m validation.cli validate-registries
.venv/bin/python -m validation.cli audit-legacy --output docs/audits/g5-legacy-runs.json
.venv/bin/python -m validation.cli audit-queries --output docs/audits/g2-query-inventory.json
.venv/bin/python -m validation.cli audit-temporal --output docs/audits/g3-temporal-inventory.json
.venv/bin/python -m validation.cli audit-artifacts --output docs/audits/g4-storage-inventory.json
```

- 実データへの end-to-end: `validate --profile legacy`（監査）と
  strict（不合格 exit 1）を既存 run_metadata で確認済み（2026-10-13）。
- G3 の再現（offline）: `compile-window`（§16）→ `collect --now ...`（固定基準）
  → `gate-run` → `coverage-run`。ライブ収集は実行しない（§13）。
- G1 収集フローの再現（offline）: `python -m collection.core.cli collect --plan
  <plan> --fixture tests/collection/fixtures/google_trends/... --workspace <root>`
  → `python -m validation.cli compare-runs --a ... --b ...`。ライブ収集は
  実行しない（§13）。
- G4 の再現（offline）: 上記 replay で生成した run に
  `validation.cli gate-run --file <run>/run_metadata.json`（L1 + storage
  contract）と `storage.cli catalog --datasets-root <root>/datasets
  --check-lineage` を実行する。改ざん検出は payload を変更したコピーに対して
  `ARTIFACT_HASH_MISMATCH` / exit 1 を確認する（§17）。
- CI ワークフローは初回実行に成功している（§6）。

## 15. G2 垂直スライス（Query Registry / 表記ゆれ / 意味検証）— 2026-10-13

G2 仕様（`docs/plans/20261013b.md`）の垂直スライス。当初の登録範囲は「taxonomy に概念が
あり、run 実績または keywords.yaml に実在する」CBX / CBD の 7 クエリだった。
**2026-10-13 追記**: taxonomy の欠落を解消（`docs/provenance/compound-taxonomy.md`）した
ため、同じ基準で HHC / HHCH / THCH / THC-O / CRDP の **10 クエリ**を追加し、**計 17 クエリ**
（6 化合物）となった。証拠台帳: `docs/provenance/query-inventory.md`。**ライブ収集・
新しい外部依存の追加は行っていない。**

- **実装済み**:
  - `metadata/queries/query-registry.json`（17 queries）/
    `metadata/queries/query-variants.json`（3 variant sets）。
    `compound_id` は taxonomy の notation（`compound_cbx` 等）。
  - 新スキーマ `query-variants-registry-v1`（variant 束ファイル。ブロック形状は
    `query-variants-v1` を後方互換のため変更せず再利用）。
  - `validation.query_semantics`: `check_query_registry` / `check_query_variants`
    （重複 ID・重複文字列・taxonomy 参照・primary 一致等を `validate-registries`
    に配線 = CI で実行）、`classify_query_text`（Stage 1。除外フレーズは
    rationale / evidence 付きの明示表）、`compare_query_definitions`
    （Q1-Q5 部分。**comparable は返さず**、L2 C1 と矛盾しないことをテストで固定）。
  - CLI: `classify-query`（0=採用可 / 1=採用不可 / 2=設定エラー）/`compare-queries`
    /`audit-queries`。
  - run provenance: registry 読込時は `query_provenance.query_registry_version` を
    記録（b.md §7）。未登録 query_id は error、deprecated は info（既存
    `semantic.check_registry_references` をそのまま使用）。
  - 旧 run 棚卸し（b.md §13）: `docs/audits/g2-query-inventory.json`。
    29 run / 75 文字列を exact_match=22 / variant_match=1 / ambiguous=36 /
    unmapped=16 / semantic_match_candidate=0 に分類し、`raw_modified: false`
    （sha256 前後比較）。テストが再計算一致を強制する。
- **決定（J1 は要確認）**:
  - 既存 29 run の旧形式 `queries` は registry 照合の対象にしない（形状分離＋
    監査ファイルで対応関係を管理）。新規 run の `query_provenance` は fail closed。
    この決定は可逆で、旧形式を fail closed の対象にする場合は凍結リスト運用
    （legacy.py）側の再設計が必要になるため、採用していない。
  - 除外方式は「正規化（NFKC + casefold）＋明示フレーズ表」（正規表現なし。
    根拠: docs/collection-gap-analysis.md 原因 G2 行 + b.md §8）。
  - THC-O / THCH / CRDP / HHC / HHCH は taxonomy に概念がなく登録できない
    （taxonomy 側の課題として引き継ぎ。§15 ラスト参照）。
- **未実装（引き継ぎ）**:
  - Platform Query Compiler（b.md Phase 3）と platform syntax の registry 表現
    （Q5 は現状 `submitted_query` の一致で代用。compiler 導入時に置換する）。
  - Semantic Filter Stage 2/3 と評価データ（b.md §8.3: 分類精度を測定せずに
    本番採用してはならない — Stage 1 はクエリ文字列の検証・デモ用で、コンテンツ
    分類の本番採用は未実施）。
  - provenance の `variant_id` / `compiler_id` / content hash（G5 schema 未拡張）。

## 16. G3 垂直スライス（Temporal Contract / Window Compiler / Coverage）— 2026-10-13

G3 仕様（`docs/plans/20261013c.md`）の垂直スライス。対象は Google Trends 1 ソース。
**ライブ収集・新しい外部依存の追加は行っていない。**

### 16.1 決定事項

- **§13 と §4.2 の矛盾**: G1/G2 と同じ解釈を踏襲。§13 の required リストを必須、
  §4.2 の追加項目（`calendar` / `week_start` / `temporal_contract_version`）は任意
  （`validation.schemas.temporal` の docstring に記録済み）。
- **window 正本**: `metadata/windows/<window_id>.json`（ファイル名 = window_id）。
  スキーマは既存 `temporal-window-v1` を再利用（**新スキーマなし**）。研究計画の
  正本はこの絶対期間であり、相対期間は collector パラメータ（compiler 出力）に
  のみ存在する。初期登録は 2 件（`2025-10-12_2026-10-12` / `2021-10-10_2026-10-12`）。
- **旧 29 run**: 遡及変換しない（P1）。`audit-temporal` は事実の抽出のみを行い、
  `resolved_absolute_window: null` + not-derived 理由を記録する（§15）。
- **検出時点**: plan の `window.window_id` がレジストリにある場合、bounds / timezone /
granularity / week_start の完全一致を要求（不一致・未登録は exit 1）。
  レジストリ不在時は既存規約どおりチェック無効。
- **要求と実際のずれ**: 表現可能なら `partial` として採用・記録（推奨 A）。
  表現不能（候補 timeframe なし・時代不一致・絶対能力 supported なのに実装なし）は
  fail closed。厳密期間が必要な研究は plan に `window.exact_required: true` を明示する
  と、`exact=false` の collector では停止する（c.md §6.2）。

### 16.2 実装済み

- `validation/windows.py`: 半開区間の UTC 変換（c.md §7 の期待値一致）、相対時間
  語彙（`today 1-m/3-m/12-m/5-y`）の名目解決（基準時刻必須）、月末/闰年クランプ、
  DST 対応のカレンダー演算、許容差 7 日（週次バケット 1 個）の一致判定、
  月次バケット生成、`CompiledWindow` 契約と compiler shape check。
- `collection/adapters/google_trends/compiler.py`: 絶対 window → timeframe 変換の
  実行前検証。拒否理由コード（`no_registered_timeframe_matches` 等）は安定 API。
  platform 名は adapters のみ（P1）。
- pipeline 統合（`collection.core.pipeline`）: 収集前に compile し、結果を
  `query` 拡張領域へ source-agnostic にマージ。衝突は `WINDOW_TIMEFRAME_CONFLICT` で
  停止（P6）。失敗コード: `WINDOW_NOT_REPRESENTABLE` / `WINDOW_EXACTNESS_UNAVAILABLE`。
- provenance: `temporal_provenance` に `reference_time` / `limitations` を追加
  （任意、後方互換）、観測側は bucket label 範囲を `observed_min/max_timestamp`
  に記録（requested / observed の分離 = P5）。
- `validation/coverage.py` + `coverage-run`: §9.3 形式の manifest。requested /
  collector（名目解決）/ observed（ラベル）/ verified（空のまま）を区別し、
  欠測・観測ゼロ・取得失敗を区別する（P7）。実例: `common-scale-missing` →
  `partial`（terms は observed_nonzero、0 点は below_threshold 候補）、
  `nodata` → `missing`（terms は `below_threshold`。`observed_zero` は**使わない**）。
- temporal comparability（§12）: T1-T5/T8 は既存。coverage manifest を渡した場合の
  T6/T7 を追加（partial → conditional / missing → not_comparable / unknown →
  missingness 未明示として unknown）。CLI `--coverage-a/--coverage-b` で有効化。
- 旧 run 監査（§15/Phase 1）: `docs/audits/g3-temporal-inventory.json`（29 run、
  sha256 前後比較で `raw_modified: false`。テストが再計算一致を強制）。

### 16.3 未実装（引き継ぎ）

- ライブ収集による Google Trends の境界挙動検証（`exact=true` への昇格条件）。
  それまでは全 compile が `exact=false` / `boundary_semantics=unverified`。
- 他ソース（X / YouTube / TikTok / Instagram / LinkedIn）の Window Compiler と
  `dateFilter=month` 等のローリング語彙の検証。
- §10 の日次/週次のバケット集計（月次バケット生成のみ実装。分析側の集計は未接続）。
- coverage manifest の run ディレクトリへの永続化（現状は `coverage-run` のオンデマンド評価）。
- T6 の sampling / normalization 条件（comparison set 等）の完全モデル化（G7）。

## 17. G4 垂直スライス（Artifact Registry / Storage Contract / Data Catalog）— 2026-10-13

G4 仕様（`docs/plans/20261013d.md`）の垂直スライス。対象は Google Trends の
既存 29 run（読取専用監査）と新規 run（G1 replay）の Artifact／保存形式。
**ライブ収集・新しい外部依存の追加は行っていない**（SQLite は標準ライブラリ）。

### 17.1 決定事項

- **配置**: reader / schema の対応表は `metadata/artifacts/artifact-registry.json`
  （スキーマ `artifact-registry-v1`）。`config/` は G1 の実行時 registry、
  `config/storage-policies.json` は G6 の予約領域であり重複させない。
- **G4 と G6 の役割分担**: G4 は「何を・どう読むか・どう識別するか」
  （schema / reader / manifest 契約 / 棚卸し / catalog）。G6 は「どこに置けるか・
  Git 追跡・公開可否」（policy / publication gate）。本スライスでは
  `config/storage-policies.json` を追加していない。
- **SQLite の扱い（決定）**: reader と schema 契約は**宣言して実装済み**
  （read-only で存在時のみ検証）。リポジトリ範囲に実 DB が無いことは監査で
  `sqlite_present: false` として記録し、存在しないハッシュやレコードを
  作らない（P8）。ローカル専用 DB（Git 管理外）はリポジトリ監査の対象外。
- **manifest の拡張**: 既存 `artifact-manifest-v1` に任意フィールド
  （`contains_full_timeseries` / `page_index` / `artifact_group_id` /
  `database` / `artifact_groups`）を追加（後方互換。契約バージョンは 1.0.0 の
  まま — G2/G3 の踏襲）。**新規 manifest スキーマは作らない**。
- **legacy の lineage**: manifest が無い 29 run は `lineage:unknown` と明示し、
  `derived_from` を推測で埋めない（各成果物/run に
  `verification: unverifiable_no_manifest` を記録）。catalog は manifest
  からのみ生成する。（監査: `docs/audits/g4-storage-inventory.json` / `.md`）。

### 17.2 実装済み

- `src/storage/`（source-agnostic。プラットフォーム名は schema_id / registry
  側にのみ現れる）:
  - `contracts.py`: `ArtifactDescriptor` / `StorageReader` 契約。未実装モードは
    `UnsupportedRead` で**拒否**し、近似・再構成をしない（§12 / P8）。
  - `readers/`: `json-record-reader`（§9 参考実装。配列）/ `json-page-reader`
    （`items` ラッパーと素配列の両対応）/ `json-timeseries-reader`（`date`+`value|interest`）/
    `json-summary-reader`（集計のみ。`points` モードを持たない）/ 
    `json-comparison-reader`（複数語の共スケール行）/ `json-object-reader` /
    `sqlite-reader`（`mode=ro` URI・テーブル列挙・`record_lineage` 有無）。
  - `sniff.py`: 内容ベースの識別（magic bytes / JSON 構造）。判定は
    recognized / partial / ambiguous / unknown + evidence 文字列。
  - `inventory.py`: §16 非破壊棚卸し（sha256 前後比較、run マーカー除外、
    `private/` 既定除外、ページ系列の missing / observed_zero 区別）。
  - `catalog.py` / `lineage.py`: manifest からの決定論的 catalog 生成（§14）と
    catalog 横断の lineage 検証・祖先遡及（§15）。
  - `cli.py`: `read` / `inspect` / `catalog`（read-only。exit 0/1/2/3）。
- `src/validation/storage_contract.py`: §10 のうち S1 / S6-S12
  （重複 ID・format 実体照合・reader 登録（S9）・schema 適合（S7）・
  record_count（S8）・パス安全性（S11）・ページング整合（§11）・summary 矛盾（§12）・
  SQLite lineage（§13））+ registry 内部整合。`integrity.verify_artifact_manifest`
  に統合し、**L1（gate-run / collect の採用判定）で自動適用**される。
  reader 依存検査は registry 不在時に無効（既存規約どおり false failure を出さない）。
- schema: `artifact-registry-v1` 新設 + `artifact-manifest-v1` の後方互換拡張。
- CLI: `validation.cli audit-artifacts`（既定出力 `docs/audits/g4-storage-inventory.json`）
  + `storage.cli`（reader デモ・内容判定・catalog）。
- 実測（2026-10-13、offline replay）:
  - G1 replay（5y fixture、261 点）→ adopted。`gate-run` exit 0。manifest の
    SHA-256 / byte_length / record_count（data_points 261）が一致。
  - payload を 1 バイト変更したコピー → `ARTIFACT_HASH_MISMATCH` / quarantine /
    exit 1（改ざん検出）。
  - catalog 生成 → 同一 manifest から byte-identical（決定論）。
  - summary を `--mode points` で読む要求 → exit 1（宣言 261 点あっても
    フル時系列として扱わない）。
- 旧 run 監査（§16 / Phase 1）: `docs/audits/g4-storage-inventory.json`
  （77 成果物 / 29 run。`raw_modified: false`。テストが再計算一致を強制）。

### 17.3 未実装（引き継ぎ）

- 登録済み reader は recorded / synthetic fixture での検証。**ライブ収集に
  よる実レスポンス形状の照合は未実施**（§13 と同じ制約）。
- legacy 変種（comparison の averages のみ・related queries バッチ・no-data 応答・
  分散解析 JSON など。監査 §6 の 16 件）の reader 登録は、実利用時に §7 の手順で
  行う（G4-T17 の経路）。登録時は監査スナップショットの再生成が必要。
- SQLite 実データ（ローカル専用 `trends.db`）の検証はローカル環境で実施可能
  （CI は非公開 raw を扱わない）。`record_lineage` テーブルは既存 DB には未導入
  （schema.sql への追加は実運用判断）。
- Data Catalog の永続化先（`datasets/<study>/metadata/data-catalog.json` 等）は
  未確定。現状は `storage.cli catalog --output` のオンデマンド生成。

## 18. G5 垂直スライス（Provenance Contract / Evidence Registry / Audit Trail）— 2026-10-13

対象は Google Trends replay run（新規の貫通路）+ 既存 29 run（非破壊監査）。
仕様書 `docs/plans/20261013e.md`（ローカル計画書。履歴外）の垂直スライス。

### 18.1 決定事項（重複整理 T1 — canonical は1つ）

| 資産 | 役割 | 扱い |
|---|---|---|
| `src/collection/core/provenance.py`（G1） | 生成の正本（builder） | 維持。必須9項目の対応表はここが正本 |
| `collection-run-v1`（`src/validation/schemas/collection_run.py`） | 構造の正本 | 維持。変更なし |
| `transformation-v1`（`src/validation/schemas/provenance.py`） | 変換来歴の構造正本 | 維持。モジュール名と内容の不一致は docstring に記録し、rename はしない |
| `src/validation/provenance.py`（新設） | 評価の正本（assessor） | 読取専用。run_metadata を生成しない |
| `docs/provenance.md` | 人間向け来歴ナラティブ（解釈層） | 内容は変えず、冒頭に正本への参照注記のみ追加 |
| `docs/audits/g5-legacy-runs.json` | 旧 run の構造欠落監査（29件） | 形式凍結。G5 の証拠レベル監査は別ファイル |
| `docs/provenance/` 台帳群 | collector/query/taxonomy の人手台帳 | 維持。Evidence Registry の種別語彙と整合 |

- 親タスク文中の `src/validation/provenance.py`（G1 builder）および
  `src/validation/schemas/transformation.py` は実在しないことを確認
  （実体は `src/collection/core/provenance.py` と
  `src/validation/schemas/provenance.py`）。仕様との対応表は §18.4 を参照。
- 既存スキーマの変更はゼロ（後方互換）。追加のみ: `evidence-registry-v1`、
  新規 CLI `audit-provenance`、意味検査 2 件（P01/P17）。

### 18.2 実装済み

- `src/validation/provenance.py`: §9 の4指標（Completeness=22 path の検証率
  / Confidence=observed・unknown の機械付与 / Integrity=manifest 存在・妥当・
  hash の要約 / Readiness=ready・partial・not_ready・unknown）と §10 の証拠
  レベル監査。`inferred` / `ambiguous` は語彙にのみ存在し、自動付与しない
  （contract test が固定。P2/P5）。`cerberus` 非 import・プラットフォーム名なし
  （P8）・無変異。
- P01: `validate-study` が strict run 横断の `run_id` 重複を
  `RUN_ID_DUPLICATE` で FAIL（legacy は対象外。既存 29 run の run_id は重複なし
  を実測確認）。
- P17: `semantic.check_query_registry_version` を pipeline に接続。一致=沈黙・
  不一致=info・欠落=warning（判定不能）。error を出さないため既存 strict 合格
  は不変（`test_valid_document_produces_valid_outcome` の `issues == []` を維持）。
- Evidence Registry（§11）: `metadata/provenance/evidence-registry.json`
  （8 証拠。ローカル参照のみ。fixture 1 件のみ sha256 ピン留め、残りは未記録を
  明示）。`evidence-registry-v1` + 参照存在・hash 照合・ID 重複検査
  （`provenance.check_evidence_registry`）+ secret scan を `validate-registries`
  に接続。CI は変更なしで 8 ターゲットを実検証する。
- CLI `audit-provenance`: 既定出力 `docs/audits/g5-provenance-assessment.json`
  （常に exit 0 の読取専用レポート。`raw_modified` + sha256 前後一致を記録）。
  run ディレクトリ内の `transformation-*.json` があれば構造＋lineage（P18）も
  検証する（現状 0 件を明示）。
- 実測（2026-10-13）:
  - 新規 run（G1 replay、12m fixture）→ adopted。strict valid（issue なし）。
    Completeness 22/22=1.0。Integrity verified。Readiness **ready**。
  - legacy 29 run → strict_valid 0。Completeness 0.09–0.14。Readiness **not_ready
    29/29**。証拠レベルは observed/unknown のみ。`raw_modified: false`、全件
    sha256 前後一致。旧 metadata・凍結リストは無変更。
  - `pytest` **721 passed**（G4 直後 680 + G5 新規 41）。`validate-registries`
    **8 ターゲット全 valid**。
- §15 対応表は `tests/validation/test_provenance.py::test_g5_t_mapping_table`
  に機械化（未達は G5-T19 のみ。新規 source がスライスに存在しないため延期）。

### 18.3 未実装（引き継ぎ）

- Transformation record の builder（処理パイプライン側の生成器）。schema +
  lineage 検査 + 監査配線は済み。processed/interim 生成が始まる G6 以降で
  `transformation-v1` 準拠の生成器を用意すること。
- Evidence Registry と run 監査の突合（監査の unknown 項目を証拠引用で
  inferred/observed へ昇格させる pass）。語彙と参照形式は用意済み。
- Provenance Graph（§12）は lineage 辺（run→artifact→transformation）の JSON
  参照まで。グラフ DB・PROV-O 変換は将来（仕様上も初期は JSON で十分）。
- Apify クラウド側の証拠（actor 実行記録・datasets）は未取得。必要になった
  場合は取得依頼リストを上げ、推測で埋めない（P2/P5）。現 29 run は全件
  google-trends のため本スライスでは該当なし。X/YouTube 旧 run の実行条件は
  引き続き unknown。
- ライブ収集・CI ワークフロー変更は未実施（CI は pytest + validate-registries
  のまま green）。

## 19. G6 垂直スライス（Git Tracking Policy / Storage Classification / Publication Gate）— 2026-10-13

G6 仕様（`docs/plans/20261013f.md`）の垂直スライス。Git 運用全体を作り替えず、政策を「宣言」し、実ツリーに対する判定が回ることを示す。**実際の公開・リリース・DOI 登録は行わない**（判定は記録のみ）。

### 19.1 決定事項

- **配置**: Storage Policy Registry は `config/storage-policies.json`（G4 が予約した領域。G4 §17.1 の役割分担どおり）。G4 が「読み方・識別・索引」、G6 が「保存先・追跡・公開可否」。重複なし。
- **既存実装の扱い**: `src/validation/storage_policy.py`（P4-7/P4-9）は**作り替えず再利用**。本スライスは新規モジュール（`g6_inventory` / `publication_eligibility` / `private_catalog` / `storage.backend`）と CLI 配線（`audit-git-tracking` / `audit-private-catalog` / `gate-publication`）を追加したのみ。
- **Policy と `.gitignore` の役割分担**: Policy は層×種別の宣言（ファイル glob を持たない）。`.gitignore` は追跡除外の実装。両者の矛盾は inventory が実 git 状態として報告し、変更は提案に留める（適用は親判断）。
- **public-methodology の publication**: 参考例の `approved` ではなく `requires_review` とした（Fail closed P5: policy 承認 ≠ per-artifact 承認。per-artifact decision が必須）。
- **Storage Backend の範囲**: ローカル FS 宣言まで（`LocalFilesystemBackend`）。クラウド・object storage は将来。
- **Private Catalog**: 存在記録まで。内容分類は行わない。
- **Release Manifest / Zenodo（§12）**: 本スライスでは未実装（引き継ぎ §19.3）。

### 19.2 実装済み

- `config/storage-policies.json`（6 policy。`storage-policy-registry-v1` で `validate-registries` が実検証。`*.csv` 等の一括除外なし）:
  - `raw-search-tracked`（raw/search。google_trends 例外の宣言）/ `raw-social-default` / `raw-default`（`any` wildcard で TikTok/Instagram/LinkedIn 等の将来種別を被覆）/ `interim-default` / `processed-public-candidate`（`conditional`）/ `public-methodology`。
- `src/validation/g6_inventory.py` + CLI `audit-git-tracking`（§15。read-only git のみ。`raw_modified` 前後 hash 証跡。`private/` は存在・除外状態のみ）:
  - 実測: dataset 134 件全件 tracked（google_trends 99 件含む）+ extras 33 件 → `tracked 147 / ignored 4 / absent 16 / untracked_unignored 0`。`accidental_add_risk: []`、`ignore_warnings: []`。（監査: `docs/audits/g6-git-tracking-inventory.json` / `.md`）
- `src/validation/publication_eligibility.py` + CLI `gate-publication`（§10。§11 最小規則と secret scan を再利用。`cerberus` 非 import）:
  - 実在 1 件（`x_cbx_202608_summary_anonymized.csv`、`processed-public-candidate`）に実行 → **`BLOCKED`**（`failed: PUB-01/04/10`、`warnings: PUB-06/07/08`。PUB-02/03/05/09 PASS）。BLOCKED は成果物の問題の記録でありゲートの失敗ではない。（監査: `docs/audits/g6-publication-eligibility.json` / `.md`）
- `src/validation/private_catalog.py` + CLI `audit-private-catalog`（§13。値は出さない）:
  - 実測: マーカー 9 件、`present 0 / absent 9`（worktree に `private/` なし）。全件 `restricted / private / not_approved`。（監査: `docs/audits/g6-private-catalog.json` / `.md`）
- `src/storage/backend.py`（§14 local FS。`put_immutable` は上書き拒否 G6-T18。missing は False であってゼロではない P8）。
- 実測（2026-10-13、`.venv` + Python 3.14）: `pytest` **743 passed**（G5 直後 721 → +22）。`validate-registries` **9 ターゲット全 valid**（storage-policies 追加）。
- §16/§17 対応表は `tests/validation/test_g6_vertical_slice.py` に機械化（T12/T13/T19/T20 = 未達を明示、T16 = wildcard 被覆のみ）。

### 19.3 未実装（引き継ぎ）

- Release Manifest / GitHub Release・Zenodo 候補検証（G6-T12/T13/T19/T20）。schema（`release-manifest-v1` 等）・CLI・CI 配線は将来。`scripts/release/create-clean-archive.sh` と `release-zenodo.yml` の現行運用は変更なし。
- 新規収集 run の追跡方針（判断待ち①）は**現状追認で確定**（2026-10-13）: `google_trends` の raw は追跡、それ以外の raw は `**/data/raw/*` により除外。変更する場合は policy の再定義と `.gitignore` 例外の見直しが必要。
- 新規収集 run の追跡方針の確定（判断待ち①）、追跡↔除外の変更適用（判断待ち②: `*.db` 除外は追加済み・判断待ち⑤としてレビュー例外を記録、判断待ち③④は現状維持で確定）。
- ライブ収集・CI ワークフロー変更・SQLite 実データ検証は未実施（CI は pytest + validate-registries のまま green）。
