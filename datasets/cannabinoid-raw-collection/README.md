# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`（2026-10-23 に改名）。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

既存の CBX 周辺の収集（CBX 本体は [`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当）から始まり、現在は **CBX を除く 13 化合物**の市場トレンド・SNS 言及・動画コンテンツの**原記録を集める研究**。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本国内において、カンナビノイド各化合物の検索需要・SNS 言及・動画コンテンツはどう推移しているか？（当初は CBD / THC / CBG / HHC / THCV / THC-O / THCH の 7 化合物で開始し、5年・12ヶ月系列の追加収集で 13 化合物に拡張）

## 対象化合物

合計 **13 化合物**。当初は 12ヶ月収集の 7 化合物だったが、5年系列と 12ヶ月系列の追加収集で広がった。収集の詳細は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3。

| 化合物 | 分類 | Google Trends 12ヶ月 | Google Trends 5年 | X | YouTube（公開分）|
|--------|------|:----:|:----:|:-:|:-:|
| CBD | major | ✅ | ✅ | ✅ | ✅ |
| THC | major | ✅ | ✅ | ✅ | ✅ |
| CBG | minor | ✅ | ✅ | ✅ | ✅ |
| HHC | semisynthetic | ✅ | ✅ | ✅ | ✅ |
| THCV | minor | ✅ | ✅ | ✅ | ✅ |
| THC-O | semisynthetic | データなし | ✅ | ✅ | raw のみ |
| THCH | minor | ✅ | ✅ | ✅ | raw のみ |
| CBN | minor | ✅ | ✅ | — | raw のみ |
| CRDH | synthetic | サマリーのみ | ✅ | — | raw のみ |
| CRDP | synthetic | ✅ | ✅ | — | raw のみ |
| H4CBH | semisynthetic | ✅ | ✅ | — | raw のみ |
| HHBD | semisynthetic | ✅ | ✅ | — | raw のみ |
| HHCH | synthetic | ✅ | ✅ | — | raw のみ |

読み方:

- **5年系列**: 表の 13 化合物すべてが週次 raw を持つ。summary-only だった旧 `…-5y-baseline` run は raw に残るが、
  現在どの化合物の引用元でもない（[methodology.md](methodology.md) §2.1.1・§2.1.2）。
- **12ヶ月系列**: 11 化合物が週次 raw を持ち、CRDH は**サマリーのみ**（週次系列なし）、
  THC-O は Google Trends が系列を返さない。THCV は 5年には系列があるが、12ヶ月は 53 週中 1 週だけ非ゼロ
  （[methodology.md](methodology.md) §2.1.3）。
- **「サマリーのみ」**: 週次系列を収蔵していない run の記録値。raw からの独立検証はできない。
- **「データなし」**: 取得はしたが Google Trends が閾値未満で系列を返さなかった。**欠測であって 0 観測ではない**。
- **「—」**: そのソースでは収集していない（X の 6 化合物は [`datasets/cannabinoid-social-trends/`](../cannabinoid-social-trends/) が規制前後比較として収集している）。
- **「YouTube（公開分）」**: 追跡している集計（[`data/processed/youtube_videos.csv`](data/processed/youtube_videos.csv)、182 動画）に含まれるか。raw だけ有ってまだ公開集計に入れていない run は `raw のみ`（provenance のレビュー待ち）。
- **CBX はこの研究の対象外**（[`datasets/cbx-search-trends/`](../cbx-search-trends/) が担当）。`docs/audits/gt-summary.json` が 14 化合物なのはこの 1 件を含むため。
- Google Trends の正本は `data/raw/google_trends/` と [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)。5年以外に 12ヶ月・比較セット・共通スケール比較（`common-scale-*`）・表記事前調査・「リキッド」系クエリの run がある。

## データソース

| ソース | ツール | コスト | 状態 |
|--------|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | 無料 | ✅ 5年 13/13 化合物・12ヶ月 11/13（欠測は §2.1.3） |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ~$0.80 | ✅ 7 化合物 |
| YouTube | Apify `gJvjeCYNraSfhIaNd` | ~$0.09 | ✅ 7 検索語 |

> **関連データセットとの役割分担**: 本データセットは**トレンド分析**（複数プラットフォームの出現・時系列分布）が目的。
> YouTube 検索結果の**一貫性・再現性検証**は [`datasets/youtube-consistency/`](../youtube-consistency/) が担当しており、
> そちらは別の Actor（`h7sDV53CddomktSi5` / streamers/youtube-scraper）を使う。両者は目的・ Actor・格納形式（本件は raw ファイル、同件は SQLite）が異なるため重複ではなく分業である。

## 収集結果

Google Trends の系列・窓・欠測は [methodology.md](methodology.md) §2.1.2・§2.1.3 と
[`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json)（5年）が正本。
単独系列の平均と比較セット（`common-scale-*` の**共通スケール**値）は別物なので混ぜない。
共通スケールは **12ヶ月にのみ**存在し、**5年の共通スケール計測は無い**（5年は化合物間比較ができない = `ISS-20261023-GT-009`）。

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
| Google Trends | 2026-10-02, 10-08, 10-14, 10-15, 10-23 | 13 語すべて | リキッド 5 語（CBD, CBG, CBN, HHC, THC）。残り 8 語は未収集 | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（**12ヶ月のみ**。5年は無い） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`） |
| YouTube | 2026-10-02（公開集計に入る 7 run） | CBD, THC, CBG, HHC, THCV（5 語） | オイル 2 語 | 単一クエリ（actor の入力は `search_term` + `max_videos` のみ） |

- **化合物語は 13 語で閉じている**。このうち 12ヶ月で系列が取れていないのは THC-O だけ（no data）。
- **製品語のリキッドは Google Trends のみ**。12ヶ月は比較セットで測っているため、単独系列（上の 2 行）とは
  別の共通スケール値であり、混ぜない。
- **5年のリキッドは 5 語だけ**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5`）。
  12ヶ月で照会済みの残り 8 語（THCV / THC-O / THCH / CRDH / CRDP / H4CBH / HHBD / HHCH リキッド）は**未収集**で、
  12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）ため、照会しない限り不明（`ISS-20261023-GT-008`）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。**YouTube は化合物語 5 語 + オイル 2 語**で、リキッドは使っていない。
- キーワード別の件数は X が [`data/processed/collection-summary.md`](data/processed/collection-summary.md)（raw は Git 管理外の
  ローカル証跡なので記録値）、YouTube が下の `youtube_runs.csv`（run ごとの `video_rows`）。

### YouTube の収集と追跡

**追跡される形（集計のみ）**: raw は Git 管理外（`**/data/raw/*`、例外は `google_trends` のみ）で、**ローカル証跡のみ**。代わりに次の 2 表を追跡する（生成: `python -m processing.cli youtube-export`、実装 [`src/processing/youtube_export.py`](../../src/processing/youtube_export.py)）。

| ファイル | 行 | 内容 |
|---|---|---|
| `data/processed/youtube_videos.csv` | 182 | 1 行 = 1 動画（`run_id` / `video_id` / `channel_title` / `title`）。**説明文は出力しない** |
| `data/processed/youtube_runs.csv` | 7 | 1 行 = 1 公開 run（検索語 / 収集時刻 / 動画行数 / error payload 数） |

- **182 件**は `youtube_videos.csv` の行数と一致する（run ごとの内訳は `youtube_runs.csv` の `video_rows`: 22+25+34+28+23+23+27）。
- **説明文（`description`）は公開しない**: チャンネル運営者の連絡先メールが埋め込まれている事例があったため、追跡対象は ID・タイトル・チャンネル名だけにした（2026-10-23 の owner 判断）。
- **公開日は含まれない**: この収集ペイロードに投稿日が無いので、空列を作らずに落とした。
- **公開しない run は 2 表のどちらにも載せない**（2026-10-23）。除外した run には、本リポジトリが方針上使わない収集手段に由来するものや不完全系列が含まれるため、データ成果物の勘定に入れない。除外の判定と理由はコード（`src/processing/youtube_export.py` の `EXCLUSION_REASONS`）に閉じる。
- 生成は raw を要求するので、clone では再導出できない（`processing.cli audit-processed` は `not_reproducible_from_repository` と記録する。ルールはコードとテストで固定済み）。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE | 2026-10-23（5年 13/13・12ヶ月 11/13 化合物） |
| COMPLETED | — |

## 関連

- 方法と制約: [methodology.md](methodology.md)（5年 §2.1.2 / 12ヶ月 §2.1.3）
- 収集計画書: [`metadata/plans/`](metadata/plans/)、窓: [`metadata/windows/`](../../metadata/windows/)
- 既知の欠測と未決事項: [`ISS-20261023-GT-006`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-12m-recollection-findings.md)、
  [`ISS-20261023-GT-005`](../../docs/issues/active/40-provenance-storage-reproducibility/20261023_p2_gt-5y-recollection-residuals.md)
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 収集サマリー: `data/processed/collection-summary.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/), [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`
