# CBX Search Trends — Methodology

**Study ID:** cbx-search-trends
**Created:** 2026-10-01
**Last Updated:** 2026-10-01

---

## 1. Research Question

> 日本国内において、CBX / H4CBH / HHBD 関連クエリの検索需要はどう推移しているか？

- **主要データ:** Google Trends（市場全体の相対検索興味度）
- **参考データ:** Google Search Console（当社サイトの検索パフォーマンス）

---

## 2. Data Sources

### 2.1 Google Trends (Primary)

| 項目 | 値 |
|------|-----|
| ソース | Google Trends (trends.google.com) |
| 取得方法 | google-trends-mcp (npm, v0.1.1) |
| エンドポイント | 非公式（trends.google.com 内部 API） |
| 地域 | JP（日本） |
| 期間 | today 12-m（過去12ヶ月、週次） |
| 取得日 | 2026-10-01 |
| キーワード | CBX, H4CBH, HHBD, CBX リキッド |

### 2.2 Google Search Console (Reference)

| 項目 | 値 |
|------|-----|
| ソース | Google Search Console |
| 対象サイト | www.thch-vape.shop |
| 期間 | 2026-07（月次） |
| 取得日 | 2026-09 |
| 抽出条件 | keyword CONTAINS 'cbx' |

---

## 3. Collection Parameters

### 3.1 Google Trends

```json
{
  "terms": ["CBX", "H4CBH", "HHBD", "CBX リキッド"],
  "geo": "JP",
  "timeframe": "today 12-m"
}
```

**ツール呼び出し:**
- `interest_over_time`: 各キーワード単独の週次推移
- `compare_terms`: 4キーワードの比較（正規化相対指数）
- `related_queries`: 関連クエリ（取得不可の場合あり）

### 3.2 GSC

- サイト全体のクエリデータから CBX 関連を抽出
- キーワードフィルタ: `cbx` を含むクエリ

---

## 4. Run History

| Run ID | 取得日 | データ | 結果 |
|--------|--------|--------|------|
| `20261001T115959Z-google-trends-cbx-rikiddo` | 2026-10-01 | CBX リキッド単独 + 3キーワード比較 | 成功 |
| `20261001T121949Z-google-trends-h4cbh-hhbd` | 2026-10-01 | H4CBH, HHBD 単独 + 4キーワード比較 | 成功 |
| GSC 202607 | 2026-09 | 200クエリ（うち CBX 関連 6件） | 成功 |

---

## 5. Data Processing

### 5.1 Raw Data

- Google Trends: JSON 形式で `data/raw/google_trends/<run-id>/` に保存
- GSC: CSV 形式で `data/raw/gsc/` に保存

### 5.2 Derived Data

- 単独平均: 各キーワードの interest_over_time 平均値
- 比較平均: compare_terms での正規化相対指数の平均値
- ピーク: 最大値とその週

---

## 6. Limitations

### 6.1 Google Trends

| 制約 | 影響 |
|------|------|
| **相対指数 (0-100)** | 絶対検索数ではない。期間・地域により基準が変動 |
| **低ボリュームクエリ** | ニッチキーワードは 0（閾値未満）になる可能性 |
| **多義語** | 「CBX」はホンダ CBX400F 等でも使用され、カンナビノイド検索と混在 |
| **非公式エンドポイント** | Google の仕様変更・レート制限の可能性 |
| **非決定性** | 同一クエリでも結果が変動する場合あり |
| **単一回収集** | ばらつきの定量的評価が未実施 |

### 6.2 GSC

| 制約 | 影響 |
|------|------|
| **サイト依存** | 当社サイトの検索パフォーマンスのみを示す |
| **市場全体ではない** | 市場全体の検索需要は Google Trends を参照 |

---

## 7. Key Findings (2026-10-01)

### 7.1 Google Trends 結果

| キーワード | 単独平均 | 比較平均 | ピーク | 備考 |
|-----------|---------|---------|--------|------|
| CBX | 68 | 68 | 100 (2026-09-13) | 多義語のため解釈注意 |
| H4CBH | 56 | 13 | 100 (2026-07-26) | 通年データあり |
| HHBD | 33 | 7 | 100 (2025-12-07) | 2025-12 に初出 |
| CBX リキッド | 44-92 | 0 | 100 (2026-09-20) | 2026-09 から検出 |

### 7.2 多義性に関する重要な発見

```
CBX (比較クエリ, geo=JP, 12-m):
  2026-07 より前の平均: 66.8 (n=40週) ← カンナビノイド CBX 販売前
  2026-07 より後の平均: 73.0 (n=13週) ← 販売後
```

CBX 製品の日本販売開始（2026年7月）**前**でも、平均既に 66.8 と高い。この値はホンダ CBX バイク等の非カンナビノイド検索を含む可能性が高い。したがって、「CBX」単独の Google Trends 値をカンナビノイド特有の需要として解釈することはできない。

---

## 8. Interpretation Guidelines

1. **Google Trends の値は相対指数**であり、絶対検索数ではない
2. **「CBX」は多義語**であり、カンナビノイド固有の検索需要を推定するには「CBX リキッド」等の判別可能なクエリを使用すべき
3. **単独クエリと比較クエリで値が異なる**（低ボリュームクエリは単独では相対的に高く出る）
4. **0 は「検索が存在しない」ことを意味しない**。閾値未満である可能性がある
5. **GSC データは参考**であり、市場全体の検索需要を示すものではない

---

## 9. Reproducibility

### 9.1 再現手順

1. OpenCode の MCP 設定に `google-trends` サーバーが登録済みであることを確認
2. `interest_over_time` を呼び出し:
   - `terms=["CBX"], geo="JP", timeframe="today 12-m"`
   - `terms=["H4CBH"], geo="JP", timeframe="today 12-m"`
   - `terms=["HHBD"], geo="JP", timeframe="today 12-m"`
   - `terms=["CBX リキッド"], geo="JP", timeframe="today 12-m"`
3. `compare_terms` を呼び出し:
   - `terms=["CBX", "H4CBH", "HHBD", "CBX リキッド"], geo="JP", timeframe="today 12-m"`
4. 結果を `data/raw/google_trends/<run-id>/` に JSON で保存

### 9.2 再現性の制約

- Google Trends の非公式エンドポイントは、Google の仕様変更により再現性が保証されない場合がある
- 同一クエリでも結果が変動する可能性がある
- レート制限（HTTP 429）により取得を控えざるを得ない場合がある

---

## 10. Conflict of Interest

本研究の発行者（リキッド通販ショップ）は、カンナビノイド製品を販売するEC事業を運営しています。この商業的関係は、本研究のデータ選択・解釈に影響を及ぼす可能性があります。本ページのデータ・方法論・制約は、独立した評価を可能にするために記載しています。

---

## 11. Related Artifacts

| ファイル | 内容 |
|---------|------|
| `data/raw/google_trends/` | Google Trends 生データ |
| `data/raw/gsc/` | GSC 生データ |
| `README.md` | 研究概要と結果サマリー |
| `../../publication/guide_cbx_rewrite.html` | 公開用ガイドページ |

---

## 12. References

- Google Trends: https://trends.google.com
- google-trends-mcp: https://github.com/purahmanian/google-trends-mcp
- Google Search Console: https://search.google.com/search-console
