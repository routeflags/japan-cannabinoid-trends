# Issue: T6 の sampling / normalization モデルが未完（`comparable` が到達不能）

**ID:** ISS-20261015-CMP-005  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/research/comparability.py`, `src/validation/comparability.py`, `docs/specs/validation-framework.md` §7.1・§16.3

## 概要

L2 / 横断比較のうち sampling（標本の取り方）と normalization（正規化スケール）の条件が
完全にはモデル化されていない。実データでは最強判定が `conditional` に留まり、`comparable`
は証拠不足により到達不能である。

## 確認された観測

- `docs/specs/validation-framework.md` §7.1 に「CS08 sampling 明示・CS09 coverage complete・
  CS11 同一正規化スケール・CS13 公開承認の証拠が両側に揃った場合のみ `comparable`」と記載。
- `test_comparable_is_unreachable_on_repository_data` が実データの全ペアで到達不能を保証。
- comparison set（共取得した term 集合）の一致条件は GT についてのみ実測がある。

## 影響

- 「この 2 つの系列は直接比較できる」という機械判定を研究上主張できない。
- 比較可否が人手の説明に依存し、再現性の担保が弱い。

## 対応方針

- 収集側で CS08-CS13 の証拠を発生させる項目（sampling の記録、coverage、正規化スケール、
  公開承認）を定義し、比較側のモデルと同時に設計する。
- 実データで到達不能な間は、その理由を run / study 側の記録として残す。

## 完了条件

- [x] CS08-CS13 の証拠発生条件の定義（比較側の受領条件 + 収集側の発生箇所。収集側の排出は未実装）
- [x] 収集・比較の両側の実装と testing（synthetic 完全証拠ペアで定義を固定。比較側のみ。収集側は未実装）
- [ ] 実データでの到達可能性の再評価と、到達不能な場合の理由記録（再評価は継続中: 現状到達不能。収集側の証拠排出が揃うまで OPEN のまま）

## 実装メモ（2026-10-15、OPEN のまま）

transformation / evidence スライスに自然に収まる範囲のみ実装し、実データの
比較可能性の主張は変えていない。`comparable` を実データに付与する変更は一切ない。

- 証拠発生条件: `docs/provenance/comparability-evidence-cs08-cs13.md`
  （CS08-CS13 each の証拠担体・生成者・比較側/収集側の状態。CS12 の担体に
  `transformation-v1` 生成記録（本スライス PRV-010）を追加。収集側は CS08 / CS09-CS10 /
  CS11 / CS13 が pending、CS12 が partial）
- 契約テスト: `tests/research/test_comparability_evidence.py`（12 件。完全証拠ペアは
  `comparable`、各 1 項目欠落は `conditional`（CS09 missing のみ `not_comparable`、
  run 欠落は `unknown`）。全て synthetic。実データの主張は
  `test_comparability_gate.py::test_comparable_is_unreachable_on_repository_data`
  が引き続き全ペアで保証）
- 実データの再評価（2026-10-15）: 到達不能のまま。legacy run に sampling / coverage /
  正規化スケール / 承認の証拠が無いため、最強判定は `conditional`。
- 比較側/収集側の分離ピン（2026-10-15）:
  `tests/research/test_comparability_evidence.py::test_built_catalog_entries_carry_no_synthetic_evidence_keys`
  が、catalog builder（収集側）が `sampling` / `coverage` / `missingness` /
  `normalization_scale` の各キーを実エントリに一切排出しないことを固定。
  合成完全証拠ペア（比較側）のみが当該キーを持ち、実エントリが `comparable` に
  到達する経路は収集側の排出変更（本 issue の残作業）のみ。read-only・offline。

残りのオーナー/収集側作業: 新規収集で CS08（sampling 手法）・CS09/CS10（coverage manifest）・
CS11（fetch グループ/比較集合）・CS13（公開承認 decision）を排出する（schema 項目と
adapter 記録の追加が必要。ライブ収集を伴うため本スライス対象外）。排出が揃うまで
実データの `comparable` 主張は行わない。
