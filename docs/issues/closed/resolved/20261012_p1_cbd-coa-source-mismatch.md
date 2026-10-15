# Issue: CBD 調査ページが参照する COA が repository raw にない

**ID:** ISS-20261012-CBD-005  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `publication/research_cbd.html`、`datasets/cbx-product-coa/data/raw/coa/`

## 概要

CBD 調査ページは「Wing CBD」の COA を外部 URL で参照しているが、
`datasets/cbx-product-coa/data/raw/coa/` の確認済みファイル一覧に
`wing-cbd.jpg` はなく、`wing-cbg.jpg` は存在する。

外部 URL が有効か、同じ COA を指すか、公開ページの記載・画像が対象資料と一致するかは
このファイル一覧だけでは確定していない。

## 影響

公開ページの主張・画像・製品との対応を repository 内の一次資料で追跡できず、
COA の来歴・真正性・対象ロットを第三者が確認できない。

## 対応方針

- ファイル名だけで CBD / CBG の取り違えと断定しない。
- 外部参照先、画像内容、製品名、ロット、分析機関、公開許諾を照合する。
- Raw に追加する場合は原資料を無加工で保存し、取得日時・取得元・checksum・権利状況を記録する。
- 取得・再配布権限が不明な場合は raw を追加せず、公開ページを保留または制限する。

## 完了条件

- [ ] 外部 URL の対象資料と CBD 製品・ロットの対応を確認する。
- [ ] 取得・保管・再配布の権利とプライバシーを確認する。
- [ ] 許諾が確認できた場合のみ、原資料と provenance を適切な場所に保存する。
- [ ] 許諾または対象資料を確認できない場合、ページを修正し不確実性を明記する。

## オーナー回答

https://www.thch-vape.shop/html/user_data/assets/img/coa/wing-cbd.jpg

## 対応記録（2026-10-15）

- オーナー提示の URL を取得して対応を確認した（取得日 2026-10-15）: HTTP 200、`image/jpeg`、161,038 bytes、sha256 `d201bdea04f2a1dc32b10683d8a41a1fdd762c769ebd50d2b64469fcd1b45af6`。
- 内容の対応: KCA Laboratories の COA（"CBD powder"、Client WING LLC・堺市、Sample ID SA-250915-68914、Batch SN401250301、受領 2025-03-27／完了 2025-04-07、CBD 99.7%・Total Δ9-THC 0.000274%）。ページの記載「Wing CBD 製品の COA 分析結果（サプライヤー提示）」と一致する。
- 未確認のまま残る点: 再配布の権利確認とローカル raw の保存は行っていない（`datasets/cbx-product-coa/` には README のみ。raw ディレクトリ自体が無い）。権利はオーナー側の管理であり、本 issue では外部 URL の到達性と内容対応の確認をもって解決とする。権利確認・raw 保存が必要になった場合は別 issue とする。
