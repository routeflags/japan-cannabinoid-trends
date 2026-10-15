# Issue: Release Manifest / Zenodo 候補検証（G6-T12/T13/T19/T20）が未実装

**ID:** ISS-20261015-REL-014  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `scripts/release/create-clean-archive.sh`, `.github/workflows/release-zenodo.yml`, `docs/specs/validation-framework.md` §19.3

## 概要

G6 のうち Release Manifest（`release-manifest-v1` 等）の schema・CLI・CI 配線が未実装で、
GitHub Release / Zenodo へ何を含めるかの機械検証が無い。公開は現行の人手運用のまま。

## 確認された観測

- `docs/specs/release-process.md` と `scripts/release/create-clean-archive.sh` は
  手順と生成のみで、内容の検証ゲートは無い。
- `docs/specs/validation-framework.md` §19.3 に T12/T13/T19/T20 が未実装と記載。
- 過去に公開アーカイブの内容問題が発生しており（X 識別情報を含むアーカイブが
  `10.5281/zenodo.23253840` / `10.5281/zenodo.23095153` に配布済み）、公開前検査の
  必要性は実例で確認されている。

## 影響

- リリースに何が入ったかを後から機械的に検証できない（内容の同一性を人手で確かめる）。
- storage policy と実際のアーカイブ内容のズレをリリース時に検出できない。

## 対応方針

- 実装可否を先に決める（scope が大きい場合は対象を絞る）。
- 実装する場合は、既存の storage policy / git tracking 監査を再利用し、同じ規則を 2 実装しない。

## 完了条件

- [x] 実装可否の判断記録
- [x] （可なら）Release Manifest の schema / CLI / CI 配線とテスト

## 対応記録（2026-10-15）

- Implementer が一度着手したが failed。Release Manifest / Zenodo 候補検証は未実装のため、ステータスは `OPEN` のまま維持する。

## 解決記録（2026-10-15）

**Scope 判断**: 実装可。ただし計画書（`docs/plans/dev/20261015-release-manifest-validation-plan.md`）どおり **検証のみの vertical slice** とする。公開・push・Zenodo 送信・`release-archives/` 変更・raw 変更は一切行わない。

**実装内容**（AC1–AC7 全て満たす）:

- schema: `release-manifest-v1`（`src/validation/schemas/release.py`、registry 登録＋契約テスト `tests/validation/test_release_manifest.py`）。
- 検証: `src/validation/release_manifest.py`（`check_release_manifest`）。required 不足・禁止パス・include-root 外を検査し、version / DOI 一致と canonical 禁止パスは既存 `validation.release_archive_check.check_archive`（REL-015）に委譲。規則の二重実装なし（manifest が canonical 禁止リストを狭めると構造エラー）。
- CLI: `validate-release-manifest --file <manifest> [--archive <zip>] --format text|json [--output <path>]`（終了コード 0/1/2/3 は既存規約どおり）。
- 生成器: `scripts/release/make-release-manifest.py`（canonical scope を version / concept DOI / archive に束縛するだけ。送信機能なし）。
- CI 配線: `.github/workflows/release-zenodo.yml` に `Validate release manifest` ステップを追加（archive 作成後・Zenodo 公開前。不一致は upload 前に失敗）。既存 `Verify archive release identity` は残す（包含関係はテストで固定）。YAML 構文は検証済み。
- 台帳: `contract-ledger.json` を再生成（30 契約。`release-manifest-v1` の scope `(validation, G6)` と gate `gate-release-manifest` を追加）。
- 仕様: `docs/specs/validation-framework.md` §19.3 の未実装項目を解消し §19.4 に記録。`docs/specs/release-process.md` の checklist に反映。

**証拠**（全て offline・合成 fixture。実 Zenodo・実アーカイブ不使用）:

- `pytest tests/validation/test_release_manifest.py tests/validation/test_schema_coverage.py tests/validation/test_contract_ledger.py tests/validation/test_version_internal_consistency.py tests/validation/test_release_archive_check.py tests/validation/test_cli.py` — 全 PASS。
- `python -m validation.cli validate-registries --format json` — 全 valid。
- `python -m validation.cli audit-issues --format json` — failures=0（本 issue の移動後）。

**残存する owner / release 側の動作**（実装ではなく運用）:

- 次回リリース時に workflow の `Validate release manifest` ステップが green であることを目視確認する（release イベント無しには実地実行できない）。
- `INCLUDE_PATHS`（workflow / `create-clean-archive.sh` の copy リスト）と `DEFAULT_INCLUDE_ROOTS`（検証側 default）は別宣言のまま。不一致は fail-closed（検証が落とす）方向だが、将来 scope 変更時は両方を同時更新すること。
