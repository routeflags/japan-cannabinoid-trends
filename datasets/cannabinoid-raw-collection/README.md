# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

所有はソースで分かれる。**Google Trends は収集済み 15 化合物すべてがこの study 自身の raw**（5年 15/15・12ヶ月 14/15）で、**CBX の Google Trends raw も 2026-11-04 の owner 決定で `cbx-search-trends` からこの study へ移管した**（[`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)）。**YouTube は収集済み 15 化合物すべてがこの study 自身の raw** で、primary は liquid-only の 17 run（CBX を含む）。**THCNM（別名 THA）は 2026-11-04 に化合物集合へ加えた 15 番目の化合物**で、同じ日に Google Trends の初回 run（12ヶ月・5年）と、YouTube の 2 本の required primary query（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`）を採用した（YouTube primary は化合物 15/15、クエリ 16/16）。

**登録化合物は 17**（2026-11-10 に `CBC` と `CBDV` を追加）。両者は taxonomy に既存の canonical concept（`compound_cbc` / `compound_cbdv`）があるため、その ID を再利用して query だけを登録した。**run は 0 本で未収集**であり、0 観測でも欠測でもない（[`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)）。

Google Trends の被覆（収集済み 15 化合物 + 登録済み・未収集 2 化合物）:

| 範囲 | 化合物数 | Google Trends 5年 | Google Trends 12ヶ月 |
|---|---:|---:|---:|
| この study 自身の raw（収集済み） | 15 | 15/15 | 14/15（THC-O は no data） |
| 登録済み・未収集（CBC・CBDV） | 2 | 未収集（run 0） | 未収集（run 0） |

CBX を化合物間比較に載せるため、**CBX + CBD + THC を 1 リクエストで測る共通スケール bridge** を 12ヶ月・5年とも収集した（§2.1.6）。これは単独系列（各語のピーク=100）の平均を合成した値ではない。**CBX の YouTube は 2026-11-01 の owner 決定でこの study の所有**であり、`cbx-search-trends` 側に残るのは Google Search Console raw だけである（[`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本におけるカンナビノイド成分へのオンライン関心は、どのように推移しているか？
>
> Google Trends は `geo=JP`。X / YouTube は国単位のgeo filterを持たず、YouTubeは日本語の製品語「リキッド」による検索語ベースの近似を用いる（[methodology.md](methodology.md) §1.4・§2.3）。

## 対象化合物

登録 **17 化合物**（2026-11-10 に CBC・CBDV を追加）。うち **15 化合物が収集済み**で、すべてが YouTube liquid primary の run を持ち、Google Trends もこの study 自身の raw として観測済み（CBX は 2026-11-04 に所有移管）。**CBC・CBDV は canonical concept が既存のため query だけを登録した未収集の 2 化合物**で、run は 0 本（0 観測でも欠測でもない）。化合物ごとの収集状況は下表、収集条件は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3、§2.1.6、§2.3。

| No. | 化合物 | 分類 | Google Trends 12ヶ月 | Google Trends 5年 | X | YouTube raw |
|---:|--------|------|:----:|:----:|:-:|:-:|
| 1 | CBX | minor | ✅ | ✅ | — | ✅ |
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
| 15 | THCNM（別名 THA） | semisynthetic（暫定） | ✅ | ✅ | — | ✅ |
| 16 | CBC | minor | 未収集 | 未収集 | — | 未収集 |
| 17 | CBDV | minor | 未収集 | 未収集 | — | 未収集 |

読み方:

- **5年系列**: 収集済み 15 化合物すべてが週次 raw を持つ（15/15）。旧 `…-5y-baseline` run は summary-only で、どの化合物の引用元でもない（証跡として残る。[methodology.md](methodology.md) §2.1.1・§2.1.2）。
- **12ヶ月系列**: 14 化合物が週次 raw を持ち（14/15）、THC-O は Google Trends が系列を返さない。THCV・CRDH は 12ヶ月が 53 週中 1 週だけ非ゼロ（[methodology.md](methodology.md) §2.1.3）。CRDH の旧 summary（`records_crdh_12m.json`）は証跡として残るが、その記録値（`avg_12m` 1.9 等）は raw から再現できないので引用しない。
- **週次系列は全面で比較できるわけではない**: 5年は 3 つの窓に分かれ（10 化合物が 2021-10-10 〜 2026-10-11（CBX を含む）、4 化合物が 2021-10-17 〜 2026-10-18、THCNM が 2021-10-31 〜 2026-11-01）、12ヶ月も 4 窓（8 化合物が 2025-09-28 〜 2026-09-27、4 化合物が 2025-10-19 〜 2026-10-18、CBX が 2025-10-12 〜 2026-10-11、THCNM が 2025-11-02 〜 2026-11-01）に分かれる。また各 run は自分のピーク=100 に正規化されるので、単独系列の値を化合物間で比べない。化合物間の比較は共通スケール（§2.1.4・§2.1.6）でのみ行う。
- **「データなし」**: 取得はしたが Google Trends が閾値未満で系列を返さなかった。**欠測であって 0 観測ではない**。
- **「—」**: そのソースのクエリを設計していない（収集対象外）。X 列は 7 化合物だけを対象に設計しており、それ以外は「—」である。X の 6 化合物は [`datasets/cannabinoid-social-trends/`](../cbx-social-trends/) が規制前後比較として収集している。
- **「未収集」**: そのソースの query は登録済みだが adopted run が **0 本**。**0 観測でも欠測でもない**（run 0）。2026-11-10 に登録した CBC・CBDV がこの状態で、Google Trends / YouTube とも run を持たない（X は両化合物のクエリを設計していないので「—」）。
- **THCNM の状態**: 2026-11-04 に化合物集合へ加えた 15 番目の化合物。**Google Trends は 12ヶ月・5年とも収集済み**（`20261104T115425Z-google-trends-thcnm-12m` / `20261104T115431Z-google-trends-thcnm-5y`）、**YouTube も required primary の 2 本（`20261104T120627Z-youtube-…` = `THCNM リキッド`、`20261104T120805Z-youtube-…` = `THA リキッド`）が採用済み**で化合物被覆は 2/2 完了。2 run は別観測で、件数は合算しない。収集した系列は登録文字列（`THCNM` / `THA リキッド`）に一致する検索需要であり、物質そのものの観測ではない。化学的同一性は供給元・市場の記載によるもので**未確認**（`THA` は別名・商業名。[`ISS-20261104-TAX-028`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thcnm-identity-unconfirmed.md)）。
- **YouTube raw（一次被覆）**: primary は**製品語「リキッド」17 run / 15 化合物**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド + THCNM の 2 run）で、**収集対象として宣言した 15 化合物すべて**が揃う。**THCNM は 2 本の required primary query**（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）を各 1 run で持ち、**2 本揃って化合物の被覆が完了する**（片方を他方の代替にしない。run をまたいで件数を合算しない）。required primary query は **18 本**（2026-11-10 に `cbc-liquid-ja` = `CBC リキッド`、`cbdv-liquid-ja` = `CBDV リキッド` を登録）で、**adopted run があるのは 16 本**（15 化合物）。**CBC・CBDV の 2 本は未収集**なので、化合物被覆は 15/17・クエリ被覆は 16/18 である。primary 外の裸の化合物語 `HHC` 1 run は raw / catalog に**保持**するが、liquid-only primary の外であり、どの化合物の一次被覆も完成させない。run ごとに検索語と観測窓が異なるので、run をまたいで件数を合算しない（[methodology.md](methodology.md) §2.3）。
- **CBX の状態**: Google Trends は 2026-11-04 に所有をこの study へ移管した。単独系列は 5年 `20261015T042857Z-google-trends-boundary-5y`（2021-10-10 〜 2026-10-11、262 週）と 12ヶ月 `20261015T042853Z-google-trends-boundary-12m`（2025-10-12 〜 2026-10-11、53 週）、加えて 1m・3m の boundary probe と 2026-10-01 の legacy 4 run。**run id と payload は移管前と同一**で、観測のやり直しではない（[methodology.md](methodology.md) §2.1.6）。YouTube 列の CBX はこの study の own raw。CBX リキッドは製品語であり、CBX 化合物語の系列とは別観測である。
- **配布物との差**: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/) の YouTube 行は COL-033 の 6 run だけを使う。この study の YouTube raw（17 primary + 1 retained）は配布 slice の外にある（[methodology.md](methodology.md) §5.1）。THCNM はいずれの配布 slice にも入らない（COL-033 に YouTube run は無く、Google Trends 系列は配布物の公開化合物集合外）。
- Google Trends の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。単独系列（12ヶ月・5年）のほかに、比較セット／共通スケール（12ヶ月 `common-scale-*`・5年 `5y-common-scale-set*`・CBX bridge の `comparison_cbx-cbd-thc.json`）・表記事前調査・「リキッド」系クエリの run がある。

## データソース

| ソース | ツール | 状態 |
|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | ✅ own raw 5年 15/15・12ヶ月 14/15（欠測は §2.1.3）。CBX を含む共通スケール bridge は §2.1.6。**CBC・CBDV は未収集** |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ✅ 7 化合物（CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run。条件は未記録）。**geo filter なし**。CBC・CBDV のクエリは設計していない |
| YouTube | Apify `h7sDV53CddomktSi5` (`streamers/youtube-scraper`) | primary はリキッド **17 run / 15 化合物**（CBX 含む）。THCNM は 2 本の required primary query を各 1 run。**`CBC リキッド`・`CBDV リキッド` は 2026-11-10 に required primary として登録したが未収集**。裸の化合物語 `HHC` 1 run は保持するが primary 外。raw は非追跡・公開対象外（§2.3） |

> **関連データセットとの役割分担**: 本データセットはカンナビノイドのトレンド分析用 raw を収蔵する。
> [`datasets/youtube-consistency/`](../youtube-consistency/) は YouTube 検索結果の一貫性・再現性検証を目的とする別研究である。

## 収集結果

Google Trends の系列・窓・欠測は [methodology.md](methodology.md) §2.1.2・§2.1.3 と
[`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)（5年）が正本。
単独系列の平均と比較セット（`common-scale-*` の**共通スケール**値）は別物なので混ぜない。
単独系列の平均は化合物間でも比べない（正規化が語ごとに違う）。比較は共通スケールでのみ行う。
**5年の共通スケールはアンカー CBD/THC を含む 4 セット**（[methodology.md](methodology.md) §2.1.4）。
12ヶ月の共通スケールは `common-scale-*` の各 run。
**CBX は 2026-11-04 に、CBX + CBD + THC を 1 リクエストで測る bridge を 12ヶ月・5年とも収集した**（[methodology.md](methodology.md) §2.1.6）。bridge の値は同一 run 内の共通スケールであり、単独系列の平均から作った値ではない。

### 収集したキーワード

収集語は canonical の 3 種類（化合物語・製品語・アンカー語）と、その登録済み表記ゆれ（variant）からなる。各語は下表のどこかに 1 回だけ現れる。

| 種別 | 語 |
|---|---|
| 化合物語（収集 15 / 登録 17） | CBX, CBD, THC, CBG, HHC, THCV, THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH, THCNM。未収集の登録語 `CBC`・`CBDV` は「登録済み・未収集のキーワード」を参照 |
| 製品語 — リキッド（収集 15 / 登録 17） | 化合物語のうち CBX と THCNM を除く 13 語に「リキッド」を付けた形（`CBD リキッド` 〜 `THCV リキッド`、`THC-O リキッド` を含む）と、THCNM の 2 表記（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`。THA は同じ化合物の別名・商業名）。Google Trends で照会したのは 13 語、YouTube で採用済みなのは 16 語 |
| 製品語 — オイル（2） | CBD オイル, THC オイル |
| 製品語・比較アンカー | CBX リキッド（CBX 化合物語とは別観測。Google Trends の比較セットにも登場し、YouTube では primary の 1 run） |
| 表記ゆれ（variant） | `THCO`（`thc-o-general-ja` の variant）、`THCO リキッド`（`thc-o-liquid-ja` の variant）。canonical の別表記であり、化合物語・製品語の数を増やさない。`THCO` は tetrahydrocannabiorcol（Δ8-/Δ9-THCO）にも使われる別物質の表記であり、単一物質の名称ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)） |

| プラットフォーム | 収集時点 | 化合物語 | 製品語 | 測定モード |
|---|---|---|---|---|
| Google Trends | 2026-10-02, 10-08, 10-15, 10-23, 11-04 | 15 語すべて（THC-O は no data。CBX は 10-15 の boundary probe） | リキッド 13 語（8 語が系列、5 語は no data） | 12ヶ月・単独系列 |
| Google Trends | 2026-10-02, 10-08, 10-14, 10-15, 10-23, 11-04 | 15 語すべて（CBX は 10-15 の boundary probe） | リキッド 13 語中 12 語が系列（main5 の 5 語 + 別窓の新規 7 語）。THC-O は系列なし | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（12ヶ月） |
| Google Trends | 2026-10-23 | 13 語（アンカー CBD/THC を含む 4 セット） | なし | 5年の共通スケール（`compare_terms`） |
| Google Trends | 2026-11-04 | CBX + アンカー CBD/THC の 3 語 | なし | CBX bridge の共通スケール（12ヶ月・5年、`compare_terms`。§2.1.6） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`）。CBD は追加 3 run（条件未記録） |
| YouTube | 2026-10-10, 10-11, 11-01, 11-04 | 裸の `HHC` 1 run（保持・primary 外） | リキッド **15 化合物 / 17 run**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド、および THCNM の 2 表記 = `THCNM リキッド`・`THA リキッド`） | 1 run 1 クエリ。**geo filter なし**。日本語「リキッド」語による近似的な市場限定 |

- **収集済みの化合物語は 15 語**（CBX を含む。2026-11-04 の所有移管で対象に確定）。2026-11-10 に `CBC`・`CBDV` を登録して**登録集合は 17 語**になったが、両語は未収集（「登録済み・未収集のキーワード」）。このうち 12ヶ月で系列が取れていないのは THC-O だけ（no data）。
- **表記ゆれ（2026-11-04）**: THC-O の `THCO` と `THCO リキッド` を `query-variants.json` に登録し、canonical の `query_id` のまま別 run として 12ヶ月・5年を収集した（Google Trends、geo JP）。canonical の `THC-O`（12ヶ月 no data・5年系列）と `THC-O リキッド`（no data）を置換・統合しない。run 一覧は [methodology.md](methodology.md) §2.1.5。
  - **`THCO` 表記で別系列がある**: 12ヶ月 53 週・非ゼロ 3（`20261104T135330Z-google-trends-thc-o-general-thco-12m`）、5年 262 週・非ゼロ 90（`20261104T135339Z-google-trends-thc-o-general-thco-5y`）。`THCO リキッド`は12ヶ月53週・非ゼロ1、5年262週・非ゼロ23。
  - canonicalの「12ヶ月 no data」は維持する。variantで系列が返ることはcanonicalのno dataを否定・置換しない。canonicalとvariantの値は合算しない。
  - `THCO`はPubMed/PubChem等で`THC-O-acetate`の略記として使われる一方、Δ8-THCO/Δ9-THCO（tetrahydrocannabiorcol）という別物質にも使われる。variantは検索文字列の対応であり、単一CAS・構造の同定ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)）。
- **THCNM（`thcnm-general-ja`）は 2026-11-04 に Google Trends の 12ヶ月・5年を収集した**（化合物語 14 語の最後）。同じ日に YouTube の 2 表記（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）も各 1 run で採用した。THA は同じ化合物の別名・商業名であり、別の収集語・別物質ではない（2 run は別観測で、件数を合算しない）。
- **製品語のリキッド**は Google Trends と YouTube で使う。YouTube の primary はリキッド **17 run / 15 化合物**（HHBD・H4CBH・CBD ×2・CBN・CRDH・HHC・CBG・CRDP・THC・THC-O・THCH・THCV・HHCH・CBX リキッド + THCNM の 2 run）。2026-11-10 に `CBC リキッド`（`cbc-liquid-ja`）・`CBDV リキッド`（`cbdv-liquid-ja`）を required primary query として登録したが、**run は 0 本（未収集）**。裸の `HHC` 1 run は保持するが primary 外で、対の必須 run でもない。
  Google Trends の比較セットは単独系列とは別の共通スケール値であり、混ぜない。
- **5年のリキッドは 13 語中 12 語が系列**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5 語 + 新規 8 run のうち 7 語）。
  新規 8 run は main5 と窓が異なる別観測であり（main5 は 2021-10-10 〜 2026-10-11、新規は 2021-10-17 〜 2026-10-18）、単独系列の値をまたいで比較しない。
  THC-O リキッドは 5年でも系列なし（`NO_DATA`）。12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。

### 登録済み・未収集のキーワード（2026-11-10）

2026-11-10 に登録した 2 化合物は、canonical identity が taxonomy に既にあったため **ID・分類を新設せずに再利用**し、query だけを登録した。**run は 1 本も無い**。

| 化合物 | `compound_id` | query（`intent_id`） | 状態 |
|---|---|---|---|
| CBC | `compound_cbc` | `CBC`（`compound_general`）= `cbc-general-ja`、`CBC リキッド`（`product_liquid`）= `cbc-liquid-ja` | 未収集（Google Trends / YouTube / X とも run 0） |
| CBDV | `compound_cbdv` | `CBDV`（`compound_general`）= `cbdv-general-ja`、`CBDV リキッド`（`product_liquid`）= `cbdv-liquid-ja` | 未収集（同上） |

- 未収集は **0 観測でも欠測でもない**。表の ✅ とも「データなし」（no data）とも読み替えない。
- 登録は「対象集合とクエリ設計の拡張」であり、収集・raw payload 作成・採用・公開・release slice の拡張は行っていない。
- `CBC` はカナダ放送協会など化合物以外の略号と衝突する。登録文字列は物質の同定ではなく、**その文字列に一致するコンテンツ**を測る（収集した場合も同じ）。
- 同じ追加依頼で挙げられた残りの語（THCB / THCP / THCJD / THCPO / CBE / HHCPO / CBND / CBL / CBGa / CBP / 10-OH-HHC / THXE / THCA）は **canonical identity が未登録**のため保留し、query も登録していない。理由と必要な確認事項は [`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)。

### YouTube の収集と追跡

クエリ設計は [methodology.md](methodology.md) §2.3 と [`metadata/query-design.json`](metadata/query-design.json) が正本。**primary は liquid-only**: `<compound> リキッド`（`product_liquid`）17 run / 15 化合物。required primary query は **18 本**: 2026-11-04 時点で **16 本に adopted run がある**（収集済み 15 本（14 化合物、CBD のみ 2 run）と `compound_thcnm` の 2 本（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`、各 1 run））が、2026-11-10 に登録した `cbc-liquid-ja`・`cbdv-liquid-ja` の **2 本は未収集（run 0）**。被覆は**クエリ単位と化合物単位の両方**で報告し、化合物は自身の required primary query が全部揃って初めて完了する（`make audit-youtube-coverage` は 化合物 15/17・クエリ 16/18、`partial_compounds=0`、`missing_compounds=2`（`compound_cbc`・`compound_cbdv`）、および THCNM について `primary coverage 2/2` を報告する）。`query-design.json` の `compound_set.declared_not_yet_collected` はこの 2 化合物を `state: not_collected` で列挙する。裸の化合物語 `HHC` 1 run は raw / catalog に保持するが **primary coverage 外**であり、HHC の liquid run と対にする必須 run ではない。

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
| primary | `THCNM リキッド` | `all` | 30 | 2017-11-30 〜 2026-11-03 | [`20261104T120627Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261104T120627Z-youtube-cannabinoid-raw-collection/) |
| primary | `THA リキッド` | `all` | 311 | 2012-01-17 〜 2026-11-05 | [`20261104T120805Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261104T120805Z-youtube-cannabinoid-raw-collection/) |
| **retained / out-of-scope** | `HHC`（裸語） | `all` | 482 | 2006-09-05 〜 2026-11-02 | [`20261101T085920Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T085920Z-youtube-cannabinoid-raw-collection/) |

- **request と観測窓は別物**。Actor 入力に `dateFilter` を渡していない run は、絶対日付窓もローリング窓も持たない。表の窓は payload の動画公開日を UTC の半開区間 `[start, end_exclusive)` に正規化した**観測**であり、検索条件ではない。request の事実は `collection_request`（`date_filter` / `reference_time` / actor input）に、観測窓は `window` に記録する（[methodology.md](methodology.md) §2.3）。
- CBD リキッドの 2 run は観測窓と `date_filter` が異なる別観測。統合せず、run をまたいで件数を合算しない。
- `HHC`（裸語）は保持するが primary 外。`HHC リキッド` の有無を補うための run ではなく、liquid coverage を完成させない。件数も primary に加算しない。
- 件数は検索結果として返された動画の標本数で、YouTube 全体の投稿数ではない。
- 2026-11-01 の liquid 8 クエリ一括実行は、最初の試行で 2 クエリ（HHCH・THCH）だけが完走し、残り 6 クエリは Apify アカウントの請求サイクル上限で中断した。上限引き上げ後の再実行（同日 11:14〜11:33Z、3 run ずつ）では 6 クエリすべてが SUCCEEDED になり、CBG・CRDP・THC・THC-O・THCV の 5 run を採用した。CBX はその時点では採用先未決だったが、同じ 2026-11-01 の owner 決定（YouTube はこの study が所有し、CBX の Google Trends / GSC raw は `cbx-search-trends` に残す）を受けて、完全 payload を採用した。中断時の部分 payload は raw に採用していない（[ISS-20261101-YT-019](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。
- 2026-11-04 の THCNM 2 run（`THCNM リキッド` / `THA リキッド`）は同じ入力を用いる**別 run** として 1 回ずつ実行し、両方 SUCCEEDED（status は actor run status object による）。
  1 run 1 クエリ、`maxResults` 500・`maxResultsShorts` 0・`maxResultStreams` 0、`dateFilter` なし。件数は 30 と 311 で、
  **片方が他方の代替でも合算対象でもない**（`THA` は同じ化合物の別名・商業名であり、2 run は 2 つの検索文字列を測る）。
  採用宣言は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)。
  payload は Git 非追跡（`git_untracked`）で、宣言・catalog・run metadata が committed 側の証跡、payload はこの checkout のローカル証跡。
- 採用宣言: HHBD は [`20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json)、リキッド 5 run は [`20261015-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261015-youtube-liquid-batch-cannabinoid-raw-collection.json)、HHC 2 run は [`20261101-youtube-hhc-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-cannabinoid-raw-collection.json) / [`20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json)、2026-11-01 の HHCH・THCH 2 run は [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)、再実行の CBG・CRDP・THC・THC-O・THCV 5 run は [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)、CBX は [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json)、THCNM 2 run は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)（いずれも `staging-declaration-v1`、L1 を経て catalog）。
- HHC 2 run の request 語彙・actor build・実行状態の訂正は [`20261101-youtube-hhc-request-parameters.json`](../../metadata/provenance/corrections/20261101-youtube-hhc-request-parameters.json) に記録する。元の宣言は handover hash を保つため書き換えず、訂正版 declaration を併置する。
- `maxResults` が現行 Actor の正規名。旧宣言の `max_videos` は歴史的記録としてのみ読み、新規入力に使わない。
- **配布制限**: この study の YouTube raw は [`cannabinoid-platform-trends`](../cannabinoid-platform-trends/) の配布 slice（COL-033 の 6 run）には含まれない。HHC の raw はこの study に採用済みだが、配布物の `not_collected` は「配布 slice に無い」という意味であり、この study で未収集という意味ではない。
- 月別の検索結果件数は [`data/processed/youtube_monthly_counts.csv`](data/processed/youtube_monthly_counts.csv)。この中間集計は HHBD リキッド run に固定され、当該 CSV の SHA-256 に限って公開承認済み（[審査記録](../../metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json)）。他の 17 run の集計はまだ作っていない。
- 外部公開・リリースは実施していない。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE（Google Trends 部分のみ） | 2026-11-04（own raw 5年 15/15・12ヶ月 14/15。THCNM の 12ヶ月・5年と CBX の所有移管・bridge は 2026-11-04 に追加） |
| COMPLETED | — |

> **YouTube の liquid-only primary は、収集対象として宣言した 15 化合物すべてで完了。** その 15 化合物すべてに liquid run があり（17 run、CBD のみ 2 run、THCNM のみ 2 クエリで 2 run）、収集済み化合物に未採用はない。THCNM は 2026-11-04 に集合へ追加し、同日 `THCNM リキッド` と `THA リキッド` の 2 本を required primary として各 1 run で採用した（化合物被覆 2/2）。裸の `HHC` run は保持された primary 外証跡で、primary の内訳には数えない（`make audit-youtube-coverage` が 化合物 15/17・クエリ 16/18、`partial_compounds=0`、`missing_compounds=2`（`compound_cbc`・`compound_cbdv`）、retained 1、THCNM につき `primary coverage 2/2` を報告する）。**CBC・CBDV は 2026-11-10 に登録したが未収集**で、missing はその run 0 の 2 化合物だけである。`COLLECTION_COMPLETE` は、登録集合を 17 に広げる前の 15 化合物について Google Trends と YouTube の収集が揃った状態を指し、X は CBD・THC・CBG・HHC・THCV・THC-O・THCH の 7 化合物に限られ、全体の COMPLETED は未宣言。

## 関連

- 方法と制約: [methodology.md](methodology.md)（5年 §2.1.2 / 12ヶ月 §2.1.3 / 5年の共通スケール §2.1.4 / CBX の所有移管と bridge §2.1.6 / YouTube §2.3）
- YouTube クエリ設計: [`metadata/query-design.json`](metadata/query-design.json)（`youtube-liquid-only-primary`）
- 収集計画書: [`metadata/plans/`](metadata/plans/)、窓: [`metadata/windows/`](../../metadata/windows/)
- 既知の欠測と未決事項: [`ISS-20261023-GT-006`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-12m-recollection-findings.md)（12ヶ月の欠測・ページ数値）、
  [`ISS-20261023-GT-005`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-5y-recollection-residuals.md)（5年の窓・反復測定・公開承認）、
  [`ISS-20261024-YT-013`](../../docs/issues/active/40-provenance-storage-reproducibility/20261024_p2_youtube-raw-batch-without-metadata.md)（YouTube の `raw のみ` 8 化合物）、
  [`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)（CBX の対象化と Google Trends 所有の移管・bridge）,
  [`ISS-20261101-PRV-017`](../../docs/issues/active/40-provenance-storage-reproducibility/20261101_p2_audit-snapshots-require-local-raw.md)（監査スナップショットと raw 不在）、
  [`ISS-20261101-PRV-018`](../../docs/issues/active/40-provenance-storage-reproducibility/20261101_p2_catalog-declaration-raw-mismatch.md)（catalog / declaration / raw の不一致）、
  [`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)（2026-11-01 の liquid 一括収集と CBX YouTube の所有）、
  [`ISS-20261104-TAX-028`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thcnm-identity-unconfirmed.md)（THCNM の同一性未確認と収集済み）、
  [`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)（THCO 表記の証拠と化学的同一性の留保）、
  [`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)（CBC・CBDV の登録と未収集、identity 未登録 13 語の保留）
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/)（Google Search Console raw の正本。CBX の Google Trends raw は 2026-11-04 に本 study へ移管済み）, [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
