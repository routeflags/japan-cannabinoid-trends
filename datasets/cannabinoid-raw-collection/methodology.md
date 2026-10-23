# Methodology

## 1. 研究設計

### 1.1 研究 ID

```
cannabinoid-raw-collection
```

### 1.2 観測期間

| データソース | 観測期間 | 根拠 |
|-------------|---------|------|
| Google Trends（12ヶ月） | 2025-09-28 〜 2026-09-27（旧 8 化合物）/ 2025-10-19 〜 2026-10-18（2026-10-23 取得 3 化合物）（`today 12-m`、週次） | §2.1.3 |
| Google Trends（5年） | 2021-10-10 〜 2026-10-11（2026-10-02〜10-15 の run）/ 2021-10-17 〜 2026-10-18（2026-10-23 再取得 4 化合物）（`today 5-y`、週次） | §2.1.1、§2.1.2 |
| X (Twitter) | 2026-09-01 〜 2026-10-01（主系列）、CBD は 1 年 / 1ヶ月 / latest10 も | 2026-10-02・10-08 の run |
| YouTube | 2026-10-02（7 検索語のスナップショット）、2026-10-08〜09 に追加 | Apify `gJvjeCYNraSfhIaNd` |
| X (Twitter) | 2026-09-01 〜 2026-10-01（主系列）、CBD は 1 年 / 1ヶ月 / latest10 も | 2026-10-02・10-08 の run |
| YouTube | 2026-10-02（7 化合物のスナップショット）、2026-10-08〜09 に追加 | Apify `gJvjeCYNraSfhIaNd` |

### 1.3 対象化合物

この研究が扱うのは **13 化合物**。12ヶ月系列の収集から始まり、5年系列の追加で広がった。

| キーワード | SKOS notation | 分類（`skos:broader`） | 12ヶ月単独 | 5年系列 |
|-----------|----------------|---------|:------:|:------:|
| CBD | `compound_cbd` | major | ✅ | ✅ |
| THC | `compound_thc` | major | ✅ | ✅ |
| CBG | `compound_cbg` | minor | ✅ | ✅ |
| HHC | `compound_hhc` | semisynthetic | ✅ | ✅ |
| THCV | `compound_thcv` | minor | ✅ | ✅ |
| THC-O | `compound_thc_o` | semisynthetic | データなし | ✅ |
| THCH | `compound_thch` | minor | ✅ | ✅ |
| CBN | `compound_cbn` | minor | ✅ | ✅ |
| CRDH | `compound_crdh` | synthetic | サマリーのみ（§2.1.3） | ✅ |
| CRDP | `compound_crdp` | synthetic | ✅ | ✅ |
| H4CBH | `compound_h4cbh` | semisynthetic | ✅ | ✅ |
| HHBD | `compound_hhbd` | semisynthetic | ✅ | ✅ |
| HHCH | `compound_hhch` | synthetic | ✅ | ✅ |

- **「データなし」**: 取得はしたが Google Trends が閾値未満として系列を返さなかった。欠測であって 0 観測ではない。
- **5年系列は 13 化合物すべてが週次 raw を持つ**（§2.1.2）。summary-only だった旧 baseline run（§2.1.1）は raw に残るが、どの化合物の引用元でもない。
- **12ヶ月系列は 11 化合物が週次 raw を持ち、CRDH はサマリーのみ、THC-O は no data**（§2.1.3）。
- 分類は [`metadata/taxonomy/compound-taxonomy.skos.jsonld`](../../metadata/taxonomy/compound-taxonomy.skos.jsonld) の `skos:broader`（major / minor / semisynthetic / synthetic）に従う。
- **CBX はこの研究の対象外**: [`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当する（`gt-summary` の 14 化合物目はそこ由来）。
- 12ヶ月・5年以外に、比較セットと共通スケール比較（`common-scale-*`）と「リキッド」系クエリの run もある（`data/raw/google_trends/`）。

---

## 2. データ収集

### 2.1 Google Trends

**ツール:** google-trends-mcp (npm v0.1.1)、
`python -m collection.core.cli collect --live`（`make collect`）経由

**パラメータ:**
- geo: `JP`
- timeframe: 計画書ごとに `today 12-m` または `today 5-y`（**相対表記**。相対窓は収集時刻で解決されるため、
  絶対窓を [`metadata/windows/`](../../metadata/windows/) に登録して計画書から参照する。§2.1.2 の「窓」を参照）
- 収集語: `metadata/queries/query-registry.json` の `query_id`（例 `cbd-general-ja` = `CBD`）。
  表記は**登録された `canonical_text` のまま送る**（例: THC-O は `THC-O`。`THCO` のような別表記は未検証）。
  プラットフォーム別の収集語一覧（化合物語 13・リキッド 13・オイル 2・アンカー 1）は
  [README の「収集したキーワード」](README.md#収集したキーワード)を正本とする。

**収集内容:**
1. 各クエリの interest_over_time（1 クエリ 1 run。単独系列）
2. 比較セットの compare_terms（2026-10-02・10-05・10-08 の run）
3. 関連クエリの related_queries（旧 SKILL 時代の手順。現在のパイプライン経路では未使用）

**比較セット（2026-10-02 初回収集時）:**
- セットA: CBD, THC, CBG, HHC, THCV
- セットB: THC-O, THCH, CBD オイル, THC オイル, HHC オイル

**注意事項:**
- Google Trends は相対指数（0-100）
- 低ボリュームクエリはデータが返らない場合あり（閾値未満。**欠測であって 0 観測ではない**。§2.1.3）
- 429 エラー時は 2-5 分待機
- 2026-10-08 以前の旧 run は legacy 形状（`records_*.json` のみで `execution` ブロックが無い）。
  2026-10-14 以降の run は `payload.json`（verbatim 応答）+ `records_<term>.json` + `run_metadata.json` +
  `artifact-manifest.json` を持つ（2026-10-23 時点で 16 run。2026-10-12 の「リキッド」系 run はまだ legacy 形状）

### 2.1.1 5年ベースライン（summary-only / raw timeline missing）

- run: `data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/`（2026-10-06 収集、geo JP / `today 5-y`、CBD・THC・CBG・HHC・THCV）
- 本 run は summary JSON（`cbd_5y_summary.json` 等）のみで、週次 raw タイムラインを収蔵していない（summary-only / raw timeline missing）。
  raw は immutable のため本 run には手を加えない。
- 週数 261・5年平均・ピーク値・ピーク日・初出値・最新値は**記録値（observed summary）**であり、
  raw 時系列観測からの独立検証はできない。欠測をゼロ観測に読み替えないこと。
- `20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5年系列は「CBD リキッド」等の別クエリ・別正規化であり、
  bare `CBD` の検証には使えない（`src/processing/gt_statistics.py` の `find_run` も除外する）。
- **本 run を引用する化合物は無い**。各化合物は週次系列の run で置き換え済み（§2.1.2）。旧 run は証跡として残す。
- 原稿利用者向けの注意（外部 THCV 原稿での誤用を受けた恒久ガード）:
  - 本 run の記録値（261 週・平均・ピーク・初出値・最新値）を、週次系列（262 週）の値と混ぜないこと。
    両者は別の run・別の窓の観測であり、週数 261 と 262 の差は run 形状の差に由来する（期間の日数から数え直さないこと）。
  - 「原稿の週次系列は本 run に含まれる」と書かないこと（summary-only であり、系列を収蔵していない）。
  - 機械可読の正本は `docs/audits/gt-summary.json`。各化合物の `shape` / `stats` / `unavailable` を併読し、
    `shape=baseline` の項目が現れたら `unavailable`（`data_period` / `raw_timeline`）を必ず添えること。
    検査は `tests/processing/test_gt_statistics.py` の baseline ガード群が行う。

### 2.1.2 5年系列（週次 raw）

5年系列は 13 化合物すべてが週次 raw を持つ（`ISS-20261012-CBD-004`）。2026-10-14 以降に追加した 5 化合物の run:

| 化合物 | run（`data/raw/google_trends/`） | `window_id` | 週数 | 平均 | ゼロ週 |
|---|---|---|---:|---:|---:|
| CBD | `20261015T205048Z-google-trends-cannabinoid-multi-trends` | `2021-10-10_2026-10-12` | 262 | 34.0229 | 0 |
| THC | `20261023T162500Z-google-trends-thc-5y` | `2021-10-17_2026-10-18` | 262 | 12.4084 | 0 |
| CBG | `20261023T160420Z-google-trends-cbg-5y` | `2021-10-17_2026-10-18` | 262 | 48.1756 | 11 |
| HHC | `20261023T160428Z-google-trends-hhc-5y` | `2021-10-17_2026-10-18` | 262 | 2.4924 | 72 |
| THCV | `20261023T160436Z-google-trends-thcv-5y` | `2021-10-17_2026-10-18` | 262 | 7.4313 | 217 |

- 経路: `collect --live`（`make collect` / `scripts/collection/google-trends-live-guard.py fetch` の時間制限つきラッパ）→
  L1 ゲート通過後に catalog 採用。計画書は `metadata/plans/gt-5y-recollect-*.json`、
  窓は [`metadata/windows/`](../../metadata/windows/)。成果物は verbatim `payload.json` + 解析済み `records_<term>.json`。
- 既存 raw は上書きしない（旧 baseline の summary JSON もそのまま）。
- 作業の詳細・制約・検証結果は [`docs/reports/20261023-gt-5y-recollection.md`](../../docs/reports/20261023-gt-5y-recollection.md)。
- 化合物間で**窓が 1 週ずれる**: `2021-10-10 〜 2026-10-11` の run と `2021-10-17 〜 2026-10-18` の run が混在する。
  `today 5-y` は収集時刻で解決されるため、窓をまたいだ比較はしない（別観測として扱う。相対 timeframe を
  絶対窓に固定できないことは §4.2 と [`docs/specs/gt-boundary-verification.md`](../../docs/specs/gt-boundary-verification.md)）。
- Google Trends は**クエリ単位の相対指数（0-100）**であり、単独系列の平均値を化合物間で比較しないこと。
  共通スケール比較 run（`common-scale-*`）は **12ヶ月にのみ**存在する。5年の共通スケール計測は無いため、
  5年では化合物間比較ができない（`ISS-20261023-GT-009`）。
- 数値の正本は `docs/audits/gt-summary.json`（`processing.cli gt-summary` の生成物）。
  publication ページの 5年ブロックも同じコマンド（`--write`）が書く。
- 残り 8 化合物（CBN・CRDH・CRDP・H4CBH・HHBD・HHCH・THCH・THC-O）の 5年 run は本表には載せず、
  `docs/audits/gt-summary.json` の各エントリの `run_id` / `path` を正本とする。

### 2.1.3 12ヶ月系列（週次 raw）

12ヶ月系列は 11 化合物が週次 raw を持ち、CRDH はサマリーのみ、THC-O は Google Trends が系列を返さない。
収集は `today 12-m` / geo JP、1 化合物 1 run、窓 [`metadata/windows/`](../../metadata/windows/)、
計画書 `metadata/plans/gt-12m-recollect-*.json`。値は各 run の `records_<term>.json` から算出:

| 化合物 | run（`data/raw/google_trends/`） | 観測範囲 | 週数 | 平均 | 非ゼロ週 |
|---|---|---|---:|---:|---:|
| CBD | `20261002T063821Z-google-trends-cbd` | 2025-09-28 〜 2026-09-27 | 53 | 46.8113 | 53 |
| THC | `20261002T063852Z-google-trends-thc` | 同 | 53 | 64.3774 | 53 |
| CBG | `20261002T063924Z-google-trends-cbg` | 同 | 53 | 62.8868 | 53 |
| HHC | `20261002T064008Z-google-trends-hhc` | 同 | 53 | 37.5660 | 32 |
| THCH | `20261002T064118Z-google-trends-thch` | 同 | 53 | 3.0000 | 3 |
| CBN | `20261002T081839Z-google-trends-cbn-12m` | 同 | 53 | 55.6226 | 53 |
| CRDP | `20261002T085022Z-google-trends-crdp-12m` | 同 | 53 | 22.2830 | 18 |
| HHCH | `20261002T094657Z-google-trends-hhch-12m` | 同 | 53 | 3.1321 | 2 |
| THCV | `20261023T161929Z-google-trends-thcv-12m` | 2025-10-19 〜 2026-10-18 | 53 | 1.8868 | 1 |
| H4CBH | `20261023T162128Z-google-trends-h4cbh-12m-r2` | 同 | 53 | 57.8868 | 51 |
| HHBD | `20261023T161921Z-google-trends-hhbd-12m` | 同 | 53 | 52.8491 | 37 |
| CRDH | `20261008T102022Z-google-trends-crdh`（`records_crdh_12m.json`） | — | （53） | （1.9） | （2） |
| THC-O | （catalog せず）`20261023T162326Z-google-trends-thc-o-12m-r3` | — | — | — | — |

- 上の 11 行が**週次系列**（`data` 配列あり）。
- **CRDH は 12ヶ月だけ summary-only**: `records_crdh_12m.json` は `data_points` 53・`avg_12m` 1.9・
  `nonzero_weeks` 2 の**記録値**で、週次系列を収蔵していない（括弧内の値は記録値であり raw からは検算できない）。
  5年側は `20261014T215738Z-google-trends-cannabinoid-multi-trends` の系列があるので、**12ヶ月のみの欠落**。
  再取得するかは未決（owner 判断）。
- **THC-O は no data 応答**。本文は
  “Google Trends returned no data for the given terms and timeframe. Try a broader timeframe or different terms.”
  で、`errors[].code = NO_DATA`（parser の `no_data` 規則、`docs/specs/gt-boundary-verification.md` §4.4）として記録する。
  `status=failed` のため L1 は **quarantine** に置き catalog しない。すなわちこの欠測は「収集失敗」ではなく
  「**ソースが系列を返さない**」だが、パイプラインに「no data を採用記録として残す」状態が無いのが現状
  （`ISS-20261023-GT-006`）。0 観測ではない。
- 採用されなかった run（`PARSE_FAILED` / `NO_DATA`）は `.quarantine/` に残る（Git 管理外）。catalog には入らない。
- **公開ページの 12ヶ月平均は収蔵系列と一致しない**:

  | ページ | 記載の 12ヶ月平均 | 収蔵系列 |
  |---|---:|---|
  | `research_h4cbh.html` | 56 | 57.8868 |
  | `research_hhbd.html` | 33 | 52.8491 |
  | `research_thcv.html` | 3.1 | 1.8868 |
  | `research_thc-o.html` | 8.2 | 系列なし（NO_DATA） |

  12ヶ月ブロックは手書きで、`gt-summary --write` は 5年ブロックしか置換しない。数値の訂正と生成器追加は
  `ISS-20261023-GT-006`（本 doc はページを書き換えない。公開内容の変更は審査対象）。
- 2 つの収集バッチで**窓が違う**（2025-09-28〜 vs 2025-10-19〜）。窓をまたいだ 12ヶ月同士の比較はしないこと。
- 12ヶ月側には 5年側の [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json) に相当する機械可読レポートが無い
  （`gt-summary --timeframe 12m` はレポートを出せるが `--write` は 5年のみ。`ISS-20261023-GT-006` §2）。

### 2.1.4 5年の共通スケール（週次、`compare_terms`）

5年の単独系列は各語のピーク=100 に正規化されるため、化合物間比較ができない（`ISS-20261023-GT-009`）。
そこで `compare_terms` で**アンカー（CBD, THC）を含む 4 セット**を取得し、共通スケールの週次系列を持たせた。

| セット | run（`data/raw/google_trends/`） | 語 | 平均（共通スケール） |
|---|---|---|---|
| A | `20261023T171700Z-google-trends-5y-common-scale-setA` | CBD, THC, CBG, HHC, THCV | CBD 33 / THC 5 / CBG 1 / HHC 2 / THCV 0 |
| B | `20261023T171709Z-google-trends-5y-common-scale-setB` | CBD, THC, THCH, CBN, CRDH | CBD 33 / THC 5 / THCH 2 / CBN 5 / CRDH 0 |
| C | `20261023T171717Z-google-trends-5y-common-scale-setC` | CBD, THC, CRDP, H4CBH, HHBD | CBD 33 / THC 5 / CRDP 0 / H4CBH 0 / HHBD 0 |
| D | `20261023T171726Z-google-trends-5y-common-scale-setD` | CBD, THC, HHCH, THC-O | CBD 33 / THC 5 / HHCH 1 / THC-O 0 |

- 窓は `2021-10-17_2026-10-18`（262 週）、geo JP、`today 5-y`。計画書は `metadata/plans/gt-5y-common-scale-set{A..D}.json`。
- **アンカー（CBD 33・THC 5）が 4 セットで一致**しているので、セット間を橋渡しできる（各語はアンカー経由で同じスケールに載る）。
- 成果物は verbatim `payload.json` + 共通スケール文書 `comparison_<terms>.json`（schema `google-trends-comparison-v1`）。
- **単独系列の平均とは比較しない**（別の正規化）。化合物間比較はこの共通スケール内でのみ行う。
- 平均が 0 の語（THCV・CRDH・CRDP・H4CBH・HHBD・THC-O）は、262 週のうち非ゼロがごく少ない語である。0 観測ではない。

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

### 4.1 検証（実行するコマンド）

採用は「ゲートを通った run だけを catalog する」運用（`AGENTS.md` Production Entry Points）。
手作業のチェックリストではなく、次のコマンドが検証の実行点である。数値の正本は各出力ファイル（と `raw/`）。

| 何を確かめるか | 実行 | 出力 |
|---|---|---|
| run の採用可否（構造・意味・欠測・成果物整合） | `validation.cli gate-run --file <run_metadata.json>`（`collect` / `adopt` の内部で自動実行） | 非 0 なら `.quarantine/`（採用しない） |
| 値の範囲（相対指数 0-100） | parser の `value_out_of_range`（`collection.adapters.google_trends.boundary`） | 範囲外の応答は系列にしない |
| クエリの登録照合 | `validation.cli audit-queries` | `docs/audits/g2-query-inventory.json` |
| 時系列と窓の記録 | `validation.cli audit-temporal` | `docs/audits/g3-temporal-inventory.json` |
| 成果物と run の対応 | `validation.cli audit-artifacts` | `docs/audits/g4-storage-inventory.json` |
| 公開契約（PC-1〜PC-8） | `validation.cli audit-publication` | `docs/audits/publication-contract.json` |
| 研究カタログ（study / run の可発見性） | `research.cli audit-studies` | `docs/audits/g7-study-inventory.json` |
| スナップショットの鮮度 | `pytest tests/validation/test_audit_report_freshness.py` | — |
| 全体 | `pytest -q` | — |

自動化されていない項目（手作業で確認する）: X のシャドウバンによる 0 件、キーワードの含有率、
API のコスト実績。X raw は Git 管理外のため、run の件数はローカル証跡でしか確認できない。

### 4.2 制約事項

| 制約 | 対策 |
|------|------|
| Google Trends 相対指数 | 絶対検索数ではない点を明記 |
| Google Trends の窓は相対表記 | `today 5-y` / `today 12-m` は収集時刻で解決される（`exact_window_match=false`）。窓ごとに `window_id` を切り、run 間で窓が違えば別観測として扱う（§2.1.2・§2.1.3） |
| 閾値未満で系列が返らない語 | `status=failed` + `errors[].code=NO_DATA` として記録し、0 観測に読み替えない。現行契約では採用記録にできず quarantine 止まり（`ISS-20261023-GT-006`） |
| X シャドウバン | 0 件でも observed_zero として記録 |
| 多義語（CBD, THC） | コンテキスト分析で誤検知を排除 |
| ソース間の比較 | 単位が異なるため直接比較不可 |

---

## 5. 局所化

### 5.1 関連研究

| Study ID | 関係 |
|----------|------|
| cannabinoid-platform-trends | 本 study の素材から作る**配布物**（Google Trends + YouTube の集計表） |
| cbx-search-trends | CBX/H4CBH/HHBD の検索需要（本 study は CBX を対象外とする） |
| cbx-social-trends | CBX の SNS 言及（規制前後の比較） |
| cbx-liquid-online-trend | CBX リキッドの週次データ |

### 5.2 既存インフラ

- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
- 検証スクリプト: `scripts/validation/validate-data-schema.sh`
- エクスポート: `scripts/export/`

## 6. 研究軸の分離（2026-10-12 追記）

cbx-search-trends は CBX 製品軸（CBX リキッド等の製品需要）の研究であり、cannabinoid-raw-collection は成分横断軸（CBD・THC・CBG・CBN・HHC 等の成分間比較）の研究である。両者は観測対象の軸が異なるため、クエリー設計・比較スケール・解釈を分離する。日本語「○○ リキッド」拡張（GTJA-20261012）は成分横断軸に属し、CBX は比較のアンカー語としてのみ用いる。
