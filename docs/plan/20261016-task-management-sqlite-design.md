# 2026-10-16 plan — 軽量タスク管理基盤 SQLite 設計案

**状態:** 開発設計案（2026-10-16）。本ファイルは `docs/plan/20261016.md` の採用済み ER 図と `docs/plan/20261016-procedures.md` の algorithm draft を前提にした plan 文書であり、正式仕様ではない。  
**用途:** 後続エージェントが研究データの生産・検収・出荷・保管・目録・検証・納品物化を迷わず進めるための、ローカルファイルシステム上の Markdown 本文 + SQLite 索引による作業管理基盤を設計する。  
**非目的:** 本書は publication / release / raw 改変 / 外部送信 / 秘密情報保存 / 研究データ・タスク本文・issue 本文の正本化を追加しない。

## 0. 確認根拠

- `docs/plan/20261016.md`: Contract → Study → Production → Acceptance Evaluation → Shipping → Storage Target / Inventory → Validation Result → Deliverable → Release の ER 関係を確認した。
- `docs/plan/20261016-procedures.md`: acceptance pass なしに shipping へ進めない、inventory を読んで validation する、validation pass 後に deliverable / release candidate へ進める手続きを確認した。
- `docs/domain/glossary.md`: Production / Shipping / Storage / Inventory / Contract / Validation / Deliverable / Release の用語と「出荷≠リリース」を確認した。
- `docs/domain/context-map.md`: U3 validation ↔ storage 隣接 protocol と U5 production の gate 呼び出し境界を確認した。
- `.gitignore`: `*.db` / `*.db-wal` / `*.db-shm` と `/.agents` が Git 管理外であることを確認した。
- `src/` 構成: 既存の production / processing / research / storage / validation パッケージを確認し、タスク管理は既存ドメイン実装を直接置換しない横断的 facade として提案する。

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
| Study | `tasks.study_ref` で対象 study を参照する。研究質問・方法論・研究本文は DB に保存しない。 | `datasets/<study-id>/README.md`、`methodology.md`、study registry |
| Production | task の `work_type='production'` または status `in_progress` で作業状態を追う。成果物の内容は保存しない。 | production / processing code と生成された artifact |
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

| 操作 | 期待する振る舞い |
|---|---|
| `create(task_doc_path, contract_ref, study_ref=None, work_type=..., task_doc_sha256=None)` | `proposed` の task を作成し、初回 event を記録する。本文・raw payload・秘密情報を受け取らない。 |
| `plan(task_id, plan_ref, acceptance_refs, validation_refs, storage_condition_refs)` | 契約由来の参照を紐づけ、`planned` へ遷移する。未確認条件は `unknown` 参照ではなく owner 判断待ちとして残す。 |
| `claim(task_id, agent_id, ttl)` | active claim がなければ `claimed` へ遷移し、`agent_claims` に期限付き lock を作る。期限切れ claim は再取得可能。 |
| `start(task_id)` | claim 保持者だけが `in_progress` へ進める。 |
| `record_artifact(task_id, artifact_ref, artifact_role, data_layer, sensitivity)` | artifact の参照だけを記録する。内容・レコード値・秘密情報は保存しない。 |
| `update_status(task_id, to_status, reason_ref)` | transition table と不変条件に合わない遷移を拒否し、event を append-only に残す。 |
| `record_evaluation(task_id, artifact_ref, condition_ref, result, evidence_ref)` | Acceptance Evaluation を記録する。`pass/fail/unknown/partial/collection_failed/observed_zero/missing` を区別する。 |
| `prepare_shipping(task_id, artifact_ref, storage_target_ref)` | 全必須 Acceptance Evaluation が `pass` でなければ拒否する。 |
| `record_inventory(task_id, artifact_ref, location_ref, sha256, size_bytes, format, tracking_state)` | Inventory を非破壊事実として記録する。存在しない hash や record count を作らない。 |
| `record_validation(task_id, artifact_ref, validation_item_ref, result, inventory_ref, evidence_ref)` | Inventory 参照なしの validation pass を拒否する。 |
| `mark_deliverable(task_id, artifact_ref, version_ref)` | Validation Result が `pass` で、shipping と inventory が揃う場合だけ `deliverable_ready` へ進める。 |
| `close(task_id, summary_ref)` | deliverable_ready または明示的な non-deliverable 完了理由がある場合だけ terminal close する。 |
| `fail(task_id, reason_ref)` | 任意の非終端状態から `failed` に遷移し、再開には新規 task または owner 承認付き replan を要求する。 |
| `quarantine(task_id, reason_ref, quarantine_ref=None)` | 不明・不合格・private / restricted の疑いを記録し、shipping / deliverable 化を止める。 |
| `audit()` | 破損・過不足・不正遷移・孤立 record を検出し、DB を変更しない。 |

### 3.3 CLI 案

```text
python -m task_management.cli init --db .agents/task-manager/task-manager.db
python -m task_management.cli create --task-doc .agents/task-manager/tasks/task-001.md --contract-ref "..." --study-ref "..."
python -m task_management.cli plan TASK --plan-ref docs/...
python -m task_management.cli claim TASK --agent AGENT --ttl-minutes 60
python -m task_management.cli start TASK
python -m task_management.cli record-artifact TASK --ref datasets/... --role artifact --data-layer processed
python -m task_management.cli record-evaluation TASK --artifact ART --condition C --result pass --evidence docs/...
python -m task_management.cli prepare-shipping TASK --artifact ART --target repository:datasets/...
python -m task_management.cli record-inventory TASK --artifact ART --location datasets/... --sha256 ... --size ... --format json --tracking-state tracked
python -m task_management.cli record-validation TASK --artifact ART --item V --result pass --inventory INV --evidence docs/...
python -m task_management.cli mark-deliverable TASK --artifact ART --version-ref v...
python -m task_management.cli close TASK --summary-ref docs/...
python -m task_management.cli fail TASK --reason-ref docs/...
python -m task_management.cli quarantine TASK --reason-ref docs/...
python -m task_management.cli audit --db .agents/task-manager/task-manager.db
```

### 3.4 直接 DB 書込み禁止の設計

- migration と seed 以外の書込みは `TaskManager` transaction 経由に限定する。
- SQLite trigger は最後の防衛線として、不正な status event と孤立参照を拒否する。
- CLI は facade の薄い wrapper にし、CLI と Python API で規則を二重実装しない。
- `task_events` は append-only とし、修正が必要な場合は correction event を追加する。
- DB 破損が疑われる場合、facade は自動修復せず `audit` で検出し、owner 判断を要求する。

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
    'created', 'status_changed', 'claimed', 'artifact_recorded',
    'evaluation_recorded', 'shipping_prepared', 'inventory_recorded',
    'validation_recorded', 'deliverable_marked', 'correction'
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
    'observed_zero', 'missing'
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
    'tracked', 'ignored', 'local_only', 'untracked', 'remote_only', 'unknown'
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
  result TEXT NOT NULL CHECK (result IN ('pass', 'fail', 'unknown', 'partial', 'missing')),
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

> 注: 上記は設計案である。SQLite は `CHECK` 内でサブクエリを使えないため、cross-table invariant は facade transaction と trigger / audit query の併用で守る。

### 4.3 transition seed 案

```sql
INSERT INTO allowed_status_transitions(from_status, to_status, requires_facade_check) VALUES
('proposed', 'planned', 'plan refs exist'),
('planned', 'claimed', 'active claim absent'),
('claimed', 'in_progress', 'claim holder only'),
('in_progress', 'awaiting_evaluation', 'artifact refs exist'),
('awaiting_evaluation', 'accepted', 'all required evaluations pass'),
('accepted', 'shipping_ready', 'storage targets resolved'),
('shipping_ready', 'shipped', 'storage conditions pass and location refs exist'),
('shipped', 'inventoried', 'inventory records exist'),
('inventoried', 'validating', 'inventory records exist'),
('validating', 'validated', 'all required validations pass'),
('validated', 'deliverable_ready', 'validation pass and eligible artifact'),
('deliverable_ready', 'closed', 'summary exists'),
('proposed', 'failed', 'reason required'),
('planned', 'failed', 'reason required'),
('claimed', 'failed', 'reason required'),
('in_progress', 'failed', 'reason required'),
('awaiting_evaluation', 'failed', 'reason required'),
('validating', 'failed', 'reason required'),
('awaiting_evaluation', 'quarantined', 'reason required'),
('shipping_ready', 'quarantined', 'reason required'),
('shipped', 'quarantined', 'reason required'),
('validating', 'quarantined', 'reason required');
```

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
| `closed` | task 完了。release 実行を意味しない。 |
| `failed` | 条件不成立または実行不能として停止。 |
| `quarantined` | 不明・不合格・private / restricted の疑いなどにより隔離。 |

### 5.2 代表シナリオ

#### 正常系

1. `create` → `proposed`
2. `plan` → `planned`
3. `claim` → `claimed`
4. `start` → `in_progress`
5. `record_artifact` → `awaiting_evaluation`
6. `record_evaluation(result=pass)` → `accepted`
7. `prepare_shipping` → `shipping_ready`
8. `record_inventory` / `mark_shipped` → `shipped` → `inventoried`
9. `record_validation(result=pass)` → `validating` → `validated`
10. `mark_deliverable` → `deliverable_ready`
11. `close` → `closed`

#### 異常系・エッジケース

- Acceptance Evaluation が `unknown` の場合、`accepted` / `shipping_ready` へ進めず `quarantined` または owner 判断待ちにする。
- `collection_failed` は `observed_zero` に変換しない。
- `Storage Target` が `remote` でも release 済みとは扱わない。
- Inventory が存在しない artifact は validation pass にできない。
- Validation Result が `fail` / `unknown` / `partial` / `missing` の場合、deliverable にできない。
- active claim がある task は別 agent が `start` できない。ただし claim 期限切れは再取得可能にする。

## 6. 不変条件・ゲート

Facade は少なくとも次を強制する。

1. **Acceptance Evaluation なしに Shipping へ進めない。**  
   `awaiting_evaluation -> accepted` は、必須 condition / validation item に対する `task_evaluations.result='pass'` が揃う場合だけ許可する。
2. **Storage Condition 未解決なら `shipped` にできない。**  
   `shipping_ready -> shipped` は `task_storage_targets.resolved_result='pass'` と location 参照が必要。
3. **Inventory 記録なしに Validation 完了にできない。**  
   `task_validations.inventory_id` は必須。`validating -> validated` は対象 artifact の Inventory が揃う場合だけ許可する。
4. **Validation Result が `pass` でなければ Deliverable にできない。**  
   `mark_deliverable` は `task_validations.result='pass'` の validation_id だけ受け付ける。
5. **Deliverable と Release は別物。**  
   `deliverable_ready`、`release_candidate_ref`、`release_ref` は release 実行を意味しない。publication / release gate は別工程。
6. **DB は作業管理であり、研究データの source of truth ではない。**  
   DB 破損時に artifact を DB から復元する設計にしない。
7. **DB は本文を持たない。**  
   task / issue / plan / evaluation / validation / summary の本文は Markdown 等の path を source of truth とし、DB は path・checksum・状態・時刻・短い機械用 enum だけを保持する。
8. **raw は参照のみ。**  
   `data_layer='raw'` の artifact は参照可能だが、facade は raw 編集・置換・採用判定を行わない。
9. **秘密情報を保存しない。**  
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

- **正常系:** 空 DB に migration を適用すると `tasks`、`task_document_refs`、`task_events`、`task_artifacts`、`task_evaluations`、`task_storage_targets`、`task_inventory_records`、`task_validations`、`task_deliverables`、`agent_claims` が作成され、transition seed が入る。
- **異常系:** foreign key off / migration checksum 不一致 / duplicate active claim は失敗する。
- **データ例:** `task_id='task_20261016_0001'`、`task_doc_path='.agents/task-manager/tasks/task_20261016_0001.md'`、`contract_ref='contract-ledger:...'`、`study_ref='datasets/cannabinoid-platform-trends'`。
- **受け入れ条件:** CI の一時 DB で migration test が通る。実 DB は commit されない。
- **優先度:** P1。

### Step 3: facade skeleton

- **正常系:** `TaskManager.create(task_doc_path=...)` / `plan()` / `claim()` / `start()` が transaction で task と event を作る。
- **異常系:** DB 直書きで壊れた current_status、期限内 active claim、許可外 transition を拒否する。
- **受け入れ条件:** CLI なしでも Python API から最小 lifecycle を動かせる。本文文字列を DB に渡す API は作らない。
- **優先度:** P1。

### Step 4: transition validation tests

- **正常系:** `proposed -> planned -> claimed -> in_progress` が許可される。
- **異常系:** `proposed -> shipped`、Acceptance Evaluation なしの `shipping_ready`、Inventory なしの `validated`、Validation fail の `deliverable_ready` が拒否される。
- **エッジケース:** `collection_failed` と `observed_zero` が別 result として記録される。
- **受け入れ条件:** 不正確なデータの出荷につながる遷移がテストで落ちる。
- **優先度:** P1。

### Step 5: CLI

- **正常系:** 後続エージェントが `create`、`claim`、`record-evaluation`、`prepare-shipping`、`record-inventory`、`record-validation`、`mark-deliverable` を CLI だけで実行できる。
- **異常系:** payload や secret らしき入力、本文文字列、絶対 path の誤用、raw 編集を示唆する操作を拒否または警告する。
- **受け入れ条件:** CLI は facade の wrapper で、独自の transition 規則を持たない。
- **優先度:** P2。

### Step 6: audit command

- **正常系:** `audit` が不整合なしを exit 0 で報告する。
- **異常系:** status/event 不一致、orphan artifact、active claim 重複、deliverable と validation pass の不一致、DB に本文を入れた疑い、絶対 path / 長すぎる ref を exit 1 で報告する。
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
| SQLite 同時書き込み | 複数 agent が同時に claim / update して lock 競合する。 | WAL、busy_timeout、短い transaction、partial unique index、claim TTL。remote 共有 DB は当面扱わない。 | 要 owner 判断: 同時実行の上限と retry 方針。 |
| Multi-agent claim / lock | claim 放置で task が進まない。 | `expires_at` を必須化し、期限切れは再 claim 可能。release は明示記録。 | 要 owner 判断: TTL の標準値。 |
| DB を commit するか | ローカル状態・機微 metadata・環境差分を repository に混入する。 | DB は commit しない。schema / migration / docs / tests のみ commit。 | 推奨決定案。 |
| DB が本文の第二正本になる | issue / task / 研究内容本文を DB に入れると Markdown と矛盾し、リポジトリ汚染や機微情報混入につながる。 | 本文は `.agents/.../*.md` または既存 `docs/issues/...` 等の file path を正本にし、DB は path / checksum / status / timestamp / enum だけを保持。監査で長すぎる ref・絶対 path・content flag を検出する。 | 追加要件として反映済み。 |
| issue docs / milestones との関係 | issue docs と DB の二重管理で矛盾する。 | issue docs は人間向け計画・判断記録の本文正本、DB は作業状態と facade invariant の索引。相互参照は path / ID / checksum だけ。 | 要 owner 判断: issue から task を生成するか。 |
| audit snapshots との関係 | DB audit と `docs/audits/` を混同する。 | task DB audit は作業 DB の整合性検査。研究データ監査スナップショットを代替しない。 | 明記済み。 |
| Storage Target / Inventory の粒度 | 1 task に複数 artifact / target があると status が粗くなる。 | task_artifacts / targets / inventory を多対一で持ち、status は aggregate 状態として扱う。 | 要 owner 判断: artifact 単位 task に分ける閾値。 |
| Release 連携 | deliverable_ready を release 済みと誤解する。 | `release_ref` は外部参照だけ。release command は提供しない。 | 明記済み。 |
| Remote storage 連携 | 将来 GitHub / Zenodo API を呼びたくなる。 | v1 は外部送信なし。将来は別 contract / publication gate / owner 承認後。 | 将来課題。 |
| 契約条件の参照形式 | `condition_ref` の命名が未統一だと照合できない。 | 初期は opaque ref。正式な condition registry が必要なら Contract 側で owner 判断。 | 要 owner 判断。 |
| タスク管理基盤の bounded context | 研究管理基盤 core の一部か supporting tool か。 | 本書では「横断的 local work-management facade」として扱い、既存 DDD 正本を変更しない。 | 要 owner 判断。 |

## 11. Owner 判断が必要な点

1. `src/task_management/` を新規 package として置くか、既存 `src/research/` 配下の workflow 管理とみなすか。
2. `condition_ref` / `validation_item_ref` / `storage_condition_ref` の正規 ID 体系を Contract 側で定義するか。
3. claim TTL の標準値と、期限切れ claim を誰が破棄できるか。
4. task DB から issue docs / milestones を生成または同期するか。それとも相互参照だけに留めるか。
5. deliverable_ready 後の release candidate 連携を、いつ・どの gate 契約で扱うか。

