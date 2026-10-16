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
