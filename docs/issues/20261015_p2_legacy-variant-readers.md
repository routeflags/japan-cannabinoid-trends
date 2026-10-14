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

- [ ] 対象変種の一覧化（16 件の識別と代表例）
- [ ] 実装・登録した変種の reader と契約テスト
- [ ] 監査スナップショット再生成と鮮度テスト更新
