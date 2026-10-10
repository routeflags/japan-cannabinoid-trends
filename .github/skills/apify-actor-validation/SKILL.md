---
name: apify-actor-validation
description: |
  Apify Actor の選定基準をバリデーションするスキル。
  「Actor選定」「Actor検証」「actor validation」「どのActorを使うべき」
  「Actorの条件を確認」「Actorの再現性検証」「サンプリング設計」などで使う。
---

# Apify Actor 選定基準バリデーションスキル

Apify Actor を研究データ収集に使用する前に、選定基準を体系的にバリデーションするスキル。

---

## トリガー

- 「Actor選定」
- 「Actor検証」
- 「どのActorを使うべき」
- 「Actorの条件を確認」
- 「actor validation」
- 「収集に適したActorか確認」
- 「Actorの再現性を検証」
- 「サンプリングに使えるか」

---

## 重要な原則

### 研究データ収集の基本原則

| 原則 | 内容 |
|------|------|
| **Rawデータ不変** | 既存のRawデータを変更しない |
| **0件≠欠測** | 取得できなかった投稿を0件と判断しない |
| **推測禁止** | 推測を実測結果として報告しない |
| **事前承認** | API費用が発生する実行は事前に見積もりと承認を得る |
| **証拠保存** | すべての判定にRun IDを紐付ける |

---

## バリデーション チェックリスト

### 1. 機能的適合性

| 項目 | 確認内容 | 必須 |
|------|---------|:----:|
| **入力スキーマ** | 必須パラメータが研究要件を満たすか | ✅ |
| **出力スキーマ** | 必要なフィールドが含まれるか | ✅ |
| **フィルタ機能** | 言語フィルタがあるか | ⚠️ |
| **日付フィルタ** | since:/until: 等の期間指定が可能か | ⚠️ |
| **ページング** | 大量データ取得に対応しているか | ✅ |
| **上限** | 取得件数の上限は適切か | ✅ |

### 2. データ品質

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **日本語対応** | 日本語コンテンツを取得できるか | 高 |
| **データ完全性** | メタデータが充実しているか | 高 |
| **一貫性** | 同一クエリで安定した結果が返るか | 中 |
| **重複処理** | 重複データの排除機能があるか | 中 |

### 3. 統計的サンプリング適性

研究データ収集では、Actor の検挙・出力特性が統計的推定の前提条件を満たすか検証する。

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **検索順序** | 検索結果が時系列で単調減少しているか | 高 |
| **期間指定の正確性** | 指定期間外の投稿が混入しないか | 高 |
| **網羅性** | 指定期間の投稿を網羅的に取得できるか | 高 |
| **再現性** | 同一クエリで同じ結果が返るか | 高 |
| **重複率** | ページングによる重複の程度 | 中 |
| **欠測パターン** | 取得できない投稿の特徴 | 中 |

### 4. コスト効率

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **課金モデル** | PAY_PER_EVENT / FLAT_RATE | 高 |
| **単価** | 1件あたりのコスト | 高 |
| **最低課金** | 最小課金額（テストコスト） | 中 |
| **予算適合** | 研究予算内に収まるか | 高 |

### 5. 技術的制約

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **Login要否** | Cookie/ログインが必要か | 高 |
| **レート制限** | APIレート制限の有無 | 中 |
| **実行時間** | 収集にかかる時間 | 中 |
| **信頼性** | 実行成功率 | 高 |

### 6. 法的・規制

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **利用規約** | プラットフォームTOSに準拠しているか | 高 |
| **再配布権** | 収集データの再配布が可能か | 高 |
| **プライバシー** | 個人情報の取り扱い | 高 |

---

## 検証フェーズ

### Phase 1: 既存データ監査

API費用を発生させず、既存データのみで検証する。

| # | 検証項目 | 方法 |
|:-:|----------|------|
| 1 | 既存Rawデータの件数 | データセットの件数確認 |
| 2 | 検索クエリの記録 | Run Metadata からクエリ抽出 |
| 3 | 検索順序の検証 | 投稿日時が単調減少しているか確認 |
| 4 | 重複率 | 投稿IDの重複を計算 |
| 5 | 期間外混入 | 指定期間外の投稿がないか確認 |
| 6 | 仕様照合 | 公開仕様と実際の出力を比較 |

### Phase 2: 追加PoC（事前承認が必要）

既存データで判定できない場合に実施する。

| # | 検証項目 | コスト |
|:-:|----------|--------|
| 1 | 同一クエリの再実行 | 発生 |
| 2 | maxPages=1 vs maxPages=3 | 発生 |
| 3 | 過去の日付範囲指定 | 発生 |
| 4 | 時刻指定の動作確認 | 発生 |

**注意:** 追加API費用が発生する実行は、事前に件数と費用を見積もり、ユーザーの承認を得る。

### Phase 3: 報告

表形式で以下を報告する。

| 項目 | 内容 |
|------|------|
| 検証項目 | 何を検証したか |
| 公式仕様 | 公開されている仕様 |
| 実測結果 | 実際に確認された結果 |
| 判定 | PASS / FAIL / UNKNOWN |
| 証拠 | Run ID |
| 影響 | 研究設計への影響 |

---

## 最終判断基準

Actor の研究利用可否を判断する際、以下の3点を結論として示す。

| # | 判断項目 | 判定基準 |
|:-:|----------|----------|
| 1 | **確率的サンプリング適性** | 指定時間窓からの確率的サンプリングに使用できるか |
| 2 | **取得完全性** | 月次投稿量を統計的に推定できるだけの取得完全性があるか |
| 3 | **代替手段の要否** | 使用できない場合、Actor変更または研究指標の変更が必要か |

---

## バリデーション判定基準

### PASS（採用可能）

```
✅ 必須項目を全て満たす
✅ コストが研究予算内
✅ 法的リスクが低い
✅ データ品質が研究目的に足りる
✅ 統計的サンプリングの前提条件を満たす
```

### CONDITIONAL（条件付き採用）

```
⚠️ 制約があるが代替手段で補完可能
⚠️ コストがやや高いが必要なデータが取れる
⚠️ 技術的制約があるが回避策がある
⚠️ 日付フィルタが一部のみ動作（クライアント側フィルタで補完）
```

### FAIL（不採用）

```
❌ 必須機能がない（言語フィルタなし等）
❌ コストが予算を大幅に超過
❌ 法的リスクが高い
❌ データ品質が研究目的に足りない
❌ 実行成功率が低い
❌ 統計的推定の前提条件を満たさない
```

---

## 出力フォーマット

### Actor 評価レポート

```markdown
## Actor 評価レポート

### 基本情報
| 項目 | 内容 |
|------|------|
| Actor ID | xxxxxxxx |
| 名前 | xxx/xxxxx |
| 評価日 | YYYY-MM-DD |
| 評価者 | research-agent |

### 機能的適合性
| 項目 | 結果 | 備考 |
|------|:----:|------|
| 入力スキーマ | ✅/⚠️/❌ | |
| 出力スキーマ | ✅/⚠️/❌ | |
| 言語フィルタ | ✅/⚠️/❌ | |
| 日付フィルタ | ✅/⚠️/❌ | |

### 統計的サンプリング適性
| 項目 | 結果 | 証拠 |
|------|:----:|------|
| 検索順序（単調減少） | ✅/⚠️/❌/UNKNOWN | Run ID: |
| 期間指定の正確性 | ✅/⚠️/❌/UNKNOWN | Run ID: |
| 取得完全性 | ✅/⚠️/❌/UNKNOWN | Run ID: |
| 再現性 | ✅/⚠️/❌/UNKNOWN | Run ID: |

### コスト分析
| 項目 | 値 |
|------|-----|
| 課金モデル | |
| 単価 | |
| テストコスト | |
| 100件収集コスト | |

### 判定
**結果:** PASS / CONDITIONAL / FAIL

**理由:**
- ...

**推奨事項:**
- ...
```

---

## 実行手順

### Step 1: Actor 情報取得

```bash
# Actor 詳細を取得
# MCP経由
fetch-actor-details {"actor": "ACTOR_ID"}

# API直叩き
source .env.d/apify.env
curl -s "https://api.apify.com/v2/acts/ACTOR_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.data | {id, name, title, pricing}'
```

### Step 2: 入出力スキーマ確認

```bash
# inputSchema と outputSchema を確認
curl -s "https://api.apify.com/v2/acts/ACTOR_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.data.inputSchema'
```

### Step 3: テスト実行

```bash
# 最小コストでテスト
curl -s -X POST "https://api.apify.com/v2/acts/ACTOR_ID/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"<required_param>": "<test_value>"}'
```

### Step 4: 出力検証

```bash
# 収集データの品質を確認
curl -s "https://api.apify.com/v2/datasets/DATASET_ID/items?clean=true&format=json&limit=5" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.[0]'
```

### Step 5: 判定・記録

評価結果を `research/apify/actor-evaluations.md` に記録。

**重要:** Actor 検証を実施した場合、必ず `research/apify/actor-evaluations.md` を更新すること。

更新対象:
- 評価マトリクス（A. 機能的適合性）
- スコア集計
- 検証結果
- 詳細評価
- 推奨アクション
- 検証が必要な項目
- 更新履歴

---

## よくある問題と回避策

| 問題 | 回避策 |
|------|--------|
| 言語フィルタなし | 日本語クエリを使用 |
| 日付フィルタが機能しない | クライアント側でフィルタ |
| コスト超過 | maxItems/maxPages を制限 |
| 0件が返る | クエリを調整、別Actorを検討 |
| レート制限 | 実行間隔を空ける |

---

## 評価記録テンプレート

```yaml
actor_evaluation:
  actor_id: ""
  actor_name: ""
  evaluated_at: ""
  use_case: ""
  
  functional_fit:
    input_schema: ""
    output_schema: ""
    language_filter: ""
    date_filter: ""
    pagination: ""
  
  statistical_sampling:
    search_order_monotonic: ""  # 検索順序が単調減少するか
    date_filter_accuracy: ""    # 期間指定が正確か
    completeness: ""            # 取得完全性
    reproducibility: ""         # 再現性
    duplicate_rate: ""          # 重複率
    missing_pattern: ""         # 欠測パターン
    evidence_run_ids: []        # 証拠となるRun ID
  
  cost_analysis:
    pricing_model: ""
    unit_cost: ""
    test_cost: ""
    production_estimate: ""
  
  technical_constraints:
    login_required: ""
    rate_limit: ""
    execution_time: ""
  
  legal_compliance:
    tos_compliant: ""
    redistribution: ""
    privacy: ""
  
  final_judgment:
    probability_sampling: ""    # 確率的サンプリング適性
    completeness_for_stats: ""  # 統計的推定に必要な取得完全性
    alternative_needed: ""      # 代替手段の要否
  
  decision: ""
  rationale: ""
  recommendations: []
```

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `apify-mcp` | MCP 起動・認証 |
| `apify-x-search` | X (Twitter) 検索 |
| `apify-x-posts-search` | X (Twitter) 検索（日付フィルタ対応） |
| `apify-youtube-search` | YouTube 検索 |
| `apify-tiktok-search` | TikTok 検索 |
| `apify-instagram-search` | Instagram 検索 |
| `apify-linkedin-search` | LinkedIn 検索 |
