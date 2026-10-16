# U3 判断材料: validation ↔ storage の隣接 protocol

**状態:** owner決定済み（2026-10-16：隣接 protocol として正式化を採用。コード変更なし）。
**親文書:** `docs/domain/context-map.md` §4 U3。定義の正本は `docs/specs/contracts.md`。DDD 用語としての「保管 Storage」「目録 Inventory（インベントリー）」「出荷 Shipping」は `docs/domain/glossary.md` に登録済み。
**採用ER:** `docs/plan/20261016.md`（2026-10-16 採用、plan / adopted draft）。ER と DDD の対応は本書 §3。
**実測日:** 2026-10-16（コード現物の引用。推測で補わない）。

## 1. 実測（Observed）

双方向の辺はパッケージレベルに存在する。モジュールレベルの循環 import はない。

| 方向 | 辺 | 目的 |
|---|---|---|
| validation → storage | `src/validation/storage_contract.py:44-47` が `storage.contracts` / `storage.readers` / `storage.registry` / `storage.sniff` を import | G4 保管契約の検査（S1 / S6–S9 / §11–§13 の content・contract レベル検査） |
| storage → validation | `src/storage/inventory.py:31-33` が `validation.integrity.sha256_file` を import（他は `storage.registry` / `storage.sniff`） | G4 §16 目録（inventory）の走査前後ハッシュ取得（`raw_modified` 証拠） |
| 閉路なし | `src/validation/integrity.py:32-35` は validation 内のみ import（storage に触れない）。`storage/inventory.py` は `validation.storage_contract` を import しない | Python の循環 import 障害は発生しない |

補足（隣接の参考実測。U3 の辺そのものではない）:

- `src/collection/core/staging.py:51-53`、`src/research/views.py:32-35` も `storage.*` を読むが、これは生産・研究→保管の参照であり、validation ↔ storage の双方向とは別の辺である。
- 既存の境界テスト T1（`tests/domain/test_production_verification_separation.py`）は生産↔検証（P5 方向）のみを検査し、validation ↔ storage は対象外である。

## 2. 分類: 実装上の問題か、自然な関係か

両方に分けて記録する。どちらか一方だけでは説明にならない。

- **実装上の観点では、今日のところ障害ではない。** モジュール間の閉路がなく、import 障害は起きない。残るのは将来の結合度リスク（うっかり閉路を作りやすい形）だけである。
- **契約・台帳・監査上の観点では、自然な関係である。** 台帳は `storage-reader-contract-v1` の `enforced_by` を `validation.storage_contract` と記録している（owner = storage、検査 = validation）。所有と検査の分離は `contracts.md` §4 規則2 が許す形と同型である。逆方向の `sha256_file` 共有は、目録（保管対象の非破壊棚卸し）で使うハッシュ primitive の再利用であり、判定意味の共有ではない。
- **境界上の位置では、本マップの範囲外同士の隣接事実であり、隣接 protocol として固定する。** 保管も検証も本マップでは範囲外・辺の相手方としての記載に留まる（context-map §3）。生産・研究・契約の境界はこの辺に触れない。許可する辺と禁止は本書 §4 のとおり。

## 3. 採用ERとDDDの対応

`docs/plan/20261016.md` の採用ER（plan / adopted draft。機械検査の正本ではない）を DDD 側でどう読むか。用語の正本は `contracts.md`、写しは glossary。

| ER | DDD での読み方 |
|---|---|
| `CONTRACT` が `ACCEPTANCE_CONDITION` / `VALIDATION_ITEM` / `STORAGE_CONDITION` を defines | 契約は検収条件・検証項目・保管条件を含む（`contracts.md` §2、glossary 契約）。1契約が複数の保管対象・保管先を束ねること（1契約:多保管）を許容する |
| `CONTRACT` が `TERMS_OF_SERVICE` / `THIRD_PARTY_CONSTRAINT` を incorporates、`LEGAL_FRAMEWORK` を references | 契約内容の由来（規約・法令・第三者制約）。収集条件・制約の根拠であり、本 protocol の対象外 |
| `CONTRACT` が `STUDY` を governs | 研究 Study 集約が契約に統治される関係（`contracts.md` §2 研究） |
| `PRODUCTION` が `ACCEPTANCE_EVALUATION` を performs（`ACCEPTANCE_CONDITION` / `VALIDATION_ITEM` を evaluates、`CONTRACT` に follows） | 生産は契約に含まれる検収条件・検証項目を評価する（U5・`contracts.md` §3.1 規則1）。判定ルール・判定理由・可否の意味は独自所有しない |
| `PRODUCTION` が `SHIPPING` を prepares（`CONTRACT` に follows、`ARTIFACT` を ships、`STORAGE_TARGET` へ to） | 出荷は契約の検収条件・検証項目・保管条件を満たした成果物を指定保管先へ引き渡す工程（glossary 出荷）。リリースとは別 |
| `STORAGE` が `STORAGE_TARGET` を has（`LOCAL_STORAGE` / `REPOSITORY_STORAGE` / `REMOTE_STORAGE`。REMOTE は `GITHUB` / `ZENODO` を may be） | 保管先の種別（local / repository / remote）。生産/出荷の引渡し先 |
| `STORAGE` が `ARTIFACT` を stores、`INVENTORY` を maintains | 保管が成果物を保持し、目録を維持する関係 |
| `INVENTORY` が `ARTIFACT` を records、`STORAGE_TARGET` の location in を records、`STORAGE_CONDITION` の checking を supports | 目録はどこに何が保管されているかを知るための非破壊記録。判定ではない |
| `ARTIFACT` が `VALIDATION` を undergoes、`VALIDATION` が `VALIDATION_RESULT` を produces（`VALIDATION_ITEM` / `STORAGE_CONDITION` を checks、`INVENTORY` を uses） | 検証は保管条件が満たされているかを見るため、保管の public interface と目録を読んでよい。検証は保管物を生成・変更しない |
| `VALIDATION` が `DELIVERABLE` を qualifies、DELIVERABLE は `VERSION` で identified | 検証を通過した成果物とその版表示（契約の版管理の対象） |
| `RELEASE` が `DELIVERABLE` を distributes、`VERSION` を packages、`SHIPPING` に depends on | リリースは配布単位・配布行為であり出荷とは別。出荷済みであることに依存する |

## 4. 隣接 protocol（正式方針。owner決定 2026-10-16）

保管と検証は隣接する。どちらも本マップの範囲外同士であり、生産・研究・契約の境界はこの辺に触れない。許可する辺と禁止を次に固定する。

### 許可する辺（allowlist。現状の辺として固定）

| 方向 | 辺 | 目的（ER との対応） |
|---|---|---|
| validation → storage | `validation.storage_contract` → `storage.contracts` | G4 保管契約の検査（§3 ER：`VALIDATION_RESULT` が `STORAGE_CONDITION` を checks） |
| validation → storage | `validation.storage_contract` → `storage.readers` | 同上（S7 / S8 / S9 の reader 依存検査） |
| validation → storage | `validation.storage_contract` → `storage.registry` | 同上（registry 文書 consistency） |
| validation → storage | `validation.storage_contract` → `storage.sniff` | 同上（S6 format 実測） |
| storage → validation | `storage.inventory` → `validation.integrity.sha256_file` | 目録走査前後ハッシュ取得（`raw_modified` 証拠）。hash primitive の再利用であり、判定意味の共有ではない（§3 ER：`INVENTORY` が checking を supports、RESULT が `INVENTORY` を uses） |

いずれも read 系参照または primitive 再利用であり、モジュール間の閉路はない（§1）。

### 禁止

- 保管・目録が gate / verdict / CLI / judgment を所有または参照すること。例：`storage/*` が `validation.gates`・`validation.storage_contract` の判定部分・`validation.cli`・判断記録（`metadata/publication/`）を import／参照しない。
- 検証が保管物を生成・変更すること。検証の関数は read-only（レポートは書くが、収集記録・加工成果物は作らない。`contracts.md` §3.1 規則2）。

### 本 protocol の辺ではないもの（従来どおり。混同しないこと）

- `src/collection/core/staging.py`、`src/research/views.py` の `storage.*` 読みは生産・研究→保管の参照であり、validation ↔ storage の双方向とは別の辺である。
- 既存の境界テスト T1（`tests/domain/test_production_verification_separation.py`）は生産↔検証（P5 方向）のみを検査し、validation ↔ storage は対象外である（対象外のまま変えない）。

## 5. 選択肢と状態（決定済み／将来再判断）

### 選択肢 1: 現状維持（隣接記録として明示し、解消しない）

- **状態:** **採用（一部として。本 protocol（§4）に吸収。コード変更なし）。**

- **内容:** context-map U3 行の記載を維持する。コード変更なし。
- **メリット:** 変更コストゼロ、ランタイムリスクゼロ。両端が範囲外であることと整合し、地図の責務を広げない。
- **リスク:** パッケージレベルの双方向が残る。将来のモジュール移動・import 追加で true cycle を作り込む余地が残る（ただし今日のテストは green）。
- **追加テスト候補:** T1 型の AST pin テストを validation ↔ storage 用に新設する（例: `storage/inventory.py` が validation から import してよいのは `validation.integrity.sha256_file` のみ、`validation/storage_contract.py` が storage から読むのは read 系 API のみ、を allowlist で固定）。doc-only で終えるか、この pin まで行うかは owner 判断。

### 選択肢 2: 依存方向を明示的に許可する protocol として固定する

- **状態:** **採用（doc-only 部分。方向・範囲・禁止の文書固定。本書 §4）。テストによる機械固定は 2026-10-16 T-J承認により `tests/domain/test_storage_validation_adjacency.py` として実装済み（§7 Q2）。**

- **内容:** 許可する方向と範囲を文書＋テストで固定する。例: validation → storage の read 系参照を許可、storage → validation はハッシュ primitive（`validation.integrity`）のみ許可、判定モジュール（`validation.gates` / `storage_contract` の判定部分）への逆依存は禁止。
- **メリット:** 例外ではなく規則になる。ドリフトを機械的に検出できる。
- **リスク:** 範囲外同士の関係に地図が口を出す形になり、境界文書の責務が膨らむ。allowlist の保守コストが発生する。`sha256_file` のような共有 primitive が増えるたびに規則改定が要る。
- **追加テスト候補:** 選択肢 1 の pin テストを両方向 allowlist 化したもの。既存 T1 と同形（stdlib AST 走査）のため実装は軽い。CI 配線（`research-validation.yml` への追加有無）も決める必要がある。

### 選択肢 3: 中間の contract abstraction に寄せる

- **状態:** **不採用（今回は見送り。将来 true cycle 兆候時の再検討とする）。**

- **内容:** 双方向を断つ。例: `sha256_file` を両者の中立な共有場所（あるいは storage 側の所有）に移し、storage → validation の辺を消す。完全形では reader protocol / descriptor の所有も整理する。
- **メリット:** 層構造が最もきれいになる。パッケージ循環の議論自体が消える。
- **リスク:** ランタイムコードの変更であり、影響範囲が広い（`sha256_file` の利用者は `collection/core/provenance.py`、`research/audit.py`、`research/views.py` にも及ぶ）。import 移行＋全 suite＋監査 freshness の再確認が必須。範囲外同士の辺のために生産・研究の import に触るのは費用対効果が悪い。
- **追加テスト候補:** 移行前後で `contract-ledger`・監査スナップショットの再生成一致（freshness）、全 suite green。pin テストは不要になる（辺が消えるため）。

## 6. 決定記録（owner決定 2026-10-16）

**選択肢 1 の現状維持（コード変更なし）と選択肢 2 の文書固定（方向・範囲・禁止の明文化）を合わせた隣接 protocol 正式化を採用する。** 理由：両端が本マップの範囲外であり障害の実害がない（閉路なし）ためコードは変えず、一方で採用ER（`docs/plan/20261016.md`）により契約・保管条件・保管先・目録・出荷・検証の関係が俯瞰できるようになったため、規則として書ける状態になった。選択肢 3（中間 abstraction）は今回は見送り、将来 true cycle の兆候が出た時点での再検討とする。**本決定は doc-only であり、台帳 owner・gate version・研究データ・監査出力に触らない。**

## 7. owner 確認事項（解決済み／将来再判断に整理）

- Q1: U3 を隣接 protocol として正式化してよいか（選択肢 1＋2 の doc-only 部分）。→ **解決済み。本書 §4・§6 のとおり採用。**
- Q2: pin テスト（allowlist AST）を追加するか、文書のみに留めるか。→ **解決済み（2026-10-16 T-J承認「U3隣接 protocol の allowlist test 追加」により実装：`tests/domain/test_storage_validation_adjacency.py`）。** 当初は文書正式化を主目的として見送ったが、許可辺のドリフト防止のため追加を承認。対象は実測済み2ファイル（`src/validation/storage_contract.py`・`src/storage/inventory.py`）に限定し、許可する辺は §4 の allowlist に限定する（広域スキャンは既存例の洗い出し後の別タスクに残す）。共有 primitive が増えるたびに規則改定が要る点は変わらない。
- Q3: 選択肢 2・3 に進む将来条件を今決めておくか。→ **解決済み（条件だけ確定）。** true cycle の兆候（import 障害・遅延 import の出現）が出た時点で再検討する。選択肢 3（中間 abstraction への寄せ）はその際の案とする。

## 8. 検証観点

- 本書の実測引用（ファイル・行）が現物と一致すること（`git diff --check`＋目視。行番号は 2026-10-16 に現物再確認済み）。
- doc-only であること：`src/validation/contract_ledger.py`・`docs/audits/contract-ledger.json`・研究データ・監査出力に触らない（台帳 owner・gate version 不変）。U4 に触らない。
- Q2 で将来 pin テストを選んだ場合：T1 と同形の AST 走査で green、新規テストが既存 suite を壊さないこと。許可する辺は §4 の allowlist に限定し、過剰な固定はしない。
- allowlist test（`tests/domain/test_storage_validation_adjacency.py` A1・A2）が green であること。対象は §4 の allowlist に限定した2ファイルのみとし、広域スキャンは別タスクとする。
