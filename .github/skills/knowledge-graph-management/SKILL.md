---
name: knowledge-graph-management
description: |
  知識グラフと project.json の管理スキル。
  「知識グラフの更新」「project.json の編集」「ノード追加」「関係追加」
  「規制情報の構造化」「ナレッジグラフの管理」などで使う。
---

# Knowledge Graph Management スキル

知識グラフ（`metadata/taxonomy/*.json`）と `project.json` を体系的に管理するスキル。

---

## トリガー

- 「知識グラフの更新」
- 「project.json の編集」
- 「ノードを追加」
- 「関係を追加」
- 「規制情報の構造化」
- 「ナレッジグラフの管理」

---

## 管理対象

### 1. 知識グラフ

```
metadata/taxonomy/
├── thc-regulatory-knowledge-graph.json  # THC規制知識グラフ
├── content-taxonomy.skos.jsonld         # コンテンツ分類
├── compound-taxonomy.skos.jsonld        # 化合物分類
└── iptc-mapping.yaml                    # IPTCマッピング
```

### 2. project.json

```
project.json
├── project          # プロジェクト情報
├── scope            # 調査範囲
├── dataSources      # データソース
├── queryDesign      # クエリ設計
├── thcIsomers       # THC異性体管理
├── dataCoverage     # データカバレッジ
└── metadata         # メタデータ
```

---

## 知識グラフのスキーマ

### 基本構造

```json
{
  "title": "string",
  "as_of": "YYYY-MM-DD",
  "schema": "knowledge-graph-v1",
  "nodes": [],
  "relations": [],
  "sources": [],
  "caveats": []
}
```

### ノード定義

```json
{
  "id": "string (一意識別子)",
  "term": "string (表示名)",
  "kind": "enum",
  "definition": "string (定義)"
}
```

**kind の種類:**

| kind | 用途 |
|------|------|
| `plant` | 植物 |
| `material` | 物質 |
| `chemical` | 化学物質 |
| `chemical_group` | 化合物群 |
| `treaty` | 条約 |
| `schedule` | スケジュール |
| `institution` | 機関 |
| `jurisdiction` | 法域 |
| `domestic_law` | 国内法 |
| `legal_concept` | 法的概念 |
| `legal_process` | 法的プロセス |
| `potential_measure` | 講じ得る措置 |

### 関係定義

```json
{
  "subject": "node_id",
  "predicate": "string",
  "object": "node_id",
  "qualification": "string (optional)"
}
```

**主要な述語:**

| predicate | 意味 |
|-----------|------|
| `has_defined_part` | 定義上の一部である |
| `source_of` | 由来である |
| `may_contain` | 含有し得る |
| `includes` | 含む |
| `regulates` | 規制する |
| `listed_under` | 以下のスケジュールに掲載 |
| `creates` | 創設する |
| `provides` | 提供する |
| `enacted` | 制定した |
| `scientifically_advises` | 科学的助言を行う |
| `performs` | 実施する |
| `may_result_in` | 結果となり得る |

---

## project.json の構造

### thcIsomers セクション

```json
{
  "thcIsomers": {
    "lastUpdated": "YYYY-MM-DD",
    "regulatoryBasis": "string",
    "sourceUrl": "url",
    "knowledgeGraph": "path",
    "internationalTreatyStatus": {},
    "recommendedPhrasing": "string",
    "limitationNote": "string",
    "classificationSystem": {},
    "stereoisomerBreakdown": {},
    "regulatedIsomers": [],
    "regulatedAcetates": [],
    "nomenclatureSystems": {},
    "nomenclatureMapping": {},
    "naturalOccurrence": {},
    "productionTypes": {},
    "isomers": {}
  }
}
```

### isomer エントリの構造

```json
{
  "canonicalName": "string",
  "japaneseName": "string",
  "aliases": [],
  "regulation": "string",
  "regulationStatus": "string",
  "naturalOccurrence": "confirmed | unconfirmed | not-natural",
  "casNumber": "string | null",
  "iupacName": "string | null",
  "commonName": "string",
  "notes": "string"
}
```

---

## 更新ワークフロー

### Step 1: 変更計画

```yaml
change_plan:
  target: "knowledge_graph | project.json | both"
  type: "add_node | add_relation | update_node | update_metadata"
  reason: "string"
  sources: []
```

### Step 2: 変更実行

```bash
# JSON検証
python3 -c "import json; json.load(open('file.json')); print('Valid JSON')"
```

### Step 3: 整合性確認

```bash
# ノードIDの参照確認
python3 -c "
import json
kg = json.load(open('metadata/taxonomy/thc-regulatory-knowledge-graph.json'))
node_ids = {n['id'] for n in kg['nodes']}
for r in kg['relations']:
    assert r['subject'] in node_ids, f'Subject not found: {r[\"subject\"]}'
    assert r['object'] in node_ids, f'Object not found: {r[\"object\"]}'
print('✅ All relations reference valid nodes')
"
```

### Step 4: 日付更新

```json
{
  "as_of": "YYYY-MM-DD",  // 知識グラフ
  "lastUpdated": "YYYY-MM-DD"  // project.json
}
```

### Step 5: コミット

```bash
git add metadata/taxonomy/*.json project.json
git commit -m "Update knowledge graph: [変更内容]"
```

---

## 命名規則

### ノードID

```text
小文字 + ハイフン区切り
例: "delta9", "other6", "japan-act"
```

### ファイル名

```text
lowercase-kebab-case.json
例: "thc-regulatory-knowledge-graph.json"
```

---

## バリデーション

### 必須チェック

| チェック | 内容 |
|----------|------|
| JSON妥当性 | パース可能か |
| ノードID一意性 | 重複がないか |
| 関係参照 | subject/objectが有効なノードか |
| 日付形式 | YYYY-MM-DD 形式か |
| 出典 | sources に記載があるか |

### バリデーションコマンド

```bash
# 知識グラフ検証
python3 -c "
import json
kg = json.load(open('metadata/taxonomy/thc-regulatory-knowledge-graph.json'))
print(f'Nodes: {len(kg[\"nodes\"])}')
print(f'Relations: {len(kg[\"relations\"])}')
print(f'Sources: {len(kg[\"sources\"])}')
# ノードID一意性
ids = [n['id'] for n in kg['nodes']]
assert len(ids) == len(set(ids)), 'Duplicate node IDs'
print('✅ Validation passed')
"
```

---

## 更新履歴管理

### 知識グラフ

```json
{
  "as_of": "YYYY-MM-DD",
  "update_history": [
    {
      "date": "YYYY-MM-DD",
      "change": "string",
      "sources": []
    }
  ]
}
```

### project.json

```json
{
  "metadata": {
    "updated": "YYYY-MM-DD"
  }
}
```

---

## 注意事項

| 項目 | 内容 |
|------|------|
| **出典必須** | すべての変更には一次資料が必要 |
| **日付記録** | 変更日を必ず記録 |
| **整合性** | ノードと関係の参照整合性を維持 |
| **重複防止** | 同一ノードの重複追加を防止 |
| **JSON検証** | 変更後は必ずJSON妥当性を確認 |

---

## 関連ファイル

| ファイル | 内容 |
|----------|------|
| `project.json` | プロジェクト設定 |
| `metadata/taxonomy/thc-regulatory-knowledge-graph.json` | THC規制知識グラフ |
| `docs/specs/thc-nomenclature-standard.md` | 命名法標準 |
| `.github/skills/regulatory-status-compiler/SKILL.md` | 規制情報コンパイラ |
