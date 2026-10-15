# Issue: legacy 変種 16 件の reader が未登録（storage contract の対象外）

**ID:** ISS-20261015-ART-006  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/artifacts/artifact-registry.json`, `src/storage/readers/`, `docs/audits/g4-storage-inventory.json`, `docs/specs/validation-framework.md` §17.3

## 概要

G4 の棚卸しで分類された legacy 変種（comparison の averages のみ、related queries のバッチ、
no-data 応答、分散解析 JSON など 16 件）は、schema / reader が未登録のため storage contract
の対象外で、`partial` 判定のままになっている。

## 確認された観測

- `metadata/artifacts/artifact-registry.json` の `artifact_schemas` は GT / YouTube / X /
  SQLite の計 10 件で、上記変種は含まれない。
- `validation/storage_contract.py` の S9 は未登録 schema を
  `ARTIFACT_READER_UNREGISTERED`（error）として返すため、これらを新規 run の raw にはできない。
- 登録時は監査スナップショットの再生成が必要（`tests/validation/test_audit_report_freshness.py`
  の registry）。

## 影響

- これら成果物の形式主張が人間の記述に依存し、機械検証（S6-S9）を受けない。
- 新規収集で同型のレスポンスを raw にした場合、reader 登録まで隔離される。

## 対応方針

- 実利用する成果物から順に reader を実装する（`src/storage/readers/__init__.py` docstring の
  手順: reader 実装 → registry 登録 → 契約テスト）。
- 形式の判定は実ファイルで行う。**推測で schema を当てない**（`storage/sniff.py` の状態機械に
  合わせる）。
- 監査スナップショットと鮮度テストの registry を同時に更新する。

## 完了条件

- [x] 対象変種の一覧化（16 件の識別と代表例）
- [x] 実装・登録した変種の reader と契約テスト
- [x] 監査スナップショット再生成と鮮度テスト更新

## 実装メモ（2026-10-15、OPEN のまま）

16 件中の最初の 1 変種（no-data 応答）のみ実装し、残り 15 件は未登録の
ため本 issue は OPEN のまま残す。外部 API は一切呼んでいない。

- 対象一覧（`docs/audits/g4-storage-inventory.md` §7 の 16 件。現 JSON では
  リポジトリ成長により `partially_recognized` 28 件）: comparison の
  averages のみ 9 件 / related queries バッチ・queries+object 3 件 /
  no-data 応答 1 件 / notation presurvey（`comparisons`）1 件 /
  分散解析・差分（analysis 形状）3 件ほか
- 実装スライス: no-data 応答（GT 品質に直結する「欠損はゼロではない」
  の機械保証。実ファイル
  `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261002T064135Z-google-trends-nodata/records_nodata.json`
  の形状のみで判定し、推測なし）
- 追加: `src/storage/readers/nodata.py`（`json-no-data-reader`。
  `keywords` モードのみ提供し `points` 等は拒否。per-bucket `data` を
  持つ文書は no-data として認めない。`count` は None
  ＝欠損エントリを件数として扱わない）
- 登録: `src/storage/sniff.py`（`fields:no_data_keywords` を
  `google-trends-no-data-v1` / `raw_response` の `recognized` に昇格）、
  `metadata/artifacts/artifact-registry.json`（reader＋schema 各 1 件。
  `record_count_mode: none`）、`src/storage/readers/__init__.py`
- 契約テスト: `tests/storage/test_sniff.py`（実ファイルの recognized 断言＋
  空リスト形状の維持）、`tests/storage/test_readers.py`（実ファイルの
  2 keyword 読解・`points` 拒否・系列混入拒否・ malformed 拒否・reader 一覧更新）
- スナップショット再生成手順:
  `PYTHONPATH=src python3 -m validation.cli audit-artifacts --output docs/audits/g4-storage-inventory.json`
  （差分は当該 1 件のみ: `partially_recognized` 28→27、
  `recognized` 65→66。`raw_modified: false` 維持）
- 検証: `PYTHONPATH=src python3 -m pytest tests/validation/test_audit_report_freshness.py tests/validation/test_storage_inventory_audit.py -q`
  （22 passed）。なお `.venv` が無い本 worktree では `PYTHONPATH=src` 無しの
  実行で鮮度テストの子プロセスが import 失敗する（変更前から 12 件失敗の
  環境要因。再生成内容自体は一致確認済み）

残り 15 件（averages のみ 9 件ほか）は実利用順に §7 手順で登録する。
特に averages のみ変種は `averages` / `average_interest` の 2 形状がある
ため、登録時は両形状の実ファイル照合を必須とする。
