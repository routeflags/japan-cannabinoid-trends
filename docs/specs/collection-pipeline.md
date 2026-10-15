# Collection Pipeline (G1 垂直スライス) — 運用契約

**ドメイン名:** 生産 (Production)。「パイプライン」は実装（モジュール・CLI）の名前で、
ドメイン上の名前は生産である（`docs/specs/contracts.md` §3.1）。

**版:** 0.5.0（2026-10-15）
**仕様:** `docs/plans/20261013a.md`（G1、リポジトリ履歴外）+ `20261013h.md` §12
**状態:** 実装済み・**ライブ収集実施済み**（2026-10-15 に 8 run をパイプライン経由で採用。
契約検証は録画リプレイ / 合成 fixture でも継続）

**0.5.0 の変更:** ドメイン名 **生産 (Production)** を明記（契約内容の変更なし）。
同じ日に `collect --live` で 8 run をライブ収集し採用した（§9 の制限事項を更新）。
契約検証は録画リプレイ / 合成 fixture でも継続。

**0.4.0 の変更:** ソース別 staging ドライバ（宣言ファイル `staging-declaration-v1`
→ `stage_run`）と `stage` CLI サブコマンドを追加（§3.4、ISS-20261015-COL-017）。
CSV reader（`csv-record-reader`）と artifact schema `youtube-dataset-csv-v1` を
登録し、ダウンロード済み dataset export を CSV のまま L1 に通せるようにした
（§3.4、ISS-20261015-ART-009）。実記録 7 件での rehearsal は
`docs/reports/20261015b-youtube-csv-staging-driver.md`。

**0.3.0 の変更:** staging 境界の独立検証（
`docs/reports/20261015a-staging-acceptance-review.md`）で指摘された欠陥を修正。
外部由来の `run_id` / `study_id` を単一のパス安全な構成要素として検証
（`RUN_ID_UNSAFE` / `STUDY_ID_UNSAFE`）、`execution.status` / `returned_count` の
宣言を必須化（`STAGING_EXECUTION_INCOMPLETE`）、アーティファクトの相対
サブディレクトリを配置可能に、`environment` のパイプライン所有キーの上書き禁止
（§3.3）。

**0.2.0 の変更:** 外部 collector の staging 産出側（`collection.core.pipeline.stage_run`）
を実装（§3.3）。収集済み payload を契約準拠の staged run にする経路が入り、
実記録 Google Trends 応答で rehearsal 済み（§9）。

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

- 実装: `src/collection/adapters/google_trends/compiler.py` と
  `src/collection/adapters/youtube/compiler.py`（collector 別）。YouTube は
  `dateFilter=year` の MVP のみで、未測定 `dateFilter` は fail closed。共通
  プリミティブは `validation/windows.py`（platform 名は adapters のみ = P1）。
- `collect` は収集前に plan の絶対 window を compile し、結果を `query` 拡張
  領域へ source-agnostic にマージする。plan が同キーに非空の異なる値を宣言して
  いれば `WINDOW_TIMEFRAME_CONFLICT` で停止（P6: 期間の無断切替なし）。
- 拒否は fail closed: `WINDOW_NOT_REPRESENTABLE`（候補 timeframe なし・時代不一致・
  絶対能力 supported なのに実装なし）。`window.exact_required: true` の plan は
  `exact=false` の collector では `WINDOW_EXACTNESS_UNAVAILABLE` で停止。
- ドライラン: `python -m collection.core.cli compile-window`（収集しない）。
- 現在 `exact=false` は、Google Trends が pass 2 の time gate 待ちであること、
  YouTube `dateFilter=year` が adoption-level の測定根拠に留まり live 境界検証済み
  ではないことを反映する。Google Trends の昇格条件と計測プロトコルは
  `docs/specs/gt-boundary-verification.md`（2026-10-15）。GT pass 2 までは
  `exact=false`（ISS-20261015-GT-001 PENDING）。

### 3.3 外部 collector の staging（`stage_run`）と既存 shell 収集との整合

- 移行パス（判断 A）の**産出側を実装した**:
  `collection.core.pipeline.stage_run`（2026-10-15）。外部 collector
  （MCP セッション、クラウド dataset エクスポート、既存 shell）が取得済みの
  payload を、`plan`（`collection-plan-v1`）+ `CollectedArtifact[]` +
  実行事実の宣言として受け取り、`.staging/<run-id>/`（payload のコピー +
  `artifact-manifest.json` + `run_metadata.json`）を書く。
  **判断は下さない** — `adopt` が L1 を実行して catalog / quarantine を決める
  （producer と verdict の分離。gate が自分の入力を生成するコードに依存しない）。
- `run_metadata.json` / `artifact-manifest.json` は `collect` と同じ
  `collection.core.provenance` のビルダが生成するため、2 経路は乖離しない。
  collector の同一性（`adapter_id` / `version`）は**レジストリから読む**
  （宣言からは読まない。registry が正本 = G1 §7.2。stager は collector を
  昇格できない）。
- `stage_run` が検査する入力: plan 構造、`collector_id` の登録、
  window の完全性（`start` / `end_exclusive` / `granularity` / `timezone`）と
  順序、plan の window と window registry の一致、時刻の順序、`execution` の
  `status` / `returned_count` の**宣言**（欠落は `STAGING_EXECUTION_INCOMPLETE`
  — stager は観測していない結果を作らない）、artifact の存在とパス安全性
  （絶対パス・`..`・ファイル名を持たないパスを拒否。宣言された相対サブディレクトリは
  作成して配置）、`run_id` / `study_id` が**単一のパス安全な構成要素**であること
  （`RUN_ID_UNSAFE` / `STUDY_ID_UNSAFE`。外部由来の値がディレクトリ名になるため）、
  study ディレクトリ、run_id 衝突。
  **capability gate は通さない**: capability は「要求」への制約であり、
  収集済み run は要求を出さない。registry 参照（source / collector / query /
  study）は L1 が検査する。
- `environment` のパイプライン所有キー（`adapter` / `collection_core_version` /
  `adapter_contract_version` / `runtime_version` / `code_commit`）はパイプラインが
  書く。宣言側は収集固有の詳細を足せるだけで、上書きできない（`collect` と同一規則。
  `code_commit` はワークスペースが git checkout のときだけ記録する）。
- **artifact の中身は検査しない**: 宣言された `record_count` は L1 の storage
  contract が登録 reader と突き合わせる（S8）。同じ規則を 2 実装しない。
- payload は **byte 単位でコピー**し、manifest の SHA-256 / byte 長はディスク上の
  ファイルから計算する（`collect` と同じ規則）。
- staging ドライバ（0.4.0 で追加・§3.4）: 宣言ファイル（`staging-declaration-v1`）
  + `stage` CLI。`stage_run` を直接呼ぶ経路も引き続き有効（§8）。
- **受容した限界**（2026-10-15 の独立検証で確認、修正しないと決めたもの）:
  staging は原子的でない — `mkdir` の後、manifest / run_metadata を書く前に中断すると
  部分的な `.staging/<run-id>/` が残り、再実行は `RUN_ID_ALREADY_EXISTS` で止まる
  （fail closed。掃除は人）。artifact_id の slug 衝突（`a b.json` と `a-b.json`）は
  採用時に `ARTIFACT_ID_DUPLICATE` で隔離される（遅いが fail closed）。宣言された
  `observed_min/max_timestamp` など payload の**意味**は検査しない（byte 一致と件数の
  みを検証する — 上記記載どおり）。
- `scripts/validation/run-gates.sh run <run_metadata.json>` は新しく L1 ゲート
  （`gate-run`）を呼ぶ: exit 0 = 採用可、非 0 = 隔離。

### 3.4 staging 宣言ドライバ（`stage` CLI / `staging-declaration-v1`）— 0.4.0

実装: `src/collection/core/staging.py` + `collection.core.cli stage`。
外部で取得済みの payload（クラウド dataset export 等）を、`stage_run` の入力を
人手で組み立てずに契約へ乗せる経路。

- **宣言ファイル（判断）**: 入力は CLI 引数ではなく 1 つの JSON
  （`staging-declaration-v1`、`stage --declaration <file>`）。run ごとに query
  対応・窓・時刻・実行結果・artifact を持つため引数ではレビューできず、かつ
  宣言は「どの payload がどの検索か」を人間が明示する唯一の場所である
  （ドライバは payload の列を読んで検索を推定しない）。
- **keyword → `query_id` は宣言**: `query_id` は query registry で照合し、
  未登録は exit 2 で拒否する（registry への G2 準拠エントリ追加は別作業）。
  `compound_id` / `intent_id` は registry の記載をそのまま記録する。
- **窓**: 絶対窓（`start` / `end_exclusive` / `granularity` / `timezone`）と、
  相対要求（`date_filter` / `reference_time`）の両方を宣言から受け取る。
  staging 宣言は取得済み payload の handover なので宣言値を正とし、ここでは
  相対→絶対の compile を行わない。別途、収集前 dry-run / plan gate 用として
  YouTube Apify `dateFilter=year` の window compiler MVP は WIN-002 で実装済み。
  `reference_time` と `limitations` は `temporal_provenance` に、
  `collector_window_type` / `boundary_semantics` / `exact_window_match` は
  宣言値を記録する（ソース知識をコアに置かない = P1）。絶対窓は
  「宣言された観測区間」であり collector が強制した境界ではない旨を
  limitation に書く。
- **時刻**: payload に収集時刻列が無い場合は started_at / finished_at を
  宣言し、根拠を `environment.handover.timestamp_basis` に記録する
  （例: export ファイル名の timestamp のみ・timezone 未確証）。捏造しない。
- **artifact**: `record_count` 宣言時はそのまま渡す（S8 が検証 = 非空虚）。
  未宣言時は登録 reader（`storage.readers`）で導出し、physical line ではなく
  **CSV record 数**を数える。reader が解決・読み取りできない場合は exit 2
  （新形式は ART-009 の手順で reader + schema を先に登録する）。
- **run メタデータ**: `environment.handover` に宣言ファイル名 / SHA-256 /
  timestamp basis / record_count と returned_count の導出根拠
  （declared / derived:<reader>）を記録する。
- **実行**: 宣言全体を先に準備（query 照合・件数導出）し、宣言レベルの失敗は
  何も staging せず exit 2。`stage_run` レベルの拒否は run 単位で報告し、
  他の run の staging は続ける（各 run ディレクトリは独立・fail closed）。
- **exit code**: 0 = 全 run staged（採用は `adopt` が判定）/ 1 = 1 つ以上
  stopped / 2 = 宣言・設定エラー / 3 = 宣言ファイル読み取り不可。
- **検証できる範囲（制限）**: 窓・date_filter・実行 status など宣言の事実は
  payload からは独立検証できない。L1 が検証するのは契約（件数・format・
  reader・hash・registry 参照・欠測規則）まで。宣言の根拠は
  `timestamp_basis` と `limitations` に、rehearsal か実採用かは運用記録に残す
  （2026-10-15 の 7 件 rehearsal: `docs/reports/20261015b-youtube-csv-staging-driver.md`）。

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

### 7.1 G7 横断ゲート（2026-10-13 垂直スライスで追加）

実装: `research.comparability.check_cross_study_comparability`（CS01-CS13）/
`research.cli compare`。測定サブセットは `validation.comparability.compare_measurements`
（G7 §9 準拠）に委譲し重複実装しない。

- `comparable` の定義: CS01-CS07 の同一性に加え、CS08 sampling 明示・CS09 coverage complete・
  CS10 missingness 明示・CS11 同一正規化スケール・CS12 run+manifest 来歴・CS13 公開承認の証拠が
  両側に揃った場合のみ（`tests/research/test_comparability_gate.py` で synthetic 完全証拠ペアにより定義を固定）。
- 実データ（legacy 29件）には sampling/coverage/正規化スケール/承認の証拠がないため、
  実データ上の最強判定は `conditional` のまま。`comparable` を返さないのは未実装ではなく
  証拠不足による到達不能（`test_comparable_is_unreachable_on_repository_data` が全ペアで保証）。
- GT 相対指数は fetch グループ（query type＋共取得 term 集合＋timeframe）が異なる場合に
  `cs11_normalization_scale_mismatch` で直接比較を拒否（§8.3）。同一グループの再取得は
  `conditional`＋`cs11_renormalization_instability_review_required`（`repeat_diff.json` の実践と整合）。
- G7 measurement registry（`metadata/measurements/measurement-registry.json`）の unit
  （`relative_index_0_100` / `posts` / `videos`）と整合。X 投稿数と YouTube 動画数は
  同一単位として扱わない（G7-T12）。
- CS08-CS13 の証拠発生条件は `docs/provenance/comparability-evidence-cs08-cs13.md`
  に定義。CS12 の担体には `transformation-v1` 生成記録
  （`src/processing/transformations.py`、2026-10-15 スライス）が加わった。

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

# 外部 collector の payload を staged run にする（産出側。宣言ファイル。§3.4）
python -m collection.core.cli stage --declaration declaration.json \
  --workspace <root> --datasets-root <root>/datasets
# exit 0 = 全 run staged / 1 = stopped あり / 2 = 宣言・設定エラー / 3 = 読取不可
# 採用判定は別途 `adopt`。`stage_run` を直接呼ぶ経路も引き続き有効。

# L1 単体（任意の run ディレクトリ）
python -m validation.cli gate-run --file <run_metadata.json>

# L2（run ペア。--coverage-a/b で G3 T6/T7 条件を有効化）
python -m validation.cli compare-runs --a a.json --b b.json

# G3 §9 coverage manifest（常に exit 0 のレポート）
python -m validation.cli coverage-run --file <run_dir or run_metadata.json>
```

| exit | 意味（collect / adopt / stage / gate-run） |
|---|---|
| 0 | adopted（catalog）。`stage` は「全 run staged」（採用は `adopt` の判定） |
| 1 | quarantined / stopped（採用しない。raw は保全）。`stage` は 1 つ以上の run が stopped |
| 2 | 設定エラー（registry 不正、adapter 未実装、plan 不正、compiler 未登録、宣言不正・query 未登録・reader 未解決） |
| 3 | I/O エラー（計画・宣言ファイルを読めない） |

`compare-runs` は常に 0（比較判定は採用可否のゲートではない）。`coverage-run`
も常に 0（coverage はレポート。0 への変換禁止は判定側で行う）。`compile-window`
は 0 = 表現可能 / 1 = 拒否（fail closed）/ 2 = 設定エラー。

---

## 9. 制限事項と引き継ぎ

- **ライブ収集は実施済み（2026-10-15）**。`collection.core.cli collect --live`
  （`SessionMcpTransport` + `mcp_session.McpStdioSession`、MCP stdio で
  `google-trends-mcp@0.1.1` を起動）で 8 run を採用した（CBN / THC-O / H4CBH /
  HHBD / HHCH / CRDP / THCH / CRDH、`today 5-y` / geo=JP）。ライブはオプトインで、
  セッションを起動できない環境では従来どおり fail closed（失敗として記録）。
- 境界挙動の実測検証（`exact=true` への昇格）は**未実施のまま**。キャプチャ検証 /
  staging（`collection.adapters.google_trends.boundary`）と対応表・昇格規則の
  評価器（`validation.cli boundary-report`）および実行手順を 2026-10-15 に実装
  （`docs/specs/gt-boundary-verification.md`）。行列（4 timeframe × 2 pass。pass 2 は
  参照時刻を 7 日以上離す必要がある）は未実行で、ISS-20261015-GT-001 は PENDING。
- replay fixture は合成（録画形式に基づく）。ただし **2026-10-15 に、実記録
  GT 応答（tracked `datasets/cannabinoid-multi-trends/data/raw/google_trends/
  20261012T064246Z-google-trends-ja-rikiddo-5y-main5/records_cbd-rikiddo-5y.json`）
  での照合を行った**: adapter の想定形状（`{keyword, geo, timeframe,
  collected_at, data:[{date, value}]}`）は実レスポンスと一致し、抽出件数
  （262 点）と観測境界（2021-10-10 .. 2026-10-11）が実データと一致する
  （`tests/collection/test_pipeline_e2e.py::
  `test_collect_replays_a_real_recorded_response`）。**境界挙動（`exact=true`
  昇格）は依然未検証**（ライブ収集は系列取得のために実施したが、境界計測は
  未実施）。
- 外部 collector staging（§3.3）は実記録 GT 応答で
  stage → adopt → 厳格検証（artifact 検証込み）まで通過済み
  （`tests/collection/test_staging.py`）。staging 宣言ドライバ + `stage` CLI
  （§3.4、COL-017）と CSV reader / `youtube-dataset-csv-v1`（ART-009）を
  0.4.0 で追加し、2026-10-14 ダウンロードの実 YouTube dataset export 7 件を
  scratch workspace で stage → adopt → 厳格検証 + `audit-new-runs` まで
  rehearsal 済み（`docs/reports/20261015b-youtube-csv-staging-driver.md`）。
  **実採用は未実施**: 窓・date_filter・実行 status 等の宣言事実の確認が先
  （§3.4 の「検証できる範囲」を参照）。
- 2026-10-15 に staging 境界の**独立検証**を行った
  （`docs/reports/20261015a-staging-acceptance-review.md`）。実記録 GT 応答での
  stage → adopt → 厳格検証は独立スクリプトでも再現し、拒否 7 経路・改竄検出・
  `audit-new-runs` の非空虚性も確認済み。指摘のうち `run_id` のパストラバーサルは
  0.3.0 で修正し、残りは上記の受容限界として記録した。未検証はライブ収集経路のみ。
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
