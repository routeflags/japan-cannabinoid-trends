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

- [ ] CS08-CS13 の証拠発生条件の定義
- [ ] 収集・比較の両側の実装と testing（synthetic 完全証拠ペアで定義を固定）
- [ ] 実データでの到達可能性の再評価と、到達不能な場合の理由記録
