---
name: standards-compliance
description: |
  ソーシャルデータの技術標準対応（W3C SKOS, IPTC, Schema.org）。
  「タクソノミー作成」「分類を標準対応に」「SKOS 準拠」「IPTC マッピング」
  「Schema.org 対応」などで使う。
---

# Standards Compliance スキル

ソーシャルデータの分類・分析基盤を技術標準（W3C SKOS, IPTC Media Topics, Schema.org）に準拠させるスキル。

---

## トリガー

- 「タクソノミー作成」
- 「分類を標準対応に」
- 「SKOS 準拠」
- 「IPTC マッピング」
- 「Schema.org 対応」
- 「RDF エクスポート」
- 「JSON-LD で公開」

---

## 対象標準

| 標準 | 用途 | 必須 |
|------|------|:----:|
| W3C SKOS | タクソノミー / Controlled Vocabulary | ✅ |
| IPTC Media Topics | Topic 分類の標準語彙 | ✅ |
| Schema.org / SocialMediaPosting | SNS 投稿メタデータ | ✅ |
| RDF/Turtle | ナレッジグラフ表現 | 出力要件 |
| JSON-LD | Web リンクデータ | 出力要件 |

---

## 設計原則

```
SocialMediaPosting
        │
        ▼
Content Metadata       ← Schema.org
        │
        ▼
Taxonomy               ← W3C SKOS
        │
        ├── Media Topics ← IPTC
        ├── Intent
        ├── Hook
        └── Format
        │
        ▼
Classifier
        │
        ▼
Statistical Analysis
```

### 必須原則

1. **分類ロジックと Taxonomy 定義を分離**
2. **Taxonomy は特定の LLM / モデル / ライブラリに依存させない**
3. **Concept ID で交換可能な設計**（将来の分類器交換が可能）
4. **既存標準との対応関係を明示**

---

## ワークフロー

### Step 1: タクソノミー定義（SKOS）

**成果物:** `metadata/taxonomy/*.skos.jsonld`

```json
{
  "@context": {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dct": "http://purl.org/dc/terms/",
    "iptc": "http://cv.iptc.org/newscodes/mediatopic/",
    "jptr": "https://japan-cannabinoid-trends.routeflags.com/taxonomy/"
  },
  "@graph": [
    {
      "@id": "jptr:my-taxonomy",
      "@type": "skos:ConceptScheme",
      "dct:title": { "@value": "My Taxonomy", "@language": "en" },
      "skos:hasTopConcept": ["jptr:concept-1", "jptr:concept-2"]
    },
    {
      "@id": "jptr:concept-1",
      "@type": "skos:Concept",
      "skos:inScheme": "jptr:my-taxonomy",
      "skos:topConceptOf": "jptr:my-taxonomy",
      "skos:prefLabel": { "@value": "Concept 1", "@language": "en" },
      "skos:altLabel": [{ "@value": "別名", "@language": "ja" }],
      "skos:notation": "concept_1",
      "skos:scopeNote": { "@value": "説明", "@language": "en" },
      "skos:broader": "jptr:parent-concept",
      "skos:related": ["jptr:related-concept"],
      "skos:closeMatch": "iptc:20000347"
    }
  ]
}
```

**必須 SKOS プロパティ:**

| プロパティ | 説明 | 必須 |
|-----------|------|:----:|
| `skos:ConceptScheme` | タクソノミー全体 | ✅ |
| `skos:Concept` | 各分類項目 | ✅ |
| `skos:prefLabel` | 正式名称（言語付き） | ✅ |
| `skos:altLabel` | 別名 | 推奨 |
| `skos:notation` | 分類コード（交換用） | ✅ |
| `skos:inScheme` | ConceptScheme 参照 | ✅ |
| `skos:scopeNote` | 定義・注意事項 | 推奨 |
| `skos:broader` / `skos:narrower` | 階層関係 | 推奨 |
| `skos:related` | 関連 Concept | 推奨 |
| `skos:closeMatch` | 外部語彙マッピング | 推奨 |

---

### Step 2: IPTC マッピング

**成果物:** `metadata/taxonomy/iptc-mapping.yaml`

```yaml
content_mapping:
  - skos_id: "jptr:concept-1"
    skos_prefLabel_en: "Concept 1"
    iptc_topic_id: "20000347"
    iptc_topic_name: "Chemistry"
    iptc_topic_uri: "http://cv.iptc.org/newscodes/mediatopic/20000347"
    mapping_type: "closeMatch"
    confidence: "medium"
    notes: "マッピングの限界を記載"
```

**マッピング種別:**

| 種別 | 意味 |
|------|------|
| `exactMatch` | 完全に同一の概念 |
| `closeMatch` | 近い概念（微妙な差異あり） |
| `related` | 関連するが同一ではない |

**IPTC Media Topics:** https://cv.iptc.org/newscodes/mediatopic/

---

### Step 3: Schema.org マッピング

**成果物:** `metadata/schema/socialmediaposting.jsonld`

```json
{
  "@context": { "schema": "https://schema.org/" },
  "@type": "schema:DefinedTermSet",
  "schema:hasDefinedTerm": [
    {
      "@type": "schema:DefinedTerm",
      "schema:name": "text",
      "internal_field": "text",
      "schema_property": "schema:text"
    }
  ]
}
```

**主要マッピング:**

| 内部フィールド | Schema.org プロパティ |
|---------------|----------------------|
| `text` | `schema:text` |
| `author_id` | `schema:author` |
| `createdAt` | `schema:datePublished` |
| `lang` | `schema:inLanguage` |
| `platform` | `schema:isPartOf` |
| `topic_id` | `schema:about` |
| `views` | `schema:interactionStatistic` (ViewAction) |
| `likes` | `schema:interactionStatistic` (LikeAction) |
| `reposts` | `schema:interactionStatistic` (ShareAction) |
| `replies` | `schema:interactionStatistic` (CommentAction) |

---

### Step 4: 分類ルール定義

**成果物:** `metadata/taxonomy/classification-rules.yaml`

```yaml
classifier_type: "rule_based"
classifier_version: "1.0.0"
taxonomy_reference: "metadata/taxonomy/content-taxonomy.skos.jsonld"

topic_keywords:
  topic_ingredient:
    - "成分"
    - "配合"
    - "CBG"
    - "CBD"

classification_logic:
  topic:
    method: "keyword_matching"
    fallback: "unclassified"
```

**重要:** Concept ID (notation) は固定。分類器は交換可能。

---

### Step 5: データスキーマ拡張

**datapackage.json に分類フィールドを追加:**

```json
{
  "name": "topic_id",
  "type": "string",
  "description": "話題分類 ID (SKOS Concept notation)",
  "constraints": {
    "enum": ["topic_ingredient", "topic_product", "unclassified"]
  },
  "references": {
    "taxonomy": "metadata/taxonomy/content-taxonomy.skos.jsonld",
    "skos_scheme": "jptr:topic-scheme"
  }
}
```

---

### Step 6: エクスポート

```bash
# RDF/Turtle エクスポート
python3 scripts/export/skos-to-rdf.py input.jsonld output.ttl

# Schema.org JSON-LD エクスポート
python3 scripts/export/skos-to-schema-jsonld.py input.jsonld output.schema.jsonld

# 統合エクスポート
bash scripts/export/export-taxonomy.sh
```

---

### Step 7: 検証

```bash
bash scripts/validation/validate-data-schema.sh
```

**検証内容:**

| 検証項目 | 内容 |
|---------|------|
| SKOS ファイル存在 | content, compound, IPTC mapping 等 |
| ConceptScheme 存在 | タクソノミー定義の存在 |
| Concept 必須プロパティ | prefLabel, notation |
| inScheme 参照 | 全 Concept に inScheme あり |
| Concept ID 妥当性 | CSV の分類値が有効な Concept ID |

---

## 成果物一覧

| ファイル | 内容 | 標準 |
|----------|------|------|
| `metadata/taxonomy/*.skos.jsonld` | SKOS タクソノミー | W3C SKOS |
| `metadata/taxonomy/iptc-mapping.yaml` | IPTC 対応表 | IPTC |
| `metadata/taxonomy/classification-rules.yaml` | 分類ルール | — |
| `metadata/schema/socialmediaposting.jsonld` | Schema.org マッピング | Schema.org |
| `scripts/export/skos-to-rdf.py` | RDF/Turtle エクスポート | RDF |
| `scripts/export/skos-to-schema-jsonld.py` | JSON-LD エクスポート | JSON-LD |
| `scripts/export/export-taxonomy.sh` | 統合エクスポート | — |
| `scripts/validation/validate-data-schema.sh` | 検証スクリプト | — |

---

## エクスポート形式

| 形式 | ファイル拡張子 | 用途 |
|------|--------------|------|
| RDF/Turtle | `.ttl` | ナレッジグラフ、トリプルストア |
| Schema.org JSON-LD | `.schema.jsonld` | Web 公開、SEO |
| SKOS JSON-LD | `.skos.jsonld` | 元データ |
| YAML | `.yaml` | 対応表、ルール |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| SKOS ファイルが見つからない | パスの誤り | `metadata/taxonomy/` を確認 |
| Concept ID が無効 | CSV とタクソノミーの不一致 | 両方を確認して修正 |
| エクスポートが失敗 | JSON-LD の構文エラー | JSON 構文を確認 |
| IPTC マッピングが見つからない | ファイル不在 | `iptc-mapping.yaml` を作成 |

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `docs/specs/standards-compliance-analysis.md` | 差分分析 |
| `docs/specs/standards-compliance-implementation-plan.md` | 実装計画 |
| `metadata/datapackage.json` | データパッケージ |
| `docs/data-dictionary.md` | カラム定義 |
