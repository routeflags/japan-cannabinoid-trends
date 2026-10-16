# Issue: .venv 無しの checkout で make 実行系が起動失敗する

**ID:** ISS-20261016-MNT-003  
**優先度:** P3 (Low)  
**ステータス:** OPEN  
**対象:** `Makefile`（`PYTHON ?= .venv/bin/python`）, `scripts/validation/run-gates.sh`, `docs/specs/validation-framework.md` §setup, `pyproject.toml`

## 概要

`.venv` を作っていない checkout では `make test` / `make gates` が起動段階で失敗する。
手順どおり `.venv` を作れば動くため環境構築の問題ではあるが、失敗の出方が不親切で、
特に `make gates` は原因の特定しにくい `ModuleNotFoundError` になる。

## 確認された観測

- `make test` → `make: .venv/bin/python: No such file or directory`。
- `make gates` → `run-gates.sh` が `python3` に fallback するが `PYTHONPATH=src` を付けないため
  `ModuleNotFoundError: No module named 'validation'`。
- CI（`.github/workflows/research-validation.yml`）は `pip install -e ".[dev]"` 後の
  素の `python -m pytest` 方式であり、この問題を踏まない。docs（validation-framework.md §setup /
  pyproject.toml）は `.venv` 作成手順を規定済み。
- 2026-10-16 の保守ではローカルに `.venv` を作成（gitignored、リポジトリ変更なし）して対処した。

## 影響

- 新規 checkout で最初に `make test` した人が「パイプラインが壊れている」と誤認する。実害は初回 setup 時のみ。

## 対応方針

- owner 決定待ち。小規模な選択肢: (a) `Makefile` / `run-gates.sh` に `.venv` 不在時の案内メッセージを出す、
  (b) `run-gates.sh` の fallback に `PYTHONPATH=src` を付ける（editable install 無しでも動く）、
  (c) 現状維持（docs 手順どおり作れば動くため対応しない）。
- (b) を選ぶ場合は CI との二重経路にならないよう、validation-framework.md の運用契約に一行で位置づける。

## 完了条件

- [ ] `.venv` 無しの clean checkout で `make test` / `make gates` が「何をすべきか分かる失敗」になるか、素通しできる
- [ ] `make test` が green のままである

## 対応メモ (2026-10-16, T-G)

OPEN のまま残す。実装は完了したが close (resolved への移動 +
`docs/issues/milestones.json` 更新) は見送る。親 worktree に T-F の未コミット変更
(`docs/issues/milestones.json` を含む) があり、本 worker が milestones を同時更新すると
競合するため。親側で本メモを確認後に close 判断することを想定する。

### 実装 (選択肢 (a) を採用, (b) の fallback 方式は不採用)

- `Makefile`: 再利用可能な `check-venv` ヘルパーターゲットを追加し、Python 実行系の
  9 ターゲット (`test`, `collect`, `stage`, `adopt-all`, `platform-trends`,
  `audit-new-runs`, `audit-publication`, `audit-snapshots`, `gates`) の前提条件にした。
  `$(PYTHON)` が実行可能でない場合 (`test -x` かつ `command -v` のいずれも不成立) は
  setup 案内を表示して exit 2 で失敗する。production の実行意味は変えていない。
- `scripts/validation/run-gates.sh`: `python3` への暗黙 fallback を廃止し、
  `${ROOT}/.venv/bin/python` が無い場合は setup 案内を表示して exit 2 で失敗する。
  システム Python 経由の実行は追加しない (`.venv` ワークフローを維持)。
- 案内メッセージ (Makefile / run-gates.sh 共通の `Run:` ブロック):

```text
missing .venv/bin/python
Run:
  python3 -m venv .venv
  .venv/bin/python -m pip install -e ".[dev]"
Then retry ...
```

  (Makefile は `missing $(PYTHON)`、run-gates.sh は `missing ${ROOT}/.venv/bin/python`
  と実パスを表示する。デフォルトではいずれも `.venv/bin/python` を含む。)
- テスト追加なし。本リポジトリに Makefile / shell 振る舞いの既存テスト前例がなく、
  指示どおり brittle なテスト追加を避けて手動検証とした。

### 検証 (いずれも本 worktree で実施, `.venv` は gitignored のためリポジトリ変更なし)

- `make PYTHON=.missing-venv/bin/python test` → 案内表示 + exit 2 (`.venv` 不在時の再現)。
- `make PYTHON=.missing-venv/bin/python gates` → 案内表示 + exit 2。
- `make test` (デフォルト, `.venv` 不在) → `missing .venv/bin/python` + 案内 + exit 2
  (`No such file or directory` にならない)。
- `bash scripts/validation/run-gates.sh registries` (`.venv` 不在) → 案内表示 + exit 2
  (`ModuleNotFoundError` にならない)。直接起動時の確認は `.venv` 作成前に実施し、
  実 `.venv` の移動・削除は行っていない。
- `.venv` 作成 (`python3 -m venv .venv` +
  `.venv/bin/python -m pip install -e ".[dev]"`) 後の `make test` →
  `1446 passed, 4 skipped` (exit 0)。
- `.venv` ありの `make gates` → `summary: 11 target(s), valid` (exit 0)。
- `.venv` ありで `make PYTHON=.missing-venv/bin/python test` → 案内表示 + exit 2
  (override 経路でも案内が出ることの再確認)。
- `PYTHONPATH=src python3 -m validation.cli audit-issues` →
  `72 issue(s) ... failures=0` (本メモ追記後も OPEN P3 のため failure なし)。
