# Issue: 公開契約 PC-7（artifact ごとの審査 envelope）が未実装

**ID:** ISS-20261015-PUB-036  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/validation/publication_contract.py`（`UNIMPLEMENTED`）、`metadata/publication/`、
`validation.cli gate-publication`、`publication/`（15 artifact）

## 概要

公開契約の **PC-7「artifact ごとに公開判断の記録（審査 envelope）が存在する」は未実装**の
ままで、`docs/audits/publication-contract.json` の `unimplemented_rules` に記録されている。
審査 envelope があるのは `metadata/publication/x-cbx-202608-summary-anonymized/` の 1 件だけで、
`publication/` の 15 artifact（研究ページ 13 + guide + search-emergence-tracker）には無い。

## 確認された観測

- `audit-publication`（2026-10-15）: `implemented_rules` = PC-1〜PC-6、
  `unimplemented_rules` = **PC-7 / PC-8**。findings 0 / declared gaps 0。
- 既存 envelope は `artifact.json` / `evidence.json` / `decision.json` の 3 ファイルで、
  ゲートは成果物単位（`gate-publication --artifact …`）。
- `publication-decision-v1` の `status` は `approved` / `denied` / `requires_review` / `unknown`
  （`src/validation/schemas/storage_policy.py` の `PUBLICATION_STATES`）。
- 対象 publication は**まだ公開していない**（メンテナ 2026-10-15）。判断の記録は
  「未審査 / 非公開」から始まるのが実態に合う。

## 影響

- 公開物に「誰がいつ何を根拠に承認したか」の記録が無いまま release / Zenodo へ進む経路が残る。
- ゲートが成果物単位なので、envelope の無い artifact は**判定が存在しない**
  （「未審査」と「拒否」が記録の上で区別できない）。

## 対応方針

**判断（承認/拒否）は人の行為なのでエージェントが埋めない。** 未審査は
`requires_review` として記録する（推測で `approved` を書かない）。

- (a) **artifact ごとに 15 件の envelope**（現行規則どおり。推奨）。既存 1 件と同じ形式で、
  `artifact.json` は sha256、`decision.json` は `requires_review`、`evidence.json` は
  監査レポートの参照。
- (b) **1 release = 1 判断記録**へ PC-7 を再定義する（`metadata/publication/<release_id>/` +
  対象 artifact 一覧）。ファイル数は減るが、既存 1 件の記録も移行対象になり、
  成果物単位の `gate-publication` と単位がずれる。

推奨は (a)。決めたら `publication_contract.py` に PC-7 を実装し、
`docs/specs/contracts.md`（判断記録）と `docs/reports/20261015c-publication-refresh-plan.md` §6.1 を
同時に更新する。

## 完了条件

- [ ] 選択肢 (a) / (b) の決定と記録
- [ ] 対象 artifact の判断記録（少なくとも `requires_review`）と `metadata/publication/README.md` の更新
- [ ] PC-7 の実装（envelope の有無 + `criteria_version` / evidence 参照）と非空虚性テスト
- [ ] `audit-publication` の `unimplemented_rules` から PC-7 を外し、`docs/audits/publication-contract.json` を再生成

## 依存

- PC-8（`ISS-20261015-PUB-037`）と同じ変更にまとめられる。
- 審査 envelope の入力形式は `metadata/publication/README.md` と
  `tests/validation/test_audit_report_freshness.py`（invocation record の扱い）が正本。
