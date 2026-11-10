# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

所有はソースで分かれる。**Google Trends は登録 30 語のうち 26 語が 5年、20 語が 12ヶ月で adopted 系列を持つ**。**YouTube は liquid-only primary の 31 run が adopted**で、登録 30 化合物のうち 29 化合物・required primary query 31 本のうち 30 本を被覆する（欠けは `compound_thca` の 1 クエリ）。**CBX の Google Trends raw は 2026-11-04 の owner 決定で `cbx-search-trends` からこの study へ移管済み**（[`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)）。**YouTube はこの study 自身の raw** で、**THCNM（別名 THA）は 2 本の required primary query**（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`）を各 1 run で持つ。

**登録化合物は 30**。既存 15 化合物（CBX, CBD, THC, CBG, HHC, THCV, THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH, THCNM）に、追加 15 語（CBC, CBDV, THCB, THCP, THCJD, THCPO, CBE, HHCPO, CBND, CBL, CBGa, CBP, 10-OH-HHC, THXE, THCA）を加えた集合である。CBC・CBDV は taxonomy に既存の canonical concept（`compound_cbc` / `compound_cbdv`）があるため ID を再利用し、残り 13 語は**管理上の登録状態カテゴリ `compound_identity_unverified`**（化学的同一性は未確認。経路・天然存在・化学クラス・構造・別名・規制状態を主張しない）に登録した。owner の依頼文は「17 物質」だが列挙は 15 語で、不足する 2 語は推測で補っていない（[`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)、[`ISS-20261111-TAX-040`](../../docs/issues/active/50-taxonomy-standards/20261111_p1_compound-registration-state-batch.md)）。

Google Trends の被覆（登録 30 語）:

| 範囲 | 化合物数 | Google Trends 5年 | Google Trends 12ヶ月 |
|---|---:|---:|---:|
| 既存 15 化合物 | 15 | 15/15 | 14/15（THC-O は NO_DATA） |
| 追加 15 語 | 15 | 11/15（NO_DATA 1・HTTP 429 3） | 6/15（NO_DATA 6・HTTP 429 3） |
| **登録 30 語** | **30** | **26/30** | **20/30** |

追加 15 語の内訳は、13 語バッチが 14/26 adopted（5年 9/13・12ヶ月 5/13）、CBC・CBDV が 4 run 中 3 adopted（CBDV の 12ヶ月は記録された HTTP 429 の後に NO_DATA）。採用されなかった 13 本は quarantine に残り、0 観測でも欠測でもない（§2.1.2・§2.1.3）。

CBX を化合物間比較に載せるため、**CBX + CBD + THC を 1 リクエストで測る共通スケール bridge** を 12ヶ月・5年とも収集した（§2.1.6）。これは単独系列（各語のピーク=100）の平均を合成した値ではない。**CBX の YouTube は 2026-11-01 の owner 決定でこの study の所有**であり、`cbx-search-trends` 側に残るのは Google Search Console raw だけである（[`ISS-20261101-YT-019`](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本におけるカンナビノイド成分へのオンライン関心は、どのように推移しているか？
>
> Google Trends は `geo=JP`。X / YouTube は国単位のgeo filterを持たず、YouTubeは日本語の製品語「リキッド」による検索語ベースの近似を用いる（[methodology.md](methodology.md) §1.4・§2.3）。

## 対象化合物

登録 **30 化合物**。既存 15 化合物は Google Trends・YouTube とも adopted run を持ち、追加 15 語も Google Trends / YouTube の少なくとも一方で adopted run を持つ（THCA の YouTube は `NO_VIDEOS` で未採用）。CBC・CBDV は taxonomy の既存 concept を再利用し、13 語は管理カテゴリ `compound_identity_unverified` に登録した。**13 語の adopted 系列が測るのは登録された検索文字列に一致する需要であり、物質の同定・存在・化学クラスを主張しない**。化合物ごとの状態は下表、収集条件は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3、§2.1.6、§2.3。

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
| 16 | CBC | minor | ✅ | ✅ | — | ✅ |
| 17 | CBDV | minor | データなし | ✅ | — | ✅ |
| 18 | THCB | 未確認（登録状態） | データなし | ✅ | — | ✅ |
| 19 | THCP | 未確認（登録状態） | ✅ | ✅ | — | ✅ |
| 20 | THCJD | 未確認（登録状態） | 失敗（429） | ✅ | — | ✅ |
| 21 | THCPO | 未確認（登録状態） | データなし | ✅ | — | ✅ |
| 22 | CBE | 未確認（登録状態） | ✅ | ✅ | — | ✅（331、partial） |
| 23 | HHCPO | 未確認（登録状態） | データなし | ✅ | — | ✅ |
| 24 | CBND | 未確認（登録状態） | ✅ | ✅ | — | ✅ |
| 25 | CBL | 未確認（登録状態） | ✅ | ✅ | — | ✅（269、partial） |
| 26 | CBGa | 未確認（登録状態） | データなし | データなし | — | ✅ |
| 27 | CBP | 未確認（登録状態） | ✅ | ✅ | — | ✅ |
| 28 | 10-OH-HHC | 未確認（登録状態） | データなし | 失敗（429） | — | ✅ |
| 29 | THXE | 未確認（登録状態） | 失敗（429） | 失敗（429） | — | ✅ |
| 30 | THCA | 未確認（登録状態） | 失敗（429） | 失敗（429） | — | 未採用（NO_VIDEOS） |

読み方:

- **5年系列**: 登録 30 語のうち **26 語が adopted**（既存 15/15、追加 11/15）。追加の採用なし 4 語は CBGa（NO_DATA）と 10-OH-HHC・THXE・THCA（HTTP 429、quarantine）。旧 `…-5y-baseline` run は summary-only で、どの化合物の引用元でもない（証跡として残る。[methodology.md](methodology.md) §2.1.1・§2.1.2）。
- **12ヶ月系列**: 登録 30 語のうち **20 語が adopted**（既存 14/15、追加 6/15）。既存の THC-O は NO_DATA。追加の採用なし 9 語は NO_DATA 6（CBDV・THCB・THCPO・HHCPO・CBGa・10-OH-HHC）と HTTP 429 3（THCJD・THXE・THCA）で、CBDV は記録された HTTP 429 の後に NO_DATA。THCV・CRDH は 12ヶ月が 53 週中 1 週だけ非ゼロ（[methodology.md](methodology.md) §2.1.3）。CRDH の旧 summary（`records_crdh_12m.json`）は証跡として残るが、その記録値（`avg_12m` 1.9 等）は raw から再現できないので引用しない。
- **週次系列は全面で比較できるわけではない**: 既存の 5年は 3 窓（10 化合物が 2021-10-10 〜 2026-10-11（CBX を含む）、4 化合物が 2021-10-17 〜 2026-10-18、THCNM が 2021-10-31 〜 2026-11-01）、12ヶ月は 4 窓（8 化合物が 2025-09-28 〜 2026-09-27、4 化合物が 2025-10-19 〜 2026-10-18、CBX が 2025-10-12 〜 2026-10-11、THCNM が 2025-11-02 〜 2026-11-01）に分かれる。追加 15 語は 12ヶ月 `2025-11-09_2026-11-15`（観測 2025-11-09 〜 2026-11-08、53 週）と 5年 `2021-11-07_2026-11-15`（観測 2021-11-07 〜 2026-11-08、262 週）で、`today 12-m` / `today 5-y` を reference time で nominal に解決した**近似窓**である。各 run は自分のピーク=100 に正規化されるので、単独系列の値を化合物間・run 間で比べない。化合物間の比較は共通スケール（§2.1.4・§2.1.6）でのみ行う。
- **「データなし」**: 取得はしたが Google Trends が閾値未満で系列を返さなかった。**欠測であって 0 観測ではない**。
- **「失敗（429）」**: HTTP 429 で取得に失敗し、adopted run が無い。試行は quarantine に残る。**0 観測でも欠測でもない**。
- **「未採用（NO_VIDEOS）」**: YouTube actor は SUCCEEDED だが `NO_VIDEOS` で動画行が 0。絶対窓を導けないため採用しない。**世界全体の 0 ではない**。
- **「—」**: そのソースのクエリを設計していない（収集対象外）。X 列は 7 化合物だけを対象に設計しており、それ以外は「—」である。X の 6 化合物は [`datasets/cannabinoid-social-trends/`](../cbx-social-trends/) が規制前後比較として収集している。
- **13 語の分類欄**: taxonomy の管理カテゴリ `compound_identity_unverified`（同一性未確認の登録状態）であり、経路・化学クラス・天然存在の主張ではない。
- **THCNM の状態**: 15 番目の既存化合物。**Google Trends は 12ヶ月・5年とも adopted**（`20261104T115425Z-google-trends-thcnm-12m` / `20261104T115431Z-google-trends-thcnm-5y`）、**YouTube も required primary の 2 本（`20261104T120627Z-youtube-…` = `THCNM リキッド`、`20261104T120805Z-youtube-…` = `THA リキッド`）が adopted**で化合物被覆は 2/2 完了。2 run は別観測で、件数は合算しない。収集した系列は登録文字列（`THCNM` / `THA リキッド`）に一致する検索需要であり、物質そのものの観測ではない。化学的同一性は供給元・市場の記載によるもので**未確認**（`THA` は別名・商業名。[`ISS-20261104-TAX-028`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thcnm-identity-unconfirmed.md)）。
- **YouTube raw（一次被覆）**: primary は liquid-only `<compound> リキッド` の **31 run / 29 化合物**（既存 17 run / 15 化合物 + 追加 14 run / 14 化合物）。required primary query は **31 本**で、**adopted run があるのは 30 本**。**欠けるのは `thca-liquid-ja`（`THCA リキッド`）1 本だけ**で、actor は SUCCEEDED だが `NO_VIDEOS` のため未採用。したがって化合物被覆は **29/30**・クエリ被覆は **30/31** である。CBE 331（3/354 actor requests 失敗）と CBL 269（5/296 失敗）は **partial** であり、完全な census ではない。primary 外の裸の化合物語 `HHC` 1 run は raw / catalog に**保持**するが、liquid-only primary の外であり、どの化合物の一次被覆も完成させない。catalog / declaration 上は合計 32 run（primary 31 + retained 1）。run ごとに検索語と観測窓が異なるので、run をまたいで件数を合算しない（[methodology.md](methodology.md) §2.3）。
- **CBX の状態**: Google Trends は 2026-11-04 に所有をこの study へ移管した。単独系列は 5年 `20261015T042857Z-google-trends-boundary-5y`（2021-10-10 〜 2026-10-11、262 週）と 12ヶ月 `20261015T042853Z-google-trends-boundary-12m`（2025-10-12 〜 2026-10-11、53 週）、加えて 1m・3m の boundary probe と 2026-10-01 の legacy 4 run。**run id と payload は移管前と同一**で、観測のやり直しではない（[methodology.md](methodology.md) §2.1.6）。YouTube 列の CBX はこの study の own raw。CBX リキッドは製品語であり、CBX 化合物語の系列とは別観測である。
- **配布物との差**: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/) の YouTube 行は COL-033 の 6 run だけを使う。この study の YouTube raw（31 primary + 1 retained）は配布 slice の外にある（[methodology.md](methodology.md) §5.1）。THCNM はいずれの配布 slice にも入らない（COL-033 に YouTube run は無く、Google Trends 系列は配布物の公開化合物集合外）。追加 15 語も配布 slice の外である。
- Google Trends の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。`gt-summary` の化合物集合は既存の公開ページ 14 化合物で、**追加 15 語は含まれない**。追加 15 語の数値は各 run の `records_*.json` と [`metadata/data-catalog.json`](metadata/data-catalog.json) を正本とする。単独系列（12ヶ月・5年）のほかに、比較セット／共通スケール（12ヶ月 `common-scale-*`・5年 `5y-common-scale-set*`・CBX bridge の `comparison_cbx-cbd-thc.json`）・表記事前調査・「リキッド」系クエリの run がある。

## データソース

| ソース | ツール | 状態 |
|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | ✅ 登録 30 語のうち **5年 26/30・12ヶ月 20/30**。既存 15 語は 5年 15/15・12ヶ月 14/15（THC-O は NO_DATA）。追加 15 語は **17/30 adopted**（5年 11/15・12ヶ月 6/15）で、採用外 13 本は NO_DATA / HTTP 429 として quarantine。CBX を含む共通スケール bridge は §2.1.6 |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ✅ 7 化合物（CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run。条件は未記録）。**geo filter なし**。CBC・CBDV と 13 語のクエリは設計していない |
| YouTube | Apify `h7sDV53CddomktSi5` (`streamers/youtube-scraper`) | ✅ primary は liquid-only `<compound> リキッド` の **31 run / 29 化合物**（required query 30/31）。**`compound_thca` だけが `NO_VIDEOS` で未採用**。CBE 331（3/354 失敗）・CBL 269（5/296 失敗）は partial。**date filter なし・geo filter なし**、`maxResults` 500、Shorts/streams 0。裸の化合物語 `HHC` 1 run は保持するが primary 外。raw は非追跡・公開対象外（§2.3） |

> **関連データセットとの役割分担**: 本データセットはカンナビノイドのトレンド分析用 raw を収蔵する。
> [`datasets/youtube-consistency/`](../youtube-consistency/) は YouTube 検索結果の一貫性・再現性検証を目的とする別研究である。

## 収集結果

Google Trends の系列・窓・欠測は [methodology.md](methodology.md) §2.1.2・§2.1.3 が正本。既存 15 化合物のうち公開ページを持つ 14 化合物の 5年系列の機械可読レポートは [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json) だが、**追加 15 語はこの化合物集合外**なので各 run の `records_*.json` と [`metadata/data-catalog.json`](metadata/data-catalog.json) を正本とする。
単独系列の平均と比較セット（`common-scale-*` の**共通スケール**値）は別物なので混ぜない。
単独系列の平均は化合物間でも比べない（正規化が語ごとに違う）。比較は共通スケールでのみ行う。
**5年の共通スケールは、アンカー CBD/THC を含む legacy setA〜D（旧窓）と、現行窓の setA〜D / THCNM anchored run が catalog にある**（[methodology.md](methodology.md) §2.1.4・§2.1.6）。
12ヶ月の共通スケールは `common-scale-*` の各 run。**追加 15 語には共通スケール run が無い**ので、単独系列の値を既存化合物と比較しない。
**CBX は 2026-11-04 に、CBX + CBD + THC を 1 リクエストで測る bridge を 12ヶ月・5年とも収集した**（[methodology.md](methodology.md) §2.1.6）。bridge の値は同一 run 内の共通スケールであり、単独系列の平均から作った値ではない。

Google Trends は run ごとの相対指数（0-100）、YouTube は検索結果として返された動画件数で、**単位が異なる。両者を比較・合算しない**。追加 15 語の Google Trends 窓は `today 12-m` / `today 5-y` を reference time で nominal に解決した**近似**であり、各系列は自分のピーク=100 に正規化されている。

### 収集したキーワード

収集語は canonical の 3 種類（化合物語・製品語・アンカー語）と、その登録済み表記ゆれ（variant）からなる。各語は下表のどこかに 1 回だけ現れる。

| 種別 | 語 |
|---|---|
| 化合物語（登録 30） | CBX, CBD, THC, CBG, HHC, THCV, THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH, THCNM, CBC, CBDV, THCB, THCP, THCJD, THCPO, CBE, HHCPO, CBND, CBL, CBGa, CBP, 10-OH-HHC, THXE, THCA。既存 15 語は Google Trends・YouTube とも adopted run を持ち、追加 15 語の採用状況は「登録済みキーワードと収集状態」を参照 |
| 製品語 — リキッド（登録 30 化合物 / required primary 31 本） | 化合物語のうち CBX と THCNM を除く 13 語に「リキッド」を付けた形（`CBD リキッド` 〜 `THCV リキッド`、`THC-O リキッド` を含む）と、THCNM の 2 表記（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`）。Google Trends で照会したのは既存 13 語。YouTube で **adopted run があるのは 30 本（29 化合物）**、**adopted run が無いのは `thca-liquid-ja` 1 本だけ**（`NO_VIDEOS`） |
| 製品語 — オイル（2） | CBD オイル, THC オイル |
| 製品語・比較アンカー | CBX リキッド（CBX 化合物語とは別観測。Google Trends の比較セットにも登場し、YouTube では primary の 1 run） |
| 表記ゆれ（variant） | `THCO`（`thc-o-general-ja` の variant）、`THCO リキッド`（`thc-o-liquid-ja` の variant）。canonical の別表記であり、化合物語・製品語の数を増やさない。`THCO` は tetrahydrocannabiorcol（Δ8-/Δ9-THCO）にも使われる別物質の表記であり、単一物質の名称ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)） |

| プラットフォーム | 収集時点 | 化合物語 | 製品語 | 測定モード |
|---|---|---|---|---|
| Google Trends | 既存 15 語: 2026-10-02 〜 11-04 / 追加 15 語: 2026-11-10 | 既存 15 語 + 追加 15 語（合計 20 語が 12ヶ月 adopted） | 既存リキッド 13 語（8 語が系列、5 語は NO_DATA） | 12ヶ月・単独系列 |
| Google Trends | 既存 15 語: 2026-10-02 〜 11-04 / 追加 15 語: 2026-11-10 | 既存 15 語 + 追加 15 語（合計 26 語が 5年 adopted） | 既存リキッド 13 語中 12 語が系列（main5 の 5 語 + 別窓の新規 7 語）。THC-O は系列なし | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（12ヶ月） |
| Google Trends | 2026-10-23, 11-04 | 既存 13 語（アンカー CBD/THC を含む 4 セット）+ THCNM の anchored run | なし | 5年の共通スケール（`compare_terms`） |
| Google Trends | 2026-11-04 | CBX + アンカー CBD/THC の 3 語 | なし | CBX bridge の共通スケール（12ヶ月・5年、`compare_terms`。§2.1.6） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`）。CBD は追加 3 run（条件未記録） |
| YouTube | 既存 15 化合物: 2026-10-10 〜 11-04 / 追加 14 クエリ: 2026-11-10 | 裸の `HHC` 1 run（保持・primary 外） | リキッド **29 化合物 / 31 primary run**（required query 30/31。`thca-liquid-ja` のみ `NO_VIDEOS` で未採用） | 1 run 1 クエリ。**date filter なし・geo filter なし**、`maxResults` 500、Shorts/streams 0。日本語「リキッド」語による近似的な市場限定 |

- **登録集合は 30 語**。既存 15 語は Google Trends・YouTube とも adopted run を持ち、追加 15 語も Google Trends / YouTube の少なくとも一方で adopted run を持つ。Google Trends の 12ヶ月で系列が取れていないのは、既存では THC-O（NO_DATA）、追加では CBDV・THCB・THCPO・HHCPO・CBGa・10-OH-HHC（NO_DATA）と THCJD・THXE・THCA（HTTP 429）。
- **表記ゆれ（2026-11-04）**: THC-O の `THCO` と `THCO リキッド` を `query-variants.json` に登録し、canonical の `query_id` のまま別 run として 12ヶ月・5年を収集した（Google Trends、geo JP）。canonical の `THC-O`（12ヶ月 no data・5年系列）と `THC-O リキッド`（no data）を置換・統合しない。run 一覧は [methodology.md](methodology.md) §2.1.5。
  - **`THCO` 表記で別系列がある**: 12ヶ月 53 週・非ゼロ 3（`20261104T135330Z-google-trends-thc-o-general-thco-12m`）、5年 262 週・非ゼロ 90（`20261104T135339Z-google-trends-thc-o-general-thco-5y`）。`THCO リキッド`は12ヶ月53週・非ゼロ1、5年262週・非ゼロ23。
  - canonicalの「12ヶ月 no data」は維持する。variantで系列が返ることはcanonicalのno dataを否定・置換しない。canonicalとvariantの値は合算しない。
  - `THCO`はPubMed/PubChem等で`THC-O-acetate`の略記として使われる一方、Δ8-THCO/Δ9-THCO（tetrahydrocannabiorcol）という別物質にも使われる。variantは検索文字列の対応であり、単一CAS・構造の同定ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)）。
- **THCNM（`thcnm-general-ja`）は 2026-11-04 に Google Trends の 12ヶ月・5年を収集した**（化合物語 14 語の最後）。同じ日に YouTube の 2 表記（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）も各 1 run で採用した。THA は同じ化合物の別名・商業名であり、別の収集語・別物質ではない（2 run は別観測で、件数を合算しない）。
- **製品語のリキッド**は Google Trends と YouTube で使う。YouTube の primary はリキッド **31 run / 29 化合物**（既存 17 run / 15 化合物 + 追加 14 run / 14 化合物）。required primary query は 31 本で、**30 本に adopted run がある**。`thca-liquid-ja`（`THCA リキッド`）だけが `NO_VIDEOS` で未採用。裸の `HHC` 1 run は保持するが primary 外で、対の必須 run でもない。
  Google Trends の比較セットは単独系列とは別の共通スケール値であり、混ぜない。
- **5年のリキッドは 13 語中 12 語が系列**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5 語 + 新規 8 run のうち 7 語）。
  新規 8 run は main5 と窓が異なる別観測であり（main5 は 2021-10-10 〜 2026-10-11、新規は 2021-10-17 〜 2026-10-18）、単独系列の値をまたいで比較しない。
  THC-O リキッドは 5年でも系列なし（`NO_DATA`）。12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。

### 登録済みキーワードと収集状態（追加 15 語）

CBC・CBDV は taxonomy に既存の canonical concept があったため **ID・分類を新設せずに再利用**し、query だけを登録した。残り 13 語は **owner 指示**（「ほかのHHBDなどと同じく対応、いちいち保留しなくていい」）で、**管理上の登録状態カテゴリ `compound_identity_unverified`** に登録した。下表の adopted run は、登録された検索文字列に一致する Google Trends 相対指数 / YouTube 検索結果であり、**物質の同定・存在・化学クラスを主張しない**。

| 化合物 | `compound_id` | taxonomy | query（`intent_id`） | 状態 |
|---|---|---|---|---|
| CBC | `compound_cbc` | 既存（`compound_minor`、Wikidata Q422441） | `CBC`（`compound_general`）= `cbc-general-ja`、`CBC リキッド`（`product_liquid`）= `cbc-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 358 ✅ |
| CBDV | `compound_cbdv` | 既存（`compound_minor`、Wikidata Q422426） | `CBDV`（`compound_general`）= `cbdv-general-ja`、`CBDV リキッド`（`product_liquid`）= `cbdv-liquid-ja` | GT 12m NO_DATA（記録された HTTP 429 の後）/ 5y 262 週 ✅、YouTube 112 ✅ |
| THCB | `compound_thcb` | 新規（`compound_identity_unverified`） | `THCB`（`compound_general`）= `thcb-general-ja`、`THCB リキッド`（`product_liquid`）= `thcb-liquid-ja` | GT 12m NO_DATA / 5y 262 週 ✅、YouTube 209 ✅ |
| THCP | `compound_thcp` | 新規（`compound_identity_unverified`） | `THCP`（`compound_general`）= `thcp-general-ja`、`THCP リキッド`（`product_liquid`）= `thcp-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 419 ✅ |
| THCJD | `compound_thcjd` | 新規（`compound_identity_unverified`） | `THCJD`（`compound_general`）= `thcjd-general-ja`、`THCJD リキッド`（`product_liquid`）= `thcjd-liquid-ja` | GT 12m 429 / 5y 262 週 ✅、YouTube 55 ✅ |
| THCPO | `compound_thcpo` | 新規（`compound_identity_unverified`） | `THCPO`（`compound_general`）= `thcpo-general-ja`、`THCPO リキッド`（`product_liquid`）= `thcpo-liquid-ja` | GT 12m NO_DATA / 5y 262 週 ✅、YouTube 33 ✅ |
| CBE | `compound_cbe` | 新規（`compound_identity_unverified`） | `CBE`（`compound_general`）= `cbe-general-ja`、`CBE リキッド`（`product_liquid`）= `cbe-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 331 ✅（partial: 3/354 失敗） |
| HHCPO | `compound_hhcpo` | 新規（`compound_identity_unverified`） | `HHCPO`（`compound_general`）= `hhcpo-general-ja`、`HHCPO リキッド`（`product_liquid`）= `hhcpo-liquid-ja` | GT 12m NO_DATA / 5y 262 週 ✅、YouTube 38 ✅ |
| CBND | `compound_cbnd` | 新規（`compound_identity_unverified`） | `CBND`（`compound_general`）= `cbnd-general-ja`、`CBND リキッド`（`product_liquid`）= `cbnd-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 9 ✅ |
| CBL | `compound_cbl` | 新規（`compound_identity_unverified`） | `CBL`（`compound_general`）= `cbl-general-ja`、`CBL リキッド`（`product_liquid`）= `cbl-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 269 ✅（partial: 5/296 失敗） |
| CBGa | `compound_cbga` | 新規（`compound_identity_unverified`） | `CBGa`（`compound_general`）= `cbga-general-ja`、`CBGa リキッド`（`product_liquid`）= `cbga-liquid-ja` | GT 12m NO_DATA / 5y NO_DATA、YouTube 89 ✅ |
| CBP | `compound_cbp` | 新規（`compound_identity_unverified`） | `CBP`（`compound_general`）= `cbp-general-ja`、`CBP リキッド`（`product_liquid`）= `cbp-liquid-ja` | GT 12m 53 週 ✅ / 5y 262 週 ✅、YouTube 384 ✅ |
| 10-OH-HHC | `compound_10_oh_hhc` | 新規（`compound_identity_unverified`） | `10-OH-HHC`（`compound_general`）= `10-oh-hhc-general-ja`、`10-OH-HHC リキッド`（`product_liquid`）= `10-oh-hhc-liquid-ja` | GT 12m NO_DATA / 5y 429、YouTube 172 ✅ |
| THXE | `compound_thxe` | 新規（`compound_identity_unverified`） | `THXE`（`compound_general`）= `thxe-general-ja`、`THXE リキッド`（`product_liquid`）= `thxe-liquid-ja` | GT 12m 429 / 5y 429、YouTube 326 ✅ |
| THCA | `compound_thca` | 新規（`compound_identity_unverified`） | `THCA`（`compound_general`）= `thca-general-ja`、`THCA リキッド`（`product_liquid`）= `thca-liquid-ja` | GT 12m 429 / 5y 429、YouTube 未採用（`NO_VIDEOS`） |

- **NO_DATA / HTTP 429 / `NO_VIDEOS` は 0 観測でも欠測でもない**。Google Trends の採用外試行（13 語バッチの 12 本と CBDV 12ヶ月）は quarantine に残し、catalog に入れない。YouTube の `NO_VIDEOS` は「世界全体で 0 本」ではなく、絶対窓を導けないため未採用である。
- 登録は**検索文字列の固定**であり、物質の同定ではない。`CBGa` の小文字 `a` と `10-OH-HHC` のハイフンを含め、**owner の表記をそのまま** canonical text に使う。外部識別子（CAS / ChEBI / Wikidata / PubChem）は検証していないので記載しない。
- `CBC` はカナダ放送協会など化合物以外の略号と衝突する。登録文字列は物質の同定ではなく、**その文字列に一致するコンテンツ**を測る。
- 13 語は `compound_rare` ではなく管理カテゴリに置いた。`compound_rare` は引き続き空であり、`compound_cbdp` も登録していない。`THCP` については 2026-10-15 の [`ISS-20261015-TAX-027`](../../docs/issues/active/50-taxonomy-standards/20261015_p2_compound-rare-membership.md) の非登録判断を 2026-11-11 の owner 指示が置換した（[`ISS-20261111-TAX-040`](../../docs/issues/active/50-taxonomy-standards/20261111_p1_compound-registration-state-batch.md)）。
- 依頼文は「17 物質」とするが**列挙は 15 語**である。列挙された 15 語を登録し、**不足する 2 語は推測で補わない**（未決事項として issue に記録）。

### YouTube の収集と追跡

クエリ設計は [methodology.md](methodology.md) §2.3 と [`metadata/query-design.json`](metadata/query-design.json) が正本。**query-design は必須 primary query と被覆ルールを定め、現在の adopted 状態は `make audit-youtube-coverage` と catalog が報告する。** **primary は liquid-only**: `<compound> リキッド`（`product_liquid`）**31 run / 29 化合物**。required primary query は **31 本**で、**30 本に adopted run がある**（既存 16 本（15 化合物、CBD のみ 2 run、THCNM は 2 本）+ 追加 14 本）。**`thca-liquid-ja`（`THCA リキッド`）1 本だけが `NO_VIDEOS` で未採用**。被覆は**クエリ単位と化合物単位の両方**で報告し、化合物は自身の required primary query が全部揃って初めて完了する。`make audit-youtube-coverage` は **primary runs=31、compounds=29/30、queries=30/31、partial_compounds=0、missing_compounds=1（`compound_thca`）、retained_out_of_scope=1、violations=0** を報告し、THCNM について `primary coverage 2/2` を出す。ここでの `partial_compounds=0` は**クエリ被覆**の状態であり、CBE・CBL の actor request 失敗による payload の partial とは別の軸である。裸の化合物語 `HHC` 1 run は raw / catalog に保持するが **primary coverage 外**であり、HHC の liquid run と対にする必須 run ではない。

いずれも `data/raw/youtube/<run-id>/` に置き、raw は非追跡かつ公開対象外（公開承認なし）。raw は machine-local のため、clone によっては下表のリンク先が存在しない（catalog / declaration は committed、payload は手元の証跡）。**追加 14 run（CBC・CBDV + 追加 12 クエリ）の raw は一次 checkout にあり、歴史的 18 run の payload は Git 非追跡のため clone には含まれない**。payload の有無は被覆判定に影響しない。

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
| primary | `CBC リキッド` | `all` | 358 | 2007-07-19 〜 2026-11-11 | [`20261110T170316Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T170316Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBDV リキッド` | `all` | 112 | 2016-02-14 〜 2026-11-05 | [`20261110T171742Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T171742Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCB リキッド` | `all` | 209 | 2006-10-12 〜 2026-10-13 | [`20261110T191309Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T191309Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCP リキッド` | `all` | 419 | 2021-02-13 〜 2026-10-29 | [`20261110T191712Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T191712Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCJD リキッド` | `all` | 55 | 2018-04-24 〜 2026-03-12 | [`20261110T192423Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192423Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCPO リキッド` | `all` | 33 | 2017-05-09 〜 2026-09-15 | [`20261110T192549Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192549Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBE リキッド` | `all` | 331（partial: 3/354 失敗） | 2009-01-05 〜 2026-11-11 | [`20261110T192628Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192628Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHCPO リキッド` | `all` | 38 | 2017-04-28 〜 2026-09-20 | [`20261110T193648Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193648Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBND リキッド` | `all` | 9 | 2008-03-03 〜 2025-11-19 | [`20261110T193743Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193743Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBL リキッド` | `all` | 269（partial: 5/296 失敗） | 2009-06-16 〜 2026-11-09 | [`20261110T193806Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193806Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBGa リキッド` | `all` | 89 | 2013-03-04 〜 2026-10-26 | [`20261110T194826Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T194826Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBP リキッド` | `all` | 384 | 2010-06-03 〜 2026-10-18 | [`20261110T195055Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T195055Z-youtube-cannabinoid-raw-collection/) |
| primary | `10-OH-HHC リキッド` | `all` | 172 | 2006-02-14 〜 2026-10-06 | [`20261110T200043Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T200043Z-youtube-cannabinoid-raw-collection/) |
| primary | `THXE リキッド` | `all` | 326 | 2021-09-04 〜 2026-10-18 | [`20261110T200518Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T200518Z-youtube-cannabinoid-raw-collection/) |
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
- **2026-11-10 の追加 14 run** はすべて 1 run 1 クエリで、`maxResults` 500・`maxResultsShorts` 0・`maxResultStreams` 0、`dateFilter` なし、geo filter なし、`CBC リキッド`〜`THXE リキッド` の登録済み liquid クエリを送った。**CBE は 331 件（3/354 actor requests 失敗）、CBL は 269 件（5/296 失敗）で partial** であり、完全な census ではない。**THCA は actor status が SUCCEEDED でも `NO_VIDEOS` で動画行が 0**、絶対窓を no-date/no-video payload から導けないため現行 declaration contract では採用しない（`thca-liquid-ja` は adopted run 0）。これは世界全体の 0 でも、採用済み primary query でもない。
- 採用宣言: HHBD は [`20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json)、リキッド 5 run は [`20261015-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261015-youtube-liquid-batch-cannabinoid-raw-collection.json)、HHC 2 run は [`20261101-youtube-hhc-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-cannabinoid-raw-collection.json) / [`20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json)、2026-11-01 の HHCH・THCH 2 run は [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)、再実行の CBG・CRDP・THC・THC-O・THCV 5 run は [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)、CBX は [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json)、THCNM 2 run は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)、追加 14 run は [`20261110-youtube-cbc-cbdv-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261110-youtube-cbc-cbdv-cannabinoid-raw-collection.json) と `20261110-youtube-<query>-cannabinoid-raw-collection.json` 12 本（いずれも `staging-declaration-v1`、L1 を経て catalog）。
- HHC 2 run の request 語彙・actor build・実行状態の訂正は [`20261101-youtube-hhc-request-parameters.json`](../../metadata/provenance/corrections/20261101-youtube-hhc-request-parameters.json) に記録する。元の宣言は handover hash を保つため書き換えず、訂正版 declaration を併置する。
- `maxResults` が現行 Actor の正規名。旧宣言の `max_videos` は歴史的記録としてのみ読み、新規入力に使わない。
- **配布制限**: この study の YouTube raw は [`cannabinoid-platform-trends`](../cannabinoid-platform-trends/) の配布 slice（COL-033 の 6 run）には含まれない。HHC の raw はこの study に採用済みだが、配布物の `not_collected` は「配布 slice に無い」という意味であり、この study で未収集という意味ではない。
- 月別の検索結果件数は [`data/processed/youtube_monthly_counts.csv`](data/processed/youtube_monthly_counts.csv)。この中間集計は HHBD リキッド run に固定され、当該 CSV の SHA-256 に限って公開承認済み（[審査記録](../../metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json)）。他の 31 run の集計はまだ作っていない。
- **raw の公開範囲**: 採用した YouTube raw（catalog / declaration 上 32 run）は Git 非追跡・machine-local の per-video データで、**公開承認されていない**。公開済みなのは上記 HHBD 月別集計だけであり、他の化合物の raw / 集計は未公開。
- 外部公開・リリースは実施していない。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE（既存 15 化合物の Google Trends） | 2026-11-04（既存 15 化合物は 5年 15/15・12ヶ月 14/15。登録 30 語への拡張後は 5年 26/30・12ヶ月 20/30） |
| COMPLETED | — |

> **YouTube の liquid-only primary は、登録 30 化合物のうち 29 化合物・required query 30/31 を被覆。** primary は 31 run（CBD のみ 2 run、THCNM のみ 2 クエリで 2 run）で、欠けるのは `thca-liquid-ja` 1 本だけ（`NO_VIDEOS` で未採用）。CBE 331（3/354 失敗）と CBL 269（5/296 失敗）は partial であり、完全な census ではない。裸の `HHC` run は保持された primary 外証跡で、primary の内訳には数えない。`make audit-youtube-coverage` は **primary runs=31、compounds=29/30、queries=30/31、partial_compounds=0、missing_compounds=1（`compound_thca`）、retained_out_of_scope=1、violations=0** を報告する。`COLLECTION_COMPLETE` は既存 15 化合物の Google Trends 収集が揃った状態を指し、**登録 30 語全体の完了ではない**（30 語では 5年 26/30・12ヶ月 20/30）。X は CBD・THC・CBG・HHC・THCV・THC-O・THCH の 7 化合物に限られ、全体の COMPLETED は未宣言。

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
  [`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)（CBC・CBDV の登録と収集状態）、
  [`ISS-20261111-TAX-040`](../../docs/issues/active/50-taxonomy-standards/20261111_p1_compound-registration-state-batch.md)（2026-11-11 の 13 語の登録、管理カテゴリ、THCP の非登録判断の置換）
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/)（Google Search Console raw の正本。CBX の Google Trends raw は 2026-11-04 に本 study へ移管済み）, [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
