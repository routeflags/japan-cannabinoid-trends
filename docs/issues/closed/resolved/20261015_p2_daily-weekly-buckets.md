# Issue: 日次・週次バケット集計が未実装（月次のみ）

**ID:** ISS-20261015-WIN-003  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `src/validation/windows.py`, `src/validation/coverage.py`, `docs/specs/validation-framework.md` §16.3

## 概要

バケット生成は月次のみ実装されており、日次・週次の集計は分析側に接続されていない。
coverage / missingness の機械評価は現状この粒度に依存できない。

## 確認された観測

- `validation-framework.md` §16.2 は月次バケット生成を実装済みとして記載し、
  §16.3 で日次/週次を未実装として明記している。
- `coverage-run` は run 単位のオンデマンド評価のみ（永続化は ISS-20261015-COV-004）。

## 影響

- 週次・日次の欠測判定を機械化できず、人手集計に依存する。
- 粒度の異なる run 同士の coverage 比較（T6/T7）ができない。

## 対応方針

- 月次実装と同じ契約（半開区間・タイムゾーン・週の開始曜日）で日次・週次を追加する。
- 境界規則は `metadata/windows/*.json` の `week_start` / `timezone` と整合させる。
- 推測でバケット境界を決めない（既存の window 正本を参照する）。

## 完了条件

- [x] 日次・週次バケット生成の実装とテスト
- [x] coverage / missingness 判定への接続
- [x] 境界規則（週開始・タイムゾーン）の文書化

## 実装記録 (2026-10-15)

PM 計画 `docs/plans/dev/20261015-daily-weekly-buckets-plan.md` の AC1–AC6 に
沿って実装・検証した。変更は加算のみで、既存の月次挙動・coverage 状態機械・
レガシー GT 例は不変。raw データ・公開承認・release メタデータ・Zenodo に
は触れていない。

### 変更ファイル

- `src/validation/windows.py`: `day_buckets` / `week_buckets` /
  `time_buckets(start, end, granularity, timezone_name, week_start)` を追加。
  `month_buckets` と同一契約（tz-aware 必須・半開区間・先頭/末尾の部分
  バケット保持・UTC ISO 出力）。`week_start` は `sunday` / `monday` のみ
  受理し、それ以外は `ValueError` で fail closed。
- `src/validation/coverage.py`: `temporal_provenance.granularity` が
  `day` / `week` / `month` かつ exact window 証拠がある場合、
  `expected_granularity` / `expected_intervals` /
  `missing_expected_intervals` を manifest に追加記録。欠測バケットは
  missing/unknown 証拠であり、`observed_zero` には変換しない。状態機械・
  既存 interval フィールドは不変。
- `tests/validation/test_windows.py` / `tests/validation/test_coverage.py`:
  AC1 の UTC 日次例、`Asia/Tokyo` の日次・週次（sunday/monday）、
  `America/New_York` の DST 跨ぎ日次、naive・逆転・未知 TZ・不正 week_start
  の失敗、欠測日の missing 扱い、月次不変をカバー。
- `docs/specs/validation-framework.md` §16.2/§16.3: 日次・週次を実装済みに
  移動する最小更新（ART-008 は commit 済みのため競合なし）。

### 境界規則（文書化）

- 日次: 宣言 TZ の地方真夜中が境界。DST 日は 23/25 時間バケットになる。
- 週次: 宣言 TZ・宣言 `week_start`（`metadata/windows/*.json` と同じ値）の
  地方真夜中が境界。先頭・末尾は要求半開ウィンドウにクランプ。
- 日付のみラベル（GT の記録形状 `YYYY-MM-DD`）は UTC 真夜中のカレンダー日
  として読む。パース不能ラベルは照合から除外し、推測しない。
- 生成不能な exact window（逆転・未知 TZ・不正 week_start）は
  `expected_buckets_undetermined` 理由で記録し、ゼロ補完しない。

### 検証結果

- `python3 -m pytest tests/validation/test_windows.py
  tests/validation/test_coverage.py` → 42 passed。
- `coverage-run`（nodata  fixture）→ `missing` のまま、`expected_*` は空
  （exact window なし）。boundary-12m 実 run（week / Asia/Tokyo / sunday）
  → 53 期待バケット・欠測 1（部分先頭バケット）・`observed_zero` なし・
  status `partial` のまま。2 回実行で同一ハッシュ（決定性）。
- `python3 -m pytest -q` 全体 → 1156 passed に対し 12 failed は
  `test_audit_report_freshness.py` の既存失敗（変更前の clean tree でも
  同一 12 件）。本変更の回帰ではない。
