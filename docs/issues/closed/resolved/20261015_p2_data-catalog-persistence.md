# Issue: Data Catalog の永続化先が未確定（オンデマンド生成のみ）

**ID:** ISS-20261015-ART-008  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `src/storage/catalog.py`, `storage.cli catalog`, `docs/specs/validation-framework.md` §17.3

## 概要

Data Catalog は `storage.cli catalog --output` で都度生成するのみで、保存先（例:
`datasets/<study>/metadata/data-catalog.json`）が決まっていない。棚卸し結果がリポジトリの
記録として残らない。

## 確認された観測

- `docs/audits/g4-storage-inventory.json` は監査出力であり、catalog 本体の永続化先は未定。
- `docs/audits/*.json` は鮮度テストの登録対象なので、代用にはできない。

## 影響

- artifact の棚卸しが時点依存で、過去の判断を再現できない。
- study 単位の成果物一覧を publication ときに参照できない。

## 対応方針

- 保存先と形式を決定し、生成器を配線する（既存の catalog 実装を再利用）。
- 既存 raw を変更しない。生成物は派生物として扱う。

## 完了条件

- [x] 保存先・形式の決定と文書化
- [x] 生成器の配線とテスト
- [x] 鮮度検査への登録要否の判断

## 実装記録（2026-10-15）

保存先（決定）: `datasets/<study-id>/metadata/data-catalog.json`（1 study 1
ファイル）。派生メタデータとして扱い、raw は変更しない。仕様は
`docs/specs/validation-framework.md` §17.1（決定）・§17.2（実装済み）に記録し、
§17.3 の未確定項目は解消済みとして更新した。

変更ファイル:

- `src/storage/catalog.py`: `CATALOG_FILENAME` / `catalog_path_for_study()` /
  `build_study_catalog()`（`build_catalog(<study>/data)` を再利用し規則を複製しない）/
  `dump_catalog()`（既存 `--output` と byte 互換の単一シリアライザ）/
  `write_catalog()`（同 dir tmp → `os.replace` の atomic 置換。失敗時は部分ファイルを
  残さず、既存ファイルも変更しない）を追加。出力は timestamp・絶対パスなし。
- `src/storage/cli.py`: `catalog --study-dir <study> --persist [--check-lineage]`
  を追加。`--persist` は `--study-dir` 必須・`--output` と排他。`--study-dir` 単独では
  当該 study の `data/` を範囲とするオンデマンド生成。`--check-lineage` 失敗時は
  書込み前に exit 1 し、正規ファイルを生成・更新しない（既存の良好版があれば保持）。
  manifest が無い study は拒否せず `count: 0` / `manifest_count: 0` の空 catalog を
  永続化する（空 datasets root と同じ規則）。既存 `catalog --datasets-root --output`
  の挙動は維持（シリアライザのみ `dump_catalog()` に一本化し、出力バイトは同一）。
- `tests/storage/test_catalog.py`: 永続化 13 件を追加（正規パス生成、`build_catalog`
  との一致、byte-identical 再生成・絶対パス混入なし、raw 不変、lineage 失敗時の
  未生成／既存保持、`--check-lineage` なしでの書込み、空 study の固定、引数不備の
  exit 2、既存 `--output` 互換）。
- `docs/specs/validation-framework.md`: §17.1・§17.2・§17.3 を更新。

検証:

- `tests/storage/test_catalog.py` + `test_storage_cli.py`: 28 passed。
- 実 study 実行: `catalog --study-dir datasets/cannabinoid-raw-collection --persist
  --check-lineage` → exit 0、16 entries / 8 manifests / errors 0。2 回実行で
  sha256 一致（byte-identical）。`datasets/**/data/raw` の差分なし。
- `validation.cli validate-registries`: valid（issues なし）。
- フルスイート: 1156 passed, 4 skipped。
- 注: `.venv` は当環境に存在しないため `PYTHONPATH=src python3` で実行。
  `release-archives/`・Zenodo・publication approval には触れていない。

鮮度検査の判断: 登録しない。catalog は追跡済み manifest からいつでも決定論的に
再生成でき、再実行一致自体が鮮度の証拠になる。監査面は既に鮮度登録済みの
`audit-artifacts`（`g4-storage-inventory.json`）が担う。study 単位の catalog を
鮮度テストに登録すると、run 採用のたびに再永続化が強制される運用負荷に見合わない。

残務・リスク:

- 生成物 `datasets/cannabinoid-raw-collection/metadata/data-catalog.json` は作業ツリーに
  未追跡のまま残している（派生出力であり、コミットは別判断。`data/processed/` 等と
  同様にコミット前例なし）。
- 他 study への永続化は未実行（必要になった study ごとに同コマンドで生成する）。
