---
name: generate-compound-guide
description: |
  カンナビノイド化合物のガイドページ（HTML）を生成するスキル。
  CBX ガイドページ（guide_cbx_rewrite.html）と同じ構造で、
  CBD・CBN・CBG・THC などの化合物用ガイドを生成する。
  「化合物のガイドページ作成」「CBN のガイド生成」
  「CBD ガイドを同じフォーマットで」などで使う。
---

# Compound Guide Page Generator スキル

CBX ガイドページ（`publication/guide_cbx_rewrite.html`）と同じ構造で、他のカンナビノイド化合物用のガイドページを生成するスキル。

---

## トリガー

- 「CBN のガイドページ作成」
- 「CBD ガイドを同じフォーマットで」
- 「化合物のガイド生成」
- 「HHC ガイドページを作って」
- 「CBX ガイドと同じフォーマットで」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `compound_name` | string | ✅ | 化合物の名前（例: "CBN", "CBD", "CBG", "THC", "HHC"） |
| `compound_japanese` | string | ✅ | 日本語名（例: "カンナビノール", "カンナビジェロール"） |
| `compound_full_name` | string | — | 学術的な正式名（例: "Cannabinol"） |
| `discovery_year` | string | — | 発見年（例: "1940年"） |
| `regulation_status` | string | ✅ | 日本での規制状況（例: "指定薬物（2026年6月1日施行）"） |
| `key_characteristics` | array | ✅ | 特徴のリスト |
| `comparison_compounds` | array | — | 比較対象とする化合物（デフォルト: CBD, CBG, CBX） |
| `data_sources` | object | — | 独自データのソース情報 |

---

## 出力先

```
publication/guide_{compound_name_lowercase}.html
```

例: `publication/guide_cbn.html`, `publication/guide_cbd.html`

---

## ページ構造

CBX ガイドと同じ以下のセクションを含む：

### 1. ヘッダー（HTML Head）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{compound_name} とは？成分・規制・安全性の現状（2026年版）</title>
  <meta name="description" content="...">
  <link rel="canonical" href="https://www.thch-vape.shop/guide/{compound_lowercase}">
  
  <!-- 構造化データ: BreadcrumbList -->
  <script type="application/ld+json">{...}</script>
  
  <!-- 構造化データ: Article -->
  <script type="application/ld+json">{...}</script>
  
  <!-- 構造化データ: FAQPage -->
  <script type="application/ld+json">{...}</script>
  
  <style>...</style>
</head>
```

### 2. ボディ構造

```html
<body>
  <!-- ヘッダー -->
  <header class="header">...</header>
  
  <!-- パンくず -->
  <div class="container">
    <nav class="breadcrumb">...</nav>
  </div>
  
  <main class="container">
    <!-- 著者・ライセンス情報 -->
    <!-- 利益相反の開示 -->
    <!-- 要点ブロック -->
    <!-- H1 -->
    <!-- {compound_name} とは -->
    <!-- 規制状況 -->
    <!-- 安全性について -->
    <!-- 比較 -->
    <!-- 独自データ: Google Trends -->
    <!-- 独自データ: COA分析（該当する場合） -->
    <!-- 独自データ: X/YouTubeトレンド -->
    <!-- 他の成分も探す -->
    <!-- FAQ -->
    <!-- 信頼性情報 -->
  </main>
  
  <!-- フッター -->
  <footer class="footer">...</footer>
</body>
</html>
```

---

## CSS スタイル

CBX ガイドと同じ CSS を使用：

```css
:root { 
  --brand: #2ec9bb; 
  --brand3: #2b1e1e; 
  --ink: #262626; 
  --gray: #6c757d; 
}
```

主要クラス:
- `.container` - コンテナ
- `.header` - ヘッダー
- `.breadcrumb` - パンくず
- `.trust-block` - 信頼性ブロック
- `.summary-block` - 要点ブロック
- `.caution-block` - 注意ブロック
- `.comparison-table` - 比較テーブル
- `.regulation-box` - 規制セクション
- `.data-section` - データセクション
- `.data-table` - データテーブル
- `.ingredient-cta` - 成分別CTA
- `.footer` - フッター

---

## 生成フロー

### Step 1: 化合物情報の収集

| 項目 | 収集方法 |
|------|---------|
| 化学的特徴 | 学術文献、PubChem |
| 規制状況 | 厚生労働省、INCB |
| 安全性データ | 臨床研究、毒性試験 |
| 比較データ | Google Trends、GSC、COA |

### Step 2: データ収集

| データタイプ | ソース | 備考 |
|-------------|--------|------|
| Google Trends | Google Trends API | 地域: JP、期間: 12ヶ月 |
| COA分析 | 既存データ | 該当する製品がある場合 |
| Xトレンド | Apify Twitter Search | 期間指定で取得 |
| YouTubeトレンド | YouTube Data API | クォータ注意（100回/日） |

### Step 3: HTML生成

1. テンプレートを読み込む
2. 化合物情報を埋め込む
3. データセクションを生成
4. FAQを生成
5. 出力先に保存

### Step 4: 品質チェック

- [ ] 全セクションが存在する
- [ ] 構造化データが正しい
- [ ] CSSスタイルが適用されている
- [ ] データに出典がある
- [ ] 利益相反が開示されている
- [ ] 規制情報が最新

---

## コンテンツルール

### 文体

- 敬体（です・ます調）
- 専門用語には説明を添える
- 事実と意見を分離する
- 「〜とされています」「〜が示唆されています」で表現

### 注意事項の重要性

以下のセクションは省略不可：

1. **利益相反の開示** - EC事業を運営していることを明記
2. **安全性の注意** - 医療助言ではないことを明記
3. **規制情報** - 法的リスクを明記
4. **データの限界** - データの制約を明記

### 禁止事項

- 効能の保証
- 治療の推奨
- 副作用の軽視
- 規制の過小評価

---

## データセクションの構造

```html
<!-- ===== 独自データ：Google Trends ===== -->
<div class="data-section">
  <h2 id="data-search">独自データ: {compound_name} の Google Trends 検索需要 <span class="data-badge data-badge--first">一次データ</span></h2>
  <p class="meta">データソース: Google Trends / 地域: 日本 (JP) / 期間: 過去12ヶ月 / 取得日: YYYY-MM-DD</p>
  
  <table class="data-table">
    <thead>
      <tr>
        <th>キーワード</th>
        <th class="num">平均</th>
        <th class="num">ピーク</th>
        <th>特徴</th>
      </tr>
    </thead>
    <tbody>
      <!-- データ行 -->
    </tbody>
  </table>
  
  <p class="data-note">
    <strong>所見:</strong> ...
  </p>
</div>
```

---

## FAQ生成のヒント

FAQは必ず4問以上含める：

1. **合法ですか？** - 規制状況を説明
2. **〇〇と△△の違いは何ですか？** - 比較対象との違い
3. **副作用はありますか？** - 安全性データを説明
4. **製品を選ぶときの注意点は？** - COA確認などを説明

---

## 使用例

### 例1: CBN ガイドページ生成

```
入力:
- compound_name: "CBN"
- compound_japanese: "カンナビノール"
- compound_full_name: "Cannabinol"
- discovery_year: "1940年"
- regulation_status: "指定薬物（2026年6月1日施行）"
- key_characteristics: ["大麻の主要カンナビノイド", "THCの酸化で生成", "催眠作用の可能性"]
- comparison_compounds: ["CBD", "THC", "CBG"]

出力: publication/guide_cbn.html
```

### 例2: CBD ガイドページ生成

```
入力:
- compound_name: "CBD"
- compound_japanese: "カンナビジェロール"
- compound_full_name: "Cannabidiol"
- discovery_year: "1940年"
- regulation_status: "非規制（条件付き、2024年12月施行の改正法対象）"
- key_characteristics: ["最も普及したカンナビノイド", "非精神活性", "広範な研究実績"]
- comparison_compounds: ["THC", "CBG", "CBN"]

出力: publication/guide_cbd.html
```

---

## 品質チェックリスト

生成後、必ず以下の項目を確認：

| 項目 | 確認内容 |
|------|---------|
| 構造化データ | JSON-LD が正しい形式か |
| CSSスタイル | CBX と同じスタイルが適用されているか |
| 規制情報 | 最新の法改正が反映されているか |
| データ出典 | 全データに出典があるか |
| 利益相反 | 開示が含まれているか |
| 安全性注意 | 医療助言ではない旨が明記されているか |
| FAQ | 4問以上あるか |
| 構造化データ FAQ | FAQPage が正しいか |

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `publication/guide_cbx_rewrite.html` | テンプレート（CBX） |
| `publication/guide_{compound}.html` | 生成されるページ |
| `research/regulatory-status/` | 規制状況のデータ |
| `datasets/cannabinoid-multi-trends/` | Google Trends データ |

---

## 注意事項

| 項目 | 内容 |
|------|------|
| **YouTube クォータ** | 100回/日。必要に応じて日を分ける |
| **規制情報の鮮度** | 法改正があった場合は必ず反映する |
| **COAデータ** | 該当製品のCOAがある場合のみ掲載 |
| **Google Trends の限界** | 相対指数であり、絶対検索数ではない |

---

## 関連スキル

- **update-cbx-guide**: CBX ガイドの月次更新
- **research-google-trends**: Google Trends データ収集
- **research-x-search**: X データ収集
- **research-youtube-search**: YouTube データ収集
- **standards-compliance**: 技術標準対応
