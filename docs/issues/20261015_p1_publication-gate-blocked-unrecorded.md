# Issue: publication ゲートの `BLOCKED` が受容記録のないまま公開が続いている

**ID:** ISS-20261015-PUB-015  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `docs/audits/g6-publication-eligibility.json`, `config/storage-policies.json`, `docs/specs/validation-framework.md` §22.5

## 概要

公開適格性の監査は `verdict: BLOCKED`（PUB-01 provenance 欠落 / PUB-04 personal-data review
欠落 / PUB-10）を記録したままで、対象成果物（匿名化済み X CSV）は公開されている。
AGENTS.md は「公開ゲートの失敗は解決または明示的に文書化されるまで公開を止める」と定めるが、
その受容の記録が見当たらない。

## 確認された観測

- `docs/audits/g6-publication-eligibility.json` は record-only 設計の監査出力として存在する。
- `audit-issues` は issue 記録の一貫性を検査するが、この監査結果と公開状態の整合は検査しない。
- 2026-10-13 の先例として、公開アーカイブの取り下げが「不要（受容）」と判断された記録がある
  （`docs/specs/validation-framework.md` §21.6）。

## 影響

- 公開ゲートが実効性を持つのか、単なる記録なのかを第三者が判定できない。
- 公開物の可否判断の履歴が、非公開の会話に依存する。

## 対応方針

- (a) 受容を明示的に記録する、または (b) ゲートを再実行して verdict を更新する。
- どちらかを選んだら、その判断を文書（spec の該当節 or 監査の隣）に残す。
- **推測で PASS にしない。**

## 完了条件

- [ ] 受容 / 再実行のいずれかを選択
- [ ] 選んだ結果の記録（日付付き）
- [ ] 監査と公開状態の関係を説明する文章の追記
