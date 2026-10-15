# staging 境界（`stage_run` / `adopt_staged`）の独立検証 — 2026-10-15

外部 collector の staging 産出側（commit `fae7fe2`、当時の HEAD）を、実装者とは
別の作業域・別スクリプトで検証した記録。**リポジトリは変更していない**（検証後
`git status --porcelain` が空）。

- 検証方法: 独立 worktree（clean checkout、Python 3.14.6 / cerberus 1.3.8 / pytest 9.1.1）、
  検証スクリプトは `/tmp` 配下、入力は tracked な実記録 Google Trends 応答
  （`datasets/cannabinoid-multi-trends/data/raw/google_trends/
  20261012T064246Z-google-trends-ja-rikiddo-5y-main5/records_cbd-rikiddo-5y.json`、
  262 点 / 2021-10-10 .. 2026-10-11）。
- 判定は **verified / refuted / unverifiable** の 3 値。拒否経路は実際に発火させて確認。

## 1. 主張別の判定

| # | 主張 | 判定 | 独立に確認したこと |
|---|---|---|---|
| 1 | `stage_run` は宣言された payload を byte 単位で staging する | verified | 独自 plan / 宣言で `action=staged`、payload は元ファイルと byte 一致、manifest の SHA-256 と byte_length はディスクから算出 |
| 2 | `adopt_staged` が L1 を通して catalog へ移す | verified | `action=adopted`、`l1.valid=True`、issues なし。`.staging/` からは移動（コピーでない） |
| 3 | 採用後は厳格検証（artifact 検証込み）で valid | verified | `verify_artifacts=True` で **全 severity で issue 0 件** |
| 4 | リポジトリ raw は読み取りのみ | verified | 前後で SHA-256（`hashlib` と `shasum -a 256` の両方）一致、`git status -- datasets` 空 |
| 5 | 自己収集経路（`collect`）の replay も同じ結論 | verified | fixture / plan を実行時に tracked ファイルから生成して `exit=0` / `adopted` / `l1.valid=True` |
| 6 | `audit-new-runs` が新規 run を凍結 legacy と区別する | verified（非空虚性も確認） | 新規 workspace で `new=1`、リポジトリ全体で `frozen_legacy_seen=29`。`query_provenance.query_id` を削った負の対照で `failure_count=1` |
| 7 | 全ゲート・全テストが green | **一部 refuted** | 各ゲートは再現。pytest は clean checkout で `914 passed / 3 failed / 6 skipped`（下記 §3） |
| 8 | 実記録 GT 応答の形状は adapter の想定と一致、テストはトートロジーでない | verified | tracked ファイルを独立に parse。テストは実行時にファイルを読み期待値を導出している |

拒否・改竄の検証（すべて fail closed、`.staging/` 作成前に停止）: artifact 不在、
`../` と絶対パス、未登録 collector、window フィールド欠落、終了 < 開始、naive 時刻。
採用時の改竄検出も実動作を確認（宣言 `record_count=999` → `ARTIFACT_RECORD_COUNT_MISMATCH`、
payload へ追記 → `ARTIFACT_HASH_MISMATCH` + `ARTIFACT_SIZE_MISMATCH`、raw は `.quarantine/` に保全）。

## 2. 指摘と対応

| # | 指摘 | 重大度 | 対応 |
|---|---|---|---|
| 1 | `adopt_staged` / `stage_run` が外部由来の `run_id` を無検証でパスに結合（`"../escaped-adopt"` が `datasets/<study>/data/` に採用・移動される） | Medium | **修正**（`RUN_ID_UNSAFE`。`study_id` も同型のため `STUDY_ID_UNSAFE` を追加）。spec 0.3.0 |
| 2 | `environment.adapter` が宣言側で上書きでき、docstring の「handover である」という記述と矛盾 | Low | **修正**（`environment` のパイプライン所有キーは宣言で置換できない。`collect` と同一規則） |
| 3 | 捏造された `observed_min/max_timestamp`・不正な時刻が採用される | Low | **受容**（payload の意味は検査しない設計。byte 一致・件数のみ検証）。§3.3 に明記 |
| 4 | `execution.status` の既定値 `"success"`（fail closed 経路の緩い既定） | Low | **修正**（`status` / `returned_count` の宣言を必須化 = `STAGING_EXECUTION_INCOMPLETE`） |
| 5 | staging が原子的でない（中断で部分ディレクトリが残り、再実行が `RUN_ID_ALREADY_EXISTS` で止まる） | Info | **受容**（fail closed。運用負担のみ）。§3.3 に明記 |
| 6 | artifact_id の slug 衝突は採用時に隔離される（遅い拒否） | Info | **受容**（fail closed。L1 の `ARTIFACT_ID_DUPLICATE` が正本で、stager に同じ規則を 2 実装しない） |

検証中に追加で確認した欠陥: 宣言された相対サブディレクトリ（`series/payload.json`）は
親ディレクトリを作らず **`FileNotFoundError` で落ちる**、`path="."` は `IsADirectoryError`
で落ちる（いずれも拒否コードではなく例外）。同じ修正で親を作成し、ファイル名を持たない
パスを `STAGING_ARTIFACT_PATH_UNSAFE` で拒否するようにした。

報告の `commit subject` の引用が 1 件誤っていた（同一 SHA）。

## 3. 「923 passed」の但し書き（要判断）

検証者の環境では `914 passed / 3 failed / 6 skipped`。原因は
`.gitignore` 対象の未追跡ローカルデータ（`datasets/*/data/private/`）で、
**この commit 固有ではなく親 commit でも失敗する既存問題**（親では 4 件失敗）。
ただし含意は残る:

- 追跡済みの `docs/audits/g7-study-inventory.json` は `cbx-social-trends` の
  `data_file_count` を **7** と記録しているが、これは未追跡ファイルを含む数で、
  clean checkout での再生成は **6** になる（`test_audit_report_freshness` が落ちる）。
  同じ型の依存が `docs/audits/g6-private-catalog.json`（private ディレクトリの
  `exists`）と `test_processed_artifacts.py::test_stale_declaration_is_reported`
  （private 入力からの再導出を前提）にもある。
- つまり「`pytest` 全 green」は**作者のマシンにしか成立しない**主張であり、
  コミット済みスナップショットが未追跡データに依存している。

対応: 追跡外データへの依存を **ISS-20261015-AUD-028** として記録した
（`docs/issues/closed/resolved/20261015_p1_audit-snapshots-assume-untracked-data.md`）。
規則は「コミットされる監査スナップショットは追跡ファイルだけで再生成できる」。
**未修正**（issue で追跡）。

## 4. 検証が覆っていない範囲

- **ライブ収集経路**（`SessionMcpTransport` / 実 MCP サーバ / ネットワーク）。
  検証したのはローカルファイルのリプレイ。したがって境界挙動（`exact=true` 昇格）は
  依然未検証（ISS-20261015-GT-001）。
- `stage` CLI / ソース別 staging ドライバ（未実装。ISS-20261015-COL-017）。
- 並行実行、部分書き込みからの復旧（§2 の #5）。
- `audit-new-runs` は payload のハッシュを検証しない（`validate_full` に
  `verify_artifacts` を渡さない）。壊れた payload は L1 / 採用時に捕捉される。

## 5. 総合判定

**境界の修正を条件に承認**。「外部 collector の経路が実 GT データで end-to-end に
動く」ことは、実記録応答の byte 単位の staging・L1 通過・厳格検証・新規 run 監査まで
**オフラインで実証されている**。指摘 1（境界のパストラバーサル）は本記録と同日に
修正済み。未実証はライブ収集経路のみ。
