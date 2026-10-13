# Reports

このディレクトリは**報告書・指示書**を置く。issue（追跡すべき欠陥）ではない。

| ディレクトリ | 何を置くか | 検査 |
|---|---|---|
| `docs/issues/` | 追跡すべき欠陥。`**ID:**` / `**優先度:**` / `**ステータス:**` を持つ issue レコード**のみ** | `validation.cli audit-issues` が機械検査する（OPEN P0 は CI を落とす） |
| `docs/reports/` | 報告書・作業指示・検証記録（issue ではないもの） | 形式の検査なし |
| `docs/audits/` | 再生成可能な機械可読監査レポート | `tests/validation/test_audit_report_freshness.py` |
| `docs/specs/` | 仕様・運用契約 | なし |

2026-10-13 に `docs/issues/` から本ディレクトリへ 3 件を移した。いずれも issue では
なかった（HTML バリデーション報告、データ品質改善の指示書、X 収集 Actor の検証報告）
ため、`docs/issues/` が「issue レコードのみ」を意味するようにした。
