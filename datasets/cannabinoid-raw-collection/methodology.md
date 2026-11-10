# Methodology

## 1. 研究設計

### 1.1 研究 ID

```
cannabinoid-raw-collection
```

### 1.2 観測期間

| データソース | 観測期間 | 根拠 |
|-------------|---------|------|
| Google Trends（12ヶ月） | 2025-09-28 〜 2026-09-27（8 化合物）/ 2025-10-19 〜 2026-10-18（THCV・H4CBH・HHBD・CRDH）/ 2025-10-12 〜 2026-10-11（CBX）/ 2025-11-02 〜 2026-11-01（THCNM）。CBX bridge（3 語の共通スケール）は 2025-11-02 〜 2026-11-01 | §2.1.3、§2.1.6 |
| Google Trends（5年） | 2021-10-10 〜 2026-10-11（10 化合物。CBX を含む）/ 2021-10-17 〜 2026-10-18（THC・CBG・HHC・THCV、および共通スケール setA〜D）/ 2021-10-31 〜 2026-11-01（THCNM、および CBX bridge）。リキッドは main5 の 5 語が 2021-10-10 〜 2026-10-11、新規 7 語が 2021-10-17 〜 2026-10-18（THC-O は系列なし） | §2.1.2、§2.1.4、§2.1.6 |
| X (Twitter) | 2026-09-01 〜 2026-10-01（主系列、7 語）。CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run（2026-10-08）もある（§2.2） | §2.2 |
| YouTube | 2026-10-10 / 10-11 / 11-01 / 11-04。primary のリキッド 17 run（15 化合物、観測窓は run ごとに異なる。primary の全体の包絡は 2008-08-01 〜 2026-11-04）+ primary 外の裸語 `HHC` 1 run（2006-09-05 〜 2026-11-02） | §2.3 |

### 1.3 対象化合物

Google Trends は **収集済み 15 化合物すべてがこの study 自身の raw** である。CBX は 2026-11-04 の owner 決定で `cbx-search-trends` から所有を移管した（単独系列 5年・12ヶ月と boundary probe 4、2026-10-01 の legacy 4。§2.1.6）。YouTube は 2026-11-01 の owner 決定により **15 化合物すべて**がこの study の own raw（liquid-only primary）である。2026-11-04 に **THCNM（別名 THA）を 15 番目の化合物**として宣言に加え、同日 **Google Trends の初回 run（12ヶ月・5年）と YouTube の 2 本の required primary query（`THCNM リキッド` / `THA リキッド`）を採用した**。YouTube primary は化合物 15/15・クエリ 16/16。

2026-11-10 に **CBC と CBDV を登録化合物集合に加え**、**登録化合物は 17 になった**。両者は taxonomy に既存の canonical concept（`compound_cbc` / `compound_cbdv`）があるためその ID を再利用し、query を登録しただけで**まだ 1 run も収集していない**。したがって下の Google Trends 被覆は「収集済み 15 化合物」の値であり、登録 17 化合物の被覆ではない。

| 範囲 | 5年 | 12ヶ月 |
|---|---:|---:|
| own raw（収集済み 15 化合物） | 15/15 | 14/15（THC-O は no data） |
| 登録済み・未収集（CBC・CBDV） | 未収集（run 0） | 未収集（run 0） |

CBX を化合物集合に含めるかと、CBX の Google Trends raw をどちらが所有するかは [`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md) の決定事項である。2026-11-04 の owner 決定で **CBX の Google Trends raw もこの study が所有する**（§2.1.6）。YouTube の所有は [`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md) が記録する。

| No. | キーワード | SKOS notation | 分類（`skos:broader`） | 12ヶ月単独 | 5年系列 |
|---:|-----------|----------------|---------|:------:|:------:|
| 1 | CBX | `compound_cbx` | minor | ✅ | ✅ |
| 2 | CBD | `compound_cbd` | major | ✅ | ✅ |
| 3 | THC | `compound_thc` | major | ✅ | ✅ |
| 4 | CBG | `compound_cbg` | minor | ✅ | ✅ |
| 5 | HHC | `compound_hhc` | semisynthetic | ✅ | ✅ |
| 6 | THCV | `compound_thcv` | minor | ✅ | ✅ |
| 7 | THC-O | `compound_thc_o` | semisynthetic | データなし | ✅ |
| 8 | THCH | `compound_thch` | minor | ✅ | ✅ |
| 9 | CBN | `compound_cbn` | minor | ✅ | ✅ |
| 10 | CRDH | `compound_crdh` | synthetic | ✅ | ✅ |
| 11 | CRDP | `compound_crdp` | synthetic | ✅ | ✅ |
| 12 | H4CBH | `compound_h4cbh` | semisynthetic | ✅ | ✅ |
| 13 | HHBD | `compound_hhbd` | semisynthetic | ✅ | ✅ |
| 14 | HHCH | `compound_hhch` | synthetic | ✅ | ✅ |
| 15 | THCNM（別名 THA） | `compound_thcnm` | semisynthetic（暫定） | ✅ | ✅ |
| 16 | CBC | `compound_cbc` | minor | 未収集 | 未収集 |
| 17 | CBDV | `compound_cbdv` | minor | 未収集 | 未収集 |

- **「データなし」**: 取得はしたが Google Trends が閾値未満として系列を返さなかった。欠測であって 0 観測ではない。
- **「未収集」**: その化合物をそのソースで収集していない（run 0）。0 観測でも欠測でもない。**現在この状態なのは 2026-11-10 に登録した CBC・CBDV の query（Google Trends と YouTube）だけ**で、2026-11-04 までに宣言した 16 本の YouTube primary query には全て adopted run がある。
- **THCNM の系列が測っているもの**: 登録 `canonical_text`（Google Trends は `THCNM`）に一致する検索需要であり、同定された物質の存在ではない。同一性が未確認の間、本系列の解釈はこの限界に拘束される（下の同じ identity 注記）。
- **THCNM の同一性と分類**: `skos:broader` は `compound_semisynthetic`（暫定）。供給元・市場の記載は 2 通りあり（`Tetrahydrocannabinol-N-methyl` / `1′-Dimethyl-Δ9-THCH`）、いずれも「フィトカンナビノイドを化学修飾した置換誘導体」を記述しているため、`compound_synthetic`（天然対応物を持たない）ではなく半合成に置いた。**構造の検証結果ではなく、未確認の同一性に基づく暫定配置**である（[`ISS-20261104-TAX-028`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thcnm-identity-unconfirmed.md)）。`THA` は同じ化合物の別名・商業名として登録し、別物質とも同一物質とも断定しない。外部識別子（CAS / ChEBI / Wikidata）は記録していない。
- **CBC・CBDV の追加（2026-11-10）**: taxonomy に既存の canonical concept（`compound_cbc` = Cannabichromene / `compound_cbdv` = Cannabidivarin、いずれも `compound_minor` 配下で Wikidata `exactMatch` 付き）を再利用し、query registry に `cbc-general-ja` / `cbc-liquid-ja` / `cbdv-general-ja` / `cbdv-liquid-ja` を登録した。**run は 0 本で未収集**。分類は taxonomy の既存 `skos:broader` をそのまま写し、新しい分類判断をしていない。`CBC` はカナダ放送協会など化合物以外の略号と衝突するため、登録文字列は物質の同定ではない（[`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)）。
- **5年系列は収集済み 15 化合物すべてが週次 raw を持つ**（§2.1.2）。summary-only だった旧 baseline run（§2.1.1）は raw に残るが、どの化合物の引用元でもない。
- **12ヶ月系列は own raw 14 化合物が週次 raw を持ち、THC-O は no data**（§2.1.3）。CRDH の旧 summary（`records_crdh_12m.json`）は証跡として残るが、正本は週次系列の run。
- 分類は [`metadata/taxonomy/compound-taxonomy.skos.jsonld`](../../metadata/taxonomy/compound-taxonomy.skos.jsonld) の `skos:broader`（major / minor / semisynthetic / synthetic）に従う。
- **CBX の Google Trends は 2026-11-04 から own raw**: 12ヶ月・5年の正本は `data/raw/google_trends/20261015T042853Z-google-trends-boundary-12m` / `20261015T042857Z-google-trends-boundary-5y`。これらは `cbx-search-trends` から run id と payload バイトを変えずに移管したもので、観測のやり直しではない（§2.1.6）。YouTube の CBX リキッド run はこの study の own raw である。
- 12ヶ月・5年以外に、比較セット（12ヶ月 `common-scale-*` / 5年 `5y-common-scale-set*` / CBX bridge の `comparison_cbx-cbd-thc.json`）と「リキッド」系クエリの run もある（`data/raw/google_trends/`）。
- THC-O の**表記ゆれ** `THCO` / `THCO リキッド` は canonical の被覆数に含めない別観測である（§2.1.5）。canonical `THC-O` の 12ヶ月 no data・5年系列はそのまま正本。

### 1.4 地理スコープ（ソース別）

| ソース | API の geo filter | 観測の限定方法 | 限界 |
|---|---|---|---|
| Google Trends | あり（`geo=JP`） | 検索需要を日本に明示的に限定 | 相対指数であり検索数の絶対値ではない |
| X (Twitter) | なし | なし（採用済み run の記録は `{keyword} since:... until:...` のみ。geo / language filter は記録されていない） | 国も言語も保証しない。日本語の海外投稿・非日本語の国内投稿を分離できない |
| YouTube | なし（Actor input に geo パラメータがない） | 日本語の製品語「リキッド」による**検索語ベースの近似的な日本市場限定** | geo 保証ではない。日本語の海外向けコンテンツ・非日本語の国内向けコンテンツを分離できない |

- Google Trends だけが明示的な国指定を持つ。X / YouTube の観測を「日本国内の件数」と書かない。
- YouTube の primary 語を `<compound> リキッド` に限定する理由の一つがこの近似である（§2.3）。裸の化合物語はこの近似を持たない。
- `config/collectors.json` の `geo_filter: unknown` は「能力が未測定」という意味であり、「geo 制限がある」という主張ではない。実際の入力に geo パラメータはない。

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
  通常は**登録された `canonical_text` のまま送る**（例: THC-O は `THC-O`）。
  表記ゆれは `metadata/queries/query-variants.json` に登録した variant だけを、
  canonical の `query_id` を変えずに `query.text` として送る別 run にする（§2.1.5）。
  プラットフォーム別の収集語一覧（化合物語 13・リキッド 13・オイル 2・アンカー 1）は
  [README の「収集したキーワード」](README.md#収集したキーワード)を正本とする。

**収集内容:**
1. 各クエリの interest_over_time（1 クエリ 1 run。単独系列）
2. 比較セットの compare_terms（§2.1.4 と下記「比較セット」）
3. 関連クエリの related_queries（旧 SKILL 時代の手順。現在のパイプライン経路では未使用）

**比較セット（`compare_terms`）:**

- 12ヶ月の比較セットは 3 日付に分かれる。
  - 2026-10-02 `comparison_setA` = CBD, THC, CBG, HHC, THCH（1 run）
  - 2026-10-05 `common-scale-expansion` = setB（CBN, CRDP, HHCH, THC-O, THCV）/ setC（CBN, CBG, CBD）/
    setD（H4CBH, HHBD, CRDP）（1 run に 3 比較）
  - 2026-10-08 `common-scale-crdh`（CRDH, CBD, THC）/ `common-scale-thch`（THCH, CBD, THC）/
    `common-scale-missing`（H4CBH, HHBD, CRDH）
- 12ヶ月のリキッド: 2026-10-12 の 3 run（phase-a と phase-a-repeat の `ja1`、phase-b の `ja2`〜`ja4`。
  `CBX リキッド` をアンカーに含む）と、同表記の事前調査 1 run。
- 5年: 2026-10-23 の setA〜D（§2.1.4）。
- 比較セットの値は**同一 run 内での相対値**（その run の最大語が 100）。run をまたいで数値を比べない。

**注意事項:**
- Google Trends は相対指数（0-100）
- 低ボリュームクエリはデータが返らない場合あり（閾値未満。**欠測であって 0 観測ではない**。§2.1.3）
- 429 エラー時は 2-5 分待機
- 2026-10-12 以前の run は legacy 形状（`records_*.json` のみで `execution` ブロックが無い）。
  2026-10-14 以降の run（5年再取得・12ヶ月再取得・5年共通スケール）は `payload.json`（verbatim 応答）+
  `records_<term>.json` + `run_metadata.json` + `artifact-manifest.json` を持つ

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

5年系列は収集済み 15 化合物すべてが週次 raw を持つ（`ISS-20261012-CBD-004`）。CBX の正本 run は `20261015T042857Z-google-trends-boundary-5y`（2026-11-04 に `cbx-search-trends` から所有を移管。§2.1.6）で、観測範囲 2021-10-10 〜 2026-10-11・262 週・平均 48.3244・非ゼロ 262 週。2026-10-14 以降に追加した 5 化合物の run:

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
  化合物間比較は共通スケール（§2.1.4）でのみ行う。12ヶ月の共通スケールは `common-scale-*`、5年の共通スケールは
  `5y-common-scale-set*`。
- 数値の正本は `docs/audits/gt-summary.json`（`processing.cli gt-summary` の生成物）。
  publication ページの 5年ブロックも同じコマンド（`--write`）が書く。
- 5年リキッド系列は `data/raw/google_trends/` の main5 run（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5`、5 語）と新規 8 run（7 語が系列、THC-O リキッドは系列なしで quarantine）に収蔵する。`docs/audits/gt-summary.json` は bare 化合物 13 + CBX のみを扱いリキッドを含まないため、リキッド run の特定は `docs/audits/g2-query-inventory.json`（クエリ照合）と `g4-storage-inventory.json`（成果物）、数値は各 run の `records_*.json` を正本とする。
- 残り 8 化合物（CBN・CRDH・CRDP・H4CBH・HHBD・HHCH・THCH・THC-O）の5年 run は本表には載せず、
  `docs/audits/gt-summary.json` の各エントリの `run_id` / `path` を正本とする。
- **THCNM（初回収集、2026-11-04）**: `20261104T115431Z-google-trends-thcnm-5y`（窓 `2021-10-31_2026-11-08`、262 週、
  観測範囲 2021-10-31 〜 2026-11-01、平均 0.9122、非ゼロ 3 週）。計画書は `metadata/plans/gt-5y-thcnm.json`。
  窓は reference time（2026-11-04T11:54:32Z）で nominal に解決される 5 年を週バケットグリッド（sunday start）に
  量子化した**宣言値**であり、collector が実施する窓ではない。非ゼロの 3 週はいずれも最終 3 週に集中する。
  **この系列は `docs/audits/gt-summary.json` に含まれない**（同レポートの化合物集合は公開ページを持つ 14 化合物で、
  THCNM は配布 slice 外）。数値の正本は run の `records_thcnm.json`。

### 2.1.3 12ヶ月系列（週次 raw）

12ヶ月系列は 14 化合物が週次 raw を持ち、THC-O は Google Trends が系列を返さない。
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
| CRDH | `20261024T000000Z-google-trends-crdh-12m` | 2025-10-19 〜 2026-10-18 | 53 | 1.8868 | 1 |
| THCNM | `20261104T115425Z-google-trends-thcnm-12m` | 2025-11-02 〜 2026-11-01 | 53 | 4.4906 | 3 |
| CBX | `20261015T042853Z-google-trends-boundary-12m` | 2025-10-12 〜 2026-10-11 | 53 | 69.7736 | 53 |
| THC-O | （catalog せず）`20261023T162326Z-google-trends-thc-o-12m-r3` | — | — | — | — |

- 上の 14 行が**週次系列**（`data` 配列あり）。
- **CRDH の 12ヶ月系列**: `20261024T000000Z-google-trends-crdh-12m` の `records_crdh.json` に 53 週の週次系列がある
  （窓 2025-10-19 〜 2026-10-18。THCV・H4CBH・HHBD の 2026-10-23 再取得と同一窓）。旧 `20261008T102022Z-google-trends-crdh` の
  `records_crdh_12m.json`（`data_points` 53・`avg_12m` 1.9・`nonzero_weeks` 2 の記録値、週次系列なし）は証跡として残すが、
  正本は新 run の系列とし、旧記録値は引用しない。
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
- 3 つの収集バッチで**窓が違う**（2025-09-28〜 / 2025-10-19〜 / 2025-11-02〜）。窓をまたいだ 12ヶ月同士の比較はしないこと。
- **THCNM（初回収集、2026-11-04）**: `20261104T115425Z-google-trends-thcnm-12m`（窓 `2025-11-02_2026-11-08`、
  観測範囲 2025-11-02 〜 2026-11-01、53 週、平均 4.4906、非ゼロ 3 週）。計画書は `metadata/plans/gt-12m-thcnm.json`。
  窓は reference time（2026-11-04T11:54:26Z）で nominal に解決される 12 ヶ月を週バケットグリッドに量子化した宣言値。
  非ゼロの 3 週はいずれも最終 3 週に集中する（この化合物の検索需要は観測期間の末尾で立ち上がっている）。
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
- **この 4 セットは現行被覆ではなく歴史観測**（§2.1.6）。ポリシー `gt-5y-common-scale-cbd-thc` の
  現行窓は `2021-10-31_2026-11-08` で、その窓の再収集計画は
  `metadata/plans/gt-5y-common-scale-current-set{A..D}.json`。旧窓の 4 run は
  `legacy_out_of_scope` として残し、現行窓の被覆には数えない。
- **アンカー（CBD 33・THC 5）が 4 セットで一致**しているので、セット間を橋渡しできる（各語はアンカー経由で同じスケールに載る）。
- 成果物は verbatim `payload.json` + 共通スケール文書 `comparison_<terms>.json`（schema `google-trends-comparison-v1`）。
- **単独系列の平均とは比較しない**（別の正規化）。化合物間比較はこの共通スケール内でのみ行う。
- 平均が 0 の語（THCV・CRDH・CRDP・H4CBH・HHBD・THC-O）は、262 週のうち非ゼロがごく少ない語である。0 観測ではない。

### 2.1.5 表記ゆれ（THCO / THCO リキッド）の別観測

THC-O の canonical text は変えず、表記ゆれを `metadata/queries/query-variants.json`
に登録する。2026-11-04（owner 決定）に次の 4 run を、canonical の `query_id` の
まま variant text を送って収集した。

| variant text | query_id（canonical） | variant_id | run（`data/raw/google_trends/`） | モード | 窓 | 観測範囲 | 週数 | 非ゼロ週 |
|---|---|---|---|---|---|---|---:|---:|
| `THCO` | `thc-o-general-ja` | `thc-o-general-no-hyphen` | `20261104T135330Z-google-trends-thc-o-general-thco-12m` | 12ヶ月 | `2025-11-02_2026-11-08` | 2025-11-02 〜 2026-11-01 | 53 | 3 |
| `THCO` | `thc-o-general-ja` | `thc-o-general-no-hyphen` | `20261104T135339Z-google-trends-thc-o-general-thco-5y` | 5年 | `2021-10-31_2026-11-08` | 2021-10-31 〜 2026-11-01 | 262 | 90 |
| `THCO リキッド` | `thc-o-liquid-ja` | `thc-o-liquid-no-hyphen` | `20261104T135345Z-google-trends-thc-o-liquid-thco-12m` | 12ヶ月 | `2025-11-02_2026-11-08` | 2025-11-02 〜 2026-11-01 | 53 | 1 |
| `THCO リキッド` | `thc-o-liquid-ja` | `thc-o-liquid-no-hyphen` | `20261104T135350Z-google-trends-thc-o-liquid-thco-5y` | 5年 | `2021-10-31_2026-11-08` | 2021-10-31 〜 2026-11-01 | 262 | 23 |

- 経路は §2.1 と同じ `make collect`（`collect --live`、google-trends-mcp 0.1.1、
  geo `JP`）。計画書は `metadata/plans/gt-{12m,5y}-thc-o-{general,liquid}-thco-spelling.json`。
- **1 variant × 1 timeframe = 1 run**。run の `query_provenance` は canonical の
  `query_id` と variant の `submitted_query` を別フィールドで保持する
  （例 `{"query_id": "thc-o-general-ja", "submitted_query": "THCO"}`）。
  異なる表記の系列を合算・平均・置換しない。値は各 run の単独正規化（その run の
  ピーク = 100）である。
- **canonical は不変**: `THC-O` の 12ヶ月は Google Trends が no data を返した状態
  （`ISS-20261023-GT-006`）、5年は `20261014T204904Z-google-trends-cannabinoid-multi-trends`
  （262 週・非ゼロ 19 週）が正本。variant の run はどちらの代用でもない。
- **処理層での分離**: `processing.gt_statistics.find_run` は record の `keyword` が
  化合物名と**完全一致**するものだけを選び、`リキッド` を含む製品語は除外する。
  `THCO` / `THCO リキッド` の record は `THC-O` の候補にならない。本変更では
  `docs/audits/gt-summary.json` も公開ページも再生成していない。したがって
  canonical の 5年サマリ・12ヶ月の no data 記載・被覆数（§1.3）は従来のまま。
- 登録は「同じ意味を意図する表記候補」であり、検索結果の同等性を主張しない。
  例えば 5年の非ゼロ週が canonical 19・variant 90 と異なるのは、2 つの異なる
  検索文字列の観測値であり、canonical 系列の修正ではない。`THCO` は後述のとおり
  別物質（tetrahydrocannabiorcol）の話題も拾い得るので、差を「表記だけの違い」と
  解釈しない。
- 窓は canonical の 5年 run（`2021-10-10 〜 2026-10-11` 等）と異なる。窓をまたいだ
  数値比較はしない（§4.2）。
- 12ヶ月・5年の variant run はいずれも raw のみで、`docs/audits/gt-summary.json`
  の化合物集合（公開ページの 14 化合物）には入らない。

**証拠（2026-11-04）**: `THCO` を `THC-O` の表記ゆれとして登録する根拠は、PubMed 37466480 が
tetrahydrocannabinol-O-acetate の口語名として `THCO` を記録していること、PubChem CID 198013 が
Tetrahydrocannabinol acetate（別名 `THC-O-ACETATE`、CAS 23132-17-4、`C23H32O3`）のレコードで
あること、PubMed 37381980 / 36508081 が `THC-O-Acetate` 表記を用いることである。証拠 ID は
`metadata/provenance/evidence-registry.json`。

**同一性の留保（重要）**: `THCO` は Δ8-THCO / Δ9-THCO（tetrahydrocannabiorcol、CAS 22972-64-1 /
22972-65-2、`C17H22O2`、Cayman Chemical 33762 / 33763）にも使われる**別物質の表記**である。
アセテート体（`C23H32O3`）と tetrahydrocannabiorcol（`C17H22O2`）は別物質で、Δ8 / Δ9 の 2 異性体も
ある。したがって `THCO` という検索文字列は単一の CAS にも単一の構造にも対応せず、variant run の
観測値は「送信した文字列の検索需要」であって含有物質の同定ではない。taxonomy の `compound_thc_o`
に CAS / ChEBI / Wikidata / PubChem の exactMatch を追加しない（ISS-20261104-TAX-029、
`docs/provenance/compound-taxonomy.md`）。

### 2.1.6 共通スケール比較の必須アンカー（CBD / THC）

Google Trendsの単独系列は各語のピーク=100に正規化されるため、化合物間で値を比べられない。
化合物間比較は、同じ`compare_terms`要求にアンカーCBD・THCを含む共通スケールでのみ行う。
この規則は`metadata/query-design.json`の`comparison_scales`に宣言し、計画・収集・採用で検証する。

- 正本ポリシー `gt-5y-common-scale-cbd-thc`: anchor query `cbd-general-ja` /
  `thc-general-ja`、anchor term `CBD` / `THC`、request `compare_terms` /
  `geo=JP` / `locale=ja` / `today 5-y`、window `2021-10-31_2026-11-08`（owner 決定 B）。
  旧窓 `2021-10-17_2026-10-18` の setA〜D は legacy として残し、現行窓の被覆に数えない。
- 必須化合物集合は `metadata/queries/query-registry.json` の active
  `compound_general` クエリを権威とする。化合物を追加すれば自動的に必須になる。
  除外は `excluded_compound_ids` に理由付きで宣言する。
- **収集前**: `make gate-plan PLAN=<plan>` は、`common_scale` で両アンカーが
  同一要求に無い場合、geo / timeframe / window / locale がポリシーと一致しない
  場合、宣言のない複数語 plan の場合に停止する。単独系列 plan は許可するが
  `single_series`（非比較）として記録する。
- **収集後 / 採用**: L1 は、宣言済み run の request と comparison artifact の
  両方にアンカーがあり、window / request metadata が一致することを検証する。
  宣言のない comparison-shaped run は legacy warning として残し、raw は変更しない。
- **監査**: `make audit-comparison-scale` がポリシーごとの missing anchor sets /
  compound coverage を報告する。比較に使えない run は `not_comparable_runs`、
  要求条件（geo / timeframe / window）がポリシーの外にある run は
  `out_of_scope_runs`、アンカーはあるが宣言前の run は `legacy_undeclared_runs`
  として別々に出す。`ARGS=--require-complete` で missing compound を失敗にする。

**THCNM の現状**: 5年の単独系列（`20261104T115431Z-google-trends-thcnm-5y`）はあるが、
アンカー付き common-scale run はまだ無い。計画
[`metadata/plans/gt-5y-common-scale-thcnm.json`](metadata/plans/gt-5y-common-scale-thcnm.json)
（CBD + THC + THCNM、現行窓・geo JP・locale ja）を宣言済みで、ライブ収集・採用まで
監査は `thcnm-general-ja` を **missing** と報告する。現行窓の setD 計画も THCNM を
含むため、どちらか一方の採用で被覆は `complete` になる。

**CBXの所有移管とbridge（2026-11-04）**: CBXのGoogle Trends raw 8 runを`cbx-search-trends`から本studyへ移管した。移管は新規観測ではなく、run ID・payload bytes・hashを保持した再採用である。移管 declarationは`20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json`に記録し、旧study側のGoogle Trends rawは削除した。

さらに、CBX+CBD+THCを同一`compare_terms` requestで12ヶ月・5年各1 run取得した。bridgeは単独系列を合成したものではなく、同一run内の共通スケール値である。既存のsingle-term seriesや5年set A-Dは変更しない。5年bridgeは既存set A-Dと窓が異なるため、同一スケールとは主張しない。

| モード | run | 観測範囲 | 平均（共通スケール） |
|---|---|---|---|
| 12ヶ月 | `20261104T165149Z-google-trends-cannabinoid-raw-collection` | 2025-11-02〜2026-11-01 | CBX 8 / CBD 46 / THC 12 |
| 5年 | `20261104T165155Z-google-trends-cannabinoid-raw-collection` | 2021-10-31〜2026-11-01 | CBX 4 / CBD 33 / THC 5 |

**legacy**: 既存set A-Dや12ヶ月比較setは、新ポリシー導入前のlegacyとして報告しrawは変更しない。

### 2.2 X (Twitter)
CBX は化合物集合には含まれていたが、Google Trends raw は [`datasets/cbx-search-trends/`](../cbx-search-trends/) にあった。2026-11-04 の owner 決定で **CBX の Google Trends raw の所有をこの study へ移す**（[`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)）。移管は「観測のやり直し」ではなく「同じ run の再採用」である。

#### 移管した run

`cbx-search-trends/data/raw/google_trends/` にあった 8 run が対象。移管後は同ディレクトリに Google Trends raw は無く、この study の `data/raw/google_trends/` が唯一の所在になる。

| run id | 移管の方法 | 移管前の状態 |
|---|---|---|
| `20261015T042845Z-google-trends-boundary-1m` | `staging-declaration-v1` で run_metadata を再発行（run id・payload バイト不変） | 現行契約（manifest あり） |
| `20261015T042849Z-google-trends-boundary-3m` | 同上 | 同上 |
| `20261015T042853Z-google-trends-boundary-12m` | 同上 | 同上（12ヶ月の正本） |
| `20261015T042857Z-google-trends-boundary-5y` | 同上 | 同上（5年の正本） |
| `20261001T115959Z-google-trends-cbx-rikiddo` | ディレクトリを `git mv`（ファイルバイト不変） | 凍結 legacy（manifest なし、catalog 外） |
| `20261001T121949Z-google-trends-h4cbh-hhbd` | 同上 | 同上 |
| `20261001T132500Z-google-trends-disambiguated` | 同上 | 同上（`run_metadata.run_id` は `disambiguated_queries`） |
| `20261001T135424Z-google-trends-variance-check` | 同上 | 同上（`run_metadata.run_id` は `variance_check`） |

- **宣言**: [`20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json)。再発行した 4 run は `environment.ownership_migration` に `previous_study_id` / `previous_study_run_id` / 移管前 path / 移管前 `run_metadata.json` と `artifact-manifest.json` の SHA-256 / 移管前 `code_commit` を記録し、`is_new_observation: false` を明示する。payload（`mcp-tool-result.json`）と `records_cbx.json` は移管前と同一バイトで、SHA-256 も一致する。
  - 宣言の `artifacts[].source` は**移管前の path** である。移管後はそこにファイルが無いので、この宣言は handover の記録であって再実行可能な staging 入力ではない。バイトの同一性は採用済み run の manifest と宣言の `source_artifacts[].sha256` で照合する（両者は一致する）。
  - 宣言の SHA-256 は各 run の `environment.handover.declaration_sha256` に固定されている。移管の記録を後から書き換えるとこの照合が切れるので、宣言は事実の記録として扱い、編集しない。
- **移管で変わらないもの**: run id、payload / 系列のバイト、窓、観測範囲、要求パラメータ、値。
- **移管で変わるもの**: `study_id`（`cbx-search-trends` → `cannabinoid-raw-collection`）、再発行した `artifact-manifest.json`（`derived_from` は宣言経路が表現できないため入らない。移管前の manifest は Git 履歴に残る）、`environment.code_commit`（移管を実行した commit。収集時の commit は `ownership_migration.previous_code_commit`）。
- **legacy 4 run の `run_metadata.json` は収集時の `study_id` のまま**（raw は不変）。manifest が無いため catalog にも入らない。同じ扱いは旧 `cannabinoid-multi-trends` の run でも使っている。

#### bridge（CBX + CBD + THC の共通スケール）

単独系列は各語のピーク=100 に正規化されるので、CBX を化合物間比較に載せるには同じ run でアンカーと一緒に測る必要がある。そこで **CBX + CBD + THC を 1 リクエストの `compare_terms`** で、12ヶ月・5年を各 1 run 収集した。**単独系列の平均を合成・平均して作った値ではない**。

| モード | run（`data/raw/google_trends/`） | `query_id` | 窓 | 観測範囲 | 週数 | 平均（共通スケール） |
|---|---|---|---|---|---:|---|
| 12ヶ月 | `20261104T165149Z-google-trends-cannabinoid-raw-collection` | `comparison-cbx-bridge` | `2025-11-02_2026-11-08` | 2025-11-02 〜 2026-11-01 | 53 | CBX 8 / CBD 46 / THC 12 |
| 5年 | `20261104T165155Z-google-trends-cannabinoid-raw-collection` | `comparison-cbx-bridge` | `2021-10-31_2026-11-08` | 2021-10-31 〜 2026-11-01 | 262 | CBX 4 / CBD 33 / THC 5 |

- 経路は §2.1 と同じ `make collect`（`collect --live`、google-trends-mcp 0.1.1、geo `JP`）。計画書は `metadata/plans/gt-{12m,5y}-cbx-bridge.json`、語は両方とも `CBX` / `CBD` / `THC`。`query_id` は両方とも `comparison-cbx-bridge`（query registry は語の集合と意図を登録し、timeframe は登録しない。単独系列の `cbd-general-ja` と同じ規則）。
- 成果物は verbatim `payload.json` + 共通スケール文書 `comparison_cbx-cbd-thc.json`（schema `google-trends-comparison-v1`）。
- **単独系列の CBX 平均（12ヶ月 69.7736・5年 48.3244）と bridge の値（12ヶ月 8・5年 4）は別の正規化**。両者を比べない・合成しない。単独系列の平均は化合物間でも比べない（§2.1.2・§2.1.3）。
- **5年 bridge の窓は既存 setA〜D（`2021-10-17_2026-10-18`）と 2 週ずれる**（`2021-10-31` 〜 `2026-11-01`。`today 5-y` を 2026-11-04 に解決した結果）。アンカーは setA〜D と同じ整数値（CBD 33 / THC 5）だが、窓が違うので「同じスケールに載った」とまでは主張しない。bridge 内の CBX / CBD / THC の比較は同一 run 内なので有効。
- **12ヶ月 bridge に対応する既存の CBX 入り比較セットは無い**（12ヶ月の比較セットは CBX を含まない）。したがって 12ヶ月の CBX はこの bridge だけが共通スケール値を持つ。
- **canonical の単独系列は変えない**：CBX の 5年・12ヶ月単独系列、`docs/audits/gt-summary.json` の CBX エントリ、他の 14 化合物の系列はいずれも従来のまま。bridge は別 run・別文書である。
**legacy の扱い**: 5年 setA〜D（旧窓 `2021-10-17_2026-10-18`）は CBD/THC を含むが、
ポリシーの現行窓の外にあるため `legacy_out_of_scope`。新規準拠とも現行窓の被覆とも
扱わない（raw は書き換えない）。共通スケールとしては有効なので
`not_comparable_runs` には入れず、`out_of_scope_runs` として別に報告する。
宣言を持たないが、要求条件とアンカーが一致する run は
`legacy_undeclared_anchored`（比較可能・未宣言）として `legacy_undeclared_runs`
に報告する。
12ヶ月の legacy comparison sets も同じく範囲外（`legacy_out_of_scope`）だが、
アンカー欠落は監査の `legacy_missing_anchor_sets` に残る。raw は書き換えない。

**現行窓の被覆**: 現行窓 `2021-10-31_2026-11-08` の common-scale run はまだ無いため、
監査は必須 14 化合物をすべて `missing` と報告する（旧窓の被覆では代替しない）。

### 2.2 X (Twitter)

**ツール:** Apify Actor `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search)

**パラメータ:**
- section: `latest`
- maxPages: 2-3（キーワードに依存）
- query: `{keyword} since:2026-09-01 until:2026-10-01`

**収集キーワード:**

| キーワード | maxPages |
|-----------|----------|
| CBD | 3 |
| THC | 3 |
| CBG | 2 |
| HHC | 2 |
| THCV | 2 |
| THC-O | 2 |
| THCH | 2 |

**注意事項:**
- シャドウバンの可能性（THC 等の敏感キーワード）
- 0 件でも observed_zero として記録
- 集計件数ではなく `records.json` の実レコード数で確認する

**CBD の追加 3 run（2026-10-08、`data/raw/x/`）:**

| run | `records.json` 行 | 備考 |
|---|---:|---|
| `20261008T165031Z-x-cbd-1year` | 0 | `status: SUCCEEDED` の 0 件（observed_zero） |
| `20261008T165122Z-x-cbd-1m` | 60 | |
| `20261008T165330Z-x-cbd-latest10` | 200 | |

- 3 run とも `run_metadata.json` に収集条件（クエリ・`maxPages`・窓）の記録が無く、実行状態の 3 項目だけを持つ。
  run-id から読める以上の条件を推定しない。

### 2.3 YouTube

**ツール:** Apify Actor `h7sDV53CddomktSi5` (`streamers/youtube-scraper`)

**クエリ設計（study が宣言）**: [`metadata/query-design.json`](metadata/query-design.json) の `youtube-liquid-only-primary`。

- **primary**: `<compound> リキッド`（`product_liquid`）のみ。**1 run 1 クエリ**。
- **primary 外**: 裸の化合物語（`compound_general`）など。raw / catalog に保持してよいが、primary coverage に数えない。
- 理由: (a) Actor input に geo filter はない、(b) 日本語の製品語「リキッド」が検索語ベースで日本市場向け製品コンテンツを近似的に絞り込む、(c) これは geo 保証ではない。裸の化合物語は (b) を持たず、日本語製品コンテンツに限定されないため primary 外。
- **「化合物語と製品語を必ず対で取る」規則はこの study にはない。** 裸の `HHC` run は保持された out-of-scope 証跡であり、`HHC リキッド` の必須 companion ではない。

採用済み YouTube raw は 18 run。primary のリキッドが 17 run / 15 化合物、primary 外の裸語 `HHC` が 1 run。required primary query は **18 本**（2026-11-10 に `cbc-liquid-ja` = `CBC リキッド` と `cbdv-liquid-ja` = `CBDV リキッド` を登録）で、**16 本に adopted run がある**。うち `compound_thcnm` が 2 本（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）を持ち、**2 本とも adopted run がある**（2026-11-04、各 1 run）。残る 2 本は CBC・CBDV のリキッドで **run 0（未収集。0 観測でも欠測でもない）**。

- **2 本の required primary query を持つ化合物がある**（現状は THCNM だけ）。被覆は**クエリ単位と化合物単位**の両方で報告する: クエリは自身の `query_id` の adopted run が 1 本以上あれば被覆、化合物は自身の required primary query が**全部**揃って初めて完了、一部だけなら `partial`、零本なら `missing`。run は自分の `query_id` しか被覆せず、兄弟クエリの代替にならない（件数も合算しない）。`make audit-youtube-coverage` はこの規約で `compound_coverage` を出し、THCNM は `primary coverage 2/2` と表示する。
  THA は `compound_thcnm` の**別名・商業名**（別物質ではない）であり、2 本のクエリは 2 つの検索文字列を測るもので、2 物質を測るものではない（`ISS-20261104-TAX-028`）。

- **THCNM の 2 クエリは 2026-11-04 に各 1 run で実行した**（同一 Actor・同一入力条件）。`THCNM リキッド` は 30 件（`20261104T120627Z-youtube-cannabinoid-raw-collection`）、`THA リキッド` は 311 件（`20261104T120805Z-youtube-cannabinoid-raw-collection`）で、両方 SUCCEEDED。件数差はクエリ文字列の違いに由来し、統合・合算しない。宣言は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)。

| 区分 | 検索語 | `query_id` | `intent_id` | `date_filter` | 件数 | 観測窓（UTC、`end_exclusive`） | run |
|---|---|---|---|---|---:|---|---|
| primary | `HHBD リキッド` | `hhbd-liquid-ja` | `product_liquid` | `all` | 224 | 2020-09-30 〜 2026-10-06 | `20261010T141947Z-youtube-cannabinoid-raw-collection` |
| primary | `H4CBH リキッド` | `h4cbh-liquid-ja` | `product_liquid` | `all` | 395 | 2020-10-01 〜 2026-10-02 | `20261010T143430Z-youtube-cannabinoid-raw-collection` |
| primary | `CBD リキッド` | `cbd-liquid-ja` | `product_liquid` | `all` | 456 | 2014-11-17 〜 2026-10-10 | `20261010T144422Z-youtube-cannabinoid-raw-collection` |
| primary | `CBN リキッド` | `cbn-liquid-ja` | `product_liquid` | `all` | 468 | 2008-08-01 〜 2026-09-24 | `20261010T145729Z-youtube-cannabinoid-raw-collection` |
| primary | `CRDH リキッド` | `crdh-liquid-ja` | `product_liquid` | `all` | 352 | 2022-09-29 〜 2026-09-12 | `20261010T164917Z-youtube-cannabinoid-raw-collection` |
| primary | `CBD リキッド` | `cbd-liquid-ja` | `product_liquid` | `year` | 393 | 2025-10-11 〜 2026-10-10 | `20261011T191902Z-youtube-cannabinoid-raw-collection` |
| primary | `HHC リキッド` | `hhc-liquid-ja` | `product_liquid` | `all` | 412 | 2013-06-25 〜 2026-09-20 | `20261101T091646Z-youtube-cannabinoid-raw-collection` |
| primary | `HHCH リキッド` | `hhch-liquid-ja` | `product_liquid` | `all` | 138 | 2012-04-09 〜 2026-10-18 | `20261101T105037Z-youtube-cannabinoid-raw-collection` |
| primary | `THCH リキッド` | `thch-liquid-ja` | `product_liquid` | `all` | 240 | 2011-06-07 〜 2026-09-15 | `20261101T105058Z-youtube-cannabinoid-raw-collection` |
| primary | `CBG リキッド` | `cbg-liquid-ja` | `product_liquid` | `all` | 219 | 2017-05-17 〜 2026-10-18 | `20261101T111408Z-youtube-cannabinoid-raw-collection` |
| primary | `CRDP リキッド` | `crdp-liquid-ja` | `product_liquid` | `all` | 433 | 2016-06-18 〜 2026-10-18 | `20261101T111429Z-youtube-cannabinoid-raw-collection` |
| primary | `THC リキッド` | `thc-liquid-ja` | `product_liquid` | `all` | 435 | 2009-05-01 〜 2026-10-30 | `20261101T111450Z-youtube-cannabinoid-raw-collection` |
| primary | `THC-O リキッド` | `thc-o-liquid-ja` | `product_liquid` | `all` | 388 | 2015-10-30 〜 2026-11-01 | `20261101T112513Z-youtube-cannabinoid-raw-collection` |
| primary | `THCV リキッド` | `thcv-liquid-ja` | `product_liquid` | `all` | 435 | 2011-08-15 〜 2026-10-15 | `20261101T112534Z-youtube-cannabinoid-raw-collection` |
| primary | `CBX リキッド` | `cbx-liquid-ja` | `product_liquid` | `all` | 329 | 2010-03-19 〜 2026-10-28 | `20261101T112555Z-youtube-cannabinoid-raw-collection` |
| primary | `THCNM リキッド` | `thcnm-liquid-ja` | `product_liquid` | `all` | 30 | 2017-11-30 〜 2026-11-03 | `20261104T120627Z-youtube-cannabinoid-raw-collection` |
| primary | `THA リキッド` | `tha-liquid-ja` | `product_liquid` | `all` | 311 | 2012-01-17 〜 2026-11-05 | `20261104T120805Z-youtube-cannabinoid-raw-collection` |
| **retained / out-of-scope** | `HHC`（裸語） | `hhc-general-ja` | `compound_general` | `all` | 482 | 2006-09-05 〜 2026-11-02 | `20261101T085920Z-youtube-cannabinoid-raw-collection` |

- **request と観測窓は別物**。Actor 入力に `dateFilter` を渡していない run は、絶対日付窓もローリング窓も持たない。`date_filter: "all"` は宣言語彙であり、Actor の enum 値ではない（`src/collection/adapters/youtube/request.py` は `all` を「`dateFilter` を省略」に写す）。
- 観測窓は payload の動画公開日を UTC の半開区間 `[start, end_exclusive)` に正規化したもの: `start` = 最小日の `00:00:00Z`、`end_exclusive` = 最大日 + 1 日の `00:00:00Z`。これは返された項目の範囲であり、検索条件でも完全性の証明でもない。
- `collection_request` には `date_filter` / `reference_time` / actor input（`searchQueries` / `maxResults` / `maxResultsShorts` / `maxResultStreams`）を記録する。
- CBD リキッドの 2 run は `date_filter`（`all` / `year`）と観測窓が異なる別観測である。統合しない。
- 裸の `HHC` は `compound_general` であり primary 外。`HHC リキッド` との統合・合算をしない。
- 件数は検索結果として返された動画の標本数であり、YouTube 全体の動画数ではない。run 間で窓が違うため、件数をまたいで合算しない。
- 2026-11-01 の liquid 8 クエリ一括実行は、最初の試行で 2 run（HHCH・THCH）だけが完走し、残り 6 クエリは Apify アカウントの請求サイクル上限で中断した。上限引き上げ後の再実行（同日 11:14〜11:33Z）で 6 クエリすべてが SUCCEEDED になり、CBG・CRDP・THC・THC-O・THCV の 5 run を採用した。CBX はその時点では採用先未決だったが、同じ 2026-11-01 の owner 決定（CBX YouTube はこの study が所有し、CBX の Google Trends / GSC raw は当時 `cbx-search-trends` に残す）を受けて採用した（Google Trends の所有は 2026-11-04 に本 study へ移管。§2.1.6）。中断時の部分 payload は raw に採用していない（[ISS-20261101-YT-019](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。
- payload の `date` は動画の公開日時であり、相対時刻ではない。`id` は動画 ID、`title` はタイトル。run 内の重複は `id` で確認する（raw は編集しない）。
- 2026-10-02 の YouTube run は API 疎通検証であり、本研究の観測としては扱わない。

**注意事項:**
- raw は **byte 単位**で保持し、Git 管理外とする（公開対象外）。列は `id` / `title` / `date` / `input` / `type` などを含む。raw を書き換えない。2026-10-10/11 の 6 run と 2026-11-01 の HHC 2 run は flat CSV（`youtube-dataset-csv-v1`）、2026-11-01 の liquid 8 run（HHCH・THCH・CBG・CRDP・THC・THC-O・THCV・CBX）と 2026-11-04 の THCNM 2 run（`THCNM リキッド`・`THA リキッド`）は Apify dataset JSON（`youtube-search-result-list-v1`）で保存している。
- 保存先は `datasets/<study-id>/data/raw/youtube/<run-id>/`。`run_metadata.json`（`collection-run-v1`）と `artifact-manifest.json`（`artifact-manifest-v1`）は `make stage` / `make adopt-all` が生成する。手書きしない。
- 重複排除は run 内の `id` で確認し、件数だけを宣言の `environment` に記録する。raw は変更せず、分析用 dedup は下流の再現可能な処理で行う。
- 採用宣言は [`20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json)（HHBD）、[`20261015-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261015-youtube-liquid-batch-cannabinoid-raw-collection.json)（リキッド 5 run）、[`20261101-youtube-hhc-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-cannabinoid-raw-collection.json) / [`20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json)（HHC 2 run）、2026-11-01 の HHCH・THCH 2 run は [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)、再実行の CBG・CRDP・THC・THC-O・THCV 5 run は [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)、CBX は [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json)、THCNM 2 run は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)。
- HHC 2 run の request 語彙・actor build・実行状態は [`20261101-youtube-hhc-request-parameters.json`](../../metadata/provenance/corrections/20261101-youtube-hhc-request-parameters.json) が訂正する。元の宣言は handover hash を保つため書き換えず、訂正版 declaration を併置する。
- 結果上限の正規名は現行 Actor の **`maxResults`**。旧宣言の `max_videos`（HHBD の 999999、HHC 2 run の 500）は**歴史的記録**であり、新規入力には使わない。リキッド 5 run の宣言には上限の記録がない（記録がないことを 0 や無制限と読み替えない）。
- この study の YouTube raw は配布物 [`cannabinoid-platform-trends`](../cannabinoid-platform-trends/) の COL-033 slice に含まれない。配布物の `not_collected` は「slice に無い」であり、この study の未収集ではない。

---

## 3. データ処理

### 3.1 重複排除

| ソース | キー | 方法 |
|--------|------|------|
| X | tweet_id | ユニーク ID で重複排除 |
| YouTube | `id`（flat CSV の動画 ID） | run 内のユニーク `id` で確認。raw は編集しない。run 間は畳まない（同じ動画が 2 run に出れば 2 行）|
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

> 本表の `author_id` は初出順の連番であり、ハッシュではない。`tweet_id_hash` は SHA-256 の先頭 16 文字である。
> 本 study は X raw をリポジトリに保持していないため、この変換の適用先成果物は `cbx-social-trends` 側にある。

### 3.4 YouTube 月別集計

`make youtube-aggregate` が採用済み 18 run（primary 17 + retained 1）のうち HHBD リキッド run だけを読み、`date` を UTC の暦月に変換して `id` のユニーク件数を集計する。run 内の重複 ID は1件に数え、同じ ID が異なる月に現れた場合は処理を停止する。出力には動画 ID、タイトル、チャンネル、説明文、個別の反応数を含めない。他の primary run と retained run はまだ集計していない。

出力は [`data/processed/youtube_monthly_counts.csv`](data/processed/youtube_monthly_counts.csv)。月に結果がない場合は行を作らず、0件とは記録しない。件数は `HHBD リキッド` の YouTube 検索結果に含まれた動画の標本数であり、その月にYouTube全体で公開された動画数を表さない。raw の SHA-256 と件数を run metadata / artifact manifest と照合し、raw は変更しない。月別集計は公開審査済みで、承認は当該 CSV の SHA-256 に限定される（[審査記録](../../metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json)）。raw は公開対象外。外部公開・リリースは別途実施していない。

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
| catalog / declaration の run が raw に存在するか | `make audit-raw-completeness` | 標準出力（checkout ローカル） |
| YouTube の liquid-only primary 被覆 | `make audit-youtube-coverage` | 標準出力（クエリ単位・化合物単位。primary と retained を分離） |
| 配布 slice と raw study のスコープ差 | `make audit-distribution-scope` | 標準出力（COL-033 の 6 run と raw の 18 run） |
| 監査スナップショットの前提（raw の完全性） | `make audit-snapshots` の前後の `snapshot-guard` | `.staging/audit-snapshot-guard.json` |
| スナップショットの鮮度 | `pytest tests/validation/test_audit_report_freshness.py` | — |
| 全体 | `pytest -q` | — |

自動化されていない項目（手作業で確認する）: X のシャドウバンによる 0 件、キーワードの含有率。
X raw は Git 管理外のため、run の件数はローカル証跡でしか確認できない。

### 4.2 制約事項

| 制約 | 対策 |
|------|------|
| Google Trends 相対指数 | 絶対検索数ではない点を明記 |
| Google Trends の窓は相対表記 | `today 5-y` / `today 12-m` は収集時刻で解決される（`exact_window_match=false`）。窓ごとに `window_id` を切り、run 間で窓が違えば別観測として扱う（§2.1.2・§2.1.3） |
| 閾値未満で系列が返らない語 | `status=failed` + `errors[].code=NO_DATA` として記録し、0 観測に読み替えない。現行契約では採用記録にできず quarantine 止まり（`ISS-20261023-GT-006`） |
| X シャドウバン | 0 件でも observed_zero として記録 |
| 多義語（CBD, THC, CBC） | コンテキスト分析で誤検知を排除する。`CBC` はカナダ放送協会などドメイン外の略号と衝突するため、登録文字列は物質の同定ではない（CBC・CBDV は未収集。`ISS-20261110-TAX-039`） |
| ソース間の比較 | 単位が異なるため直接比較不可 |
| THCNM の化学的同一性が未確認 | 系列は登録 `canonical_text` に一致する検索需要であり、物質の検出・存在の証拠ではない。同一性・`skos:broader` の確定は `ISS-20261104-TAX-028` の解消条件で扱う（本 doc は taxonomy を変更しない） |

---

## 5. 局所化

### 5.1 関連研究

| Study ID | 関係 |
|----------|------|
| cannabinoid-platform-trends | **配布物**。YouTube は COL-033 の 6 liquid run に限定され、本 study の YouTube raw 18 run（primary 17 + retained 1）は含まれない。THCNM はこの配布 slice に入らない（COL-033 に YouTube run は無く、Google Trends 系列は `gt-summary` の公開化合物集合外） |
| cbx-search-trends | CBX/H4CBH/HHBD の検索需要。**CBX の Google Trends raw は 2026-11-04 に本 study へ所有移管**（§2.1.6）。同 study に残る raw は Google Search Console だけ |
| cbx-social-trends | CBX の SNS 言及（規制前後の比較） |
| cbx-liquid-online-trend | CBX リキッドの週次データ |

### 5.2 既存インフラ

- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
- 検証スクリプト: `scripts/validation/validate-data-schema.sh`
- エクスポート: `scripts/export/`

## 6. 研究軸の分離

cbx-search-trends は CBX 製品軸（CBX リキッド等の製品需要）の研究であり、cannabinoid-raw-collection は成分横断軸（CBD・THC・CBG・CBN・HHC 等の成分間比較）の研究である。両者は観測対象の軸が異なるため、クエリー設計・比較スケール・解釈を分離する。日本語「○○ リキッド」拡張（GTJA-20261012）は成分横断軸に属する。

CBX の Google Trends は 2026-11-04 から **この study の own raw** である（§2.1.6）。したがって Google Trends の被覆は**収集済み 15 化合物すべて own raw**（5年 15/15・12ヶ月 14/15）で、「参照込み」と「own raw」を分けて数える必要はない（§1.3）。2026-11-10 に登録した CBC・CBDV は run 0 のため、この被覆数は登録 17 化合物の被覆ではない。CBX リキッドは製品語であり、CBX 化合物語の系列とは別観測である。CBX の Google Trends の扱いは [`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md) の決定事項であり、CBX YouTube の所有は 2026-11-01 の owner 決定で本 study に確定した（[`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。

YouTube のクエリ設計は [`metadata/query-design.json`](metadata/query-design.json) が正本。primary は liquid-only であり、裸の化合物語は保持しても primary coverage に数えない（§2.3）。
