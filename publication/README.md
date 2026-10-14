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

規則（PC-1〜PC-6）と未実装項目（PC-7 / PC-8）は
`src/validation/publication_contract.py` と `docs/specs/contracts.md` が正本。
現在の判定と宣言済みギャップは `docs/audits/publication-contract.json`。

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

run_id は数値の出所（どの収集実行から出たか）を示す（公開契約 PC-2）。run_id を持たない
ソースは、**収集日と study_id** で示す（旧契約の収集で run 記録が無いため）。

| データソース | Study ID | run_id / 収集 | 内容 | 区分 |
|-------------|----------|----------------|------|------|
| Google Trends | `cbx-search-trends` | 収集日 2026-08〜09（旧契約。run 記録なし） | CBX / H4CBH / HHBD / CBX リキッド（12ヶ月週次） | **一次データ** |
| X (Twitter) | `cbx-social-trends` | 収集日 2026-08-05 〜 09-08（旧契約。run 記録なし） | 147件 | **一次データ** |
| YouTube | `cbx-social-trends` | 収集日 2026-10-01（旧契約。run 記録なし） | 24件（フィルタ後） | **一次データ** |
| COA | `cbx-product-coa` | 収集日 2026-10-01 | ISO認定2社 | **一次データ** |
| GSC | `cbx-search-trends` | 2026-07 月次 | キーワード別クリック | 参考データ |
| OpenSEO | — | — | キーワードボリューム | 参考データ |

<!-- run_id は付与しない: これらのソースは collector 登録前の収集で、run_metadata.json が無い。
数値の出所は収集日と study_id までしか遡れないことを隠さない（欠測 ≠ 捏造）。 -->

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
- [ ] 公開の判断記録（PC-7）と guide の構造要件（PC-8）は未実装。公開前に
      `docs/audits/publication-contract.json` の `unimplemented_rules` を確認する

**Instagram / TikTok**: Instagram の定点観測は 2026-10-01 に廃止された（カンナビノイド関連 0 件、
化粧品・バイクノイズ支配）。共有仕様は `docs/specs/tiktok-data-sharing-spec.md` として
**TikTok のみ**に改訂済み（2026-10-15）。TikTok の定点観測データはデータ所有側リポジトリにあり、
本リポジトリへは未取り込み（取り込み時は `data/raw/tiktok/<run-id>/` に置く）。
