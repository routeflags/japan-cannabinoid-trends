# Issue: Evidence Registry と run 監査の突合 pass が未実装

**ID:** ISS-20261015-PRV-011  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/provenance/evidence-registry.json`, `src/validation/provenance.py`, `docs/specs/validation-framework.md` §18.3

## 概要

Evidence Registry の語彙と参照形式は用意されているが、run 監査が `unknown` と判定した項目を
証拠引用で `observed` / `inferred` へ昇格させる pass が無い。

## 確認された観測

- `validate-registries` は evidence-registry を検証するが、7 件すべてに
  `EVIDENCE_HASH_UNRECORDED`（info、ハッシュ未記録 = 完全性不明）が付く。
- 検証フレームワークは `inferred` の自動付与をしない方針を明記している。

## 影響

- 「証拠があるのに unknown のまま」の項目を人手で追うことになる。
- 旧 run の capability / 実行条件の昇格判断が場当たりになる。

## 対応方針

- 監査の unknown 項目と evidence エントリを突き合わせ、引用とともに昇格候補を出す pass を用意する（自動で `inferred` を埋めない）。
- evidence のハッシュ記録方針（何をハッシュするか）を決める。

## 完了条件

- [ ] 突合 pass の実装とテスト
- [ ] evidence ハッシュ記録方針の決定
- [ ] 現行 7 件の info の扱いを決着
