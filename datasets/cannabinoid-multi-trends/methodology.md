# Methodology

## 1. 研究設計

### 1.1 研究 ID

```
cannabinoid-multi-trends
```

### 1.2 観測期間

| データソース | 観測期間 |
|-------------|---------|
| Google Trends | 2025-10 〜 2026-10 (today 12-m) |
| X (Twitter) | 2026-09-01 〜 2026-10-01 |
| YouTube | 2026-10-02 (スナップショット) |

### 1.3 対象化合物

| キーワード | SKOS Concept ID | カテゴリ |
|-----------|----------------|---------|
| CBD | compound_cbd | Major Phytocannabinoid |
| THC | compound_thc | Major Phytocannabinoid |
| CBG | compound_cbg | Minor Phytocannabinoid |
| HHC | compound_hhc | Semi-Synthetic Cannabinoid |
| THCV | compound_thcv | Minor Phytocannabinoid |
| THC-O | compound_thc_o | Semi-Synthetic Cannabinoid |
| THCH | compound_thch | Minor Phytocannabinoid |

---

## 2. データ収集

### 2.1 Google Trends

**ツール:** google-trends-mcp (npm v0.1.1)

**パラメータ:**
- geo: `JP`
- timeframe: `today 12-m`

**収集内容:**
1. 各キーワードの interest_over_time（単独）
2. 比較セットの compare_terms
3. 関連クエリの related_queries

**比較セット:**
- セットA: CBD, THC, CBG, HHC, THCV
- セットB: THC-O, THCH, CBD オイル, THC オイル, HHC オイル

**注意事項:**
- Google Trends は相対指数（0-100）
- 低ボリュームクエリはデータが返らない場合あり
- 429 エラー時は 2-5 分待機

### 2.2 X (Twitter)

**ツール:** Apify Actor `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search)

**パラメータ:**
- section: `latest`
- maxPages: 2-3（キーワードに依存）
- query: `{keyword} since:2026-09-01 until:2026-10-01`

**収集キーワード:**

| キーワード | maxPages | コスト目安 |
|-----------|----------|-----------|
| CBD | 3 | $0.152 |
| THC | 3 | $0.152 |
| CBG | 2 | $0.077 |
| HHC | 2 | $0.077 |
| THCV | 2 | $0.077 |
| THC-O | 2 | $0.052 |
| THCH | 2 | $0.052 |

**注意事項:**
- シャドウバンの可能性（THC 等の敏感キーワード）
- 0 件でも observed_zero として記録
- chargedEventCounts を信用せず、records.json の件数を確認

### 2.3 YouTube

**ツール:** Apify Actor `gJvjeCYNraSfhIaNd` (danek/youtube-search)

**パラメータ:**
- max_videos: 50-100（キーワードに依存）

**収集キーワード:**

| キーワード | max_videos | コスト目安 |
|-----------|-----------|-----------|
| CBD | 100 | $0.050 |
| THC | 100 | $0.050 |
| CBG | 50 | $0.025 |
| HHC | 50 | $0.025 |
| THCV | 50 | $0.025 |
| CBD オイル | 50 | $0.025 |
| THC オイル | 50 | $0.025 |

**注意事項:**
- ページング重複あり、videoId で重複排除必須
- timestamp は相対表記（"3 days ago" 等）

---

## 3. データ処理

### 3.1 重複排除

| ソース | キー | 方法 |
|--------|------|------|
| X | tweet_id | ユニーク ID で重複排除 |
| YouTube | videoId | ユニーク ID で重複排除 |
| Google Trends | date | 週次データで重複なし |

### 3.2 分類

SKOS Concept ID を使用して化合物カテゴリを分類。

### 3.3 匿名化（X データ）

正本は `docs/data-dictionary.md` の匿名化マッピング。実行規則は
`src/processing/anonymize.py` にあり、`cbx-social-trends` の匿名化済み成果物に対して
列単位で検証されている。

| 元フィールド | 匿名化後 | 方法 |
|-------------|---------|------|
| `screen_name` | `author_id` | 初出順の連番 ID（`author_001` 等）に置換。**ハッシュではない** |
| `author_name` | （削除） | 個人情報のため削除 |
| `text` | `text_length` | 文字数のみ保持、本文は削除 |
| `tweet_id` | `tweet_id_hash` | SHA-256 ハッシュの**先頭 16 文字** |
| `url` | （削除） | 個人情報のため削除 |

> **2026-10-13 訂正:** 本表は以前「`screen_name` → `author_id` はハッシュ化」と
> 記載していたが誤り。実成果物の `author_id` は初出順の連番である。また
> `tweet_id_hash` は SHA-256 全長ではなく先頭 16 文字である。本 study は X raw を
> リポジトリに保持していないため、この変換の適用先成果物は
> `cbx-social-trends` 側にある。

---

## 4. 品質管理

### 4.1 検証項目

- [ ] Google Trends スコア範囲（0-100）
- [ ] X/YouTube 件数確認
- [ ] キーワード含有率確認
- [ ] コスト実績確認

### 4.2 制約事項

| 制約 | 対策 |
|------|------|
| Google Trends 相対指数 | 絶対検索数ではない点を明記 |
| X シャドウバン | 0 件でも observed_zero として記録 |
| 多義語（CBD, THC） | コンテキスト分析で誤検知を排除 |
| コソソース間の比較 | 単位が異なるため直接比較不可 |

---

## 5. 局所化

### 5.1 関連研究

| Study ID | 関係 |
|----------|------|
| cbx-search-trends | CBX/H4CBH/HHBD の検索需要 |
| cbx-social-trends | CBX の SNS 言及 |
| cbx-liquid-online-trend | CBX リキッドの週次データ |

### 5.2 既存インフラ

- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
- 検証スクリプト: `scripts/validation/validate-data-schema.sh`
- エクスポート: `scripts/export/`

## 6. 研究軸の分離（2026-10-12 追記）

cbx-search-trends は CBX 製品軸（CBX リキッド等の製品需要）の研究であり、cannabinoid-multi-trends は成分横断軸（CBD・THC・CBG・CBN・HHC 等の成分間比較）の研究である。両者は観測対象の軸が異なるため、クエリー設計・比較スケール・解釈を分離する。日本語「○○ リキッド」拡張（GTJA-20261012）は成分横断軸に属し、CBX は比較のアンカー語としてのみ用いる。
