# U3 判断材料: validation ↔ storage の双方向依存

**状態:** 未解決（owner 決定待ち）。本書は決定ではない。最終判断は owner が行う。
**親文書:** `docs/domain/context-map.md` §4 U3。定義の正本は `docs/specs/contracts.md`。DDD 用語としての「保管 Storage」「目録 Inventory（インベントリー）」は `docs/domain/glossary.md` に登録済み。
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
- **境界上の位置では、本マップの範囲外同士の隣接事実である。** 保管も検証も本マップでは範囲外・辺の相手方としての記載に留まる（context-map §3）。生産・研究・契約の境界はこの辺に触れない。よって「本マップでは解消しない」扱いは一貫している。

## 3. 選択肢

### 選択肢 1: 現状維持（隣接記録として明示し、解消しない）

- **内容:** context-map U3 行の記載を維持する。コード変更なし。
- **メリット:** 変更コストゼロ、ランタイムリスクゼロ。両端が範囲外であることと整合し、地図の責務を広げない。
- **リスク:** パッケージレベルの双方向が残る。将来のモジュール移動・import 追加で true cycle を作り込む余地が残る（ただし今日のテストは green）。
- **追加テスト候補:** T1 型の AST pin テストを validation ↔ storage 用に新設する（例: `storage/inventory.py` が validation から import してよいのは `validation.integrity.sha256_file` のみ、`validation/storage_contract.py` が storage から読むのは read 系 API のみ、を allowlist で固定）。doc-only で終えるか、この pin まで行うかは owner 判断。

### 選択肢 2: 依存方向を明示的に許可する protocol として固定する

- **内容:** 許可する方向と範囲を文書＋テストで固定する。例: validation → storage の read 系参照を許可、storage → validation はハッシュ primitive（`validation.integrity`）のみ許可、判定モジュール（`validation.gates` / `storage_contract` の判定部分）への逆依存は禁止。
- **メリット:** 例外ではなく規則になる。ドリフトを機械的に検出できる。
- **リスク:** 範囲外同士の関係に地図が口を出す形になり、境界文書の責務が膨らむ。allowlist の保守コストが発生する。`sha256_file` のような共有 primitive が増えるたびに規則改定が要る。
- **追加テスト候補:** 選択肢 1 の pin テストを両方向 allowlist 化したもの。既存 T1 と同形（stdlib AST 走査）のため実装は軽い。CI 配線（`research-validation.yml` への追加有無）も決める必要がある。

### 選択肢 3: 中間の contract abstraction に寄せる

- **内容:** 双方向を断つ。例: `sha256_file` を両者の中立な共有場所（あるいは storage 側の所有）に移し、storage → validation の辺を消す。完全形では reader protocol / descriptor の所有も整理する。
- **メリット:** 層構造が最もきれいになる。パッケージ循環の議論自体が消える。
- **リスク:** ランタイムコードの変更であり、影響範囲が広い（`sha256_file` の利用者は `collection/core/provenance.py`、`research/audit.py`、`research/views.py` にも及ぶ）。import 移行＋全 suite＋監査 freshness の再確認が必須。範囲外同士の辺のために生産・研究の import に触るのは費用対効果が悪い。
- **追加テスト候補:** 移行前後で `contract-ledger`・監査スナップショットの再生成一致（freshness）、全 suite green。pin テストは不要になる（辺が消えるため）。

## 4. 推奨案（案であり決定ではない）

**選択肢 1（現状維持）を推奨する。** 理由: 両端が本マップの範囲外であり、障害の実害がない（閉路なし）ため、地図側で解消する責務がない。pin テスト（選択肢 1 の候補）を付けるかどうかだけ owner に諮りたい。選択肢 2・3 は、将来 true cycle の兆候（import 障害・循環回避のための遅延 import の出現）が出た時点での再検討で足りる。

## 5. owner に確認すべき決定事項

- Q1: U3 を「本マップでは解消しない」のまま維持してよいか（選択肢 1）。
- Q2: pin テスト（allowlist AST）を追加するか、文書のみに留めるか。
- Q3: 選択肢 2・3 に進む将来条件（例: 循環 import 障害の発生、遅延 import の出現）を今決めておくか。
- いずれも本書では解決済みにしない。決定が出たら context-map U3 行と本書の状態欄を更新する。

## 6. 検証観点

- 本書の実測引用（ファイル・行）が現物と一致すること（`git diff --check`＋目視）。
- Q2 で pin テストを選んだ場合: T1 と同形の AST 走査で green、新規テストが既存 suite を壊さないこと。
- 選択肢 3 を選んだ場合のみ: 全 suite＋監査スナップショット再生成一致。選択肢 1・2 では研究データ・台帳・監査出力に触らない。
