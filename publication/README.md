# Publication Artifacts

CBX / カンナビノイド関連ガイドページの公開用アーティファクト。

---

## 更新方法

ページはスキルで生成する。数値の出所（run_id）は生成時に記録する。

| 対象 | 手段 |
|------|------|
| `research_*.html` | スキル `generate-research-data-page`（`.github/skills/generate-research-data-page/SKILL.md`） |
| `guide_cbx_rewrite.html` | スキル `generate-compound-guide`（`.github/skills/generate-compound-guide/SKILL.md`） |

更新後は公開契約を検査して結果を記録する（**record-only**。判定は記録し、公開を止めるかは
AGENTS.md の公開規則に従って人が決める）:

```bash
python -m validation.cli audit-publication --output docs/audits/publication-contract.json
```

規則（PC-1 / PC-3 / PC-4 / PC-5 / PC-6）と未実装項目は
`src/validation/publication_contract.py` と `docs/specs/contracts.md` が正本。

> 旧手順はスキル `update-cbx-guide` を参照していたが、同スキルは存在しない
> （2026-10-15 に確認・修正）。同じ日に不活性だった
> `scripts/validation/validate-research-pages.py`（到達不能な規則と存在しないパス）
> も削除し、上記の監査へ置換した。

---

## guide_cbx_rewrite.html

| 項目 | 内容 |
|------|------|
| ファイル | `guide_cbx_rewrite.html` |
| 種別 | HTML ガイドページ（モック/リライト版） |
| 元の場所 | `symphony_workspaces/projects/ec/seo/20260915/mock/` |
| コピー日 | 2026-10-01 |
| 最終更新 | 2026-10-01 |
| バージョン | v1.5 |

### 統合データ

| データソース | Study ID | 内容 | 区分 |
|-------------|----------|------|------|
| Google Trends | `cbx-search-trends` | CBX / H4CBH / HHBD / CBX リキッド（12ヶ月週次） | **一次データ** |
| X (Twitter) | `cbx-social-trends` | 147件（2026-08-05 ~ 09-08） | **一次データ** |
| YouTube | `cbx-social-trends` | 24件（2026-10-01 取得、フィルタ後） | **一次データ** |
| COA | `cbx-product-coa` | ISO認定2社 | **一次データ** |
| GSC | `cbx-search-trends` | 2026-07 月次 | 参考データ |
| OpenSEO | — | キーワードボリューム | 参考データ |

### 2026-10-01 更新内容

| 項目 | 変更 |
|------|------|
| 検索データ | GSC → **Google Trends** に差し替え（GSC は参考に降格） |
| YouTube | 0件 → **24件** に更新（26件から2件除外） |
| メソドロジー | データソース定義を更新 |
| dateModified | 2026-09-18 → 2026-10-01 |
| バージョン | 1.4 → 1.5 |

### 未完了タスク

- [ ] 元リポジトリ（symphony_workspaces）への反映
- [ ] Google Trends データの定期更新（四半期）
- [ ] 公開物の投稿単位 X 表現の除去（投稿単位の表現は格納禁止と同じく禁止。
      `ISS-20261015-XID-034` / `docs/specs/contracts.md`）
- [ ] 契約の未解消分: 版・DOI（13 ページ）、GT 5 年表（7 ページ）、X の信頼区間（guide）。
      `docs/audits/publication-contract.json` を参照

**Instagram / TikTok**: Instagram の定点観測は 2026-10-01 に廃止された（カンナビノイド関連 0 件、
化粧品・バイクノイズ支配）。共有仕様 `docs/specs/instagram-tiktok-data-sharing-spec.md` は
Instagram を含む DRAFT のままなので、改訂または ARCHIVED 化が必要。TikTok の定点観測データは
データ所有側リポジトリにあり、本リポジトリへは未取り込み。
