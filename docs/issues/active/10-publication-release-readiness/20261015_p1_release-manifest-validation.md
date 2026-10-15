# Issue: Release Manifest / Zenodo 候補検証（G6-T12/T13/T19/T20）が未実装

**ID:** ISS-20261015-REL-014  
**優先度:** P1 (High)  
**ステータス:** OPEN  
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

- [ ] 実装可否の判断記録
- [ ] （可なら）Release Manifest の schema / CLI / CI 配線とテスト

## 対応記録（2026-10-15）

- Implementer が一度着手したが failed。Release Manifest / Zenodo 候補検証は未実装のため、ステータスは `OPEN` のまま維持する。
