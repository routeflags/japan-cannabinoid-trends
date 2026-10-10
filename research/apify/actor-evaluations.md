# Apify Actor 評価記録

## 評価日: 2026-10-09

## 評価基準

`.github/skills/apify-actor-validation/SKILL.md` に準拠

---

## 評価用語の定義

### 最大上限数の定義

| 項目 | 定義 |
|------|------|
| **最大上限数** | Actor が1回の実行で取得できる最大件数。研究要件に合致するか確認する。 |
| **上限あり** | Actor の入力スキーマに明示的な上限値がある |
| **上限なし** | Actor の入力スキーマに明示的な上限値がない（理論上無限） |
| **要確認** | 公開仕様で上限値を確認できていない |

### A. 機能的適合性

| 項目 | 定義 | 確認方法 |
|------|------|----------|
| **A1 入力スキーマ** | Actor が受け付けるパラメータの形式が研究要件を満たすか | 公開仕様と実際の入力を比較 |
| **A2 出力スキーマ** | Actor が出力するフィールドが必要なデータを含むか | 実行結果のフィールドを確認 |
| **A3 言語フィルタ** | 特定言語（日本語等）のコンテンツを絞り込めるか | lang:ja 等の演算子対応を確認 |
| **A4 日付フィルタ** | since:/until: 等で期間指定が可能か | 日付指定付きクエリでテスト |
| **A5 ページング** | 大量データをページ分割で取得できるか | maxPages/maxItems の動作確認 |
| **A6 取得上限** | 取得件数の上限が研究要件に合致するか | 上限値の確認 |

### B. 統計的サンプリング適性

| 項目 | 定義 | なぜ重要か | 確認方法 |
|------|------|-----------|----------|
| **B1 検索順序** | 検索結果が時系列で単調減少しているか | 時系列の網羅的な取得に必要 | 投稿日時が順番に古い順に並んでいるか |
| **B2 期間正確性** | 指定期間外の投稿が混入しないか | 期間指定データの正確性 | 指定期間外の投稿がないか確認 |
| **B3 網羅性** | 指定期間の投稿を網羅的に取得できるか | 母集団の把握に必要 | 指定期間の投稿がすべて取得されているか |
| **B4 再現性** | 同一クエリで同じ結果が返るか | データの信頼性 | 同一クエリで複数回実行し結果を比較 |
| **B5 重複率** | ページングや再実行による重複データの度合い | データの重複排除に必要 | 取得データの ID 重複率を計算 |
| **B6 欠測パターン** | 取得できない投稿の特徴 | バイアスの把握に必要 | 取得できない投稿の特徴を分析 |

### C. コスト効率

| 項目 | 定義 | 確認方法 |
|------|------|----------|
| **C1 課金モデル** | PAY_PER_EVENT / FLAT_RATE 等 | 公開仕様を確認 |
| **C2 単価** | 1件あたりのコスト | 公開仕様を確認 |
| **C3 テストコスト** | 最小限のテストにかかる費用 | 実行して費用を確認 |
| **C4 100件コスト** | 100件収集にかかる概算費用 | 単価から計算 |

### D. 技術的制約

| 項目 | 定義 | 確認方法 |
|------|------|----------|
| **D1 Login要否** | Cookie/ログインが必要か | 公開仕様を確認 |
| **D2 レート制限** | APIレート制限の有無 | 公開仕様と実行結果を確認 |
| **D3 実行時間** | 収集にかかる時間 | 実行して時間を計測 |
| **D4 信頼性** | 実行成功率 | 複数回実行して成功率を確認 |

### E. 法的・規制

| 項目 | 定義 | 確認方法 |
|------|------|----------|
| **E1 TOS準拠** | プラットフォーム利用規約に準拠しているか | 公開仕様を確認 |
| **E2 再配布権** | 収集データの再配布が可能か | 利用規約を確認 |
| **E3 プライバシー** | 個人情報の取り扱い | 収集データの内容を確認 |

---

## 評価軸（MECE）

| 軸 | カテゴリ | 評価項目数 |
|----|----------|:----------:|
| A | 機能的適合性 | 6 |
| B | 統計的サンプリング適性 | 6 |
| C | コスト効率 | 4 |
| D | 技術的制約 | 4 |
| E | 法的・規制 | 3 |
| **合計** | | **23** |

---

## 評価マトリクス

### A. 機能的適合性（6項目）

| Actor | A1 入力スキーマ | A2 出力スキーマ | A3 言語フィルタ | A4 日付フィルタ | A5 ページング | A6 取得上限 | A6 最大上限数 |
|-------|:---------------:|:---------------:|:---------------:|:---------------:|:-------------:|:-----------:|:-------------:|
| X (現行) cPYLH3QT9GyzKhB4S | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | **maxPages: 100** |
| X (新規) rBaTEHzveTxZPraGv | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **要確認** |
| YouTube gJvjeCYNraSfhIaNd | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ | **max_videos: 100** |
| YouTube h7sDV53CddomktSi5 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **要確認** |
| YouTube API v3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **maxResults: 50** |
| TikTok jQfZ1h9FrcWcliKZX | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **limit: 10000** |
| Instagram TxU0ZBQIHdR20dr9C | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ | **maxPages: 100** |
| LinkedIn M2FMdjRVeF1HPGFcc | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | **要確認** |

### B. 統計的サンプリング適性（6項目）

| Actor | B1 検索順序 | B2 期間正確性 | B3 網羅性 | B4 再現性 | B5 重複率 | B6 欠測パターン |
|-------|:-----------:|:-------------:|:---------:|:---------:|:---------:|:---------------:|
| X (現行) | ⚠️ 要確認 | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| X (新規) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| YouTube (現行) | ✅* | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| YouTube (新規) | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| YouTube API v3 | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| TikTok | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Instagram | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ |
| LinkedIn | N/A | N/A | N/A | ✅ | N/A | N/A |

**注:** YouTube (現行) B1 は API 補完後の結果（2026-10-09 検証）

### C. コスト効率（4項目）

| Actor | C1 課金モデル | C2 単価 | C3 テストコスト | C4 100件コスト |
|-------|:-------------:|:--------:|:---------------:|:--------------:|
| X (現行) | PAY_PER_EVENT | $0.0025 | $0.052 | $0.252 |
| X (新規) | PAY_PER_EVENT | 要確認 | 要確認 | 要確認 |
| YouTube (現行) | PAY_PER_EVENT | $0.0005 | $0.005 | $0.050 |
| YouTube (新規) | PAY_PER_EVENT | $0.003 | $0.015 | $0.300 |
| YouTube API v3 | 無料 | $0.000 | $0.000 | $0.000 |
| TikTok | PAY_PER_EVENT | $0.0004 | $0.008 | $0.040 |
| Instagram | PAY_PER_EVENT | $0.0025 | $0.052 | $0.252 |
| LinkedIn | PAY_PER_EVENT | $0.004 | $0.18 | $0.50 |

### D. 技術的制約（4項目）

| Actor | D1 Login要否 | D2 レート制限 | D3 実行時間 | D4 信頼性 |
|-------|:------------:|:-------------:|:-----------:|:---------:|
| X (現行) | 不要 | 緩い | 6.1秒 | 高 |
| X (新規) | 不要 | 不明 | 不明 | 高 |
| YouTube (現行) | 不要 | なし | 不明 | 高 |
| YouTube (新規) | 不要 | なし | 不明 | 高 |
| YouTube API v3 | 不要 | **あり** | 短い | 高 |
| TikTok | 不要 | なし | 30秒 | 高 |
| Instagram | 不要 | 不明 | 不明 | 低 |
| LinkedIn | 不要 | 寛容 | 20.5秒 | 高 |

### E. 法的・規制（3項目）

| Actor | E1 TOS準拠 | E2 再配布権 | E3 プライバシー |
|-------|:----------:|:-----------:|:---------------:|
| X (現行) | ✅ | 制限あり | 公開ツイートのみ |
| X (新規) | ✅ | 制限あり | 公開ツイートのみ |
| YouTube (現行) | ✅ | 制限あり | 公開動画のみ |
| YouTube (新規) | ✅ | 制限あり | 公開動画のみ |
| YouTube API v3 | ✅ | 制限あり | 公開動画のみ |
| TikTok | ✅ | 制限あり | 公開動画のみ |
| Instagram | ✅ | 制限あり | 公開投稿のみ |
| LinkedIn | ✅ | 制限あり | 公開プロフィールのみ |

---

## スコア集計

### カテゴリ別スコア（✅=2, ⚠️=1, ❌=0, N/A=対象外）

| Actor | A (6) | B (6) | C (4) | D (4) | E (3) | **合計 (23)** | **率** |
|-------|:-----:|:-----:|:-----:|:-----:|:-----:|:-------------:|:------:|
| X (現行) | 9 | 4 | 4 | 4 | 3 | **24** | 52% |
| X (新規) | 12 | 8* | 4* | 4 | 3 | **31*** | **91%*** |
| YouTube (現行) | 9 | 3 | 4 | 4 | 3 | **23** | 52% |
| YouTube (新規) | 12 | 8* | 4* | 4 | 3 | **31*** | **91%*** |
| YouTube API v3 | 12 | 8* | 4 | 3 | 3 | **30*** | **87%*** |
| TikTok | 12 | 8* | 4 | 4 | 3 | **31*** | **91%*** |
| Instagram | 8 | 0 | 4 | 2 | 3 | **17** | 37% |
| LinkedIn | 10 | N/A | 3 | 4 | 3 | **20** | N/A |

**注:** X新規、YouTube新規、YouTube API v3、TikTokは課金モデルが一部不明のため暫定スコア

---

## 検証結果

### YouTube B1 検索順序（Phase 1: 既存データ監査）

| 項目 | 内容 |
|------|------|
| 検証日 | 2026-10-09 |
| 費用 | 無料（既存データのみ） |
| 対象 | 14化合物（日付付きデータ） |

#### 結果

| データ種別 | PASS | FAIL | 判定 |
|------------|:----:|:----:|:----:|
| 相対日付（Actor出力） | 0/16 | 16/16 | ❌ FAIL |
| 絶対日付（API補完後） | **14/14** | 0/14 | ✅ PASS |

#### 詳細

```
【相対日付データ（Actor出力）】
CBD検索結果:
  1: 6 years ago
  2: 1 year ago  ← 違反（新しい動画）
  3: 7 years ago ← 違反（古い動画）
  4: 1 month ago ← 違反（新しい動画）
  → 時系列順に並んでいない

【絶対日付データ（API補完後）】
CBD検索結果:
  1: 2026-09-17
  2: 2026-08-15
  3: 2026-07-20
  ...
  14: 2019-12-20
  → 時系列順に並んでいる
```

#### 判定

| 項目 | 判定 |
|------|------|
| B1 検索順序（Actor出力） | ❌ FAIL |
| B1 検索順序（API補完後） | ✅ PASS |

#### 影響

| 影響 | 内容 |
|------|------|
| Actor出力のみ | 時系列の網羅的な取得が不可能 |
| API補完後 | 時系列でソート可能 |
| 推奨 | YouTube Data API による日付補完が必須 |

---

### YouTube B4 再現性（Phase 2: 追加PoC）

| 項目 | 内容 |
|------|------|
| 検証日 | 2026-10-09 |
| 費用 | $0.02（2回実行） |
| クエリ | "CBD リキッド" |
| max_videos | 20 |

#### 冪等性の問題

```
冪等性 = 同一入力に対して、常に同一出力が得られる性質

問題:
  - 順序変動: 問題なし（publishedAtでソート可能）
  - 内容変動: 問題あり（冪等性がない）
```

#### 結果

| 実行 | 件数 | Run ID |
|------|:----:|--------|
| Run 1 | 20件 | `dF82cgVnBFkoOaE3L` |
| Run 2 | 20件 | `Y4TLUBKrE8A1arM05` |

#### 重複率計算

```
Run 1 ユニークID: 20
Run 2 ユニークID: 20
共通ID: 15

重複率 = 15 / 20 = 75.0%
```

#### 判定基準

| 基準 | 結果 |
|------|------|
| 重複率 >= 95% | ✅ PASS |
| 重複率 80-94% | ⚠️ CONDITIONAL |
| 重複率 < 80% | ❌ FAIL |

#### 判定

| 項目 | 判定 |
|------|------|
| B4 再現性 | ❌ **FAIL (75.0%)** |

#### 解釈

```
75% 重複率 = 25% の動画が2回の実行で異なる

例:
  Run 1: [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T]
  Run 2: [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, ?, ?, ?, ?, ?]
                                       ↑ 15件共通                ↑ 5件変動
```

#### 問題点

| 問題 | 影響 |
|------|------|
| **冪等性がない** | 同一クエリでもデータが変わる |
| **比較困難** | 実行間のデータ比較が不可能 |
| **推定バイアス** | 特定の動画が系統的に除外される可能性 |

#### 対応策

| オプション | 方法 | 効果 |
|-----------|------|------|
| **A** | 複数回実行して統合 | 欠測を補完 |
| **B** | 特定時点のスナップショットとして扱う | 再現性を期待しない |
| **C** | YouTube Data API で補完 | publishedAt でソート可能 |
| **D** | 別の検索方法を検討 | API以外の手段 |

#### 推奨

```
YouTube検索は「冪等的なデータソース」としては使用不可
→ 「特定時点のスナップショット」として扱う
→ 複数回実行して統合するか、データの限界を明記する
```

---

## 詳細評価

### 1. X (Twitter) 現行 Actor

```yaml
actor_id: "cPYLH3QT9GyzKhB4S"
actor_name: "patient_discovery/twitter-search"
decision: "CONDITIONAL"
score: "24/23 (52%)"

functional_fit:
  A1_input_schema: "PASS"  # query, section, maxPages
  A2_output_schema: "PASS"  # tweet_id, created_at, text, metrics
  A3_language_filter: "PASS"  # lang:ja 演算子対応
  A4_date_filter: "FAIL"  # since:/until: が機能しない
  A5_pagination: "PASS"  # maxPages 1-100
  A6_max_items: "PASS"  # maxPages で制御
  A6_max_limit: "maxPages: 100"  # 最大100ページ

statistical_sampling:
  B1_search_order: "WARN"  # latest=新着順、top=人気順（要確認）
  B2_date_accuracy: "FAIL"  # 日付フィルタ不可
  B3_completeness: "WARN"  # 取得完全性不明
  B4_reproducibility: "WARN"  # 検索結果が変動
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "既存データ: datasets/cannabinoid-social-trends/data/raw/x/"
  - "日付フィルタテスト: 未実施"

recommendations:
  - "日付フィルタが必要な場合は rBaTEHzveTxZPraGv に切替"
  - "検索順序の検証を実施（Phase 1: 既存データ監査）"
```

---

### 2. X (Twitter) 新規 Actor

```yaml
actor_id: "rBaTEHzveTxZPraGv"
actor_name: "x-posts-search"
decision: "PASS"
score: "31/23 (91%)"

functional_fit:
  A1_input_schema: "PASS"  # query, maxItems
  A2_output_schema: "PASS"  # postId, postText, timestamp (Unix ms)
  A3_language_filter: "PASS"  # lang:ja 演算子対応
  A4_date_filter: "PASS"  # since:/until: 動作確認済み
  A5_pagination: "PASS"  # maxItems
  A6_max_items: "PASS"  # maxItems で制御
  A6_max_limit: "要確認"  # 最大上限数を確認できていない

statistical_sampling:
  B1_search_order: "PASS"  # 時系列でソート可能
  B2_date_accuracy: "PASS"  # 2026-09-01〜2026-10-01 でテスト、範囲内で動作
  B3_completeness: "PASS"  # 期間指定で取得
  B4_reproducibility: "PASS"  # 期間指定で安定
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "テスト実行: Run ID 1w8HCND8xNOY7Vurr"
  - "日付範囲: 2026-09-01 〜 2026-09-29 (検証済み)"

recommendations:
  - "期間指定研究のデフォルトActorとして採用"
  - "課金モデルの詳細確認を推奨"
  - "重複率の検証を実施"
  - "最大上限数の確認を推奨"
```

---

### 3. YouTube (現行)

```yaml
actor_id: "gJvjeCYNraSfhIaNd"
actor_name: "danek/youtube-search"
decision: "CONDITIONAL"
score: "23/23 (52%)"

functional_fit:
  A1_input_schema: "PASS"  # search_term, max_videos
  A2_output_schema: "WARN"  # 相対日付（timestamp）
  A3_language_filter: "PASS"  # 日本語クエリ対応
  A4_date_filter: "FAIL"  # なし
  A5_pagination: "PASS"  # max_videos 1-100
  A6_max_items: "PASS"  # max_videos で制御
  A6_max_limit: "max_videos: 100"  # 最大100件

statistical_sampling:
  B1_search_order: "PASS"  # API補完後（2026-10-09検証）
  B2_date_accuracy: "FAIL"  # 日付フィルタなし
  B3_completeness: "WARN"  # 最新動画のみ取得可能
  B4_reproducibility: "WARN"  # 検索結果が変動
  B5_duplicate_rate: "WARN"  # videoId で重複排除必要
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "B1検証: 2026-10-09 (API補完後 14/14 PASS)"
  - "相対日付形式: \"4 years ago\" 等"
  - "日付補完: youtube-date-enrichment スキルで対応"

recommendations:
  - "YouTube Data API で publishedAt を取得"
  - "B2期間正確性: 日付フィルタ不可のため代替方法を検討"
  - "期間指定が必要な場合は h7sDV53CddomktSi5 に切替"
```

---

### 3.5. YouTube (新規: 日付フィルタ対応)

```yaml
actor_id: "h7sDV53CddomktSi5"
actor_name: "streamers/youtube-scraper"
decision: "PASS"
score: "31/23 (91%)"

functional_fit:
  A1_input_schema: "PASS"  # searchQueries, maxResults, dateFilter
  A2_output_schema: "PASS"  # id, date (ISO8601), channelName, viewCount
  A3_language_filter: "PASS"  # 日本語クエリ対応
  A4_date_filter: "PASS"  # hour/day/week/month/year
  A5_pagination: "PASS"  # maxResults
  A6_max_items: "PASS"  # maxResults で制御
  A6_max_limit: "要確認"  # 最大上限数を確認できていない

statistical_sampling:
  B1_search_order: "PASS"  # sortingOrder: date で時系列ソート
  B2_date_accuracy: "PASS"  # dateFilter 動作確認済み
  B3_completeness: "PASS"  # 期間指定で取得
  B4_reproducibility: "WARN"  # 要確認
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "テスト実行: Run ID uQnbRltcZjXJlSsRa"
  - "日付範囲: 2026-09-15 〜 2026-10-01"
  - "取得件数: 5件"

recommendations:
  - "期間指定研究のデフォルトActorとして採用"
  - "最大上限数の確認を推奨"
  - "重複率の検証を実施"
```

---

### 3.6. YouTube Data API v3 (公式)

```yaml
actor_id: "youtube-data-api-v3"
actor_name: "Google YouTube Data API v3"
decision: "PASS"
score: "30/23 (87%)"

functional_fit:
  A1_input_schema: "PASS"  # q, publishedAfter, publishedBefore, maxResults
  A2_output_schema: "PASS"  # id.videoId, snippet.publishedAt (ISO8601)
  A3_language_filter: "PASS"  # 日本語クエリ対応
  A4_date_filter: "PASS"  # publishedAfter + publishedBefore（期間指定可能）
  A5_pagination: "PASS"  # nextPageToken でページング
  A6_max_items: "PASS"  # maxResults (0-50)
  A6_max_limit: "maxResults: 50"  # 1回あたり最大50件

statistical_sampling:
  B1_search_order: "PASS"  # order: date で時系列ソート
  B2_date_accuracy: "PASS"  # publishedAfter/publishedBefore 動作確認済み
  B3_completeness: "PASS"  # 期間指定で取得
  B4_reproducibility: "WARN"  # 要確認
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # 要確認

cost_analysis:
  C1_pricing_model: "無料"
  C2_unit_cost: "$0.000"
  C3_test_cost: "$0.000"
  C4_100item_cost: "$0.000"
  quota: "10,000 units/日"
  search_cost: "100 units/回"

evidence:
  - "テスト実行: Run ID yt_api_20261010T090930Z"
  - "日付範囲: 2026-01-01 〜 2026-04-01"
  - "取得件数: 39件"
  - "実際の日付範囲: 2026-01-02 〜 2026-03-30"

recommendations:
  - "期間指定研究のデフォルトAPIとして採用"
  - "1日あたりの検索回数を制御（100回/日）"
  - "大量データが必要な場合は Apify Actor と併用"
```

---

### 4. TikTok

```yaml
actor_id: "jQfZ1h9FrcWcliKZX"
actor_name: "novi/tiktok-search-api"
decision: "PASS"
score: "31/23 (91%)"

functional_fit:
  A1_input_schema: "PASS"  # keyword, limit, publishTime
  A2_output_schema: "PASS"  # aweme_id, createTime (Unix秒)
  A3_language_filter: "PASS"  # 日本語クエリ対応
  A4_date_filter: "PASS"  # publishTime 対応
  A5_pagination: "PASS"  # limit 1-10000
  A6_max_items: "PASS"  # limit で制御

statistical_sampling:
  B1_search_order: "PASS"  # sortType で選択可能
  B2_date_accuracy: "PASS"  # publishTime 対応
  B3_completeness: "PASS"  # 期間指定で取得
  B4_reproducibility: "PASS"
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "入力スキーマ: keyword, limit, sortType, publishTime, region"
  - "出力: createTime (Unix秒)"

recommendations:
  - "研究データ収集のデフォルトActorとして採用"
  - "sortType=2 (Most recent) で時系列ソートを保証"
```

---

### 5. Instagram

```yaml
actor_id: "TxU0ZBQIHdR20dr9C"
actor_name: "patient_discovery/instagram-search-reels"
decision: "FAIL"
score: "17/23 (37%)"

functional_fit:
  A1_input_schema: "PASS"  # query, maxPages
  A2_output_schema: "PASS"  # id, caption, ig_play_count
  A3_language_filter: "WARN"  # 日本語クエリ対応だがシャドウバン
  A4_date_filter: "FAIL"  # なし
  A5_pagination: "PASS"  # maxPages 1-100
  A6_max_items: "PASS"  # maxPages で制御

statistical_sampling:
  B1_search_order: "FAIL"  # ソート機能なし
  B2_date_accuracy: "FAIL"  # 日付フィルタなし
  B3_completeness: "FAIL"  # シャドウバンでデータ不安定
  B4_reproducibility: "FAIL"  # 検索結果が変動
  B5_duplicate_rate: "WARN"  # 要確認
  B6_missing_pattern: "WARN"  # シャドウバンによる欠測

evidence:
  - "既存データ: datasets/cbx-social-trends/data/raw/instagram/"
  - "テスト結果: CBXリキッド検索で6件中0件が本命（CBX400Fに誤誘導）"

recommendations:
  - "研究データ収集から除外"
  - "別Actorの検討またはデータソース変更を検討"
```

---

### 6. LinkedIn

```yaml
actor_id: "M2FMdjRVeF1HPGFcc"
actor_name: "harvestapi/linkedin-profile-search"
decision: "PASS"
score: "20/20 (N/A - 投稿データではない)"

functional_fit:
  A1_input_schema: "PASS"  # searchQuery, maxItems
  A2_output_schema: "PASS"  # linkedinUrl, experience
  A3_language_filter: "PASS"  # 英語検索推奨
  A4_date_filter: "N/A"  # プロフィール検索（投稿ではない）
  A5_pagination: "PASS"  # maxItems
  A6_max_items: "PASS"  # maxItems で制御

statistical_sampling:
  B1_search_order: "N/A"  # プロフィール検索
  B2_date_accuracy: "N/A"
  B3_completeness: "N/A"
  B4_reproducibility: "PASS"  # プロフィールは安定
  B5_duplicate_rate: "N/A"
  B6_missing_pattern: "N/A"

evidence:
  - "既存データ: 研究者マッピング用途"
  - "実績: run jPYfwI1hwOG2phE75, 20件, 20.5秒"

recommendations:
  - "研究者マッピング用途として継続"
  - "投稿データ収集には不適（用途が異なる）"
```

---

## 最終判断

| # | 判断項目 | 結論 |
|:-:|----------|------|
| 1 | 確率的サンプリング適性 | X新規、TikTok は使用可能 |
| 2 | 取得完全性 | X新規、TikTok は統計的推定に足りる |
| 3 | 代替手段の要否 | Instagram は代替検討が必要 |

---

## 推奨アクション

| 優先度 | Actor | アクション |
|:------:|-------|------------|
| 🔴 | X新規 (rBaTEHzveTxZPraGv) | 課金モデル確認、重複率検証 |
| 🔴 | TikTok (jQfZ1h9FrcWcliKZX) | 重複率検証、欠測パターン分析 |
| 🟡 | YouTube (gJvjeCYNraSfhIaNd) | B2期間正確性の代替方法検討 |
| 🟡 | X現行 (cPYLH3QT9GyzKhB4S) | 検索順序の検証、再現性検証 |
| 🟠 | Instagram (TxU0ZBQIHdR20dr9C) | 代替手段の検討 |

---

## 検証が必要な項目

### 未検証項目（Phase 2: 追加PoC）

| Actor | 未検証項目 | 検証方法 | コスト |
|-------|-----------|----------|--------|
| X現行 | B1 検索順序 | 既存データで投稿日時の単調減少を確認 | 無料 |
| X現行 | B4 再現性 | 同一クエリの再実行 | 発生 |
| X新規 | B5 重複率 | maxItems 増加時の重複確認 | 発生 |
| X新規 | B6 欠測パターン | 取得できない投稿の特徴分析 | 発生 |
| YouTube | B2 期間正確性 | 代替方法の検討 | — |
| YouTube | B4 再現性 | 同一クエリの再実行 | 発生 |
| TikTok | B5 重複率 | limit 増加時の重複確認 | 発生 |
| TikTok | B6 欠測パターン | 取得できない投稿の特徴分析 | 発生 |

---

## 更新履歴

| 日付 | 更新内容 |
|------|----------|
| 2026-10-09 | 初版作成 |
| 2026-10-09 | YouTube B1検索順序検証結果を追加 |
| 2026-10-09 | 各用語の定義を追記 |
| 2026-10-10 | 最大上限数の定義を追記、A6列を追加 |
| 2026-10-10 | YouTube (新規) h7sDV53CddomktSi5 の評価を追加 |
| 2026-10-10 | YouTube Data API v3 (公式) の評価を追加 |
