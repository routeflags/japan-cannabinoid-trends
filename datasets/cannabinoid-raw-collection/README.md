# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

**CBX を除く 13 化合物**の市場トレンド・SNS 言及・動画コンテンツの**原記録を集める研究**。CBX 本体は [`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当する。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本国内において、カンナビノイド各化合物の検索需要・SNS 言及・動画コンテンツはどう推移しているか？

## 対象化合物

合計 **13 化合物**。化合物ごとの収集状況は下表、収集条件は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3。

| 化合物 | 分類 | Google Trends 12ヶ月 | Google Trends 5年 | X | YouTube（公開分）|
|--------|------|:----:|:----:|:-:|:-:|
| CBD | major | ✅ | ✅ | ✅ | ✅ |
| THC | major | ✅ | ✅ | ✅ | ✅ |
| CBG | minor | ✅ | ✅ | ✅ | ✅ |
| HHC | semisynthetic | ✅ | ✅ | ✅ | ✅ |
| THCV | minor | ✅ | ✅ | ✅ | ✅ |
| THC-O | semisynthetic | データなし | ✅ | ✅ | ✅ |
| THCH | minor | ✅ | ✅ | ✅ | ✅ |
| CBN | minor | ✅ | ✅ | — | ✅ |
| CRDH | synthetic | ✅ | ✅ | — | ✅ |
| CRDP | synthetic | ✅ | ✅ | — | ✅ |
| H4CBH | semisynthetic | ✅ | ✅ | — | ✅ |
| HHBD | semisynthetic | ✅ | ✅ | — | ✅ |
| HHCH | synthetic | ✅ | ✅ | — | ✅ |

読み方:

- **5年系列**: 表の 13 化合物すべてが週次 raw を持つ。旧 `…-5y-baseline` run は summary-only で、どの化合物の引用元でもない（証跡として残る。[methodology.md](methodology.md) §2.1.1・§2.1.2）。
- **12ヶ月系列**: 12 化合物が週次 raw を持ち、THC-O は Google Trends が系列を返さない。THCV・CRDH は 12ヶ月が 53 週中 1 週だけ非ゼロ（[methodology.md](methodology.md) §2.1.3）。CRDH の旧 summary（`records_crdh_12m.json`）は証跡として残るが、その記録値（`avg_12m` 1.9 等）は raw から再現できないので引用しない。
- **週次系列は全面で比較できるわけではない**: 5年は 2 つの窓に分かれ（9 化合物が 2021-10-10 〜、4 化合物が 2021-10-17 〜）、12ヶ月も 2 窓に分かれる。また各 run は自分のピーク=100 に正規化されるので、単独系列の値を化合物間で比べない。化合物間の比較は共通スケール（§2.1.4）でのみ行う。
- **「データなし」**: 取得はしたが Google Trends が閾値未満で系列を返さなかった。**欠測であって 0 観測ではない**。
- **「—」**: そのソースでは収集していない（X の 6 化合物は [`datasets/cannabinoid-social-trends/`](../cannabinoid-social-trends/) が規制前後比較として収集している）。
- **「YouTube（公開分）」**: 2026-10-29 に集計物を削除した（研究内に参照元 raw が無いため）。
- **CBX はこの研究の対象外**（[`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当）。`docs/audits/gt-summary.json` が 14 化合物なのはこの 1 件を含むため。
- Google Trends の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。単独系列（12ヶ月・5年）のほかに、比較セット／共通スケール（12ヶ月 `common-scale-*`・5年 `5y-common-scale-set*`）・表記事前調査・「リキッド」系クエリの run がある。

## データソース

| ソース | ツール | 状態 |
|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | ✅ 5年 13/13 化合物・12ヶ月 12/13（欠測は §2.1.3） |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ✅ 7 化合物（CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run。条件は未記録） |
| YouTube | Apify `gJvjeCYNraSfhIaNd` | 集計物は 2026-10-29 に削除（研究内に参照元 raw が無いため） |

> **関連データセットとの役割分担**: 本データセットは**トレンド分析**（複数プラットフォームの出現・時系列分布）が目的。
> YouTube 検索結果の**一貫性・再現性検証**は [`datasets/youtube-consistency/`](../youtube-consistency/) が担当しており、
> そちらは別の Actor（`h7sDV53CddomktSi5` / streamers/youtube-scraper）を使う。両者は目的・ Actor・格納形式（本件は raw ファイル、同件は SQLite）が異なるため重複ではなく分業である。

## 収集結果

Google Trends の系列・窓・欠測は [methodology.md](methodology.md) §2.1.2・§2.1.3 と
[`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)（5年）が正本。
単独系列の平均と比較セット（`common-scale-*` の**共通スケール**値）は別物なので混ぜない。
単独系列の平均は化合物間でも比べない（正規化が語ごとに違う）。比較は共通スケールでのみ行う。
**5年の共通スケールはアンカー CBD/THC を含む 4 セット**（[methodology.md](methodology.md) §2.1.4）。
12ヶ月の共通スケールは `common-scale-*` の各 run。

### 収集したキーワード

収集語は 3 種類しかない（化合物語・製品語・アンカー語）。各語は下表のどこかに 1 回だけ現れる。

| 種別 | 語 |
|---|---|
| 化合物語（13） | CBD, THC, CBG, HHC, THCV, THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH |
| 製品語 — リキッド（13） | 上の 13 語に「リキッド」を付けた形（`CBD リキッド` 〜 `THCV リキッド`、`THC-O リキッド` を含む） |
| 製品語 — オイル（2） | CBD オイル, THC オイル |
| アンカー語（この study の対象外） | CBX リキッド（CBX study の語。Google Trends の比較セットにだけ登場） |

| プラットフォーム | 収集時点 | 化合物語 | 製品語 | 測定モード |
|---|---|---|---|---|
| Google Trends | 2026-10-02, 10-08, 10-23 | 13 語すべて（THC-O は no data） | リキッド 13 語（8 語が系列、5 語は no data） | 12ヶ月・単独系列 |
| Google Trends | 2026-10-02, 10-08, 10-14, 10-15, 10-23 | 13 語すべて | リキッド 13 語中 12 語が系列（main5 の 5 語 + 別窓の新規 7 語）。THC-O は系列なし | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（12ヶ月） |
| Google Trends | 2026-10-23 | 13 語（アンカー CBD/THC を含む 4 セット） | なし | 5年の共通スケール（`compare_terms`） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`）。CBD は追加 3 run（条件未記録） |
| YouTube | 2026-10-02（疎通検証 7 run）・2026-10-08（9 run） | —（集計物は 2026-10-29 に削除） | — | 単一クエリ |

- **化合物語は 13 語で閉じている**。このうち 12ヶ月で系列が取れていないのは THC-O だけ（no data）。
- **製品語のリキッドは Google Trends のみ**。12ヶ月は比較セットで測っているため、単独系列（上の 2 行）とは
  別の共通スケール値であり、混ぜない。
- **5年のリキッドは 13 語中 12 語が系列**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5 語 + 新規 8 run のうち 7 語）。
  新規 8 run は main5 と窓が異なる別観測であり（main5 は 2021-10-10 〜 2026-10-11、新規は 2021-10-17 〜 2026-10-18）、単独系列の値をまたいで比較しない。
  THC-O リキッドは 5年でも系列なし（`NO_DATA`）。12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。

### YouTube の収集と追跡

集計物（`youtube_runs.csv` 16 行、`youtube_videos.csv` 397 行）は 2026-10-29 に削除した（研究内に参照元の raw が無いため、owner 決定）。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE | 2026-10-24（Google Trends 5年 13/13・12ヶ月 12/13 化合物） |
| COMPLETED | — |

## 関連

- 方法と制約: [methodology.md](methodology.md)（5年 §2.1.2 / 12ヶ月 §2.1.3）
- 収集計画書: [`metadata/plans/`](metadata/plans/)、窓: [`metadata/windows/`](../../metadata/windows/)
- 既知の欠測と未決事項: [`ISS-20261023-GT-006`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-12m-recollection-findings.md)（12ヶ月の欠測・ページ数値）、
  [`ISS-20261023-GT-005`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-5y-recollection-residuals.md)（5年の窓・反復測定・公開承認）、
  [`ISS-20261024-YT-013`](../../docs/issues/active/40-provenance-storage-reproducibility/20261024_p2_youtube-raw-batch-without-metadata.md)（YouTube の `raw のみ` 8 化合物）
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/), [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
