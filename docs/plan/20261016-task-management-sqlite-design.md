# 2026-10-16 plan — 軽量タスク管理基盤 SQLite 設計案

**状態:** 開発設計案（2026-10-16）。本ファイルは `docs/plan/20261016.md` の採用済み ER 図と `docs/plan/20261016-procedures.md` の algorithm draft を前提にした plan 文書であり、正式仕様ではない。
**用途:** 後続エージェントが研究データの生産・検収・出荷・保管・目録・検証・納品物化を迷わず進めるための、ローカルファイルシステム上の Markdown 本文 + SQLite 索引による作業管理基盤を設計する。
**非目的:** 本書は publication / release / raw 改変 / 外部送信 / 秘密情報保存 / 研究データ・タスク本文・issue 本文の正本化を追加しない。

## 0. 確認根拠

- `docs/plan/20261016.md`: Contract → Study → Production → Acceptance Evaluation → Shipping → Storage Target / Inventory → Validation Result → Deliverable → Release の ER 関係を確認した。
- `docs/plan/20261016-procedures.md` §1.1–§1.2、§4–§9: Required Condition Set（required acceptance condition / required validation item / required storage condition。"1 件でも pass" は十分条件ではない。required refs がすべて `pass` または owner 承認つき `waived` でなければ次工程へ進めない。本文は持たず `ref` / `source_doc_path` / `source_doc_sha256` の参照だけを持つ）と fail / quarantine / replan の基本モデル（非終端のどの工程でも fail / quarantine 可能。failed / quarantined は同じ履歴を巻き戻さず、owner 承認つき後続作業を新規作成し `supersedes` / `superseded-by` で記録。隔離は削除ではなく以降の出荷・検証完了・納品物化・リリース候補化を止める）を確認した。本設計書はこの procedures を実装側に落とすもので、procedures 自体の意味を変更しない。
- `docs/domain/glossary.md`: Production / Shipping / Storage / Inventory / Contract / Validation / Deliverable / Release の用語と「出荷≠リリース」を確認した。
- `docs/domain/context-map.md`: U3 validation ↔ storage 隣接 protocol と U5 production の gate 呼び出し境界を確認した。
- `.gitignore`: `*.db` / `*.db-wal` / `*.db-shm` と `/.agents` が Git 管理外であることを確認した。`*.db` blanket 例外は G6 追跡監査の reviewed exception であり（`.gitignore` コメント、`docs/specs/validation-framework.md` §19 参照）、G4 storage inventory（`make audit-snapshots` の `g4-storage-inventory.json`）とは別物であることを確認した。
- `src/` 構成: 実体は `src/collection/` + `src/processing/`（収集・加工）、`src/storage/`（保管・目録）、`src/validation/`（検証・gate）、`src/research/`（研究ドメインの audit / comparability / views / catalog / policy）である。`src/production` パッケージは存在しない。また `src/research/` 配下に本基盤が想定するような workflow 管理（task 状態機械・claim・facade）は存在しない。よってタスク管理は既存ドメイン実装を直接置換しない横断的 facade として、新規 `src/task_management/` に置くことを提案する。

## 1. 目的と非目的

### 1.1 目的

この基盤は、次の事故を防ぐための**ローカル作業管理レイヤ**である。

1. 後続エージェントが、次に実行すべき手続きや必要な証跡を誤る。
2. 生産・出荷・保管・検証・納品物化の状態が、issue 文書・チャット・ローカルメモに分散して欠落する。
3. Acceptance Evaluation や Validation Result が不合格・不明なのに、成果物を shipping / deliverable / release candidate に進める。
4. Storage Condition や Inventory の記録が欠けたまま、検証済みと誤認する。
5. 各エージェントが SQLite や複数内部 API を直接触り、状態遷移・ロック・監査履歴を壊す。
6. SQLite が task / issue / 研究内容の第二の正本になり、Markdown 本文との矛盾を生む。

本文の正本はローカルファイルシステム上の Markdown 等に置き、SQLite は **path、識別子、状態、時刻、短い機械用メタデータ、hash / checksum** だけを持つ索引として扱う。

### 1.2 非目的

この基盤は次を行わない。

- publication / release の実行、GitHub release / Zenodo upload / DOI 発行。
- raw / interim / processed / publication データの編集、再生成、正規化。
- 研究データ、payload、投稿本文、顧客情報、API token、秘密情報の保存。
- issue 本文、task 本文、長文説明、研究内容そのものの保存。
- 契約条件・検収条件・検証項目・保管条件の意味の決定または上書き。
- gate / verdict / judgment の所有。判定意味は Contract / gate 側に従う。
- `.staging/`、`.quarantine/`、`data/raw/`、`docs/audits/` の代替。
- 既存 issue docs / milestone / audit snapshot の正本化または自動書換え。

## 2. DDD 対応

| ER / 用語 | タスク管理基盤での扱い | source of truth |
|---|---|---|
| Contract | `tasks.contract_ref` と各 condition / item の `*_ref` で参照する。条件の本文は複製しない。 | `docs/specs/contracts.md`、registry、contract-ledger、各契約文書 |
| Required Condition Set | `task_required_refs` に kind（`acceptance` / `validation` / `storage`）ごとの required ref を `ref` / `source_doc_path` / `source_doc_sha256` の参照だけで登録する。本文・正本は Markdown 等に置く。gate 判定は「対象 kind の required refs がすべて `pass` または owner 承認つき `waived`」で行い、「1 件でも pass」は十分条件にしない。詳細は §4.2、`docs/plan/20261016-procedures.md` §1.1。 | 契約文書・研究計画・issue / task / plan の Markdown（正本）、DB は索引 |
| Study | `tasks.study_ref` で対象 study を参照する。研究質問・方法論・研究本文は DB に保存しない。 | `datasets/<study-id>/README.md`、`methodology.md`、study registry |
| Production（実体: `src/collection/` + `src/processing/`） | task の `work_type='production'` または status `in_progress` で作業状態を追う。成果物の内容は保存しない。`src/production` というパッケージは存在しないため、設計・コード・文書でその名を使わない。 | collection / processing code と生成された artifact |
| Acceptance Evaluation | `task_evaluations` に condition/item ごとの評価結果・根拠 path / ID を保存する。評価本文は Markdown 等に置く。判定意味は Contract に従う。 | Contract / gate と評価証跡 |
| Shipping | `prepare_shipping` / `mark_shipped` 操作と `task_storage_targets` / `artifact_locations` で追う。release とは別。 | storage policy / shipping 手続き / artifact location |
| Storage Target | `task_storage_targets` に local / repository / remote の対象を参照として記録する。実体の配置は行わない。 | storage context、storage policy、実際の保管先 |
| Inventory | `artifact_locations` と `task_inventory_records` に path / sha256 / size / format / tracking_state などの非破壊事実を記録する。 | storage inventory / manifest / catalog |
| Validation / Validation Result | `task_validations` に validation item / storage condition ごとの結果と証跡 path / ID を保存する。検証本文・audit report 本文は保存しない。検証は保管物を生成・変更しない。 | validation CLI / gate result / audit report |
| Deliverable | `task_deliverables` に検証済み artifact の候補化を記録する。すべての artifact を自動的に deliverable にしない。 | release / publication process が参照する成果物定義 |
| Release | DB では `release_ref` または `release_candidate_ref` の外部参照まで。release 実行・公開承認はしない。 | `docs/specs/release-process.md`、publication gate、Git tag / Zenodo |

## 3. ファサード設計

### 3.1 単一入口

後続エージェントは DB を直接書かず、次のどちらか一方を単一入口として使う。

- Python facade: `src/task_management/facade.py` の `TaskManager`
- CLI facade: `python -m task_management.cli ...`

内部では SQLite、migration、transition table、監査クエリを使ってよいが、外部公開 API は最小化する。

Task / issue の本文は DB ではなく Markdown 等のファイルに置く。既定のローカル作業領域は `.agents/task-manager/tasks/` と `.agents/task-manager/issues/` とし、永続的な project issue を使う場合だけ既存の `docs/issues/...` などを path 参照する。Facade は本文文字列を受け取らず、`task_doc_path` / `issue_doc_path` と任意の checksum だけを受け取る。

### 3.2 最小 API 案

各 API は DDL の NOT NULL 列を埋められる引数を持つ（§4.2）。`reason_ref` / `evidence_ref` / `summary_ref` は本文ではなく path / ID 参照である。`waived` は条件の削除ではなく owner 承認つき例外記録であり、§4.2 `task_required_refs` の waiver 列を埋める（procedures §1.1、§9）。

| 操作 | シグネチャ案と振る舞い |
|---|---|
| `create(task_doc_path, contract_ref, created_by, study_ref=None, work_type=..., task_doc_sha256=None)` | `proposed` の task を作成し、`created` event を記録する。`created_by`（`tasks.created_by` NOT NULL）を必須とする。本文・raw payload・秘密情報を受け取らない。 |
| `plan(task_id, actor, plan_ref, required_refs)` | 契約由来の required refs（acceptance / validation / storage の `ref` + `source_doc_path` + `source_doc_sha256`）を `task_required_refs` に登録し、`planned` へ遷移する。未確認条件は `unknown` 参照ではなく owner 判断待ちとして残す（required ref 未登録のまま次工程 gate は通さない）。 |
| `claim(task_id, agent_id, ttl_minutes)` | active claim（`released_at IS NULL`）がなく、かつ期限切れの active claim があればそれを auto-release（`released_at=now`、event 記録）してから `claimed` へ遷移し、`agent_claims` に期限付き lock（`expires_at = now + ttl`）を作る。期限内 active claim がある場合は拒否する。 |
| `release_claim(task_id, agent_id)` | 明示的に claim を release する（`released_at=now`）。status は変えない。claim 保持者または owner だけが実行できる。期限切れ claim の再取得は `claim()` が auto-release するため、本 API は明示的手放し・owner による強制解除用である。 |
| `start(task_id, agent_id)` | claim 保持者（期限内の active claim の `agent_id`）だけが `in_progress` へ進める。 |
| `record_artifact(task_id, actor, artifact_ref, artifact_role, data_layer, sensitivity)` | artifact の参照だけを記録する。内容・レコード値・秘密情報は保存しない。`artifact_role` / `data_layer` / `sensitivity`（いずれも NOT NULL + CHECK）は省略不可。 |
| `update_status(task_id, actor, to_status, reason_ref)` | transition table と不変条件に合わない遷移を拒否し、`status_changed` event（`from_status` / `to_status` 付き）を append-only に残す。status を変える唯一の event、`reason_ref` 必須。 |
| `record_required_ref(task_id, actor, kind, ref, source_doc_path, source_doc_sha256=None)` | `plan` 後に required ref を追加する。`kind` は `acceptance` / `validation` / `storage`。本文は受け取らず参照だけ。 |
| `record_waiver(task_id, actor, required_ref_id, owner, reason_ref, waived_at=None)` | required ref に対する owner 承認つき `waived` を記録する。`owner`・`reason_ref`（根拠文書 path）必須。条件は削除されず、監査で `pass` と同等に gate 通過扱いとなる。 |
| `record_evaluation(task_id, actor, artifact_ref, condition_ref, result, evaluator, evidence_ref, validation_item_ref=None)` | Acceptance Evaluation を記録する。`result` は `pass/fail/unknown/partial/collection_failed/observed_zero/missing/waived` を区別する（`waived` は `record_waiver` 経由が正規だが、評価経由の記録も同語彙で保存する）。`evaluator` / `evidence_ref`（NOT NULL）を必須とする。 |
| `resolve_storage_target(task_id, actor, storage_condition_ref, target_kind, target_ref, resolved_result, evidence_ref)` | Storage Target 解決を記録する。`target_kind`（`local` / `repository` / `remote`）、`storage_condition_ref`、`resolved_result`（`pass` / `fail` / `unknown`）、`evidence_ref`（NOT NULL）を必須とする。 |
| `prepare_shipping(task_id, actor, artifact_ref, storage_target_ref)` | その artifact に対する kind=`acceptance` + kind=`storage` の required refs がすべて `pass` / `waived` でなければ拒否する（「1 件でも pass」は不可）。通過すれば `shipping_ready` へ。 |
| `mark_shipped(task_id, actor, artifact_ref, storage_target_ref, inventory_ref)` | `shipping_ready` から `shipped` へ遷移する。`task_storage_targets.resolved_result='pass'` と対応する inventory 参照（location / hash）が揃わない場合は拒否する。release 実行ではない。 |
| `record_inventory(task_id, actor, artifact_ref, target_id, location_ref, format, tracking_state, recorded_by, sha256=None, size_bytes=None)` | Inventory を非破壊事実として記録する。`target_id`（`task_storage_targets` の FK）、`format`、`tracking_state`、`recorded_by`（NOT NULL）を必須とする。`tracking_state` の語彙は G6 監査実装に合わせる（§4.2）。存在しない hash や record count を作らない。 |
| `record_validation(task_id, actor, artifact_ref, inventory_id, validation_item_ref, result, mode, validated_by, evidence_ref, storage_condition_ref=None)` | Inventory 参照（`inventory_id` NOT NULL）なしの validation pass を拒否する。`mode`（`automated` / `manual`）、`validated_by`、`evidence_ref`（NOT NULL）を必須とする。`result` は `pass/fail/unknown/partial/missing/waived`。 |
| `mark_deliverable(task_id, actor, artifact_ref, validation_id, version_ref, release_candidate_ref=None)` | 対象 artifact の kind=`validation` + kind=`storage` の required refs がすべて `pass` / `waived` で、紐づく `validation_id` の result が `pass` で、shipping と inventory が揃う場合だけ `deliverable_ready` へ進める。 |
| `close(task_id, actor, summary_ref, outcome, non_deliverable_reason_ref=None)` | `outcome='deliverable'` の場合は `deliverable_ready` からのみ terminal close する。`outcome='non_deliverable'` の場合は deliverable 化しない完了（検証不要の文書 task、中止確定だが failed ではない作業等）として、**任意の非終端状態**から `closed` へ遷移できる。ただし `non_deliverable_reason_ref`（理由文書 path）必須。deliverable 化した成果物がある task を `non_deliverable` で閉じることは拒否する。 |
| `fail(task_id, actor, reason_ref)` | **任意の非終端状態**から `failed` に遷移する（seed は全非終端状態からの `failed` 行を持つ。§4.3）。`reason_ref` 必須。failed は原則終端であり、同じ task を巻き戻さない。 |
| `quarantine(task_id, actor, reason_ref, quarantine_ref=None)` | **任意の非終端状態**から `quarantined` に遷移する（`accepted` / `inventoried` / `validated` / `deliverable_ready` を含む全非終端状態。privacy fail-open 防止のため出荷後・検証後も隔離可能。§4.3）。以降の出荷・検証完了・納品物化・リリース候補化を止める。削除ではない。quarantined は原則終端であり、同じ task を巻き戻さない。 |
| `replan(task_id, actor, new_task_doc_path, reason_ref, created_by)` | failed / quarantined task の後続作業を**新規 task**として作成する（同一 task を戻さない）。新規 task は `proposed` で始まり、`task_links` に `link_type='supersedes'`（新 → 旧）/ `'superseded-by'`（旧 → 新）を記録する。owner 承認の根拠は `reason_ref` に残す。closed からの訂正は本 API ではなく公開・リリースの訂正手続きで扱う（procedures §1.2）。 |
| `audit()` | 破損・過不足・不正遷移・孤立 record・required refs 未達のまま進んだ task を検出し、DB を変更しない。 |

### 3.3 CLI 案

```text
python -m task_management.cli init --db .agents/task-manager/task-manager.db
python -m task_management.cli create --task-doc .agents/task-manager/tasks/task-001.md --contract-ref "..." --study-ref "..." --created-by AGENT
python -m task_management.cli plan TASK --plan-ref docs/... --required-ref acceptance:C:... --required-ref validation:V:... --required-ref storage:S:...
python -m task_management.cli record-required-ref TASK --kind acceptance --ref C:... --source-doc docs/... --source-sha256 ...
python -m task_management.cli record-waiver TASK --required-ref-id N --owner OWNER --reason-ref docs/...
python -m task_management.cli claim TASK --agent AGENT --ttl-minutes 60
python -m task_management.cli release-claim TASK --agent AGENT
python -m task_management.cli start TASK --agent AGENT
python -m task_management.cli record-artifact TASK --ref datasets/... --role artifact --data-layer processed --sensitivity restricted --actor AGENT
python -m task_management.cli record-evaluation TASK --artifact ART --condition C --result pass --evaluator AGENT --evidence docs/...
python -m task_management.cli resolve-storage-target TASK --condition S --kind repository --target-ref datasets/... --result pass --evidence docs/... --actor AGENT
python -m task_management.cli prepare-shipping TASK --artifact ART --target repository:datasets/... --actor AGENT
python -m task_management.cli record-inventory TASK --artifact ART --target TGT --location datasets/... --sha256 ... --size ... --format json --tracking-state tracked --recorded-by AGENT
python -m task_management.cli mark-shipped TASK --artifact ART --target TGT --inventory INV --actor AGENT
python -m task_management.cli record-validation TASK --artifact ART --item V --result pass --inventory INV --mode automated --validated-by AGENT --evidence docs/...
python -m task_management.cli mark-deliverable TASK --artifact ART --validation-id N --version-ref v... --actor AGENT
python -m task_management.cli close TASK --summary-ref docs/... --outcome deliverable --actor AGENT
python -m task_management.cli close TASK --summary-ref docs/... --outcome non-deliverable --non-deliverable-reason-ref docs/... --actor AGENT
python -m task_management.cli fail TASK --reason-ref docs/... --actor AGENT
python -m task_management.cli quarantine TASK --reason-ref docs/... --actor AGENT
python -m task_management.cli replan TASK --new-task-doc .agents/task-manager/tasks/task-002.md --reason-ref docs/... --created-by AGENT
python -m task_management.cli audit --db .agents/task-manager/task-manager.db
```

> 注: `record-evaluation` の `--evaluator`、`record-validation` の `--mode` / `--validated-by`、`record-inventory` の `--target` / `--recorded-by`、`resolve-storage-target` の各引数は DDL の NOT NULL 列に対応するため省略不可（§4.2）。`tracking-state` の取りうる値は G6 語彙（§4.2）。

### 3.4 直接 DB 書込み禁止の設計

- migration と seed 以外の書込みは `TaskManager` transaction 経由に限定する。
- SQLite trigger が守るのは遷移 allowlist（`allowed_status_transitions` の存在確認）と `from_status` と `current_status` の一致のみである。これを「最後の防衛線」とは呼ばない。cross-table invariant（required refs の充足、inventory / validation の有無、quarantine 後の出荷停止など）は facade transaction と `audit` が守る。
- CLI は facade の薄い wrapper にし、CLI と Python API で規則を二重実装しない。
- `task_events` は append-only とし、修正が必要な場合は correction event を追加する。status を変える event は `event_type='status_changed'` のみであり、`claimed` / `artifact_recorded` / `evaluation_recorded` / `shipping_prepared` / `shipped` / `inventory_recorded` / `validation_recorded` / `deliverable_marked` / `claim_released` / `waiver_recorded` / `required_ref_recorded` / `replanned` は status を変えない注釈 event（`to_status IS NULL`）である。`claim()` は `agent_claims` 行の書込みと `status_changed`（`planned -> claimed`）の両方を行い、`claimed` 注釈 event を status 遷移に使わない。
- DB 破損が疑われる場合、facade は自動修復せず `audit` で検出し、owner 判断を要求する。
- DB ファイルは worktree / clone ごとにローカルである。`claim` / lock は同一 DB ファイル内でのみ有効であり、別 worktree / 別 clone / 別マシンの agent 間の相互排除にはならない。マルチエージェント運用で claim に頼る場合は同一 DB を共有する運用（同一 worktree 上の実行）に限定し、それ以外は owner が調停する。

## 4. SQLite schema 案

### 4.1 基本方針

- SQLite は作業状態の local store であり、研究データの source of truth ではない。
- Task / issue / plan / evaluation / validation / summary の本文はローカル Markdown 等を正本とし、SQLite はその path と任意の checksum だけを持つ。
- raw payload、record 値、post text、customer data、secret、長文説明、研究内容本文は列として持たない。
- artifact は相対 path / manifest ID / external opaque ref / hash などの参照情報だけを持つ。
- path は原則 repository-relative または `.agents/...` の local-relative path とし、絶対 path は portability と漏洩リスクがあるため facade で拒否または owner 承認にする。
- `CHECK`、`FOREIGN KEY`、`UNIQUE`、partial unique index、trigger で過不足を防ぐ。
- `PRAGMA foreign_keys = ON`、`PRAGMA journal_mode = WAL`、`PRAGMA busy_timeout = 5000` を facade 初期化時に設定する。

### 4.2 DDL スケッチ

```sql
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  checksum TEXT NOT NULL
);

CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  task_doc_path TEXT NOT NULL,
  task_doc_sha256 TEXT,
  work_type TEXT NOT NULL CHECK (work_type IN (
    'contract', 'study', 'production', 'shipping', 'storage',
    'inventory', 'validation', 'deliverable', 'release_candidate', 'documentation'
  )),
  contract_ref TEXT NOT NULL,
  study_ref TEXT,
  current_status TEXT NOT NULL CHECK (current_status IN (
    'proposed', 'planned', 'claimed', 'in_progress', 'awaiting_evaluation',
    'accepted', 'shipping_ready', 'shipped', 'inventoried', 'validating',
    'validated', 'deliverable_ready', 'closed', 'failed', 'quarantined'
  )),
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  terminal_at TEXT,
  CHECK (task_doc_path NOT LIKE '/%'),
  CHECK (instr(task_doc_path, char(10)) = 0),
  CHECK (task_doc_sha256 IS NULL OR (length(task_doc_sha256) = 64 AND task_doc_sha256 NOT GLOB '*[^0-9a-f]*')),
  CHECK ((current_status NOT IN ('closed','failed','quarantined')) OR terminal_at IS NOT NULL)
);

CREATE TABLE task_document_refs (
  document_ref_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  doc_role TEXT NOT NULL CHECK (doc_role IN (
    'task_body', 'issue_body', 'plan', 'reason', 'evidence', 'summary'
  )),
  doc_path TEXT NOT NULL,
  doc_sha256 TEXT,
  content_stored_in_db INTEGER NOT NULL DEFAULT 0 CHECK (content_stored_in_db = 0),
  recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (doc_path NOT LIKE '/%'),
  CHECK (instr(doc_path, char(10)) = 0),
  CHECK (doc_sha256 IS NULL OR (length(doc_sha256) = 64 AND doc_sha256 NOT GLOB '*[^0-9a-f]*')),
  UNIQUE (task_id, doc_role, doc_path)
);

CREATE TABLE allowed_status_transitions (
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  requires_facade_check TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (from_status, to_status)
);

CREATE TABLE task_events (
  event_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'created', 'status_changed', 'claimed', 'claim_released', 'artifact_recorded',
    'required_ref_recorded', 'waiver_recorded', 'evaluation_recorded',
    'shipping_prepared', 'shipped', 'inventory_recorded',
    'validation_recorded', 'deliverable_marked', 'replanned', 'correction'
  )),
  from_status TEXT,
  to_status TEXT,
  actor TEXT NOT NULL,
  reason_ref TEXT,
  occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (reason_ref IS NULL OR instr(reason_ref, char(10)) = 0),
  CHECK (
    (event_type = 'status_changed' AND from_status IS NOT NULL AND to_status IS NOT NULL)
    OR (event_type <> 'status_changed' AND to_status IS NULL)
  )
);

CREATE TRIGGER task_status_transition_guard
BEFORE INSERT ON task_events
WHEN NEW.event_type = 'status_changed'
BEGIN
  SELECT CASE
    WHEN (SELECT current_status FROM tasks WHERE task_id = NEW.task_id) <> NEW.from_status
    THEN RAISE(ABORT, 'from_status does not match current_status')
  END;
  SELECT CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM allowed_status_transitions
      WHERE from_status = NEW.from_status AND to_status = NEW.to_status
    )
    THEN RAISE(ABORT, 'status transition is not allowed')
  END;
END;

CREATE TRIGGER task_status_transition_apply
AFTER INSERT ON task_events
WHEN NEW.event_type = 'status_changed'
BEGIN
  UPDATE tasks
  SET current_status = NEW.to_status,
      updated_at = NEW.occurred_at,
      terminal_at = CASE
        WHEN NEW.to_status IN ('closed','failed','quarantined') THEN NEW.occurred_at
        ELSE terminal_at
      END
  WHERE task_id = NEW.task_id;
END;

-- Required Condition Set の索引（procedures §1.1）。本文は持たず参照だけ持つ。
-- kind ごとの required refs がすべて pass / waived でなければ次工程へ進めない
-- （「1 件でも pass」は十分条件ではない）。結果の正本は
-- task_evaluations / task_validations / task_storage_targets 側に置き、
-- 本テーブルは「何が必須か」の解決結果と waiver 状態の索引である。
CREATE TABLE task_required_refs (
  required_ref_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  kind TEXT NOT NULL CHECK (kind IN ('acceptance', 'validation', 'storage')),
  ref TEXT NOT NULL,
  source_doc_path TEXT NOT NULL,
  source_doc_sha256 TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'pass', 'fail', 'unknown', 'partial', 'collection_failed',
    'observed_zero', 'missing', 'waived'
  )),
  waived_by TEXT,
  waiver_reason_ref TEXT,
  waived_at TEXT,
  resolved_at TEXT,
  CHECK (ref NOT LIKE '/%'),
  CHECK (instr(ref, char(10)) = 0),
  CHECK (source_doc_path NOT LIKE '/%'),
  CHECK (instr(source_doc_path, char(10)) = 0),
  CHECK (source_doc_sha256 IS NULL OR (length(source_doc_sha256) = 64 AND source_doc_sha256 NOT GLOB '*[^0-9a-f]*')),
  CHECK ((status = 'waived') = (waived_by IS NOT NULL AND waiver_reason_ref IS NOT NULL)),
  CHECK (waiver_reason_ref IS NULL OR instr(waiver_reason_ref, char(10)) = 0),
  UNIQUE (task_id, kind, ref)
);

-- fail / quarantine 後の replan 連鎖（procedures §1.2）。同一 task の巻き戻しは
-- 記録しない。後続作業は新規 task として作り、前後関係だけを残す。
CREATE TABLE task_links (
  link_id INTEGER PRIMARY KEY,
  from_task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  to_task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  link_type TEXT NOT NULL CHECK (link_type IN ('supersedes', 'superseded-by', 'related')),
  reason_ref TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (from_task_id <> to_task_id),
  CHECK (instr(reason_ref, char(10)) = 0)
);

CREATE TABLE agent_claims (
  claim_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  agent_id TEXT NOT NULL,
  claimed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  expires_at TEXT NOT NULL,
  released_at TEXT,
  CHECK (released_at IS NULL OR released_at >= claimed_at)
);

CREATE UNIQUE INDEX one_active_claim_per_task
ON agent_claims(task_id)
WHERE released_at IS NULL;

CREATE TABLE task_artifacts (
  artifact_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  artifact_role TEXT NOT NULL CHECK (artifact_role IN (
    'input_ref', 'intermediate_artifact', 'artifact', 'deliverable_candidate'
  )),
  artifact_ref TEXT NOT NULL,
  data_layer TEXT NOT NULL CHECK (data_layer IN (
    'raw', 'interim', 'processed', 'analysis', 'publication', 'metadata', 'unknown'
  )),
  sensitivity TEXT NOT NULL CHECK (sensitivity IN (
    'public_candidate', 'restricted', 'private', 'unknown'
  )),
  content_stored_in_db INTEGER NOT NULL DEFAULT 0 CHECK (content_stored_in_db = 0),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (instr(artifact_ref, char(10)) = 0),
  UNIQUE (task_id, artifact_ref)
);

CREATE TABLE task_evaluations (
  evaluation_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  artifact_id TEXT NOT NULL REFERENCES task_artifacts(artifact_id) ON DELETE RESTRICT,
  condition_ref TEXT NOT NULL,
  validation_item_ref TEXT,
  result TEXT NOT NULL CHECK (result IN (
    'pass', 'fail', 'unknown', 'partial', 'collection_failed',
    'observed_zero', 'missing', 'waived'
  )),
  evaluator TEXT NOT NULL,
  evidence_ref TEXT NOT NULL,
  evaluated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (validation_item_ref IS NULL OR validation_item_ref <> ''),
  CHECK (instr(evidence_ref, char(10)) = 0)
);

CREATE UNIQUE INDEX unique_task_evaluation_item
ON task_evaluations(
  task_id,
  artifact_id,
  condition_ref,
  COALESCE(validation_item_ref, '')
);

CREATE TABLE task_storage_targets (
  target_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  storage_condition_ref TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN ('local', 'repository', 'remote')),
  target_ref TEXT NOT NULL,
  resolved_result TEXT NOT NULL CHECK (resolved_result IN ('pass', 'fail', 'unknown')),
  evidence_ref TEXT NOT NULL,
  CHECK (instr(target_ref, char(10)) = 0),
  CHECK (instr(evidence_ref, char(10)) = 0),
  UNIQUE (task_id, storage_condition_ref, target_ref)
);

CREATE TABLE task_inventory_records (
  inventory_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  artifact_id TEXT NOT NULL REFERENCES task_artifacts(artifact_id) ON DELETE RESTRICT,
  target_id TEXT NOT NULL REFERENCES task_storage_targets(target_id) ON DELETE RESTRICT,
  location_ref TEXT NOT NULL,
  sha256 TEXT,
  size_bytes INTEGER CHECK (size_bytes IS NULL OR size_bytes >= 0),
  format TEXT NOT NULL,
  tracking_state TEXT NOT NULL CHECK (tracking_state IN (
    'tracked', 'ignored', 'untracked_unignored', 'absent'
  )),
  recorded_by TEXT NOT NULL,
  recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (instr(location_ref, char(10)) = 0),
  CHECK (sha256 IS NULL OR (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*')),
  UNIQUE (artifact_id, target_id, location_ref)
);

CREATE TABLE task_validations (
  validation_id INTEGER PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  artifact_id TEXT NOT NULL REFERENCES task_artifacts(artifact_id) ON DELETE RESTRICT,
  inventory_id TEXT NOT NULL REFERENCES task_inventory_records(inventory_id) ON DELETE RESTRICT,
  validation_item_ref TEXT NOT NULL,
  storage_condition_ref TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('automated', 'manual')),
  result TEXT NOT NULL CHECK (result IN ('pass', 'fail', 'unknown', 'partial', 'missing', 'waived')),
  evidence_ref TEXT NOT NULL,
  validated_by TEXT NOT NULL,
  validated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (instr(evidence_ref, char(10)) = 0),
  UNIQUE (task_id, artifact_id, inventory_id, validation_item_ref)
);

CREATE TABLE task_deliverables (
  deliverable_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
  artifact_id TEXT NOT NULL REFERENCES task_artifacts(artifact_id) ON DELETE RESTRICT,
  validation_id INTEGER NOT NULL REFERENCES task_validations(validation_id) ON DELETE RESTRICT,
  version_ref TEXT NOT NULL,
  release_candidate_ref TEXT,
  release_ref TEXT,
  status TEXT NOT NULL CHECK (status IN ('candidate', 'ready', 'rejected')),
  marked_by TEXT NOT NULL,
  marked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK (instr(version_ref, char(10)) = 0),
  CHECK (release_candidate_ref IS NULL OR instr(release_candidate_ref, char(10)) = 0),
  CHECK (release_ref IS NULL OR instr(release_ref, char(10)) = 0),
  UNIQUE (task_id, artifact_id, version_ref)
);
```

> 注: 上記は設計案である。SQLite は `CHECK` 内でサブクエリを使えないため、cross-table invariant（required refs の充足、quarantine 後の出荷停止など）は facade transaction と audit query で守る。trigger が守るのは遷移 allowlist と `from_status` 一致のみである（§3.4）。
>
> `tracking_state` の語彙は G6 git 追跡監査（`src/validation/g6_inventory.py`）と同一にする: `tracked`（git index 内）、`ignored`（untracked + ignore 規則一致）、`untracked_unignored`（どちらでもない。accidental-add リスク）、`absent`（既知の local-only path がこの checkout に存在しない。欠落は欠落として記録し、ゼロ内容とはみなさない）。storage inventory（G4）の追跡有無とは別概念であり、混同しない。

### 4.3 transition seed 案

```sql
INSERT INTO allowed_status_transitions(from_status, to_status, requires_facade_check) VALUES
-- 正常系チェーン（facade が required refs 充足等の cross-table 条件を追加検査する）
('proposed', 'planned', 'plan refs exist'),
('planned', 'claimed', 'active claim absent'),
('claimed', 'in_progress', 'claim holder only'),
('in_progress', 'awaiting_evaluation', 'artifact refs exist'),
('awaiting_evaluation', 'accepted', 'all required acceptance refs pass/waived'),
('accepted', 'shipping_ready', 'storage targets resolved'),
('shipping_ready', 'shipped', 'mark_shipped: storage pass + inventory refs exist'),
('shipped', 'inventoried', 'inventory records exist'),
('inventoried', 'validating', 'inventory records exist'),
('validating', 'validated', 'all required validation+storage refs pass/waived'),
('validated', 'deliverable_ready', 'validation pass and eligible artifact'),
('deliverable_ready', 'closed', 'summary exists, outcome=deliverable'),
-- non-deliverable close: deliverable 化しない完了。deliverable 化済み artifact が
-- ある task は拒否する（facade 検査）。
('proposed', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('planned', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('claimed', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('in_progress', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('awaiting_evaluation', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('accepted', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('shipping_ready', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('shipped', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('inventoried', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('validating', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
('validated', 'closed', 'outcome=non-deliverable, reason required, no deliverables'),
-- fail: 非終端のすべてから可能（procedures §1.2）。failed は原則終端。
('proposed', 'failed', 'reason required'),
('planned', 'failed', 'reason required'),
('claimed', 'failed', 'reason required'),
('in_progress', 'failed', 'reason required'),
('awaiting_evaluation', 'failed', 'reason required'),
('accepted', 'failed', 'reason required'),
('shipping_ready', 'failed', 'reason required'),
('shipped', 'failed', 'reason required'),
('inventoried', 'failed', 'reason required'),
('validating', 'failed', 'reason required'),
('validated', 'failed', 'reason required'),
('deliverable_ready', 'failed', 'reason required'),
-- quarantine: 非終端のすべてから可能。出荷後・検証後（accepted / inventoried /
-- validated / deliverable_ready を含む）も隔離できる。privacy fail-open 防止。
-- quarantined は原則終端。再開は replan（新規 task + supersedes 記録）のみ。
('proposed', 'quarantined', 'reason required'),
('planned', 'quarantined', 'reason required'),
('claimed', 'quarantined', 'reason required'),
('in_progress', 'quarantined', 'reason required'),
('awaiting_evaluation', 'quarantined', 'reason required'),
('accepted', 'quarantined', 'reason required'),
('shipping_ready', 'quarantined', 'reason required'),
('shipped', 'quarantined', 'reason required'),
('inventoried', 'quarantined', 'reason required'),
('validating', 'quarantined', 'reason required'),
('validated', 'quarantined', 'reason required'),
('deliverable_ready', 'quarantined', 'reason required');
```

> `failed` / `quarantined` / `closed` からの遷移行は持たない（原則終端）。訂正・再作業は同一 task の遷移ではなく `replan`（新規 task + `task_links`）または公開・リリースの訂正手続きで扱う（procedures §1.2）。

## 5. 状態機械

### 5.1 状態定義

| 状態 | 意味 |
|---|---|
| `proposed` | task が提案されたが、契約・研究・必要条件の参照が未整理。 |
| `planned` | Contract / Study / acceptance / validation / storage condition の参照が計画に入った。 |
| `claimed` | agent が期限付き claim を取得した。作業開始前。 |
| `in_progress` | 生産・文書化・検証準備などの作業中。 |
| `awaiting_evaluation` | Artifact 参照が記録され、Acceptance Evaluation 待ち。 |
| `accepted` | 必須 Acceptance Evaluation が `pass`。Shipping 準備へ進める。 |
| `shipping_ready` | Storage Target と Storage Condition が解決済み。 |
| `shipped` | Artifact が指定保管先へ引き渡された記録がある。Release ではない。 |
| `inventoried` | Inventory が path / hash / size / format / tracking_state を記録済み。 |
| `validating` | Validation Item / Storage Condition の検証中。 |
| `validated` | 必須 Validation Result が `pass`。 |
| `deliverable_ready` | 検証済み artifact が Deliverable 候補として識別された。Release 済みではない。 |
| `closed` | task 完了（`outcome=deliverable` または `outcome=non_deliverable`）。release 実行を意味しない。原則終端。 |
| `failed` | 条件不成立または実行不能として停止。原則終端。同じ task を巻き戻さない。再作業は `replan`（新規 task + `supersedes` 記録）のみ。 |
| `quarantined` | 不明・不合格・private / restricted の疑いなどにより隔離。以降の出荷・検証完了・納品物化・リリース候補化を止める。削除ではない。原則終端。同じ task を巻き戻さない。再開は `replan`（新規 task + `supersedes` 記録）のみ。 |

### 5.2 代表シナリオ

#### 正常系

1. `create` → `proposed`
2. `plan`（required refs 登録） → `planned`
3. `claim` → `claimed`
4. `start` → `in_progress`
5. `record_artifact` → `awaiting_evaluation`
6. `record_evaluation(result=pass)`（対象 kind=`acceptance` の required refs がすべて pass / waived） → `accepted`
7. `prepare_shipping`（kind=`acceptance` + kind=`storage` の required refs がすべて pass / waived） → `shipping_ready`
8. `record_inventory` + `mark_shipped` → `shipped` → `inventoried`
9. `record_validation(result=pass)`（対象 kind=`validation` + kind=`storage` の required refs がすべて pass / waived） → `validating` → `validated`
10. `mark_deliverable` → `deliverable_ready`
11. `close(outcome=deliverable)` → `closed`

#### 異常系・エッジケース

- Acceptance Evaluation が `unknown` / `missing` / `partial` / `failed` の場合、`accepted` / `shipping_ready` へ進めず `quarantined` または owner 判断待ちにする。「1 件でも pass」は十分条件ではない。
- `collection_failed` は `observed_zero` に変換しない。
- `Storage Target` が `remote` でも release 済みとは扱わない。
- Inventory が存在しない artifact は validation pass にできない。
- Validation Result が `fail` / `unknown` / `partial` / `missing` の場合、deliverable にできない。`waived` は owner・理由・根拠 path・時刻の記録がある場合のみ pass 相当として扱う。
- active claim がある task は別 agent が `start` できない。期限切れ claim は `claim()` が auto-release して再取得する（§3.2）。明示的に手放す場合は `release_claim()` を使う。claim / lock は同一 DB ファイル内でのみ有効である（§3.4）。
- `accepted` / `inventoried` / `validated` / `deliverable_ready` を含む非終端のすべてから `failed` / `quarantined` へ遷移できる。出荷後・検証後に private / restricted / provenance 不明の疑義が見つかった場合も隔離し、以降の出荷・検証完了・納品物化・リリース候補化を止める（privacy fail-open 防止）。
- `failed` / `quarantined` からの再開は同一 task の遷移ではなく `replan`（新規 task + `task_links.supersedes` 記録、owner 承認の `reason_ref` 必須）で行う。`closed` からの訂正は replan ではなく公開・リリースの訂正手続きで扱う。
- deliverable 化しない完了は `close(outcome=non_deliverable, non_deliverable_reason_ref=...)` で任意の非終端状態から `closed` へ遷移する。ただし deliverable 化済み artifact がある task は拒否する。

## 6. 不変条件・ゲート

中心不変条件は procedures の Required Condition Set（§1.1）である。「1 件でも pass」は十分条件ではない。gate 判定は常に対象 kind の required refs 全件で行う。

Facade は少なくとも次を強制する。

1. **Required refs なしに gate を通さない。**
   `awaiting_evaluation -> accepted` は kind=`acceptance` の required refs がすべて `pass` / `waived` の場合だけ許可する。`prepare_shipping`（`-> shipping_ready`）は kind=`acceptance` + kind=`storage` の全件、`validating -> validated` は kind=`validation` + kind=`storage` の全件、`mark_deliverable`（`-> deliverable_ready`）は kind=`validation` + kind=`storage` の全件が `pass` / `waived` の場合だけ許可する。`unknown` / `missing` / `partial` / `failed` は pass とみなさない。`waived` は owner・理由・根拠 path・時刻の記録がある場合のみ pass 相当とする。必須条件セットを解決できない（required refs 未登録の）task は推測で進めず `unknown` 停止または owner 判断へ送る。
2. **Storage Condition 未解決なら `shipped` にできない。**
   `mark_shipped`（`shipping_ready -> shipped`）は `task_storage_targets.resolved_result='pass'` と対応する inventory 参照（location / hash）が揃う場合だけ許可する。
3. **Inventory 記録なしに Validation 完了にできない。**
   `task_validations.inventory_id` は必須。`validating -> validated` は対象 artifact の Inventory が揃う場合だけ許可する。
4. **Validation Result が `pass`（または owner 承認つき `waived`）でなければ Deliverable にできない。**
   `mark_deliverable` は対象 artifact の kind=`validation` + kind=`storage` の required refs 全件が `pass` / `waived` で、紐づく `validation_id` の result が `pass` の場合だけ受け付ける。
5. **Deliverable と Release は別物。**
   `deliverable_ready`、`release_candidate_ref`、`release_ref` は release 実行を意味しない。publication / release gate は別工程。
6. **Quarantine は以降の出荷・検証完了・納品物化・リリース候補化を止める。**
   `quarantined` の task に対する `prepare_shipping` / `mark_shipped` / `record_validation(result=pass)` による `validated` 遷移 / `mark_deliverable` / release 候補化は facade が拒否する。隔離は削除ではなく、raw や既存成果物を修正しない。
7. **failed / quarantined は原則終端。再開は replan のみ。**
   同一 task を `failed` / `quarantined` / `closed` から他状態へ戻す遷移は seed に持たない。再作業は `replan`（新規 task + `task_links` の `supersedes` / `superseded-by` 記録、owner 承認の `reason_ref` 必須）で行う。`closed` からの訂正は replan ではなく公開・リリースの訂正手続きで扱う。
8. **DB は作業管理であり、研究データの source of truth ではない。**
   DB 破損時に artifact を DB から復元する設計にしない。
9. **DB は本文を持たない。**
   task / issue / plan / evaluation / validation / summary の本文は Markdown 等の path を source of truth とし、DB は path・ref・checksum・状態・時刻・短い機械用 enum だけを保持する。`task_required_refs` も `ref` / `source_doc_path` / `source_doc_sha256` の参照だけを持ち、条件本文を持たない。
10. **raw は参照のみ。**
    `data_layer='raw'` の artifact は参照可能だが、facade は raw 編集・置換・採用判定を行わない。
11. **秘密情報を保存しない。**
    path / hash / opaque ref は可、payload / token / customer-level private data は不可。

## 7. リポジトリを汚さない設計

### 7.1 SQLite ファイルの置き場所

推奨:

```text
.agents/task-manager/task-manager.db
.agents/task-manager/task-manager.db-wal
.agents/task-manager/task-manager.db-shm
.agents/task-manager/tasks/*.md
.agents/task-manager/issues/*.md
```

理由:

- `/.agents` は `.gitignore` 済みで、agent のローカル作業領域として自然。
- `*.db` / `*.db-wal` / `*.db-shm` も `.gitignore` 済み。
- `.staging/`、`.quarantine/`、`data/raw/` と混同しない。
- task / issue のローカル本文も `.agents/` 配下に置けば、リポジトリの tracked docs を増やさずに運用できる。

代替案として `.task-manager/task-manager.db` を使う場合は `.gitignore` 追加が必要である。設計時点では既存 ignore を活かすため `.agents/` を推奨する。

既存 SQLite 運用との関係:

- G4 storage inventory: 研究データの保管目録は `make audit-snapshots` が生成する tracked `docs/audits/g4-storage-inventory.json`（`src/storage/inventory.py`）であり、task DB の `artifact_locations` / `task_inventory_records` とは別物である。task DB 側は作業管理用の索引であり、G4 目録を代替しない。
- G6 blanket `*.db` 例外: `.gitignore` の `*.db` / `*.db-wal` / `*.db-shm` は、tracked `*.db` がゼロ件であることを条件にした reviewed exception（`.gitignore` コメント、`docs/specs/validation-framework.md` §19、G6 `audit-git-tracking`）である。task DB はこの例外の範囲内で untracked のまま運用し、commit しない。
- 実行入口は Makefile 経由を原則とする（AGENTS.md「Production Entry Points」）。task DB の init / migration / audit コマンドも、実装時は `make` target 経由で呼べる形にし、直接の `python -m` 実行や side channel（publish / push / delete を行う経路）を作らない。

DB ファイルは worktree / clone ごとにローカルである。別 worktree・別 clone の DB は別物であり、claim / lock・status・監査結果は共有されない（§3.4）。

### 7.2 Git に追跡するもの / しないもの

追跡する:

- 設計書。
- migration SQL。
- facade / CLI 実装。
- transition / invariant tests。
- audit query tests。

追跡しない:

- `task-manager.db`、WAL / SHM。
- ローカル claim / lock 状態。
- `.agents/task-manager/tasks/*.md`、`.agents/task-manager/issues/*.md` などのローカル task / issue 本文。
- raw / private / restricted artifact の内容。
- ローカル検証結果に機微情報が含まれる場合の出力。

### 7.3 CI での扱い

- CI は一時ディレクトリに空 DB を作り、migration / facade / transition / audit tests を実行する。
- CI はローカル `.agents/task-manager/task-manager.db` を参照しない。
- CI は raw / interim / processed / publication データを再生成しない。

### 7.4 `docs/issues/` との関係

既存 CI `audit-issues`（`python -m validation.cli audit-issues`、`research-validation.yml`）は `docs/issues/` 配下の全 issue レコードに強制ルールを適用する（`src/validation/issues.py`: `ID` / `優先度` / `ステータス` の存在、語彙 `OPEN` / `PENDING` / `RESOLVED` / `DOCUMENTED` / `MITIGATED` / `ARCHIVED`、終端 status の決定日、ID 一意、OPEN P0 は failure）。本基盤はこのルールを変更しない。

task DB の status と issue の status は二重状態になるため、同期規則を次に固定する。

- 同期しない: facade / CLI / audit は `docs/issues/` の status を自動で書き換えない。issue は人間向け計画・判断記録の本文正本であり、DB は作業状態と facade invariant の索引である。相互参照は path / ID / checksum だけ（`task_doc_path` / `issue_doc_path`）。
- 参照する: task を issue 由来で作る場合は `task_document_refs`（`doc_role='issue_body'`）または `task_doc_path` で issue path を参照し、issue 側の `ステータス` 変更は人間または既存 issue 運用が行う。DB audit は issue 本文の整合性を検査しない（`audit-issues` の責務）。
- 検出する: `audit` は「DB 上 `closed` だが参照先 issue が `OPEN` のまま」等の疑いを警告として報告してよいが、failure とはしない（research backlog は正常状態であり、`audit-issues` が P1 以下を fatal にしないのと同趣旨）。逆方向（issue は終端だが DB が非終端で放置）は active claim の有無と合わせて報告する。

## 8. 監査クエリ案

`audit` は read-only で次を検出する。

```sql
-- tasks.current_status と最後の status event の不一致
SELECT t.task_id, t.current_status, e.to_status AS last_event_status
FROM tasks t
JOIN (
  SELECT task_id, to_status, MAX(event_id) AS max_event_id
  FROM task_events
  WHERE event_type = 'status_changed'
  GROUP BY task_id
) e ON e.task_id = t.task_id
WHERE t.current_status <> e.to_status;

-- active claim が複数ある（partial unique index が効いていない/破損）
SELECT task_id, COUNT(*) AS active_claims
FROM agent_claims
WHERE released_at IS NULL
GROUP BY task_id
HAVING COUNT(*) > 1;

-- shipping_ready / shipped なのに pass の acceptance evaluation がない
-- （旧式の粗い検査。kind 別の厳密検査は次の required-refs クエリを使う）
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('shipping_ready', 'shipped', 'inventoried', 'validating', 'validated', 'deliverable_ready', 'closed')
AND NOT EXISTS (
  SELECT 1 FROM task_evaluations e
  WHERE e.task_id = t.task_id AND e.result = 'pass'
);

-- shipped 以降なのに storage target が未解決
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('shipped', 'inventoried', 'validating', 'validated', 'deliverable_ready', 'closed')
AND EXISTS (
  SELECT 1 FROM task_storage_targets st
  WHERE st.task_id = t.task_id AND st.resolved_result <> 'pass'
);

-- validated / deliverable_ready なのに inventory がない
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('validated', 'deliverable_ready', 'closed')
AND NOT EXISTS (
  SELECT 1 FROM task_inventory_records i
  WHERE i.task_id = t.task_id
);

-- deliverable が validation pass に紐づいていない
SELECT d.deliverable_id, d.task_id
FROM task_deliverables d
JOIN task_validations v ON v.validation_id = d.validation_id
WHERE v.result <> 'pass';

-- required refs の充足なしに gate を通過した疑い（中心不変条件 §6-1 の監査）
-- accepted 以降なのに kind=acceptance の required refs が全件 pass/waived でない
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('accepted', 'shipping_ready', 'shipped', 'inventoried', 'validating', 'validated', 'deliverable_ready', 'closed')
AND EXISTS (
  SELECT 1 FROM task_required_refs r
  WHERE r.task_id = t.task_id AND r.kind = 'acceptance'
  AND r.status NOT IN ('pass', 'waived')
);

-- validated / deliverable_ready なのに kind=validation/storage の required refs が未達
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('validated', 'deliverable_ready')
AND EXISTS (
  SELECT 1 FROM task_required_refs r
  WHERE r.task_id = t.task_id AND r.kind IN ('validation', 'storage')
  AND r.status NOT IN ('pass', 'waived')
);

-- shipping_ready 以降なのに kind=storage の required refs が未達
SELECT t.task_id
FROM tasks t
WHERE t.current_status IN ('shipping_ready', 'shipped', 'inventoried', 'validating', 'validated', 'deliverable_ready', 'closed')
AND EXISTS (
  SELECT 1 FROM task_required_refs r
  WHERE r.task_id = t.task_id AND r.kind = 'storage'
  AND r.status NOT IN ('pass', 'waived')
);

-- 必須条件セット未解決（required refs が空）のまま gate を通過した疑い
SELECT t.task_id, t.current_status
FROM tasks t
WHERE t.current_status IN ('accepted', 'shipping_ready', 'shipped', 'inventoried', 'validating', 'validated', 'deliverable_ready')
AND NOT EXISTS (
  SELECT 1 FROM task_required_refs r WHERE r.task_id = t.task_id
);

-- waiver に owner / 理由 / 時刻が欠けている（CHECK 制約の二重検査・破損検出用）
SELECT required_ref_id, task_id
FROM task_required_refs
WHERE status = 'waived'
AND (waived_by IS NULL OR waiver_reason_ref IS NULL OR waived_at IS NULL);

-- quarantined 後に shipping / validation / deliverable の記録が進んだ疑い
SELECT t.task_id, t.current_status
FROM tasks t
WHERE t.current_status = 'quarantined'
AND (
  EXISTS (SELECT 1 FROM task_events e WHERE e.task_id = t.task_id AND e.event_type = 'shipped'
          AND e.occurred_at > (SELECT MAX(e2.occurred_at) FROM task_events e2 WHERE e2.task_id = t.task_id AND e2.event_type = 'status_changed' AND e2.to_status = 'quarantined'))
  OR EXISTS (SELECT 1 FROM task_deliverables d WHERE d.task_id = t.task_id
          AND d.marked_at > (SELECT MAX(e2.occurred_at) FROM task_events e2 WHERE e2.task_id = t.task_id AND e2.event_type = 'status_changed' AND e2.to_status = 'quarantined'))
);

-- replan 連鎖の不整合（supersedes の相手＝旧 task が failed/quarantined でない）
SELECT l.link_id, l.from_task_id, l.to_task_id
FROM task_links l
JOIN tasks t_old ON t_old.task_id = l.to_task_id
WHERE l.link_type = 'supersedes'
AND t_old.current_status NOT IN ('failed', 'quarantined');

-- 期限切れのまま release されていない claim（claim() の auto-release が動いていない疑い）
SELECT claim_id, task_id, agent_id, expires_at
FROM agent_claims
WHERE released_at IS NULL
AND expires_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now');

-- DB に内容保存しない規則の破損
SELECT artifact_id, task_id, artifact_ref
FROM task_artifacts
WHERE content_stored_in_db <> 0;

-- task / issue / evidence 本文を DB に入れない規則の破損
SELECT document_ref_id, task_id, doc_role, doc_path
FROM task_document_refs
WHERE content_stored_in_db <> 0;

-- local-first path 規則の破損（絶対 path や改行を検出）
SELECT task_id, task_doc_path
FROM tasks
WHERE task_doc_path LIKE '/%' OR instr(task_doc_path, char(10)) > 0
UNION ALL
SELECT task_id, doc_path
FROM task_document_refs
WHERE doc_path LIKE '/%' OR instr(doc_path, char(10)) > 0;

-- path/ref 欄に長文本文が紛れた疑い
SELECT task_id, task_doc_path AS suspicious_ref
FROM tasks
WHERE length(task_doc_path) > 512
UNION ALL
SELECT task_id, doc_path
FROM task_document_refs
WHERE length(doc_path) > 512
UNION ALL
SELECT task_id, evidence_ref
FROM task_evaluations
WHERE length(evidence_ref) > 512
UNION ALL
SELECT task_id, evidence_ref
FROM task_validations
WHERE length(evidence_ref) > 512;
```

## 9. 実装タスク分解（BDD）

### Step 1: design doc only（本タスク）

- **振る舞い:** ER / algorithm に基づき、SQLite タスク管理基盤の目的・状態機械・schema・facade・不変条件・リスクを文書化する。
- **受け入れ条件:** raw / interim / processed / publication データを変更しない。既存正本と矛盾する箇所は「要 owner 判断」として残す。
- **優先度:** P0。

### Step 2: schema / migrations

- **正常系:** 空 DB に migration を適用すると `tasks`、`task_document_refs`、`task_required_refs`、`task_links`、`task_events`、`task_artifacts`、`task_evaluations`、`task_storage_targets`、`task_inventory_records`、`task_validations`、`task_deliverables`、`agent_claims` が作成され、transition seed（正常系チェーン + 全非終端状態からの `failed` / `quarantined` 行 + `non_deliverable` close 行）が入る。
- **異常系:** foreign key off / migration checksum 不一致 / duplicate active claim は失敗する。
- **データ例:** `task_id='task_20261016_0001'`、`task_doc_path='.agents/task-manager/tasks/task_20261016_0001.md'`、`contract_ref='contract-ledger:...'`、`study_ref='datasets/cannabinoid-platform-trends'`。
- **受け入れ条件:** CI の一時 DB で migration test が通る。実 DB は commit されない。in-memory sqlite で DDL が parse できること。
- **優先度:** P1。

### Step 3: facade skeleton

- **正常系:** `TaskManager.create(task_doc_path=..., created_by=...)` / `plan()` / `claim()` / `start()` が transaction で task と event を作る。`plan()` は `task_required_refs` への登録を含む。
- **異常系:** DB 直書きで壊れた current_status、期限内 active claim、許可外 transition、required refs 未達の gate 通過、`waived` に owner / 理由がない記録を拒否する。
- **受け入れ条件:** CLI なしでも Python API から最小 lifecycle を動かせる。本文文字列を DB に渡す API は作らない。API 引数は DDL の NOT NULL 列をすべて埋められること（§3.2）。
- **優先度:** P1。

### Step 4: transition validation tests

- **正常系:** `proposed -> planned -> claimed -> in_progress` が許可される。`mark_shipped`（`shipping_ready -> shipped`）、`close(outcome=non_deliverable)`（非終端 → `closed`）、全非終端状態からの `failed` / `quarantined` が許可される。
- **異常系:** `proposed -> shipped`、required refs 未達の `shipping_ready` / `validated` / `deliverable_ready`、Inventory なしの `validated`、Validation fail の `deliverable_ready`、quarantined 後の出荷・deliverable 化、failed / quarantined / closed からの巻き戻し遷移が拒否される。
- **エッジケース:** `collection_failed` と `observed_zero` が別 result として記録される。`waived` は owner・理由・根拠 path・時刻つきの場合のみ pass 相当になる。
- **受け入れ条件:** 不正確なデータの出荷につながる遷移がテストで落ちる。
- **優先度:** P1。

### Step 5: CLI

- **正常系:** 後続エージェントが `create`、`plan`、`record-required-ref`、`record-waiver`、`claim`、`release-claim`、`record-evaluation`、`resolve-storage-target`、`prepare-shipping`、`record-inventory`、`mark-shipped`、`record-validation`、`mark-deliverable`、`close --outcome deliverable|non-deliverable`、`replan` を CLI だけで実行できる。
- **異常系:** payload や secret らしき入力、本文文字列、絶対 path の誤用、raw 編集を示唆する操作を拒否または警告する。NOT NULL 対応引数の欠落は実行前に拒否する。
- **受け入れ条件:** CLI は facade の wrapper で、独自の transition 規則を持たない。
- **優先度:** P2。

### Step 6: audit command

- **正常系:** `audit` が不整合なしを exit 0 で報告する。
- **異常系:** status/event 不一致、orphan artifact、active claim 重複、required refs 未達のまま進んだ task、waiver 不備、quarantine 後の出荷・deliverable 化、replan 連鎖の不整合、DB に本文を入れた疑い、絶対 path / 長すぎる ref を exit 1 で報告する。期限切れ未 release claim は警告として報告する。
- **受け入れ条件:** audit は read-only で DB を自動修復しない。
- **優先度:** P2。

### Step 7: documentation handoff

- **正常系:** 後続エージェント向け README に「DB とローカル Markdown の置き場所」「commit しないもの」「CLI の最小例」「release しないこと」「本文は path 参照のみ」を記載する。
- **異常系:** publication / release / raw 改変に見える説明を残さない。
- **受け入れ条件:** 新規参加 agent が docs だけで安全な使い方を理解できる。
- **優先度:** P3。

## 10. リスクと未決事項

| 論点 | リスク | 設計案 | 状態 |
|---|---|---|---|
| SQLite 同時書き込み | 複数 agent が同時に claim / update して lock 競合する。別 worktree / 別 clone の DB は別物のため claim は相互排除にならない。 | WAL、busy_timeout、短い transaction、partial unique index、claim TTL。同一 DB 内の調停のみ。remote 共有 DB は当面扱わない。 | 要 owner 判断: 同時実行の上限と retry 方針。 |
| Multi-agent claim / lock | claim 放置で task が進まない。期限切れ claim の再取得経路が DDL + API で定義されていないと実装不能になる。 | `expires_at` を必須化。`claim()` が期限切れ active claim を auto-release して再 claim する。明示的手放し・強制解除は `release_claim()`。期限切れ未 release は audit 警告。 | 要 owner 判断: TTL の標準値と、期限切れ claim を誰が破棄できるか（§11-3）。 |
| DB を commit するか | ローカル状態・機微 metadata・環境差分を repository に混入する。 | DB は commit しない。schema / migration / docs / tests のみ commit。G6 blanket `*.db` 例外の範囲内で運用する。 | 推奨決定案。 |
| DB が本文の第二正本になる | issue / task / 研究内容本文・契約条件本文を DB に入れると Markdown と矛盾し、リポジトリ汚染や機微情報混入につながる。 | 本文は `.agents/.../*.md` または既存 `docs/issues/...` 等の file path を正本にし、DB は path / ref / checksum / status / timestamp / enum だけを保持。`task_required_refs` も参照だけ。監査で長すぎる ref・絶対 path・content flag を検出する。 | 追加要件として反映済み。 |
| issue docs / milestones との関係 | issue docs と DB の二重管理で矛盾する。既存 CI `audit-issues` の強制ルールと競合する恐れがある。 | issue docs は人間向け計画・判断記録の本文正本、DB は作業状態と facade invariant の索引。相互参照は path / ID / checksum だけ。facade は issue status を自動書換えしない（§7.4）。DB `closed` と issue `OPEN` の乖離は audit 警告に留める。 | 要 owner 判断: issue から task を生成するか。 |
| audit snapshots との関係 | DB audit と `docs/audits/` を混同する。 | task DB audit は作業 DB の整合性検査。研究データ監査スナップショットを代替しない。 | 明記済み。 |
| Storage Target / Inventory の粒度 | 1 task に複数 artifact / target があると status が粗くなる。 | task_artifacts / targets / inventory を多対一で持ち、status は aggregate 状態として扱う。 | 要 owner 判断: artifact 単位 task に分ける閾値。 |
| Release 連携 | deliverable_ready を release 済みと誤解する。 | `release_ref` は外部参照だけ。release command は提供しない。 | 明記済み。 |
| Remote storage 連携 | 将来 GitHub / Zenodo API を呼びたくなる。 | v1 は外部送信なし。将来は別 contract / publication gate / owner 承認後。 | 将来課題。 |
| 契約条件の参照形式 | `condition_ref` の命名が未統一だと照合できない。 | 初期は opaque ref。正式な condition registry が必要なら Contract 側で owner 判断。 | 要 owner 判断。 |
| タスク管理基盤の bounded context | 研究管理基盤 core の一部か supporting tool か。 | 本書では「横断的 local work-management facade」として扱い、既存 DDD 正本を変更しない。 | 要 owner 判断。 |

## 11. Owner 判断が必要な点

1. ~~`src/task_management/` を新規 package として置くか、既存 `src/research/` 配下の workflow 管理とみなすか。~~ → 解決済み（本改訂で §0 へ反映）。`src/research/` に workflow 管理は存在しないため、新規 `src/task_management/` package に置く。残る判断は package 名と CLI モジュール名の確定のみ。
2. `condition_ref` / `validation_item_ref` / `storage_condition_ref` の正規 ID 体系を Contract 側で定義するか。
3. claim TTL の標準値と、期限切れ claim を誰が破棄できるか。設計案: `claim()` の auto-release は誰でも可能（期限切れに限る）、`release_claim()` の期限内解除は claim 保持者または owner のみ。
4. task DB から issue docs / milestones を生成または同期するか。それとも相互参照だけに留めるか。設計案: 相互参照に留め、facade による issue status 自動書換えはしない（§7.4）。
5. deliverable_ready 後の release candidate 連携を、いつ・どの gate 契約で扱うか。
6. `task_required_refs.status` と `task_evaluations.result` / `task_validations.result` / `task_storage_targets.resolved_result` の二重記録の正本関係。設計案: 結果の正本は evaluations / validations / storage_targets 側に置き、`task_required_refs.status` は facade が結果記録時に同期する索引キャッシュとする。不一致は `audit` で検出する。どちらを正本にするかは owner 確定が必要。

## 12. 開発者向け実装指示（Implementation Instructions）

本節は実装者が迷わないための順序つき指示である。procedures（`docs/plan/20261016-procedures.md`）の意味は変えず、本設計書どおりに作る。判断に詰まったら推測で埋めず、§11 の owner 判断事項として残す。

### 12.1 作る順序

1. **migration + seed（§4.2–§4.3）:** DDL をそのまま migration SQL に落とす。`task_required_refs` / `task_links` を含めること。seed は正常系チェーン + 全非終端状態からの `failed` / `quarantined` 行 + `non_deliverable` close 行をすべて入れること（1 行でも欠けると §5 の「任意の非終端状態」が実装不能になる）。in-memory sqlite で parse できることを確認する。
2. **facade transaction（§3.2、§6）:** gate ごとに「対象 kind の required refs 全件が `pass` / `waived`」を SELECT で確認してから `status_changed` event を書く。CHECK で書けない条件は Python 側で検査し、DB 制約違反と facade 拒否をテストで区別する（facade 拒否は例外 + event なし、制約違反は sqlite エラー）。
3. **claim（§3.2）:** `claim()` は 1 transaction で「期限内 active claim の存在確認 → 期限切れ active claim の auto-release（`released_at=now` + `claim_released` event）→ 新規 claim 行 + `status_changed`」を行う。`release_claim()` は status を変えない。`start()` は期限内 active claim の `agent_id` と引数の一致を必須にする。
4. **結果記録と required refs の同期（§3.2、§11-6）:** `record_evaluation` / `record_validation` / `resolve_storage_target` は結果テーブルへの INSERT と `task_required_refs.status` の UPDATE を同一 transaction で行う。`record_waiver` は waiver 列（`waived_by` / `waiver_reason_ref` / `waived_at`）を埋めて `status='waived'` にする。owner・理由・根拠 path のいずれかが欠けたら拒否する。
5. **fail / quarantine / replan（§4.3、§5、§6-6/6-7）:** `fail()` / `quarantine()` は `reason_ref` 必須、任意の非終端状態から受ける。quarantine 後は facade が出荷・検証完了・納品物化・リリース候補化を拒否する。`replan()` は新規 task を `proposed` で作り `task_links` に両方向（`supersedes` + `superseded-by`）を書く。旧 task の status は変えない。
6. **CLI（§3.3）:** facade の薄い wrapper にする。NOT NULL 対応引数（`--created-by`、`--evaluator`、`--mode`、`--validated-by`、`--recorded-by`、`--target` 等）は省略不可にする。本文文字列を受け取る flag は作らない。`--tracking-state` は `tracked` / `ignored` / `untracked_unignored` / `absent` のみ受け付ける。
7. **audit（§8）:** read-only。§8 のクエリをそのまま実装し、required-refs 未達・waiver 不備・quarantine 後進行・replan 不整合・期限切れ未 release を含める。DB を自動修復しない。

### 12.2 してはいけないこと

- `src/production` という package を作らない（実体は `src/collection/` + `src/processing/`。§0）。
- `src/research/` 配下に workflow 管理（task 状態機械・claim・facade）を作らない。新規 `src/task_management/` に置く。
- trigger に cross-table 条件を書かない（trigger は allowlist + `from_status` 一致のみ。§3.4）。
- `status_changed` 以外の event で `tasks.current_status` を変えない（§3.4）。
- `docs/issues/` の status を facade / CLI / audit から書き換えない（§7.4）。
- production 実行入口を `make` 以外に増やさない。publish / push / delete を行う経路を作らない（§7.1）。
- raw / interim / processed / publication データに触れない。DB に本文・payload・secret を入れない。

### 12.3 テスト観点（最低限）

- DDL が in-memory sqlite で適用できる。seed 適用後、全非終端状態 ×（`failed` / `quarantined`）の遷移行が存在する。
- required refs が 1 件でも `pending` / `unknown` / `missing` / `partial` / `failed` の task は `accepted` / `shipping_ready` / `validated` / `deliverable_ready` に進めない（「1 件 pass では通らない」テストを含む）。
- `waived` は owner・理由・根拠 path なしでは gate を通さない。
- `accepted` / `inventoried` / `validated` / `deliverable_ready` から `quarantined` へ遷移できる。quarantine 後に `prepare_shipping` / `mark_shipped` / `mark_deliverable` が拒否される。
- `failed` / `quarantined` / `closed` からの遷移がすべて拒否される。`replan` で新規 task + `supersedes` 記録ができる。
- 期限切れ claim がある task に `claim()` すると auto-release されて再 claim できる。期限内 active claim がある場合は拒否される。
- `mark_shipped` なしに `shipping_ready -> shipped` へ直遷移できない（`update_status` 直指定の拒否）。`outcome=non_deliverable` の `close` は `non_deliverable_reason_ref` なしでは拒否される。
- `audit` が上記の破損 fixture をすべて検出し、DB を変更しない。

