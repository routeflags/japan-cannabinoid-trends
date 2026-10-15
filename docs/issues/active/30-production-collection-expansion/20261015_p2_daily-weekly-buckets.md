# Issue: 日次・週次バケット集計が未実装（月次のみ）

**ID:** ISS-20261015-WIN-003  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/validation/windows.py`, `src/validation/coverage.py`, `docs/specs/validation-framework.md` §16.3

## 概要

バケット生成は月次のみ実装されており、日次・週次の集計は分析側に接続されていない。
coverage / missingness の機械評価は現状この粒度に依存できない。

## 確認された観測

- `validation-framework.md` §16.2 は月次バケット生成を実装済みとして記載し、
  §16.3 で日次/週次を未実装として明記している。
- `coverage-run` は run 単位のオンデマンド評価のみ（永続化は ISS-20261015-COV-004）。

## 影響

- 週次・日次の欠測判定を機械化できず、人手集計に依存する。
- 粒度の異なる run 同士の coverage 比較（T6/T7）ができない。

## 対応方針

- 月次実装と同じ契約（半開区間・タイムゾーン・週の開始曜日）で日次・週次を追加する。
- 境界規則は `metadata/windows/*.json` の `week_start` / `timezone` と整合させる。
- 推測でバケット境界を決めない（既存の window 正本を参照する）。

## 完了条件

- [ ] 日次・週次バケット生成の実装とテスト
- [ ] coverage / missingness 判定への接続
- [ ] 境界規則（週開始・タイムゾーン）の文書化
