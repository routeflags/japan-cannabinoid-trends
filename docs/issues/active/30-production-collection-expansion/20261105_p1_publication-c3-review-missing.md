# Issue: 公開ページが C3 内容レビュー未実施のまま `SUPPORTED` と報告されていた

**ID:** ISS-20261105-PUB-037
**優先度:** P1 (High)
**ステータス:** OPEN
**対象:** `src/validation/publication_eligibility.py`,
`src/validation/publication_content_review.py`,
`src/validation/publication_contract.py`,
`metadata/publication/*/evidence.json`
**リリース:** v1.14.5 で検知を実装（レビュー自体は未実施）
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
| evidence の `content_review` 記録 | なし（全 17 artifact でなし） |
| リポジトリ内の C1〜C45 公開チェックリスト | **存在しない** |
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

## 未解決

- C1〜C45 の正式チェックリストと C3 契約の定義場所が未確定。定義が
  `metadata/publication/content-review/checklist.json` に置かれるまで、
  gate は fail closed（全ページ `BLOCKED`）である。
- したがって THCNM の C3 レビューは未実施。実施後に
  `evidence.content_review` を記録し、hash を再固定する。

## 受入条件

- [x] 機械検査だけでは `SUPPORTED` を返さない（回帰テストあり）
- [x] 旧 THCNM 状態（PUB-01〜PUB-10 PASS、C3 なし）が `BLOCKED` になる
- [ ] 正式チェックリストの定義
- [ ] THCNM の C1〜C45 レビュー記録（reviewer / reviewed_at / hash 付き）
- [x] v1.14.4 は書き換えない（訂正は本 issue と v1.14.5 で記録）
