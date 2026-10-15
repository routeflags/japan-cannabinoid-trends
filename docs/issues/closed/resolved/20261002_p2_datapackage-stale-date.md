# Issue: datapackage.json の modified 日付が古い

**ID:** ISS-20261002-016
**優先度:** P2 (Low)
**ステータス:** RESOLVED (2026-10-15)

## 概要

`metadata/datapackage.json` の `modified` 日付 (2026-10-01) が v1.5.3 リリース (2026-10-02) より古い。

## 修正

バージョン更新時に `modified` 日付も更新する運用を確立。

## 関連ファイル

- `metadata/datapackage.json`

## 解決記録（2026-10-15）

**結論**: issue 記載時の欠陥（`modified: 2026-10-01` < v1.5.3 リリース `2026-10-02`）は既に解消済み。`metadata/datapackage.json` の変更は不要のため行わない。

**現在の証拠**（いずれも 2026-10-15 時点）:

- `metadata/datapackage.json`: `version: 1.13.2`、`modified: 2026-10-15`。
- `CITATION.cff`: `version: 1.13.2`、`date-released: 2026-10-15`。
- `CHANGELOG.md` 最新エントリ: `[1.13.2] - 2026-10-15`。
- よって `modified (2026-10-15) >= 最新 CHANGELOG 日付 (2026-10-15)`。

**自動化された運用規則**（one-off の日付編集ではなく恒久対策として既に存在）:

- `tests/validation/test_version_internal_consistency.py::test_datapackage_is_not_older_than_the_newest_changelog_entry` が「datapackage の `modified` は最新 CHANGELOG エントリの日付以上」を CI で強制（docstring に本 issue 番号を明記）。2026-10-15 に PASS を確認。
- `.github/skills/release-zenodo/SKILL.md` Step 1 がバージョン更新時の `modified` 更新を手順化。
- `scripts/validation/validate-version-sync.sh` §3 が `modified` を表示（INFO）し、version / DOI 不一致は FAIL。

残存 owner 動作なし。次回バージョン更新時に `modified` を忘れた場合は上記テストが失敗する。
