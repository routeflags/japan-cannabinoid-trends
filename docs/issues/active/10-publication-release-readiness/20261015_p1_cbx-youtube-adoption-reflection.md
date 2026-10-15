# Issue: CBX ページ YouTube 節への COL-033 採用反映 (follow-up)

**ID:** ISS-20261015-PUB-CBX-YT-033
**優先度:** P1 (High)
**ステータス:** OPEN (実装済み・審査待ち)
**対象:** `publication/research_cbx.html` (`data-youtube`, `data-youtube-analysis`), `metadata/publication/research-cbx/`, `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`, `docs/issues/closed/resolved/20261015_p1_unadopted-youtube-exports.md`
**計画:** `docs/plans/dev/20261015-cbx-youtube-adoption-reflection.md`

## 背景

- COL-033 は RESOLVED (2026-10-15): 6 runs 採用、raw は `datasets/youtube-consistency/data/raw/youtube/<run-id>/` の無追跡 private 保管。宣言 sha256 `423e8c15f18ce4ae685ab5b405edb0262375576f1785cad9df3f64b65c11e3c1`。
- `publication/research_cbx.html` の YouTube 2 節は 2026-10-04 v3 値のまま。v3 は 2026-10-12 方針で使用取り止め・raw 削除済み (ページに記録あり)。
- 採用 6 runs に CBX キーワードは無い (HHBD/H4CBH/CBD/CBN/CRDH)。CBX ページでは他化合物の run を CBX 数値に流用せず、欠測として明示する必要がある。

## 実装 (2026-10-15, 本 worktree)

- `data-youtube`: v3 derived を残し、採用 6 runs 表 (run_id/キーワード/件数/dateFilter/観測範囲) と合計 2288 (224+395+456+468+352+393) を追加。宣言・issue への参照、dateFilter-vs-観測範囲の区別、search-sample としての制約を記載。CBX 採用なしを明示。
- `data-youtube-analysis`: v3 125 + Apify 24件フィルタの由来を維持し、24件が COL-033 と別物であること、CBD リキッド 2 runs (456 all / 393 year) を CBX 証拠に流用しないことを追記。per-post 行の追加なし。
- 照合: ページ内訳は宣言の `returned_count` と一致。raw は触らない。tracked/public 層への per-post・非公開データの漏洩なし (集計のみ、actor run ID/dataset ID/費用等の公開なし)。
- envelope: `metadata/publication/research-cbx/{artifact,evidence,decision}.json` を現行 hash `5ba5c823e8aace4f03bee3cd8087c2792cfbd9ad0a5db3f76f1d3479032e494c` (22315 bytes) に更新。decision は `requires_review` のまま (承認の発明なし)。
- gate: `validation.cli gate-publication --artifact/--decision/--evidence (research-cbx)` を実行。verdict=BLOCKED (PUB-04/PUB-10 FAIL、未公開の想定どおり。PUB-05 PASS)。承認は対象外。`docs/audits/g6-publication-eligibility.json` (別 artifact の invocation record) は上書きしない。

## 検証

- `tests/validation/test_publication_contract.py`: 24 passed。
- `audit-publication` (当 worktree): PC-7 解消。残り PC-2 6 件 (`run_reference_unresolved`) は当 worktree に untracked raw が無いための環境差。所有者環境 (catalog 47、採用 6 件あり) では解決し findings 0 になる想定。推測で raw を捏造しない。
- `pytest` 全体: 当 worktree では pre-existing の鮮度差 + 別作業の dirty (milestones.json の JSON break 等) により 12 failed / 1115 passed。 publication-contract 以外の失敗は本作業の回帰ではない。詳細はコミットメッセージに記録。
- 監査スナップショット (`docs/audits/publication-contract.json` 等) は本作業では再生成しない (所有者環境の catalog 47 を上書きしないため)。

## 残作業

- [ ] 所有者環境 (採用 raw あり) で `audit-publication` が findings 0 / catalog 47 であることの確認。
- [ ] 人間による内容審査 (効能・法務・再配布) と公開承認 (対象外のため未実施)。
- [ ] GT 境界作業 (2026-10-22+、別件) との整合確認。
