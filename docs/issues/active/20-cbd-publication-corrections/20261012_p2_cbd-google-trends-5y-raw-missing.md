# Issue: CBD Google Trends 5年系列の raw タイムラインが未収蔵

**ID:** ISS-20261012-CBD-004  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/`

## 概要

CBD の Google Trends 12ヶ月データは raw タイムライン（53点）が存在する一方、
5年ベースラインは CBD の summary JSON のみで、報告上 261 点の時系列 raw がない。
そのため年次・月次の再集計やピーク値の独立検証ができない。

## 確認された記録

summary JSON の CBD 行:

- geo: JP
- timeframe: `today 5-y`
- data_points: 261
- first_value: 42
- last_value: 14
- peak_value: 100
- peak_date: 2025-08-31 to 2025-09-06
- avg_5y: 32.5

これらの値を構成する個々の日時・値は同 run の raw ファイルとして確認されていない。

## 影響

5年の peak_date、平均、長期推移を元観測値から再検証・再計算できない。
summary 値と raw observation の区別も読み手に不明確になる。

## 対応方針

- 既存 summary を raw として扱わない。
- 既存の collection log / 保存場所を確認し、raw が見つからない場合は「未収蔵」と明記する。
- 追加取得を行う場合は、Google Trends の取得日時・地域・期間・query・collector 情報を保存する。

## 完了条件

- [ ] raw タイムラインが存在するか、その保管場所と来歴を確認する。
- [ ] 見つからない場合は summary-only / raw missing と dataset metadata に記録する。
- [ ] summary の 261 点・平均・ピーク値を raw で検証できるか明示する。
- [ ] 新規取得する場合、既存 summary を上書きせず新しい run として保存する。
