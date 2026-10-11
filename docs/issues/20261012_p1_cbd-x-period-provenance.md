# Issue: CBD X データの観測期間・収集条件・metadata が一致しない

**ID:** ISS-20261012-CBD-002  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-multi-trends/data/raw/x/`、`datasets/cannabinoid-social-trends/data/raw/x/`、`publication/research_cbd.html`

## 概要

CBD の X データに、1年・1ヶ月・期間指定データと読める名称またはページ記載があるが、
確認可能な投稿 timestamp は 2026-10 の短期間に集中している。
metadata に query / observation period が記録されていない run もあり、
長期系列としての利用やページ記載の検証ができない。

## 観測された run

| Run | 件数 | 投稿日時（UTC） | 確認事項 |
|-----|-----:|-----------------|----------|
| `20261002T064331Z-x-cbd` | 60 | 2026-10-01 19:59–21:55 | metadata は 2026-09-01〜10-01 の query を記録するが、投稿はほぼ 10-01 |
| `20261008T165031Z-x-cbd-1year` | 0 | — | 空の JSON 配列 |
| `20261008T165122Z-x-cbd-1m` | 60 | 2026-10-01 11:15–21:27 | Actor run metadata のみ。query / period 記録なし |
| `20261008T165330Z-x-cbd-latest10` | 200 | 2026-10-07〜10-08 | Actor run metadata のみ。query / period 記録なし |
| `20261006T104633Z-main-compounds/cbd.json` | 100 | 2026-10-01 08:52–20:14 | run_metadata なし |

`publication/research_cbd.html` には X の収集期間が「2026-10-01（1日間）」と
「2026-07-01〜2026-10-01」の両方で記載されている。

## 影響

現状のデータから CBD の X 言及を年次・月次で比較できない。
期間指定 query と投稿日時のずれは、検索条件、Actor の挙動、または記録の不備の
いずれによるものか確定していない。

## 対応方針

- raw ファイルは変更しない。
- 既存 metadata、collection log、Actor run 情報で query と期間を検証し、確認できない値は unknown とする。
- 必要な場合のみ、費用・取得条件・API制約を事前に明示した別 run として再収集を提案する。
- 既存の 0 件 run を、根拠なく `observed_zero` と扱わない。

## 完了条件

- [ ] 各 CBD X run の検索語、期間、Actor、取得上限、record count、状態を run ごとに記録する。
- [ ] 不明な条件は推測で補完せず、unknown と明示する。
- [ ] `research_cbd.html` の X 期間表示を検証結果に一致させる。
- [ ] CBD の X データを長期時系列として扱えるかどうか、根拠付きで判定する。
