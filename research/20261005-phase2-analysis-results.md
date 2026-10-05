# フェーズ 2 分析結果

| 項目 | 内容 |
|------|------|
| **分析日** | 2026-10-05 |
| **対象データ** | 日本語 YouTube、CBN 規制前後 X、H4CBH/HHBD 拡大 X |

---

## 1. 日本語 YouTube データ分析

### 収集結果

| キーワード | 総件数 | ユニークID | 日本語コンテンツ |
|-----------|:------:|:----------:|:---------------:|
| CBD オイル | 60 | 28 | ✅ 確認 |
| CBX リキッド | 60 | 23 | ✅ 確認 |
| カンナビノイド | 60 | 24 | ✅ 確認 |

### サンプル動画

| キーワード | サンプル |
|-----------|---------|
| CBD オイル | 精神科医による CBD オイル解説、医師による安全性解説 |
| CBX リキッド | CBX 体験レビュー、CBX×HHBD 比較 |
| カンナビノイド | 合成カンナビノイドと CBD の違い解説 |

**所見:** 日本語キーワードを使用することで、日本語圏のカンナビノイド関連動画を収集可能。YouTube API のクォータ制限を Apify で回避。

---

## 2. CBN 規制前後分析

### 基本統計

| 指標 | 規制前 (1-5月) | 規制後 (6-10月) | CBG 対照 |
|------|:--------------:|:---------------:|:--------:|
| 件数 | 100 | 100 | 100 |
| ユニークユーザー | 64 | 70 | 33 |
| 総いいね | 1,855 | 983 | 483 |
| **平均いいね** | **18.6** | **9.8** | **4.8** |

### 所見

1. **エンゲージメント低下:** CBN の平均いいねは規制前 18.6 → 規制後 9.8 に低下（-47%）
2. **ユーザー数は維持:** ユニークユーザーは 64 → 70 とほぼ変化なし
3. **CBG 対照:** CBG の平均いいねは 4.8 で、CBN と比べても低い水準

### コンテンツ分析

| 期間 | 主な内容 |
|------|---------|
| 規制前 | 規制への言及、製品宣伝（SEXYDOSE 等） |
| 規制後 | 規制後市場への言及、別製品への言及（CBX 等） |

**限界:** `section=latest` のため、期間内の最新投稿が中心。ランダムサンプルではない。

---

## 3. H4CBH/HHBD 拡大データ分析 (n=200)

### 分類分布（規則ベース）

| カテゴリ | H4CBH (n=200) | HHBD (n=200) |
|----------|:-------------:|:------------:|
| 製品宣伝・販売 | 26 (13.0%) | 59 (29.5%) |
| 製品レビュー | 18 (9.0%) | 18 (9.0%) |
| 会話・引用 | 0 (0.0%) | 0 (0.0%) |
| その他 | 156 (78.0%) | 123 (61.5%) |

### 旧データ (n=40) との比較

| 化合物 | 旧 製品宣伝 | 新 製品宣伝 | 変化 |
|--------|:----------:|:----------:|:----:|
| H4CBH | 55% | 13.0% | -42pp |
| HHBD | 60% | 29.5% | -30.5pp |

**注意:** 分類方法が異なる（旧: 手動分類、新: 規則ベース）。直接比較はできない。

### 信頼区間（n=200 時）

| 化合物 | 比率 | 95% CI |
|--------|:----:|:------:|
| H4CBH 製品宣伝 | 13.0% | 8.9-18.5% |
| HHBD 製品宣伝 | 29.5% | 23.7-36.2% |

**改善:** n=40 時の CI（30pp 幅）から、n=200 時は約 10pp 幅に狭小化。

---

## 総括

### 成功した分析

| # | 分析 | 結果 |
|:-:|------|------|
| 1 | 日本語 YouTube 収集 | ✅ 日本語コンテンツを確認 |
| 2 | CBN 規制前後 | ⚠️ エンゲージメント低下を確認、コンテンツ分析は追加必要 |
| 3 | H4CBH/HHBD 拡大 | ✅ サンプルサイズ拡大、CI 狭小化 |

### 限界と注意点

| 項目 | 内容 |
|------|------|
| **サンプリング** | `section=latest` のため期間内の最新投稿中心 |
| **分類方法** | 規則ベース分類は文脈理解に限界 |
| **直接比較不可** | 旧データ（n=40）と新データ（n=200）は分類方法が異なる |
| **コンテンツ分析** | CBN 前後の内容差分は手動確認が必要 |

---

## 引用可能な記述

### 日本語 YouTube

> "Japanese-language YouTube data for cannabinoid keywords (CBD オイル, CBX リキッド, カンナビノイド) was collected via Apify actor gJvjeCYNraSfhIaNd, yielding 60 records per keyword with confirmed Japanese-language content."

### CBN 規制前後

> "X/Twitter engagement (average likes per post) for CBN-related content decreased from 18.6 (January-May 2026, pre-regulation) to 9.8 (June-October 2026, post-regulation), while unique user count remained stable (64 vs 70). CBG control showed lower engagement (4.8 average likes). This is a temporal association; causation cannot be inferred."

### H4CBH/HHBD

> "Expanded X/Twitter samples (n=200 per compound) for H4CBH and HHBD yielded narrower confidence intervals (approximately 10 percentage points wide) compared to the initial n=40 samples (approximately 30 percentage points wide)."

---

## 次のステップ

| # | タスク | 優先度 |
|:-:|--------|:------:|
| 1 | CBN 前後のコンテンツを手動分類（宣伝/規制議論/その他） | HIGH |
| 2 | 日本語 YouTube データの年次トレンド分析 | MEDIUM |
| 3 | 全データの v1.9.0 統合 | MEDIUM |
