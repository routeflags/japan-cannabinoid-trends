# Issue: 影響アカウントへの通知の要否が未判断

**ID:** ISS-20261015-XID-023
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `docs/issues/closed/mitigated/20261013_p0_x-identity-published-in-all-releases.md`, `metadata/privacy/x-identity-denylist.json`, `docs/specs/validation-framework.md` §21.6

## 概要

公開アーカイブに X の handle・本文が含まれていた事案について、影響アカウントへの通知の要否が未判断のまま残っていた。

## 判断（2026-10-15）

owner 指示により、通知は **不要** と判断した。

理由:

- 現行方針では X 元投稿データをリポジトリ配下に保存しない（`ISS-20261015-PRV-036`）。
- 平文 handle は保持しておらず、`metadata/privacy/x-identity-denylist.json` はソルト付き SHA-256 のみを保持する。
- 既公開アーカイブの削除・制限は 2026-10-13 に不要と判断済みで、残存リスクとして記録済み。
- 連絡先特定のために handle を復元・再収集すると、保存禁止方針に反して新たな X 元投稿データ処理を発生させる。

したがって、本件は「通知しない」と理由を記録して close する。追加の連絡先探索や X データ保持は行わない。

## 完了条件

- [x] 通知要否の決定と理由の記録
- [x] 判断に応じた作業（不要として close）
