# Issue: 公開ページが C3 内容レビュー未実施のまま `SUPPORTED` と報告されていた

**ID:** ISS-20261105-PUB-037
**優先度:** P1 (High)
**ステータス:** OPEN
**対象:** `src/validation/publication_eligibility.py`,
`src/validation/publication_content_review.py`,
`src/validation/publication_contract.py`,
`metadata/publication/*/evidence.json`
**リリース:** v1.14.5 で検知を実装し、THCNM の C3 レビューを記録（他の 16 artifact は未実施）
**GitHub:** 未起票（ローカル記録。起票時にこの行へ追記する）

## 概要

v1.14.4 まで、公開適格ゲートの 10 項目（PUB-01〜PUB-10）はすべて機械検査
だった。`research_thcnm.html` は decision が `approved`、PUB-01〜PUB-10 が
PASS で、`SUPPORTED` と報告された。しかし内容（C3）を人が読んで記録した
レビューは存在しない。機械検査は「成果物が整っていて承認されている」ことしか
示さず、「内容がレビュー済み」であることは示さない。

## 実測

| 観測 | 値 |
|---|---|
| v1.14.4 時点の `research-thcnm` の gate | `SUPPORTED`（failed 0 / warnings 0） |
| evidence の `content_review` 記録 | v1.14.5 時点で `research-thcnm` の 1 件のみ（他 16 artifact はなし） |
| C1〜C45 公開チェックリスト | v1.14.5 で `metadata/publication/content-review-checklist.json`（v1.0.0）として定義 |
| リポジトリ内の C 系定義 | `docs/specs/collection-pipeline.md` の比較可能性 C1〜C3 のみ（公開内容レビューとは別物） |

C1〜C45 の正式定義が無いため、45 項目の内容レビューは実施できていない。
「実施した」と記録することはできない。

## 修正（v1.14.5、検知のみ）

1. 機械検査（PUB-01〜PUB-10 / PC-1〜PC-9）と内容レビュー（C3）を別ゲートに
   分けた。`PUB-11`（gate）と `PC-10`（audit）が C3 を検査する。
2. 次のいずれかで `BLOCKED` / finding になる:
   - チェックリスト定義が無い（`CONTENT_REVIEW_CHECKLIST_UNDEFINED`）
   - `evidence.content_review` が無い（`CONTENT_REVIEW_MISSING`）
   - 項目数不足（`CONTENT_REVIEW_INCOMPLETE`）、判定なし・不正
     （`CONTENT_REVIEW_INVALID`）、根拠なし（`basis` 空）、
     `fail` 判定（`CONTENT_REVIEW_ITEM_FAILED`）
   - reviewer / reviewed_at なし（`CONTENT_REVIEW_INVALID`）
   - 対象 HTML hash 不一致（`CONTENT_REVIEW_HASH_MISMATCH`）
3. `approved` 決定があっても C3 未完なら `BLOCKED`。`SUPPORTED` は両ゲートの
   PASS でのみ返る。

## 実施済み（THCNM、2026-11-05）

- `metadata/publication/content-review-checklist.json` v1.0.0 に C1〜C45 を定義した。
- `research-thcnm` の `evidence.content_review` に 45 項目（verdict / basis）、reviewer、`reviewed_at` 2026-11-05、現行 HTML hash `d7a0b7ee…` を記録した。
- レビューで 9 件の記載不備を検出して訂正した（12ヶ月 THC 最大値の 3 週、3ヶ月の非ゼロ分布、5年共通スケールの要求語と正規化、データソース表の 5年 run、`average_interest` の整数丸め、3ヶ月 `granularity` 不備の開示、YouTube 実行状態の語彙、再計算できない重複除去後の件数、公開状態の PUB-11）。
- `gate-publication` は `SUPPORTED`（PUB-01〜PUB-11 PASS、warnings なし）、`audit-publication` は本ページ finding 0。

## 未解決

- 他の 16 artifact は C3 レビュー未実施で `BLOCKED`。各ページは PUB-01〜PUB-10 の結果でゲートを記述したままで、C3 未記録を本文に反映していない（本文変更は artifact hash と承認の再固定を伴うため、所有者の判断を待つ）。

## 受入条件

- [x] 機械検査だけでは `SUPPORTED` を返さない（回帰テストあり）
- [x] 旧 THCNM 状態（PUB-01〜PUB-10 PASS、C3 なし）が `BLOCKED` になる
- [x] 正式チェックリストの定義（`metadata/publication/content-review-checklist.json` v1.0.0）
- [x] THCNM の C1〜C45 レビュー記録（reviewer / reviewed_at / hash 付き）
- [x] v1.14.4 は書き換えない（訂正は本 issue と v1.14.5 で記録）
