# キーワードカバレッジ拡張計画書

| 項目 | 内容 |
|------|------|
| **計画ID** | EXP-20261002 |
| **目的** | 既存 CBX/H4CBH/HHBD に加え、主要カンナビノイド7化合物のトレンドデータを収集し、カバレッジを充足させる |
| **作成日** | 2026-10-02 |
| **対象キーワード** | CBD, THC, CBG, HHC, THC-O, THCH, THCV |
| **ステータス** | PLANNED |

---

## 1. 対象キーワード一覧

| # | キーワード | 化合物カテゴリ | 既存カバレッジ | 優先度 |
|---|-----------|---------------|:--------------:|:------:|
| 1 | **CBD** | Major Phytocannabinoid | ❌ 未収集 | 高 |
| 2 | **THC** | Major Phytocannabinoid | ❌ 未収集 | 高 |
| 3 | **CBG** | Minor Phytocannabinoid | ❌ 未収集 | 高 |
| 4 | **HHC** | Semi-Synthetic Cannabinoid | ❌ 未収集 | 高 |
| 5 | **THCV** | Minor Phytocannabinoid | ❌ 未収集 | 中 |
| 6 | **THC-O** | Semi-Synthetic Cannabinoid | ❌ 未収集 | 中 |
| 7 | **THCH** | Minor Phytocannabinoid | ❌ 未収集 | 中 |

---

## 2. 既存カバレッジとの対比

### カバレッジ済み（本リポジトリ）

| キーワード | Google Trends | X | YouTube | GSC |
|-----------|:------------:|:-:|:-------:|:---:|
| CBX | ✅ | ✅ | ✅ | ✅ |
| CBX リキッド | ✅ | ✅ | ✅ | ✅ |
| H4CBH | ✅ | ❌ | ❌ | ✅ |
| HHBD | ✅ | ❌ | ❌ | ❌ |

### 本計画で追加

| キーワード | Google Trends | X | YouTube | GSC |
|-----------|:------------:|:-:|:-------:|:---:|
| CBD | 📋 計画 | 📋 計画 | 📋 計画 | 参考 |
| THC | 📋 計画 | 📋 計画 | 📋 計画 | 参考 |
| CBG | 📋 計画 | 📋 計画 | 📋 計画 | — |
| HHC | 📋 計画 | 📋 計画 | 📋 計画 | — |
| THCV | 📋 計画 | 📋 計画 | 📋 計画 | — |
| THC-O | 📋 計画 | 📋 計画 | 📋 計画 | — |
| THCH | 📋 計画 | 📋 計画 | 📋 計画 | ✅ |

---

## 3. 収集計画

### 3.1 Google Trends

**保存先:** `datasets/cannabinoid-multi-trends/data/raw/google_trends/`

| キーワード | キーワード群 | 地域 | 期間 |
|-----------|-------------|------|------|
| CBD | CBD, CBD オイル, CBD リキッド | JP | today 12-m |
| THC | THC, THC オイル | JP | today 12-m |
| CBG | CBG | JP | today 12-m |
| HHC | HHC, HHC オイル | JP | today 12-m |
| THCV | THCV | JP | today 12-m |
| THC-O | THC-O | JP | today 12-m |
| THCH | THCH | JP | today 12-m |

**比較セット（最大5語）:**

```
セットA: CBD, THC, CBG, HHC, THCV
セットB: THC-O, THCH, CBD オイル, THC オイル, HHC オイル
```

**関連クエリ:** 各キーワードで related_queries を収集

### 3.2 X (Twitter)

**保存先:** `datasets/cannabinoid-multi-trends/data/raw/x/`

| キーワード | 期間 | section | maxPages | コスト目安 |
|-----------|------|---------|----------|-----------|
| CBD | 2026-09-01 〜 2026-10-01 | latest | 3 | $0.152 |
| THC | 2026-09-01 〜 2026-10-01 | latest | 3 | $0.152 |
| CBG | 2026-09-01 〜 2026-10-01 | latest | 2 | $0.077 |
| HHC | 2026-09-01 〜 2026-10-01 | latest | 2 | $0.077 |
| THCV | 2026-09-01 〜 2026-10-01 | latest | 2 | $0.077 |
| THC-O | 2026-09-01 〜 2026-10-01 | latest | 2 | $0.052 |
| THCH | 2026-09-01 〜 2026-10-01 | latest | 2 | $0.052 |

**合計:** ~240件 / ~$0.64

### 3.3 YouTube

**保存先:** `datasets/cannabinoid-multi-trends/data/raw/youtube/`

| キーワード | max_videos | コスト目安 |
|-----------|-----------|-----------|
| CBD | 100 | $0.050 |
| THC | 100 | $0.050 |
| CBG | 50 | $0.025 |
| HHC | 50 | $0.025 |
| THCV | 50 | $0.025 |
| CBD オイル | 50 | $0.025 |
| THC オイル | 50 | $0.025 |

**合計:** 450件 / ~$0.23

---

## 4. 保存先ディレクトリ

```
datasets/cannabinoid-multi-trends/
├── README.md
├── methodology.md
├── data/
│   ├── raw/
│   │   ├── google_trends/
│   │   │   ├── {run-id}-cbd/
│   │   │   ├── {run-id}-thc/
│   │   │   ├── {run-id}-cbg/
│   │   │   ├── {run-id}-hhc/
│   │   │   ├── {run-id}-thcv/
│   │   │   ├── {run-id}-thc-o/
│   │   │   └── {run-id}-thch/
│   │   ├── x/
│   │   │   └── {run-id}-{keyword}/
│   │   └── youtube/
│   │       └── {run-id}-{keyword}/
│   └── processed/
├── metadata/
└── analysis/
```

---

## 5. コスト見積

| ソース | コスト |
|--------|--------|
| Google Trends | **無料** |
| X (Twitter) | **$0.64** |
| YouTube | **$0.23** |
| **合計** | **~$0.87** |

---

## 6. 実行ステップ

### Step 1: プラン準備

- [ ] `datasets/cannabinoid-multi-trends/` ディレクトリ作成
- [ ] `README.md` 作成
- [ ] `methodology.md` 作成

### Step 2: Google Trends 収集（無料）

- [ ] CBD（単独 + オイル/リキッド）
- [ ] THC（単独 + オイル）
- [ ] CBG（単独）
- [ ] HHC（単独 + オイル）
- [ ] THCV（単独）
- [ ] THC-O（単独）
- [ ] THCH（単独）
- [ ] 比較セットA（CBD, THC, CBG, HHC, THCV）
- [ ] 比較セットB（THC-O, THCH, CBD オイル, THC オイル, HHC オイル）

### Step 3: X (Twitter) 収集（~$0.64）

- [ ] CBD
- [ ] THC
- [ ] CBG
- [ ] HHC
- [ ] THCV
- [ ] THC-O
- [ ] THCH

### Step 4: YouTube 収集（~$0.23）

- [ ] CBD（100件）
- [ ] THC（100件）
- [ ] CBG（50件）
- [ ] HHC（50件）
- [ ] THCV（50件）
- [ ] CBD オイル（50件）
- [ ] THC オイル（50件）

### Step 5: データ処理

- [ ] 重複排除（X: tweet_id, YouTube: videoId）
- [ ] 分類（SKOS Concept ID）
- [ ] 集計・サマリー作成

### Step 6: 品質チェック

- [ ] Google Trends スコア範囲確認（0-100）
- [ ] X/YouTube 件数確認
- [ ] キーワード含有率確認
- [ ] コスト実績確認

### Step 7: ドキュメント

- [ ] README.md 更新
- [ ] methodology.md 更新
- [ ] data-dictionary.md 更新（必要に応じて）

---

## 7. SKOS 分類マッピング

| キーワード | 化合物 Concept ID | 備考 |
|-----------|------------------|------|
| CBD | `compound_cbd` | Major Phytocannabinoid |
| THC | `compound_thc` | Major Phytocannabinoid |
| CBG | `compound_cbg` | Minor Phytocannabinoid |
| HHC | `compound_hhc` | Semi-Synthetic |
| THCV | `compound_thcv` | Minor Phytocannabinoid |
| THC-O | `compound_thc_o` | Semi-Synthetic |
| THCH | `compound_thch` | Minor Phytocannabinoid |

---

## 8. 成果物

| 成果物 | 場所 |
|--------|------|
| Google Trends データ | `datasets/cannabinoid-multi-trends/data/raw/google_trends/` |
| X データ | `datasets/cannabinoid-multi-trends/data/raw/x/` |
| YouTube データ | `datasets/cannabinoid-multi-trends/data/raw/youtube/` |
| サマリー | `datasets/cannabinoid-multi-trends/README.md` |
| 方法論 | `datasets/cannabinoid-multi-trends/methodology.md` |

---

## 9. 注意事項

| 項目 | 内容 |
|------|------|
| **多義語** | CBD, THC は高頻度検索語。コンテキスト分析が必要 |
| **レート制限** | Google Trends 429 エラー時は 2-5 分待機 |
| **シャドウバン** | X は敏感キーワード（THC 等）で 0 件になる可能性あり |
| **コスト管理** | 各ソースの usageTotalUsd を都度確認 |
| **COI 開示** | 研究報告時は商業関係を明示 |
| **比較可能性** | Google Trends は相対指数、X/YouTube は絶対件数。直接比較不可 |

---

## 10. ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | — |
| COMPLETED | — |

---

## 関連ドキュメント

- 研究計画書: `docs/plans/`
- 技術標準: `docs/specs/standards-compliance-implementation-plan.md`
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
