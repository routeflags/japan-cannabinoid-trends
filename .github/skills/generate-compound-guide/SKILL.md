---
name: generate-compound-guide
description: |
  カンナビノイド化合物のガイドページ（HTML）を生成するスキル。
  CBX ガイドページ（guide_cbx_rewrite.html）と同じ構造で、
  CBD・CBN・CBG・THC などの化合物用ガイドを生成する。
  substance-dictionary 準拠のエビデンスラダーシステム、
  主張ラベル、薬機法コンプライアンスを含む。
  「化合物のガイドページ作成」「CBN のガイド生成」
  「CBD ガイドを同じフォーマットで」などで使う。
---

# Compound Guide Page Generator スキル

CBX ガイドページ（`publication/guide_cbx_rewrite.html`）と同じ構造で、他のカンナビノイド化合物用のガイドページを生成するスキル。

substance-dictionary スキルのアプローチを HTML ページに統合した、**エビデンス重視の化合物ガイド生成システム**。

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
| `tier` | string | — | "flagship" または "standard"（デフォルト: standard） |
| `data_sources` | object | — | 独自データのソース情報 |

---

## Tier システム（substance-dictionary 準拠）

作成開始前に必ず tier を決める。tier は `独自調査` セクションの要否と、検証の深さを決める。

| Tier | 対象例 | 独自調査 | 要件 |
|------|--------|---------|------|
| **flagship** | THC / CBD / CBN / CBG / CBX 等、主要カンナビノイド | **必須** | 検索動向・SNS動向・COA の 3 本柱 |
| **standard** | 上記以外、または取り扱い実績の薄い物質 | **任意** | 独自調査を行わない場合は省略し、その旨を明記 |

**flagship の判定基準**（いずれかを満たす）:
1. 当該物質に関する記事・企画が 2 件以上ある
2. GSC で当該物質のクエリが月 100 インプレッション以上ある

---

## Evidence Ladder（エビデンスラダー）

科学的主張には必ず証拠レベルを付す。**レベルを書かずに断定しない。**

| レベル | 定義 | 例 |
|--------|------|-----|
| **L1** | ヒト介入研究（RCT / 併用試験） | 臨床試験の主要評価項目 |
| **L2** | ヒト観察研究 / 症例報告 | 過去調査の疫学知見、症例報告 |
| **L3** | 動物研究 | マウス / ラットでの受容体活性 |
| **L4** | in vitro / in silico | 細胞株での結合実験、分子ドッキング |
| **L0** | 逸話 / SNS / マーケティング表現 | **本文の根拠には使わない** |

**重要な区別**:
- `receptor binding affinity`（L4）と `functional activity`（L4-L3）は別物
- `functional activity` と `ヒトでの効能`（L1）は別物
- `受容体活性` と `体感上の効力` は別物

これらを混同した記述は **書き直す**。

---

## Claim Labels（主張ラベル）

本文中の主張には、該当するラベルを付ける。

| ラベル | 意味 | 例 |
|--------|------|-----|
| **OBSERVED** | 測定・観測された事実 | 「X に N 件の投稿を取得した」 |
| **DERIVED** | 上記から計算・集計した値 | 「月平均 M 件」 |
| **INTERPRETATION** | 観測からの解釈 | 「春に増加傾向があった」 |
| **HYPOTHESIS** | 未検証の仮説 | 「規制報道が増加した影響と考えられる」 |
| **RECOMMENDATION** | 推奨（読者への助言） | 原則この記事では扱わない |

ラベルを明示できない主張は書かない。

---

## Compliance Rules（コンプライアンスルール）

### 必須

- 一次資料と二次資料を区別する
- 科学的主張には出典を付ける（証拠レベルとセットで）
- 法規制は政府・官報等の一次資料を優先する
- 公布日と施行日を区別する
- 観測結果と因果関係を区別する
- 不明なことは「不明」と書く
- ヒト研究と動物研究を区別する
- 受容体活性と体感上の効力を混同しない
- SNS 投稿数と使用者数を混同しない
- Google Trends Index を検索件数として扱わない
- データ取得日を記録する
- 利益相反の開示を記載する
- ライセンス（CC-BY-4.0 等）を明記する

### 禁止

- 「THC の○倍」と根拠なく断定すること
- SNS 情報だけによる薬理作用の断定
- 販売促進目的の誇張
- **規制回避方法の提示**
- 出典のない安全性の断定
- 相関関係から因果関係を導くこと
- 独自調査を第三者研究のように表現すること
- 用法・用量の指示（薬機法リスク）
- 疾病の治療・予防を暗示する表現（薬機法リスク）
- 研究結果を当社商品の効果であるかのように書くこと

### 薬機法・YMYL 対応

このカテゴリは健康に関する情報（YMYL）に該当する。以下を徹底する。

1. **効能・効果の断定をしない**。「〜に効く」「〜を治す」は書かない。研究知見を「研究では X が示された」という形で述べる。
2. **医療行為の代替を装わない**。「医療相談の代わりになる」等の表現を使わない。
3. **個別の治療助言をしない**。読者個人への助言として読める記述は書かない。
4. **用量・投与経路の指示をしない**。
5. 不確実な知見を確実な形で述べない。`may` / `suggests` の訳語で不確実性を保持する。

---

## COA Section の特別ルール

COA（Certificate of Analysis）に関する記述は、他セクションより厳しい規律を課す。

**書いてよいこと**:
- COA が何を記載するか（カンナビノイドプロファイル、残留農薬、重金属、溶剤、微生物）
- COA の読み方（検査機関、抽出方法、定量限界、単位）
- 天然物製品におけるロット間変動の考え方
- 購入者が COA を確認すべき理由

**書いてはいけないこと**:
- 当社製品の分析結果数値の提示
- 当社製品の純度・安全性の保証
- サプライヤー提供 COA を当店自身の分析であるかのように表現すること

**必ず明記する区別**:
- 原料 COA ≠ 販売製品ごとの検査結果
- サプライヤーによる分析 ≠ 当店自身による分析
- 商品設計意図 ≠ 医学的効果

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

### 市場・社会動向セクションの要件

| 項目 | 内容 |
|------|------|
| **H2 ID** | `market` |
| **H3 1** | 市場の文脈（出典付き） |
| **H3 2** | 製品形態（リスト形式） |
| **H3 3** | 社会的議論（観測と推論を分離） |
| **注意ブロック** | 市場情報の限界を明記 |

**重要な規則:**
- 観測と推論を分離する
- 販売促進に転化しない
- 出典を付ける

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
    <!-- 市場・社会動向 -->
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
    <!-- 市場・社会動向 -->
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
| エビデンスラダー | 科学的主張に証拠レベルが付いているか |
| 主張ラベル | OBSERVED / DERIVED / INTERPRETATION 等が付いているか |
| 薬機法対応 | 禁止事項（効能断定・用量指示等）がないか |
| COA 区別 | 原料COAと製品COAが区別されているか |

---

## Validation Gates（検証ゲート）

生成完了後、以下のゲートを通過すること。

| Gate | 検証内容 | 通過基準 |
|------|---------|---------|
| **G1** | 構造 | 全セクションが存在し、H1 が 1 つ |
| **G2** | 証拠 | 科学的主張にすべて証拠レベル（L1-L4）が付く |
| **G3** | コンプライアンス | 禁止事項・薬機法リスク表現が 0 件 |
| **G4** | 境界 | `/guide` と `/ingredient` の境界を越える記述が 0 件 |
| **G5** | 独自調査 | flagship なら 5 H3 が完備、standard なら不実施が明記 |
| **G6** | 一貫性 | 本文・FAQ・表の数値が矛盾しない |

**G3 が通らないページは公開しない。** 修正不能な場合はその旨をユーザーに報告する。

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
