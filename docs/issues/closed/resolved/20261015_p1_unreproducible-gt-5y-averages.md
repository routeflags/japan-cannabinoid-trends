# Issue: 公開ページの 5 年平均がリポジトリの記録から再現できない

**ID:** ISS-20261015-GT-003  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15) — 5 年系列を再取得し、ページの数値をすべて run から生成。PC-2 は公開契約の未実装項目として別途追跡  
**対象:** `publication/research_h4cbh.html`, `publication/research_hhbd.html`,
`publication/research_thc-o.html`, `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261002T*/`,
`src/processing/gt_statistics.py`, `src/validation/publication_contract.py`（PC-2）

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

- ページの 5 年表は**手書きせず、run 記録から生成する**（**恒久対応**）。
  実装: `src/processing/gt_statistics.py` + `python -m processing.cli gt-summary`
  （`--html` でブロックを出力、`--output docs/audits/gt-summary.json` で機械可読レポート）。
  記録の形状（系列 / baseline / partial / averaged）ごとに計算できことを計算し、
  **できない項目は「算出不能」と理由付きで報告**する（推測で埋めない）。
- 3 ページの出所未詳の平均はどうなったか: 2026-10-02 の run は**系列も平均も保存していない**
  ため、**リポジトリからは再計算できない**（実測。`gt-summary` の `unavailable_mean` が
  6 化合物を列挙）。再計算するには当該の 5 年系列を**再取得**する必要がある（§未解決）。
  再取得が済べば、同じスクリプトがコード変更なしに平均を出す。
- `thc-o` のピークは生成により記録の **2022-04-10** に修正された（日付単位）。
- PC-2（各数値が run / 記録項目を指す）の完全な検査は今後の作業だが、
  生成されたブロックは各表の下に出所（run_id・収集日）を必ず含む。
- 同じ問題が guide と search-emergence-tracker にないか確認する。

## 対応（2026-10-15）

メンテナ指示により**ライブ収集をパイプライン経由で実行**し、この issue の原因（系列が保存されていない）を解消した。

- 実装: `collection.core.cli collect --live`（`SessionMcpTransport` + `mcp_session.McpStdioSession`）
  + pipeline が「verbatim な tool result（生）」と「解析済み系列（派生、`records_<term>.json`）」の
  **2 成果物**を 1 run に書くようにした。7 run（CBN / THC-O / H4CBH / HHBD / HHCH / CRDP / THCH）を
  `today 5-y` / geo=JP で収集し、L1 を通過して catalog に採用（`audit-new-runs`: new=7 / failures=0）。
- `processing.cli gt-summary` の結果: **13 化合物すべて computed、`unavailable_mean` は空**になり、
  7 ページの 5 年表がライブ系列から生成された。
- `thc-o` のピークは記録どおり **2022-04-10**（旧記載の 2023-03 を置換）。
- 旧 2026-10-02 の要約との差（実例）: `h4cbh` の初出は旧記録 2025-04-06 だったが、
  実系列では **2022-12-04**（値 44）。`hhbd` も 2025-11-30 → 2022-09-18。
  **要約形の記録は系列から検算できない**という本 issue の主張を裏付ける事例。
- 監査: `docs/audits/publication-contract.json` の findings 0、宣言済みギャップは 1 件
  （`crdh` の最新値のみ。crdh は 2026-10-08 の要約形のままで、系列がない）。
- **CRDH も再取得して閉じた（2026-10-15、実施⑧）**: 同じライブ経路（`collect --live`）で
  `today 5-y` の系列（262 週）を取得し、`gt-summary` が 4 項目すべてを算出した。
  系列が無い化合物は 0 になり、宣言済みギャップも 0 に。
  旧要約との差（要約形は系列から検算できないことの実例がまた 1 件増えた）:
  初出 2023-09-24 → **2024-08-25**、5 年平均 15.3 → **8.25**、ピーク 2024-12-15 →
  **2024-12-29**。ページは series から生成した値に置換済み。

## 残り

- `PC-2`（各数値が run / 記録項目を指すことの機械検査）は **実装済み（2026-10-15、実施⑧）**。
  規則は「研究ページの Google Trends セクションが生成元の run を名乗る」+
  「ページが名乗った run は catalog に存在する」（`src/validation/publication_contract.py`、
  非空虚性テストは `tests/validation/test_publication_contract.py`）。
  X / YouTube / COA セクションは旧契約の収集で run 記録が無いため、「run を名乗る」
  ことは要求していない（名乗った場合の解決だけを検査する）。

## 未解決

- なし（系列の再取得は 8 化合物すべて完了。境界計測は `ISS-20261015-GT-001` の範囲）。

## 完了条件

- [x] 5 年表の数値がすべて run 記録から生成される（手書きをやめた）
- [x] `thc-o` のピークの不一致が解消（記録の 2022-04-10）
- [x] 記録にない値は「算出不能」として理由付きで表示される
- [x] **8 化合物の 5 年系列を再取得し、実の平均値を出した**（2026-10-15、パイプライン経由の
  ライブ収集。7 化合物 + CRDH）
- [x] PC-2 の検査（非空虚性テスト付き）を実装（2026-10-15）

## 依存

- 本 issue は `ISS-20261015-GT-001`（境界計測）とは独立。
- 再取得は `ISS-20261015-GT-001` のライブ計測承認に相乗りした（2026-10-15）。
- `docs/reports/20261015c-publication-refresh-plan.md` §11-U9（形式）と §11-U10（THCH）は
  本 issue と同じ問題を共有し、どちらも 2026-10-15 に解消。
