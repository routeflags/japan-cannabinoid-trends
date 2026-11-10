# Publication Artifacts

CBX / カンナビノイド関連ガイドページの公開用アーティファクト。

---

## 更新方法

ページはスキルで生成する。数値の出所（run_id）は生成時に記録する。

| 対象 | 手段 |
|------|------|
| `research_*.html` | スキル `generate-research-data-page`（`.github/skills/generate-research-data-page/SKILL.md`） |
| `figures/<compound>/` と図の差し込み | スキル `compound-page-figures`（`.agents/skills/compound-page-figures/SKILL.md`） |

## figures/

各 `research_<compound>.html` に埋め込む図の実体を置く。

```text
publication/figures/<compound>/
    trends-5y-standalone.svg / .png      # 検索関心度の5年推移（折れ線）
    youtube-yearly-<slug>.svg / .png    # 動画の年次公開件数（縦棒、run ごと）
    bubble-matrix-<set>.svg / .png      # 年間検索ボリューム（compare_terms の同一要求内）
```

ページは `figures/<compound>/...` を相対参照する。図の生成・差し込みは
`scripts/` の2つのスクリプトで行い、数値の出所は
`datasets/cannabinoid-raw-collection/analysis/<compound>-page-charts/provenance.json`
に記録する（系列 CSV も同ディレクトリ）。

バブルマトリクスは `compare_terms` の共通スケールを使う。**同じ要求の中でだけ**比較でき、
要求間・単独系列とは換算できない（`datasets/cannabinoid-raw-collection/metadata/query-design.json`
の `comparison_scales` が正本）。

```bash
python3 scripts/analysis/compound_page_charts.py      # ページ記載値と raw を照合して図を生成
python3 scripts/publication/embed_compound_figures.py  # 図をページに差し込む
```

図を差し込むとページの SHA-256 が変わる。公開承認（`metadata/publication/research-<compound>/decision.json`）
は hash 単位なので、**図を含む版には再承認と hash の再固定が必要**になる。

更新後は公開契約を検査して結果を記録する（**record-only**。判定は記録し、公開を止めるかは
AGENTS.md の公開規則に従って人が決める）:

```bash
python -m validation.cli audit-publication --output docs/audits/publication-contract.json
```

規則（PC-1〜PC-6）と未実装項目（PC-7 / PC-8）は
`src/validation/publication_contract.py` と `docs/specs/contracts.md` が正本。
現在の判定と宣言済みギャップは `docs/audits/publication-contract.json`。

> 旧手順はスキル `update-cbx-guide` を参照していたが、同スキルは存在しない
> （2026-10-15 に確認・修正）。同じ日に不活性だった
> `scripts/validation/validate-research-pages.py`（到達不能な規則と存在しないパス）
> も削除し、上記の監査へ置換した。

---

## 研究ページ

現行の公開記事は `research_*.html` と、それらが参照する `figures/<compound>/` で構成する。
旧ガイドページ `guide_cbx_rewrite.html` は現行公開物から削除した。過去の収集・分析記録に
残る同ファイルへの参照は、履歴・出所記録として保持する。

**Instagram / TikTok**: Instagram の定点観測は 2026-10-01 に廃止された（カンナビノイド関連 0 件、
化粧品・バイクノイズ支配）。共有仕様は `docs/specs/tiktok-data-sharing-spec.md` として
**TikTok のみ**に改訂済み（2026-10-15）。TikTok の定点観測データはデータ所有側リポジトリにあり、
本リポジトリへは未取り込み（取り込み時は `data/raw/tiktok/<run-id>/` に置く）。
