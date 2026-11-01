# Issue: 2026-11-01 YouTube liquid 8 クエリ収集の経過と CBX の採用先

**ID:** ISS-20261101-YT-019  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/youtube/`、`metadata/provenance/declarations/`、`datasets/cbx-search-trends/`、`metadata/studies/study-registry.json`

## 背景

owner 依頼（2026-11-01）で、`cannabinoid-raw-collection` の liquid-only primary である次 8 クエリを 1 クエリ 1 run で収集した。Actor は現行の `h7sDV53CddomktSi5`（`streamers/youtube-scraper`）、入力は全 run 共通で次のとおり（`searchQueries` のみクエリごとに異なる）。

```json
{
  "searchQueries": ["<query registry canonical_text>"],
  "maxResults": 500,
  "maxResultsShorts": 0,
  "maxResultStreams": 0
}
```

`dateFilter` は渡していない（絶対日付窓もローリング窓も無い）。クエリ語と `query_id` は [`metadata/queries/query-registry.json`](../../../../metadata/queries/query-registry.json) の `canonical_text` をそのまま使った。actor build は全 run `0.0.322`（`DNnMNbpTBkxkxiqx9`）。

## 最初の試行（10:48〜10:56Z、6 run 中断）

8 run を同時に起動したところ、アカウントの請求サイクル上限に達し、HHCH・THCH の 2 run だけが完走した。残り 6 run は `ABORTED` になり、次の状態で停止した。

```text
Actor aborted. You've reached the maximum usage for your current billing cycle.
```

| 検索語 | actor run ID | dataset ID | status | 件数（部分） | 観測窓（UTC、`end_exclusive`） | payload SHA-256 |
|---|---|---|---|---:|---|---|
| `CBG リキッド` | `G6xWIVcJngvmErUzU` | `fEq6KUn4xWbxRYHrW` | ABORTED | 363 | 2015-06-30 〜 2026-10-18 | `3432f27cfa74eb3725b4118f130f07a31a37d3f6337134c34152bd373eb690c5` |
| `CBX リキッド` | `ffVJ8GcbfVP6uSSlL` | `QL4UwUwRxllQUh1Hh` | ABORTED | 279 | 2010-03-19 〜 2026-10-28 | `1ae5cb798c4d9a917154395f159afe76a90f581492cb0d4542c229e1ba307b62` |
| `CRDP リキッド` | `WhjjXLW2Z9pbe2hOn` | `9p3ocScPkNnHLMmzz` | ABORTED | 250 | 2021-06-16 〜 2026-10-18 | `2547c0203d9e8e4ad2ac1e749540aff77ee0131228a4b28145c0240db317d7a1` |
| `THC リキッド` | `ImMHwcEawFExFUpHA` | `YiIhCEwOELzSWbbl7` | ABORTED | 335 | 2009-05-01 〜 2026-10-30 | `ff7b184ef50c692b044d4f37222cd9a054e4ffe38a1926329e7281561d65e66a` |
| `THC-O リキッド` | `ZwxVMtmum3bg2pYxy` | `1HyLBqE5fY6m8tXQ5` | ABORTED | 330 | 2014-08-26 〜 2026-10-30 | `03faa0a4af76c5d6ac282e3d147a63f16f3aa982695c21aac9a0a5a713f923d3` |
| `THCV リキッド` | `LeaGQhG1KjrBPGciE` | `wiSe34v01Q0nOzVx0` | ABORTED | 297 | 2011-08-15 〜 2026-10-15 | `6e748d061b7db844eb69a19fa5740fa336cf8af233a0a73524050526350666e3` |

完走した 2 run（HHCH 138 件、THCH 240 件）は `metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json` で採用済み。中断 run の部分 payload は raw に採用していない。

## 再実行（11:14〜11:33Z、6 run すべて成功）

owner が Apify の請求サイクル上限を更新した後、6 クエリを 3 run ずつ 2 回に分けて再実行した。**6 run すべてが SUCCEEDED** になった。

| 検索語 | actor run ID | dataset ID | status | 件数（一意） | 観測窓（UTC、`end_exclusive`） | payload SHA-256 | 採用 |
|---|---|---|---|---:|---|---|---|
| `CBG リキッド` | `0gmGcmM3PebBaAZn6` | `dO5K6KAS3b3dj8K1a` | SUCCEEDED | 219（219） | 2017-05-17 〜 2026-10-18 | `041eddfe638357e274a1b119273a31d8b0b2f98f6ed621cc544f10e1cdcadafb` | ✅ `20261101T111408Z-youtube-cannabinoid-raw-collection` |
| `CRDP リキッド` | `NmUt1uMYUaYt8VoIM` | `tqZ8MkqYmLy4yQlcc` | SUCCEEDED | 433（433） | 2016-06-18 〜 2026-10-18 | `8fb9e0ace10b7a5e24b0c876ec821fc3d48671bc31b881a07322cd131259037e` | ✅ `20261101T111429Z-youtube-cannabinoid-raw-collection` |
| `THC リキッド` | `8VZPBk0UClHCsRzSN` | `VuxmmDSoSJcl78LwQ` | SUCCEEDED | 435（435） | 2009-05-01 〜 2026-10-30 | `c1874ee61e54898c11a5e95cdd338cb275e3a6a75289fcc52836f2c567ab7754` | ✅ `20261101T111450Z-youtube-cannabinoid-raw-collection` |
| `THC-O リキッド` | `DFEoOKf7VPqmrobWx` | `cOXG36lTOGbxa4Yxl` | SUCCEEDED | 388（388） | 2015-10-30 〜 2026-11-01 | `4554dc2f3c33c8333663357aef7a3cf5035b5f55bdc57ab10ad47edad6237c6e` | ✅ `20261101T112513Z-youtube-cannabinoid-raw-collection` |
| `THCV リキッド` | `qhwPzh9whFRgo5iy3` | `V000qGI0L84VBeOjB` | SUCCEEDED | 435（435） | 2011-08-15 〜 2026-10-15 | `bfbbb862b046fd5d2c55ca650da102ba10fd29e4406c38cc01ff4ea7f15b47ef` | ✅ `20261101T112534Z-youtube-cannabinoid-raw-collection` |
| `CBX リキッド` | `rjEle2xXT3WNcg5Wl` | `ez0mgIizWolbKqlfW` | SUCCEEDED | 329（329） | 2010-03-19 〜 2026-10-28 | `85fa05a32b557fc573261988c3eaa2b2a1faa55e72dd8538d1c28b59aa0471dc` | ✅ `20261101T112555Z-youtube-cannabinoid-raw-collection` |

実行時刻（UTC）: CBG `11:14:08.101` → `11:19:20.618`、CRDP `11:14:29.018` → `11:24:43.300`、THC `11:14:50.158` → `11:22:44.739`、THC-O `11:25:13.536` → `11:32:01.213`、THCV `11:25:34.395` → `11:33:17.639`、CBX `11:25:55.215` → `11:32:40.802`。

全 payload で `id` は一意（重複 0）、`input` は 1 クエリのみ、`type` は `video` のみ、`date` の欠損は 0。観測窓は payload の `date` を UTC の半開区間 `[start, end_exclusive)` に正規化した派生値であり、request 条件ではない。

## 採用先の決定（2026-11-01、owner）

CBX YouTube は **`cannabinoid-raw-collection` が所有**する（liquid-only primary の 14 番目の化合物）。CBX の Google Trends / GSC raw は従来どおり [`datasets/cbx-search-trends/`](../../../../datasets/cbx-search-trends/) に残し、移動も複製もしない。所有はソース単位で分かれる:

| ソース | 所有者 | 扱い |
|---|---|---|
| YouTube（`CBX リキッド`） | `cannabinoid-raw-collection` | primary（`product_liquid`）。15 run 目 / 14 化合物目 |
| Google Trends / GSC | `cbx-search-trends` | 本 study は参照のみ（§1.3、§5.1） |

この決定を受けて、完全 payload を宣言 [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json) で `make stage` → `make adopt-all` に通した。L1 は **catalog**（`COLLECTOR_LEGACY_REFERENCE` は collector `youtube-apify-scraper` が `unverified` である旨の情報検出で、既存 15 run と同じ扱い）。raw は `datasets/cannabinoid-raw-collection/data/raw/youtube/20261101T112555Z-youtube-cannabinoid-raw-collection/` にあり、payload の SHA-256 は元 handover と一致する。

## ブロッカー

1. ~~Apify アカウントの請求サイクル上限~~: 解消（2026-11-01、owner が上限を更新）。6 クエリの再実行はすべて SUCCEEDED。金額は本リポジトリに記録しない（AGENTS.md Scope Exclusion: Cost）。
2. **中断 payload は完全な観測ではない**: 最初の試行で返った 250〜363 件は pagination の途中で停止しており、検索順の先頭部分に偏る。よって部分 payload は raw に採用せず、再実行の完全 payload を採用した。
3. ~~**CBX の採用先が未決**~~: 解消（2026-11-01、owner 決定）。CBX YouTube は `cannabinoid-raw-collection` が所有し、Google Trends / GSC は `cbx-search-trends` に残す。採用は「採用先の決定」節のとおり。

## 保全したもの

- **採用済み（L1 通過）**: 最初の試行の HHCH・THCH 2 run（宣言 [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)）と、再実行の CBG・CRDP・THC・THC-O・THCV 5 run（宣言 [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)）。raw は `datasets/cannabinoid-raw-collection/data/raw/youtube/<run-id>/`。
- **CBX（採用済み）**: 完全 payload を handover ディレクトリ（`/Users/bookair18/Desktop/youtube/youtube-dataset-cbx-liquid_ez0mgIizWolbKqlfW_2026-11-01.json`、SHA-256 `85fa05a32b557fc573261988c3eaa2b2a1faa55e72dd8538d1c28b59aa0471dc`）から byte 単位で raw 層へ採用した（run `20261101T112555Z-youtube-cannabinoid-raw-collection`）。
- **最初の試行の部分 payload**: 6 件を `*.partial.json` として同じ handover ディレクトリに保持する。再実行の完全 payload に置き換わる証跡であり、raw には置かない。
- actor input は全 run で同一（`searchQueries` のみ可変）。run status の started/finished は Apify の run オブジェクト（netloom `apify run-status`）から取得した。

## 次に必要な判断・作業

1. ~~**owner / 設計**: CBX リキッドの観測 owner を決める~~: 決済（2026-11-01）。CBX YouTube は `cannabinoid-raw-collection` が所有し、Google Trends / GSC は `cbx-search-trends` に残す。CBX リキッドの宣言・採用は完了した。
2. **再実行後（完了）**: CBG・CRDP・THC・THC-O・THCV は採用済み。成功 run のみ `staging-declaration-v1` → `make stage` → `make adopt-all` の経路を使った。

## 完了条件

- [x] 未収集 5 クエリの run が完走し、採用済みになる（CBG・CRDP・THC・THC-O・THCV、2026-11-01）。
- [x] CBX リキッドの観測 owner とクエリ設計が決まり、採用先が文書化される（2026-11-01、`cannabinoid-raw-collection` 所有・liquid-only primary）。
- [x] `make audit-youtube-coverage` の missing compounds が、決定済みの範囲と一致する（15 run / 14 化合物、`missing_compounds=0`、retained `HHC` 1 run）。
- [ ] close 時に、最初の試行の部分 payload の扱い（保持継続 / 破棄）を明記する。

## 参照

- [`metadata/queries/query-registry.json`](../../../../metadata/queries/query-registry.json)
- [`datasets/cannabinoid-raw-collection/metadata/query-design.json`](../../../../datasets/cannabinoid-raw-collection/metadata/query-design.json)
- [`ISS-20261024-COL-016`](20261024_p2_cbx-in-scope.md)（CBX を対象に含めるか）
- [`ISS-20261029-PRV-016`](../40-provenance-storage-reproducibility/20261029_p2_cbx-youtube-adoption-window.md)（CBX YouTube の採用方針）
- [`ISS-20261024-YT-013`](../40-provenance-storage-reproducibility/20261024_p2_youtube-raw-batch-without-metadata.md)（記録の無い YouTube raw）
