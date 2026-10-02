# 技術標準対応 差分分析

**Version:** 1.0.0
**Date:** 2026-10-02
**Purpose:** 既存データモデルと技術標準（W3C SKOS, IPTC, Schema.org）の差分を特定し、標準対応に必要な変更点を提示する

---

## 1. 対象標準

| 標準 | 用途 | 重要度 |
|------|------|:------:|
| W3C SKOS | タクソノミー / Controlled Vocabulary の基本データモデル | 必須 |
| IPTC Media Topics / NewsCodes | Topic 分類の標準語彙 | 必須 |
| Schema.org / SocialMediaPosting | SNS 投稿メタデータ表現 | 必須 |
| RDF/Turtle | ナレッジグラフ表現 | 出力要件 |
| JSON-LD | Web リンクデータ | 出力要件 |

---

## 2. 既存データモデル調査結果

### 2.1 現在のファイル構成

| ファイル | 形式 | 標準準拠 | 問題点 |
|----------|------|:--------:|--------|
| `metadata/keywords.yaml` | カスタム YAML | ❌ | SKOS 非準拠。Concept URI なし。階層関係なし |
| `metadata/datapackage.json` | Frictionless | △ | Schema.org マッピングなし |
| X データ CSV | CSV | ❌ | コンテンツ分類フィールドなし |
| ガイドページ分類表 | HTML | ❌ | タクソノミー定義ファイルなし |

### 2.2 keywords.yaml の問題点

```yaml
# 現在の形式（SKOS 非準拠）
CBX:
  display_name: "CBX"
  category: "minor_phytocannabinoid"
  keywords:
    - "CBX"
    - "CBX リキッド"
  polysemy_warning: "..."
  discriminating_queries:
    - "CBX 大麻"
```

**SKOS で表現すべき内容:**

| 現在のフィールド | SKOS での表現 |
|-----------------|--------------|
| `CBX` (キー) | `skos:Concept` + `@id` (URI) |
| `display_name` | `skos:prefLabel` |
| `keywords` | `skos:altLabel` |
| `category` | `skos:broader` (上位 Concept への参照) |
| `polysemy_warning` | `skos:scopeNote` または `skos:note` |
| `discriminating_queries` | `skos:related` またはカスタムプロパティ |
| (なし) | `skos:inScheme` (ConceptScheme への参照) |
| (なし) | `skos:topConceptOf` |

### 2.3 X データスキーマの問題点

**現在のカラム:**
```
tweet_id_hash, createdAt, week, lang, author_id,
views, likes, reposts, replies, has_text, text_length
```

**不足しているカラム:**

| カテゴリ | 必要フィールド | Schema.org 対応 |
|----------|---------------|-----------------|
| コンテンツ分類 | `topic_id`, `intent_id`, `format_id` | `about`, `keywords` |
| 投稿メタデータ | `platform`, `url` | `isPartOf`, `url` |
| 意味論的メタデータ | `language`, `datePublished` | `inLanguage`, `datePublished` |

---

## 3. 標準対応差分分析

### 3.1 W3C SKOS 差分

| 要件 | 現状 | 差分 | 変更内容 |
|------|------|------|---------|
| Concept URI | ❌ なし | Concept ごとに永続 URI を発行 | `@id` フィールド追加 |
| ConceptScheme | ❌ なし | タクソノミー全体を ConceptScheme として定義 | `skos:ConceptScheme` 定義 |
| prefLabel | △ `display_name` | SKOS プロパティ名に変更 | `skos:prefLabel` |
| altLabel | △ `keywords` | SKOS プロパティ名に変更 | `skos:altLabel` |
| broader/narrower | ❌ なし | 階層関係を定義 | `skos:broader` / `skos:narrower` |
| related | ❌ なし | 関連 Concept を定義 | `skos:related` |
| inScheme | ❌ なし | Concept が属する Scheme を指定 | `skos:inScheme` |
| scopeNote | △ `polysemy_warning` | SKOS プロパティ名に変更 | `skos:scopeNote` |
| notation | ❌ なし | 分類コード（例: "ingredient_discussion"） | `skos:notation` |

### 3.2 IPTC Media Topics 差分

| 要件 | 現状 | 差分 | 変更内容 |
|------|------|------|---------|
| IPTC Topic ID | ❌ なし | 各 Concept に IPTC Topic ID を割り当て | `skos:exactMatch` / `skos:closeMatch` |
| IPTC Hierarchical Coding | ❌ なし | IPTC の階層構造を参照 | `skos:broader` で IPTC Concept にリンク |
| Topic とのマッピング | ❌ なし | 独自 Concept と IPTC Topic の対応表 | `skos:mappingRelation` |

**IPTC Media Topics とのマッピング例:**

| 独自 Concept | IPTC Topic (候補) | マッピング種別 |
|-------------|------------------|---------------|
| 配合/成分 | 20000347 (Chemistry) | closeMatch |
| 新商品/入荷 | 20000323 (Products and Services) | closeMatch |
| 体感/効果 | 20000329 (Health and Fitness) | closeMatch |
| セール/キャンペーン | 20000322 (Marketing) | closeMatch |
| レビュー | 20000349 (Reviews) | closeMatch |
| 店舗情報 | 20000325 (Retail) | closeMatch |

### 3.3 Schema.org / SocialMediaPosting 差分

| 要件 | 現状 | 差分 | 変更内容 |
|------|------|------|---------|
| SocialMediaPosting 型 | ❌ なし | SNS 投稿を Schema.org 型で表現 | `@type: SocialMediaPosting` |
| text | △ CSV のみ | Schema.org プロパティにマッピング | `schema:text` |
| author | △ `author_id` | Schema.org プロパティにマッピング | `schema:author` |
| datePublished | △ `createdAt` | Schema.org プロパティにマッピング | `schema:datePublished` |
| platform | ❌ なし | プラットフォームを指定 | `schema:isPartOf` (Platform) |
| url | ❌ 匿名化で削除 | 公開 URL（ハッシュ化済み） | `schema:url` |
| keywords | ❌ なし | 分類キーワード | `schema:keywords` |
| about | ❌ なし | 話題の Concept | `schema:about` |
| inLanguage | △ `lang` | Schema.org プロパティにマッピング | `schema:inLanguage` |
| interactionStatistic | △ views/likes 等 | Schema.org プロパティにマッピング | `schema:interactionStatistic` |

---

## 4. 変更点サマリー

### 4.1 新規作成ファイル

| ファイル | 内容 | 標準 |
|----------|------|------|
| `metadata/taxonomy/content-taxonomy.skos.jsonld` | コンテンツ分類タクソノミー | W3C SKOS |
| `metadata/taxonomy/compound-taxonomy.skos.jsonld` | 化合物タクソノミー | W3C SKOS |
| `metadata/taxonomy/iptc-mapping.yaml` | IPTC Topic との対応表 | IPTC |
| `metadata/schema/socialmediaposting.jsonld` | Schema.org マッピング定義 | Schema.org |

### 4.2 変更ファイル

| ファイル | 変更内容 |
|----------|---------|
| `metadata/keywords.yaml` | SKOS 準拠形式に変換（後方互換のため YAML は維持、JSON-LD を追加） |
| `metadata/datapackage.json` | Schema.org マッピング追加 |
| X データ CSV | 分類フィールド追加（topic_id, intent_id, format_id） |
| `docs/data-dictionary.md` | 新規フィールドの定義追加 |

### 4.3 新規カラム（X データ）

| カラム名 | 型 | 説明 | Schema.org |
|----------|-----|------|------------|
| `topic_id` | string | 話題分類 ID (SKOS Concept ID) | `schema:about` |
| `intent_id` | string | 投稿意図 ID (SKOS Concept ID) | カスタム |
| `format_id` | string | 投稿形式 ID (SKOS Concept ID) | カスタム |
| `platform` | string | プラットフォーム名 | `schema:isPartOf` |
| `language` | string | 言語コード (BCP 47) | `schema:inLanguage` |

---

## 5. 設計原則の適用

### 5.1 分類ロジックと Taxonomy の分離

```
現在: 分類結果が HTML に直接埋め込まれている
     ↓
目標: Taxonomy は独立ファイル、分類器は Concept ID を出力
```

### 5.2 ポータビリティ

```
現在: keywords.yaml はカスタム形式
     ↓
目標: SKOS JSON-LD で公開、任意のツールで読み取り可能
```

### 5.3 将来の分類器交換

```
現在: 分類方法が不明
     ↓
目標: Concept ID が固定、分類器（LLM/BERT等）は交換可能
```

---

## 6. 実装ロードマップ

| フェーズ | 内容 | 工数目安 |
|---------|------|---------|
| Phase 1 | SKOS タクソノミー定義（コンテンツ分類 + 化合物） | 1-2日 |
| Phase 2 | IPTC マッピングテーブル作成 | 0.5日 |
| Phase 3 | Schema.org マッピング定義 | 0.5日 |
| Phase 4 | X データスキーマ拡張 | 0.5日 |
| Phase 5 | 既存データへの分類フィールド追加 | 1日 |
| Phase 6 | エクスポートスクリプト（RDF/Turtle, JSON-LD） | 1日 |
| Phase 7 | 検証スクリプト更新 | 0.5日 |

**合計:** 5-6日

---

## 7. リスクと制約

| リスク | 対策 |
|--------|------|
| IPTC Topic とのマッピングが不完全 | closeMatch を使用し、マッピングの限界を文書化 |
| 既存データへの分類フィールド追加 | 既存 147 件を再分類する必要あり |
| SKOS URI の管理 | リポジトリ内で解決可能な URI スキームを定義 |
| 後方互換性 | 既存 CSV のカラムは維持し、追加カラムとして導入 |
