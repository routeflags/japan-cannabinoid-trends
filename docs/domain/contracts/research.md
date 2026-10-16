# 研究 Research — Agent Contract

**版:** 0.1.0（草案、2026-10-16）  
**語彙:** `docs/domain/glossary.md`（研究）。

## Purpose and domain vocabulary

研究質問・対象範囲・入力証拠・処理方法・成果物・制約を Study 集約として束ね、dataset release の根拠にする。

## Owned paths (advisory ownership)

- `src/research/`（audit / comparability / views / catalog / policy）
- `datasets/<study-id>/`（README・methodology・data・metadata・analysis の組）
- `metadata/studies/study-registry.json`（Study の登録簿）

## Invariants and acceptance criteria

- Study 集約ルート（README / methodology / study-registry の組）が揃うこと。
- 凍結 legacy run 以外は現行契約を満たす（`contracts.md` 付録A3）。
- 観測・導出・解釈を区別する（Observed / Derived / Interpretation。解釈を観測として提示しない）。
- 時間相関から因果を推論しない（限定的言語を用いる。AGENTS.md Research Claims）。

## Public interfaces / integration events

- 入力：検証済み来歴（検証コンテキストから）。
- 出力：research view（公開コンテキストへ）、evidence 記録。
- 登録：`study-registry.json` への Study 登録。監査 `audit-studies`（g7）が研究数を数える。

## Allowed dependencies

- 検証の監査・比較可能性判定（`audit-studies`、`comparability` C1 ゲート）。
- 保管からの証拠読み取り（artifact descriptor / evidence registry）。

## Forbidden dependencies

- 生産の産出ロジックへの依存（研究は収集・加工を実装しない。必要なら生産側の変更として要求する）。
- 未検証の分類語彙の使用（taxonomy 準拠。`compound-taxonomy` 等の正本を参照）。
- 公開判断の代行（承認は `gate-publication`＋人間の reviewer。PUB-10）。

## Cross-context change protocol

- 新規 study は registry 登録＋`audit-studies` 再生成が対になる（g7-study-inventory は freshness 対象）。
- 研究横断の比較は comparability gate（C1: query 不一致は不可）を経由する。定義ゲートと C1 の矛盾は許さない。
- 公開物（HTML）の数値訂正は provenance 照合を伴う（CBD-002 / CBD-006 の先例）。

## Required tests and CI checks

- `research.cli audit-studies` の再生成一致（g7 freshness）。
- `tests/research/test_comparability_evidence.py` 等の比較可能性テスト。
- `make audit-new-runs`（新規 run の契約適合）。

## Escalation and human approval triggers

- 公開承認（`approved`＋同一 sha256 の decision。reviewer の人間判断が必須。MNT-001 の envelope 再ピンは owner review）。
- evidence フラグ・判断記録の新規作成（根拠の記録を伴う人間の判断）。
- 第一者データ（analytics / ecommerce）の公開前集計方針（識別子・秘密の非公開。AGENTS.md First-Party Data）。
