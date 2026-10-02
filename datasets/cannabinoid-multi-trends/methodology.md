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

| 元フィールド | 匿名化後 | 方法 |
|-------------|---------|------|
| screen_name | author_id | ハッシュ化 |
| text | text_length | 文字数カウント |
| tweet_id | tweet_id_hash | SHA-256 ハッシュ |

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
