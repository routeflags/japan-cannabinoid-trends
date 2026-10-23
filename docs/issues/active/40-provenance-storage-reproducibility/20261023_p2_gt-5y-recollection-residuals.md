# Issue: GT 5年系列の窓ずれ・反復測定・公開審査・12ヶ月欠測の方針決定

**ID:** ISS-20261023-GT-005  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/windows/`, `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261014T*`・`20261015T*`・`20261023T*`,
`datasets/cannabinoid-platform-trends/data/processed/`, `publication/research_{thc,cbg,hhc,thcv}.html`,
`metadata/publication/research-{thc,cbg,hhc,thcv}/`
**GitHub:** [#2](https://github.com/routeflags/japan-cannabinoid-trends/issues/2)
**関連:** `ISS-20261023-GT-006`（12ヶ月再取得の所見・`20261023_p2_gt-12m-recollection-findings.md`）、
`ISS-20261023-GT-007`（CRDH 12ヶ月 summary-only・`20261023_p2_crdh-12m-summary-only.md`）、
`ISS-20261023-GT-008`（5年リキッド 5/13 語・`20261023_p2_gt-rikiddo-5y-incomplete.md`）、
`ISS-20261023-GT-009`（5年共通スケール・`20261023_p2_gt-5y-no-common-scale.md`）

## 現状（実測）

13 化合物すべてが 5年週次系列を持つ（各 262 週）。以下は方針決定だけが残っている。

### 1. 5年単独系列は 2 つの窓に分かれている

登録窓は `metadata/windows/*.json` の 4 件（5年用 2 件＋12ヶ月用 2 件）。
新パイプライン run の `temporal_provenance.window_id` と観測範囲は次の通り
（`today 5-y` は収集時刻解決のため 7 日ずれている）。

| 化合物 | run | window_id | 観測範囲 |
|---|---|---|---|
| CBD・CBN・CRDP・H4CBH・HHBD・HHCH・THCH・THC-O・CRDH（9 件） | `20261014T204841Z`〜`204904Z` ×7・`20261014T215738Z`・`20261015T205048Z` | `2021-10-10_2026-10-12` | 2021-10-10 〜 2026-10-11 |
| THC・CBG・HHC・THCV（4 件） | `20261023T162500Z`・`160420Z`・`160428Z`・`160436Z` | `2021-10-17_2026-10-18` | 2021-10-17 〜 2026-10-18 |

5年共通スケール setA〜D（`20261023T171700Z`〜`171726Z`、各 262 週）はすべて
新窓 `2021-10-17_2026-10-18`（観測 2021-10-17 〜 2026-10-18）:
setA = CBD/THC/CBG/HHC/THCV、setB = CBD/THC/THCH/CBN/CRDH、
setC = CBD/THC/CRDP/H4CBH/HHBD、setD = CBD/THC/HHCH/THC-O。
`platform_coverage.csv` / `trend_observations.csv` は 2 窓混在のまま
（例: CBD は 2021-10-10 〜 2026-10-11、THC は 2021-10-17 〜 2026-10-18）。

- 選択肢: (a) 現状維持＋「同一窓内でのみ比較」を methodology に明記 /
  (b) 全 13 化合物を同一窓で取り直す（絶対窓リクエストの実装が前提 = `GT-001` / `GT-004`） /
  (c) `window_id` を比較キーに含める（下流スキーマ変更）。

### 2. 反復測定はリキッド 12ヶ月でのみ実施済み

- 唯一の repeat run は `20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m`
 （`repeat_of: 20261012T055259Z-...-phase-a-12m`）。`repeat_diff.json` が差分を記録している:
  単独系列（CBD/THC/CBG/CBN/HHC リキッド、`today 12-m`）は 5 系列×53 週中 1 週だけ変化
  （CBD リキッド 2026-10-11: 62 → 65、最大 |diff| = 3）。比較 JA-1 は 265 セル中 2 セル変化。
  HHC リキッドの no-data は両 run で再現（`below_threshold` 確定）。
- 未測定のまま: 一般化合物語の単独系列の repeat、5年系列の repeat、共通スケール set の repeat。
  `*variance-check*` run は存在しない。setA〜D は各 1 回収集。

### 3. 再生成した公開 4 ページの内容審査

- 5年ブロックは「2021-10-17 〜 2026-10-18（262 週）」で再生成済み。
  hash は再ピン済みで、現行ファイルの sha256 と `decision.json` の `artifact_sha256` は 4 件とも一致する
  （`research-thc: 47e84474…` / `research-cbg: d26ac2c6…` / `research-hhc: 92c7b76e…` / `research-thcv: dea3e477…`、2026-10-23 確認）。
- ただし `decision.status` は 4 件とも `requires_review` のまま。
  `PUB-10` は `approved` かつ同一 sha256 の decision を要求するため、**この 4 ページは公開不可のまま**。

### 4. 12ヶ月カバレッジ（化合物別）

| 化合物 | 12ヶ月週次系列 | 備考 |
|---|---|---|
| CBD・THC・CBG・HHC・THCH・CBN・CRDP・HHCH（8 件） | あり（各 53 週、legacy run・窓未登録、観測 2025-09-28〜） | `20261002T0*` |
| HHBD・THCV・H4CBH（3 件） | あり（各 53 週、窓 `2025-10-19_2026-10-18`、観測 2025-10-19 〜 2026-10-18） | `20261023T161921Z`・`161929Z`・`162128Z`。THCV は非ゼロ 1 週 |
| CRDH | なし（summary-only） | `ISS-20261023-GT-007` を参照 |
| THC-O | なし（NO_DATA） | 新パイプラインの 12ヶ月取得は `NO_DATA` で quarantine（`.quarantine/` は Git 管理外のため tracked run なし）。詳細は `ISS-20261023-GT-006` §3 |

- 12ヶ月の「データなし」注記を公開表に入れるかは未決。`ISS-20261023-GT-006` の完了条件 1・3 と連動する。

## 残る owner 判断

- D1: 上記 1 の窓の扱い（選択肢 a / b / c）。
- D2: 上記 2 の追加反復測定の範囲（一般語 5年の repeat を回すか、回さず limitations に明記するか）。
  リキッド 12ヶ月の測定結果を一般語に外挿しないこと。
- D3: 上記 3 の 4 ページの公開承認または見送り（`decision.status` の更新）。
- D4: 上記 4 の THC-O（NO_DATA）・CRDH（summary-only）の注記の公開表記（`ISS-20261023-GT-006` と連動）。

## 完了条件

- [ ] D1〜D4 の方針決定（owner）
- [ ] 決定に基づく実施（収集・スキーマ・文書のいずれか）
- [ ] 4 ページの公開承認または見送りの記録（`decision.status` の更新）
