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
│   ├── 個別正規化値
│   ├── 共通スケール比較
│   └── 規制前後の変化（該当する場合）
├── 独自データ: 規制状況
│   ├── 法的扱い
│   └── 合法化条件
└── 引用情報
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
