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
| G7 垂直スライス | Study Registry / Research Catalog / Comparability Gate / Research View | **実装済み（9-study: 2026-10-13 増分で残り7件を登録。`cbx-product-coa` は sources 空（lab COA に対応する source なし）。測定は既存3件で充足のため追加なし）**（Study/Measurement Registry＋CI 検証11件。Catalog は派生索引（P2）。Gate は CS01-CS13、`comparable` は完全証拠時のみで実データ上限は `conditional`。View は `parallel_timeseries` 派生（合算なし）。9 study 非破壊監査は `docs/audits/g7-study-inventory.*`（再生成なし。registry 登録とは独立）、raw sha256 前後一致） |

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
- pre-commit フック導入: `bash scripts/git-hooks/install.sh`（schema＋version＋research-pages＋emergence の4検証。検証は /tmp scratch clone でのみ行う）。

## 3. テスト

```bash
.venv/bin/python -m pytest
```

- Contract Tests: `tests/validation/`（609件）+ `tests/collection/`（77件）
  + `tests/storage/`（57件）+ `tests/research/`（46件）＝ **789件**（2026-10-13 G2/G7 増分後も同数。
  `.venv/bin/python -m pytest` で実測（Python 3.14＋editable install）。G6 直後は 743 件）。
  G2/G7 増分では件数を増やさず、崩れた前提の assertion を新しい真実に更新した
  （`test_audit_snapshot_records_the_legacy_examples` の分割不変条件化、
  `test_study_registry_covers_exactly_the_nine_studies` の 9-study 化）。
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

### 6.1 追加ステップ（2026-10-13 増分）と除外の記録

追加（いずれも main 上で green をローカル実測。秒単位。`release-zenodo.yml` は不変）:

- `bash scripts/validation/validate-data-schema.sh`（PASS 45 / WARN 2 / FAIL 0、約0.2秒）
- `python -m validation.cli audit-publication --output docs/audits/publication-contract.json`
  （公開契約 PC-1〜PC-8。read-only、record-only、常に exit 0。2026-10-15 に
  `scripts/validation/validate-research-pages.py`（不活性）を削除して置換）
- `bash scripts/validation/validate-search-emergence-tracker.sh`（PASS、約0.1秒。network 不要。§3 の日付比較は WARN のみで exit に影響しない）
- `python -m validation.cli audit-git-tracking --output /tmp/g6-git-tracking-inventory.json`
  （read-only、report-only、常に exit 0。tracked/ignored/absent を CI ログに記録）
- exports 同期検査（`export-taxonomy.sh --output-dir` を scratch に実行し、tracked の
  `exports/taxonomy/*` と diff して一致を要求。regeneration は正規スクリプトのみ）
- `python -m processing.cli audit-processed`（Phase B 増分。read-only。コミット済み
  processed 成果物が「再実行可能な導出」か「欠落入力を明示した再現不能宣言」の
  どちらかであることを要求。現状 8 成果物で exit 0。§20）

除外（理由）:

- `validate-version-sync.sh`: CI ゲートから除外する（2026-10-13 再評価済み）。
  除外理由は初期の「完走不能」ではなく、基準値の意味論にある: 基準バージョン・
  DOI は最新 Git タグと公開済み Zenodo/GitHub Release から取るため、(1) main より
  古いブランチの PR では無実の FAIL になる、(2) バージョン上げコミットからタグ付け
  までの間は main でも FAIL になる、(3) network 到達不能時は基準が空になり検査が
  静かに素通りする。リリース時の正本確認としては正しいが、push/PR 毎のゲートには
  向かない。pre-commit フックと手動実行で使う。なお `preferred-citation.doi`
  （`10.5281/zenodo.23253840`）の追記によりスクリプトは完走し、現 main では
  PASS 12 / WARN 1 / FAIL 0 である。
- `validate-all`（strict）: legacy 29件で exit 1 が正常＝ゲートにできない（従来どおり）。
- ライブ収集・認証情報・network・ローカル専用ファイル（`trends.db` 等）を要するもの。
- リリースのブロック: `release-zenodo.yml` は published トリガ（公開後に走るため
  公開を止められない）。公開可否は `gate-publication` の人手実行＋記録で行う
  （`docs/specs/release-process.md` の Pre-release 項目）。

非決定論の扱い:

- `exports/taxonomy/*.ttl` の `# Generated:` 行は `datetime.utcnow()` 埋め込みの
  非決定論的生成記録であり、同期検査の比較対象から除外する（`grep -v '^# Generated:'`
  で正規化。スクリプト本体は変えない）。`schema.jsonld` の `dateCreated` は固定値
  のため除外不要。

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
| 既存検証資産 | `scripts/validation/*.sh`（3本）※ `validate-research-pages.py` は 2026-10-15 に不活性（到達不能な規則・存在しないパス）のため削除し、公開契約の監査へ置換（`docs/specs/contracts.md` の PC 規則） |
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

## 10. スキーマ一覧（19件、契約バージョンはいずれも 1.0.0）

「契約」は総称である。用語の定義・所有コンテキスト・宣言場所・検査手段は
`docs/specs/contracts.md`（契約のドメインモデル）を正本とする。下表の**グループ**列は
Cerberus の作業グループ（`G1`〜`G7` / `P6`）を指す。

| Schema ID | グループ | 主な内容 |
|---|---|---|
| `collection-run-v1` | G5 | run_metadata（finalized） |
| `collection-run-v1-running` | G5 | 実行中 profile。`status=running` のみ許容、`collection_finished_at` は未知フィールド扱い（復帰ラベルによる回避を検出） |
| `source-registry-v1` | G1 | `config/sources.json` |
| `collector-registry-v1` | G1 | `config/collectors.json`（capability 三値・status 五値） |
| `query-registry-v1` | G2 | `metadata/queries/query-registry.json` |
| `query-variants-v1` | G2 | 表記ゆれブロック |
| `query-variants-registry-v1` | G2 | `metadata/queries/query-variants.json`（variant 束。ブロック形状は `query-variants-v1` を再利用） |
| `temporal-window-v1` | G3 | 単独 window 文書 |
| `coverage-manifest-v1` | G3 | run の coverage 判断（§9.3 manifest。`schema_id` / `schema_version` 付き。永続化は `<run-dir>/coverage-manifest.json` への明示 opt-in のみ — §16） |
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
| `metadata/queries/query-registry.json` | query-registry-v1 | **あり**（G2 垂直スライス + 2026-10-13 増分: 31 queries。`validate-registries` と CI が実検証する） |
| `metadata/queries/query-variants.json` | query-variants-registry-v1 | **あり**（3 variant sets） |
| `metadata/windows/*.json` | temporal-window-v1 | **あり**（G3 垂直スライス: 2 windows。`validate-registries` と CI が実検証する） |
| `metadata/artifacts/artifact-registry.json` | artifact-registry-v1 | **あり**（G4 垂直スライス + 2026-10-15 増分: 8 readers / 12 artifact schemas。`validate-registries` と CI が実検証する） |
| `metadata/provenance/evidence-registry.json` | evidence-registry-v1 | **あり**（G5 垂直スライス: 8 証拠。`validate-registries` と CI が実検証する — §18） |
| `metadata/studies/study-registry.json` | study-registry-v1 | **あり**（G7 垂直スライス + 2026-10-13 増分: 9 studies。`validate-registries` と CI が実検証する） |
| `metadata/measurements/measurement-registry.json` | measurement-registry-v1 | **あり**（G7 垂直スライス: 3 measurements。`validate-registries` と CI が実検証する） |
| `config/storage-policies.json` | storage-policy-registry-v1 | **あり**（G6 垂直スライス: 6 policies。`validate-registries` と CI が実検証する） |

`validate-registries` は存在するファイルのみを検証する（現在 **11 ターゲット**。実測 valid）。G2 の 2 ファイルは検証
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
  - ライブ収集（レート制限・資格情報）の実行と実レスポンスでの契約照合。
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
**2026-10-13 追記（G2 増分）**: taxonomy に概念があるのにクエリ未登録だった
THC / CBG / CBN / CRDH / H4CBH / HHBD / THCV の **14 クエリ**（`compound_general` +
`product_liquid` の分離を維持。表記ゆれは実収集の証拠がないため追加なし）を登録し、
**計 31 クエリ**（14 化合物）となった。証拠は `docs/provenance/query-inventory.md` §1
（版 1.2.0）に run 単位で追記。`audit-queries` を正規コマンドで再生成:
exact_match 41 → **73**、`ambiguous` 32 → **0**（29 run に記録された化合物トークンは
全て登録済みとなった正当な帰結）、`variant_match` 1 / `semantic_match_candidate` 1
（`THC-Oリキッド`）/ `unmapped` 0 は不変、`raw_modified: false`。`test_audit_snapshot_records_the_legacy_examples`
の旧前提（`states["THC リキッド"] == "ambiguous"`、`ambiguous > 0`）は崩れたため
新しい真実（全分割 73/1/1/0/0）に合わせて assertion を更新した。**ライブ収集・
新しい外部依存の追加は行っていない。**

- **実装済み**:
  - `metadata/queries/query-registry.json`（31 queries）/
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
    29 run / 75 文字列を exact_match=73 / variant_match=1 / ambiguous=0 /
    unmapped=0 / semantic_match_candidate=1 に分類し、`raw_modified: false`
    （sha256 前後比較）。テストが再計算一致を強制する。
- **決定（J1 は要確認）**:
  - 既存 29 run の旧形式 `queries` は registry 照合の対象にしない（形状分離＋
    監査ファイルで対応関係を管理）。新規 run の `query_provenance` は fail closed。
    この決定は可逆で、旧形式を fail closed の対象にする場合は凍結リスト運用
    （legacy.py）側の再設計が必要になるため、採用していない。
  - 除外方式は「正規化（NFKC + casefold）＋明示フレーズ表」（正規表現なし。
    根拠: docs/collection-gap-analysis.md 原因 G2 行 + b.md §8）。
  - THC-O / THCH / CRDP / HHC / HHBD の taxonomy 欠落は解消済み（登録済み）。
    残る taxonomy 側の課題は §15 ラスト参照。
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
  日次・週次（`week_start: sunday/monday`）・月次バケット生成、`CompiledWindow`
  契約と compiler shape check。
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
  欠測・観測ゼロ・取得失敗を区別する（P7）。宣言 granularity（day/week/month）
  の期待バケット `expected_intervals` と欠測 `missing_expected_intervals` を
  加算記録する（欠測は missing/unknown 証拠であり `observed_zero` 化しない）。
  実例: `common-scale-missing` →
  `partial`（terms は observed_nonzero、0 点は below_threshold 候補）、
  `nodata` → `missing`（terms は `below_threshold`。`observed_zero` は**使わない**）。
- temporal comparability（§12）: T1-T5/T8 は既存。coverage manifest を渡した場合の
  T6/T7 を追加（partial → conditional / missing → not_comparable / unknown →
  missingness 未明示として unknown）。CLI `--coverage-a/--coverage-b` で有効化。
- 旧 run 監査（§15/Phase 1）: `docs/audits/g3-temporal-inventory.json`（29 run、
  sha256 前後比較で `raw_modified: false`。テストが再計算一致を強制）。
- coverage manifest の永続化（ISS-20261015-COV-004、2026-10-15）: schema
  `coverage-manifest-v1`（`schema_id` / `schema_version` 付き。`SCHEMA_VERSIONS`
  は 1.0.0）を登録し、正規の派生ファイル `<run-dir>/coverage-manifest.json`
  を `coverage-run --persist` の明示 opt-in でのみ生成する。`--persist` は
  `--output` と排他（併用は exit 2）、対象不在は exit 3。生成器は既存の
  `evaluate_coverage` を再利用し（規則の複製なし）、決定論的シリアライザ +
  同 dir tmp → `os.replace` の atomic 置換で同一入力から byte-identical に
  再生成できる。既存 run への遡及生成はしない。`--persist` 無しは従来どおり
  読取専用のオンデマンド報告。raw payload と `run_metadata.json` は不変。
  併せて `expected_buckets_undetermined` 分岐の潜在例外（未定義 `reasons` への
  追加）を修正し、bucket 化不能な exact window を欠測証拠として記録する
  （`observed_zero` 化しない）。
- YouTube Apify `dateFilter=year` compiler MVP（ISS-20261015-WIN-002 部分実装、
  2026-10-15）: `collection.adapters.youtube.compiler` を追加し、
  `youtube-apify-scraper` の window compiler として登録した。COL-033 の採用済み
  宣言に基づく trailing ~365 days のみ compile し、`month` / `week` / `today` /
  `hour` / `all` は推測せず fail closed。`youtube` の live source factory は未登録の
  まま、registry capability も `unknown` のまま維持する。

### 16.3 未実装（引き継ぎ）

- ライブ収集による Google Trends の境界挙動検証（`exact=true` への昇格条件）。
  2026-10-15 に計測プロトコル・昇格規則（`docs/specs/gt-boundary-verification.md`）
  とオフライン計測基盤（`collection.adapters.google_trends.boundary` /
  `validation.cli boundary-report`）を実装した。owner `go` により pass 1 は実行・
  採用済みで、pass 2 は 2026-10-22T04:28Z 以降の time gate 待ち。それまでは
  `exact=false` / `boundary_semantics=unverified`（ISS-20261015-GT-001 PENDING）。
- 他ソース（X / TikTok / Instagram / LinkedIn）の Window Compiler と、YouTube の
  未測定 `dateFilter=month` / `week` / `today` / `hour` / `all` ローリング語彙の検証。
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
- **Data Catalog の永続化先（決定、ISS-20261015-ART-008、2026-10-15）**:
  canonical persisted catalog は `datasets/<study-id>/metadata/data-catalog.json`
  （1 study 1 ファイル）。本ファイルは派生メタデータであり raw ではない:
  `storage.catalog.build_catalog(<study>/data)` の再利用で生成し、timestamp や
  絶対パスを含まず、同一入力からは byte-identical に再生成できる。
  `docs/audits/*.json` は鮮度テスト登録の監査スナップショットであり代替しない。
  manifest が無い study は拒否せず `count: 0` / `manifest_count: 0` の空 catalog
  を永続化する（空 datasets root と同じ規則）。`--check-lineage` 付き永続化は
  書込み前に検証し、dangling 参照がある場合は正規ファイルを生成・更新せず
  exit 1 とする。

### 17.2 実装済み

- `src/storage/`（source-agnostic。プラットフォーム名は schema_id / registry
  側にのみ現れる）:
  - `contracts.py`: `ArtifactDescriptor` / `StorageReader` 契約。未実装モードは
    `UnsupportedRead` で**拒否**し、近似・再構成をしない（§12 / P8）。
  - `readers/`: `json-record-reader`（§9 参考実装。配列）/ `json-page-reader`
    （`items` ラッパーと素配列の両対応）/ `json-timeseries-reader`（`date`+`value|interest`）/
    `json-summary-reader`（集計のみ。`points` モードを持たない）/ 
    `json-comparison-reader`（複数語の共スケール行）/ `json-object-reader` /
    `sqlite-reader`（`mode=ro` URI・テーブル列挙・`record_lineage` 有無）/
    `csv-record-reader`（2026-10-15 追加。UTF-8+BOM / CRLF 許容、引用符内改行を保持、
    空行は record にしない、ragged / 重複列名は拒否。`count` は physical line ではなく
    CSV record 数。schema `youtube-dataset-csv-v1` = `data_rows`）。
  - `sniff.py`: 内容ベースの識別（magic bytes / JSON 構造）。判定は
    recognized / partial / ambiguous / unknown + evidence 文字列。
  - `inventory.py`: §16 非破壊棚卸し（sha256 前後比較、run マーカー除外、
    `private/` 既定除外、ページ系列の missing / observed_zero 区別）。
  - `catalog.py` / `lineage.py`: manifest からの決定論的 catalog 生成（§14）と
    catalog 横断の lineage 検証・祖先遡及（§15）。`catalog.py` は永続化
    helper（`catalog_path_for_study` / `build_study_catalog` /
    `dump_catalog` / `write_catalog`）を持ち、`build_study_catalog` は
    `build_catalog(<study>/data)` を再利用する（規則の複製なし）。
    `write_catalog` は同 dir tmp → `os.replace` の atomic 置換で、失敗時に
    部分ファイルを残さない。
  - `cli.py`: `read` / `inspect` / `catalog`（read-only。exit 0/1/2/3）。
    `catalog --study-dir datasets/<study-id> --persist [--check-lineage]`
    が正規 catalog を永続化する。`--persist` は `--study-dir` 必須・
    `--output` と排他。lineage 失敗時は書込み前に exit 1 し、正規ファイル
    を生成・更新しない。
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
- CSV reader（`csv-record-reader`、2026-10-15 追加）は synthetic fixture
  （`tests/storage/test_csv_reader.py`）に加えて、リポジトリ外の scratch
  workspace で実 dataset export 7 件の stage → adopt → 厳格検証まで
  rehearsal 済み（`docs/reports/20261015b-youtube-csv-staging-driver.md`）。
  実 export は third-party メタデータのためリポジトリには置かない。
- legacy 変種（comparison の averages のみ・related queries バッチ・no-data 応答・
  分散解析 JSON など。監査 §6 の 16 件）の reader 登録は、実利用時に §7 の手順で
  行う（G4-T17 の経路）。登録時は監査スナップショットの再生成が必要。
- SQLite 実データ（ローカル専用 `trends.db`）の検証はローカル環境で実施可能
  （CI は非公開 raw を扱わない）。`record_lineage` テーブルは既存 DB には未導入
  （schema.sql への追加は実運用判断）。
- Data Catalog の永続化先は確定済み（§17.1。ISS-20261015-ART-008、2026-10-15
  実装）。現状は `storage.cli catalog --study-dir datasets/<study-id> --persist`
  の正規永続化と、従来の `catalog --output` によるオンデマンド生成の併存。

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

### 18.3 未実装（引き継ぎ。2026-10-15 時点）

- ~~Transformation record の builder（処理パイプライン側の生成器）。schema +
  lineage 検査 + 監査配線は済み。processed/interim 生成が始まる G6 以降で
  `transformation-v1` 準拠の生成器を用意すること。~~ → **2026-10-15 に実装**
  （§18.4、ISS-20261015-PRV-010）。
- ~~Evidence Registry と run 監査の突合（監査の unknown 項目を証拠引用で
  inferred/observed へ昇格させる pass）。語彙と参照形式は用意済み。
  2026-10-15 に候補提示 pass とハッシュ方針まで実装。~~ → **2026-10-15 に実装・
  evidence hash の扱いも決着**（§18.4、ISS-20261015-PRV-011）。
- ~~Provenance Graph（§12）は lineage 辺（run→artifact→transformation）の JSON
  参照まで。グラフ DB・PROV-O 変換は将来（仕様上も初期は JSON で十分）。~~ →
  **2026-10-15 に不要と判断して記録**（§18.4、ISS-20261015-PRV-012）。
- Apify クラウド側の証拠（actor 実行記録・datasets）は未取得。必要になった
  場合は取得依頼リストを上げ、推測で埋めない（P2/P5）。現 29 run は全件
  google-trends のため本スライスでは該当なし。X/YouTube 旧 run の実行条件は
  引き続き unknown。
- ライブ収集・CI ワークフロー変更は未実施（CI は pytest + validate-registries
  のまま green）。

### 18.4 Provenance transformation / evidence スライス — 2026-10-15

§18.3 から引き継いだ来歴 backlog のうち、外部 API・raw 変更なしで閉じられる
vertical slice（ISS-20261015-PRV-010/011/012 + 関連の ISS-20261015-CMP-005）。

- **正本規則（PRV-010）**: 導出の正本は `processing.reproduce.DERIVATIONS` /
  `NON_REPRODUCIBLE`。生成器 `src/processing/transformations.py` は宣言を
  `transformation-v1` 形状に描画する派生 view であり、第二のレジストリではない
  （未登録は `KeyError`、構造不正は `ValueError`、`executed_at` は必須で遡及
  捏造不可）。構造の正本は既存 `TRANSFORMATION_SCHEMA`、lineage 規則は既存
  `check_transformation_lineage` のまま。platform-trends は 1 回の実行を 1 record
  （入力 = manifest の `sources` を再利用、出力 = 5 成果物）で表す。テストは
  `tests/processing/test_transformations.py`。遡及生成はしない（新規分から）。
- **突合 pass（PRV-011、RESOLVED）**: `src/validation/evidence_reconciliation.py`
  （`reconcile_evidence`）。run 監査の `unknown` と evidence エントリを突き合わせ、
  引用つき `candidate` / `no_covering_evidence` を出す read-only pass。自動昇格は
  しない（出力語彙に `observed` / `inferred` なし）。被覆は既知対応表のある
  `registry_definition` のみ。ハッシュ方針は
  `docs/provenance/evidence-hash-policy.md`（立会い観測時のみ記録。再生成出力は
  pin 留めせず、外部参照は対象外）。現行 7 件の `EVIDENCE_HASH_UNRECORDED` は
  6 件を owner 指示による現在時刻の観測として pin 済み、1 件は
  `regenerated_output` として pin 留めしない方針で決着。テストは
  `tests/validation/test_evidence_reconciliation.py`。
- **グラフ判断（PRV-012）**: PROV-O / グラフ DB は今は不要と判断し記録して閉じた。
  lineage 辺は JSON 参照 + 既存検査で完結し（本スライスで transformation 生成記録が
  加わった）、横断問い合わせは `storage.lineage.trace_ancestors` で答えられる
  （`tests/storage/test_catalog.py` が固定）。将来は具体的要求を trigger に
  JSON → PROV-O export のみ実装し、graph DB は持ち込まない。
- **比較証拠（CMP-005、OPEN のまま）**: CS08-CS13 の証拠発生条件を
  `docs/provenance/comparability-evidence-cs08-cs13.md` に定義（担体・生成者・
  比較側/収集側の状態。CS12 の担体に本スライスの生成記録を追加）。比較側の
  条件 pins は `tests/research/test_comparability_evidence.py`（全て synthetic）。
  実データの `comparable` 主張はなし（到達不能のまま）。収集側の排出は将来作業。
  （2026-10-16: 収集側契約のみ予約。`collection-run-v1` の任意 `comparability_evidence`
  ブロックに `sampling_method` / `normalization_scale` を追加。adapter 排出・
  catalog/gate 読取は未実装のため実データ到達不能は不変）

## 19. G6 垂直スライス

G6 仕様（`docs/plans/20261013f.md`）の垂直スライス。Git 運用全体を作り替えず、政策を「宣言」し、実ツリーに対する判定が回ることを示す。**実際の公開・リリース・DOI 登録は行わない**（判定は記録のみ）。

### 19.1 決定事項

- **配置**: Storage Policy Registry は `config/storage-policies.json`（G4 が予約した領域。G4 §17.1 の役割分担どおり）。G4 が「読み方・識別・索引」、G6 が「保存先・追跡・公開可否」。重複なし。
- **既存実装の扱い**: `src/validation/storage_policy.py`（P4-7/P4-9）は**作り替えず再利用**。本スライスは新規モジュール（`g6_inventory` / `publication_eligibility` / `private_catalog` / `storage.backend`）と CLI 配線（`audit-git-tracking` / `audit-private-catalog` / `gate-publication`）を追加したのみ。
- **Policy と `.gitignore` の役割分担**: Policy は層×種別の宣言（ファイル glob を持たない）。`.gitignore` は追跡除外の実装。両者の矛盾は inventory が実 git 状態として報告し、変更は提案に留める（適用は親判断）。
- **public-methodology の publication**: 参考例の `approved` ではなく `requires_review` とした（Fail closed P5: policy 承認 ≠ per-artifact 承認。per-artifact decision が必須）。
- **Storage Backend の範囲**: ローカル FS 宣言まで（`LocalFilesystemBackend`）。クラウド・object storage は将来。
- **Private Catalog**: 存在記録まで。内容分類は行わない。
- **Release Manifest / Zenodo（§12）**: 本スライスでは未実装（引き継ぎ §19.3）。2026-10-15 に ISS-20261015-REL-014 の validation-only スライスとして実装（§19.4）。

### 19.2 実装済み

- `config/storage-policies.json`（6 policy。`storage-policy-registry-v1` で `validate-registries` が実検証。`*.csv` 等の一括除外なし）:
  - `raw-search-tracked`（raw/search。google_trends 例外の宣言）/ `raw-social-default` / `raw-default`（`any` wildcard で TikTok/Instagram/LinkedIn 等の将来種別を被覆）/ `interim-default` / `processed-public-candidate`（`conditional`）/ `public-methodology`。
- `src/validation/g6_inventory.py` + CLI `audit-git-tracking`（§15。read-only git のみ。`raw_modified` 前後 hash 証跡。`private/` は存在・除外状態のみ）:
  - 実測: dataset 134 件全件 tracked（google_trends 99 件含む）+ extras 33 件 → `tracked 147 / ignored 4 / absent 16 / untracked_unignored 0`。`accidental_add_risk: []`、`ignore_warnings: []`。（監査: `docs/audits/g6-git-tracking-inventory.json` / `.md`）
- `src/validation/publication_eligibility.py` + CLI `gate-publication`（§10。§11 最小規則と secret scan を再利用。`cerberus` 非 import）:
  - 実在 1 件（`x_cbx_202608_summary_anonymized.csv`、`processed-public-candidate`）に実行 → **`BLOCKED`**（`failed: PUB-01/04/10`、`warnings: PUB-06/07/08`。PUB-02/03/05/09 PASS）。BLOCKED は成果物の問題の記録でありゲートの失敗ではない。（監査: `docs/audits/g6-publication-eligibility.json` / `.md`）
- `src/validation/private_catalog.py` + CLI `audit-private-catalog`（§13。値は出さない）:
  - 実測: マーカー 9 件、`present 0 / absent 9`（worktree に `private/` なし）。全件 `restricted / private / not_approved`。（監査: `docs/audits/g6-private-catalog.json` / `.md`）
  - 2026-10-16 に既定出力を committed-safe 化（ISS-20261016-MNT-002）: `exists` / `present` / `absent` は `null`＋`include_local_state: false` で checkout 非依存にし、鮮度検査は完全一致に戻した。checkout の実在検査は `--include-local-state` の opt-in（コミット不可）。
- `src/storage/backend.py`（§14 local FS。`put_immutable` は上書き拒否 G6-T18。missing は False であってゼロではない P8）。
- 実測（2026-10-13、`.venv` + Python 3.14）: `pytest` **743 passed**（G5 直後 721 → +22）。`validate-registries` **9 ターゲット全 valid**（storage-policies 追加）。
- §16/§17 対応表は `tests/validation/test_g6_vertical_slice.py` に機械化（T12/T13/T19/T20 = 未達を明示、T16 = wildcard 被覆のみ）。

### 19.3 未実装（引き継ぎ）

- 新規収集 run の追跡方針（判断待ち①）は**現状追認で確定**（2026-10-13）: `google_trends` の raw は追跡、それ以外の raw は `**/data/raw/*` により除外。変更する場合は policy の再定義と `.gitignore` 例外の見直しが必要。
- 新規収集 run の追跡方針の確定（判断待ち①）、追跡↔除外の変更適用（判断待ち②: `*.db` 除外は追加済み・判断待ち⑤としてレビュー例外を記録、判断待ち③④は現状維持で確定）。
- ライブ収集・CI ワークフロー変更・SQLite 実データ検証は未実装（CI は pytest + validate-registries のまま green）。

### 19.4 Release Manifest 検証スライス（G6-T12/T13/T19/T20）— 2026-10-15

§19.3 から引き継いだ Release Manifest / Zenodo 候補検証（ISS-20261015-REL-014）。**検証のみで、公開・リリース・DOI 登録・Zenodo 送信は一切行わない**。

- **schema**: `release-manifest-v1`（`src/validation/schemas/release.py`、registry 登録＋契約テスト）。宣言するのは release identity（version / tag / concept DOI）、archive path、required paths、include roots、disallowed prefix/exact のみ。
- **検証**: `src/validation/release_manifest.py`（`check_release_manifest`）。required 不足・禁止パス・scope 外パスを検査し、version / DOI 一致と canonical 禁止パスは既存 `validation.release_archive_check.check_archive`（REL-015）に委譲する。規則の二重実装なし：manifest が canonical 禁止リストを狭めると構造エラーになる。
- **CLI**: `validate-release-manifest --file <manifest> [--archive <zip>] --format text|json [--output <path>]`。終了コードは既存規約（0 合格 / 1 内容不一致 / 2 manifest 構造エラー / 3 ファイル I/O）。zip と manifest は読むだけで、書くのは `--output` のみ。
- **CI 配線**: `.github/workflows/release-zenodo.yml` は clean archive 作成後・Zenodo 公開前に `scripts/release/make-release-manifest.py` で manifest を生成して検証する。不一致は upload 前に失敗する。既存の `Verify archive release identity` ステップは残す（新コマンドが同規則を包含することは `test_manifest_check_delegates_to_the_archive_identity_check` が固定）。
- **テスト**: `tests/validation/test_release_manifest.py`（合成 zip fixture のみ。`release-archives/`・実 Zenodo 不使用）。妥当 manifest 合格 / required 不足 / 禁止 prefix / scope 外 / stale DOI・version 不一致 / manifest 構造エラー / CLI 終了コード・JSON・`--output`・決定性・非破壊を coverage。
- 実測（2026-10-15）: 新規テスト 20 件を含む対象テスト全 PASS。`validate-registries` 全 valid。`contract-ledger.json` を再生成（30 契約。gap 8 は `gate-release-manifest` の version 未宣言＋既存 7）。

## 20. Processed 成果物の再現性（Phase B 垂直スライス）— 2026-10-13

### 20.1 背景（実測した不整合）

コミット済みの `datasets/*/data/processed/**` 8 成果物を調べたところ、導出規則が
実行可能な形では存在していなかった。AGENTS.md は「手作業のスプレッドシート操作より
実行可能な変換を優先する」と定めているが、実際には:

- どの `.py`/`.sh` も `early-warning-index-v1.csv`・`collection-summary.md`・
  `youtube_filtered_202607/*` を生成していない（grep で確認）。
- `classification-rules.yaml`・`iptc-mapping.yaml`・`metadata/keywords.yaml` を
  **読む Python コードがリポジトリに 1 つも無い**。分類器は 2026-10-02 に一度
  リポジトリ外で実行され、その出力だけがコミットされている。
- `cbx-social-trends/methodology.md` §2.1 は `data/raw/x/202608/` を raw の場所と
  して示すが、`data/raw/` にあるのは `.gitkeep` のみ。
- `cannabinoid-raw-collection/methodology.md` §3.3 は `screen_name` → `author_id` を
  「ハッシュ化」と記載していたが、実成果物の `author_id` は初出順の連番（`docs/data-dictionary.md`
  が正しい）。

### 20.2 規則（1 つの規則ですべての成果物に適用）

コミット済み processed 成果物は、次のいずれかでなければならない。

1. 追跡可能な入力から実行可能な変換で再導出できる（`DERIVATIONS`）
2. リポジトリ内容からは再現不能であることを、**欠落入力を名指しして**宣言する
   （`NON_REPRODUCIBLE`）

どちらにも無い成果物は FAIL。これにより新規にコミットされた processed ファイルが
この問いを素通りできない。さらに次の 2 状態も FAIL とする（宣言が嘘になっている
ため）:

- `undeclared_drift` — 導出結果が宣言していない差異で成果物と食い違う
- `stale_declaration` — 宣言済みの差異がもう発生していない（成果物を直した場合など）

静的ファイル（`.gitkeep`）は `placeholder` として件数を出し、黙って除外しない。

### 20.3 実装

- `src/processing/rulespec.py` — `classification-rules.yaml` のリーダ
- `src/processing/classify.py` — ルールベース分類（出力は SKOS notation のみ）
- `src/processing/anonymize.py` — 重複排除済み CSV → 匿名化 CSV の導出
- `src/processing/reproduce.py` — 再導出監査（`DERIVATIONS` / `NON_REPRODUCIBLE` /
  `REVIEW_NOTES`）
- `src/processing/cli.py` — `python -m processing.cli {audit-processed,reproduce,classify}`

**決定（YAML の読み方）**: 本リポジトリの第三者依存は cerberus のみと定めているため
（`pyproject.toml`）、YAML ライブラリを追加せずに文書化されたサブセットだけを読む
リーダを `rulespec.py` に置いた。リーダは**厳格**（キーワード集合が空・fallback 欠落・
閾値が読めない場合は `RuleSpecError`）で、`load_content_rules` が返す記録済み分布を
`reproduce.py` の自己検査に使う。YAML ライブラリ導入または仕様の JSON 正本化を選ぶ
場合は `load_content_rules` 1 関数のみ差し替えればよい。

**決定（同点の扱い）**: 仕様はキーワード同数時の規則を定めていない。ファイル記載順で
先の概念を採用するという読みを `classify.py` に明記し、テストで拘束している。

### 20.4 検証結果（2026-10-13 実測、Python 3.14）

- `x_cbx_202608_summary_anonymized.csv` は追跡済みの非匿名化 summary から
  **16 列中 15 列が 147/147 で一致**。残る `week` のみ 3 行差（成果物は 2026-08-31 を
  `unknown`、規則は W5）。差は `src/processing/reproduce.py` に日付付きで宣言。
- 分類 3 列（`topic_id`/`intent_id`/`format_id`）の再現分布は仕様自身の
  `classification_results` と**完全一致**（147 件）。
- 監査結果: `not_reproducible_from_repository` 6 / `placeholder` 1 /
  `reproducible_with_declared_discrepancy` 1、`failure_count 0`。
- `pytest` **823 passed**（`tests/processing/` 34 件追加、従来 789）。
- `validate-registries` 11 ターゲット全 valid、`validate-data-schema.sh` PASS 45 /
  WARN 2 / FAIL 0、`validate-version-sync.sh` PASS 12 / WARN 1 / FAIL 0。

### 20.5 レビュー事項（決着済み/未決）

- ~~X の個別アカウント情報を含む CSV の追跡継続~~ → **2026-10-13 に公開取り下げで決着**。
  §21 を参照。
- ~~`early-warning-index-v1.csv`（導出規則が皆無の唯一の成果物）~~ → **2026-10-15 に
  公開取り下げで決着**。作業途中の成果物で、導出規則が無く、何もこのファイルから導出して
  いないため、公開 processed 層に残す根拠が無いと判断した。理由・代替・露出（v1.8.0〜
  v1.12.0 のアーカイブに含まれる）は `src/processing/reproduce.py` の `WITHDRAWN` に、
  引用元の注記は `docs/provenance/compound-taxonomy.md` にある。CHANGELOG エントリは
  次回リリース時に付ける（version-sync ゲートが `[Unreleased]` を許さない）。
- `docs/audits/*.json`（機械可読の監査報告）は再生成されないままレジストリから乖離
  している（例: `g7-study-inventory.json` は 9 study 中 7 件を `registered: false`
  と誤記録）。鮮度検査は未実装（Phase A 候補）。ただし G4 storage inventory には
  既に鮮度テストがある（`tests/validation/test_storage_inventory_audit.py`、
  §21.4 で本変更時に更新した）。

## 21. X 識別情報の封じ込めと施行（2026-10-13）

### 21.1 背景（文書化されていた方針が施行されていなかった）

`docs/specs/sns-redistribution-assessment.md` §1.4（2026-10-01）は「DOI アーカイブに
ツイート本文・ユーザー名・個別 URL を含めない」と定めていた。しかし施行する仕組みが
無かったため、該当 CSV は 2026-10-01 の追加以降 **全 14 タグ・全 14 Release** の
クリーンアーカイブに含まれ、Zenodo `10.5281/zenodo.23253840`（open access）にも
入ったまま公開された。露出範囲・経緯は
`docs/issues/closed/mitigated/20261013_p0_x-identity-published-in-all-releases.md`。

これは本フレームワークが何度も見てきた失敗形（規則はあるが検査が無い）の再発である。

### 21.2 決定（メンテナ、2026-10-13）

- **X は公開前に匿名化が必要**。YouTube は現状のままでよい。
- 原典はクラウドに保管されているため、本リポジトリ側のデータをマスキングしてよい。
- 既公開分の対応は **前向き修正（A）を主軸**とし、プラットフォームへの削除・制限依頼（C）は
  別途判断。履歴書き換え（B）は AGENTS.md「公開済みリリースを書き換えて隠さない」と
  矛盾し、fork/clone/Zenodo に残るため効果も限定的で、採用しない。

### 21.3 実施内容

- `x_cbx_202608_summary.csv` を追跡から外し、非公開の `data/private/` へ退避。削除は
  `processing.reproduce.WITHDRAWN` に理由・代替成果物・露出として記録（黙って消さない）。
  非公開入力を前提とする導出は新状態
  `reproducible_requires_non_published_input` として報告され、failure にはならない。
- 公開ページ 1 件と分析レポート 2 件のアカウント名を**文書内の通し記号**で疑似名化
  （文書間で対応が取れないようにし、リンクによる再識別を防ぐ）。
- 再発防止ゲート `src/validation/x_identity.py`:
  - `identity_column` — 追跡 CSV/TSV のヘッダが `username`・`author_name` 等を名乗る
  - `post_permalink` — `x.com/<handle>/status/<id>` のリンク（文書例の `user` 等は除外）
  - `known_handle` — `metadata/privacy/x-identity-denylist.json` のソルト付き
    SHA-256 照合。**denylist はダイジェストのみを保持**するので、ゲートはアカウントを
    再掲載せずに同名の再公開を検出できる
- 正式な例外は `x_identity.ACKNOWLEDGED` に `(path, digest)` で書き、理由を添える。
  一致しなくなった例外も failure（宣言の腐敗を検出）。YouTube の 2 件が該当。
- 施行点: CI `python -m validation.cli audit-x-identity`、pre-commit チェック 6
  （`PYTHONPATH=src python3 -m validation.x_identity`。`validation.cli` は cerberus を
  要するため、venv を前提としないフック専用の stdlib 入口を分けている）。

### 21.4 pre-commit フックの構造修正（本変更に必要だった）

検出ループが 1 本の `case` で書かれていたため、**最初に一致した分岐しか実行されず**、
processed CSV の変更ではスキーマ検証だけが走り、再現性検証と X 識別検査は黙って
省略されていた。検証は相互排他ではないので、`case` を検証ごとに独立させた。

### 21.5 実測（2026-10-13、Python 3.14）

- `pytest` **844 passed**（`tests/validation/test_x_identity.py` 15 件、
  `tests/processing/` の改訂を含む）。
- `audit-x-identity`: 552 ファイル走査中 0 findings、認められた例外 2、stale 0。
- `audit-processed`: 7 成果物、failure 0（`publication` 取り下げ 1 件を含む）。
- `audit-artifacts` を再生成（77 → 76 ファイル）。G4 鮮度テストが更新漏れを検出した。
- pre-commit フックでチェック 1/2/5/6 が実行され exit 0。

### 21.6 未実施（引き継ぎ）

- 既公開 Zenodo アーカイブ（v1.7.0 = `10.5281/zenodo.23095153`、v1.12.0 =
  `10.5281/zenodo.23253840`）の削除・制限は**不要と判断**（2026-10-13）。残存は受容済み
  のリスクとして記録する。GitHub Release はアセット 0 件で、タグ書き換えにより
  自動生成のソースアーカイブはクリーンになった。
- **履歴書き換え（B）は 2026-10-13 に実施**（`git filter-repo`。54 handle の全履歴置換
  ＋ 投稿 CSV の全パス変種と旧 logbook の全履歴除去）。作業ツリーのゲートでは検出
  できない対象（改名前パス、HEAD に無い logbook）があったため、履歴側にも検査が要る。
  経緯・副作用は `docs/issues/closed/mitigated/20261013_p0_x-identity-published-in-all-releases.md`。
- CHANGELOG エントリは新リリースと同時に付ける（`validate-version-sync.sh` は
  CHANGELOG の先頭見出しを最新タグと比較するため、`[Unreleased]` を先頭に置けない）。
- 影響アカウントへの通知の要否は未判断。
- `publication/guide_cbx_rewrite.html` の種別列から店舗地区（「麻布十番」）を除去した。
  ハンドル以外の残余識別情報（店舗地区等）の扱いは方針未定。

### 21.7 追記（2026-10-15）: 投稿単位の X データは匿名化後も公開しない

§21 は「識別子を落とせば公開してよい」という前提で匿名化版 CSV を公開対象にしていた。
2026-10-15 のメンテナ決定（`ISS-20261015-COL-030` §4.1）でその前提を閉じた。

- 施行（格納・追跡側）: `src/validation/x_identity.py` の `per_post_dataset`。追跡下の
  `datasets/` 配下ファイルの**構造**（列セット: `POST_RECORD_FIELDS` の 3 件以上）から
  投稿単位の表を検出する。列名の一覧はこのモジュールが単一の正本で、公開契約 PC-3 の
  散文規則も同じ一覧から派生する（規則を二重実装しない）。
- 施行（公開物側）: 公開契約 PC-3（`src/validation/publication_contract.py`、§22 の監査）。
- 成果物: `x_cbx_202608_summary_anonymized.csv` を `git rm` し、`src/processing/reproduce.py`
  の `WITHDRAWN` に理由・代替・露出（8 タグ + Zenodo DOI）を日付付きで記録した
  （`ISS-20261015-PUB-035`）。これで `DERIVATIONS` は空になり、再導出経路の検証は
  fixture テスト（`tests/processing/test_processed_artifacts.py`）に移った。
- 公開判断の記録: `metadata/publication/x-cbx-202608-summary-anonymized/decision.json` を
  `status: denied`（2026-10-15、根拠は §4.1 の決定文）に置き換え、2026-10-13 の approved は
  `notes` に残した。ゲート再実行の verdict は `BLOCKED`（PUB-10 FAIL = 公開拒否）。
  既公開アーカイブの取り下げは §21.6 の判断（不要 = 受容済み）を維持する。
- 語彙: 保存方針の `publication` は既存の `denied` を使う。`config/storage-policies.json` への
  新しい policy 追加は**しない**: その registry の次元は layer × source_kind であり、
  X 投稿単位と他の social 処理済み成果物を区別できないため、追加すると YouTube 等を
  誤分類する。判断は成果物単位の decision で表す。

## 22. Phase 6 本体配線（ゲートの回避防止）— 2026-10-13

### 22.1 判明したこと（実測）

- **実収集は framework を通っていない。** `src/collection/apify_run.sh` は
  `<actor_id> <input_json> <out_base>` で任意パスに生 JSON を書き、registry 参照・
  run identity・provenance・ゲートのいずれも無い。`fetch_tiktok.sh` /
  `fetch_instagram.sh` は `projects/automation/Apify/data/teiten_YYYYMMDD/` に書くが、
  **`projects/` はリポジトリに存在しない**（tracked 0 件）。
- framework の `collection.core.cli collect` は **offline replay 専用**（`--fixture`、
  「live collection is not executed here」）。adapter は `google_trends` のみで、
  X / YouTube / Instagram / TikTok 用 adapter は無い。
- `validate-all`（strict）は正しい規則を述べているが、凍結 29 run のため常に exit 1 で
  あり、**ゲートには使えない**（§12）。
- `src/collection/cron_gate.sh` は検証ゲートではなく**抽選スケジューラ**（1/24 確率）。
  名前だけが `gate` で、検証とは無関係。

つまり以前は、「実収集が `datasets/` に直接着地しても誰も止めない」状態だった。

### 22.2 採用した規則（CI で施行できる形）

凍結 legacy 29 run は**租父条項**。それ以外の run は**現行契約**（`collection-run-v1`、
参照整合を含む）を満たさなければならない。

```bash
python -m validation.cli audit-new-runs   # exit 0 = 非凍結 run はすべて適合
```

- 実装: `src/validation/new_runs.py`。読取専用。
- 実測: 29 run（すべて凍結）/ new 0 / failures 0。`frozen_legacy_seen` を報告するので、
  規則が何も照合しなくなった場合は見える（非空性の明示）。
- 迂回した run は provenance を欠くため通れない（合成 run で `REQUIRED_FIELD_MISSING`
  を実測）。
- 参照整合は `registries` を渡したときだけ効く。`test_reference_checks_are_what_registries_add`
  がその差を固定している（未登録 study を名乗る構造適合 run は registries 付きでのみ落ちる）。

### 22.3 収集側の fail closed

`apify_run.sh` は出力先が**このリポジトリの `datasets/` 配下**なら exit 2 で拒否し、
staged → `adopt` を案内する。パスは字句的に正規化するため `./datasets/x`・
`a/../datasets/x`・`/abs/.../datasets/x`・`datasets` 自身も拒否される（実測）。
シンボリックリンクは解決しない（既知の限界）。引数検証は認証チェックより前に
置いたため、credentials 無しでも不正な出力先を弾ける。

### 22.4 未実施（引き継ぎ）

- **shell / skill を staged 出力 → `adopt` へ移行する本体作業は未実施。** `adopt` は
  staged ディレクトリに conformant な `run_metadata.json` を要求し、それは plan
  （query registry + window compile）と collector id を要する。X / YouTube 等には
  adapter がまだ無いので、まず adapter が必要。§22.2 のゲートは「迂回を検知して止める」
  側であり、迂回せずに収集できるようにする側ではない。
- `cron_gate.sh` が書く `projects/` はリポジトリに存在しない。この定点観測経路が現役か
  どうかの確認が必要。
  → **2026-10-15 に不要（retired）と判定し RESOLVED**（`ISS-20261015-COL-019`）。
  根拠: `projects/` の tracked 0 件、呼び出し chain の二重破損
  （`$DIR/fetch_*.sh` も `$DIR/apify_run.sh` も存在しない）、crontab・CI 参照 0 件、
  Instagram 定点の 2026-10-01 廃止。`cron_gate.sh` は retired stub（exit 2・無書込）化し、
  `fetch_tiktok.sh` / `fetch_instagram.sh` は既定拒否＋`TEITEN_OUTDIR` 明示のみ許可
  （明示指定でも `datasets/` / `projects/` 配下は拒否）。ガードは
  `tests/collection/test_cron_gate_guard.py` が固定する。
- pre-commit フックの軽量検査は実装済み（ISS-20261015-COL-020、2026-10-15）。方針は
  「縮小検査を入れる」: `src/validation/staged_runs.py` が staged の
  `datasets/*/data/raw/*/*/run_metadata.json` を Git index から読み、stdlib だけで
  JSON 可読・`run_id`（非空文字列）・新規 run の最小 provenance キー存在
  （`study_id` / `source_id` / `collector.collector_id` / `collector.adapter_id` /
  `collection_started_at` / `query_provenance.query_id` / `execution.status` /
  `execution.returned_count` / `execution.errors`）だけを確認する。凍結 legacy は
  `validation.legacy.LEGACY_RUN_IDS` を正本として免除し、新規扱いの再分類はしない。
  型・temporal・参照整合・artifact 照合などの完全検証は CI の `audit-new-runs` が担う
  （`validation.pipeline` が cerberus を要するためフックには入れない方針を維持）。
  フック出力と `tests/validation/test_staged_runs.py` がこの分担を固定している。

### 22.5 関連する未決（本作業中に発見）

- `docs/audits/g6-publication-eligibility.json` の `verdict: BLOCKED`（PUB-01 provenance
  欠落 / PUB-04 personal-data review 欠落 / PUB-10）と、対象成果物（匿名化済み X CSV）
  が公開されている状態の不整合は、**2026-10-15 に ISS-20261015-PUB-015 として解消**
  （メンテナ指示: ゲートを再実行して verdict を更新）。

  再実行の結果は `BLOCKED` → `CONDITIONAL`（公開は拒否されない。PUB-06/07/08 の
  レビュア確認が残る）。判定履歴を非公開の会話に依存させないため、審査 envelope は
  `metadata/publication/<artifact_id>/{artifact,evidence,decision}.json` として追跡し、
  判定は登録コマンドで再現する（`tests/validation/test_audit_report_freshness.py` が
  再実行一致と承認 hash のピン留めを検査する）。

  **ゲートと公開状態の関係（変更なし、明文化）**: `gate-publication` は record-only で、
  公開・Release 作成・Zenodo アップロード・DOI 発行を一切行わない。したがって
  「verdict が何であれゲートが公開を止める」のではなく、**公開を止めるのは AGENTS.md の
  公開ゲート規則を人が適用する場合**である。判定が `BLOCKED` のまま公開が続く状態が
  問題だったのは、未確認が失敗と区別できず、受容の記録も無かったため。現在は
  CONDITIONAL（拒否なし）+ 残作業（PUB-06/07/08）が記録されている。

  記録の解釈（要確認）: 専用の承認文書が存在しないため、`decision.json` は
  §21.2（メンテナ決定 2026-10-13）を匿名化済み成果物の公開承認として転記した。
  別の形にする場合はその 1 フィールドと再実行で変更できる。

## 23. タクソノミーと文書の整合（2026-10-13）

### 23.1 見つかった欠陥（最大のものは当初の想定外）

1. **JSON の重複キーによる無言のデータ欠落。** 両 SKOS ファイルは 1 概念につき
   `skos:prefLabel` を 2 回書いており（`en` と `ja`）、JSON は重複キーを後勝ちで読むため
   **英語ラベル 38 件（compound 24 + content 14）がパース時に消えていた**。公開済みの
   `exports/taxonomy/compound-taxonomy.ttl` の英語 `prefLabel` は **0 件**で、ソースは 24 件を
   宣言していた。CI の export 同期検査は、エクスポータも `json.load` を使うため同じ欠落を
   忠実に再現しており、**検知できなかった**（同じ入力から同じ出力を作る検査は、入力の
   解釈が壊れていても通る）。
   - 修正: 複数値を配列にする（SKOS JSON-LD の正しい形）。
   - 副次効果として Schema.org エクスポートの `schema:name` が日本語から英語に変わり、
     日本語が `schema:alternateName` に入った。これは**エクスポータ本来の設計**
     （`schema:name = pref_label_en or pref_label_ja`、`alternateName = pref_label_ja`）が、
     英語が常に空だったため黙って fallback していたものが復旧したもの。重複していた
     `schema:alternateName`（例: H4CBH が 2 回）も解消した。
2. `docs/data-dictionary.md` §6.4 は 3 カテゴリ 7 化合物のみを載せ、カテゴリ ID も独自
   （`major_phytocannabinoid`）だった。taxonomy は 6 カテゴリ 18 化合物。
   → taxonomy を正本として写し直した。
3. `compound_rare` が空で説明も無く、欠落と読めた。→ `skos:scopeNote` に「意図的に空」と
   明記（他の 5 カテゴリにも scopeNote を追加。全 6 カテゴリが説明を持つ状態にした）。
4. `iptc-mapping.yaml` は 38 概念中 15 のみ対応し、残り 23 について何も言っていなかった。
   → `coverage` 宣言を追加（mapped ∪ deliberately_unmapped ∪ not_applicable が全概念を
   重複なく覆う）。
5. `research/google-trends/20261004-google-trends-compound-summary.md` は THCH を
   「ヘキサカンナビノール類」と記載していた（taxonomy にも化学クラスとしても存在しない
   名称）。→ taxonomy と同じマイナー・フィトカンナビノイドに修正し、同列が**化学クラス**で
   あり taxonomy の分類（**製造経路**）とは別語彙である旨を表の下に明記した。

### 23.2 施行（規則）

- `src/validation/json_hygiene.py` ＋ `tests/validation/test_json_hygiene.py`:
  **追跡された JSON / JSON-LD に重複キーが無いこと**（全 156 ファイルを走査）。重複は
  無言のデータ欠落なので、キーごと・囲んでいる概念名つき（`skos:notation` / `@id`）で報告する。
- `tests/validation/test_taxonomy_consistency.py`:
  §6.4 ＝ taxonomy、空カテゴリは `skos:scopeNote` 必須、IPTC coverage が全概念を覆う、
  **公開 TTL が en / ja 両方の `prefLabel` を持つ**。
- YAML パーサは導入していない（本リポジトリの第三者依存は cerberus のみ）。`iptc-mapping.yaml`
  の coverage は厳格なテキスト読取で検証し、構造が読めなければ failure にする
  （`processing/rulespec.py` と同じ方針）。

### 23.3 実測（2026-10-13、Python 3.14）

- `pytest` **889 passed**（+14: json_hygiene 8 / taxonomy_consistency 6）。
- TTL の英語 `prefLabel`: compound **0 → 24**、content **0 → 14**。
- export 同期検査（CI と同一手順）: 6 ファイルすべて一致。
- `validate-registries` 11 valid / `audit-new-runs` failures 0 / `audit-processed` 7 成果物 /
  `validate-data-schema` PASS 45・FAIL 0 / `validate-version-sync` PASS 12・FAIL 0 /
  research pages 全ページ最新 / `audit-x-identity` 0 findings。

### 23.4 未実施（引き継ぎ）

- IPTC の 17 末端概念（化合物 9 / intent 4 / format 4）は未対応のまま。対応可否は IPTC 語彙の
  確認後に判断する（推測で対応付けない）。
- **化学クラスと製造経路クラスの 2 語彙は、2026-10-15 に判断済み（ISS-20261015-TAX-026、オーナー選択肢 (a)）。**
  化学クラスを taxonomy の第 2 次元として持つ: 製造経路・由来の次元は `jptr:compound-taxonomy`
  に残し、化学クラスは `metadata/taxonomy/chemical-class-taxonomy.skos.jsonld`
 （`jptr:chemical-class-taxonomy`）に置く。結合は対称 `skos:related` のみで行い、
  `skos:broader` / `skos:narrower` は次元を跨がない。形式化したのは根拠のある 2 クラスのみ
 （水素化: HHC・HHCH・H4CBH・HHBD、アセテート体: THC-O）。研究文書側の語彙は独自語彙として残し、
  構造不明の CRDP / CRDH に対する「ヒドロキシ酸類似体」は採用しない。IPTC Media Topics に
  化学構造クラスは無いため `iptc-mapping.yaml` では `not_applicable` として宣言し、推測で
  対応付けない。2 次元の分離は `tests/validation/test_chemical_class_dimension.py` が検査する。
- `compound_rare` の会員（CBDP / THCP 等）は未登録のまま維持する（ISS-20261015-TAX-027 判断 2026-10-15、issue は OPEN のまま）。
  リポジトリ内の証拠は scopeNote の例示名・COA パネルの THCP（ND）・汎用リストの言及のみで、
  収集 run・query-registry・queryDesign・regulatory-status 記録が無いため、日中ラベル・外部 ID・IPTC 対応の
  創作が必要になり見送る。追加の gate と証拠棚卸しは `docs/provenance/compound-taxonomy.md` の TAX-027 節に記録し、
  空・説明付きの状態は `tests/validation/test_compound_rare_membership.py` が固定する。

## 24. 未解決 issue の棚卸しと施行（2026-10-13）

### 24.1 施行（規則）

- `src/validation/issues.py` ＋ `validation.cli audit-issues` ＋ CI:
  `docs/issues/` の全ファイルが issue レコードであること（`ID` / `優先度` / `ステータス`）、
  優先度の整合（P0=Critical、P1=High）、**終端ステータスは決定日を伴うこと**、
  ID が重複しないこと、そして **OPEN な P0 は failure**（解決するか、PENDING/MITIGATED として
  理由を記録する）。P1 以下は報告のみ（研究バックログは正常状態であり欠陥ではない）。
- 検査結果: 23 issue、OPEN 9、**OPEN P0 0**、OPEN P1 6、malformed 0、failures 0。
- **却下した検査**: issue が参照するパスの実在確認。実測で 60 参照中 24 が設計上存在しない
  （削除済み成果物、保持していない raw、裸のファイル名）ため、ノイズにしかならない。

### 24.2 ディレクトリの意味の修復

`docs/issues/` に issue でない文書が 3 件混在していた（HTML バリデーション報告、データ品質
改善の指示書、X 収集 Actor の検証報告）。`docs/reports/` を新設して移動し、
`docs/reports/README.md` に各ディレクトリの意味と検査の有無を記録した。これで
`docs/issues/` が「issue レコードのみ」を意味するようになり、規則が例外なしで適用できる。

### 24.3 閉じた P0（2 件）

- `20261002_p0_version-doi-mismatch` → **RESOLVED**。報告された 12 件は解消済み。ただし
  同種の欠陥が生存していた: `metadata/datapackage.json` のトップレベル `.doi` が
  **v1.11.0 の DOI**（`10.5281/zenodo.23243495`）のまま `version: 1.12.0` と共存し、同じ
  ファイルの `citation` 文字列と**自己矛盾**していた。release-time スクリプトは
  `citation` 文字列中の DOI しか見ていなかったため **PASS 12 / FAIL 0** と報告していた。
  修正（DOI 更新）+ スクリプトに `.doi` 検査を追加（修正前は意図的に FAIL することを実測）
  + **タグも network も使わない内部整合テスト**（CI 施行）。
- `20261002_p0_unapplied-self-corrections` → **RESOLVED**。4 件中 3 件は既に修正済み
  （各ファイルに日付付き注記あり）、1 件（26週レポートの W23/W26 と総件数）が残っていたため
  修正。値の根拠は `cbx-social-trends/methodology.md` §2.1/§7.3 の再収集記録で、**週次合計と
  月次合計がともに 321 で一致することを検算**した。issue が示していた対象パスも誤っていた
  （`cbx-social-trends/analysis/` → 実際は `x-26week-trends/analysis/`）。

### 24.4 未解決 P1 の棚卸し（判断待ち・研究内容に踏み込むため未修正）

5 件が「公開ページ／戦略文書の数値・カバレッジが実データを過大評価している」という同型で、
いずれも 2026-10-13 時点で対象ファイルに記載が残っている（実測）。

| issue | 現在の記載 | 実データ側の制約 |
|---|---|---|
| `20261012_p1_cbd-coverage-matrix-overstates-completeness` | `research/strategy/20261008-compound-research-matrix.md` L54「CBD 9/9 100% 🟢A 全ソース完備」 | X の期間指定 run は実測 2026-10 に集中（`cbd-1year` 0 件）、YouTube 2025 欠落、COA raw 不在、GT 5年は summary のみ |
| `20261012_p1_cbd-research-page-count-period-mismatch` | `publication/research_cbd.html` が X 期間を「2026-10-01（1日間）」と「2026-07-01〜2026-10-01」の両方で記載 | 投稿 timestamp は短期間に集中 |
| `20261012_p1_cbd-x-period-provenance` | run 名が 1年 / 1ヶ月 / 期間指定を示す | metadata に query・観測期間が無い run があり、長期系列として検証できない |
| `20261012_p1_cbd-youtube-10year-incomplete` | 旧10年系列は証拠・公開対象外 | 採用済み Apify CBD 2 runs を別系列として扱う（宣言ファイルを正とする） |
| `20261012_p1_cbd-coa-source-mismatch` | 公開ページが参照する COA | raw ディレクトリに該当なし |

**選択肢（研究判断を含むため本作業では決めない）:**

- **(i) 評価を修正**: マトリックスの CBD 評価を実データの制約に合わせて下げる。研究戦略の
  結論そのものが変わる。
- **(ii) 制約を併記して評価は残す**（推奨）: 評価が「プラットフォームの有無」を指すことを
  明示し、期間系列・来歴・再現性の制約を併記する。結論は変えず、AGENTS.md の
  「観測・派生・解釈を分ける」に沿う最小の修復。
- **(iii) 再収集して埋める**: X の期間指定・COA を再収集し、実際に充足させる。
  ライブ収集の承認が必要（§22.4 の adapter も前提）。

> **2026-10-16 追記:** `20261012_p1_cbd-youtube-10year-incomplete`（CBD-003）は除外方針で RESOLVED。旧10年系列は上記 (ii) の併記対象・(iii) の再収集対象としない。採用済み YouTube 証拠は宣言ファイルの別系列 runs を正とする。

---

## 25. 監査スナップショットの鮮度規則（ISS-20261015-AUD-028、2026-10-15）

### 25.1 規則（1 つだけ）

**コミットされる監査スナップショット（`docs/audits/*.json`）は、追跡ファイルだけで
再生成できなければならない。** ローカルのディスク状態に依存する事実は、次のどちらかに
寄せる。

| 扱い | 適用先 | 実装 |
|---|---|---|
| (a) **追跡対象の事実に置き換える** | g7 study inventory の `data_file_count` | `private` を**名前で除外**（`src/research/audit.py`）。gitignored な `data/private/` の中身はチェックアウトごとに違い、公開レポートに現れる理由も無い。境界の存在は `audit-private-catalog` が扱う（**内容は数えない**） |
| (b) **生成側で committed-safe にする** | g6 private catalog の `exists` / `present` / `absent` | `src/validation/private_catalog.py`: 既定出力は `exists: null` / `present: null` / `absent: null`＋`include_local_state: false`（checkout 非依存。`make audit-snapshots` はこの mode）。checkout の実在を見たい場合は `audit-private-catalog --include-local-state`（ローカル専用、コミット不可）。鮮度検査は normalizer なし（`identity`）の完全一致に戻し、`boundary_only` normalizer は廃止（ISS-20261016-MNT-002） |
| 既存の先例 | g6 git tracking の `state_summary` / `count` | normalizer `tracked_only`（`ignored` / `absent` も排除）。**追跡されているかどうか**はリポジトリの事実 |

- 検査は `tests/validation/test_audit_report_freshness.py` の **1 つの登録表**（`REPORTS`）
  が持つ。新しいレポートは登録しないと落ちる。
- ローカルの disk 事実を検証したい場合は、既定の committed-safe 出力とは別の明示的な
  opt-in 経路（`--include-local-state` 等）にし、スナップショット側には混ぜない。
  **「このマシンでしか green にならない」検査を増やさない。**
- 個人入力（`datasets/*/data/private/`）からしか再導出できない検証は、既存の
  `requires_source` マーカー（`tests/processing/test_processed_artifacts.py`）と同じく
  **スキップ**にする（private 入力がある環境では実行される）。

### 25.2 実測（2026-10-15）

- clean checkout（private ディレクトリ無し）での `pytest` は 3 件失敗していた:
  `test_stale_declaration_is_reported`（private 入力が無いと `reproduce_artifact` が
  `FileNotFoundError` を送出。`source_published=False` の導出に対してテストだけが
  既定値 `True` の `Derivation` を作っていた）、g6-private-catalog 鮮度、g7 鮮度。
  CI（`38587265312` / `38628877292`）も同じ 3 件で停止していた。
- 修正後は clean checkout でも**スキップのみ**（private 入力に依存する検証は実行される
  環境で走る）。「ローカルで green でも CI は落ちる」状態は解消。
