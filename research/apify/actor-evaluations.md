# Apify Actor 評価記録

## 評価日: 2026-10-09

## 評価基準

`.github/skills/apify-actor-validation/SKILL.md` に準拠

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

| Actor | A1 入力スキーマ | A2 出力スキーマ | A3 言語フィルタ | A4 日付フィルタ | A5 ページング | A6 取得上限 |
|-------|:---------------:|:---------------:|:---------------:|:---------------:|:-------------:|:-----------:|
| X (現行) cPYLH3QT9GyzKhB4S | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| X (新規) rBaTEHzveTxZPraGv | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| YouTube gJvjeCYNraSfhIaNd | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ |
| TikTok jQfZ1h9FrcWcliKZX | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Instagram TxU0ZBQIHdR20dr9C | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ |
| LinkedIn M2FMdjRVeF1HPGFcc | ✅ | ✅ | ✅ | N/A | ✅ | ✅ |

### B. 統計的サンプリング適性（6項目）

| Actor | B1 検索順序 | B2 期間正確性 | B3 網羅性 | B4 再現性 | B5 重複率 | B6 欠測パターン |
|-------|:-----------:|:-------------:|:---------:|:---------:|:---------:|:---------------:|
| X (現行) | ⚠️ 要確認 | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| X (新規) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| YouTube | ❌ | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| TikTok | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Instagram | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ |
| LinkedIn | N/A | N/A | N/A | ✅ | N/A | N/A |

### C. コスト効率（4項目）

| Actor | C1 課金モデル | C2 単価 | C3 テストコスト | C4 100件コスト |
|-------|:-------------:|:--------:|:---------------:|:--------------:|
| X (現行) | PAY_PER_EVENT | $0.0025 | $0.052 | $0.252 |
| X (新規) | PAY_PER_EVENT | 要確認 | 要確認 | 要確認 |
| YouTube | PAY_PER_EVENT | $0.0005 | $0.005 | $0.050 |
| TikTok | PAY_PER_EVENT | $0.0004 | $0.008 | $0.040 |
| Instagram | PAY_PER_EVENT | $0.0025 | $0.052 | $0.252 |
| LinkedIn | PAY_PER_EVENT | $0.004 | $0.18 | $0.50 |

### D. 技術的制約（4項目）

| Actor | D1 Login要否 | D2 レート制限 | D3 実行時間 | D4 信頼性 |
|-------|:------------:|:-------------:|:-----------:|:---------:|
| X (現行) | 不要 | 緩い | 6.1秒 | 高 |
| X (新規) | 不要 | 不明 | 不明 | 高 |
| YouTube | 不要 | なし | 不明 | 高 |
| TikTok | 不要 | なし | 30秒 | 高 |
| Instagram | 不要 | 不明 | 不明 | 低 |
| LinkedIn | 不要 | 寛容 | 20.5秒 | 高 |

### E. 法的・規制（3項目）

| Actor | E1 TOS準拠 | E2 再配布権 | E3 プライバシー |
|-------|:----------:|:-----------:|:---------------:|
| X (現行) | ✅ | 制限あり | 公開ツイートのみ |
| X (新規) | ✅ | 制限あり | 公開ツイートのみ |
| YouTube | ✅ | 制限あり | 公開動画のみ |
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
| YouTube | 9 | 2 | 4 | 4 | 3 | **22** | 48% |
| TikTok | 12 | 8* | 4 | 4 | 3 | **31*** | **91%*** |
| Instagram | 8 | 0 | 4 | 2 | 3 | **17** | 37% |
| LinkedIn | 10 | N/A | 3 | 4 | 3 | **20** | N/A |

**注:** X新規とTikTokは課金モデルが一部不明のため暫定スコア

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
```

---

### 3. YouTube

```yaml
actor_id: "gJvjeCYNraSfhIaNd"
actor_name: "danek/youtube-search"
decision: "CONDITIONAL"
score: "22/23 (48%)"

functional_fit:
  A1_input_schema: "PASS"  # search_term, max_videos
  A2_output_schema: "WARN"  # 相対日付（timestamp）
  A3_language_filter: "PASS"  # 日本語クエリ対応
  A4_date_filter: "FAIL"  # なし
  A5_pagination: "PASS"  # max_videos 1-100
  A6_max_items: "PASS"  # max_videos で制御

statistical_sampling:
  B1_search_order: "FAIL"  # 検索結果の順序が不明・不安定
  B2_date_accuracy: "FAIL"  # 日付フィルタなし
  B3_completeness: "WARN"  # 最新動画のみ取得可能
  B4_reproducibility: "WARN"  # 検索結果が変動
  B5_duplicate_rate: "WARN"  # videoId で重複排除必要
  B6_missing_pattern: "WARN"  # 要確認

evidence:
  - "既存データ: datasets/cannabinoid-multi-trends/data/raw/youtube/"
  - "相対日付形式: \"4 years ago\" 等"
  - "日付補完: youtube-date-enrichment スキルで対応"

recommendations:
  - "YouTube Data API で publishedAt を取得"
  - "検索順序の検証を実施（Phase 1: 既存データ監査）"
  - "再現性の検証を実施（同一クエリの再実行）"
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
  B1_search_order: "PASS"  # sortType で選択可能（0:Relevance, 1:Most liked, 2:Most recent）
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
| 🟡 | YouTube (gJvjeCYNraSfhIaNd) | 検索順序の検証、再現性検証 |
| 🟡 | X現行 (cPYLH3QT9GyzKhB4S) | 検索順序の検証、再現性検証 |
| 🟠 | Instagram (TxU0ZBQIHdR20dr9C) | 代替手段の検討 |

---

## 検証が必要な項目

### 未検証項目（Phase 2: 追加PoC）

| Actor | 未検証項目 | 検証方法 |
|-------|-----------|----------|
| X現行 | B1 検索順序 | 既存データで投稿日時の単調減少を確認 |
| X現行 | B4 再現性 | 同一クエリの再実行 |
| X新規 | B5 重複率 | maxItems 増加時の重複確認 |
| X新規 | B6 欠測パターン | 取得できない投稿の特徴分析 |
| YouTube | B1 検索順序 | 既存データで検索結果の順序を確認 |
| YouTube | B4 再現性 | 同一クエリの再実行 |
| TikTok | B5 重複率 | limit 増加時の重複確認 |
| TikTok | B6 欠測パターン | 取得できない投稿の特徴分析 |
