---
name: generate-research-data-page
description: |
  化合物の調査データページ（HTML）を生成するスキル。
  CSS・スタイル・ヘッダーを含まない、調査情報のみのクリーンな HTML を出力する。
  「調査データページ作成」「CBN の調査データHTML」「研究データだけのページ」
  などで使う。
---

# Research Data Page Generator スキル

化合物の調査データのみを表示するクリーンな HTML ページを生成するスキル。

CSS、インラインスタイル、ヘッダー、フッター、記事構造を含まず、**調査方法と独自データのみ**を出力する。

---

## トリガー

- 「調査データページ作成」
- 「CBN の調査データHTML」
- 「研究データだけのページ」
- 「クリーンな調査HTML」

---

## 出力構造

生成される HTML の構成:

```
├── 調査方法
│   ├── 研究質問
│   ├── データソース
│   ├── 検索クエリ
│   ├── 取得期間
│   ├── 含み・除外基準
│   └── 再現性チェックリスト
├── 独自データ: Google Trends
│   ├── 用語の定義（単独平均・比較平均・興味度スコア）
│   ├── 個別正規化値
│   ├── 共通スケール比較
│   └── 規制前後の変化（該当する場合）
├── 独自データ: 規制状況
│   ├── 法的扱い
│   └── 合法化条件
├── 独自データ: COA（該当する場合）
├── 独自データ: X トレンド（該当する場合）
├── 独自データ: YouTube トレンド（該当する場合）
└── 引用情報
```

---

## 用語定義（必須）

Google Trends データを表示する際、以下の用語定義を**必ず**含める。

### 単独平均（個別正規化値）

各キーワードを**個別に**取得した際の12ヶ月平均値。

- 各キーワードのピークを100とする正規化
- **キーワード間の比較には使用できない**
- 各化合物の時系列推移を把握するために使用

### 比較平均（共通スケール値）

複数キーワードを**同時取得**した際の12ヶ月平均値。

- 比較セット内の最大値を100とする正規化
- **キーワード間の相対的な検索需要を示す**
- 化合物間の横断比較に使用

### 興味度スコア

Google Trends が返す相対指数（0-100）。

- 絶対検索数ではない
- 期間内の最大検索量を100とした相対値

### 定義の表示形式

```html
<div style="margin: 12px 0; padding: 12px; background: #f8f9fa; border-left: 3px solid #6c757d;">
  <p style="margin: 0 0 8px 0; font-size: 13px;"><strong>用語の定義:</strong></p>
  <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
    <li><strong>単独平均</strong>: ...</li>
    <li><strong>比較平均</strong>: ...</li>
    <li><strong>興味度スコア</strong>: ...</li>
  </ul>
</div>
```

---

## 入力パラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `compound_name` | string | ✅ | 化合物名（例: "CBD", "CBN"） |
| `compound_japanese` | string | ✅ | 日本語名（例: "カンナビジェロール"） |
| `regulation_status` | string | ✅ | 規制状況（例: "非規制（条件付き合法）"） |
| `gt_individual_avg` | number | — | Google Trends 個別平均値 |
| `gt_common_scale` | number | — | 共通スケール値（CBD=100 基準） |
| `regulation_date` | string | — | 規制施行日 |
| `regulation_law` | string | — | 関連法令 |
| `regulation_source` | string | — | 一次資料の URL |

---

## 使用例

### 基本的な生成

```bash
python3 generate_research_data_page.py \
  --compound CBN \
  --japanese "カンナビノール" \
  --regulation "指定薬物（2026年6月1日施行）" \
  --gt-individual-avg 55.6 \
  --gt-common-scale 11 \
  --regulation-date "2026-06-01" \
  --regulation-law "薬機法（指定薬物）" \
  --regulation-source "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/yakubuturanyou/other/CBN_shitei.html"
```

### 生成結果

```
publication/research_cbn.html
```

---

## 出力ファイルの特徴

| 特徴 | 内容 |
|------|------|
| **CSS** | なし |
| **インラインスタイル** | なし |
| **ヘッダー/フッター** | なし |
| **JSON-LD** | なし |
| **記事構造** | なし（調査データのみ） |
| **ファイルサイズ** | 約 8-10KB |

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `generate-compound-guide` | 完全なガイドページ（記事構造付き） |
| `generate-research-data-page` | **調査データのみのクリーン HTML** |
