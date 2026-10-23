# Methodology

## 1. 研究設計

### 1.1 研究 ID

```
cannabinoid-raw-collection
```

### 1.2 観測期間

| データソース | 観測期間 | 根拠 |
|-------------|---------|------|
| Google Trends（12ヶ月・単独） | 2025-10 〜 2026-10（`today 12-m`） | 2026-10-02 初回収集 |
| Google Trends（5年） | 2021-10-10 〜 2026-10-11（旧 10 run）/ 2021-10-17 〜 2026-10-18（2026-10-23 再取得 4 run）（`today 5-y`、週次） | 2026-10-02〜2026-10-23 の複数 run（§2.1.1、§2.1.2） |
| X (Twitter) | 2026-09-01 〜 2026-10-01（主系列）、CBD は 1 年 / 1ヶ月 / latest10 も | 2026-10-02・10-08 の run |
| YouTube | 2026-10-02（7 化合物のスナップショット）、2026-10-08〜09 に追加 | Apify `gJvjeCYNraSfhIaNd` |

### 1.3 対象化合物（2026-10-24 更新）

この研究が扱うのは **13 化合物**。当初は下記の「12ヶ月収集」7 化合物だけだったが、5年系列と 12ヶ月系列の追加収集（2026-10-23 に 4 化合物ずつ）で広がった。

| キーワード | SKOS notation | 分類（`skos:broader`） | 12ヶ月単独 | 5年系列 |
|-----------|----------------|---------|:------:|:------:|
| CBD | `compound_cbd` | major | ✅ | ✅（2026-10-15 再取得） |
| THC | `compound_thc` | major | ✅ | ✅（2026-10-23 再取得） |
| CBG | `compound_cbg` | minor | ✅ | ✅（2026-10-23 再取得） |
| HHC | `compound_hhc` | semisynthetic | ✅ | ✅（2026-10-23 再取得） |
| THCV | `compound_thcv` | minor | ✅（2026-10-23 再取得） | ✅（2026-10-23 再取得） |
| THC-O | `compound_thc_o` | semisynthetic | データなし（2026-10-23 再確認） | ✅ |
| THCH | `compound_thch` | minor | ✅ | ✅ |
| CBN | `compound_cbn` | minor | ✅ | ✅ |
| CRDH | `compound_crdh` | synthetic | ✅ | ✅ |
| CRDP | `compound_crdp` | synthetic | ✅ | ✅ |
| H4CBH | `compound_h4cbh` | semisynthetic | ✅（2026-10-23 追加） | ✅ |
| HHBD | `compound_hhbd` | semisynthetic | ✅（2026-10-23 追加） | ✅ |
| HHCH | `compound_hhch` | synthetic | ✅ | ✅ |

- **「データなし」**: 取得はしたが Google Trends が閾値未満として系列を返さなかった（旧 run `…-nodata`、または 2026-10-23 の `NO_DATA` 応答 §2.1.3）。欠測であって 0 観測ではない。
- **5年系列は 13 化合物すべてが週次 raw を持つ**（2026-10-23 完了）。summary-only だった旧 baseline run（§2.1.1）は raw に残るが、どの化合物の引用元でもない。
- **12ヶ月系列は 12 化合物が週次 raw を持ち、1 化合物（THC-O）は Google Trends が no data を返す**（§2.1.3）。
- 分類は [`metadata/taxonomy/compound-taxonomy.skos.jsonld`](../../metadata/taxonomy/compound-taxonomy.skos.jsonld) の `skos:broader`（major / minor / semisynthetic / synthetic）に従う。
- **CBX はこの研究の対象外**: [`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当する（`gt-summary` の 14 化合物目はそこ由来）。
- 12ヶ月・5年以外に、比較セットと共通スケール比較（`common-scale-*`）と「リキッド」系クエリの run もある（`data/raw/google_trends/`）。

---

## 2. データ収集

### 2.1 Google Trends

**ツール:** google-trends-mcp (npm v0.1.1)

**パラメータ:**
- geo: `JP`
- timeframe: `today 12-m`

**収集内容:**
1. 各キーワードの interest_over_time（単独）
2. 比較セットの compare_terms
3. 関連クエリの related_queries

**比較セット:**
- セットA: CBD, THC, CBG, HHC, THCV
- セットB: THC-O, THCH, CBD オイル, THC オイル, HHC オイル

**注意事項:**
- Google Trends は相対指数（0-100）
- 低ボリュームクエリはデータが返らない場合あり
- 429 エラー時は 2-5 分待機

### 2.1.1 5年ベースライン（summary-only / raw timeline missing）

- run: `data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/`（2026-10-06 収集、geo JP / `today 5-y`、CBD・THC・CBG・HHC・THCV）
- 本 run は summary JSON（`cbd_5y_summary.json` 等）のみで、週次 raw タイムラインを収蔵していない（summary-only / raw timeline missing）。
  raw は immutable のため本 run には手を加えない。
- 週数 261・5年平均・ピーク値・ピーク日・初出値・最新値は**記録値（observed summary）**であり、
  raw 時系列観測からの独立検証はできない。欠測をゼロ観測に読み替えないこと。
- `20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5年系列は「CBD リキッド」等の別クエリ・別正規化であり、
  bare `CBD` の検証には使えない（`src/processing/gt_statistics.py` の `find_run` も除外する）。
- **2026-10-23 時点で、本 run を引用する化合物は無い**。CBD は 2026-10-15、THC・CBG・HHC・THCV は
  2026-10-23 に、それぞれ週次系列の run を新規収集して置き換えた（§2.1.2）。旧 run は証跡として残す。
- 原稿利用者向けの注意（2026-10-16 追記。外部 THCV 原稿 v1.9 での誤用 E1・E2 を受けた恒久ガード）:
  - 本 run の記録値（261 週・平均・ピーク・初出値・最新値）を、週次系列（262 週）の値と混ぜないこと。
    両者は別の run・別の窓の観測であり、週数 261 と 262 の差は run 形状の差に由来する（期間の日数から数え直さないこと）。
  - 「原稿の週次系列は本 run に含まれる」と書かないこと（summary-only であり、系列を収蔵していない）。
  - 機械可読の正本は `docs/audits/gt-summary.json`。各化合物の `shape` / `stats` / `unavailable` を併読し、
    `shape=baseline` の項目が現れたら `unavailable`（`data_period` / `raw_timeline`）を必ず添えること。
    検査は `tests/processing/test_gt_statistics.py` の baseline ガード群が行う。

### 2.1.2 5年系列（週次 raw）

2026-10-23 に、summary-only だった 4 化合物（THC・CBG・HHC・THCV）の週次系列をライブ収集し、
**5年系列を 13 化合物すべてが週次 raw を持つ状態**にした（CBD は 2026-10-15 に完了、`ISS-20261012-CBD-004`）。

| 化合物 | run（`data/raw/google_trends/`） | 収集 | `window_id` | 週数 | 平均 | ゼロ週 |
|---|---|---|---|---:|---:|---:|
| CBD | `20261015T205048Z-google-trends-cannabinoid-multi-trends` | 2026-10-15 | `2021-10-10_2026-10-12` | 262 | 34.0229 | 0 |
| THC | `20261023T162500Z-google-trends-thc-5y` | 2026-10-23 | `2021-10-17_2026-10-18` | 262 | 12.4084 | 0 |
| CBG | `20261023T160420Z-google-trends-cbg-5y` | 2026-10-23 | `2021-10-17_2026-10-18` | 262 | 48.1756 | 11 |
| HHC | `20261023T160428Z-google-trends-hhc-5y` | 2026-10-23 | `2021-10-17_2026-10-18` | 262 | 2.4924 | 72 |
| THCV | `20261023T160436Z-google-trends-thcv-5y` | 2026-10-23 | `2021-10-17_2026-10-18` | 262 | 7.4313 | 217 |

- 経路: `collect --live`（`make collect` / `scripts/collection/google-trends-live-guard.py fetch` の時間制限つきラッパ）→
  L1 ゲート通過後に catalog 採用。計画書は `metadata/plans/gt-5y-recollect-{thc,cbg,hhc,thcv}.json`、
  窓は [`metadata/windows/2021-10-17_2026-10-18.json`](../../metadata/windows/2021-10-17_2026-10-18.json)。
  成果物は CBD と同じ 2 点セット（verbatim `payload.json` + 解析済み `records_<term>.json`）。
- 既存 raw は上書きしない。旧 baseline の summary JSON も残したまま、各化合物を**新規 run** として追加した（`raw/` は不変）。
- 作業の詳細・制約・検証結果は [`docs/reports/20261023-gt-5y-recollection.md`](../../docs/reports/20261023-gt-5y-recollection.md)。
- **窓が 1 週ずれる**: 2026-10-23 の `today 5-y` は `2021-10-17 〜 2026-10-18` に解決され、
  2026-10-15 収集分（`2021-10-10 〜 2026-10-11`）とは 1 週ずれる。同一窓で取り直したのではなく、
  **別窓の観測**として扱う（相対 timeframe を絶対窓に固定できないことは §4.2 と
  [`docs/specs/gt-boundary-verification.md`](../../docs/specs/gt-boundary-verification.md)）。
- Google Trends は**クエリ単位の相対指数（0-100）**であり、平均値の水準を化合物間で比較しないこと。
  化合物間の比較は共通スケール比較 run（`common-scale-*`）が担う。
- 数値の正本は `docs/audits/gt-summary.json`（`processing.cli gt-summary` の生成物）。
  publication ページの 5年ブロックも同じコマンド（`--write`）が書く。

### 2.1.3 12ヶ月系列（週次 raw、2026-10-23 追加）

12ヶ月系列は 2026-10-02 の収集では 7 化合物分しかなく、THCV・THC-O は nodata、H4CBH・HHBD は未収集だった。
2026-10-23 に 4 化合物を再取得した（`today 12-m`、geo JP、窓
[`metadata/windows/2025-10-19_2026-10-18.json`](../../metadata/windows/2025-10-19_2026-10-18.json)、
計画書 `metadata/plans/gt-12m-recollect-{thcv,thc-o,h4cbh,hhbd}.json`）。

| 化合物 | run（`data/raw/google_trends/`） | 結果 | 週数 | 平均 | 非ゼロ週 |
|---|---|---|---:|---:|---:|
| HHBD | `20261023T161921Z-google-trends-hhbd-12m` | success | 53 | 52.8491 | 37 |
| THCV | `20261023T161929Z-google-trends-thcv-12m` | success | 53 | 1.8868 | 1 |
| H4CBH | `20261023T162128Z-google-trends-h4cbh-12m-r2` | success | 53 | 57.8868 | 51 |
| THC-O | （catalog せず）`20261023T162326Z-google-trends-thc-o-12m-r3` | **NO_DATA** | — | — | — |

- 観測範囲は 3 run とも `2025-10-19 〜 2026-10-18`（登録窓と一致、53 週）。
- **THC-O は Google Trends が no data を返した**。応答本文は
  “Google Trends returned no data for the given terms and timeframe. Try a broader timeframe or different terms.”
  で、`errors[].code = NO_DATA` として記録する（§2.1.3 追記の parser 規則 `no_data`）。
  `status=failed` のため L1 は **quarantine** に置き catalog しない（`.quarantine/` は Git 管理外）。
  すなわち THC-O の 12ヶ月欠測は「収集失敗」ではなく「**ソースが系列を返さない**」だが、
  パイプラインに「no data を採用済み記録として残す」状態が無いのが現状（`ISS-20261023-GT-006`）。
- **古い版の再取得失敗も記録に残す**: 2026-10-23 の 1 回目の H4CBH・THC-O は parser が応答を解釈できず
  `PARSE_FAILED` で quarantine になった（当時の実装は解釈失敗時に**応答本文を捨てていた**）。
  本文を保全するよう `collect()` を直した後、H4CBH は 2 回目で成功し、THC-O は本文が no data と判明した。
  失敗した run は `.quarantine/` に残している（Git 管理外、raw は不変）。
- **公開ページの 12ヶ月平均はこの系列と一致しない**（2026-10-23 実測）:

  | ページ | 記載の 12ヶ月平均 | 今回の系列 |
  |---|---:|---|
  | `research_h4cbh.html` | 56 | 57.8868 |
  | `research_hhbd.html` | 33 | 52.8491 |
  | `research_thcv.html` | 3.1 | 1.8868 |
  | `research_thc-o.html` | 8.2 | 系列なし（NO_DATA） |

  ページの 12ヶ月ブロックは手書きで、`processing.cli gt-summary` は 5年ブロックしか生成しない
  （`--write` の置換対象も 5年のみ）。数値の訂正と 12ヶ月ブロックの生成器追加は `ISS-20261023-GT-006`。
  本作業では**ページの 12ヶ月数値を書き換えていない**（公開内容の変更は審査対象）。

### 2.2 X (Twitter)

**ツール:** Apify Actor `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search)

**パラメータ:**
- section: `latest`
- maxPages: 2-3（キーワードに依存）
- query: `{keyword} since:2026-09-01 until:2026-10-01`

**収集キーワード:**

| キーワード | maxPages | コスト目安 |
|-----------|----------|-----------|
| CBD | 3 | $0.152 |
| THC | 3 | $0.152 |
| CBG | 2 | $0.077 |
| HHC | 2 | $0.077 |
| THCV | 2 | $0.077 |
| THC-O | 2 | $0.052 |
| THCH | 2 | $0.052 |

**注意事項:**
- シャドウバンの可能性（THC 等の敏感キーワード）
- 0 件でも observed_zero として記録
- chargedEventCounts を信用せず、records.json の件数を確認

### 2.3 YouTube

**ツール:** Apify Actor `gJvjeCYNraSfhIaNd` (danek/youtube-search)

**パラメータ:**
- max_videos: 50-100（キーワードに依存）

**収集キーワード:**

| キーワード | max_videos | コスト目安 |
|-----------|-----------|-----------|
| CBD | 100 | $0.050 |
| THC | 100 | $0.050 |
| CBG | 50 | $0.025 |
| HHC | 50 | $0.025 |
| THCV | 50 | $0.025 |
| CBD オイル | 50 | $0.025 |
| THC オイル | 50 | $0.025 |

**注意事項:**
- ページング重複あり、videoId で重複排除必須
- timestamp は相対表記（"3 days ago" 等）

---

## 3. データ処理

### 3.1 重複排除

| ソース | キー | 方法 |
|--------|------|------|
| X | tweet_id | ユニーク ID で重複排除 |
| YouTube | videoId | ユニーク ID で重複排除 |
| Google Trends | date | 週次データで重複なし |

### 3.2 分類

SKOS Concept ID を使用して化合物カテゴリを分類。

### 3.3 匿名化（X データ）

正本は `docs/data-dictionary.md` の匿名化マッピング。実行規則は
`src/processing/anonymize.py` にあり、`cbx-social-trends` の匿名化済み成果物に対して
列単位で検証されている。

| 元フィールド | 匿名化後 | 方法 |
|-------------|---------|------|
| `screen_name` | `author_id` | 初出順の連番 ID（`author_001` 等）に置換。**ハッシュではない** |
| `author_name` | （削除） | 個人情報のため削除 |
| `text` | `text_length` | 文字数のみ保持、本文は削除 |
| `tweet_id` | `tweet_id_hash` | SHA-256 ハッシュの**先頭 16 文字** |
| `url` | （削除） | 個人情報のため削除 |

> **2026-10-13 訂正:** 本表は以前「`screen_name` → `author_id` はハッシュ化」と
> 記載していたが誤り。実成果物の `author_id` は初出順の連番である。また
> `tweet_id_hash` は SHA-256 全長ではなく先頭 16 文字である。本 study は X raw を
> リポジトリに保持していないため、この変換の適用先成果物は
> `cbx-social-trends` 側にある。

---

## 4. 品質管理

### 4.1 検証項目

- [ ] Google Trends スコア範囲（0-100）
- [ ] X/YouTube 件数確認
- [ ] キーワード含有率確認
- [ ] コスト実績確認

### 4.2 制約事項

| 制約 | 対策 |
|------|------|
| Google Trends 相対指数 | 絶対検索数ではない点を明記 |
| Google Trends の窓は相対表記 | `today 5-y` は収集時刻で解決される（`exact_window_match=false`）。窓ごとに `window_id` を切り、run 間で窓が違えば別観測として扱う（§2.1.2） |
| X シャドウバン | 0 件でも observed_zero として記録 |
| 多義語（CBD, THC） | コンテキスト分析で誤検知を排除 |
| コソソース間の比較 | 単位が異なるため直接比較不可 |

---

## 5. 局所化

### 5.1 関連研究

| Study ID | 関係 |
|----------|------|
| cbx-search-trends | CBX/H4CBH/HHBD の検索需要 |
| cbx-social-trends | CBX の SNS 言及 |
| cbx-liquid-online-trend | CBX リキッドの週次データ |

### 5.2 既存インフラ

- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
- 検証スクリプト: `scripts/validation/validate-data-schema.sh`
- エクスポート: `scripts/export/`

## 6. 研究軸の分離（2026-10-12 追記）

cbx-search-trends は CBX 製品軸（CBX リキッド等の製品需要）の研究であり、cannabinoid-raw-collection は成分横断軸（CBD・THC・CBG・CBN・HHC 等の成分間比較）の研究である。両者は観測対象の軸が異なるため、クエリー設計・比較スケール・解釈を分離する。日本語「○○ リキッド」拡張（GTJA-20261012）は成分横断軸に属し、CBX は比較のアンカー語としてのみ用いる。
