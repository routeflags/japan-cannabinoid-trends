# Issue: 旧 GT run（phase-a 系）の系列ラベルに年誤りの疑い（`2026-12-28`）

**ID:** ISS-20261015-GT-002
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m/`, `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m/`（凍結 legacy。本 issue では変更しない）

## 概要

ISS-20261015-GT-001 の境界対応表（`python -m validation.cli boundary-report`）が、
phase-a 系 2 run を `inconsistent` として報告した。原因は記録系列に収集時刻より
**未来の日付**（`2026-12-28`）が 1 点混入していること。

## 確認された観測

- `20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m`（collected 2026-10-12T05:53:04Z）
  の 53 点系列のうち、データ順で `2025-12-21` の直後に `2026-12-28` が入り、
  次が `2026-01-04`。つまり週ラベルは `2025-12-28` であるべき位置。
- 同型のファイルは 8 件（4 化合物 × 2 run）: phase-a の `records_{cbd,cbg,cbn,thc}-rikiddo.json`
  と phase-a-repeat の同 4 ファイル。各 53 点、ギャップは 14 日 ×1・78 日 ×1、
  他は 7 日。
- 同 2 run は boundary-report で `last_end_offset_days = +77.755` / `+77.746`（許容 ±7 日超）
  として報告される（`docs/reports/20261015b-gt-boundary-verification.md`）。

## 影響

- 該当系列を「週次 53 点の連続系列」として下流変換（月次集計等）すると、
  1 点が誤った年に入る。
- GT-001 の昇格判断には影響しない（legacy は計測コホート外）が、このままでは
  legacy データの不整合が暗黙に伝搬する。

## 対応方針

- 8 ファイルの該当ラベルの扱いを決定する（下流補正するか、記録のみで残すか）。
- 補正する場合は raw を編集せず、補正規則（対象ファイル・変換・根拠）を
  `interim/` 以下の再現可能な変換として記録する（AGENTS.md: raw 不変）。
- 原因（記録時変換の年誤りか、元応答の異常か）は特定できていない。生応答
  `raw_text` が保持されているファイルでは照合可能（未実施）。

## 完了条件

- [x] 該当 8 ファイルのラベル扱いの決定（補正 / 記録のみ）
- [x] 補正する場合、非破壊の下流変換と根拠の記録、監査スナップショットの再生成
- [x] 原因の切り分け（原本 `raw_text` との照合）

## 対応記録（2026-10-15）

- 扱いは **downstream 補正** とした。raw JSON は凍結 legacy として編集しない。
- `src/processing/gt_legacy_label_corrections.py` を追加し、該当 8 ファイルについて
  `2026-12-28` を downstream では `2025-12-28` と読む補正 manifest を決定論的に生成する。
- 生成物は `datasets/cannabinoid-raw-collection/data/interim/google_trends/20261015_gt_legacy_label_corrections.json`。
  layer は `interim`、`raw_files_modified=false`、対象 raw ファイルの sha256 と `raw_text` 根拠を記録する。
- 原本照合:
  - `phase-a-repeat` の 4 records は各 `records_*.json` 内の `raw_text` が
    `Dec 28, 2025 – Jan 3, 2026` を示す。
  - `phase-a` の 4 records は per-term `raw_text` が無いため、同 run の
    `comparison_ja1.json` 内 `raw_text` の同ラベルを日付根拠として使う。comparison の値は
    比較表スケールなので単独系列値とは比較しない。
- `correct_record()` はコピーを返し、対象点の日付だけを `2025-12-28` に変える。値・raw 入力は変更しない。
- 検証:
  - `.venv/bin/python -m pytest tests/processing/test_gt_legacy_label_corrections.py` → 4 passed
  - `.venv/bin/python -m processing.cli gt-legacy-label-corrections --output /tmp/gt-corrections-check.json --format json` → exit 0

**ステータス: RESOLVED（2026-10-15）**。
