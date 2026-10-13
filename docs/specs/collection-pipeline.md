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
      v  window registry 照合 (metadata/windows; 不一致は停止)
Temporal Contract (絶対 window の正本性確認)
      |
      v  Window Compiler (collector 別。表現不能は fail closed = P6)
Compiled Window (parameters / exact / limitations)
      |
      v  adapter.validate_plan / adapter.collect
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
      v  validation.cli compare-runs  = L2 (C1/C2/C3、--coverage-* で T6/T7)
      +-- not_comparable --> 採用は維持、比較不可を別途報告
      |
      v  validation.cli coverage-run  = G3 §9 coverage manifest (report)
```

L1（正しさ）と L2（比較可能性）は独立して判定する（G1 P5）。採用済み run でも
L2 が `not_comparable` になることはある。

---

## 2. レジストリ

| ファイル | スキーマ | 内容 |
|---|---|---|
| `config/sources.json` | `source-registry-v1` | source の性質（kind / measurement_types / publication_review_required）。秘密情報は置かない |
| `config/collectors.json` | `collector-registry-v1` | 実際の収集手段（provider / transport / external_id / adapter_id / version / status / capability 三値 / evidence） |
| `metadata/windows/*.json` | `temporal-window-v1` | G3: 絶対期間の正本（ファイル名 = window_id、UTC 保存・半開区間）。plan が同名 window_id を名乗る場合は完全一致を要求 |
| `metadata/artifacts/artifact-registry.json` | `artifact-registry-v1` | G4: `schema_id` / `artifact_type` / `format` → `reader_id` の対応表（readers / artifact_schemas）。L1 の storage contract 検査（S7/S8/S9）と監査の reader 注釈がこれを使う |

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

### 3.2 Window Compiler（G3 §6）

- 実装: `src/collection/adapters/google_trends/compiler.py`（collector 別）。共通
  プリミティブは `validation/windows.py`（platform 名は adapters のみ = P1）。
- `collect` は収集前に plan の絶対 window を compile し、結果を `query` 拡張
  領域へ source-agnostic にマージする。plan が同キーに非空の異なる値を宣言して
  いれば `WINDOW_TIMEFRAME_CONFLICT` で停止（P6: 期間の無断切替なし）。
- 拒否は fail closed: `WINDOW_NOT_REPRESENTABLE`（候補 timeframe なし・時代不一致・
  絶対能力 supported なのに実装なし）。`window.exact_required: true` の plan は
  `exact=false` の collector では `WINDOW_EXACTNESS_UNAVAILABLE` で停止。
- ドライラン: `python -m collection.core.cli compile-window`（収集しない）。
- 現在 `exact=false` / `boundary_semantics=unverified` は Google Trends の
  ローリング期間の実測検証が未実施であることを反映する。

### 3.3 既存 shell 収集（`src/collection/*.sh`, `scripts/collect-youtube-*.sh`）との整合

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

G4 以降の補足: manifest には任意フィールド `contains_full_timeseries` /
`page_index` / `artifact_group_id` / `database` / `artifact_groups` を記録できる
（後方互換。要約とフル時系列の区別、ページ分割、SQLite lineage のための枠）。
L1 は引き続き `artifact-manifest-v1` の構造 + SHA-256 / byte_length を検証し、
さらに storage contract（S1/S6-S12: 内容 format 照合・reader 登録・record_count・
ページング整合・SQLite lineage）を適用する。詳細は
`docs/specs/validation-framework.md` §17。

既存 9 項目（e.md §4.1）のマッピング: `run_id`→`run_id` / `study_id`→`study_id` /
`source`→`source_id` / 収集手段→`collector.*` / `collection_timestamp`→
`collection_started_at` / `queries`→`query_provenance` / 件数→
`execution.returned_count` / `purpose`→`purpose` / エラー→`execution.errors`。

G2 以降の補足: `query_provenance.compound_id` は compound-taxonomy の notation
（例 `compound_cbx`）を使い、registry 読込時は `query_registry_version` も記録
する（b.md §7。registry が無い場合は記録しない — 推測しない）。

G3 以降の補足: window compiler が動いた run は `temporal_provenance` に
`reference_time`（相対期間の解決基準時刻）と `limitations`（exact=false の理由）
を記録し、観測側は応答系列の bucket label 範囲を `observed_min_timestamp` /
`observed_max_timestamp` に記録する（requested / observed の分離 = P5。既存 29 run
への遡及変換はしない）。

秘密情報: `submitted_parameters` は adapter が許可リスト方式で組み立てる
（tool / terms / geo / timeframe のみ）。env ファイルや token は保存しない。

G5 以降の補足（canonical contract の正本整理 — T1）: 構造の正本は
`collection-run-v1`（`src/validation/schemas/collection_run.py`）、生成の正本は
本モジュール（`src/collection/core/provenance.py` の対応表）、評価の正本は
`src/validation/provenance.py`（Completeness / Confidence / Integrity /
Readiness の機械評価。`inferred` の自動付与はしない）。証拠の登録場所は
`metadata/provenance/evidence-registry.json`（`evidence-registry-v1`。
`validate-registries` が実検証する）。旧 run の監査は
`validation.cli audit-provenance`（既定出力
`docs/audits/g5-provenance-assessment.json`。非破壊・`raw_modified: false`）。
P01（run_id 一意性）は `validate-study` が strict run 横断で検査し、P17
（`query_registry_version` 追跡可能性）は意味検証が warning/info で報告する
（いずれも既存 strict 合格を FAIL に変えない）。詳細は
`docs/specs/validation-framework.md` §18。

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
| L1-11 | Artifact storage contract（G4） | `integrity.verify_artifact_manifest` → `storage_contract`（S1/S6-S12。reader 登録・内容 format 照合・record_count・ページング・SQLite lineage。registry 不在時は reader 依存検査のみ無効） |

L1-09 の規則:

- 終端 status は「raw artifact の存在」が必須（証拠なしは FAIL）。
- `success` + `returned_count=0` は `record_count: 0` の artifact でのみ受理
  （**取得失敗をゼロ観測として記録しない**）。
- `success` と `partial`/`missing` な raw artifact は矛盾。
- `failed` は errors 記録必須。failed run は**カタログせず隔離**（raw 保全）。

---

## 6. Quarantine（2026-10-13 決定）

- **場所: `<workspace>/.quarantine/<run-id>/` を正式採用**（`docs/plans/20261013a.md`
  §13 の記載どおり。staging は `<workspace>/.staging/<run-id>/`）。
  両方とも `.gitignore` 済みで、release アーカイブには含めない。
- 内容: 取得した全ファイル + `quarantine-reason.json`（run_id / 時刻 / issues /
  contains_secrets）。
- 上書き禁止（staging / catalog / quarantine のいずれかに同じ run_id があれば停止）。
- **自動削除しない。** 削除は人のレビュー後のみ可能とし、理由を記録する。
- 秘密情報検出時は `chmod 700`（＋理由フラグ）。
  **リポジトリ内での権限制限は漏洩対応ではない**: 検出された資格情報は
  リポジトリ外で失効・ローテーションする。
- アクセス制御は当面ローカル FS 権限のみ（単一マシン前提）。
- **方式 (B)（repo 外の保護パス）へ切り替える条件**: ワークスペースが共有実行環境
  （複数人・共有ランナー）へ移る場合。それまでは発見性を優先して (A) を維持する。

---

## 7. L2 — Research Comparability（最小実装）

実装: `validation.comparability.compare_runs` / `validation.cli compare-runs`。

| 条件 | 判定 |
|---|---|
| C1 | `compound_id` / `query_id` / `submitted_query` の不一致 → `not_comparable` |
| C2 | `temporal_provenance`（window / granularity / timezone / week_start / time_axis）→ `compare_temporal_windows` を再利用 |
| C3 | `source_id` 不一致（単位の代理）→ `not_comparable`。同一 source で collector のみ不一致 → `conditional` |
| T6/T7（任意） | `--coverage-a`/`--coverage-b` で G3 coverage manifest を渡した場合のみ。partial → `conditional`（`t6_coverage_partial`）/ missing → `not_comparable`（`t6_coverage_missing`）/ unknown → 欠測状態未明示として `unknown`（`t7_missingness_not_explicit`） |

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
  --workspace <root> --datasets-root <root>/datasets \
  --now 2026-10-13T00:00:00Z   # 決定論的リプレイ用の基準時刻固定（任意）

# G3 window compiler のドライラン（収集しない）
python -m collection.core.cli compile-window --window-id <window_id> \
  --collector google-trends-mcp --reference-time 2026-10-13T00:00:00Z

# 外部 collector が staging に出した run の採用判定
python -m collection.core.cli adopt --staged <staging>/<run-id> --workspace <root>

# L1 単体（任意の run ディレクトリ）
python -m validation.cli gate-run --file <run_metadata.json>

# L2（run ペア。--coverage-a/b で G3 T6/T7 条件を有効化）
python -m validation.cli compare-runs --a a.json --b b.json

# G3 §9 coverage manifest（常に exit 0 のレポート）
python -m validation.cli coverage-run --file <run_dir or run_metadata.json>
```

| exit | 意味（collect / adopt / gate-run） |
|---|---|
| 0 | adopted（catalog） |
| 1 | quarantined / stopped（採用しない。raw は保全） |
| 2 | 設定エラー（registry 不正、adapter 未実装、plan 不正、compiler 未登録） |
| 3 | I/O エラー |

`compare-runs` は常に 0（比較判定は採用可否のゲートではない）。`coverage-run`
も常に 0（coverage はレポート。0 への変換禁止は判定側で行う）。`compile-window`
は 0 = 表現可能 / 1 = 拒否（fail closed）/ 2 = 設定エラー。

---

## 9. 制限事項と引き継ぎ

- **ライブ収集は未実施**。Google Trends の live 経路（`SessionMcpTransport`）は
  MCP セッション callable の注入のみ実装し、本リポジトリは実行しない。
- replay fixture は合成（録画形式に基づく）。実レスポンス形状との最終照合は
  ライブ収集承認後のタスク。
- 既存 shell / skill（`research-google-trends` 等）への強制適用は未実施
  （移行は親の判断）。
- G2（query registry / variants）は導入済み（2026-10-13 垂直スライス）。
  plan の `query_id` は registry 照合され、未登録は fail closed で停止する。
  旧 run の旧形式 `queries` は変更せず、対応関係は
  `docs/audits/g2-query-inventory.json`（b.md §13 の 5 状態）で管理する。
- G3（temporal contract / window compiler / coverage）は Google Trends 1 ソースで
  導入済み（2026-10-13 垂直スライス。詳細は
  `docs/specs/validation-framework.md` §16）。他ソースの compiler は未実装で、
  compiler 未登録の collector は従来どおり adapter 自身が期間パラメータを検証する。
  ライブ収集による境界挙動の検証（`exact=true` への昇格）は未実施。
- G7（study / measurement registry）導入時は、plan の `study_id` 参照検証が
  自動で有効になる（CLI の `--metadata-dir` に registry が置かれればよい）。
- G4（Artifact Registry / Storage Contract）は 2026-10-13 に導入済み（詳細は
  `docs/specs/validation-framework.md` §17）。L1 に storage contract 検査が加わり、
  manifest を持つ新規 run は reader 登録・record_count・ページング・SQLite lineage
  まで機械検証される。legacy 29 run は manifest を持たず、読取専用の棚卸し
  （`audit-artifacts` → `docs/audits/g4-storage-inventory.json`）で管理する。
  SQLite 契約は宣言済み（存在時のみ read-only で検証。DB は Git 管理外）。
- G6（Git Tracking Policy / Storage Classification / Publication Gate）は 2026-10-13 に垂直スライス導入（詳細は `docs/specs/validation-framework.md` §19）。収集完了を理由に自動で Git へ追加・公開 Release へ含めない（P7）。`config/storage-policies.json` が保存・追跡・公開方針の宣言であり、`.staging/` / `.quarantine/` は引き続きローカル作業域（追跡・公開とも対象外）。新規 run の追跡方針確定と追跡↔除外の変更適用は親判断待ちのため、本スライスは現状追認のみ。
