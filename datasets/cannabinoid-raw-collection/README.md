# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

所有はソースで分かれる。**Google Trends は CBX 以外の 13 化合物がこの study 自身の raw**（5年 13/13・12ヶ月 12/13）で、**CBX の Google Trends 正本は [`datasets/cbx-search-trends/`](../cbx-search-trends/) を参照**する（raw の重複複製は行わない）。**YouTube は 14 化合物すべてがこの study 自身の raw** で、primary は liquid-only の 15 run（CBX を含む）。

| 範囲 | 化合物数 | Google Trends 5年 | Google Trends 12ヶ月 |
|---|---:|---:|---:|
| この study 自身の raw（CBX 以外） | 13 | 13/13 | 12/13（THC-O は no data） |
| CBX 参照込み | 14 | 14/14 | 13/14 |

CBX の Google Trends を参照する扱いは [`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md) の決定事項で、本 README はその参照関係を記録する。**CBX の YouTube は 2026-11-01 の owner 決定でこの study の所有**になり、`cbx-search-trends` 側の Google Trends / GSC raw は移動も複製もしない（[`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本国内の検索需要（Google Trends、`geo=JP`）と、国単位のフィルタを持たない X / YouTube 上の言及・動画コンテンツはどう推移しているか？
>
> YouTube は API の geo filter を持たない。日本語の製品語「リキッド」による検索語ベースの近似的な日本市場限定を使っており、これは geo 保証ではない（[methodology.md](methodology.md) §1.4・§2.3）。

## 対象化合物

合計 **14 化合物**。ソースごとの所有は上のとおり（Google Trends は CBX を参照、YouTube は 14 化合物すべて own raw）。化合物ごとの収集状況は下表、収集条件は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3、§2.3。

| No. | 化合物 | 分類 | Google Trends 12ヶ月 | Google Trends 5年 | X | YouTube raw |
|---:|--------|------|:----:|:----:|:-:|:-:|
| 1 | CBX | minor | ✅* | ✅* | — | ✅ |
| 2 | CBD | major | ✅ | ✅ | ✅ | ✅ |
| 3 | THC | major | ✅ | ✅ | ✅ | ✅ |
| 4 | CBG | minor | ✅ | ✅ | ✅ | ✅ |
| 5 | HHC | semisynthetic | ✅ | ✅ | ✅ | ✅ |
| 6 | THCV | minor | ✅ | ✅ | ✅ | ✅ |
| 7 | THC-O | semisynthetic | データなし | ✅ | ✅ | ✅ |
| 8 | THCH | minor | ✅ | ✅ | ✅ | ✅ |
| 9 | CBN | minor | ✅ | ✅ | — | ✅ |
| 10 | CRDH | synthetic | ✅ | ✅ | — | ✅ |
| 11 | CRDP | synthetic | ✅ | ✅ | — | ✅ |
| 12 | H4CBH | semisynthetic | ✅ | ✅ | — | ✅ |
| 13 | HHBD | semisynthetic | ✅ | ✅ | — | ✅ |
| 14 | HHCH | synthetic | ✅ | ✅ | — | ✅ |

読み方:

- **5年系列**: この study 自身の raw は 13 化合物すべてが週次 raw を持つ（13/13）。CBX の正本は [`datasets/cbx-search-trends/`](../cbx-search-trends/) にあり、参照込みでは 14/14。旧 `…-5y-baseline` run は summary-only で、どの化合物の引用元でもない（証跡として残る。[methodology.md](methodology.md) §2.1.1・§2.1.2）。
- **12ヶ月系列**: この study 自身の raw は 12 化合物が週次 raw を持ち（12/13）、THC-O は Google Trends が系列を返さない。CBX の既存 12ヶ月 series を参照に加えると 13/14。THCV・CRDH は 12ヶ月が 53 週中 1 週だけ非ゼロ（[methodology.md](methodology.md) §2.1.3）。CRDH の旧 summary（`records_crdh_12m.json`）は証跡として残るが、その記録値（`avg_12m` 1.9 等）は raw から再現できないので引用しない。
- **週次系列は全面で比較できるわけではない**: 5年は 2 つの窓に分かれ（9 化合物が 2021-10-10 〜、4 化合物が 2021-10-17 〜）、12ヶ月も 2 窓に分かれる。また各 run は自分のピーク=100 に正規化されるので、単独系列の値を化合物間で比べない。化合物間の比較は共通スケール（§2.1.4）でのみ行う。
- **「データなし」**: 取得はしたが Google Trends が閾値未満で系列を返さなかった。**欠測であって 0 観測ではない**。
- **「—」**: そのソースで採用済みの観測がない（未収集）。X の 6 化合物は [`datasets/cannabinoid-social-trends/`](../cbx-social-trends/) が規制前後比較として収集している。
- **YouTube raw（一次被覆）**: primary は**製品語「リキッド」15 run / 14 化合物**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド）で、14 化合物すべてが揃う。primary 外の裸の化合物語 `HHC` 1 run は raw / catalog に**保持**するが、liquid-only primary の外であり、どの化合物の一次被覆も完成させない。run ごとに検索語と観測窓が異なるので、run をまたいで件数を合算しない（[methodology.md](methodology.md) §2.3）。
- **CBX の表記（*）**: 表の Google Trends 列の CBX は別 study に保存された raw を参照する（この study 自身の Google Trends raw ではない）。YouTube 列の CBX はこの study の own raw である。CBX リキッドは製品語であり、CBX 化合物語の系列とは別観測である。
- **配布物との差**: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/) の YouTube 行は COL-033 の 6 run だけを使う。この study の YouTube raw（15 primary + 1 retained）は配布 slice の外にある（[methodology.md](methodology.md) §5.1）。
- Google Trends の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。単独系列（12ヶ月・5年）のほかに、比較セット／共通スケール（12ヶ月 `common-scale-*`・5年 `5y-common-scale-set*`）・表記事前調査・「リキッド」系クエリの run がある。

## データソース

| ソース | ツール | 状態 |
|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | ✅ own raw 5年 13/13・12ヶ月 12/13。CBX 参照込みで 5年 14/14・12ヶ月 13/14（欠測は §2.1.3） |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ✅ 7 化合物（CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run。条件は未記録）。**geo filter なし** |
| YouTube | Apify `h7sDV53CddomktSi5` (`streamers/youtube-scraper`) | primary はリキッド **15 run / 14 化合物**（CBX 含む）。裸の化合物語 `HHC` 1 run は保持するが primary 外。raw は非追跡・公開対象外（§2.3） |

> **関連データセットとの役割分担**: 本データセットはカンナビノイドのトレンド分析用 raw を収蔵する。
> [`datasets/youtube-consistency/`](../youtube-consistency/) は YouTube 検索結果の一貫性・再現性検証を目的とする別研究である。

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
| 製品語・比較アンカー | CBX リキッド（CBX 化合物語とは別観測。Google Trends の比較セットにも登場し、YouTube では primary の 1 run） |

| プラットフォーム | 収集時点 | 化合物語 | 製品語 | 測定モード |
|---|---|---|---|---|
| Google Trends | 2026-10-02, 10-08, 10-23 | 13 語すべて（THC-O は no data） | リキッド 13 語（8 語が系列、5 語は no data） | 12ヶ月・単独系列 |
| Google Trends | 2026-10-02, 10-08, 10-14, 10-15, 10-23 | 13 語すべて | リキッド 13 語中 12 語が系列（main5 の 5 語 + 別窓の新規 7 語）。THC-O は系列なし | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（12ヶ月） |
| Google Trends | 2026-10-23 | 13 語（アンカー CBD/THC を含む 4 セット） | なし | 5年の共通スケール（`compare_terms`） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`）。CBD は追加 3 run（条件未記録） |
| YouTube | 2026-10-10, 10-11, 11-01 | 裸の `HHC` 1 run（保持・primary 外） | リキッド **14 化合物 / 15 run**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド） | 1 run 1 クエリ。**geo filter なし**。日本語「リキッド」語による近似的な市場限定 |

- **化合物語は 13 語で閉じている**。このうち 12ヶ月で系列が取れていないのは THC-O だけ（no data）。
- **製品語のリキッド**は Google Trends と YouTube で使う。YouTube の primary はリキッド **15 run / 14 化合物**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド）。裸の `HHC` 1 run は保持するが primary 外で、対の必須 run でもない。
  Google Trends の比較セットは単独系列とは別の共通スケール値であり、混ぜない。
- **5年のリキッドは 13 語中 12 語が系列**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5 語 + 新規 8 run のうち 7 語）。
  新規 8 run は main5 と窓が異なる別観測であり（main5 は 2021-10-10 〜 2026-10-11、新規は 2021-10-17 〜 2026-10-18）、単独系列の値をまたいで比較しない。
  THC-O リキッドは 5年でも系列なし（`NO_DATA`）。12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。

### YouTube の収集と追跡

クエリ設計は [methodology.md](methodology.md) §2.3 と [`metadata/query-design.json`](metadata/query-design.json) が正本。**primary は liquid-only**: `<compound> リキッド`（`product_liquid`）15 run / 14 化合物。裸の化合物語 `HHC` 1 run は raw / catalog に保持するが **primary coverage 外**であり、HHC の liquid run と対にする必須 run ではない。

いずれも `data/raw/youtube/<run-id>/` に置き、raw は非追跡かつ公開対象外。raw は machine-local のため、clone によっては下表のリンク先が存在しない（catalog / declaration は committed、payload は手元の証跡）。

| 区分 | 検索語 | `date_filter` | 件数 | 観測窓（UTC、`end_exclusive`） | run |
|---|---|---|---:|---|---|
| primary | `HHBD リキッド` | `all` | 224 | 2020-09-30 〜 2026-10-06 | [`20261010T141947Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T141947Z-youtube-cannabinoid-raw-collection/) |
| primary | `H4CBH リキッド` | `all` | 395 | 2020-10-01 〜 2026-10-02 | [`20261010T143430Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T143430Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBD リキッド` | `all` | 456 | 2014-11-17 〜 2026-10-10 | [`20261010T144422Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T144422Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBN リキッド` | `all` | 468 | 2008-08-01 〜 2026-09-24 | [`20261010T145729Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T145729Z-youtube-cannabinoid-raw-collection/) |
| primary | `CRDH リキッド` | `all` | 352 | 2022-09-29 〜 2026-09-12 | [`20261010T164917Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T164917Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBD リキッド` | `year` | 393 | 2025-10-11 〜 2026-10-10 | [`20261011T191902Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261011T191902Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHC リキッド` | `all` | 412 | 2013-06-25 〜 2026-09-20 | [`20261101T091646Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T091646Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHCH リキッド` | `all` | 138 | 2012-04-09 〜 2026-10-18 | [`20261101T105037Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T105037Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCH リキッド` | `all` | 240 | 2011-06-07 〜 2026-09-15 | [`20261101T105058Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T105058Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBG リキッド` | `all` | 219 | 2017-05-17 〜 2026-10-18 | [`20261101T111408Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111408Z-youtube-cannabinoid-raw-collection/) |
| primary | `CRDP リキッド` | `all` | 433 | 2016-06-18 〜 2026-10-18 | [`20261101T111429Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111429Z-youtube-cannabinoid-raw-collection/) |
| primary | `THC リキッド` | `all` | 435 | 2009-05-01 〜 2026-10-30 | [`20261101T111450Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111450Z-youtube-cannabinoid-raw-collection/) |
| primary | `THC-O リキッド` | `all` | 388 | 2015-10-30 〜 2026-11-01 | [`20261101T112513Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112513Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCV リキッド` | `all` | 435 | 2011-08-15 〜 2026-10-15 | [`20261101T112534Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112534Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBX リキッド` | `all` | 329 | 2010-03-19 〜 2026-10-28 | [`20261101T112555Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112555Z-youtube-cannabinoid-raw-collection/) |
| **retained / out-of-scope** | `HHC`（裸語） | `all` | 482 | 2006-09-05 〜 2026-11-02 | [`20261101T085920Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T085920Z-youtube-cannabinoid-raw-collection/) |

- **request と観測窓は別物**。Actor 入力に `dateFilter` を渡していない run は、絶対日付窓もローリング窓も持たない。表の窓は payload の動画公開日を UTC の半開区間 `[start, end_exclusive)` に正規化した**観測**であり、検索条件ではない。request の事実は `collection_request`（`date_filter` / `reference_time` / actor input）に、観測窓は `window` に記録する（[methodology.md](methodology.md) §2.3）。
- CBD リキッドの 2 run は観測窓と `date_filter` が異なる別観測。統合せず、run をまたいで件数を合算しない。
- `HHC`（裸語）は保持するが primary 外。`HHC リキッド` の有無を補うための run ではなく、liquid coverage を完成させない。件数も primary に加算しない。
- 件数は検索結果として返された動画の標本数で、YouTube 全体の投稿数ではない。
- 2026-11-01 の liquid 8 クエリ一括実行は、最初の試行で 2 クエリ（HHCH・THCH）だけが完走し、残り 6 クエリは Apify アカウントの請求サイクル上限で中断した。上限引き上げ後の再実行（同日 11:14〜11:33Z、3 run ずつ）では 6 クエリすべてが SUCCEEDED になり、CBG・CRDP・THC・THC-O・THCV の 5 run を採用した。CBX はその時点では採用先未決だったが、同じ 2026-11-01 の owner 決定（YouTube はこの study が所有し、CBX の Google Trends / GSC raw は `cbx-search-trends` に残す）を受けて、完全 payload を採用した。中断時の部分 payload は raw に採用していない（[ISS-20261101-YT-019](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。
- 採用宣言: HHBD は [`20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json)、リキッド 5 run は [`20261015-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261015-youtube-liquid-batch-cannabinoid-raw-collection.json)、HHC 2 run は [`20261101-youtube-hhc-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-cannabinoid-raw-collection.json) / [`20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json)、2026-11-01 の HHCH・THCH 2 run は [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)、再実行の CBG・CRDP・THC・THC-O・THCV 5 run は [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)、CBX は [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json)（いずれも `staging-declaration-v1`、L1 を経て catalog）。
- HHC 2 run の request 語彙・actor build・実行状態の訂正は [`20261101-youtube-hhc-request-parameters.json`](../../metadata/provenance/corrections/20261101-youtube-hhc-request-parameters.json) に記録する。元の宣言は handover hash を保つため書き換えず、訂正版 declaration を併置する。
- `maxResults` が現行 Actor の正規名。旧宣言の `max_videos` は歴史的記録としてのみ読み、新規入力に使わない。
- **配布制限**: この study の YouTube raw は [`cannabinoid-platform-trends`](../cannabinoid-platform-trends/) の配布 slice（COL-033 の 6 run）には含まれない。HHC の raw はこの study に採用済みだが、配布物の `not_collected` は「配布 slice に無い」という意味であり、この study で未収集という意味ではない。
- 月別の検索結果件数は [`data/processed/youtube_monthly_counts.csv`](data/processed/youtube_monthly_counts.csv)。この中間集計は HHBD リキッド run に固定され、当該 CSV の SHA-256 に限って公開承認済み（[審査記録](../../metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json)）。他の 15 run の集計はまだ作っていない。
- 外部公開・リリースは実施していない。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE（Google Trends 部分のみ） | 2026-10-24（own raw 5年 13/13・12ヶ月 12/13。CBX 参照込みで 5年 14/14・12ヶ月 13/14） |
| COMPLETED | — |

> **YouTube の liquid-only primary は完了。** 14 化合物すべてに liquid run があり（15 run、CBD のみ 2 run）、未採用の化合物はない。裸の `HHC` run は保持された primary 外証跡で、primary の内訳には数えない（`make audit-youtube-coverage` が 15 run / 14 化合物、retained 1 を報告する）。`COLLECTION_COMPLETE` は引き続き Google Trends 部分に限る。

## 関連

- 方法と制約: [methodology.md](methodology.md)（5年 §2.1.2 / 12ヶ月 §2.1.3 / YouTube §2.3）
- YouTube クエリ設計: [`metadata/query-design.json`](metadata/query-design.json)（`youtube-liquid-only-primary`）
- 収集計画書: [`metadata/plans/`](metadata/plans/)、窓: [`metadata/windows/`](../../metadata/windows/)
- 既知の欠測と未決事項: [`ISS-20261023-GT-006`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-12m-recollection-findings.md)（12ヶ月の欠測・ページ数値）、
  [`ISS-20261023-GT-005`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-5y-recollection-residuals.md)（5年の窓・反復測定・公開承認）、
  [`ISS-20261024-YT-013`](../../docs/issues/active/40-provenance-storage-reproducibility/20261024_p2_youtube-raw-batch-without-metadata.md)（YouTube の `raw のみ` 8 化合物）、
  [`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)（CBX の Google Trends 参照の扱い）、
  [`ISS-20261101-PRV-017`](../../docs/issues/active/40-provenance-storage-reproducibility/20261101_p2_audit-snapshots-require-local-raw.md)（監査スナップショットと raw 不在）、
  [`ISS-20261101-PRV-018`](../../docs/issues/active/40-provenance-storage-reproducibility/20261101_p2_catalog-declaration-raw-mismatch.md)（catalog / declaration / raw の不一致）、
  [`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)（2026-11-01 の liquid 一括収集と CBX YouTube の所有）
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/)（CBX の Google Trends / GSC raw の正本）, [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
