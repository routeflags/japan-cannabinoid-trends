# Issue: CBD 調査ページの X / YouTube 数値が raw・run metadata と不一致

**ID:** ISS-20261012-CBD-006  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `publication/research_cbd.html`

## 概要

CBD ページの収集期間・件数・取得日が、確認できた raw ファイルや run metadata と
複数箇所で一致しない。公開内容の数値を一次データから照合し、観測・派生・解釈を
分けて修正する必要がある。

## 確認された不整合

### X

- ページ内に「2026-10-01（1日間）」と「2026-07-01〜2026-10-01」の両方の期間がある。
- raw `cbd.json` の100件は `created_at` が 2026-10-01 の範囲に集中しており、
  3ヶ月分の時系列とは確認できない。
- X の分類結果は raw 100件中 99件を有効分類とするが、元データの観測期間と掲載期間が不一致。

### YouTube

- ページは「CBD オイル」unique 28件 / raw 60件と記載。
- 確認した `20261002T064905Z-youtube-cbd-オイル` run は `records.json` 23件。
- ページの取得日 2026-10-05 と、run ディレクトリの収集日 2026-10-02 が不一致。
- 28件が別の run または変換工程の結果か、現状の provenance からは確定できない。

## 影響

公開値が誤解を招くほか、どの収集 run・変換から導出された値か第三者が追跡できない。

## 対応方針

- raw を書き換えず、件数差は upstream / processing / deduplication の各層で調べる。
- 根拠のない値を「正しい方」として選ばず、再現できない数値は訂正または撤回する。
- 既存の `docs/issues/20261006_html-validation_research_cbd.md` は HTML 構文検証 issue であり、
  本 issue は内容・データ整合性を対象とする。

## 完了条件

- [ ] X の期間・件数が run ID と raw timestamp に照合される。
- [ ] YouTube の 28 / 23 / 60 の定義と由来が説明できる。
- [ ] 取得日・期間・件数を raw / metadata / reproducible transformation に一致させる。
- [ ] 再現できない記載は削除または未確認と表示する。
- [ ] ページの更新日と変更理由を記録する。
