# Issue: コミット済み監査スナップショットが追跡外データに依存し、clean checkout で落ちる

**ID:** ISS-20261015-AUD-028  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `docs/audits/g7-study-inventory.json`（生成: `research.cli … audit-studies`）、
`docs/audits/g6-private-catalog.json`（生成: `validation.cli audit-private-catalog`）、
`tests/validation/test_audit_report_freshness.py`、
`tests/processing/test_processed_artifacts.py`

## 概要

`docs/audits/` のスナップショットは「コミットされたファイル＝追跡ファイルから再生成できる」
ことを `test_audit_report_freshness` が検査しているが、実際には**そのマシンにしか
無いディスク状態**に依存するフィールドを含んでいる。結果、`datasets/*/data/private/`
（`.gitignore:51`）にローカルデータを持つマシンでしか `pytest` が green にならない。

## 確認された観測

- `docs/audits/g7-study-inventory.json` は `cbx-social-trends` の `data_file_count` を
  **7** と記録する。この数は `datasets/cbx-social-trends/data/` 配下の実ファイル数を
  数えており、追跡下のデータファイルは **6**（差の 1 件は gitignore された
  `data/private/` 配下）。clean checkout での再生成は 6 になり、コミット済みの 7 と
  一致しない。
- `docs/audits/g6-private-catalog.json` は `datasets/cbx-social-trends/data/private` を
  `exists: true`（`present: 1`）と記録する。`.gitignore` 対象のディレクトリの実在は
  ワークスペース依存の事実で、clean checkout では `present: 0` になる
  （同ファイルは「存在と除外状態のみ。内容は出力しない」という方針を持つが、
  **存在自体がローカル事実**である点は扱われていない）。
- `tests/processing/test_processed_artifacts.py::test_stale_declaration_is_reported` は
  private 入力（同ファイルの `SOURCE` 定数が指すファイル）からの再導出を前提に
  しており、同ファイル冒頭の `requires_source` マーカー（private 入力が無ければ
  skip）が付いていない。
- clean checkout（`git archive HEAD` の展開 + `python -m pip install -e ".[dev]"`）
  での `python -m pytest` = **914 passed / 3 failed / 6 skipped**。失敗は
  `test_audit_report_freshness[g6-private-catalog]`、`[g7-study-inventory]`、
  `test_processed_artifacts.py::test_stale_declaration_is_reported`。
  ローカルに当該ファイルがある環境では 931 passed（両方実測）。
- 親 commit でも 4 件失敗しており、**今回の staging 修正の回帰ではない**
  （2026-10-13 のスナップショット以降の状態）。
- 対処の前例が同テスト内にある: `tracked_only` normalizer は「`ignored` / `absent` は
  checkout 依存のローカル事実で 2 台のマシンでは一致しない」ことを理由に
  `state_summary` / `count` / `extra_count` を検査対象から外している
  （`test_tracked_only_normalizer_drops_local_state` が規則を固定している）。
  g6-private-catalog と g7 は同じ問題を抱えたまま snapshot として登録された。
- `.github/workflows/research-validation.yml` は push / pull_request で
  `python -m pytest` を実行する。clean checkout でこの 3 件が落ちることから、
  **CI でも同じ 3 件が落ちると推定される**（これは導出。CI 実行そのものは未確認）。

## 影響

- 「全ゲート green」が作者のマシンでしか成立しない。第三者の検証・引用時に同じ
  結果を再現できない（今回の staging 境界の独立検証でもこの 1 点だけ再現しなかった）。
- 監査スナップショットの鮮度ゲートが、リポジトリに存在しないデータの存在を要求する。
- 追跡外の private データの**存在**が、公開されている追跡済みファイルの数値
  （`data_file_count`）に現れる。

## 対応方針

規則を 1 つにする: **コミットされる監査スナップショットは追跡ファイルだけで再生成
できなければならない。**ローカルのディスク状態に依存する事実は、次のどちらかに寄せる。

- (a) 追跡対象の事実に置き換える（g7 の `data_file_count` を tracked に限定し、
  追跡外の件数を別フィールドとして記録する。`data_file_count` を減らすだけでは
  「なぜ減ったか」が残らないため、記録は有意義に保つ）。
- (b) 事実としては残すが鮮度検査の対象から外す（`tracked_only` と同型の normalizer
  を g6-private-catalog に適用し、`exists` を比較から除く）。

その他:

- `test_stale_declaration_is_reported` に既存の `requires_source` を付ける
  （private 入力がある環境では実行、無い環境では skip。skip は既に 6 件許容）。
- 修正はスナップショットの再生成で行い、raw には触れない。日付付きの記録
  （`docs/audits/*.md`）は当時の記録として変更しない。
- 選んだ扱いを `docs/specs/validation-framework.md` の audit freshness 節に明記し、
  同型のレポートが同じ判断を繰り返せるようにする。

## 完了条件

- [ ] clean checkout（private ディレクトリなし）の `python -m pytest` が green
      （skip は許容）
- [ ] `docs/audits/` のスナップショットが追跡ファイルのみから再生成できる
      （ローカル事実を排除、または検査対象外にした）
- [ ] 選んだ扱いを `docs/specs/validation-framework.md` に明記
