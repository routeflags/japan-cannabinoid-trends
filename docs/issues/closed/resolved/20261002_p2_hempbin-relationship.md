# Issue: Hempbin と Routeflags の関係が不明

**ID:** ISS-20261002-011
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)

## 概要

COA セクションに「依頼者: Hempbin」と記載されているが、Hempbin と Routeflags の関係が説明されておらず、サプライチェーンの来歴が曖昧。

## 修正手順

1. Hempbin と Routeflags の関係を明記（例: 提携実験室、子会社、独立第三者）
2. 関係性の開示を COA セクションに追加
3. 独立性が確保されていることを明記

## 関連ファイル

- `publication/guide_cbx_rewrite.html` L732

## オーナー回答

COA セクションの依頼者部分は不要なので削除。これを共通ルール化

## 対応記録（2026-10-15）

- `publication/guide_cbx_rewrite.html` の COA セクション meta 行から `/ 依頼者: Hempbin` を削除（他に `依頼者` の出現は publication 配下に無いことを確認）。
- 共通ルール化: `.github/skills/generate-compound-guide/SKILL.md` の COA Section「書いてはいけないこと」に「COA の依頼者（client）の記載」を追加。依頼者情報は provenance 記録（study README 等）に残し、公開物の COA セクションには載せない。
- 機械検査: 公開契約 PC-8 に `guide_coa_requester_mention` を追加（guide の `data-coa` セクション内の `依頼者` を検出）。非空虚性テスト付き（`tests/validation/test_publication_contract.py`）。
- 副作用の処理: guide 編集で sha256 が変わったため、PC-7 が hash mismatch を検出（設計どおり）。envelope の `artifact.json` / `decision.json` の hash を現行ファイルに更新し、decision は `requires_review` のままにした（承認の発明なし）。`audit-publication` は 16 artifact / findings 0 に復帰。