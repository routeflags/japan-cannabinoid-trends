# Issue: `cron_gate.sh` の書込先 `projects/` がリポジトリに存在しない

**ID:** ISS-20261015-COL-019
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `src/collection/cron_gate.sh`, `docs/specs/validation-framework.md` §22.4

## 概要

`cron_gate.sh` は `projects/` に書く前提だが、そのディレクトリはリポジトリに存在しない。
定期観測（定点収集）の経路が現役かどうかが不明で、実行されていても生成物が把握されていない。

## 確認された観測

- リポジトリ直下に `projects/` は存在しない（`.gitignore` にも記載なし）。
- 実行履歴・生成物の記録が見当たらない。

## 影響

- 定期収集が動いているかどうかを第三者が判定できない。
- 仮に動いていても、出力がどこの管理下にあるか不明で、契約外の raw を生む可能性がある。

## 対応方針

- 現役確認（実行履歴・生成物の探索）。
- 不要なら削除し、必要なら書込先をリポジトリ構造（dataset 配置）に合わせる。
- 契約外の出力を生む経路は、`apify_run.sh` と同じく fail closed にする。

## 完了条件

- [x] 現役/不要の判定と根拠の記録 — **不要（retired）と判定**（下記「対応記録」）
- [x] 不要なら削除、必要なら書込先の変更とガード — 削除ではなく fail-closed の
  retired stub 化＋参照先 fetch の既定拒否とガード（削除より stub を選んだ理由は下記）

## 対応記録（2026-10-15）

判定: **不要（retired）**。根拠は以下の実測。

1. `projects/` は存在しない。`git ls-files | grep -c ^projects/` = 0、`.gitignore`
   に記載なし、`ls projects` も不在。一方で旧 `fetch_*.sh` は `mkdir -p`
   で当該ディレクトリを作るため、動けば stage/adopt 外の raw を生む side channel
   だった。
2. 呼び出し chain は二重に壊れていた。旧 `cron_gate.sh` は
   `$DIR/fetch_tiktok.sh` を呼ぶが当該パスは存在せず（実体は `tiktok/` /
   `instagram/` サブディレクトリ）、旧 `fetch_*.sh` は `$DIR/apify_run.sh` を
   呼ぶが当該パスも存在しない（実体は `../apify_run.sh`）。gate 通過時は収集
   ではなく実行エラーになっていた（override 経路の実測で `No such file`
   を確認）。
3. スケジュールの実体が無い。crontab・CI workflow からの参照は 0 件
   （`cron_gate` / `fetch_tiktok` / `fetch_instagram` の grep 実測。参照は
   docs と script 本体のみ）。
4. Instagram 定点は 2026-10-01 に廃止済み
   （`docs/reports/20261015c-publication-refresh-plan.md` P7、外部 HANDOVER 引用）。
   最後に参照された出力は `teiten_20260910`（2026-09 の分析 report のみ、履歴）。

対応（削除ではなく stub 化: 野良 cron が残っていても reason 付き exit 2 で
loud に失敗し、`projects/` を作らないため）:

- `src/collection/cron_gate.sh`: retired stub 化。何も書かず exit 2。
  stage/adopt（`make stage` / `make adopt-all`）への移行先を表示する。
- `src/collection/{tiktok,instagram}/fetch_*.sh`: 既定は拒否（exit 2、
  mkdir・認証・network より前の検査）。手動 handover 用に `TEITEN_OUTDIR` の
  明示だけを通し、明示指定でもリポジトリの `datasets/` / `projects/` 配下は
  拒否する（`apify_run.sh` と同じ字句正規化規則）。override が実経路になる
  よう `$DIR/../apify_run.sh` の callee 誤りも修正した。
- `tests/collection/test_cron_gate_guard.py`（新規 19 件）: stub の exit 2 と
  無書込、既定拒否のガード順序（`APIFY_TOKEN` 以前）、明示指定の
  datasets/projects 拒否（相対・絶対・dotdot 形）、scratch override が認証
  検査まで進むこと（token 無しのため network 到達なし）を固定。
  `projects/` side channel は作らない（テスト内で不存在を assert）。
- `config/collectors.json` の変更は無い（capability の推測昇格なし）。

検証: 新規 19 件 passed、既存 `test_apify_run_guard.py` と併せて回帰なし。

**ステータス: RESOLVED（2026-10-15）**。
