# Issue: X 取り下げ作業で仮決めした 3 点の確認

**ID:** ISS-20261015-XID-035  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `ISS-20261015-PUB-035`（RESOLVED）、`ISS-20261015-XID-034`（RESOLVED）、
`metadata/publication/x-cbx-202608-summary-anonymized/decision.json`、
`config/storage-policies.json`

## 概要

投稿単位 X 匿名化 CSV の取り下げ（`eb78853`）で、判断が必要な 3 点をエージェントが
仮決めして記録した。いずれも覆せるが、覆す場合の作業が決まっているので、
承認するか差し戻すかをここに記録する。

## 確認された観測（仮決めの内容と根拠）

### C1: 既公開アーカイブは取り下げない（U5）

- 仮決め: `WITHDRAWN` の `exposure` に 8 タグ + Zenodo DOI を記録し、アーカイブ自体は
  取り下げない（`docs/specs/validation-framework.md` §21.6 の 2026-10-13 の判断を維持）。
- 根拠: §21.6 は「露出は受容済み・記録する」と判断済みで、覆す指示は無い。
- 差し戻す場合: Zenodo 側の操作（バージョン削除 / 制限）と `exposure` の再記述が必要。
  リポジトリ側の変更（`git rm` / `WITHDRAWN`）は変わらない。

### C2: 方針違反は `status: denied` で表す（新語彙なし）

- 仮決め: `decision.json` を `status: "denied"`（2026-10-15、根拠 `ISS-20261015-COL-030` §4.1）
  に置き換えた。2026-10-13 の `approved` は `notes` に残した。
- 根拠: `PUBLICATION_STATES` に `denied` があり、新しい語彙を作る必要が無い。
  再実行の verdict は `BLOCKED`（PUB-10 FAIL）で、公開拒否が機械的に表れる。
- 差し戻す場合: 1 フィールドの変更 + `gate-publication` の再実行で変わる
  （例: `requires_review` に戻す）。

### C3: policy registry に新しい policy を追加しない

- 仮決め: `config/storage-policies.json` に `processed + social + denied` のような
  エントリを足さず、判断は成果物単位の decision で表す。
- 根拠: その registry の次元は layer × source_kind で、「X の投稿単位」と
  「他の social の処理済み成果物」を区別できない。追加すると YouTube の処理済み成果物まで
  公開不可に分類される。記録は `ISS-20261015-XID-034` の追記にある。
- 差し戻す場合: policy 追加 + YouTube の誤分類を避ける次元の追加（schema 変更）が必要。
  小さな変更ではない。

## 影響

- 3 点はいずれも「記録として残る」形なので、確認が遅れてもリポジトリは壊れない
  （CI は緑、監査は再生成済み）。
- ただし C1 を覆す場合は Zenodo 側の操作が要るため、公開物の次回リリース前に決める。

## 対応方針

- 承認する: 各項目に承認の日付と承認者を追記し、本 issue を RESOLVED にする。
- 差し戻す: 差し戻す項目と代替案を追記し、対応する変更（上記の「差し戻す場合」）を行ってから
  RESOLVED にする。

## 完了条件

- [x] C1 / C2 / C3 のそれぞれについて承認または代替案の記録
      — **2026-10-15、オーナー承認**: C1 は取り下げ実施、C2・C3 は現状のまま承認
      （「そのほかよい」。以下「オーナー回答の記録」）
- [x] C1 の Zenodo 側の実行 — **完了（2026-10-15）**: 対象 12 record（v1.5.2〜v1.12.0）をオーナーが自力削除。Zenodo API で 12/12 の 410 Gone を確認。`WITHDRAWN` 2 件の exposure を「取り下げ済み」に更新（`src/processing/reproduce.py`）。CITATION.cff の DOI 更新は次回クリーン release の新 record 確定後に行う。
- [ ] 実行後の `exposure` / 本 issue の RESOLVED 化（日付付き）

## 承認内容の整理（エージェント記録。上はオーナーの原文）

- C1: 取り下げ実施。実施は Zenodo 側の操作（§12 の手順）。
  リポジトリ側の露出記録（`WITHDRAWN` の `exposure`）は、取り下げ実行後に
  「取り下げ済み」に更新する。
- C2・C3: 現状のまま承認（`denied` のまま、policy 追加なし）。変更不要。

## 依存

- `ISS-20261015-PUB-035`、`ISS-20261015-XID-034`（仮決めの記録本体）。

## オーナー回答

過去のZenodoアーカイブは取り下げる。そのほかよい
