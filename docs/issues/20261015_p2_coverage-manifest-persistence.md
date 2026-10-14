# Issue: coverage manifest が永続化されない（オンデマンド評価のみ）

**ID:** ISS-20261015-COV-004  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/validation/coverage.py`, `validation.cli coverage-run`, `docs/specs/validation-framework.md` §16.3

## 概要

coverage manifest は `coverage-run` のオンデマンド評価としてしか得られず、run ディレクトリ
に保存されない。評価時点のコードと暗黙の前提に依存した結果が記録として残らない。

## 確認された観測

- `coverage-run` は常に exit 0 のレポート（採用可否のゲートではない）。
- run 側に coverage の派生物は保存されていない（29 legacy run も、今回 staging した GT
  rehearsal run も同様）。

## 影響

- ある時点の「この run は部分的」という判断を後から再現・比較できない。
- 公開時の完全性主張の根拠が、その時実行したコマンド出力に依存する。

## 対応方針

- coverage manifest の保存先と schema ID を決定し、run の派生物として生成する経路を用意する。
- raw へ書き戻さない（`raw` 不変）。既存 run への遡及変換はしない。
- 生成器は既存の評価関数を再利用し、同じ規則を 2 実装しない。

## 完了条件

- [ ] 保存先・形式・schema ID の決定と文書化
- [ ] 生成器 + 検証テスト
- [ ] 遡及変換しない方針の明記
