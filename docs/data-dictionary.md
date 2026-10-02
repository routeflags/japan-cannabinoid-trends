# Data Dictionary

**Version:** 1.0.0
**Last Updated:** 2026-10-02
**Purpose:** 各データセットのカラム定義、型、単位、欠損値の扱いを文書化

---

## 1. X (Twitter) データ

### 1.1 処理済みデータ: `x_cbx_202608_summary.csv`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `tweet_id` | string | — | X (Twitter) のユニークなツイート ID | 欠損なし |
| `createdAt` | string (ISO 8601) | — | ツイートの投稿日時（UTC） | 欠損なし |
| `lang` | string | — | 言語コード（例: `ja` = 日本語） | 欠損なし |
| `username` | string | — | 投稿者のユーザー名（@なし） | 欠損なし |
| `author_name` | string | — | 投稿者の表示名 | 欠損なし |
| `views` | integer | 回 | ツイートの表示回数 | 欠損なし |
| `likes` | integer | 個 | いいね数 | 欠損なし |
| `reposts` | integer | 個 | リポスト（リツイート）数 | 欠損なし |
| `replies` | integer | 個 | 返信数 | 欠損なし |
| `url` | string (URL) | — | ツイートへの直接リンク | 欠損なし |
| `text` | string | — | ツイート本文（全角・絵文字含む） | 欠損なし |

**データ完全率:** 全カラム 147/147 (100%)

**注意事項:**
- `username` と `author_name` は個人情報を含む可能性があるため、再配布時は注意が必要
- `views` は取得時点の値であり、変動する
- `createdAt` は UTC 表記

### 1.2 匿名化版: `x_cbx_202608_summary_anonymized.csv`

**用途:** 公開用（DOI アーカイブ、第三者再利用）

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `tweet_id_hash` | string | — | ツイート ID の SHA256 ハッシュ（先頭16文字） | 欠損なし |
| `createdAt` | string (ISO 8601) | — | ツイートの投稿日時（UTC） | 欠損なし |
| `week` | string | — | 週分類（W1-W6） | 欠損なし |
| `lang` | string | — | 言語コード（例: `ja` = 日本語） | 欠損なし |
| `author_id` | string | — | 匿名化された著者 ID（author_001 等） | 欠損なし |
| `views` | integer | 回 | ツイートの表示回数 | 欠損なし |
| `likes` | integer | 個 | いいね数 | 欠損なし |
| `reposts` | integer | 個 | リポスト数 | 欠損なし |
| `replies` | integer | 個 | 返信数 | 欠損なし |
| `has_text` | string | — | 本文が存在するか（yes/no） | 欠損なし |
| `text_length` | integer | 文字 | 本文の文字数 | 欠損なし |
| `topic_id` | string | — | 話題分類 ID（SKOS Concept notation） | `unclassified` |
| `intent_id` | string | — | 投稿意図 ID（SKOS Concept notation） | `unclassified` |
| `format_id` | string | — | 投稿形式 ID（SKOS Concept notation） | `unclassified` |
| `platform` | string | — | プラットフォーム名 | `x_twitter` |
| `language` | string | — | 言語コード（BCP 47） | `ja` |

**データ完全率:** 全カラム 147/147 (100%)

**分類フィールドの値:**

| フィールド | 許容値 | タクソノミー |
|-----------|--------|-------------|
| `topic_id` | `topic_ingredient`, `topic_product`, `topic_effect`, `topic_promotion`, `topic_review`, `topic_store`, `unclassified` | `metadata/taxonomy/content-taxonomy.skos.jsonld` |
| `intent_id` | `intent_informational`, `intent_commercial`, `intent_experiential`, `intent_harm_report`, `unclassified` | 同上 |
| `format_id` | `format_text`, `format_image`, `format_video`, `format_link`, `unclassified` | 同上 |

**分類フィールドの参考:**

| フィールド | Schema.org 対応 | SKOS 対応 |
|-----------|----------------|-----------|
| `topic_id` | `schema:about` | `skos:notation` |
| `intent_id` | カスタム | `skos:notation` |
| `format_id` | カスタム | `skos:notation` |
| `platform` | `schema:isPartOf` | — |
| `language` | `schema:inLanguage` | — |

**匿名化内容:**

| 元のフィールド | 匿名化後 | 方法 |
|---------------|---------|------|
| `tweet_id` | `tweet_id_hash` | SHA256 ハッシュ（先頭16文字） |
| `username` | `author_id` | 連番 ID（author_001 等）に置換 |
| `author_name` | （削除） | 個人情報のため削除 |
| `text` | `text_length` | 文字数のみ保持、本文は削除 |
| `url` | （削除） | 個人情報のため削除 |

**匿名化マッピング:**
- ローカル専用: `datasets/cbx-social-trends/data/private/x_anonymization_mapping.json`
- gitignore 対象（公開不可）

### 1.2 集計統計（ガイドページ掲載値）

| 指標 | 中央値 | P90 | 最大値 | 合計 | 算出方法 |
|------|--------|-----|--------|------|---------|
| Views | 963 | 4,904 | 17,247 | 282,478 | 全147件の統計 |
| Likes | 7 | 23 | 110 | 1,715 | 同上 |
| Reposts | 2 | 6 | 127 | 495 | 同上 |

**週別推移:**

| 週 | 期間 | 投稿数 | ユニーク著者数 |
|----|------|:------:|:--------------:|
| W1 | 8/3〜8/9 | 12 | 7 |
| W2 | 8/10〜8/16 | 10 | 9 |
| W3 | 8/17〜8/23 | 48 | 22 |
| W4 | 8/24〜8/30 | 28 | 17 |
| W5 | 8/31〜9/6 | 33 | 18 |
| W6 | 9/7〜9/8 | 13 | 8 |

---

## 2. YouTube データ

### 2.1 フィルタ済みデータ: `youtube_filtered_202607/records_filtered.csv`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `videoId` | string | — | YouTube のユニークな動画 ID | 欠損なし |
| `title` | string | — | 動画タイトル（ハッシュタグ含む） | 欠損なし |
| `channel` | string | — | チャンネル名 | 欠損なし |
| `views` | integer | 回 | 動画の表示回数 | 欠損なし |
| `duration` | string | — | 動画の長さ（例: "5:30"） | 欠損なし |
| `timestamp` | string | — | 公開時期（相対表記: "2 weeks ago"） | 欠損なし |
| `url` | string (URL) | — | 動画への直接リンク | 欠損なし |

**データ完全率:** 全カラム 24/24 (100%)

**フィルタ情報:**

| 項目 | 値 |
|------|-----|
| フィルタ日 | 2026-10-01 |
| 元データ件数 | 26 |
| フィルタ後件数 | 24 |
| 除外件数 | 2 |
| 除外基準 | `timestamp` に "years ago" を含む（2年以上前） |

---

## 3. Google Trends データ

### 3.1 raw データ: `google_trends/{run_id}/records.json`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `query` | string | 検索クエリ（例: "CBX"） |
| `geo` | string | 地域コード（例: "JP"） |
| `timeframe` | string | 観測期間（例: "today 12-m"） |
| `collected_at` | string (ISO 8601) | 収集日時（UTC） |
| `source` | string | データソース（"google-trends-mcp"） |
| `data` | array | 週次データポイントの配列 |

**`data` 配列の各要素:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | string (ISO 8601) | 週の開始日 |
| `interest` | integer (0-100) | 検索関心度（相対指数） |

**注意:** Google Trends の値は相対指数であり、絶対検索数ではない。

### 3.2 比較データ: `google_trends/{run_id}/comparison.json`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `terms` | array | 比較対象のクエリ一覧 |
| `geo` | string | 地域コード |
| `timeframe` | string | 観測期間 |
| `data` | array | クエリ別の週次データポイント |

---

## 4. COA データ

### 4.1 分析結果（ガイドページ掲載値）

| 分析項目 | 単位 | KCA Labs | Anresco | 判定 |
|----------|------|----------|---------|------|
| CBG | % | 30.4 | 30.28 | 一致 |
| CBD | % | 5.74 | 5.27 | ほぼ一致 |
| Total Cannabinoids | % | 36.1 | 35.55 | ほぼ一致 |
| Δ9-THC | % (ppm) | 0.000045 (0.45 ppm) | ND | 微量検出 |
| Δ8-THC | % | ND | ND | 未検出 |
| HHC | % | ND | ND | 未検出 |
| HHCH | % | ND | ND | 未検出 |
| THCP | % | ND | ND | 未検出 |

**ND = Not Detected（未検出）**

**注意:**
- 分析対象は原料（Concentrate-Distillate）であり、成品ではない
- Δ9-THC の限度値は原料 10 ppm、成品（その他）1 ppm

---

## 5. キーワード辞書: `metadata/keywords.yaml`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `display_name` | string | 表示名 |
| `category` | string | カテゴリ（例: "minor_phytocannabinoid"） |
| `keywords` | array | 検索に使用するキーワード一覧 |
| `polysemy_warning` | string / null | 多義性に関する警告 |
| `discriminating_queries` | array | 多義性を排除する判別クエリ |
| `search_notes` | object | プラットフォーム別の検索ノート |

---

## 6. 欠損値の扱い

### 6.1 状態定義

| 状態 | 意味 | 表記 |
|------|------|------|
| `observed_zero` | 観測されたが、値がゼロ | 0 |
| `observed_nonzero` | 観測され、値が存在 | 実際の値 |
| `missing` | データが存在しない | 空文字または "NA" |
| `collection_failed` | 収集が失敗した | "collection_failed" |
| `partial` | 部分的なデータ | 実際の値 + 注記 |
| `unknown` | 不明 | "unknown" |

### 6.2 各データセットの欠損値状況

| データセット | 欠損値 | 状態 |
|-------------|--------|------|
| X データ (147件) | なし | 全カラム 100% |
| YouTube データ (24件) | なし | 全カラム 100% |
| Google Trends | 低ボリュームクエリで 0 件 | `observed_zero` または `no_data` |
| 26週 X データ | 空週あり | `observed_zero`（製品投入前） |

---

## 7. カラム名の正規化

### 7.1 X データ

| 元のフィールド（Apify） | 正規化後 | 理由 |
|------------------------|---------|------|
| `tweet_id` | `tweet_id` | そのまま |
| `created_at` | `createdAt` | キャメルケースに統一 |
| `user_info.screen_name` | `username` | ネスト解除 |
| `user_info.name` | `author_name` | ネスト解除 |
| `favorites` | `likes` | 意味が明確な名前に変更 |
| `retweets` | `reposts` | 意味が明確な名前に変更 |
| `text` | `text` | そのまま |

---

## 8. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `methodology.md` | 収集・処理方法の詳細 |
| `datasets/cbx-social-trends/methodology.md` | ソーシャルデータの方法論 |
| `datasets/cbx-search-trends/methodology.md` | 検索トレンドの方法論 |
| `docs/provenance.md` | データ来歴の詳細 |
| `metadata/datapackage.json` | データパッケージ定義 |
| `metadata/keywords.yaml` | キーワード辞書 |
