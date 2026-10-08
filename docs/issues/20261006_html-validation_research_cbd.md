# HTMLバリデーション: research_cbd.html

## 判定

**PASS**（修正後）

| 項目 | 値 |
|------|-----|
| 対象 | `publication/research_cbd.html` |
| 検証日 | 2026-10-06 |
| ツール | html-validate 11.16.0 |
| ルール | `html-validate:recommended`（seo-operations `.htmlvalidate.json` 準拠） |
| 修正前 | FAIL（6 errors） |
| 修正後 | **PASS（0 errors）** |

---

## 検証範囲

- HTML 構文・推薦ルール（`html-validate:recommended`）
- インラインスタイル有無
- 行末空白
- 基本メタ情報（doctype / lang / charset / viewport / title）

対象外: 表示品質、SEO 指標、リンク切れ、コンテンツ正確性

---

## 修正前（6 errors）

| 行:列 | ルール | 内容 |
|--------|--------|------|
| 29:1 | `no-trailing-whitespace` | 空白行の行末空白 |
| 30:8 | `no-inline-style` | 定義ブロック `<div style="...">` |
| 31:8 | `no-inline-style` | 定義見出し `<p style="...">` |
| 32:9 | `no-inline-style` | 定義リスト `<ul style="...">` |
| 38:1 | `no-trailing-whitespace` | 空白行の行末空白 |
| 149:105 | `no-inline-style` | COA画像 `<img style="...">` |

---

## 適用した修正

方針: **インラインスタイルは削除**（CSSクラス化は行わない）。装飾より情報構造を優先。

### 1. インラインスタイル削除（4件）

| 要素 | 削除した style | 結果 |
|------|----------------|------|
| 定義ブロック `<div>` | margin / padding / background / border-left | スタイルなしの `<div>` |
| 定義見出し `<p>` | margin / font-size | 通常の `<p>` |
| 定義リスト `<ul>` | margin / padding-left / font-size | 通常の `<ul>` |
| COA画像 `<img>` | max-width / height | 通常の `<img>`（alt維持） |

### 2. 行末空白の除去（2件）

29行目・38行目の空白行をクリーンアップ。

---

## 修正後

```
npx html-validate --config .htmlvalidate.json publication/research_cbd.html
exit=0
```

| 検査 | 結果 |
|------|------|
| html-validate（recommended） | ✅ 0 errors |
| `style=` 残留 | ✅ なし |
| 行末空白残留 | ✅ なし |

---

## 構造所見（エラーではない）

| 項目 | 状態 | 所見 |
|------|------|------|
| H1 | なし（H2開始） | **許容**（当該ページは調査データ断片として H2 始まりで問題なし） |
| `<html lang="ja">` | ✅ | |
| charset / viewport | ✅ | |
| `<title>` | ✅ | 「CBD 調査データ」 |
| テーブル | ✅ | thead / tbody あり |
| 画像 alt | ✅ | |
| 一次資料リンク | ✅ | 厚労省PDF・Zenodo DOI |

---

## 影響

- インラインスタイル削除により、外部CSS未接続でも意味構造は保持される
- 装飾（定義ブロックの背景・左罫線）は当面失われる。必要なら後日CSSで付与可
- COA画像の縮小表示は、親要素CSSや `img { max-width: 100% }` に依存する

---

## 推奨フォロー

任意（本レポートでは未実施）:

1. publication配下で共通CSSを使うなら、`img { max-width: 100%; height: auto }` を側車CSSに置く
2. 同型の `research_*.html` も同じルールで監査する
