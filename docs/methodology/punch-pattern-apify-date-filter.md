# パンチパターン: Apify Twitter Search の日付指定方法

**発見日:** 2026-09-17
**発見者:** Rei (AI Agent)
**検証者:** ユーザー
**重要度:** 高

---

## 1. 何が起きたか

Apify Actor `cPYLH3QT9GyzKhB4S`（Twitter Search）を使って CBX リキッドの X データを取得していた。

- 8月分（147件）は既に取得済み
- 9月分を取得しようとしたが、`chargedEventCounts` が 0 を返した
- 「X がカンナビノイド関連をブロックしている」と結論した（**誤り**）
- 実際はデータセットの中身にデータが存在した（20件）
- `chargedEventCounts` の reporting が不正確だった

## 2. 教訓

### chargedEventCounts を信用してはいけない

| フィールド | 意味 | 信頼性 |
|-----------|------|--------|
| `chargedEventCounts` | 課金カウンタ | **不正確な場合がある** |
| `defaultDatasetId` | データセットID | ✅ 正常 |
| `get-dataset-items` | 実際のデータ | ✅ 信頼できる |

**正しい手順:**
1. API 実行
2. `defaultDatasetId` を取得
3. `get-dataset-items` で中身を確認
4. 件数を確認
5. `chargedEventCounts` は参考程度にしか使わない

## 3. 日付指定の方法

### Actor の入力スキーマ

```json
{
  "query": "string (必須)",
  "section": "top | latest | people | photos | videos",
  "maxPages": "integer (1-100)"
}
```

**専用の日付パラメータはない。**

### X の検索構文で日付指定

`query` フィールド内に X の検索演算子として `since:` / `until:` を書く:

```
"CBX リキッド since:2026-08-01 until:2026-08-08"
```

### 検証結果

| クエリ | 結果 |
|--------|------|
| `CBX リキッド since:2026-08-01 until:2026-08-08` | 8月7日の投稿5件 ✅ |
| `CBX リキッド`（日付指定なし） | 9月12日〜17日の20件 ✅ |

## 4. 私が犯した間違い

| # | 間違い | なぜ起きたか |
|---|--------|-------------|
| 1 | `chargedEventCounts` をデータ件数として扱った | 課金フィールドとデータ件数が別物だと知らなかった |
| 2 | データセットの中身を確認しなかった | 「0件」という表示をそのまま信じた |
| 3 | 「X がブロックしている」と結論した | 確認せずに推測を事実として扱った |
| 4 | 「過去データは取れない」と結論した | 日付指定の方法を知らなかった |

## 5. 恒久的対応

### チェックリスト（今後のデータ取得時）

```
□ API 実行
□ defaultDatasetId を取得
□ get-dataset-items で中身を確認 ← これを必ずやる
□ 件数を確認
□ chargedEventCounts は参考程度に
□ 日付指定が必要なら since/until を query に含める
```

### ドキュメント化

- Apify X データ取得スキルに日付指定機能を組み込む
- データ整合性ドキュメントに「chargedEventCounts の制約」を記載

## 6. 費用

| 項目 | コスト |
|------|--------|
| 日付指定テスト（1回） | $0.002 + 5件×$0.0025 = $0.0145 |
| 5〜7月取得（3ヶ月分） | 約 $0.05〜$0.15 |

## 7. 記録場所

- このレポート: `projects/ec/research/20260917/punch-pattern-apify-date-filter.md`
- データ整合性: `projects/ec/seo/20260915/cbx_x_data_integrity.md`
- スキル: `.github/skills/apify-x-search/SKILL.md`
