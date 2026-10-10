# Apify Actor 評価記録

## 評価日: 2026-10-09

## 評価対象

`routeflags/japan-cannabinoid-trends` で利用中の Apify Actor

## 評価基準

`.github/skills/apify-actor-validation/SKILL.md` に準拠

---

## 総合評価表

| Actor | ID | 日付フィルタ | 統計的サンプリング | コスト/件 | 判定 |
|-------|-----|:------------:|:------------------:|----------|:----:|
| **X (現行)** | cPYLH3QT9GyzKhB4S | ❌ | ⚠️ | $0.0025 | CONDITIONAL |
| **X (新規)** | rBaTEHzveTxZPraGv | ✅ | ✅ | 要確認 | **PASS** |
| **YouTube** | gJvjeCYNraSfhIaNd | ❌ | ⚠️ | $0.0005 | CONDITIONAL |
| **TikTok** | jQfZ1h9FrcWcliKZX | ✅ | ✅ | $0.0004 | **PASS** |
| **Instagram** | TxU0ZBQIHdR20dr9C | ❌ | ❌ | $0.0025 | FAIL |
| **LinkedIn** | M2FMdjRVeF1HPGFcc | N/A | N/A | $0.004 | PASS* |

---

## 詳細評価

### 1. X (Twitter) 現行 Actor

```yaml
actor_evaluation:
  actor_id: "cPYLH3QT9GyzKhB4S"
  actor_name: "patient_discovery/twitter-search"
  evaluated_at: "2026-10-09"
  use_case: "X (Twitter) データ収集"

  functional_fit:
    input_schema: "PASS"  # query, section, maxPages
    output_schema: "PASS"  # tweet_id, created_at, text, metrics
    language_filter: "PASS"  # lang:ja 演算子対応
    date_filter: "FAIL"  # since:/until: が機能しない
    pagination: "PASS"  # maxPages 1-100

  statistical_sampling:
    search_order_monotonic: "UNKNOWN"  # latest=新着順、top=人気順
    date_filter_accuracy: "FAIL"  # 日付フィルタ不可
    completeness: "UNKNOWN"  # 取得完全性不明
    reproducibility: "WARN"  # 検索結果が変動する場合あり
    duplicate_rate: "UNKNOWN"
    missing_pattern: "UNKNOWN"
    evidence_run_ids: []

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "$0.0025/件"
    test_cost: "$0.002 + 取得料"
    production_estimate: "100件 = $0.252"

  technical_constraints:
    login_required: "No"
    rate_limit: "緩い"
    execution_time: "6.1秒 (実績)"
    reliability: "高"

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開ツイートのみ"

  final_judgment:
    probability_sampling: "使用不可"  # 日付フィルタ不可のため
    completeness_for_stats: "不明"
    alternative_needed: "Yes"  # 日付必要時は新規Actorへ

  decision: "CONDITIONAL"
  rationale: "日付フィルタが機能しないため、期間指定研究には不適。日付不要の場合は使用可能。"
  recommendations:
    - "日付フィルタが必要な場合は rBaTEHzveTxZPraGv を使用"
    - "クライアント側で日付フィルタを適用する場合のみ継続"
```

---

### 2. X (Twitter) 新規 Actor

```yaml
actor_evaluation:
  actor_id: "rBaTEHzveTxZPraGv"
  actor_name: "x-posts-search"
  evaluated_at: "2026-10-09"
  use_case: "X (Twitter) データ収集（期間指定）"

  functional_fit:
    input_schema: "PASS"  # query, maxItems
    output_schema: "PASS"  # postId, postText, timestamp (Unix ms)
    language_filter: "PASS"  # lang:ja 演算子対応
    date_filter: "PASS"  # since:/until: 動作確認済み
    pagination: "PASS"  # maxItems

  statistical_sampling:
    search_order_monotonic: "PASS"  # 時系列でソート可能
    date_filter_accuracy: "PASS"  # 2026-09-01〜2026-10-01 でテスト、範囲内で動作
    completeness: "PASS"  # 期間指定で取得
    reproducibility: "PASS"  # 期間指定で安定
    duplicate_rate: "UNKNOWN"  # 要確認
    missing_pattern: "UNKNOWN"  # 要確認
    evidence_run_ids:
      - "1w8HCND8xNOY7Vurr"  # テスト実行

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "要確認"
    test_cost: "要確認"
    production_estimate: "要確認"

  technical_constraints:
    login_required: "No"
    rate_limit: "不明"
    execution_time: "不明"
    reliability: "高 (テスト成功)"

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開ツイートのみ"

  final_judgment:
    probability_sampling: "使用可能"  # 期間指定でサンプリング可能
    completeness_for_stats: "高い"  # 期間指定で取得
    alternative_needed: "No"

  decision: "PASS"
  rationale: "日付フィルタ対応、研究用途に最適。"
  recommendations:
    - "期間指定研究のデフォルトActorとして採用"
    - "課金モデルの詳細確認を推奨"
```

---

### 3. YouTube

```yaml
actor_evaluation:
  actor_id: "gJvjeCYNraSfhIaNd"
  actor_name: "danek/youtube-search"
  evaluated_at: "2026-10-09"
  use_case: "YouTube 動画データ収集"

  functional_fit:
    input_schema: "PASS"  # search_term, max_videos
    output_schema: "WARN"  # 相対日付（timestamp）
    language_filter: "PASS"  # 日本語クエリ対応
    date_filter: "FAIL"  # なし
    pagination: "PASS"  # max_videos 1-100

  statistical_sampling:
    search_order_monotonic: "UNKNOWN"
    date_filter_accuracy: "FAIL"  # 日付フィルタなし
    completeness: "WARN"  # 最新動画のみ
    reproducibility: "WARN"  # 検索結果が変動
    duplicate_rate: "WARN"  # videoId で重複排除必要
    missing_pattern: "UNKNOWN"
    evidence_run_ids: []

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "$0.0005/件"
    test_cost: "$0.00005 + 取得料"
    production_estimate: "100件 = $0.05"

  technical_constraints:
    login_required: "No"
    rate_limit: "なし"
    execution_time: "不明"
    reliability: "高"

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開動画のみ"

  final_judgment:
    probability_sampling: "使用不可"  # 日付フィルタなし
    completeness_for_stats: "低い"  # 最新のみ
    alternative_needed: "Yes"  # 日付補完に YouTube Data API 必要

  decision: "CONDITIONAL"
  rationale: "日付フィルタなし、相対日付。YouTube Data API で補完する場合のみ使用可。"
  recommendations:
    - "YouTube Data API で publishedAt を取得"
    - "既存の youtube-date-enrichment スキルを使用"
```

---

### 4. TikTok

```yaml
actor_evaluation:
  actor_id: "jQfZ1h9FrcWcliKZX"
  actor_name: "novi/tiktok-search-api"
  evaluated_at: "2026-10-09"
  use_case: "TikTok 動画データ収集"

  functional_fit:
    input_schema: "PASS"  # keyword, limit, publishTime
    output_schema: "PASS"  # aweme_id, createTime (Unix秒)
    language_filter: "PASS"  # 日本語クエリ対応
    date_filter: "PASS"  # publishTime 対応
    pagination: "PASS"  # limit 1-10000

  statistical_sampling:
    search_order_monotonic: "PASS"  # sortType で選択可能
    date_filter_accuracy: "PASS"  # publishTime 対応
    completeness: "PASS"  # 期間指定で取得
    reproducibility: "PASS"
    duplicate_rate: "WARN"  # 要確認
    missing_pattern: "UNKNOWN"
    evidence_run_ids: []

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "$0.0004/件"
    test_cost: "$0.00023 + 取得料"
    production_estimate: "100件 = $0.04"

  technical_constraints:
    login_required: "No"
    rate_limit: "なし"
    execution_time: "30秒 (100件)"
    reliability: "高"

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開動画のみ"

  final_judgment:
    probability_sampling: "使用可能"
    completeness_for_stats: "高い"
    alternative_needed: "No"

  decision: "PASS"
  rationale: "日付フィルタ対応、コスト最安、研究用途に適。"
  recommendations:
    - "研究データ収集のデフォルトActorとして採用"
```

---

### 5. Instagram

```yaml
actor_evaluation:
  actor_id: "TxU0ZBQIHdR20dr9C"
  actor_name: "patient_discovery/instagram-search-reels"
  evaluated_at: "2026-10-09"
  use_case: "Instagram Reels データ収集"

  functional_fit:
    input_schema: "PASS"  # query, maxPages
    output_schema: "PASS"  # id, caption, ig_play_count
    language_filter: "WARN"  # 日本語クエリ対応だがシャドウバン
    date_filter: "FAIL"  # なし
    pagination: "PASS"  # maxPages 1-100

  statistical_sampling:
    search_order_monotonic: "FAIL"  # ソート機能なし
    date_filter_accuracy: "FAIL"  # 日付フィルタなし
    completeness: "FAIL"  # シャドウバンでデータ不安定
    reproducibility: "FAIL"  # 検索結果が変動
    duplicate_rate: "UNKNOWN"
    missing_pattern: "UNKNOWN"
    evidence_run_ids: []

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "$0.0025/件"
    test_cost: "$0.002 + 取得料"
    production_estimate: "100件 = $0.252"

  technical_constraints:
    login_required: "No"
    rate_limit: "不明"
    execution_time: "不明"
    reliability: "低"  # シャドウバン影響

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開投稿のみ"

  final_judgment:
    probability_sampling: "使用不可"
    completeness_for_stats: "低い"
    alternative_needed: "Yes"  # 代替手段検討必要

  decision: "FAIL"
  rationale: "検索順序不明、日付フィルタなし、シャドウバンでデータ不安定。研究用途に不適。"
  recommendations:
    - "研究データ収集から除外"
    - "別Actorの検討またはデータソース変更を検討"
```

---

### 6. LinkedIn

```yaml
actor_evaluation:
  actor_id: "M2FMdjRVeF1HPGFcc"
  actor_name: "harvestapi/linkedin-profile-search"
  evaluated_at: "2026-10-09"
  use_case: "研究者マッピング"

  functional_fit:
    input_schema: "PASS"  # searchQuery, maxItems
    output_schema: "PASS"  # linkedinUrl, experience
    language_filter: "PASS"  # 英語検索推奨
    date_filter: "N/A"  # プロフィール検索
    pagination: "PASS"  # maxItems

  statistical_sampling:
    search_order_monotonic: "N/A"
    date_filter_accuracy: "N/A"
    completeness: "N/A"
    reproducibility: "PASS"  # プロフィールは安定
    duplicate_rate: "N/A"
    missing_pattern: "N/A"
    evidence_run_ids: []

  cost_analysis:
    pricing_model: "PAY_PER_EVENT"
    unit_cost: "$0.004/件 + $0.10/ページ"
    test_cost: "$0.18 (20件)"
    production_estimate: "100件 = $0.50"

  technical_constraints:
    login_required: "No"
    rate_limit: "寛容"
    execution_time: "20.5秒 (実績)"
    reliability: "高"

  legal_compliance:
    tos_compliant: "Yes"
    redistribution: "制限あり"
    privacy: "公開プロフィールのみ"

  final_judgment:
    probability_sampling: "N/A"
    completeness_for_stats: "N/A"
    alternative_needed: "No"

  decision: "PASS"
  rationale: "研究者マッピング用途に適。投稿データではないため日付フィルタ不要。"
  recommendations:
    - "研究者マッピング用途として継続"
```

---

## 推奨アクション

| Actor | 推奨 | 理由 |
|-------|------|------|
| **X 新規 (rBaTEHzveTxZPraGv)** | ✅ 採用 | 日付フィルタ対応、研究用途に最適 |
| **X 現行 (cPYLH3QT9GyzKhB4S)** | ⚠️ 条件付き継続 | 日付必要時は新規Actorに切替 |
| **YouTube (gJvjeCYNraSfhIaNd)** | ⚠️ 条件付き継続 | YouTube Data API で日付補完 |
| **TikTok (jQfZ1h9FrcWcliKZX)** | ✅ 継続 | 日付フィルタ対応、コスト最安 |
| **Instagram (TxU0ZBQIHdR20dr9C)** | ❌ 不採用 | シャドウバンでデータ不安定 |
| **LinkedIn (M2FMdjRVeF1HPGFcc)** | ✅ 継続 | 研究者マッピング用途に適 |

---

## 最終判断

| # | 判断項目 | 結論 |
|:-:|----------|------|
| 1 | 確率的サンプリング適性 | X新規、TikTok は使用可能 |
| 2 | 取得完全性 | X新規、TikTok は統計的推定に足りる |
| 3 | 代替手段の要否 | Instagram は代替検討が必要 |

---

## 次のステップ

1. X新規Actor (rBaTEHzveTxZPraGv) の課金モデル確認
2. 全13化合物のXデータ収集計画策定
3. Instagram の代替手段検討
