# Validation Framework (Cerberus) — セットアップと運用

研究データ契約（G1〜G7）の構造検証フレームワーク。
仕様書: `docs/plans/20261013h.md`（ローカル計画書。`docs/plans/` はgitignore対象のため
リポジトリ履歴には含まれない）。

## 現状（2026-10-13 時点）

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | 既存環境監査 | 完了（監査結果は下記 §8） |
| Phase 2 | 依存導入・共通Validator・G5スキーマ・Contract Tests | **実装済み** |
| Phase 3〜8 | Schema Registry拡充 / Semantic / CLI / Pipeline / CI / Legacy Audit | 計画のみ（未実装） |

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

- Contract Tests: `tests/validation/`（2026-10-13 時点: 76件）。
- 新しいスキーマを登録したら、対応する Contract Test を必ず追加する
  （20261013h.md §9 / §16）。

## 4. ライブラリとしての利用

```python
from validation.core import validate_document
from validation.schema_registry import get_schema

result = validate_document(document, get_schema("collection-run-v1"))
```

- `cerberus` を import してよいのは `src/validation/core.py` のみ。
- 共通設定: `allow_unknown=False` / `purge_unknown=False` / `normalize=False`。
  検証は入力ドキュメントを変更しない（raw不変原則）。
- スキーマ側で意図的に許可した拡張領域のみ `allow_unknown=True`
  （`environment`、`temporal_provenance.submitted_parameters`）。

## 5. CLI（Phase 5 で実装予定 — 現在未実装）

```bash
.venv/bin/python -m validation.cli validate \
  --schema collection-run-v1 \
  --file datasets/<study>/.../run_metadata.json
```

- 目標 Exit Code: 0=成功 / 1=データ検証失敗 / 2=スキーマ・設定エラー /
  3=ファイルI/Oエラー（20261013h.md §13）。
- CLI 実装までは §4 のライブラリ利用または pytest を利用する。

## 6. CI（Phase 7 で統合予定 — 現在未統合）

予定構成:

```yaml
# GitHub Actions
- uses: actions/setup-python@v5
  with:
    python-version: "3.14"
- run: python -m pip install -e ".[dev]"
- run: python -m pytest
- run: python -m validation.cli validate-registries
```

- CI では `.venv` を作らない（ランナーの Python に直接インストール）。
- 非公開 raw を CI へアップロードしない。
- JSON Schema Draft 2020-12 との整合性検証を CI に含める（20261013h.md §17）。
- **決定（2026-10-13）**: CI の Python は **3.14**（開発機と同一）。ローカルと CI の環境差を
  減らすことを優先する。`requires-python` の下限 3.12 は互換性表示として維持する。

## 7. 責務分離（重要）

Cerberus は**構造検証のみ**を担当する。

| 検証対象 | 担当 |
|---|---|
| 必須項目・型・値域・列挙値・ネスト・余分なフィールド | Cerberus（本フレームワーク） |
| Compound / Query / Source / Collector の Registry 存在 | Registry Validator（Phase 4） |
| 日時・期間境界の前後関係 | Temporal / Semantic Validator（Phase 4） |
| Query と Source の整合性 | Semantic Validator（Phase 4） |
| ファイルハッシュ | Integrity Validator（Phase 4） |
| Artifact 参照関係 | Lineage Validator（Phase 4） |
| Git 追跡状態 | Git Policy Validator（Phase 4） |
| 公開承認・研究上の比較可能性 | Publication / Comparability Gate（Phase 4） |

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
4. Registry に新スキーマを登録した場合は Contract Test を追加する。
5. 既存 raw・旧 metadata・Git 履歴を変更しない。
