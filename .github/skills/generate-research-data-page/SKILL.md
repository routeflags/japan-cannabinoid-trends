---
name: generate-research-data-page
description: |
  化合物 1 つ分の調査データページ（HTML）を作るスキル。
  調査方法と集計値の表だけを出力し、記事・CSS・ヘッダーは含めない。
  「調査データページ作成」「CBN の調査データ HTML」などで使う。
---

# 調査データページ生成

化合物 1 つにつき HTML 1 枚（`publication/research_<compound>.html`）を作る。
載せるのは**調査方法と、収集したデータの集計値**だけ。記事・CSS・ナビゲーションは入れない。

## 手順

1. **数値の出所を決める**
   対象化合物の raw run を探し、`run_metadata.json` を読む。使う run の `run_id` を控える。
2. **値を集計する**
   run にある実測値だけを使い、平均・ピーク・件数は生データから計算する。
   run に無い値は「未取得」と書く。推測で埋めない。
3. **ページを生成する**

   ```bash
   python3 .github/skills/generate-research-data-page/generate_research_data_page.py \
     --compound CBN --japanese カンナビノール \
     --regulation "指定薬物（2026-06-01 施行）" \
     --gt-individual-avg 55.6 --gt-common-scale 11 \
     --output publication
   ```

4. **出力を確認する**
   下の「必須項目」を満たすか、数値と `run_id` が対応しているかを見る。
5. **公開契約を記録する**（ページを変えたときだけ）

   ```bash
   python -m validation.cli audit-publication --output docs/audits/publication-contract.json
   ```

   これは記録のみ。公開するかどうかは人が決める。

## 必須ルール

- **数値には出所を付ける。** 表の近くに `run_id` と study_id を書く（公開契約 PC-2）。
- **要求条件と観測範囲を分ける。** 「JP / today 12-m」は要求、「2025-11-02〜2026-11-01」は観測。
  1 行にまとめない。
- **単独系列と共通スケールを混ぜない。** 単独系列はその語のピークが 100、共通スケールは
  同じ要求内の最大値が 100。別の物差しなので、片方の値をもう片方に換算しない。
  表ごとにどちらかを明記する。
- **共通スケールはアンカー付き run だけを使う。** CBD・THC を同じ要求に含む run の値だけを載せる。
  現行窓の run が無ければ「未取得」と書き、旧窓の値は「歴史観測」と明記して現行窓の値と混ぜない。
- **行単位のデータを載せない。** 投稿・動画の 1 件ずつ（ID・タイトル・URL・個別の値）は
  公開しない。集計値だけを載せる。チャンネル名・アカウント名を含む分布表も載せない（識別子になる）。
- **未取得と 0 を区別する。** 取得できなかったのか、0 件だったのかを書き分ける。
- **版表記は現行リリースに合わせる。** 引用節の `Version` は `CITATION.cff` の `version` と同じ番号にする（PC-1）。
- **公開状態を変えない。** 承認状態・hash・review envelope は publication review の担当。
  このスキルはページ本文だけを作る。

## 必須項目

### Google Trends

| 項目 | 内容 |
|---|---|
| 系列の種類 | 単独系列 / 共通スケール（どちらか明記） |
| 要求条件 | geo / timeframe / window |
| 観測範囲 | 返却点の最初と最後の日付、点数 |
| 平均・ピーク・最新値 | 実測値。ピークは日付も書く |
| 非ゼロ点 | 値が 0 でない点の数 |
| `run_id` | 値の出所 |

系列の使い分け:

- **12ヶ月**: 主系列。
- **3ヶ月**: 補足。日次で直近の変化を見る。12ヶ月で全週 0 の語（例: 窓内で初出が遅い THCNM）は、
  12ヶ月の 0 が「無い」ことを意味しないため、3ヶ月を併記して分解能を補う。
- **5年**: 長期比較の補助。アンカー付き 5年 run が未採用なら、5年は被覆未完了と書く。

### X

| 項目 | 内容 |
|---|---|
| 件数 | ユニーク投稿数 |
| 分類 | カテゴリ別の件数・比率・Wilson 95% CI |
| 期間 | 観測期間（要求条件と分ける） |
| 言語 | フィルタ条件 |

### YouTube

| 項目 | 内容 |
|---|---|
| 件数 | 返却レコード数（ユニーク動画数） |
| 再生数 | 平均・中央値・最大・最小 |
| 動画長 | 平均秒数と範囲 |
| 公開年 | 年別の件数 |
| 公開日範囲 | 最小と最大 |
| 要求条件 | 検索語、`dateFilter` など |
| 取得日 | 収集日 |

### 規制・COA

該当する場合だけ。法的扱い、施行日、根拠 URL、COA の出所を書く。

## 用語

- **単独系列**: 1 語だけを取得した系列。その語のピークが 100。
- **共通スケール**: 複数語を同じ要求で取得した系列。要求内の最大値が 100。
  化合物間で比べられるのはこちらだけ。
- **興味度スコア**: Google Trends が返す 0〜100 の相対指数。検索回数ではない。

## 入力

| 引数 | 必須 | 内容 |
|---|:--:|---|
| `--compound` | ✅ | 化合物名（例 CBN） |
| `--japanese` | ✅ | 日本語名 |
| `--regulation` | ✅ | 規制状況 |
| `--gt-individual-avg` | — | 単独系列の平均 |
| `--gt-common-scale` | — | 共通スケールの値 |
| `--regulation-date` / `--regulation-law` / `--regulation-source` | — | 規制の根拠 |
| `--coa-url` / `--coa-notes` | — | COA |
| `--x-records` / `--x-period` / `--x-findings` | — | X の集計 |
| `--youtube-records` / `--youtube-period` / `--youtube-findings` | — | YouTube の集計 |
| `--output` | — | 出力先（既定 `publication`） |

## やらないこと

- CSS・インラインスタイル・ヘッダー・フッター・記事構造を入れる
- 件数だけ書く。「多様なコンテンツ」のような定性表現だけで済ませる
- run に無い数値を推測で書く
- 公開の承認状態を変える

## 関連

- 数値の正本: `datasets/<study>/data/raw/**/run_metadata.json`
- 公開契約: `src/validation/publication_contract.py`、`docs/audits/publication-contract.json`
- 完全なガイドページ: スキル `generate-compound-guide`
