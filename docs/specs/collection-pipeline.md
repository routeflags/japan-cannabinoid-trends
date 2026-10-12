# Collection Pipeline (G1 垂直スライス) — 運用契約

**版:** 0.1.0（2026-10-13）
**仕様:** `docs/plans/20261013a.md`（G1、リポジトリ履歴外）+ `20261013h.md` §12
**状態:** 実装済み・**ライブ収集は未実施**（契約検証は録画リプレイ / 合成 fixture）

G1 の垂直スライスを Google Trends 1 ソースで貫通させた実装の運用契約。
検証フレームワーク本体は `docs/specs/validation-framework.md` を参照。

---

## 1. 全体フロー

```text
Collection Plan (collection-plan-v1)
      |
      v  python -m collection.core.cli collect
Source / Collector Registry (config/sources.json, config/collectors.json)
      |
      v  select_collector  (capability gate; unknown は自動選択しない)
Capability / Selection Gate (fail closed)
      |
      v  adapter.validate_plan
Source Adapter (G1 §8 contract)
  └─ transport: live (SessionMcp) / recorded replay
      |
      v
.staging/<run-id>/            payload / artifact manifest / run_metadata
      |
      v  validation.cli gate-run  = L1
Schema + Provenance + Hash + Missingness + Completeness
      |
      +-- FAIL --> .quarantine/<run-id>/  (raw 保全 + quarantine-reason.json)
      |
      v
<datasets-root>/<study>/data/raw/<run-id>/   (catalog)
      |
      v  validation.cli compare-runs  = L2 (C1/C2/C3)
      +-- not_comparable --> 採用は維持、比較不可を別途報告
```

L1（正しさ）と L2（比較可能性）は独立して判定する（G1 P5）。採用済み run でも
L2 が `not_comparable` になることはある。

---

## 2. レジストリ

| ファイル | スキーマ | 内容 |
|---|---|---|
| `config/sources.json` | `source-registry-v1` | source の性質（kind / measurement_types / publication_review_required）。秘密情報は置かない |
| `config/collectors.json` | `collector-registry-v1` | 実際の収集手段（provider / transport / external_id / adapter_id / version / status / capability 三値 / evidence） |

- capability は `supported` / `unsupported` / `unknown` の三値（G1 §7.2）。
  **未確認を `unknown` のまま保つ**（推測で `supported` にしない）。
- status は `active` / `legacy` / `deprecated` / `unverified` / `disabled`。
  新規収集に使えるのは `active` のみ。
- 証拠は `evidence[]` にファイルパスで記録し、台帳は
  `docs/provenance/collector-inventory.md`。
- どの collector を登録してあるか（2026-10-13 時点）: `google-trends-mcp`
  （active）のみ。他ソースの collector は `unverified`（capability 全 unknown）
  で登録済みだが、**新規収集には使えない**（capability 検証後に昇格する）。

---

## 3. Adapter Contract（G1 §8）

実装: `src/collection/core/contracts.py`（Protocol + 検証関数）。

| 要素 | 内容 |
|---|---|
| 識別 | `adapter_id` / `source_id` / `collector_id` / `version`。pipeline が collector registry と照合（不一致は停止） |
| `capabilities()` | registry に記録された三値をそのまま返す。pipeline が registry と完全一致を検証（adapter が自分を昇格できない） |
| `validate_plan(plan)` | adapter 固有の事前検証（未確認 timeframe の拒否など） |
| `collect(plan)` | transport 経由の取得。失敗は `status=failed`＋errors の結果として記録（**0 件への変換禁止**） |
| `extract_observations(raw)` | ソース固有のレスポンス解析。コアはソース形状を知らない |
| `describe_execution()` | 非秘密の実行情報（tool / version / collection_mode） |
| transport | live（MCP セッション callable 注入）と recorded replay（fixture）を分離。replay は fixture 記載の request と一致しない呼び出しを拒否 |

- コア（`src/collection/core/`）にプラットフォーム名は置かない（P1）。
  adapter 解決表は `src/collection/adapters/__init__.py` のみ。
- 新規ソース追加手順: ①registry に source/collector を登録 → ②
  `src/collection/adapters/<source>/` に Contract 実装を追加 → ③契約テスト
  （`tests/collection/`）を追加 → ④ capability を実測して registry を更新。
  コアの改修は不要（a.md §15 の架空ソーステストで検証済み）。

### 3.1 既存 shell 収集（`src/collection/*.sh`, `scripts/collect-youtube-*.sh`）との整合

- 今回は既存 shell を書き換えていない。移行パスは
  「staged ディレクトリ（`run_metadata.json` + artifact）を出力し、
  `python -m collection.core.cli adopt --staged <dir>` に渡す」方式（判断 A、
  親の承認待ち）。
- `scripts/validation/run-gates.sh run <run_metadata.json>` は新しく L1 ゲート
  （`gate-run`）を呼ぶ: exit 0 = 採用可、非 0 = 隔離。

---

## 4. Run Manifest / Provenance

`src/collection/core/provenance.py` が staging 内に 3 ファイルを生成する:

| ファイル | スキーマ | 生成方法 |
|---|---|---|
| `payload.json` | （adapter が宣言する payload schema ID） | transport が返したレスポンスをそのまま保存 |
| `artifact-manifest.json` | `artifact-manifest-v1` | **実ファイルから** SHA-256 / byte_length を計算 |
| `run_metadata.json` | `collection-run-v1` | 既存必須 9 項目を維持（対応表: モジュール docstring / 下記） |

既存 9 項目（e.md §4.1）のマッピング: `run_id`→`run_id` / `study_id`→`study_id` /
`source`→`source_id` / 収集手段→`collector.*` / `collection_timestamp`→
`collection_started_at` / `queries`→`query_provenance` / 件数→
`execution.returned_count` / `purpose`→`purpose` / エラー→`execution.errors`。

秘密情報: `submitted_parameters` は adapter が許可リスト方式で組み立てる
（tool / terms / geo / timeframe のみ）。env ファイルや token は保存しない。

---

## 5. L1 — Collection Integrity

実装: `validation.cli gate-run` / `validation.gates.post_collection_gate`。

| L1 | 項目 | 実装 |
|---|---|---|
| L1-01〜03 | Source/Collector/Adapter 登録・一致 | `semantic.check_registry_references` |
| L1-04 | Metadata Schema | `validate_full`（構造→意味の順） |
| L1-05 | 必須来歴 | 構造 + temporal + execution + manifest run_id 一致 |
| L1-06/07 | raw 存在・SHA-256 | `integrity.verify_artifact_manifest`。終端 status は manifest 必須（欠落は FAIL） |
| L1-08 | 件数・ページング | `semantic.check_execution_consistency` |
| L1-09 | 欠測とゼロの区別 | `semantic.check_missingness_consistency`（下記） |
| L1-10 | 秘密情報 | `semantic.scan_for_secrets` |

L1-09 の規則:

- 終端 status は「raw artifact の存在」が必須（証拠なしは FAIL）。
- `success` + `returned_count=0` は `record_count: 0` の artifact でのみ受理
  （**取得失敗をゼロ観測として記録しない**）。
- `success` と `partial`/`missing` な raw artifact は矛盾。
- `failed` は errors 記録必須。failed run は**カタログせず隔離**（raw 保全）。

---

## 6. Quarantine（暫定規約 - 親の判断待ち）

`docs/plans/20261013a.md` §13 の記載に従った暫定実装:

- 場所: `<workspace>/.quarantine/<run-id>/`（staging は `<workspace>/.staging/<run-id>/`）。
  両方とも `.gitignore` 済み。
- 内容: 取得した全ファイル + `quarantine-reason.json`（run_id / 時刻 / issues / contains_secrets）。
- 上書き禁止（staging / catalog / quarantine のいずれかに同じ run_id があれば停止）。
- 自動削除しない。秘密情報検出時は `chmod 700`（＋理由フラグ）。
- **未決**（親・ユーザーの判断事項）:
  - (A) 現行案（repo 内 `.quarantine/`、ローカル FS）の維持
  - (B) repo 外の保護パスへの分離
  - 保持期間・削除レビュー手順・アクセス制御の正式化（G1 P6-4 は未設計）。

---

## 7. L2 — Research Comparability（最小実装）

実装: `validation.comparability.compare_runs` / `validation.cli compare-runs`。

| 条件 | 判定 |
|---|---|
| C1 | `compound_id` / `query_id` / `submitted_query` の不一致 → `not_comparable` |
| C2 | `temporal_provenance`（window / granularity / timezone / week_start / time_axis）→ `compare_temporal_windows` を再利用 |
| C3 | `source_id` 不一致（単位の代理）→ `not_comparable`。同一 source で collector のみ不一致 → `conditional` |

- 現時点の最強判定は `conditional`（coverage / sampling レビューが必要なため
  `comparable` は未実装。既存方針どおり）。
- 現時点では direct comparison のみモデル化。cross-source を正規化パターン
  比較するような研究目的は将来対応（purpose 未対応は `unknown` で返す）。
- run metadata は unit ラベルを持たない（G7 measurement registry 導入時に整合
  を取る）。

---

## 8. コマンドと exit code

```bash
# 収集（offline replay。ライブは MCP セッション承認後）
python -m collection.core.cli collect --plan plan.json \
  --fixture <recorded_response.json> \
  --workspace <root> --datasets-root <root>/datasets

# 外部 collector が staging に出した run の採用判定
python -m collection.core.cli adopt --staged <staging>/<run-id> --workspace <root>

# L1 単体（任意の run ディレクトリ）
python -m validation.cli gate-run --file <run_metadata.json>

# L2（run ペア）
python -m validation.cli compare-runs --a a.json --b b.json
```

| exit | 意味（collect / adopt / gate-run） |
|---|---|
| 0 | adopted（catalog） |
| 1 | quarantined / stopped（採用しない。raw は保全） |
| 2 | 設定エラー（registry 不正、adapter 未実装、plan 不正） |
| 3 | I/O エラー |

`compare-runs` は常に 0（比較判定は採用可否のゲートではない）。

---

## 9. 制限事項と引き継ぎ

- **ライブ収集は未実施**。Google Trends の live 経路（`SessionMcpTransport`）は
  MCP セッション callable の注入のみ実装し、本リポジトリは実行しない。
- replay fixture は合成（録画形式に基づく）。実レスポンス形状との最終照合は
  ライブ収集承認後のタスク。
- 既存 shell / skill（`research-google-trends` 等）への強制適用は未実施
  （移行は親の判断）。
- G2（query registry）・G7（study / measurement registry）導入時は、
  plan の `query_id` / `study_id` 参照検証が自動で有効になる（CLI の
  `--metadata-dir` に registry が置かれればよい）。
