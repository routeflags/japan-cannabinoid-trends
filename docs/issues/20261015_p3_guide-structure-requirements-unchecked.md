# Issue: 公開契約 PC-8（guide 固有の構造要件）が未実装

**ID:** ISS-20261015-PUB-037  
**優先度:** P3 (Low)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `publication/guide_cbx_rewrite.html`、`src/validation/publication_contract.py`、
`.github/skills/generate-compound-guide/SKILL.md`

## 概要

`guide_cbx_rewrite.html` は研究ページとは別の生成器（`generate-compound-guide`）で作られており、
研究ページの構造要件（PC-5）は適用されない。そのため **guide 固有の構造要件は
機械検査されていない**（PC-8 として `unimplemented_rules` に記録）。

## 確認された観測（2026-10-15）

- 実測: `guide_cbx_rewrite.html` に `95%` は 0 件。guide の X セクションは
  週別推移 / 投稿者 / エンゲージメントの表で、**分類比率の表を持たない**ため
  信頼区間を要求する対象が無い（研究ページの `data-x` とは形状が違う）。
- guide のデータソース表は run_id を持たない旧契約の収集で、study_id と収集日で示している
  （`publication/README.md`。PC-2 の「run を名乗る」要求は研究ページ限定）。
- 2026-10-15 に PC-5 を研究ページ限定へ整理した（`docs/reports/20261015c-publication-refresh-plan.md` §9）。
  PC-1 / PC-3 / PC-4 / PC-6 は HTML 全体に適用されるので guide にも掛かる。

## 影響

- guide は 13 研究ページと並ぶ公開物だが、契約上は「研究ページの要件の外」にある。
- guide の生成器契約が変わっても、公開物に反映されたかを機械的に確認できない。

## 対応方針

- `generate-compound-guide` の SKILL.md から**機械検証できる要求だけ**を抽出し、PC-8 として実装する。
  散文の要求（表現のトーン等）は対象外と明記し、検査できないことを検査したふりをしない。
- 抽出の際は、guide に実際に存在する形状（表の種類）を要求にする。
  「無い表を要求する規則」を書かない（PC-5 を guide に適用して戻した理由と同じ）。

## 完了条件

- [x] guide の生成器契約から検査可能な要求を抽出し、対象 / 対象外を明記
- [x] PC-8 の実装と非空虚性テスト（違反フィクスチャで落ち、現行 guide で findings 0）
- [x] `unimplemented_rules` から PC-8 を外し、監査と `docs/specs/contracts.md` を再生成

## 依存

- PC-7（`ISS-20261015-PUB-036`）と同じ変更にまとめられる。

## オーナー回答

research_cbx.html の欠損を先に対応

## 対応記録（2026-10-15）

`publication/research_cbx.html` を作成し、オーナーの前提条件を満たした（本 issue は PC-8 が残るため OPEN のまま）。
内容は既存 13 ページと同一形式で、数値はすべて記録から導出: GT 5 年は `processing.cli gt-summary` の生成ブロック
（出所は唯一の CBX 単独系列である境界計測 run `20261015T042857Z-google-trends-boundary-5y`）、
12 ヶ月は境界計測 12 ヶ月 run（平均 69.77 / ピーク 2026-09-13 / 最新 78）、X は 147 件の記録済み分布
（トピック・意図・形式＋Wilson 95% CI）、規制は MHLW（合法・ブラックリスト方式・THC 残留限度値）、
YouTube は v3 レポート 2 本（CBX 600 件中 232 関連 / CBX リキッド 125 件）と Apify 24 件の深度統計。
共通スケール比較と CBX 製品 COA は記録が無い旨を明記した（欠測 ≠ ゼロ）。
`audit-publication` は 16 artifact / findings 0。

## 対応記録（PC-8、2026-10-15）

`generate-compound-guide` から機械検査できる要求だけを抽出して PC-8 とした。対象は
JSON-LD 3 種（BreadcrumbList / Article / FAQPage）、H1 1 件、主要 H2、主要 CSS class、
利益相反・ライセンス・医療助言でない旨・Google Trends の相対指数制約・COA の独立分析制約、
FAQ 4 問以上。文体、科学的妥当性、薬機法リスク表現の精査など人間判断が必要な項目は
PC-7 の review envelope に残す対象であり、PC-8 では「検査したふり」をしない。
