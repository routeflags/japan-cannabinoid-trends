# G4 Storage Inventory（Phase 1）— 保存形式の棚卸し

**日付:** 2026-10-13
**仕様:** `docs/plans/20261013d.md` §16 / §19 Phase 1（ローカル計画書）
**機械可読版:** [`g4-storage-inventory.json`](./g4-storage-inventory.json)（再生成: `python -m validation.cli audit-artifacts`）
**非破壊:** 読取専用。対象ファイルの sha256 を走査前後で比較し `raw_modified: false`。

> **2026-10-13 注記（鮮度）:** 本文の件数はこのスライス時点の記録。同日に JSON を
> 再生成し、現在は **76 件 / 29 run**（X 投稿 CSV の公開取り下げ分が減）。
> **現在の状態は JSON を参照すること。** 本 `.md` は日付付きの記録として残し、自動検証
> の対象外としている。

---

## 1. 対象と方法

- 対象: `datasets/**/data/**` の成果物ファイル **77 件 / 29 run**（すべて legacy。
  manifest は未導入）。
- run マーカー（`run_metadata.json` / `artifact-manifest.json` /
  `quarantine-reason.json`）は成果物ではないため一覧から除くが、ハッシュ保護と
  run 情報には使用する（存在状態は run 単位で記録）。
- 意味判定は **内容ベース**（`storage.sniff`）。ファイル名は補助のみで、意味を
  確定しない（P3 / §16）。判定の根拠は各エントリの `notes` に記録する。
- 判定語彙（§16）と優先順位:
  `unknown_format` → `ambiguous` → `recognized`（schema 登録 + active な reader が
  解決）→ `missing_metadata`（manifest も run metadata も無い）→
  `partially_recognized`（format は判明、schema 未登録・変種形状）。
- `private/` ディレクトリ（匿名化対応表等）は**既定で除外**（AGENTS.md）。
  含める場合は `audit-artifacts --include-private`（値は一切出力しない）。

## 2. 結果サマリ（リポジトリ範囲、2026-10-13）

| 判定 | 件数 |
|---|---|
| `recognized` | 53 |
| `partially_recognized` | 16 |
| `missing_metadata` | 8 |
| `unknown_format` / `ambiguous` | 0 |

| format | 件数 |
|---|---|
| json | 72 |
| csv | 4 |
| text | 1 |

| artifact_type | 件数 |
|---|---|
| timeseries | 34 |
| summary | 13 |
| comparison | 4 |
| raw_response | 3 |
| raw_records | 1 |
| 未確定（legacy 変種等） | 22 |

すべて `manifest: missing`（legacy）。検証不能の明示と lineage の扱いは §6 を参照。

## 3. summary と full timeseries の区別（§12）

- **summary 13 件**: `contains_full_timeseries = false` / `record_count = null`。
  集計値（`data_points` 等）は `declared_data_points` として別記録し、
  記録件数として扱わない（§6.2）。
- **timeseries 34 件**: `data` 配列に実値があり、`contains_full_timeseries = true`
  / `record_count` は実点数。
- 実例（ファイル名と内容が一致しない実データ）:
  - `records_crdh_5y.json`・`records_thc_o_5y.json` など「records」を名乗るが、
    内容は `first_mention` / `peak` / `data_summary` のみの**要約**。
  - `records_cbd-rikiddo-5y.json` は `data:[{date,value}]` を持つ**フル時系列**。
  → 名前で判定すると混同する。内容で判定し、両者を別 artifact type とする。
- 混同防止は reader 契約でも強制する: `json-summary-reader` は `points` モードを
  持たず、要約をフル時系列として読む要求は拒否される（`storage.cli read --mode
  points` は exit 1。P8: 再構成しない）。

## 4. ページ分割と「取得失敗 / ゼロ」の区別（§11）

- リポジトリ範囲にページ分割コレクションは存在しない（`groups: []`）。
- 実装済みの判定（`storage.inventory`。月別 / 年+サブページ / 週別 / 連番
  `page_NNNN`）:
  - `expected_pages`: run metadata の期間が導出できる場合はその全ページ、
    できなければ観測範囲（その場合 `complete` とは判定しない = `unverified`）。
  - **欠落ページ = `missing_pages`**（取得失敗 / 未収集であり、ゼロではない）
  - **存在して 0 件のページ = `observed_zero_pages`**（`state: observed_zero`）
  - 重複インデックス・期待範囲外インデックスは別途報告する。
- リポジトリ範囲の 29 run は Google Trends のみのためグループは空。ローカル
  専用データ（Git 管理外の YouTube 月別・年別ページ、X checkpoint ページ）では
  `--datasets-root <local checkout>/datasets` で同じ判定を実行できる。
  ローカル結果は個人情報・再配布審査の対象になり得るため**コミットしない**
  （検証手順は `docs/specs/validation-framework.md` の G4 節を参照）。

## 5. SQLite（`trends.db`）の扱い — 決定（2026-10-13）

- リポジトリ内に SQLite 成果物は**存在しない**。監査はそれを
  `sqlite_present: false` として記録する（存在しないハッシュやレコードを
  作らない = P8）。「ゼロ件の DB」ではなく「監査範囲に DB が無い」の意味。
- 契約は宣言済み: `sqlite-reader`（read-only、`mode=ro` URI）/
  `sqlite-trends-db-v1` / database artifact の lineage 必須（§13、T12）。
- 存在時のみ検証する: 読み取り専用でテーブル列挙・行数・`record_lineage`
  テーブルの有無のみを報告し、レコード値は出力しない。
- ローカル専用 DB（`datasets/x-consistency/data/trends.db`、
  `datasets/youtube-consistency/data/trends.db`、バックアップ）は Git 管理外
  のためリポジトリ監査の対象外（ローカルでのみ同じコマンドで検証可能）。

## 6. Lineage / manifest 不在の明示（検証不能の明示）

- 全 77 件が `manifest: missing`（legacy）。`derived_from` の不明は
  `lineage:unknown` と明示し、推測で埋めない（P8）。
- 各成果物と各 run に `verification` を記録する: legacy は全件
  `unverifiable_no_manifest`（**検証不能であることを明示**し、存在しない
  ハッシュを捏造しない）。manifest を持つ run は `manifest_present` となり、
  L1（`gate-run` / `collect`）の S3-S12 検証対象になる。
- manifest を持つ新規 run の改ざんは `ARTIFACT_HASH_MISMATCH` として拒否される
  （quarantine / exit 1。2026-10-13 の replay で実測）。

## 7. 未登録形式（G5 以降への引き継ぎ）

`partially_recognized` 16 件の内訳（判定根拠付き）:

| 形式 | 件数 | 根拠 | reader 登録の扱い |
|---|---|---|---|
| comparison の averages のみ（系列なし） | 9 | `comparison:averages_only` | 未登録（§12 の区別を維持） |
| related queries の複数語バッチ / queries+object | 2 | `fields:queries` | 未登録 |
| no-data 応答 | 1 | `fields:no_data_keywords` | 未登録（G3 の閾値未満と対応） |
| notation presurvey | 1 | `fields:comparisons` | 未登録 |
| 分散解析・差分（analysis 形状） | 3 | `json_object` | 未登録 |

追加する場合は §7 の手順（reader 実装 → registry 登録 → contract test）で行う
（G4-T17）。登録すると監査スナップショットが変わるため、再生成とドリフトテストの
更新が必要になる（意図的な変更として扱う）。

## 8. 再現

```bash
.venv/bin/python -m validation.cli audit-artifacts \
  --output docs/audits/g4-storage-inventory.json

# ローカル専用ストアを含めた棚卸し（Git 管理外。結果はコミットしない）
.venv/bin/python -m validation.cli audit-artifacts \
  --datasets-root "<local checkout>/datasets" \
  --output /tmp/g4-local-inventory.json
```

`tests/validation/test_storage_inventory_audit.py` が再計算一致・`raw_modified:
false`・29 run・manifest 不在の明示・summary/timeseries 非混同を機械的に強制する
（スナップショットのドリフト検出）。

## 9. 限界

- 内容判定は形状ヒューリスティックであり、既知の実データ形状に対して検証して
  いる。新しい変種は `ambiguous` / `partially_recognized` として現れ、勝手に
  スキーマへ割り当てられない（その分は人手レビュー対象）。
- SQLite 実データ・ページ分割の実データ検証はローカル環境でのみ実施可能
  （CI は非公開 raw を扱わない）。
- 監査は記録であり、公開判定ではない。公開可否は G6 の
  publication gate（`docs/specs/validation-framework.md` の G6 節）で別途判定する。
