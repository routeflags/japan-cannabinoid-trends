# Cannabinoid Raw Collection

**表示名:** カンナビノイド 原データ収集（Google Trends / X / YouTube の生記録）
**Study ID:** `cannabinoid-raw-collection`（ディレクトリ名と一致）
**旧 `study_id`:** `cannabinoid-multi-trends`。raw の `run_metadata.json` は**収集時の ID のまま**（raw は不変）。旧 ID は [`study-registry.json`](../../metadata/studies/study-registry.json) の `previous_study_ids` に宣言され、research catalog が現在の ID に解決する。古い run id の末尾も旧名のまま。
**Created:** 2026-10-02
**Status:** ACTIVE
**Scope:** 主要カンナビノイド化合物の Google Trends / X / YouTube 原記録の収集

---

## 概要

所有はソースで分かれる。**Google Trends は登録 63 トピックのうち 5年 29/63・12ヶ月 21/63 で adopted 系列を持つ**（内訳は「収集被覆」）。**YouTube は liquid-only primary の 31 run / 29 化合物が adopted**で、required primary 64 本のうち 30 本を被覆する。**CBX の Google Trends raw は 2026-11-04 の owner 決定で `cbx-search-trends` からこの study へ移管済み**（[`ISS-20261024-COL-016`](../../docs/issues/active/30-production-collection-expansion/20261024_p2_cbx-in-scope.md)）。**YouTube はこの study 自身の raw** で、THCNM（別名 THA）は 2 本の required primary query（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`）を各 1 run で持つ。

登録集合は **63 検索トピック**で、63 の化学的に確定した物質という意味ではない。うち 27 は 2026-11-15 に登録したが**未収集**である（「2026-11-15 登録バッチ」）。この README は、検索語・構造形式・被覆状態を混ぜずに次の四層へ分ける。

1. **構造形式辞書** — taxonomy concept が表す形式と、形式ごとの構造（位置異性体・酸／中性／エステル・立体化学）および根拠（「構造形式辞書」）。
2. **検索語 → 形式の crosswalk** — 登録 63 語それぞれの語の範囲と、対応する形式または**未解決**（「検索語 → 構造形式の crosswalk」）。
3. **term-to-query map** — taxonomy concept と canonical query の対応、および語ごとの被覆状態（「登録済みキーワードと収集状態」）。
4. **collection coverage** — ソース別の被覆状態と凡例（「収集被覆」）。

形式が証拠で支えられても owner が登録語として列挙していないものは、**未登録・未収集の候補形式**として 4 層の外に置き、query ID も run も与えない。2026-11-15 に登録指示された 27 形式は候補状態を終え、構造形式辞書・crosswalk・term-to-query map に登録済みで、被覆は未収集である（TAX-045）。

run-level の事実（run id・件数・観測窓）は [`metadata/data-catalog.json`](metadata/data-catalog.json)、採用宣言、[methodology.md](methodology.md)、source audit を正本とする。集計・配布は別研究 [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)（横断集計）が担当する。ここは「素材」、あちらは「配布物」。

## 研究質問

> 日本におけるカンナビノイド成分へのオンライン関心は、どのように推移しているか？
>
> Google Trends は `geo=JP`。X / YouTube は国単位のgeo filterを持たず、YouTubeは日本語の製品語「リキッド」による検索語ベースの近似を用いる（[methodology.md](methodology.md) §1.4・§2.3）。

## 対象トピック

登録 **63 検索トピック**（63 の化学的に確定した物質という意味ではない）。登録済み検索語の正本は [`metadata/queries/query-registry.json`](../../metadata/queries/query-registry.json)。

この節は三つを混ぜない。

1. **検索語** — owner が登録した文字列。系列が測るのはその文字列への一致だけである。
2. **構造形式** — 物質の構造上の単位（位置異性体、酸／中性／エステル、立体化学）。証拠が支える粒度までしか書かない。
3. **被覆状態** — ソース別に adopted run があるか。「収集被覆」に置き、同一性・形式の状態と混ぜない。

`major` / `minor` / `semisynthetic` / `synthetic` は taxonomy の `skos:broader`（経路・由来の次元）で、異性体や構造の解像度を表さない。全系列が測るのは登録文字列への一致であり、返却結果の化学的同一性は確認していない。収集条件は [methodology.md](methodology.md) §1.3、§2.1.2、§2.1.3、§2.1.6、§2.3。

### 化学・トピック辞書（登録 63 トピック）

「何を検索語として登録したか」「その概念が表す構造形式をどこまで確認したか」「その語と形式の関係を証拠が確定するか」を分けて示す。形式が確認できない語を形式辞書に載せず、crosswalk で「未解決」と書く。

#### 構造形式辞書 — 概念が表す形式

taxonomy concept が表す形式だけを載せる。**検索語と形式の関係は次表の crosswalk で別に扱う。** 異性体未指定のファミリー（`THCP` / `THCJD` / `THCPO` / `THCB-O-acetate` / `THCJD-O-acetate`）と、異性体未指定の親トピックである `THCV` / `THCH`、市場語・未確認語は、形式が確定していないためこの表に載せない（`THCJD-O-acetate` は 2026-11-15 に異性体未指定の検索トピックとして登録したため crosswalk と term-to-query map に現れるが、形式辞書の行はもたない）。ただし `THCV` / `THCH` の 2026-11-15 登録 Δ8/Δ9 形式（`Δ9-THCV` / `Δ8-THCV` / `Δ8-THCH` / `Δ9-THCH`）は個別形式の行をもつ。証拠支持の有無と登録は別であり、2026-11-15 に候補表から登録した 27 形式のうち、形式が確定する 26 形式を本表の末尾に置く。

| 構造形式 | 位置異性体 | 酸／中性／エステル | 立体化学 | 形式の状態 | taxonomy concept | 根拠（検証済みレコード・確認） |
|---|---|---|---|---|---|---|
| `Δ9-THC` | Δ9 | 中性 | レコードは天然の立体異性体を指す。概念名は特定の立体異性体を指定しない（台帳 2026-11-15 の粒度注記） | 検証済みレコード | `compound_thc` | ChEBI 66964 / Wikidata Q190067。登録文字列 `THC` は総称（crosswalk 参照） |
| `CBD` | —（Δ 体の区別なし） | 中性 | 同上 | 検証済みレコード | `compound_cbd` | ChEBI 69478 / Wikidata Q422917 |
| `CBG` | — | 中性 | 同上 | 検証済みレコード | `compound_cbg` | ChEBI 69477 / Wikidata Q412122 |
| `CBGA` | — | 酸 | レコード準拠（立体化学の粒度は本変更で未検証） | 検証済み＋owner 確認 | `compound_cbga` | ChEBI 67081 / Wikidata Q27135612 / UNII 80I4ZM847Y |
| `CBN` | — | 中性 | レコードに立体化学層なし（未指定） | 検証済みレコード | `compound_cbn` | ChEBI 3360 / Wikidata Q265831 |
| `CBC` | — | 中性 | レコードに立体化学層なし（未指定） | 検証済みレコード | `compound_cbc` | ChEBI 3357 / Wikidata Q410949 |
| `CBE`（cannabielsoin） | — | 中性 | 未指定（概念は立体化学を指定しない） | owner 確認＋レコード | `compound_cbe` | UNII 2ERD6V6652 / Wikidata Q22668702 |
| `CBL`（cannabicyclol） | — | 中性 | 未指定（CAS 21366-63-2 / 67920-00-7 が立体化学の扱いを異にする） | owner 確認＋レコード | `compound_cbl` | Wikidata Q907909 / UNII MP5WZK8M5U |
| `CBDV`（cannabidivarin） | — | 中性 | 未指定（立体異性体グループ） | 検証済みグループレコード | `compound_cbdv` | Wikidata Q1104117（立体化学を定義した ChEBI 182159 は付けない） |
| `Δ9-THCA-A` | Δ9 | 酸 | 未確認（本変更では検証していない） | owner 命名・同一性未確認 | `compound_delta9_thca_a` | Moreno-Sanz 2016（DOI 10.1089/can.2016.0008）/ Filer 2021（DOI 10.1089/can.2021.0003）。単一の外部レコードは未選択 |
| `THCA-B` | Δ9（THCA-A の構造異性体） | 酸 | 未確認 | owner 命名・同一性未確認 | `compound_thca_b` | 同上。THCA-A の別名ではない |
| `Δ8-THCA` | Δ8 | 酸 | 未確認 | 部分指定・同一性未確認 | `compound_delta8_thca` | 構造・命名の出所（A/B カルボキシル配置を含む）を本変更で確認していない |
| `Δ8-THCB` | Δ8 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta8_thcb` | 文献は製品分析で Δ8 体を同定（Tanaka & Kikura-Hanajiri 2024、DOI 10.1248/yakushi.24-00029）。単一の外部レコードは未選択 |
| `Δ9-THCB` | Δ9 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta9_thcb` | Linciano et al. 2020（DOI 10.1021/acs.jnatprod.9b00876）/ 同上 |
| `Δ8-THCP` | Δ8 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta8_thcp` | **registry record + 製品検出（文献）**: PubChem CID 44307335 / CAS 51768-60-6 / UNII Q6P6W9SNR2 / Wikidata Q141317106。2026 年の製品検出報告（TAX-042）。taxonomy に単一レコードは未選択、本研究の製品分析ではない |
| `Δ9-THCP` | Δ9 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta9_thcp` | **registry record + 植物単離**: PubChem CID 6453074 / CAS 54763-99-4 / UNII WTK87HN3LG / Wikidata Q85806080。Citti et al. 2019 が植物から単離・構造確認（TAX-042）。単一レコードは未選択 |
| `Δ8-THCJD` | Δ8 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta8_thcjd` | **registry record + 製品分析**: PubChem CID 102024084 / CAS 431041-39-3 / Wikidata Q114242092。Tanaka & Kikura-Hanajiri 2024 が国内流通製品から NMR 同定（TAX-042）。特定製品の分析で、本研究の観測ではない |
| `Δ9-THCJD` | Δ9 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta9_thcjd` | **registry record + 製品分析**: PubChem CID 155318984 / CAS 2552798-63-5。同上（TAX-042）。特定製品の分析で、本研究の観測ではない |
| `Δ8-THCP-O-acetate` | Δ8 | エステル（アセテート） | 未確認 | 法令の構造グループ（製品同定なし） | `compound_delta8_thcp_o_acetate` | **法令（構造グループ）+ registry record**: 令和6年厚生労働省令第81号の別紙が Δ8/Δ9 両構造を列挙（麻薬を除く）。PubChem CID 172874392。CAS / GSRS / Wikidata は未確認。**製品分析**: 未確認（TAX-042） |
| `Δ9-THCP-O-acetate` | Δ9 | エステル（アセテート） | 未確認 | 法令の構造グループ（製品同定あり） | `compound_delta9_thcp_o_acetate` | **法令（構造グループ）+ registry record + 製品分析**: 同上の別紙。PubChem CID 172677450 / CAS 2829292-82-0 / Wikidata Q122689235。Tanaka et al. 2025（DOI 10.1002/dta.3883）が製品から同定（TAX-042） |
| `Δ8-THCB-O-acetate` | Δ8 | エステル（アセテート） | 未確認 | 法令の構造グループ（製品同定なし） | `compound_delta8_thcb_o_acetate` | **法令（構造グループ）+ registry record**: 同上の別紙が列挙。PubChem CID 172871934。CAS / GSRS / Wikidata は未確認。**製品分析**: 未確認（TAX-042） |
| `Δ9-THCB-O-acetate` | Δ9 | エステル（アセテート） | 未確認 | 法令の構造グループ（製品同定なし） | `compound_delta9_thcb_o_acetate` | **法令（構造グループ）+ registry record**: 同上の別紙が列挙。PubChem CID 172875699。CAS / GSRS / Wikidata は未確認。**製品分析**: 未確認。Tanaka et al. 2025 が同定したのは別エステルの `Δ9-THCB-O-butanoate` で本行に含めない（TAX-042） |
| `Δ8-THC` | Δ8 | 中性 | 未確認 | owner 命名・同一性未確認（部分指定） | `compound_delta8_thc` | **命名標準 + 知識グラフ**: 命名標準の 7 分類の一つ。2024 年厚生労働省令は Δ9 系列（6a,7,8,10a-テトラヒドロ）と Δ8 系列（6a,7,10,10a-テトラヒドロ）を別の構造グループとして定義（麻薬を除く）。知識グラフは CAS 5957-75-7・天然存在 confirmed を記録。form-level 外部 record は taxonomy に未選択 |
| `Δ6a(10a)-THC` | Δ6a(10a) | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta6a_10a_thc` | **命名標準 + 知識グラフ**: 命名標準の 7 分類（WHO Annex 1）の一つ。旧式名 `Δ3-THC`。知識グラフは厚労省統制物質一覧への記載・規制区分「麻薬」・天然存在未確認を記録。form-level 外部識別子は未選択（CAS 未記録）。**製品分析**: 未確認 |
| `Δ6a(7)-THC` | Δ6a(7) | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta6a_7_thc` | **命名標準 + 知識グラフ**: 同上。旧式名 `Δ4-THC`。天然存在未確認、化学合成例あり。form-level 外部識別子は未選択（CAS 未記録）。**製品分析**: 未確認 |
| `Δ7-THC` | Δ7 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta7_thc` | **命名標準 + 知識グラフ**: 同上。旧式名 `Δ5-THC` は対応例あり・構造確認要。天然存在未確認。form-level 外部識別子は未選択（CAS 未記録）。**製品分析**: 未確認 |
| `Δ10-THC` | Δ10 | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta10_thc` | **命名標準 + 知識グラフ**: 同上。旧式名 `Δ2-THC` は構造確認要。知識グラフは CAS 50554-36-6 を記録するが、本変更で外部 record を再検証していない。天然存在未確認。**製品分析**: 未確認 |
| `Δ9(11)-THC` | Δ9(11) | 中性 | 未確認 | owner 命名・同一性未確認 | `compound_delta9_11_thc` | **命名標準 + 知識グラフ**: 同上。旧式名 `Δ1(7)-THC`、慣用名 `Δ11-THC` / `exo-THC`。天然存在未確認。form-level 外部識別子は未選択（CAS 未記録）。**製品分析**: 未確認 |
| `Δ9-THCV` | Δ9 | 中性 | 未確認 | registry record 記録済み（単一レコード未選択） | `compound_delta9_thcv` | **registry record**: ChEBI 755032 / Wikidata Q76009679（CAS 31262-37-0、PubChem CID 93147）。立体化学未指定の Q254768 もある（TAX-043）。`compound_thcv` の粒度を狭めるかは owner 判断 |
| `Δ8-THCV` | Δ8 | 中性 | 未確認 | 法令（指定薬物の列挙）のみ | `compound_delta8_thcv` | **規制資料**: 国内の規制資料が Δ8-THCV / Δ9-THCV を指定薬物として記録（`research/regulatory-status/THCV.md`）。registry record は未確認（2026-11-15 の ChEBI 検索は 0 件、TAX-043） |
| `Δ8-THCH` | Δ8 | 中性 | 未確認 | 法令の構造グループ（製品同定なし） | `compound_delta8_thch` | **法令（構造グループ）**: 消費者庁の THCH 指定薬物資料が Δ8-THCH / Δ9-THCH を対象として記録（個別指定 2023-08-04・包括指定 2023-09-10、`research/regulatory-status/THCH.md` §1）。**registry record**: 未選択。**製品分析**: 未確認 |
| `Δ9-THCH` | Δ9 | 中性 | 未確認 | 法令の構造グループ（製品同定なし） | `compound_delta9_thch` | **法令（構造グループ）**: 同上。**registry record**: 未選択。**製品分析**: 未確認 |
| `9(R)-HHC` | —（C-9 エピマー） | 中性 | (6aR,9R,10aR)（`9β-HHC`） | registry record 記録済み（単一レコード未選択） | `compound_9_r_hhc` | **registry record + WHO レビュー**: PubChem CID 11067065 / CAS 36403-90-4 / InChIKey `XKRHRBJLCLXSGE-DJIMGWMZSA-N`。WHO 47th ECDD (2024) §2C が CBD 由来製品の主要エピマーの一つとして記録。**製品分析**: 特定製品の同定ではない |
| `9(S)-HHC` | —（C-9 エピマー） | 中性 | (6aR,9S,10aR)（`9α-HHC`） | registry record 記録済み（単一レコード未選択） | `compound_9_s_hhc` | **registry record + WHO レビュー**: PubChem CID 14378541 / CAS 36403-91-5 / InChIKey `XKRHRBJLCLXSGE-USXIJHARSA-N`。WHO 47th ECDD (2024) §2C が同上として記録。**製品分析**: 特定製品の同定ではない |
| `(6aS,9S,10aS)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=S / 9=S / 10a=S | WHO レビュー（配置のみ） | `compound_6as_9s_10as_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aS,9S,10aS)`（6a=S / 9=S / 10a=S）。(6aR,9R,10aR)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |
| `(6aS,9R,10aS)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=S / 9=R / 10a=S | WHO レビュー（配置のみ） | `compound_6as_9r_10as_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aS,9R,10aS)`（6a=S / 9=R / 10a=S）。(6aR,9S,10aR)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |
| `(6aS,9S,10aR)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=S / 9=S / 10a=R | WHO レビュー（配置のみ） | `compound_6as_9s_10ar_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aS,9S,10aR)`（6a=S / 9=S / 10a=R）。(6aR,9R,10aS)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |
| `(6aS,9R,10aR)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=S / 9=R / 10a=R | WHO レビュー（配置のみ） | `compound_6as_9r_10ar_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aS,9R,10aR)`（6a=S / 9=R / 10a=R）。(6aR,9S,10aS)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |
| `(6aR,9S,10aS)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=R / 9=S / 10a=S | WHO レビュー（配置のみ） | `compound_6ar_9s_10as_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aR,9S,10aS)`（6a=R / 9=S / 10a=S）。(6aS,9R,10aR)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |
| `(6aR,9R,10aS)-HHC` | —（6a/9/10a の立体配置） | 中性 | 6a=R / 9=R / 10a=S | WHO レビュー（配置のみ） | `compound_6ar_9r_10as_hhc` | **WHO レビュー（グループ）**: WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示する。配置 `(6aR,9R,10aS)`（6a=R / 9=R / 10a=S）。(6aS,9S,10aR)-HHC のエナンチオマー。**registry record**: 個別に選択していない。**製品分析**: 個別の同定は確認していない |

- **「形式の状態」の読み方**: `検証済みレコード` は概念が検証済み外部レコードに対応する状態、`owner 確認` は owner が意図された同一性を確認した状態、`owner 命名・同一性未確認` は owner が検索トピックとして形式名を登録したが単一の外部レコードを選択していない状態、`部分指定` は形式の一部（例: Δ8 系列）だけが指定され単一構造を確定しない状態である。
- **立体化学の扱い**: レコードが天然の立体異性体を指す場合でも、概念名が特定の立体異性体を指定するという主張ではない（[`docs/provenance/compound-taxonomy.md`](../../docs/provenance/compound-taxonomy.md) の 2026-11-15 節「粒度の扱い」）。立体化学を指定しない概念には、立体化学を定義したレコードを付けない（CBDV の ChEBI 182159 を付けない判断、THCV の `exactMatch` 削除）。
- **酸／中性／エステル**: 酸型（CBGA / THCA 類）と中性型（CBG / THC 類）を別概念として扱う。総称 `THCB-O-acetate` / `THCPO` / `THC-O` は family または未解決として crosswalk に残す。一方、証拠が位置異性体を指定する `Δ8/Δ9-THCP-O-acetate` と `Δ8/Δ9-THCB-O-acetate` は個別の構造形式として本表に載せる。`THCJD-O-acetate` は Δ8/Δ9 未指定の検索トピックであり、個別形式とは扱わない（ISS-20261115-TAX-045）。

#### 検索語 → 構造形式の crosswalk（登録 63 トピック）

`検索語の範囲` は次の 5 値。`対応する構造形式` が「未解決」のとき、それは形式が存在しないという意味ではなく、**この study の登録語と形式の関係をリポジトリの証拠が確定しない**という意味である。

- `個別形式` — 語が 1 つの構造形式を指定する。
- `異性体未指定` — Δ8/Δ9 など、検索語が位置異性体を区別しないファミリー・名称。立体化学の未指定だけではこの値にせず、構造形式辞書で別記する。
- `総称リテラル` — owner が語を登録したが、化学的な展開を定義していない。
- `市場・供給元語` — 市場・供給元の語で、構造は未確認。
- `未確認リテラル` — 略号の展開がリポジトリに記録されていない。

| 登録検索語 | taxonomy concept | taxonomy分類（`skos:broader`） | 検索語の範囲 | 対応する構造形式（証拠が支える範囲） | 未解決点・根拠 |
|---|---|---|---|---|---|
| CBD | `compound_cbd` | `compound_major` | 個別形式 | CBD（中性） | 名称と検証済みレコード。返却結果の内容は同定しない |
| CBDV | `compound_cbdv` | `compound_minor` | 個別形式（立体化学は未指定） | CBDV（中性、立体異性体グループ） | グループレコードのみ。立体化学を指定しない |
| CBC | `compound_cbc` | `compound_minor` | 個別形式 | CBC（中性、立体化学未指定） | `CBC` は他分野の略号とも衝突する |
| CBE | `compound_cbe` | `compound_minor` | 個別形式 | cannabielsoin（中性） | owner が 2026-11-11 に確認。識別子を検証済み |
| CBG | `compound_cbg` | `compound_minor` | 個別形式 | CBG（中性） | 検証済みレコード |
| CBGa | `compound_cbga` | `compound_minor` | 個別形式（酸） | CBGA（酸） | owner 確認。CBG は CBGA の脱炭酸体で別概念 |
| CBL | `compound_cbl` | `compound_minor` | 個別形式 | cannabicyclol（中性） | owner 確認。単一 CAS を断定しない |
| CBN | `compound_cbn` | `compound_minor` | 個別形式 | CBN（中性、立体化学未指定） | 検証済みレコード |
| Δ8-THCA | `compound_delta8_thca` | `compound_identity_unverified`（管理） | 個別形式（部分指定） | Δ8 系列の酸（A/B カルボキシル配置は未確認） | 構造・命名の出所を本変更で確認していない |
| Δ8-THCB | `compound_delta8_thcb` | `compound_identity_unverified`（管理） | 個別形式 | Δ8-THCB（中性） | 文献は製品分析で同定。識別子は未選択 |
| Δ9-THCA-A | `compound_delta9_thca_a` | `compound_identity_unverified`（管理） | 個別形式 | Δ9-THCA-A（酸） | 文献は Δ9 酸の A 型を記録。識別子は未選択 |
| Δ9-THCB | `compound_delta9_thcb` | `compound_identity_unverified`（管理） | 個別形式 | Δ9-THCB（中性） | 文献は単離・構造確認と製品同定を記録。識別子は未選択 |
| THCA-B | `compound_thca_b` | `compound_identity_unverified`（管理） | 個別形式 | THCA-B（酸、THCA-A の構造異性体） | 文献は別個の構造異性体として扱う。識別子は未選択 |
| THCB-O-acetate | `compound_thcb_o_acetate` | `compound_identity_unverified`（管理） | 異性体未指定 | THCB-O-acetate（エステル、Δ8/Δ9 未指定） | 法令は Δ8/Δ9 両構造を列挙。製品中の分析同定は未確認 |
| THCJD | `compound_thcjd` | `compound_identity_unverified`（管理） | 異性体未指定 | THC-JD / 3-octyl-THC（C8、Δ8/Δ9 未指定） | owner が確認したのは検索語の範囲。単一物質の同定ではない |
| THCP | `compound_thcp` | `compound_identity_unverified`（管理） | 異性体未指定 | tetrahydrocannabiphorol（C7、Δ8/Δ9 未指定） | owner が確認したのは検索語の範囲。単一物質の同定ではない |
| THCPO | `compound_thcpo` | `compound_identity_unverified`（管理） | 異性体未指定 | THCP-O-acetate（エステル、Δ8/Δ9 未指定） | owner の確認は `THCPO` が THCP-O-acetate を指す意味まで。異性体の指定はない |
| THCV | `compound_thcv` | `compound_minor` | 異性体未指定 | THCV（中性、Δ8/Δ9・立体化学未指定） | 検証済みレコードはいずれも Δ9 のため `exactMatch` を付けない（TAX-043） |
| THC | `compound_thc` | `compound_major` | 総称リテラル | 未解決（検索語→形式）。概念は Δ9-THC の検証済みレコードに対応 | 登録文字列は総称 `THC`。返却結果が Δ9 体である証明ではない。他の位置異性体は個別 concept/query として登録済みだが未収集であり、この総称 query からはいずれにも割り当てない（TAX-045） |
| THCA | `compound_thca` | `compound_identity_unverified`（管理） | 総称リテラル | 未解決（`THCA` の化学的参照先） | 総称概念は文字列登録として残る。owner は 3 個別トピックへ置換（TAX-041） |
| THCB | `compound_thcb` | `compound_identity_unverified`（管理） | 総称リテラル | 未解決（`THCB` の化学的参照先） | 総称概念は文字列登録として残る。owner は 3 個別トピックへ置換（TAX-041） |
| CBX | `compound_cbx` | `compound_minor` | 市場・供給元語 | 未解決（単一構造・識別子なし） | 多義語で、車両名等とも衝突する。判別用クエリを別に持つ |
| CRDH | `compound_crdh` | `compound_synthetic` | 市場・供給元語 | 未解決（構造不明） | scopeNote が structure unknown と記録する monitoring 対象 |
| CRDP | `compound_crdp` | `compound_synthetic` | 市場・供給元語 | 未解決（構造不明） | 同上 |
| H4CBH | `compound_h4cbh` | `compound_semisynthetic` | 市場・供給元語 | 未解決（略号未展開・識別子なし） | 水素化誘導体という分類のみ |
| HHBD | `compound_hhbd` | `compound_semisynthetic` | 市場・供給元語 | 未解決（略号未展開・識別子なし） | 同上 |
| HHC | `compound_hhc` | `compound_semisynthetic` | 市場・供給元語 | 未解決（立体異性体を分けない） | 既存の HHC query は立体異性体を分離しない。8 配置は別 concept/query として登録済みだが、すべて未収集（TAX-045） |
| HHCH | `compound_hhch` | `compound_synthetic` | 市場・供給元語 | 未解決（識別子未検証） | prefLabel は化学名だが外部レコードを検証していない |
| THCH | `compound_thch` | `compound_minor` | 異性体未指定 | THCH（中性、Δ8/Δ9 未指定） | 既存 query は異性体未指定。法令上の Δ8/Δ9 は個別 concept/query として登録済みだが未収集（TAX-045） |
| THCNM | `compound_thcnm` | `compound_semisynthetic`（暫定） | 市場・供給元語 | 未解決（化学的同一性未確認） | `THA` は同一 concept の商業名・別名。構造は未確認 |
| THC-O | `compound_thc_o` | `compound_semisynthetic` | 市場・供給元語（アセテート） | 未解決（単一構造なし） | 化学クラスは `chemclass_acetate`。`THCO` は別物質にも使われる |
| 10-OH-HHC | `compound_10_oh_hhc` | `compound_identity_unverified`（管理） | 未確認リテラル | 未解決（水酸化誘導体・位置異性体・別物質のいずれかは記録なし） | scopeNote は `compound_hhc` との関係を主張しない |
| CBND | `compound_cbnd` | `compound_identity_unverified`（管理） | 未確認リテラル | 未解決（略号の展開なし） | 化学名・構造の記録なし |
| CBP | `compound_cbp` | `compound_identity_unverified`（管理） | 未確認リテラル | 未解決（略号の展開なし） | 同上 |
| HHCPO | `compound_hhcpo` | `compound_identity_unverified`（管理） | 未確認リテラル | 未解決（アセテート／エステルか別物質かも未記録） | 他概念との関係を主張しない |
| THXE | `compound_thxe` | `compound_identity_unverified`（管理） | 未確認リテラル | 未解決（略号の展開なし） | 化学名・構造の記録なし |
| Δ8-THCP | `compound_delta8_thcp` | `compound_identity_unverified`（管理） | 個別形式 | Δ8-THCP（中性。単一レコードは未選択） | registry record と文献の製品検出報告の記録のみ。登録文字列について単一の外部レコードを選択していない |
| Δ9-THCP | `compound_delta9_thcp` | `compound_identity_unverified`（管理） | 個別形式 | Δ9-THCP（中性。単一レコードは未選択） | 単離研究と registry record の記録のみ。検索結果の内容を確定しない |
| Δ8-THCJD | `compound_delta8_thcjd` | `compound_identity_unverified`（管理） | 個別形式 | Δ8 体（C8、中性。単一レコードは未選択） | 製品分析は特定製品についての文献記録。登録文字列について単一レコードを選択していない |
| Δ9-THCJD | `compound_delta9_thcjd` | `compound_identity_unverified`（管理） | 個別形式 | Δ9 体（C8、中性。単一レコードは未選択） | 製品分析は特定製品についての文献記録。登録文字列について単一レコードを選択していない |
| Δ8-THCP-O-acetate | `compound_delta8_thcp_o_acetate` | `compound_identity_unverified`（管理） | 個別形式 | Δ8 アセテート（エステル。法令の構造グループ、製品同定なし） | 法令の構造グループ該当のみ。CAS / GSRS / Wikidata と製品同定は未確認 |
| Δ9-THCP-O-acetate | `compound_delta9_thcp_o_acetate` | `compound_identity_unverified`（管理） | 個別形式 | Δ9 アセテート（エステル。法令の構造グループ＋製品同定） | 法令の列挙に加えて製品同定の文献があるが、本研究の分析ではなく検索結果を確定しない |
| Δ8-THCB-O-acetate | `compound_delta8_thcb_o_acetate` | `compound_identity_unverified`（管理） | 個別形式 | Δ8 アセテート（エステル。法令の構造グループ、製品同定なし） | 法令の構造グループ該当のみ。製品同定は未確認 |
| Δ9-THCB-O-acetate | `compound_delta9_thcb_o_acetate` | `compound_identity_unverified`（管理） | 個別形式 | Δ9 アセテート（エステル。法令の構造グループ、製品同定なし） | 法令の構造グループ該当のみ。同定済みの別エステル（`Δ9-THCB-O-butanoate`）を本行へ読み替えない |
| Δ8-THC | `compound_delta8_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ8-THC（中性。form-level 外部レコードは未選択） | 命名標準・知識グラフ・法令の構造グループの記録のみ。form-level の外部レコードは未選択 |
| Δ6a(10a)-THC | `compound_delta6a_10a_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ6a(10a)-THC（中性。form-level 外部識別子なし） | 命名標準・知識グラフ・法令の記載のみ。form-level 外部識別子は未選択で製品分析も未確認 |
| Δ6a(7)-THC | `compound_delta6a_7_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ6a(7)-THC（中性。form-level 外部識別子なし） | 命名標準・知識グラフの記録のみ。form-level 外部識別子は未選択で製品分析も未確認 |
| Δ7-THC | `compound_delta7_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ7-THC（中性。form-level 外部識別子なし） | 命名標準・知識グラフの記録のみ。名称の対応は同一性の結論ではない |
| Δ10-THC | `compound_delta10_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ10-THC（中性。CAS 50554-36-6 は未再検証） | 記録された CAS は本変更で再検証していない。form-level 外部レコードは未選択 |
| Δ9(11)-THC | `compound_delta9_11_thc` | `compound_identity_unverified`（管理） | 個別形式 | Δ9(11)-THC（中性。form-level 外部識別子なし） | 命名標準・知識グラフの記録のみ。慣用名は命名の記録で同一性の結論ではない |
| Δ9-THCV | `compound_delta9_thcv` | `compound_identity_unverified`（管理） | 個別形式 | Δ9-THCV（中性。registry record は先行レビュー記録） | 先行 crosswalk レビューが検証した registry record。`compound_thcv` の粒度は未決 |
| Δ8-THCV | `compound_delta8_thcv` | `compound_identity_unverified`（管理） | 個別形式 | Δ8-THCV（中性。registry record 未確認） | 規制資料の列挙のみ。registry record は未確認で、法令の列挙は製品検出ではない |
| THCJD-O-acetate | `compound_thcjd_o_acetate` | `compound_identity_unverified`（管理） | 異性体未指定 | THCJD-O-acetate（エステル。Δ8/Δ9 未指定） | 法令の記載のみで異性体の指定がない。Δ8/Δ9 の構造は本リポジトリで未確認 |
| Δ8-THCH | `compound_delta8_thch` | `compound_identity_unverified`（管理） | 個別形式 | Δ8-THCH（中性。法令の構造グループ、製品同定なし） | 法令の構造グループの記録のみ。registry record も製品同定も未確認 |
| Δ9-THCH | `compound_delta9_thch` | `compound_identity_unverified`（管理） | 個別形式 | Δ9-THCH（中性。法令の構造グループ、製品同定なし） | 法令の構造グループの記録のみ。registry record も製品同定も未確認 |
| 9(R)-HHC | `compound_9_r_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aR,9R,10aR)-HHC`（中性。registry record は先行レビュー記録） | WHO の記載は製品組成についてのレビュー。特定製品の同定でも本研究の分析でもない |
| 9(S)-HHC | `compound_9_s_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aR,9S,10aR)-HHC`（中性。registry record は先行レビュー記録） | WHO の記載は製品組成についてのレビュー。特定製品の同定でも本研究の分析でもない |
| (6aS,9S,10aS)-HHC | `compound_6as_9s_10as_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aS,9S,10aS)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |
| (6aS,9R,10aS)-HHC | `compound_6as_9r_10as_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aS,9R,10aS)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |
| (6aS,9S,10aR)-HHC | `compound_6as_9s_10ar_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aS,9S,10aR)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |
| (6aS,9R,10aR)-HHC | `compound_6as_9r_10ar_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aS,9R,10aR)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |
| (6aR,9S,10aS)-HHC | `compound_6ar_9s_10as_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aR,9S,10aS)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |
| (6aR,9R,10aS)-HHC | `compound_6ar_9r_10as_hhc` | `compound_identity_unverified`（管理） | 個別形式 | `(6aR,9R,10aS)-HHC`（中性。WHO レビューの配置のみ） | WHO が可能な配置として図示するのみ。個別 registry record も製品同定も未確認 |

#### 2026-11-15 登録バッチ — 候補表から登録した 27 形式（未収集）

owner は 2026-11-15、直前に棚卸しした**未登録候補 27 行を検索トピックとして登録すること**を明示した（[`ISS-20261115-TAX-045`](../../docs/issues/active/50-taxonomy-standards/20261115_p2_candidate-form-registration.md)）。登録したのは候補表の 27 行そのもので、内訳は THC の位置異性体 6 形式、THCP・THCJD・THCPO・THCB-O-acetate・THCH・THCV の個別異性体と `THCJD-O-acetate`（異性体未指定）の 13 形式、HHC の立体異性体 8 形式である（6 + 13 + 8 = 27）。

- **登録の内容**: 27 形式それぞれに taxonomy concept（`compound_identity_unverified`）と canonical query 2 本（`<term>` = `compound_general`、`<term> リキッド` = `product_liquid`、いずれも `active`）を与えた。形式が証拠で支えられることは登録の条件ではない。形式・語・被覆は上の 3 表に分けて載せ、本節は決定の記録だけを持つ。
- **収集状態は「未収集」**: 27 語はいずれも run を持たない。**0 観測でも欠測でも収集失敗でもない**。既存の Google Trends / YouTube 系列をこれらの形式へ割り当てない。
- **既存の割当ては不変**: 総称 `THC` / `THCA` / `THCB`、ファミリー `THCP` / `THCJD` / `THCPO` / `THCB-O-acetate` / `THCV` / `THCH` / `HHC` の query ID・canonical_text・status・run は変更していない。`THC` の系列はどの位置異性体へも帰属させない。
- **証拠の種類は混ぜない**: registry record（先行レビュー記録）、法令の構造グループ（令和6年厚生労働省令第81号、消費者庁の THCH 指定薬物資料）、命名標準と知識グラフ、WHO 47th ECDD (2024) §2C の可能な配置のレビュー、製品分析（文献）は別の証拠である。**法令の構造グループ該当は製品検出ではなく、WHO のレビューは配置ごとの registry record でも製品同定でもない。** 単一の検証済み外部レコードを選択していないため、27 概念には `skos:exactMatch` も識別子も `skos:related` も付けない。
- **`THCJD-O-acetate` は異性体未指定のまま**登録した。Δ8 / Δ9 の別個の構造は本リポジトリで確認しておらず、本バッチでも分割しない。
- **今回のレビュー範囲で未登録の候補行は残っていない。** `Δ9-THCB-O-butanoate` は先行レビューが本候補に含めなかった別エステルで（`Δ9-THCB-O-acetate` の行参照）、本 study の候補インベントリの対象外である。

#### 辞書全体の注記

- **分類は経路・由来の次元**: `compound_major` / `compound_minor` / `compound_semisynthetic` / `compound_synthetic` は taxonomy の分類で、化学クラスは別次元（[`chemical-class-taxonomy.skos.jsonld`](../../metadata/taxonomy/chemical-class-taxonomy.skos.jsonld)）。分類は異性体・構造の同定ではない。本標準化は 2026-11-11 の P1 判断を含め、分類・membership を変更しない。
- **`compound_identity_unverified` は管理カテゴリ**: 43 語がここにあり、経路・天然存在・化学クラス・別名・規制状態を主張しない。内訳は、展開・化学的同一性が未確認の 7 語（10-OH-HHC、CBND、CBP、HHCPO、THXE、総称 THCA / THCB）、owner の確認が検索語の範囲にとどまる 3 語（THCP・THCJD は family 範囲、THCPO は THCP-O-acetate の意味のみ）、2026-11-11 に登録した 6 個別検索トピック、2026-11-15 に候補表から登録した 27 形式。owner 確認済みの検索範囲と、単一物質としての同一性確認は別である。管理カテゴリの語には検証済み外部識別子を付けない。
- **owner 確認済みの同一性**: CBE・CBL・CBGa は owner がそれぞれ cannabielsoin・cannabicyclol・cannabigerolic acid と確認し、`compound_minor` に置いた。識別子は taxonomy に、根拠は [`docs/provenance/compound-taxonomy.md`](../../docs/provenance/compound-taxonomy.md) に記録する。それでも系列は `CBE` / `CBE リキッド` 等の文字列一致を測るもので、各結果がその物質を扱うことの確認ではない。
- **family 範囲**: THCP は tetrahydrocannabiphorol（C7）同族体、THCJD は THC-JD / 3-octyl-THC（C8）同族体で、いずれも Δ8/Δ9 未指定。owner が確認したのは**検索語の範囲**で、単一物質の同定ではない。THCPO は owner が `THCPO` = THCP-O-acetate の意味のみ確認し、異性体を名指ししなかったため、**異性体未指定の family** として登録する（family 扱いは回答の登録上の整理であり、owner が family を明示的に確認したものではない）。THCB-O-acetate も異性体未指定。個別異性体の registry 記録は family 概念へ転記せず、台帳と異性体レビューに記録する。判断は [`ISS-20261111-TAX-042`](../../docs/issues/active/50-taxonomy-standards/20261111_p3_isomer-family-evidence-review.md)。
- **THCA / THCB の総称と個別**: `compound_thca` / `compound_thcb` は総称文字列の登録として残り、既存 run もそのまま保持する。Δ9-THCA-A / THCA-B / Δ8-THCA、Δ8-THCB / Δ9-THCB / THCB-O-acetate は別 concept・別 query で、既存 run を再割当てしない（[`ISS-20261111-TAX-041`](../../docs/issues/active/50-taxonomy-standards/20261111_p2_thca-thcb-subtopic-registration.md)）。Δ8-THCA は構造・命名の出所も未確認である。
- **THC のラベルとクエリ**: taxonomy の prefLabel は Δ9-THC だが、登録クエリは総称文字列 `THC`。返却結果が Δ9 体である証明ではない。総称 `THC` の series を特定の位置異性体へ読み替えない。Δ8-THC と他の 5 位置異性体は 2026-11-15 に**別概念・別 query** として登録した形式であり、`THC` の再ラベルでも、`THC` series の再割当てでもない。
- **THCV の粒度は未決**: 概念は Δ8/Δ9 と立体化学を指定せず、検証済みレコードはすべて Δ9 のため `exactMatch` を持たない。2026-11-15 に `Δ9-THCV` / `Δ8-THCV` を別概念・別 query として登録したが、これは `compound_thcv` の粒度を変更せず、総称 `THCV` の series も移さない。Δ9 に狭めるかは引き続き owner の scope 判断である（[`ISS-20261115-TAX-043`](../../docs/issues/active/50-taxonomy-standards/20261115_p0_compound-external-identifier-crosswalk.md)）。
- **外部識別子 crosswalk**: 2026-11-15 の P0 修正で、taxonomy と IPTC 対応表に重複していた 9 概念の `skos:exactMatch` を live registry（ChEBI API・Wikidata API）で再検証した。CBD・THC・CBG・CBN・CBC・anandamide・2-AG は検証済みレコードへ差し替え、旧値（`chebi:32927` = nonadecane、`chebi:33669` = metallacycloalkanes 等）は削除した。THCV は概念が Δ8/Δ9 と立体化学を指定せず、検証済みレコードがいずれも Δ9 のため対応を削除（未対応）。CBDV は立体異性体グループの Wikidata Q1104117 のみとし、立体化学を定義した ChEBI 182159 は付けない。識別子は検索文字列の化学的同一性を確定しない（[`docs/provenance/compound-taxonomy.md`](../../docs/provenance/compound-taxonomy.md)、`ISS-20261115-TAX-043`）。
- **THCNM / THA**: `compound_semisynthetic`（暫定）。市場・供給元報告に基づく分類で、化学的同一性は未確認。`THA` は同一 concept の商業名・別名で、別物質とも断定しない（[`ISS-20261104-TAX-028`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thcnm-identity-unconfirmed.md)）。
- **THC-O**: 市場・family 名で単一構造は未確定。`THCO` は `query-variants.json` の variant で、別 query ID でも別 concept でもない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)）。
- **登録集合の由来**: 既存 15 化合物 + 追加 15 語 + 6 個別トピック + 2026-11-15 の候補形式 27 語（計 63）。CBC・CBDV は既存 concept を再利用した。canonical text は owner の表記のまま（`CBGa` の小文字 `a`、`10-OH-HHC` のハイフンを含む）。owner の依頼文は「17 物質」だが列挙は 15 語で、不足する 2 語は推測で補っていない（[`ISS-20261110-TAX-039`](../../docs/issues/active/50-taxonomy-standards/20261110_p2_compound-expansion-batch.md)、[`ISS-20261111-TAX-040`](../../docs/issues/active/50-taxonomy-standards/20261111_p1_compound-registration-state-batch.md)）。`compound_rare` は空のままで、`compound_cbdp` は登録していない。
- **27 語は登録済み・未収集**: 2026-11-15 の登録バッチ 27 形式は concept と canonical query を持ち、run を持たない。**未収集は 0 観測でも、欠測でも、収集失敗でもない。** 既存の series をこれらの形式へ帰属させない（[`ISS-20261115-TAX-045`](../../docs/issues/active/50-taxonomy-standards/20261115_p2_candidate-form-registration.md)）。

### 登録済みキーワードと収集状態（term-to-query map）

`metadata/queries/query-registry.json` を正本とする、taxonomy concept と canonical active query の対応。対象は `compound_general` と `product_liquid` の **129 query**。各 query record は 1 つの `compound_id` に結び付き、1 concept が複数 query を持てる（CBX の general 3 本、THCNM の liquid 2 本）。逆に 1 query が複数 concept を指すことはない。**この表は検索文字列と被覆の対応を持ち、形式・同一性の状態は「化学・トピック辞書」に置く。** 系列が測るのは登録文字列への一致であり、結果の化学的内容を同定しない。本標準化は query ID・canonical_text・status を変更しない。

| 登録検索語 | taxonomy concept（`compound_id`） | `compound_general`（`query_id`） | `product_liquid`（`query_id`） | 被覆・状態 |
|---|---|---|---|---|
| 10-OH-HHC | `compound_10_oh_hhc` | `10-OH-HHC` — `10-oh-hhc-general-ja` | `10-OH-HHC リキッド` — `10-oh-hhc-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| CBC | `compound_cbc` | `CBC` — `cbc-general-ja` | `CBC リキッド` — `cbc-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CBD | `compound_cbd` | `CBD` — `cbd-general-ja` | `CBD リキッド` — `cbd-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| CBDV | `compound_cbdv` | `CBDV` — `cbdv-general-ja` | `CBDV リキッド` — `cbdv-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| CBE | `compound_cbe` | `CBE` — `cbe-general-ja` | `CBE リキッド` — `cbe-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅ 331（partial、3/354 失敗）／X 設計外 |
| CBG | `compound_cbg` | `CBG` — `cbg-general-ja` | `CBG リキッド` — `cbg-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| CBGa | `compound_cbga` | `CBGa` — `cbga-general-ja` | `CBGa リキッド` — `cbga-liquid-ja` | GT 12m NO_DATA・5y NO_DATA／YouTube ✅／X 設計外 |
| CBL | `compound_cbl` | `CBL` — `cbl-general-ja` | `CBL リキッド` — `cbl-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅ 269（partial、5/296 失敗）／X 設計外 |
| CBN | `compound_cbn` | `CBN` — `cbn-general-ja` | `CBN リキッド` — `cbn-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CBND | `compound_cbnd` | `CBND` — `cbnd-general-ja` | `CBND リキッド` — `cbnd-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CBP | `compound_cbp` | `CBP` — `cbp-general-ja` | `CBP リキッド` — `cbp-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CBX | `compound_cbx` | `CBX` — `cbx-general-ja`; `CBX カンナビノイド` — `cbx-cannabinoid-ja`; `CBX 大麻` — `cbx-cannabis-ja` | `CBX リキッド` — `cbx-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CRDH | `compound_crdh` | `CRDH` — `crdh-general-ja` | `CRDH リキッド` — `crdh-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| CRDP | `compound_crdp` | `CRDP` — `crdp-general-ja` | `CRDP リキッド` — `crdp-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| Δ8-THCA | `compound_delta8_thca` | `Δ8-THCA` — `delta8-thca-general-ja` | `Δ8-THCA リキッド` — `delta8-thca-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCB | `compound_delta8_thcb` | `Δ8-THCB` — `delta8-thcb-general-ja` | `Δ8-THCB リキッド` — `delta8-thcb-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCA-A | `compound_delta9_thca_a` | `Δ9-THCA-A` — `delta9-thca-a-general-ja` | `Δ9-THCA-A リキッド` — `delta9-thca-a-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCB | `compound_delta9_thcb` | `Δ9-THCB` — `delta9-thcb-general-ja` | `Δ9-THCB リキッド` — `delta9-thcb-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| H4CBH | `compound_h4cbh` | `H4CBH` — `h4cbh-general-ja` | `H4CBH リキッド` — `h4cbh-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| HHBD | `compound_hhbd` | `HHBD` — `hhbd-general-ja` | `HHBD リキッド` — `hhbd-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| HHC | `compound_hhc` | `HHC` — `hhc-general-ja` | `HHC リキッド` — `hhc-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| HHCH | `compound_hhch` | `HHCH` — `hhch-general-ja` | `HHCH リキッド` — `hhch-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| HHCPO | `compound_hhcpo` | `HHCPO` — `hhcpo-general-ja` | `HHCPO リキッド` — `hhcpo-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| THC | `compound_thc` | `THC` — `thc-general-ja` | `THC リキッド` — `thc-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| THCA | `compound_thca` | `THCA` — `thca-general-ja` | `THCA リキッド` — `thca-liquid-ja` | GT 12m ✅・5y ✅／YouTube 未採用（NO_VIDEOS）／X 設計外 |
| THCA-B | `compound_thca_b` | `THCA-B` — `thca-b-general-ja` | `THCA-B リキッド` — `thca-b-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| THCB | `compound_thcb` | `THCB` — `thcb-general-ja` | `THCB リキッド` — `thcb-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| THCB-O-acetate | `compound_thcb_o_acetate` | `THCB-O-acetate` — `thcb-o-acetate-general-ja` | `THCB-O-acetate リキッド` — `thcb-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| THCH | `compound_thch` | `THCH` — `thch-general-ja` | `THCH リキッド` — `thch-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| THCJD | `compound_thcjd` | `THCJD` — `thcjd-general-ja` | `THCJD リキッド` — `thcjd-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| THCNM（別名 THA） | `compound_thcnm` | `THCNM` — `thcnm-general-ja` | `THCNM リキッド` — `thcnm-liquid-ja`; `THA リキッド` — `tha-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅（2/2、2 run）／X 設計外 |
| THC-O | `compound_thc_o` | `THC-O` — `thc-o-general-ja` | `THC-O リキッド` — `thc-o-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X ✅ |
| THCP | `compound_thcp` | `THCP` — `thcp-general-ja` | `THCP リキッド` — `thcp-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X 設計外 |
| THCPO | `compound_thcpo` | `THCPO` — `thcpo-general-ja` | `THCPO リキッド` — `thcpo-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| THCV | `compound_thcv` | `THCV` — `thcv-general-ja` | `THCV リキッド` — `thcv-liquid-ja` | GT 12m ✅・5y ✅／YouTube ✅／X ✅ |
| THXE | `compound_thxe` | `THXE` — `thxe-general-ja` | `THXE リキッド` — `thxe-liquid-ja` | GT 12m NO_DATA・5y ✅／YouTube ✅／X 設計外 |
| Δ8-THCP | `compound_delta8_thcp` | `Δ8-THCP` — `delta8-thcp-general-ja` | `Δ8-THCP リキッド` — `delta8-thcp-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCP | `compound_delta9_thcp` | `Δ9-THCP` — `delta9-thcp-general-ja` | `Δ9-THCP リキッド` — `delta9-thcp-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCJD | `compound_delta8_thcjd` | `Δ8-THCJD` — `delta8-thcjd-general-ja` | `Δ8-THCJD リキッド` — `delta8-thcjd-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCJD | `compound_delta9_thcjd` | `Δ9-THCJD` — `delta9-thcjd-general-ja` | `Δ9-THCJD リキッド` — `delta9-thcjd-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCP-O-acetate | `compound_delta8_thcp_o_acetate` | `Δ8-THCP-O-acetate` — `delta8-thcp-o-acetate-general-ja` | `Δ8-THCP-O-acetate リキッド` — `delta8-thcp-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCP-O-acetate | `compound_delta9_thcp_o_acetate` | `Δ9-THCP-O-acetate` — `delta9-thcp-o-acetate-general-ja` | `Δ9-THCP-O-acetate リキッド` — `delta9-thcp-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCB-O-acetate | `compound_delta8_thcb_o_acetate` | `Δ8-THCB-O-acetate` — `delta8-thcb-o-acetate-general-ja` | `Δ8-THCB-O-acetate リキッド` — `delta8-thcb-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCB-O-acetate | `compound_delta9_thcb_o_acetate` | `Δ9-THCB-O-acetate` — `delta9-thcb-o-acetate-general-ja` | `Δ9-THCB-O-acetate リキッド` — `delta9-thcb-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THC | `compound_delta8_thc` | `Δ8-THC` — `delta8-thc-general-ja` | `Δ8-THC リキッド` — `delta8-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ6a(10a)-THC | `compound_delta6a_10a_thc` | `Δ6a(10a)-THC` — `delta6a-10a-thc-general-ja` | `Δ6a(10a)-THC リキッド` — `delta6a-10a-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ6a(7)-THC | `compound_delta6a_7_thc` | `Δ6a(7)-THC` — `delta6a-7-thc-general-ja` | `Δ6a(7)-THC リキッド` — `delta6a-7-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ7-THC | `compound_delta7_thc` | `Δ7-THC` — `delta7-thc-general-ja` | `Δ7-THC リキッド` — `delta7-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ10-THC | `compound_delta10_thc` | `Δ10-THC` — `delta10-thc-general-ja` | `Δ10-THC リキッド` — `delta10-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9(11)-THC | `compound_delta9_11_thc` | `Δ9(11)-THC` — `delta9-11-thc-general-ja` | `Δ9(11)-THC リキッド` — `delta9-11-thc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCV | `compound_delta9_thcv` | `Δ9-THCV` — `delta9-thcv-general-ja` | `Δ9-THCV リキッド` — `delta9-thcv-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCV | `compound_delta8_thcv` | `Δ8-THCV` — `delta8-thcv-general-ja` | `Δ8-THCV リキッド` — `delta8-thcv-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| THCJD-O-acetate | `compound_thcjd_o_acetate` | `THCJD-O-acetate` — `thcjd-o-acetate-general-ja` | `THCJD-O-acetate リキッド` — `thcjd-o-acetate-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ8-THCH | `compound_delta8_thch` | `Δ8-THCH` — `delta8-thch-general-ja` | `Δ8-THCH リキッド` — `delta8-thch-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| Δ9-THCH | `compound_delta9_thch` | `Δ9-THCH` — `delta9-thch-general-ja` | `Δ9-THCH リキッド` — `delta9-thch-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| 9(R)-HHC | `compound_9_r_hhc` | `9(R)-HHC` — `9r-hhc-general-ja` | `9(R)-HHC リキッド` — `9r-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| 9(S)-HHC | `compound_9_s_hhc` | `9(S)-HHC` — `9s-hhc-general-ja` | `9(S)-HHC リキッド` — `9s-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aS,9S,10aS)-HHC | `compound_6as_9s_10as_hhc` | `(6aS,9S,10aS)-HHC` — `6as-9s-10as-hhc-general-ja` | `(6aS,9S,10aS)-HHC リキッド` — `6as-9s-10as-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aS,9R,10aS)-HHC | `compound_6as_9r_10as_hhc` | `(6aS,9R,10aS)-HHC` — `6as-9r-10as-hhc-general-ja` | `(6aS,9R,10aS)-HHC リキッド` — `6as-9r-10as-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aS,9S,10aR)-HHC | `compound_6as_9s_10ar_hhc` | `(6aS,9S,10aR)-HHC` — `6as-9s-10ar-hhc-general-ja` | `(6aS,9S,10aR)-HHC リキッド` — `6as-9s-10ar-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aS,9R,10aR)-HHC | `compound_6as_9r_10ar_hhc` | `(6aS,9R,10aR)-HHC` — `6as-9r-10ar-hhc-general-ja` | `(6aS,9R,10aR)-HHC リキッド` — `6as-9r-10ar-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aR,9S,10aS)-HHC | `compound_6ar_9s_10as_hhc` | `(6aR,9S,10aS)-HHC` — `6ar-9s-10as-hhc-general-ja` | `(6aR,9S,10aS)-HHC リキッド` — `6ar-9s-10as-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |
| (6aR,9R,10aS)-HHC | `compound_6ar_9r_10as_hhc` | `(6aR,9R,10aS)-HHC` — `6ar-9r-10as-hhc-general-ja` | `(6aR,9R,10aS)-HHC リキッド` — `6ar-9r-10as-hhc-liquid-ja` | GT 12m 未収集・5y 未収集／YouTube 未収集／X 設計外 |

- **CBX**: `compound_cbx` は general を 3 本持つ（`cbx-general-ja` / `cbx-cannabinoid-ja` / `cbx-cannabis-ja`）。`CBX カンナビノイド` / `CBX 大麻` は多義語 `CBX` の判別用で、別 concept ではない。
- **THCNM**: `compound_thcnm` は liquid を 2 本持つ（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）。`THA リキッド` は同一 concept の 2 本目の query で、`THA` は商業名・別名。2 query は別観測で、2 run を合算しない。
- **THCO 表記ゆれ**: `THCO` / `THCO リキッド` は [`query-variants.json`](../../metadata/queries/query-variants.json) の alternative で、`thc-o-general-ja` / `thc-o-liquid-ja` のまま。新しい query ID を作らない。canonical の 12ヶ月 NO_DATA を variant の系列で置換しない。
- **被覆・状態**: `GT` = Google Trends、`12m` / `5y` = 単独系列。`✅` は adopted run がある状態。`NO_DATA` / `未収集` / `NO_VIDEOS` / `partial` / `X 設計外` の意味は「収集被覆」に定義する。週数・件数・run は [`metadata/data-catalog.json`](metadata/data-catalog.json) と各 run を正本とする。
- **crosswalk 外の intent**: `product_oil`（`cbd-oil-ja`）と `other`（比較セット / CBX bridge / THCNM anchored）はこの map の対象外。比較セットは [`metadata/query-design.json`](metadata/query-design.json) の `comparison_scales` と [methodology.md](methodology.md) §2.1.4・§2.1.6 が正本。
- **設計上の required**: 6 検索トピックの `compound_general` は active のため、3 つの共通スケール policy（5年・12ヶ月・3ヶ月）それぞれの required 集合に 6 語ずつ、**計 18 件**の**設計上**の required entry が加わる。2026-11-15 の登録バッチ 27 語も `compound_general` が active のため、3 policy それぞれに 27 語ずつ、**計 81 件**が加わる。**合計 99 件は、既存構成からの累積追加数（18 + 81、各 policy 27 + 6 語ずつ）であり、policy ごとの有効な general 化合物の総数ではない。** 同じ 27 語の `product_liquid` は required primary を 37 本から **64 本**へ増やす。いずれも**設計上**の要求であり、未収集は収集失敗ではなく、0 観測でもない。
- **run の再割当てなし**: `thca-general-ja` / `thcb-general-ja` と既存 run は総称 concept のまま。6 個別トピックへ付け替えない。family query とその run も保持する（TAX-041・TAX-042）。
- **旧候補表の 27 行は本 map に現れる**: 2026-11-15 の owner 決定で 27 行を登録したため、各行は concept・general query・liquid query を持ち、被覆は**未収集**である（[`ISS-20261115-TAX-045`](../../docs/issues/active/50-taxonomy-standards/20261115_p2_candidate-form-registration.md)）。登録は収集の許可ではない。

## データソース

| ソース | ツール | 状態 |
|--------|--------|------|
| Google Trends | google-trends-mcp 0.1.1（`collection.core.cli collect --live`） | ✅ 登録 63 トピックのうち **5年 29/63・12ヶ月 21/63**。既存 15 化合物は 5年 15/15・12ヶ月 14/15（THC-O は NO_DATA）。追加 15 語は 5年 14/15・12ヶ月 7/15。2026-11-11 登録の 6 検索トピックは未収集。NO_DATA と失敗試行の内訳は「収集被覆」。CBX を含む共通スケール bridge は §2.1.6 |
| X (Twitter) | Apify `cPYLH3QT9GyzKhB4S` | ✅ 7 化合物（CBD は追加で 1 年 / 1ヶ月 / latest10 の 3 run。条件は未記録）。**geo filter なし**。X の query はこの 7 化合物だけで、残る 56 トピックは設計していない |
| YouTube | Apify `h7sDV53CddomktSi5` (`streamers/youtube-scraper`) | ✅ primary は liquid-only `<compound> リキッド` の **31 run / 29 化合物**（required query 30/64）。**`compound_thca` の `NO_VIDEOS`、2026-11-11 登録の 6 検索トピック 6 本、2026-11-15 登録の 27 本が未被覆**。CBE 331（3/354 失敗）・CBL 269（5/296 失敗）は partial。**date filter なし・geo filter なし**、`maxResults` 500、Shorts/streams 0。裸の化合物語 `HHC` 1 run は保持するが primary 外。raw は非追跡・公開対象外（§2.3） |

> **関連データセットとの役割分担**: 本データセットはカンナビノイドのトレンド分析用 raw を収蔵する。
> [`datasets/youtube-consistency/`](../youtube-consistency/) は YouTube 検索結果の一貫性・再現性検証を目的とする別研究である。

## 収集結果

Google Trends の系列・窓・欠測は [methodology.md](methodology.md) §2.1.2・§2.1.3 が正本。既存 14 化合物の 5年系列の機械可読レポートは [`docs/audits/gt-summary.json`](../../docs/audits/gt-summary.json) だが、**追加 15 語と 6 検索トピックはこの化合物集合外**なので各 run の `records_*.json` と [`metadata/data-catalog.json`](metadata/data-catalog.json) を正本とする。
単独系列の平均と比較セット（`common-scale-*` の**共通スケール**値）は別物なので混ぜない。
単独系列の平均は化合物間でも比べない（正規化が語ごとに違う）。比較は共通スケールでのみ行う。
**5年の共通スケールは、アンカー CBD/THC を含む legacy setA〜D（旧窓）と、現行窓の setA〜D / THCNM anchored run が catalog にある**（[methodology.md](methodology.md) §2.1.4・§2.1.6）。
12ヶ月の共通スケールは `common-scale-*` の各 run。**追加 15 語と 6 検索トピックには共通スケール run が無い**ので、単独系列の値を既存化合物と比較しない。
**CBX は 2026-11-04 に、CBX + CBD + THC を 1 リクエストで測る bridge を 12ヶ月・5年とも収集した**（[methodology.md](methodology.md) §2.1.6）。bridge の値は同一 run 内の共通スケールであり、単独系列の平均から作った値ではない。単独系列のほかに、比較セット（12ヶ月 `common-scale-*`・5年 `5y-common-scale-set*`・CBX bridge）、表記事前調査、リキッド系クエリの run がある（[methodology.md](methodology.md) §2.1.4〜§2.1.6）。

Google Trends は run ごとの相対指数（0-100）、YouTube は検索結果として返された動画件数で、**単位が異なる。両者を比較・合算しない**。

- **週次系列は全面で比較できるわけではない**: 既存の 5年は 3 窓（10 化合物が 2021-10-10 〜 2026-10-11（CBX を含む）、4 化合物が 2021-10-17 〜 2026-10-18、THCNM が 2021-10-31 〜 2026-11-01）、12ヶ月は 4 窓（8 化合物が 2025-09-28 〜 2026-09-27、4 化合物が 2025-10-19 〜 2026-10-18、CBX が 2025-10-12 〜 2026-10-11、THCNM が 2025-11-02 〜 2026-11-01）に分かれる。追加 15 語は 12ヶ月 `2025-11-09_2026-11-15`（観測 2025-11-09 〜 2026-11-08、53 週）と 5年 `2021-11-07_2026-11-15`（観測 2021-11-07 〜 2026-11-08、262 週）で、`today 12-m` / `today 5-y` を reference time で nominal に解決した**近似窓**である。各 run は自分のピーク=100 に正規化されるので、単独系列の値を化合物間・run 間で比べない。化合物間の比較は共通スケール（§2.1.4・§2.1.6）でのみ行う。

### 収集被覆（coverage layer）

ソース別の被覆状態の要約。run-level の事実（run id・件数・観測窓）は [`metadata/data-catalog.json`](metadata/data-catalog.json)、採用宣言、[methodology.md](methodology.md) §2、source audit を正本とし、この節は状態の定義と要約だけを持つ。

| 表示 | 意味 |
|---|---|
| ✅ | adopted run がある |
| `NO_DATA` | Google Trends を取得したが閾値未満で系列が返らなかった。**欠測で 0 観測ではない** |
| `未収集` | query は active だが run がない。**収集失敗でも 0 観測でもない** |
| `NO_VIDEOS` | YouTube actor は SUCCEEDED だが動画行が 0。絶対窓を導けず未採用。**世界全体の 0 ではない** |
| 失敗（HTTP 429） | 取得に失敗し adopted run がない。試行は quarantine に残る。**0 観測でも欠測でもない** |
| `partial` | adopted run はあるが actor request の一部が失敗。完全な census ではない |
| `X 設計外` | そのソースの query を設計していない（収集対象外） |

Google Trends（登録 63 トピック、単独系列）:

| 範囲 | トピック数 | 5年 | 12ヶ月 |
|---|---:|---:|---:|
| 既存 15 化合物 | 15 | 15/15 | 14/15（THC-O は NO_DATA） |
| 追加 15 語 | 15 | 14/15（NO_DATA 1） | 7/15（NO_DATA 8） |
| 追加 6 検索トピック（2026-11-11 登録） | 6 | 0/6（未収集） | 0/6（未収集） |
| 追加 27 検索トピック（2026-11-15 登録） | 27 | 0/27（未収集） | 0/27（未収集） |
| **登録 63 トピック** | **63** | **29/63** | **21/63** |

- **5年**: 29/63 adopted（既存 15/15、追加 14/15、6 検索トピック 0/6、2026-11-15 登録 27 語 0/27）。追加で未採用なのは CBGa（NO_DATA）のみ。10-OH-HHC・THXE・THCA の先行 HTTP 429 run は失敗証跡として quarantine に残り、後続の別 run が採用されている。旧 `…-5y-baseline` run は summary-only で、どの化合物の引用元でもない（§2.1.1・§2.1.2）。
- **12ヶ月**: 21/63 adopted（既存 14/15、追加 7/15、6 検索トピック 0/6、2026-11-15 登録 27 語 0/27）。既存の THC-O と追加 8 語（CBDV・THCB・THCJD・THCPO・HHCPO・CBGa・10-OH-HHC・THXE）は最新試行が NO_DATA。CBDV・THCJD・THXE の先行 HTTP 429 run も失敗証跡として保持する。THCV・CRDH は 53 週中 1 週だけ非ゼロ（§2.1.3）。CRDH の旧 summary の記録値は raw から再現できないため引用しない。
- **12ヶ月 21/63 の分子は既存の被覆記録を引き継ぐ（既知の限界）**: 古い run には `query_id` / 観測窓 ID を持たない記録があり、この checkout の `metadata/data-catalog.json` だけでは 12ヶ月 adopted 21 語を独立に再構成できない。21/63 は本変更で新たに照合した数ではなく、**既存の集計値**である。推測で件数を補正せず、run-level の事実は catalog・採用宣言・§2.1.3 を正本とする。
- 初回の追加収集では 13 語バッチが 14/26 採用（5年 9/13・12ヶ月 5/13）、CBC・CBDV が 4 run 中 3 採用だった。失敗窓 13 件を各 1 回再取得し、10-OH-HHC・THXE の 5年と THCA の 12ヶ月・5年の計 4 系列を追加採用した。残る 9 試行は NO_DATA として quarantine に保持し、先行失敗 run も保持する。

YouTube（liquid-only primary）:

- required primary は `product_liquid` の全 query **64 本**（2026-11-11 に 6 本、2026-11-15 に 27 本追加）。**30 本に adopted run があり、31 primary run / 29 化合物**を被覆する（CBD のみ 2 run、THCNM のみ 2 query で 2 run）。
- **未被覆は `thca-liquid-ja` の `NO_VIDEOS` 1 本と 6 検索トピックの 6 本、2026-11-15 登録 27 語の 27 本（計 34 本）**。CBE 331（3/354 失敗）・CBL 269（5/296 失敗）は **partial**。裸の `HHC` 1 run は保持するが primary 外で、どの化合物の被覆も完成させない。
- **被覆はクエリ単位と化合物単位の両方**で報告する。化合物は自身の required primary query が全部揃って初めて完了し、`make audit-youtube-coverage` は primary runs=31、compounds=29/63、queries=30/64、partial_compounds=0、missing_compounds=34（`compound_thca`、6 検索トピック、2026-11-15 登録 27 語）、retained_out_of_scope=1、violations=0 を報告する。THCNM は `primary coverage 2/2`。ここでの `partial_compounds=0` は**クエリ被覆**の状態で、CBE・CBL の payload partial とは別の軸である。
- catalog / declaration 上の adopted run は 32（primary 31 + retained 1）。raw は Git 非追跡・公開対象外（「YouTube の収集と追跡」）。

X (Twitter):

- X の query は 7 化合物（CBD・THC・CBG・HHC・THCV・THC-O・THCH）だけを設計しており、残る 56 トピックは `X 設計外`。CBC・CBDV・追加 13 語・6 検索トピック・2026-11-15 登録 27 語のクエリは設計していない。X の規制前後比較は [`datasets/cannabinoid-social-trends/`](../cannabinoid-social-trends/) が別研究として収集している。

### 収集したキーワード

収集語は canonical の 3 種類（化合物語・製品語・アンカー語）と、その登録済み表記ゆれ（variant）からなる。各語は下表のどこかに 1 回だけ現れる。

| 種別 | 語 |
|---|---|
| 化合物語・検索トピック語（登録 63） | CBX, CBD, THC, CBG, HHC, THCV, THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH, THCNM, CBC, CBDV, THCB, THCP, THCJD, THCPO, CBE, HHCPO, CBND, CBL, CBGa, CBP, 10-OH-HHC, THXE, THCA, Δ9-THCA-A, THCA-B, Δ8-THCA, Δ8-THCB, Δ9-THCB, THCB-O-acetate, Δ8-THCP, Δ9-THCP, Δ8-THCJD, Δ9-THCJD, Δ8-THCP-O-acetate, Δ9-THCP-O-acetate, Δ8-THCB-O-acetate, Δ9-THCB-O-acetate, Δ8-THC, Δ6a(10a)-THC, Δ6a(7)-THC, Δ7-THC, Δ10-THC, Δ9(11)-THC, Δ9-THCV, Δ8-THCV, THCJD-O-acetate, Δ8-THCH, Δ9-THCH, 9(R)-HHC, 9(S)-HHC, (6aS,9S,10aS)-HHC, (6aS,9R,10aS)-HHC, (6aS,9S,10aR)-HHC, (6aS,9R,10aR)-HHC, (6aR,9S,10aS)-HHC, (6aR,9R,10aS)-HHC。採用状況は「登録済みキーワードと収集状態」を参照 |
| 製品語 — リキッド（登録 63 トピック / required primary 64 本） | 登録は全 63 トピックの `<term> リキッド` と、THCNM の 2 表記（`THCNM リキッド` = `thcnm-liquid-ja`、`THA リキッド` = `tha-liquid-ja`）。Google Trends で照会したのは既存 13 語（`CBD リキッド` 〜 `THCV リキッド`、`THC-O リキッド` を含む）で、**2026-11-11 登録の 6 検索トピックの liquid 6 本と 2026-11-15 登録 27 語の 27 本は未照会**。YouTube の adopted と未被覆の内訳は「収集被覆」 |
| 製品語 — オイル（2） | CBD オイル, THC オイル |
| 製品語・比較アンカー | CBX リキッド（CBX 化合物語とは別観測。Google Trends の比較セットにも登場し、YouTube では primary の 1 run） |
| 表記ゆれ（variant） | `THCO`（`thc-o-general-ja` の variant）、`THCO リキッド`（`thc-o-liquid-ja` の variant）。canonical の別表記であり、化合物語・製品語の数を増やさない。`THCO` は tetrahydrocannabiorcol（Δ8-/Δ9-THCO）にも使われる別物質の表記であり、単一物質の名称ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)） |

| プラットフォーム | 収集時点 | 化合物語 | 製品語 | 測定モード |
|---|---|---|---|---|
| Google Trends | 既存 15 語: 2026-10-02 〜 11-04 / 追加 15 語・再取得: 2026-11-10 UTC | 既存 15 語 + 追加 15 語（合計 21 語が 12ヶ月 adopted。登録 63 トピックのうち 6 検索トピックと 2026-11-15 登録の 27 語は未収集） | 既存リキッド 13 語（8 語が系列、5 語は NO_DATA） | 12ヶ月・単独系列 |
| Google Trends | 既存 15 語: 2026-10-02 〜 11-04 / 追加 15 語・再取得: 2026-11-10 UTC | 既存 15 語 + 追加 15 語（合計 29 語が 5年 adopted。登録 63 トピックのうち 6 検索トピックと 2026-11-15 登録の 27 語は未収集） | 既存リキッド 13 語中 12 語が系列（main5 の 5 語 + 別窓の新規 7 語）。THC-O は系列なし | 5年・単独系列 |
| Google Trends | 2026-10-02, 10-05, 10-08, 10-12 | 12ヶ月の語の部分集合 | リキッド（phase-a/b）+ `CBX リキッド` | 比較セット / 共通スケール（12ヶ月） |
| Google Trends | 2026-10-23, 11-04 | 既存 13 語（アンカー CBD/THC を含む 4 セット）+ THCNM の anchored run | なし | 5年の共通スケール（`compare_terms`） |
| Google Trends | 2026-11-04 | CBX + アンカー CBD/THC の 3 語 | なし | CBX bridge の共通スケール（12ヶ月・5年、`compare_terms`。§2.1.6） |
| X (Twitter) | 2026-10-02, 10-08 | CBD, THC, CBG, HHC, THCV, THC-O, THCH（7 語） | なし | 単一クエリ（`{keyword} since:2026-09-01 until:2026-10-01`）。CBD は追加 3 run（条件未記録） |
| YouTube | 既存 15 化合物: 2026-10-10 〜 11-04 / 追加 14 クエリ: 2026-11-10 | 裸の `HHC` 1 run（保持・primary 外） | リキッド **29 化合物 / 31 primary run**（required query 30/64。`thca-liquid-ja` の `NO_VIDEOS`、6 検索トピックの 6 本、2026-11-15 登録の 27 本が未被覆） | 1 run 1 クエリ。**date filter なし・geo filter なし**、`maxResults` 500、Shorts/streams 0。日本語「リキッド」語による近似的な市場限定 |

- **登録集合は 63 トピック**。2026-11-11 に登録した 6 検索トピック（`Δ9-THCA-A`, `THCA-B`, `Δ8-THCA`, `Δ8-THCB`, `Δ9-THCB`, `THCB-O-acetate`）と 2026-11-15 に登録した 27 形式は登録のみで adopted run を持たない。Google Trends の 12ヶ月 NO_DATA の内訳は「収集被覆」。
- **表記ゆれ（2026-11-04）**: THC-O の `THCO` と `THCO リキッド` を `query-variants.json` に登録し、canonical の `query_id` のまま別 run として 12ヶ月・5年を収集した（Google Trends、geo JP）。canonical の `THC-O`（12ヶ月 no data・5年系列）と `THC-O リキッド`（no data）を置換・統合しない。run 一覧は [methodology.md](methodology.md) §2.1.5。
  - **`THCO` 表記で別系列がある**: 12ヶ月 53 週・非ゼロ 3（`20261104T135330Z-google-trends-thc-o-general-thco-12m`）、5年 262 週・非ゼロ 90（`20261104T135339Z-google-trends-thc-o-general-thco-5y`）。`THCO リキッド`は12ヶ月53週・非ゼロ1、5年262週・非ゼロ23。
  - canonicalの「12ヶ月 no data」は維持する。variantで系列が返ることはcanonicalのno dataを否定・置換しない。canonicalとvariantの値は合算しない。
  - `THCO`はPubMed/PubChem等で`THC-O-acetate`の略記として使われる一方、Δ8-THCO/Δ9-THCO（tetrahydrocannabiorcol）という別物質にも使われる。variantは検索文字列の対応であり、単一CAS・構造の同定ではない（[`ISS-20261104-TAX-029`](../../docs/issues/active/50-taxonomy-standards/20261104_p2_thco-query-variant-identity.md)）。
- **THCNM は 2026-11-04 に Google Trends の 12ヶ月・5年を収集した**（GT の 2 run: `20261104T115425Z-google-trends-thcnm-12m` / `20261104T115431Z-google-trends-thcnm-5y`）。同じ日に YouTube の 2 表記（`thcnm-liquid-ja` = `THCNM リキッド`、`tha-liquid-ja` = `THA リキッド`）も各 1 run で採用した。THA は同じ化合物の別名・商業名であり、別の収集語・別物質ではない（2 run は別観測で、件数を合算しない）。
- **CBX の Google Trends 系列**: 単独系列は 5年 `20261015T042857Z-google-trends-boundary-5y`（2021-10-10 〜 2026-10-11、262 週）と 12ヶ月 `20261015T042853Z-google-trends-boundary-12m`（2025-10-12 〜 2026-10-11、53 週）、加えて 1m・3m の boundary probe と 2026-10-01 の legacy 4 run。**run id と payload は 2026-11-04 の所有移管の前後で同一**で、観測のやり直しではない（[methodology.md](methodology.md) §2.1.6）。YouTube の CBX はこの study の own raw で、`CBX リキッド` は CBX 化合物語の系列とは別観測である。
- **製品語のリキッドは Google Trends と YouTube で使う**。YouTube の primary は liquid-only で、未被覆と partial の内訳は「収集被覆」。裸の `HHC` 1 run は保持するが primary 外で、対の必須 run でもない。
  Google Trends の比較セットは単独系列とは別の共通スケール値であり、混ぜない。
- **5年のリキッドは 13 語中 12 語が系列**（`20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の 5 語 + 新規 8 run のうち 7 語）。
  新規 8 run は main5 と窓が異なる別観測であり（main5 は 2021-10-10 〜 2026-10-11、新規は 2021-10-17 〜 2026-10-18）、単独系列の値をまたいで比較しない。
  THC-O リキッドは 5年でも系列なし（`NO_DATA`）。12ヶ月が no data でも 5年は取れることがある（HHC リキッドがその例）。
- **12ヶ月のリキッドは 13 語照会して 8 語が系列、5 語（HHC / CRDH / CRDP / THC-O / THCV リキッド）は no data**。
- **X は化合物語だけ**（製品語なし）。

### YouTube の収集と追跡

クエリ設計は [methodology.md](methodology.md) §2.3 と [`metadata/query-design.json`](metadata/query-design.json) が正本。**query-design は必須 primary query と被覆ルールを定め、現在の adopted 状態は `make audit-youtube-coverage` と catalog が報告する。** **primary は liquid-only**: `<compound> リキッド`（`product_liquid`）。required primary query 64 本のうち 30 本に adopted run があり、未被覆は `thca-liquid-ja` の `NO_VIDEOS` 1 本と 6 検索トピックの 6 本、2026-11-15 登録 27 形式の 27 本（計 34 本、内訳は「収集被覆」）。裸の `HHC` 1 run は raw / catalog に保持するが **primary coverage 外**であり、HHC の liquid run と対にする必須 run ではない。

いずれも `data/raw/youtube/<run-id>/` に置き、raw は非追跡かつ公開対象外（公開承認なし）。raw は machine-local のため、clone によっては下表のリンク先が存在しない（catalog / declaration は committed、payload は手元の証跡）。**追加 14 run（CBC・CBDV + 追加 12 クエリ）の raw は一次 checkout にあり、歴史的 18 run の payload は Git 非追跡のため clone には含まれない**。payload の有無は被覆判定に影響しない。

| 区分 | 検索語 | `date_filter` | 件数 | 観測窓（UTC、`end_exclusive`） | run |
|---|---|---|---:|---|---|
| primary | `10-OH-HHC リキッド` | `all` | 172 | 2006-02-14 〜 2026-10-06 | [`20261110T200043Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T200043Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBC リキッド` | `all` | 358 | 2007-07-19 〜 2026-11-11 | [`20261110T170316Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T170316Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBD リキッド` | `all` | 456 | 2014-11-17 〜 2026-10-10 | [`20261010T144422Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T144422Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBD リキッド` | `year` | 393 | 2025-10-11 〜 2026-10-10 | [`20261011T191902Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261011T191902Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBDV リキッド` | `all` | 112 | 2016-02-14 〜 2026-11-05 | [`20261110T171742Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T171742Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBE リキッド` | `all` | 331（partial: 3/354 失敗） | 2009-01-05 〜 2026-11-11 | [`20261110T192628Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192628Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBG リキッド` | `all` | 219 | 2017-05-17 〜 2026-10-18 | [`20261101T111408Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111408Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBGa リキッド` | `all` | 89 | 2013-03-04 〜 2026-10-26 | [`20261110T194826Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T194826Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBL リキッド` | `all` | 269（partial: 5/296 失敗） | 2009-06-16 〜 2026-11-09 | [`20261110T193806Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193806Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBN リキッド` | `all` | 468 | 2008-08-01 〜 2026-09-24 | [`20261010T145729Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T145729Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBND リキッド` | `all` | 9 | 2008-03-03 〜 2025-11-19 | [`20261110T193743Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193743Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBP リキッド` | `all` | 384 | 2010-06-03 〜 2026-10-18 | [`20261110T195055Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T195055Z-youtube-cannabinoid-raw-collection/) |
| primary | `CBX リキッド` | `all` | 329 | 2010-03-19 〜 2026-10-28 | [`20261101T112555Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112555Z-youtube-cannabinoid-raw-collection/) |
| primary | `CRDH リキッド` | `all` | 352 | 2022-09-29 〜 2026-09-12 | [`20261010T164917Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T164917Z-youtube-cannabinoid-raw-collection/) |
| primary | `CRDP リキッド` | `all` | 433 | 2016-06-18 〜 2026-10-18 | [`20261101T111429Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111429Z-youtube-cannabinoid-raw-collection/) |
| primary | `H4CBH リキッド` | `all` | 395 | 2020-10-01 〜 2026-10-02 | [`20261010T143430Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T143430Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHBD リキッド` | `all` | 224 | 2020-09-30 〜 2026-10-06 | [`20261010T141947Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261010T141947Z-youtube-cannabinoid-raw-collection/) |
| **retained / out-of-scope** | `HHC`（裸語） | `all` | 482 | 2006-09-05 〜 2026-11-02 | [`20261101T085920Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T085920Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHC リキッド` | `all` | 412 | 2013-06-25 〜 2026-09-20 | [`20261101T091646Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T091646Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHCH リキッド` | `all` | 138 | 2012-04-09 〜 2026-10-18 | [`20261101T105037Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T105037Z-youtube-cannabinoid-raw-collection/) |
| primary | `HHCPO リキッド` | `all` | 38 | 2017-04-28 〜 2026-09-20 | [`20261110T193648Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T193648Z-youtube-cannabinoid-raw-collection/) |
| primary | `THA リキッド` | `all` | 311 | 2012-01-17 〜 2026-11-05 | [`20261104T120805Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261104T120805Z-youtube-cannabinoid-raw-collection/) |
| primary | `THC リキッド` | `all` | 435 | 2009-05-01 〜 2026-10-30 | [`20261101T111450Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T111450Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCB リキッド` | `all` | 209 | 2006-10-12 〜 2026-10-13 | [`20261110T191309Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T191309Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCH リキッド` | `all` | 240 | 2011-06-07 〜 2026-09-15 | [`20261101T105058Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T105058Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCJD リキッド` | `all` | 55 | 2018-04-24 〜 2026-03-12 | [`20261110T192423Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192423Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCNM リキッド` | `all` | 30 | 2017-11-30 〜 2026-11-03 | [`20261104T120627Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261104T120627Z-youtube-cannabinoid-raw-collection/) |
| primary | `THC-O リキッド` | `all` | 388 | 2015-10-30 〜 2026-11-01 | [`20261101T112513Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112513Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCP リキッド` | `all` | 419 | 2021-02-13 〜 2026-10-29 | [`20261110T191712Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T191712Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCPO リキッド` | `all` | 33 | 2017-05-09 〜 2026-09-15 | [`20261110T192549Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T192549Z-youtube-cannabinoid-raw-collection/) |
| primary | `THCV リキッド` | `all` | 435 | 2011-08-15 〜 2026-10-15 | [`20261101T112534Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261101T112534Z-youtube-cannabinoid-raw-collection/) |
| primary | `THXE リキッド` | `all` | 326 | 2021-09-04 〜 2026-10-18 | [`20261110T200518Z-youtube-cannabinoid-raw-collection`](data/raw/youtube/20261110T200518Z-youtube-cannabinoid-raw-collection/) |

- **request と観測窓は別物**。Actor 入力に `dateFilter` を渡していない run は、絶対日付窓もローリング窓も持たない。表の窓は payload の動画公開日を UTC の半開区間 `[start, end_exclusive)` に正規化した**観測**であり、検索条件ではない。request の事実は `collection_request`（`date_filter` / `reference_time` / actor input）に、観測窓は `window` に記録する（[methodology.md](methodology.md) §2.3）。
- CBD リキッドの 2 run は観測窓と `date_filter` が異なる別観測。統合せず、run をまたいで件数を合算しない。
- `HHC`（裸語）は保持するが primary 外。`HHC リキッド` の有無を補うための run ではなく、liquid coverage を完成させない。件数も primary に加算しない。
- 件数は検索結果として返された動画の標本数で、YouTube 全体の投稿数ではない。
- 2026-11-01 の liquid 8 クエリ一括実行は、最初の試行で 2 クエリ（HHCH・THCH）だけが完走し、残り 6 クエリは Apify アカウントの請求サイクル上限で中断した。上限引き上げ後の再実行（同日 11:14〜11:33Z、3 run ずつ）では 6 クエリすべてが SUCCEEDED になり、CBG・CRDP・THC・THC-O・THCV の 5 run を採用した。CBX はその時点では採用先未決だったが、同じ 2026-11-01 の owner 決定（YouTube はこの study が所有）を受けて、完全 payload を採用した。CBX の Google Trends raw は 2026-11-04 にこの study へ移管済みで、`cbx-search-trends` 側に残るのは Google Search Console raw だけである。中断時の部分 payload は raw に採用していない（[ISS-20261101-YT-019](../../docs/issues/active/30-production-collection-expansion/20261101_p2_youtube-liquid-batch-usage-cap.md)）。
- 2026-11-04 の THCNM 2 run（`THCNM リキッド` / `THA リキッド`）は同じ入力を用いる**別 run** として 1 回ずつ実行し、両方 SUCCEEDED（status は actor run status object による）。
  1 run 1 クエリ、`maxResults` 500・`maxResultsShorts` 0・`maxResultStreams` 0、`dateFilter` なし。件数は 30 と 311 で、
  **片方が他方の代替でも合算対象でもない**（`THA` は同じ化合物の別名・商業名であり、2 run は 2 つの検索文字列を測る）。
  採用宣言は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)。
  payload は Git 非追跡（`git_untracked`）で、宣言・catalog・run metadata が committed 側の証跡、payload はこの checkout のローカル証跡。
- **2026-11-10 の追加 14 run** はすべて 1 run 1 クエリで、`maxResults` 500・`maxResultsShorts` 0・`maxResultStreams` 0、`dateFilter` なし、geo filter なし、`CBC リキッド`〜`THXE リキッド` の登録済み liquid クエリを送った。**CBE は 331 件（3/354 actor requests 失敗）、CBL は 269 件（5/296 失敗）で partial** であり、完全な census ではない。**THCA は actor status が SUCCEEDED でも `NO_VIDEOS` で動画行が 0**、絶対窓を no-date/no-video payload から導けないため現行 declaration contract では採用しない（`thca-liquid-ja` は adopted run 0）。これは世界全体の 0 でも、採用済み primary query でもない。
- 採用宣言: HHBD は [`20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261010-youtube-hhbd-liquid-cannabinoid-raw-collection.json)、リキッド 5 run は [`20261015-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261015-youtube-liquid-batch-cannabinoid-raw-collection.json)、HHC 2 run は [`20261101-youtube-hhc-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-cannabinoid-raw-collection.json) / [`20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-hhc-liquid-cannabinoid-raw-collection.json)、2026-11-01 の HHCH・THCH 2 run は [`20261101-youtube-liquid-batch-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch-cannabinoid-raw-collection.json)、再実行の CBG・CRDP・THC・THC-O・THCV 5 run は [`20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-liquid-batch2-cannabinoid-raw-collection.json)、CBX は [`20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261101-youtube-cbx-liquid-cannabinoid-raw-collection.json)、THCNM 2 run は [`20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261104-youtube-thcnm-tha-liquid-cannabinoid-raw-collection.json)、追加 14 run は [`20261110-youtube-cbc-cbdv-cannabinoid-raw-collection.json`](../../metadata/provenance/declarations/20261110-youtube-cbc-cbdv-cannabinoid-raw-collection.json) と `20261110-youtube-<query>-cannabinoid-raw-collection.json` 12 本（いずれも `staging-declaration-v1`、L1 を経て catalog）。
- HHC 2 run の request 語彙・actor build・実行状態の訂正は [`20261101-youtube-hhc-request-parameters.json`](../../metadata/provenance/corrections/20261101-youtube-hhc-request-parameters.json) に記録する。元の宣言は handover hash を保つため書き換えず、訂正版 declaration を併置する。
- `maxResults` が現行 Actor の正規名。旧宣言の `max_videos` は歴史的記録としてのみ読み、新規入力に使わない。
- **配布制限**: この study の YouTube raw は [`cannabinoid-platform-trends`](../cannabinoid-platform-trends/) の配布 slice（COL-033 の 6 run）には含まれない。HHC の raw はこの study に採用済みだが、配布物の `not_collected` は「配布 slice に無い」という意味であり、この study で未収集という意味ではない。THCNM はいずれの配布 slice にも入らない（COL-033 に YouTube run は無く、Google Trends 系列は配布物の公開化合物集合外）。追加 15 語と 2026-11-11 登録の 6 検索トピックも配布 slice の外である（[methodology.md](methodology.md) §5.1、[`metadata/query-design.json`](metadata/query-design.json) の `distribution`）。
- 月別の検索結果件数は [`data/processed/youtube_monthly_counts.csv`](data/processed/youtube_monthly_counts.csv)。この中間集計は HHBD リキッド run に固定され、当該 CSV の SHA-256 に限って公開承認済み（[審査記録](../../metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json)）。他の 31 run の集計はまだ作っていない。
- **raw の公開範囲**: 採用した YouTube raw（catalog / declaration 上 32 run）は Git 非追跡・machine-local の per-video データで、**公開承認されていない**。公開済みなのは上記 HHBD 月別集計だけであり、他の化合物の raw / 集計は未公開。
- 外部公開・リリースは実施していない。

## ステータス

| ステータス | 日付 |
|-----------|------|
| PLANNED | 2026-10-02 |
| ACTIVE | 2026-10-02 |
| COLLECTION_COMPLETE（既存 15 化合物の Google Trends） | 2026-11-04（既存 15 化合物は 5年 15/15・12ヶ月 14/15。追加と再取得後の登録 63 トピックは 5年 29/63・12ヶ月 21/63） |
| COMPLETED | — |

> **YouTube の liquid-only primary は、登録 63 トピックのうち 29 化合物・required query 30/64 を被覆。** primary は 31 run（CBD のみ 2 run、THCNM のみ 2 クエリで 2 run）で、欠けるのは `thca-liquid-ja` の `NO_VIDEOS` 1 本と 6 検索トピックの 6 本、2026-11-15 登録の 27 本である。CBE 331（3/354 失敗）と CBL 269（5/296 失敗）は partial であり、完全な census ではない。裸の `HHC` run は保持された primary 外証跡で、primary の内訳には数えない。`make audit-youtube-coverage` は **primary runs=31、compounds=29/63、queries=30/64、partial_compounds=0、missing_compounds=34（`compound_thca`、6 検索トピック、2026-11-15 登録 27 語）、retained_out_of_scope=1、violations=0** を報告する。`COLLECTION_COMPLETE` は既存 15 化合物の Google Trends 収集が揃った状態を指し、**登録 63 トピック全体は 5年 29/63・12ヶ月 21/63**。X は CBD・THC・CBG・HHC・THCV・THC-O・THCH の 7 化合物に限られ、全体の COMPLETED は未宣言。

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
  [`ISS-20261111-TAX-040`](../../docs/issues/active/50-taxonomy-standards/20261111_p1_compound-registration-state-batch.md)（2026-11-11 の 13 語の登録、管理カテゴリ、THCP の非登録判断の置換）、
  [`ISS-20261111-TAX-041`](../../docs/issues/active/50-taxonomy-standards/20261111_p2_thca-thcb-subtopic-registration.md)（THCA / THCB の個別検索トピック登録と総称概念の維持）、
  [`ISS-20261111-TAX-042`](../../docs/issues/active/50-taxonomy-standards/20261111_p3_isomer-family-evidence-review.md)（THCP / THCJD / THCPO / THCB-O-acetate の異性体別根拠レビューと family 登録の維持）、
  [`ISS-20261115-TAX-043`](../../docs/issues/active/50-taxonomy-standards/20261115_p0_compound-external-identifier-crosswalk.md)（外部識別子 crosswalk の P0 修正、THCV / CBDV の粒度判断）、
  [`ISS-20261115-TAX-044`](../../docs/issues/active/50-taxonomy-standards/20261115_p1_dictionary-form-precision.md)（辞書全体の形式精度の標準化・未登録候補形式のインベントリ）、
  [`ISS-20261115-TAX-045`](../../docs/issues/active/50-taxonomy-standards/20261115_p2_candidate-form-registration.md)（候補 27 形式の検索トピック登録・未収集の明示・既存 run 割当ての保持）
- 初回の計画書: `research/strategy/20261002-keyword-coverage-expansion.md`
- 配布物: [`datasets/cannabinoid-platform-trends/`](../cannabinoid-platform-trends/)、
  既存研究: [`datasets/cbx-search-trends/`](../cbx-search-trends/)（Google Search Console raw の正本。CBX の Google Trends raw は 2026-11-04 に本 study へ移管済み）, [`datasets/cbx-social-trends/`](../cbx-social-trends/)
- タクソノミー: `metadata/taxonomy/compound-taxonomy.skos.jsonld`、登録根拠と未修正の既知事項: [`docs/provenance/compound-taxonomy.md`](../../docs/provenance/compound-taxonomy.md)、クエリの正本: `metadata/queries/query-registry.json`
