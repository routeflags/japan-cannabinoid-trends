---
name: apify-actor-validation
description: |
  Apify Actor の選定基準をバリデーションするスキル。
  「Actor選定」「Actor検証」「actor validation」「どのActorを使うべき」
  「Actorの条件を確認」などで使う。
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

### 3. コスト効率

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **課金モデル** | PAY_PER_EVENT / FLAT_RATE | 高 |
| **単価** | 1件あたりのコスト | 高 |
| **最低課金** | 最小課金額（テストコスト） | 中 |
| **予算適合** | 研究予算内に収まるか | 高 |

### 4. 技術的制約

| 項目 | 確認内容 | 重要度 |
|------|---------|:------:|
| **Login要否** | Cookie/ログインが必要か | 高 |
| **レート制限** | APIレート制限の有無 | 中 |
| **実行時間** | 収集にかかる時間 | 中 |
| **信頼性** | 実行成功率 | 高 |

### 5. 法的・規制

| 項目 | 確認内容 | 重要度 |
|------|---------|:------: |
| **利用規約** | プラットフォームTOSに準拠しているか | 高 |
| **再配布権** | 収集データの再配布が可能か | 高 |
| **プライバシー** | 個人情報の取り扱い | 高 |

---

## バリデーション判定基準

### PASS（採用可能）

```
✅ 必須項目を全て満たす
✅ コストが研究予算内
✅ 法的リスクが低い
✅ データ品質が研究目的に足りる
```

### CONDITIONAL（条件付き採用）

```
⚠️ 制約があるが代替手段で補完可能
⚠️ コストがやや高いが必要なデータが取れる
⚠️ 技術的制約があるが回避策がある
```

### FAIL（不採用）

```
❌ 必須機能がない（言語フィルタなし等）
❌ コストが予算を大幅に超過
❌ 法的リスクが高い
❌ データ品質が研究目的に足りない
❌ 実行成功率が低い
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
| `apify-youtube-search` | YouTube 検索 |
| `apify-tiktok-search` | TikTok 検索 |
| `apify-instagram-search` | Instagram 検索 |
| `apify-linkedin-search` | LinkedIn 検索 |
