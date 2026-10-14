# Issue: 履歴側の X 識別情報検査が無い（作業ツリーの検査では検出できない）

**ID:** ISS-20261015-XID-021  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `src/validation/x_identity.py`, `scripts/git-hooks/pre-commit`, `docs/specs/validation-framework.md` §21.6

## 概要

2026-10-13 の履歴書き換えで、作業ツリーのゲートでは検出できない対象（改名前のパス、HEAD に
無い旧 logbook）が履歴側に存在することが判明した。現行の検査は作業ツリーと追跡ファイルだけを
見ており、履歴に対する検査は未実装。

## 確認された観測

- `git filter-repo` による全履歴置換を実施（54 handle、投稿 CSV の全パス変種と旧 logbook の
  除去）。
- `audit-x-identity` は作業ツリーを対象とし、`findings 0 / acknowledged 2` を返す。
- 履歴を走査する検査は pre-commit / CI のいずれにも存在しない。

## 影響

- 過去に混入した識別情報の再混入経路（ブランチ・fork・未追跡の持ち込み）を検出できない。
- 検出が人手の調査に依存し、見落としの危険が残る。

## 対応方針

- 全履歴走査の手順を用意し、`src/validation/x_identity.py` の規則を再利用する
  （同じ規則を 2 実装しない）。
- CI に接続する場合は shallow clone と全履歴取得の差を整理してから行う。

## 完了条件

- [ ] 全履歴走査手順の実装と実行記録
- [ ] CI 接続の要否判断と理由
