# Issue: コミット済み監査スナップショットが追跡外データに依存し、clean checkout で落ちる

**ID:** ISS-20261015-AUD-028  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15) — 規則を 1 つにし、ローカル事実を排除（§対応記録）  
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
  **CI でも同じ 3 件が落ちる**（2026-10-15 に実測で確定。下記）。
- **CI での実測（2026-10-15、`gh run view`）**:
  - run `38587265312`（commit `fae7fe2`）: **failure 21 秒**。「Run contract tests」で停止し、
    以降のステップはすべて skip。ログの失敗は 3 件で、上記の想定と一致
    （`FileNotFoundError: published source missing for datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv: data/private/x_cbx_202608_summary.csv`（`src/processing/reproduce.py`）、
    `docs/audits/g6-private-catalog.json is stale`、`docs/audits/g7-study-inventory.json is stale`）。
  - run `38628877292`（commit `9475d09`、公開契約の CI ステップ追加後）: **同じ 3 件で failure**。
    追加した「Audit the publication contract (record only)」ステップは **pytest の失敗で skip される**ため、
    この CI ステップはまだ CI 上で一度も実行されていない（unit テストでは検証済み）。
  - したがって「CI は緑」は現状成立しない。**ローカルで green でも CI は落ちる**という状態が続いている。

## 影響

- 「全ゲート green」が作者のマシンでしか成立しない。第三者の検証・引用時に同じ
  結果を再現できない（今回の staging 境界の独立検証でもこの 1 点だけ再現しなかった）。
- **CI（push ごとに実行）が常に赤**である。実測で確定（上記）。pytest で停止して以降の
  ステップが skip されるため、後続の検証（公開契約の監査を含む）が CI では動いていない。
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

- [x] clean checkout（private ディレクトリなし）の `python -m pytest` が green
      （skip は許容）
- [x] `docs/audits/` のスナップショットが追跡ファイルのみから再生成できる
      （ローカル事実を排除、または検査対象外にした）
- [x] 選んだ扱いを `docs/specs/validation-framework.md` に明記（§25）

## 対応記録（2026-10-15）

修正は 3 経路すべて（issue の「対応方針」どおり）:

- **g7 `data_file_count`**: `private` を名前で除外（`src/research/audit.py`）。gitignored な
  `data/private/` の中身（実測で差は 1 ファイル）はチェックアウトごとに異なるため数えない。
  境界の存在は `audit-private-catalog`（存在のみ、内容は数えない）が引き続き記録する。
- **g6-private-catalog**: freshness の normalizer `boundary_only` を追加し、
  `exists` / `present` / `absent` を検査から外した。`tracked` / `ignored` / 分類は
  規則ベースでチェックアウト非依存なので検査対象のまま。
- **`test_stale_declaration_is_reported`**: 既存の `requires_source` マーカーを付与。
  ソースが無い環境ではスキップする（非公開入力の検証は入力がある環境で走る）。
  観測された `FileNotFoundError` の原因も特定した: テストが
  `Derivation(..., source_published=False)` を再構築せず、既定値 `True` の新しい
  `Derivation` を作っていたため、ソース不在時に `reproduce_artifact` が送出していた。
- 規則の文言は `docs/specs/validation-framework.md` §25（1 つの規則 + 3 経路の表）。
- 実測: clean checkout（private 無し）で `pytest` は **3 件失敗 → skip のみ**。
  CI の 3 件失敗（`38587265312` / `38628877292`）も同じ原因だった。
