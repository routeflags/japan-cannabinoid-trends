# Issue: 12ヶ月系列の再取得で判明した 3 点（ページ数値・生成器・no data の扱い）

**ID:** ISS-20261023-GT-006  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `publication/research_{thcv,thc-o,h4cbh,hhbd}.html`, `src/processing/gt_statistics.py`,
`src/validation/semantic.py`（L1-09）, `src/collection/adapters/google_trends/*`  

## 概要

2026-10-23 に 12ヶ月系列の不足分（THCV・THC-O・H4CBH・HHBD）を再取得した
（方法: `datasets/cannabinoid-raw-collection/methodology.md` §2.1.3）。
H4CBH・HHBD・THCV は週次系列が取れたが（各 53 週）、THC-O は Google Trends が no data を返した。
その過程で、データ以外に **3 つの穴**が見つかった。

## 1. 公開 4 ページの 12ヶ月平均が、どの raw 系列とも一致しない

| ページ | 記載の 12ヶ月平均 | 2026-10-23 の系列 |
|---|---:|---|
| `research_h4cbh.html` | 56 | 57.8868（53 週） |
| `research_hhbd.html` | 33 | 52.8491（53 週） |
| `research_thcv.html` | 3.1 | 1.8868（53 週、非ゼロ 1 週） |
| `research_thc-o.html` | 8.2 | 系列なし（NO_DATA） |

- 旧 12ヶ月収集（2026-10-02）にはこの 4 化合物の系列が存在しない（THCV・THC-O は nodata、H4CBH・HHBD は未収集）。
  つまりページの 4 つの数値は、**リポジトリ内のどの記録からも再現できない**（`ISS-20261015-GT-003` と同型だが 12ヶ月側）。
- 今回は**ページを書き換えていない**（公開内容の変更は審査・承認の対象）。

## 2. 12ヶ月ブロックを生成する経路が無い

- `processing.cli gt-summary` は `--timeframe 12m` を受け付けるが、`--write` の置換対象は
  5年ブロックだけ（`gt_statistics._BLOCK_RE` は「5年データサマリー」固定）。
- そのため 12ヶ月ブロックは手書きのまま残り、上の 1 のような乖離を機械検出できない。
- 選択肢: (a) `gt-summary` を 12ヶ月にも対応させて `--write` で両ブロックを生成 / 
  (b) 12ヶ月はページから外す / (c) 現状維持しつつ 12ヶ月ブロック専用の検査だけ追加。
- 併せて: `docs/audits/gt-summary.json` は 5年正本だが、12ヶ月側の機械可読レポートは存在しない。

## 3. 「ソースが no data を返した」を採用記録にできない

- THC-O の応答は（本文保全の修正後）
  “Google Trends returned no data for the given terms and timeframe. Try a broader timeframe or different terms.”
  で、`errors[].code = NO_DATA` / `reason_codes = ["no_data"]` として記録される。
- しかし `execution.status` は `failed` のままなので、L1（`COLLECTION_FAILED_NOT_ADOPTED`）が **quarantine** に落とす。
  `.quarantine/` は Git 管理外なので、**欠測の証拠がコミットされない**。
- AGENTS.md の状態分類（`missing` / `collection_failed`）から見ると、これは `missing` であって
  `collection_failed` ではない。現行契約（`collection-run-v1` / L1-09）には **missing を採用する道が無い**。
- 旧 `20261002T064135Z-google-trends-nodata` は legacy 形状（`records_nodata.json`）で catalog されているため、
  同じ事実を新パイプラインでは残せないという非対称がある。
- 選択肢: (a) `status="missing"` を契約に追加（schema / L1 / 監査の変更） /
  (b) `failed` のまま、`NO_DATA` の run だけ catalog する例外を作る / 
  (c) 現状維持し、欠測は文書（本 issue と methodology）だけで記録する。

## 付随（本作業で修正済み）

解釈に失敗したとき、アダプタが**サーバーの応答本文を捨てていた**（payload が `{"error": {...}}` に置換された）。
応答を保全するよう `GoogleTrendsMcpAdapter.collect()` を直し、no data の文を `no_data` として認識する
parser 規則を追加した（`src/collection/adapters/google_trends/boundary.py`、テストあり）。
この修正が無いと、下の 3 の「何故系列が無いか」も判定できなかった。

## 完了条件

- [x] 1: 4 ページの 12ヶ月数値の扱いの決定（訂正 / 削除 / 出所明記）— 2026-11-05 に対応（下の「2026-11-05 の更新」）
- [ ] 2: 12ヶ月ブロックの生成器か検査のどちらかを実装
- [ ] 3: `missing` を採用記録に残すかの決定（契約変更の是非）

## 2026-11-05 の更新

研究ページ 15 枚の一括更新（`ISS-20261105-PUB-038`）で、項目 1 の 4 ページを次のように扱った。
**数値の出所が確認できたものは出所を書き、確認できないものは訂正した。**

| ページ | 旧値 | 現在 | 判断 |
|---|---:|---:|---|
| `research_h4cbh.html` | 56 | 56 | 2026-10-01 の要約 run `20261001T121949Z-google-trends-h4cbh-hhbd` の `summary.average_interest_solo = 56` と一致。週次系列は無いため「再計算はできない」と明記（数値は変えない） |
| `research_hhbd.html` | 33 | 33 | 同 run の `average_interest_solo = 33` と一致。同じく要約のみと明記 |
| `research_thcv.html` | 3.1 | **1.9** | 2026-10-23 の週次系列（`20261023T161929Z-google-trends-thcv-12m`、53 週、平均 1.8868）に訂正。旧値の出所は確認できなかった |
| `research_thc-o.html` | 8.2 | データなし（no data） | 既に 2026-11-04 の更新で no data 表記になっており、0 観測と区別している |

本 issue の「1」に書いた「リポジトリ内のどの記録からも再現できない」は、H4CBH / HHBD については
**要約 run（2026-10-01）が記録していた**ため、週次からは再現できないが記録からは再現できる、が正確である。
THCV は記録が無く、訂正した。

項目 2・3 は未着手のまま（12ヶ月ブロックの生成器は無く、no data の採用記録も未実装）。
ページの変更は `metadata/publication/research-{h4cbh,hhbd,thcv,thc-o}/` の hash 再固定を伴い、
承認は `requires_review` に戻っている。
