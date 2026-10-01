# Issue: .gitignore と raw-data-policy の矛盾

**ID:** ISS-20261002-012
**優先度:** P2 (Medium)
**ステータス:** OPEN

## 概要

`.gitignore` の `**/data/raw/*` 一括除外ルールが、`raw-data-policy.md` §4.1 の「Google Trends raw は公開すべき」という方針と矛盾。

## 修正オプション

### Option A: .gitignore に例外を追加

```gitignore
**/data/raw/*
!**/data/raw/google_trends/
```

### Option B: ポリシーを更新

- `raw-data-policy.md` を修正し、全 raw データの gitignore を追認

## 推奨

**Option A** — Google Trends raw は再現性に重要であり、バージョン管理すべき

## 関連ファイル

- `.gitignore`
- `docs/specs/raw-data-policy.md` §4.1
