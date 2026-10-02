# 技術標準対応 実装計画書

**Plan ID:** PLAN-20261002-STANDARDS
**Created:** 2026-10-02
**Status:** ACTIVE
**Target:** ISS-004 解決 + 技術標準対応

---

## 1. 背景

X コンテンツ分類が未検証である問題（ISS-004）を解決するため、分類システムを技術標準（W3C SKOS, IPTC, Schema.org）に準拠して再設計する。

## 2. 目標

1. タクソノミーを W3C SKOS 準拠で定義する
2. IPTC Media Topics とのマッピングを確保する
3. Schema.org / SocialMediaPosting との互換性を持たせる
4. 分類ロジックと Taxonomy 定義を分離する
5. 将来の分類器交換（LLM → BERT 等）が可能な設計にする
6. RDF/Turtle, JSON-LD でのエクスポートを可能にする

## 3. 対象標準

| 標準 | 用途 | 重要度 |
|------|------|:------:|
| W3C SKOS | タクソノミー基本データモデル | 必須 |
| IPTC Media Topics | Topic 分類の標準語彙 | 必須 |
| Schema.org / SocialMediaPosting | SNS 投稿メタデータ | 必須 |
| RDF/Turtle | ナレッジグラフ表現 | 出力要件 |
| JSON-LD | Web リンクデータ | 出力要件 |

## 4. 実装フェーズ

### Phase 1: SKOS タクソノミー定義

**対象:** コンテンツ分類 + 化合物分類

**成果物:**
- `metadata/taxonomy/content-taxonomy.skos.jsonld`
- `metadata/taxonomy/compound-taxonomy.skos.jsonld`

**内容:**
- ConceptScheme 定義
- Concept 定義（prefLabel, altLabel, broader, narrower, related, notation, scopeNote）
- 永続 Concept URI の発行
- IPTC Topic とのマッピング（exactMatch, closeMatch）

**工数目安:** 1-2日

---

### Phase 2: IPTC マッピング

**対象:** 独自 Concept と IPTC Media Topics の対応表

**成果物:**
- `metadata/taxonomy/iptc-mapping.yaml`

**内容:**
- 各 Concept への IPTC Topic ID 割り当て
- マッピング種別（exactMatch, closeMatch, related）の定義
- マッピングの限界に関する注記

**工数目安:** 0.5日

---

### Phase 3: Schema.org マッピング

**対象:** SocialMediaPosting との互換性

**成果物:**
- `metadata/schema/socialmediaposting.jsonld`

**内容:**
- Schema.org プロパティと内部フィールドのマッピング表
- SocialMediaPosting 型の定義
- interactionStatistic でのエンゲージメント表現

**工数目安:** 0.5日

---

### Phase 4: X データスキーマ拡張

**対象:** X データ CSV への分類フィールド追加

**成果物:**
- 更新版 `metadata/datapackage.json`
- 更新版 `docs/data-dictionary.md`

**追加カラム:**
| カラム名 | 型 | 説明 |
|----------|-----|------|
| `topic_id` | string | 話題分類 ID (SKOS Concept ID) |
| `intent_id` | string | 投稿意図 ID (SKOS Concept ID) |
| `format_id` | string | 投稿形式 ID (SKOS Concept ID) |
| `platform` | string | プラットフォーム名 |
| `language` | string | 言語コード (BCP 47) |

**工数目安:** 0.5日

---

### Phase 5: 既存データへの分類追加

**対象:** 既存 147 件の X データへの分類フィールド付与

**成果物:**
- 更新版 `x_cbx_202608_summary_anonymized.csv`
- 分類結果の検証レポート

**内容:**
- 147 件のツイートを SKOS Concept で分類
- 分類結果を CSV に追加
- 分類の整合性を検証

**工数目安:** 1日

---

### Phase 6: エクスポートスクリプト

**対象:** RDF/Turtle, JSON-LD エクスポート機能

**成果物:**
- `scripts/export/skos-to-rdf.py`
- `scripts/export/skos-to-jsonld.py`

**内容:**
- SKOS JSON-LD から RDF/Turtle への変換
- SKOS JSON-LD から JSON-LD への変換
- Schema.org 互換 JSON-LD の生成

**工数目安:** 1日

---

### Phase 7: 検証スクリプト更新

**対象:** スキーマ検証の拡張

**成果物:**
- 更新版 `scripts/validation/validate-data-schema.sh`
- SKOS 準拠検証スクリプト

**内容:**
- 新規カラムの検証
- SKOS Concept ID の妥当性検証
- IPTC マッピングの存在確認

**工数目安:** 0.5日

---

## 5. 成果物一覧

| ファイル | フェーズ | 標準 |
|----------|---------|------|
| `metadata/taxonomy/content-taxonomy.skos.jsonld` | Phase 1 | SKOS |
| `metadata/taxonomy/compound-taxonomy.skos.jsonld` | Phase 1 | SKOS |
| `metadata/taxonomy/iptc-mapping.yaml` | Phase 2 | IPTC |
| `metadata/schema/socialmediaposting.jsonld` | Phase 3 | Schema.org |
| `metadata/datapackage.json` (更新) | Phase 4 | Frictionless |
| `docs/data-dictionary.md` (更新) | Phase 4 | — |
| `x_cbx_202608_summary_anonymized.csv` (更新) | Phase 5 | — |
| `scripts/export/skos-to-rdf.py` | Phase 6 | RDF |
| `scripts/export/skos-to-jsonld.py` | Phase 6 | JSON-LD |
| `scripts/validation/validate-data-schema.sh` (更新) | Phase 7 | — |

## 6. 設計原則

### 6.1 分類ロジックと Taxonomy の分離

```
Taxonomy (SKOS JSON-LD)
    ↓
Classifier (任意の実装)
    ↓
Concept ID 出力
    ↓
統計分析
```

### 6.2 ポータビリティ

- Taxonomy は SKOS JSON-LD で公開
- 任意のツールで読み取り可能
- 分類器は Concept ID を出力するだけ

### 6.3 将来の分類器交換

- Concept ID が固定
- LLM → BERT → SetFit 等、分類器は交換可能
- 同一 Concept ID と Taxonomy を維持

### 6.4 標準優先

- 独自仕様を優先しない
- SKOS / IPTC / Schema.org で表現可能かを確認
- 独自 Concept を追加する場合も SKOS として定義

## 7. リスクと制約

| リスク | 対策 |
|--------|------|
| IPTC マッピングが不完全 | closeMatch を使用し、限界を文書化 |
| 既存データへの分類追加 | 147 件を再分類する必要あり |
| SKOS URI の管理 | リポジトリ内で解決可能な URI スキームを定義 |
| 後方互換性 | 既存カラムは維持し、追加カラムとして導入 |

## 8. ステータス

| フェーズ | ステータス | 開始日 | 完了日 |
|---------|:----------:|--------|--------|
| Phase 1 | PENDING | — | — |
| Phase 2 | PENDING | — | — |
| Phase 3 | PENDING | — | — |
| Phase 4 | PENDING | — | — |
| Phase 5 | PENDING | — | — |
| Phase 6 | PENDING | — | — |
| Phase 7 | PENDING | — | — |

---

## 関連ドキュメント

- `docs/specs/standards-compliance-analysis.md`: 差分分析
- `docs/issues/20261002_p1_unvalidated-classification.md`: ISS-004
- `metadata/keywords.yaml`: 現在のキーワード辞書
- `metadata/datapackage.json`: 現在のデータパッケージ
