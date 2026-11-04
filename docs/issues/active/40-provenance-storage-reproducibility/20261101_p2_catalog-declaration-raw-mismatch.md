# Issue: committed catalog / declaration が、この checkout に無い raw run を名指す

**ID:** ISS-20261101-PRV-018  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/metadata/data-catalog.json`、
`metadata/provenance/declarations/`、`datasets/*/data/raw/`、`Makefile` の
`audit-raw-completeness`、`validation.cli audit-raw-completeness`

## 概要

catalog（`data-catalog.json`）と `staging-declaration-v1` は、採用済み run の ID と
payload を committed な事実として記録する。一方 `data/raw/` は machine-local であり、
`.gitignore` の `**/data/raw/*`（例外は `google_trends`）で追跡されない。
結果として、**committed な catalog / declaration が、この checkout には存在しない raw を
名指す**状態が普通に起きる。しかしこれを報告する検査が無く、次の 2 つが区別できない。

- その run はまだ採用されていない（backlog）。
- その run は別の checkout で採用済みだが、この checkout では substantiate できない
  （可搬性の問題であり、データの誤りではない）。

さらに、2026-11-01 の HHC 2 run の宣言は**未追跡**のまま、catalog と docs は既に
それらを参照している。宣言だけ・catalog だけ・docs だけをコミットすると、どの組み合わせ
でも provenance が切れる。

## 実測（2026-11-01、この checkout）

| 対象 | 状態 |
|---|---|
| `cannabinoid-raw-collection/metadata/data-catalog.json` | catalog 64 entries / 36 manifests。うち YouTube 8 run を名指す |
| `metadata/provenance/declarations/` | 5 ファイル。`cannabinoid-raw-collection` の YouTube 8 run + `youtube-consistency` の 6 run を宣言 |
| `datasets/cannabinoid-raw-collection/data/raw/youtube/` | **存在しない**（0/8） |
| `youtube-consistency` の catalog | この checkout に無い（宣言のみ） |
| 2026-11-01 HHC 2 run の宣言 | **未追跡**（`git status` で `??`） |

`make audit-raw-completeness` の実測（この checkout）:

- claims 42（catalog 36 + declaration 14、重複統合後）
- present 28
- missing 14（`cannabinoid-raw-collection` YouTube 8 + `youtube-consistency` YouTube 6）
- correction violations 0

## 何が問題か

1. **catalog が raw に対して過剰**。clone / partial worktree では「採用済み」と
   「この checkout に無い」を区別できない。
2. **宣言と catalog のコミット単位が揃っていない**。新しい宣言を単独でコミットすると、
   catalog が参照する run の宣言が無い状態になる。逆も同じ。
3. **検査が無い**。`audit-adoption` は raw にあるディレクトリを列挙するが、
   committed claim が raw に無い場合は報告しない（`audit-new-runs` も
   `run_metadata.json` を起点にするため、raw 不在の run は出てこない）。

## 必須の対策

1. **catalog→raw completeness check** を production validation に追加する。
   catalog entry と declaration run の `(study_id, source_id, run_id)` を集め、
   `datasets/<study>/data/raw/<source>/<run_id>/run_metadata.json` の存在を検査する。
   欠落は study / source / run / state（directory 欠落 / run_metadata 欠落）で報告し、
   非 0 で終了する。raw が machine-local である以上、これは **checkout ローカルの検査**
   であり、CI の必須ゲートにはしない（CI では catalog / declaration の相互整合だけを見る）。
2. **宣言・catalog・docs を同じコミットで更新する**。新しい `staging-declaration-v1` を
   追加するときは、`data-catalog.json` と study README / methodology の run 一覧も
   同じコミットに含める。片方だけのコミットを許さない運用を README に書く。
3. **study alias を解決する**。catalog の `study_id` は収集時の旧 ID
   （`cannabinoid-multi-trends`）のままの run があり、raw directory は現在の
   `cannabinoid-raw-collection` にある。`metadata/studies/study-registry.json` の
   `previous_study_ids` で解決する（実装済み）。
4. **source の directory 表記差を吸収する**。catalog は `google-trends`、
   raw directory は `google_trends`。正規化して比較する（実装済み）。

## 実装（未コミット）

- `src/validation/raw_completeness.py`:
  - `catalog_run_claims` / `declaration_run_claims` / `present_raw_runs`
  - study alias（`previous_study_ids`）と source 表記の正規化
  - `metadata/provenance/corrections/` の `declaration_correction` を検証
    （元宣言 / 訂正版宣言の SHA-256、run id の対応）
- `validation.cli audit-raw-completeness` + `make audit-raw-completeness`
- テスト: catalog のみ / declaration のみ / 両方 / 欠落 / 旧 study ID / source 表記差。

## 完了条件

- [ ] 新しい宣言を追加するコミットに、catalog と README / methodology の更新が含まれている。
- [ ] `make audit-raw-completeness` が、raw の揃った checkout で 0、partial checkout で
      欠落 run を列挙して非 0 になる。
- [ ] CI には catalog / declaration の相互整合（raw 不在でも判定できる範囲）を追加するか、
      追加しない理由を記録する。
- [ ] 2026-11-01 HHC 宣言・訂正版宣言・correction record が追跡され、catalog と同時に
      コミットされている。

## 関連

- `ISS-20261102-PRV-019`: `audit-raw-completeness` が追跡状態とローカル raw の存在を
  分離し、`git_untracked` の不在を `not_repository_retained` として報告する。
