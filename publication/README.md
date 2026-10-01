# Publication Artifacts

CBX / カンナビノイド関連ガイドページの公開用アーティファクト。

---

## 更新方法

月次更新はスキル `update-cbx-guide` を使用します。

```
「CBX ガイドを更新」
```

詳細: `.github/skills/update-cbx-guide/SKILL.md`

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
| YouTube | `cbx-social-trends` | 26件（2026-10-01 取得、全件 CBX 関連） | **一次データ** |
| COA | `cbx-product-coa` | ISO認定2社 | **一次データ** |
| GSC | `cbx-search-trends` | 2026-07 月次 | 参考データ |
| OpenSEO | — | キーワードボリューム | 参考データ |

### 2026-10-01 更新内容

| 項目 | 変更 |
|------|------|
| 検索データ | GSC → **Google Trends** に差し替え（GSC は参考に降格） |
| YouTube | 0件 → **26件** に更新（全件 CBX 関連） |
| メソドロジー | データソース定義を更新 |
| dateModified | 2026-09-18 → 2026-10-01 |
| バージョン | 1.4 → 1.5 |

### 未完了タスク

- [ ] 元リポジトリ（symphony_workspaces）への反映
- [ ] Google Trends データの定期更新（四半期）
- [ ] Instagram/TikTok データの反映（別リポジトリで定点観測中）
