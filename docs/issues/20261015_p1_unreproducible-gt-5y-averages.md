# Issue: 公開ページの 5 年平均がリポジトリの記録から再現できない

**ID:** ISS-20261015-GT-003  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `publication/research_h4cbh.html`, `publication/research_hhbd.html`,
`publication/research_thc-o.html`, `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261002T*/`,
`src/validation/publication_contract.py`（PC-2）

## 概要

公開ページ（リリースアーカイブに同梱される）の 5 年表に、**リポジトリ内の
記録から再現できない数値**がある。`ISS-20261015-GT-001`（ライブ計測）の
調査中に、5 年記録の形状を棚卸して見つけた。

## 確認した観測（2026-10-15 実測）

5 年記録の形状は 3 種ある:

| 形状 | フィールド | 対象 run | 既存ページ |
|---|---|---|---|
| (i) 平均付き | `avg_5y` / `peak_date` / `last_value` | `20261008T093228Z-google-trends-5y-baseline`（cbd/cbg/thc/hhc/thcv）、`20261008T121338Z-crdh-5y` | cbd/cbg/hhc/thc/thcv（4 項目）、crdh（7 項目） |
| (ii) 部分統計 | `data_summary.average_all` / `average_nonzero` | crdh | crdh（全項目が記録と一致することを確認） |
| (iii) **平均なし** | `first_mention` / `first_value` / `peak` / `data_points_nonzero` | thc-o / h4cbh / hhbd（2026-10-02）、cbn / crdp / hhch | thc-o / h4cbh / hhbd は**平均を表示**、cbn / crdp / hhch は**未反映** |

不一致:

| ページ | ページの記載 | run 記録 | 判定 |
|---|---|---|---|
| `h4cbh` | 5年平均 **28.3**、ピーク 2026-07-26 | `20261002T080652Z-...-h4cbh-5y`: peak 2026-07-26、first_mention 2025-04-06、nonzero 65 / zero 197。**平均のフィールドなし** | ピークは一致、平均は**出所未詳** |
| `hhbd` | 5年平均 **12.4**、ピーク 2025-12-07 | `20261002T080800Z-...-hhbd-5y`: peak 2025-12-07、nonzero 35 / zero 227。**平均なし** | 同上 |
| `thc-o` | 5年平均 **15.8**、ピーク **2023-03** | `20261002T071255Z-...-thc-o-5y`: peak **2022-04-10**（value 100）、first_mention 2022-03-13、nonzero 22 / zero 240 | **ピークが記録と不一致**、平均は出所未詳 |

- 数値の導入は単一コミット `8847241`（"Batch update research pages: add X, YouTube, GT,
  regulation sections"、2026-10-08）。コミットメッセージに run 参照はなく、ページにも出所がない。
- **THCH / CBX には 5 年 run 自体が存在しない**（§未解決）。
- 12ヶ月系列（`data` 配列あり）は cbn / crdp / hhch / thch にも存在するが、**5 年系列は 20261012 の「○○ リキッド」5 本だけ**（2026-10-12）。

## 影響

- 「一次データ」として公開し、リリースアーカイブにも入る数値が出所不明（AGENTS.md
  Derived Data / Provenance）。第三者検証ができない。
- 既存の検証器はこの種の不一致を検出できない（公開契約の **PC-2 が未実装**。
  `docs/audits/publication-contract.json` の `unimplemented_rules` にそう記録されている）。

## 対応方針

- 3 ページの 5 年表を、**記録に存在する項目だけ**で再構成する（形状 (iii) なら
  初出・初出値・ピーク・非ゼロ週数・データあり期間）。平均を残す場合は別途根拠を記録する。
- `thc-o` のピークを記録（2022-04-10）と突合し、不一致を解消する（記録を正とするか、
  別の根拠を日付付きで記録するかはメンテナ判断）。
- PC-2（公開ページの各数値が run / 記録項目を指す）を実装し、非空虚なテストで固定する。
- 同じ問題が guide と search-emergence-tracker にないか確認する。

## 完了条件

- [ ] 3 ページの 5 年表の数値がすべて run 記録から再現できる
- [ ] `thc-o` のピークの不一致が解消または根拠付きで説明されている
- [ ] PC-2 の検査（非空虚性テスト付き）

## 依存

- 本 issue は `ISS-20261015-GT-001`（境界計測）とは独立。
- `docs/reports/20261015c-publication-refresh-plan.md` §11-U9（`cbn` / `crdp` / `hhch` の
  5 年表の形式）は本 issue と同じ形状 (iii) の問題を共有する。
