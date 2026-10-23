# Issue: YouTube Data API v3 由来の raw run が手元に残存していた

**ID:** ISS-20261024-PRV-005  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `datasets/*/data/raw/youtube/`（Git 管理外）、`docs/specs/youtube-data-api-v3-setup.md`、`publication/research_cbd.html`  
**GitHub:** [#1](https://github.com/routeflags/japan-cannabinoid-trends/issues/1)

## 概要

2026-10-12 の方針決定で YouTube Data API v3 は使用対象外となり、「v3 由来の全 run を raw 層から削除した」と記録されている
（`datasets/youtube-consistency/README.md`、公開ページの CBD 節）。しかし元の checkout には **v3 由来の raw が 17 run 残っていた**。

## 実施済み（2026-10-24、owner 指示 “Go”）

- `*-dated` 14 run を削除（各 run の `run_metadata.json` が `collection_method: "Apify + YouTube Data API"` であることを個別に確認してから削除）。
- 削除後に再スキャンし、`*-dated` の残存 0 件、他の YouTube raw に `youtube/v3` / `YouTube Data API` の痕跡が無いことを確認（下記 3 件を除く）。

## 残存（要判断）

| run | 場所 | なぜ簡単に消せないか |
|---|---|---|
| `20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01` | raw-collection（旧 multi-trends） | `run_metadata.json` に `api_key_name: YouTube Data API`。公開集計（youtube_*.csv）には入っていない |
| `20261004T135232Z-youtube-cbx-12months` | `cbx-social-trends` | 公開レポート（CBX 600 件 / 関連 232 件）の数値の出所 |
| `20261004T135457Z-youtube-cbx-rikiddo-12months` | `cbx-social-trends` | 同上（CBX リキッド 125 件） |

公開ページの CBD 節は「当時の raw は削除済み」と書いており、
上記 2 件が残っている限り**記述と実体が食い違う**。一方、レポートの数値は追跡ドキュメントに既に記録されており、
raw を消しても数値は失われない（再取得は方針上行わない）。

## 対応方針（案）

1. 3 件も削除する（方針の一般則に従う。公開記述と実体が一致する）。
2. `cbx-social-trends` の 2 件だけは「公開済み数値の削除前証跡」として残し、`datasets/cbx-social-trends/README.md` に**残っている事実と理由**を書く（公開ページの「削除済み」記述も訂正する）。

## 完了条件

- [x] `*-dated` 14 run の削除（owner 承認 2026-10-24）
- [ ] 残り 3 件の扱いの決定と実施
- [ ] 公開ページ・README の記述と実体の一致確認
