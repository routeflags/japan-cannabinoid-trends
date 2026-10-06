# Research Chair Strategic Review — Data Collection Priorities

| 項目 | 内容 |
|------|------|
| **調査ID** | CHAIR-20261005-PRIORITIES |
| **レビュー日** | 2026-10-05 |
| **担当** | Cannabinoid Research Chair |
| **目的** | 次期データ収集の優先順位を科学的価値・エビデンスギャップ・引用可能性・実行可能性で判定する |
| **対象資源** | YouTube Data API (100 queries/day), Apify X (~$5/回), Google Trends (無料) |

---

## 0. 現状評価（Chair Assessment）

### 稼働中の研究資産

| 資産 | 状態 | 引用可能性 |
|------|------|:----------:|
| Google Trends 12化合物 (common-scale set A: CBD/THC/CBG/HHC/THCH) | 完了 | HIGH |
| Regulatory Status 12化合物 (primary sources) | 完了 | HIGH |
| Early Warning Index v1 (12 compounds, first-mention + persistence + emergence_score) | 完了 | **HIGHEST** |
| YouTube English CBD (3,831 records, 11% JP) | 部分的 (2023異常, 2025欠落) | LOW |
| YouTube CBX リキッド 12ヶ月 (125 records, 68% JP) | **最も分析可能** | MEDIUM |
| X: H4CBH n=40, HHBD n=40 | 検証不足 | MEDIUM |
| X: CBX Social (2,376+451) + Multi 316件 | 収集済み・分析未完了 | MEDIUM |
| DOI v1.8.0 (10.5281/zenodo.23101318) | 公開済み | — |
| Citation count | **0** (2026-10-02公開) | — |

### 重要度の高い未解決ギャップ

| # | ギャップ | 制約する研究質問 | リソースで埋められるか |
|---|---------|-----------------|:---------------------:|
| G1 | Google Trends common-scale が5/12化合物のみ | 「日本の検索需要でCBNはHHCとどう比較されるか」 | ✅ 無料・即時 |
| G2 | CBN 規制前後の対照データなし | 「指定薬物化はSNS言及をどう変えたか」 | ✅ Apify $2 で可 |
| G3 | H4CBH/HHBD n=40 のCI幅が过大 (39–69%) | 「半合成のSNS言及のうち宣伝はどれだけか」 | ✅ Apify $0.8 で可 |
| G4 | YouTube 日本語収集が全滅 (429) | 「日本語圏の動画コンテンツは新規化合物でどう推移するか」 | ⚠️ クォータ管理で可 |
| G5 | 単一コーダー、kappa 未測定 | 「SNS分類の信頼性は研究発表に耐えるか」 | ✅ 労働のみ・ゼロコスト |
| G6 | マルチプラットフォーム比較未実施 | 「検索・SNS・動画でエマージェンスは一致するか」 | ✅ 既存+新規データで可 |
| G7 | Early Warning Index の外部検証なし | 「index が実際の市場出現を予測したか」 | ⚠️ 時間が必要 |

**Chair 判定:** ギャップG1・G2・G3は「データを取るだけで埋まる」型であり、次回リソース配分の最優先対象。G4はクォータ管理次第で部分的に埋まる。G5は収集ではなく再コーディングであり、**本レビューの優先順位とは別枠で即実行すべき**。

---

## 1. リサーチ優先順位ランキング

スコア: 0–5 各次元（科学的重要性 / エビデンスギャップ / 実行可能性 / 引用可能性 / 公衆衛生関連性）。合計は意思決定支援であり、機械的合計ではない。

| Rank | 優先事項 | 科学 | ギャップ | 実行性 | 引用 | 衛生 | 合計 | Priority |
|:----:|----------|:----:|:------:|:------:|:----:|:----:|:----:|:--------:|
| 1 | Google Trends common-scale 拡張 (7化合物) | 4 | 5 | 5 | 5 | 4 | **23** | **HIGH** |
| 2 | CBN 自然実験 (規制前後 X + CBG対照) | 5 | 5 | 4 | 4 | 5 | **23** | **HIGH** |
| 3 | X 新興化合物拡張 (H4CBH/HHBD→n=200, CRDP n=100) | 4 | 4 | 5 | 4 | 4 | **21** | **HIGH** |
| 4 | YouTube 日本語コア (CBD オイル/カンナビノイド/CBN, 近3年) | 5 | 5 | 3 | 3 | 3 | **19** | **MEDIUM-HIGH** |
| 5 | YouTube 新興化合物 JP (HHC/CRDP/H4CBH/HHBD, 12ヶ月月次) | 4 | 4 | 3 | 3 | 4 | **18** | **MEDIUM** |
| 6 | インターコーダー再コーディング (n=40 × 2化合物) | 5 | 5 | 5 | 2 | 1 | **18** | **HIGH (分析)** |
| 7 | マルチ化合物 X 横断 (12化合物×n=100) | 3 | 3 | 4 | 3 | 2 | **15** | **LOW (defer)** |

### 判断理由

**Rank 1 (common-scale 拡張) が最優先である理由:**
- Early Warning Index は本プログラムの看板引用資産だが、共通スケール比較が set A の5化合物に限られており、「CBN vs CBN対HHC」「CRDP vs CBD」の引用文がまだ書けない。
- コストはゼロ。7つの比較クエリで引用文が一気に増える。
- 引用可能性が最も高い（OPP-001 の citation unit が common-scale に依存）。

**Rank 2 (CBN 自然実験) が同点で優先である理由:**
- CBN は 2026-06-01 に指定薬物化。本プログラム唯一の **natural experiment**。
- 規制の効果（SNS言及の増減）は薬政策研究者・ジャーナリストが実際に引用する問い。
- ギャップG2が明示的に特定済み。対照系列（CBG）で因果的過剰解釈を防ぐ設計が可能。

**Rank 6 が収集ではないが必須である理由:**
- 単一コーダーの分類比率（55%, 60%等）は kappa 未測定のままでは論文・報道で引用されない。
- 再コーディングは収集コストゼロ。第二コーダーがいれば kappa を算出し、比率の信頼性が変わる。
- **この作業を先に完了させないと、Rank 3 で拡張したデータも同じ方法論的弱点を引き継ぐ。**

**Rank 7 を defer する理由:**
- 12化合物×n=100 は $3 で収集可能だが、既存の 316件が偏ったまま横断比較を行うと「見かけの化合物間差」がサンプル量差を反映するリスクがある。
- 優先化合物を深く取ってから横断する方が、結果の解釈可能性が高い。

---

## 2. YouTube データ収集計画

### 2.1 キーワード優先順位

| Tier | キーワード | 理由 | クォータ目安 |
|------|-----------|------|:------------:|
| **T1** | HHC (JP) | 規制済み・比較対象として最重要 | 12 queries (月次12ヶ月) |
| **T1** | CRDP (JP) | 監視対象・規制候補 | 12 queries |
| **T1** | H4CBH (JP) | エマージェンス指数の主対象 | 12 queries |
| **T1** | HHBD (JP) | エマージェンス指数の主対象 | 12 queries |
| **T2** | CBD オイル (JP) | 日本語コア・基準系列 | 3–5 queries (近3–5年) |
| **T2** | カンナビノイド (JP) | 広義語・市場全体 | 3–5 queries |
| **T2** | CBN オイル (JP) | 規制前後の日本語動画有無 | 3–5 queries |
| **T3** | CBG (JP), THC (JP) | 基準系列（既存英語データで代替可） | 0–6 queries |
| **除外** | CBX リキッド | 既に12ヶ月分あり (125件, 68% JP) | 0 |

### 2.2 クォータ配分 (100 queries/day)

**Day 1 — 新興化合物 JP 月次スキャン (最重要)**

| 順番 | キーワード | 期間 | Queries | 目的 |
|:----:|-----------|------|:-------:|------|
| 1 | HHC | 2025-10 〜 2026-09 月次 | 12 | 規制後の日本語動画推移 |
| 2 | CRDP | 2025-10 〜 2026-09 月次 | 12 | 監視対象の動画有無 |
| 3 | H4CBH | 2025-04 〜 2026-09 月次 | 16 | 初出(2025-04)以降の動画出現 |
| 4 | HHBD | 2025-11 〜 2026-09 月次 | 11 | 初出(2025-11)以降の動画出現 |
| **小計** | | | **51** | |
| 残 | CBD オイル | 2024, 2025, 2026 各年 | 3 | 日本語コア基準 |
| 残 | カンナビノイド | 2024, 2025, 2026 各年 | 3 | 広義市場系列 |
| 残 | CBN オイル | 2024, 2025, 2026 各年 | 3 | 規制前後の日本語動画有無 |
| **Day 1 合計** | | | **60** | 40 バッファ |

**Day 2 — 深掘り (Day 1 の結果を見て判断)**

| 項目 | Queries | 条件 |
|------|:-------:|------|
| H4CBH/HHBD の 2024 年遡及 | 8 | Day 1 で動画が見つかった場合のみ |
| CBD オイル 2021–2023 遡及 | 3 | 長期系列が必要な場合 |
| カンナビノイド 2021–2023 遡及 | 3 | 同上 |
| CBN オイル 2021–2023 遡及 | 3 | 規制前長期系列 |
| **Day 2 上限** | **17** | |

### 2.3 期間選定の判断

| 期間 | 推奨 | 根拠 |
|------|:----:|------|
| 新興化合物: **12–18ヶ月月次** | ✅ | Google Trends の初出時期（H4CBH: 2025-04, HHBD: 2025-11）に合わせ、初出以降の動画出現を月次で追跡する。年次では「動画が0件か1件か」しか分からず意味が薄い。 |
| コア化合物: **直近3年年次** | ✅ | 日本語動画が2024以降でどれだけ存在するかが主な問い。10年遡及はクォータを消費し、2023の欠落（英語CBDで確認済み）を再現するリスクがある。 |
| 10年遡及 | ❌ | 英語CBD収集で2023=61件・2025=0件の欠落が発生。クォータ超過の主因。新規収集では避ける。 |

### 2.4 期待される成果

| 成果物 | 内容 | 引用文例 |
|--------|------|----------|
| 新興化合物 YouTube 月次系列 | HHC/CRDP/H4CBH/HHBD の JP 動画数月次推移 | "YouTube search results in Japanese for H4CBH increased from 0 videos in early 2025 to N videos per month by Q3 2026." |
| 日本語コア動画有無 | CBD オイル/カンナビノイド/CBN の JP 動画量 | "Japanese-language YouTube content for 'CBD oil' remained present across 2024–2026, while 'CBN oil' content was sparse." |
| マルチプラットフォーム比較表 | Google Trends × YouTube × X の出現タイミング比較 | "All three platforms showed increased activity for CBX liquid in July–September 2026." |

### 2.5 Chair Decision

- **Priority:** MEDIUM-HIGH (Rank 4) + MEDIUM (Rank 5)
- **Expected value:** 日本語動画コンテンツの空白を埋め、Early Warning Index に「動画層」を追加
- **Resource:** YouTube quota 60–77 queries / 2日、¥0
- **Feasibility:** 可 — ただしクォータ超過の再発を防ぐため **1日60クエリ上限・余白確保** を必須とする
- **Risk:** 再び429で全滅する可能性。**各クエリ完了後に `quota` を確認し、残り20で停止するルール** を課す

---

## 3. X/Twitter データ収集計画

### 3.1 化合物優先順位

| Rank | 化合物 | 現状 | 目標 n | 理由 | コスト |
|:----:|--------|------|:------:|------|:------:|
| 1 | **CBN** (規制前 2026-01〜05) | なし | 200 | 自然実自然実験の処置群前半 | $0.50 |
| 2 | **CBN** (規制後 2026-06〜10) | なし | 200 | 自然実験の処置群後半 | $0.50 |
| 3 | **CBG** (規制前 2026-01〜05) | なし | 100 | 対照系列前半 | $0.25 |
| 4 | **CBG** (規制後 2026-06〜10) | なし | 100 | 対照系列後半 | $0.25 |
| 5 | **H4CBH** (拡張) | n=40 | 200 | CI幅縮小・宣伝比率の安定推定 | $0.40 (追加160) |
| 6 | **HHBD** (拡張) | n=40 | 200 | 同上 | $0.40 (追加160) |
| 7 | **CRDP** (新規) | なし | 100 | 監視対象3化合物目 | $0.25 |
| 8 | HHC (規制後) | なし | 100 | 2022規制済み・比較可能性 | $0.25 |

### 3.2 サンプルサイズ設計

| 分析 | 必要 n の根拠 | 目標 n |
|------|--------------|:------:|
| 比率推定 (宣伝/レビュー/会話/その他) | Wilson CI が ±10% 以内に収まるには n≈100。n=40 では CI 幅 30 ポイント超 | **200** (CI±7%) |
| 規制前後の比率差検定 | 2群の比率差を検出するには各群 n≈100 が最低ライン | **各200** |
| コンテンツ分類の kappa 測定 | サンプル n=100 で kappa を安定推定 | **100–200** |

**breadth vs depth の判断:**
- **depth を優先**する。12化合物×n=50 は横断表を作るが、各化合物の CI が過大で引用文が書けない。
- 優先7化合物を n=100–200 に達成してから、残り化合物を n=50 で埋める方が引用価値が高い。

### 3.3 予算配分

| 項目 | 件数 | 単価 | コスト |
|------|:----:|:----:|:------:|
| CBN pre/post (各n=200) | 400 | $0.0025 | $1.00 |
| CBG control pre/post (各n=100) | 200 | $0.0025 | $0.50 |
| H4CBH 拡張 (追加160) | 160 | $0.0025 | $0.40 |
| HHBD 拡張 (追加160) | 160 | $0.0025 | $0.40 |
| CRDP (n=100) | 100 | $0.0025 | $0.25 |
| HHC 規制後 (n=100) | 100 | $0.0025 | $0.25 |
| **合計** | **1,120** | | **$2.80** |

### 3.4 収集パラメータ（研究計画書準拠）

```
Actor:  cPYLH3QT9GyzKhB4S (patient_discovery/twitter-search)
query:  "<compound> since:<YYYY-MM-DD> until:<YYYY-MM-DD> lang:ja"
section: latest
maxPages: 8-10  (n=200 目安 → 8-10 pages × 20-25件)
```

**日付フィルタ規則:**
- CBN pre: `CBN since:2026-01-01 until:2026-06-01 lang:ja`
- CBN post: `CBN since:2026-06-01 until:2026-10-06 lang:ja`
- CBG control: 同期間で `CBG` に置換
- H4CBH/HHBD: `since:2026-07-01 until:2026-10-06 lang:ja`（既存40件と重複確認）

**注意:** `chargedEventCounts` を信用せず、必ず `records.json` の件数を確認する（apify-x-search スキルの教訓）。

### 3.5 期待される成果

| 成果物 | 内容 | 引用文例 |
|--------|------|----------|
| CBN 自然実験レポート | 規制前後の日本語X言及比率・内容分類比較、CBG対照 | "Japanese-language X posts mentioning CBN decreased/increased from X% to Y% after the June 2026 designation, while CBG mention classification remained stable (CBG as control)." |
| 半合成 SNS 検証 | H4CBH/HHBD n=200 での宣伝比率・CI付き推定 | "In a sample of 200 Japanese X posts mentioning H4CBH (Jul–Sep 2026), 55% (95% CI 48–62%) were classified as product promotion." |
| 監視対象3化合物横断 | H4CBH / HHBD / CRDP の n=100+ 比較 | "Among unregulated monitoring compounds, H4CBH showed the highest Japanese X post volume in Q3 2026." |

### 3.6 Chair Decision

- **Priority:** HIGH (Rank 2 + Rank 3)
- **Expected value:** 本プログラム唯一の因果的推論可能な分析（CBN自然実験）を実現し、Early Warning Index に検証可能なSNS層を追加
- **Resource:** Apify $2.80、収集時間 約1時間（並列実行）
- **Feasibility:** 高 — actor 稼働実績あり、日付演算子対応確認済み
- **Risk:** X のシャドウバン・期間指定の非対称応答。**observed_zero と collection_failed を区別して記録**し、0件を「効果なし」と解釈しない

---

## 4. Google Trends 収集計画 (無料・即時)

### 4.1 common-scale 拡張

| # | 比較セット | キーワード | Queries | 目的 |
|:-:|-----------|-----------|:-------:|------|
| 1 | Set B | CBN, CRDP, HHCH, THC-O, H4CBH, HHBD, THCV (7語比較) | 1 | 共通スケールで新興7化合物を一括把握 |
| 2 | Set C | CBN vs CBG vs CBD（規制前後対照用） | 1 | CBN自然実験の検索側の系列 |
| 3 | Set D | H4CBH vs HHBD vs CRDP（監視対象3化合物） | 1 | 監視対象の相対検索需要 |
| 4 | 個別 | CBN 週次 (2026-01〜2026-10) | 1 | 自然実験の週次系列（既存12mを確認） |
| 5 | 個別 | CBG 週次 (2026-01〜2026-10) | 1 | 対照系列の週次系列 |
| **合計** | | | **5** | |

### 4.2 Chair Decision

- **Priority:** **HIGHEST** (Rank 1)
- **Expected value:** 引用文が「CBNはHHCの何倍」と書けるようになる。Early Warning Index の引用可能性が一段上がる
- **Resource:** Google Trends MCP、5クエリ、¥0
- **Feasibility:** 即時 — データパイプライン確立済み
- **Risk:** Google Trends の相対指数特性。**絶対検索数として扱わない**旨を引用文に必ず添える

---

## 5. 分析タスク（収集以外・即実行）

| タスク | 内容 | コスト | 優先 |
|--------|------|:------:|:----:|
| **インターコーダー再コーディング** | H4CBH n=40, HHBD n=40 を第二コーダーで再分類し Cohen's kappa を算出 | 労働のみ | **即** |
| **既存Xデータのマルチプラットフォーム比較** | CBX の Google Trends / X / YouTube 出現タイミング比較（既存データで可） | 分析のみ | 即 |
| **CBN 12m Trends の規制前後分解** | 既存 `20261002T082000Z-google-trends-cbn-5y` から 2026-06-01 前後の週次変化を記述 | 分析のみ | 即 |
| **Early Warning Index の引用文生成** | 12化合物分の citation unit を英語で書き出す（既存データ） | 分析のみ | 即 |

---

## 6. 新しく答えられる研究質問

### 新規データで回答可能になる質問

| ID | 研究質問 | 必要データ | 分析設計 |
|----|---------|-----------|---------|
| RQ-1 | 日本における指定薬物化 (2026-06-01) は CBN の SNS 言及量・内容をどう変化させたか？ | X CBN pre/post + CBG control | 前後比較 + 対照系列（非因果的言語を維持） |
| RQ-2 | Google Trends における CBN と HHC の相対検索需要は日本の規制タイムラインとどう整合するか？ | GT common-scale Set B | 規制日を重ねた記述的時系列 |
| RQ-3 | H4CBH/HHBD の SNS 言及のうち製品宣伝の比率は信頼区間付きでいくらか？ | X n=200 (拡張) + kappa | Wilson CI + kappa 付き分類 |
| RQ-4 | 新興半合成カンナビノイドの動画コンテンツは Google Trends の検索出現に追随するか？ | YouTube JP monthly (HHC/CRDP/H4CBH/HHBD) | プラットフォーム間の出現タイミング記述比較 |
| RQ-5 | 日本語圏の YouTube で「CBD オイル」と「CBN オイル」のコンテンツ量はどう異なるか？ | YouTube JP recent 3年 | 日本語コンテンツ量の記述比較 |
| RQ-6 | 監視対象3化合物 (H4CBH, HHBD, CRDP) の検索・SNS・動画での出現パターンは一貫するか？ | GT Set D + X + YouTube | 3プラットフォームの出現有無マトリクス |

### 回答しない質問（データが足りない／方法が不適切）

| 質問 | なぜ答えられないか |
|------|-------------------|
| 「規制は新規化合物の流入を防いだか」 | 因果推論に必要な対照群設計・サンプルが未整備。前後比較は関連として記述するにとどめる |
| 「CBX の市場シェアは何か」 | Google Trends は相対指数。シェアの定義に必要な絶対検索数・販売データがない |
| 「H4CBH の健康リスクは何か」 | 本データセットは行動・言及データであり、毒性・臨床データを含まない |
| 「どのブランドが人気か」 | COI により自社データは市場証拠にならない。OPP-002（透明性調査）が別途必要 |

---

## 7. リソース配分サマリー

| リソース | 配分 | 総コスト | タイムライン |
|----------|------|:--------:|:------------:|
| **Google Trends** | common-scale 3セット + 自然実験系列 2本 = 5クエリ | **¥0** | Day 0 (即時) |
| **YouTube quota** | Day 1: 60 queries / Day 2: ≤17 queries | **¥0** | Day 1–2 |
| **Apify X** | CBN pre/post + CBG control + H4CBH/HHBD拡張 + CRDP + HHC = 1,120件 | **$2.80** | Day 1–2 |
| **労働 (分析)** | kappa再コーディング、既存データ比較、引用文生成 | 人件費のみ | 今週 |
| **合計** | | **$2.80 + 労働** | |

### クォータ管理ルール（必須）

```
YouTube:
  - 1日あたり max 60 queries で計画（残40をバッファ）
  - 各クエリ後に quota を確認
  - 残り20で収集を停止し、翌日に再開
  - 429 エラーを検知したら即停止し、エラーファイルを raw/ に保持

Apify:
  - chargedEventCounts を信用しない
  - records.json の件数を正とする
  - maxPages は n 目標 ÷ 22 (1ページ約22件) + 1で逆算
  - 1クエリ実行後、件数を確認してから次に進む
```

---

## 8. 期待される研究価値

### この収集サイクルで得られる資産

| 資産 | 価値 | 引用文が書けるようになるか |
|------|------|:------------------------:|
| Google Trends common-scale 7化合物拡張 | Early Warning Index の比較可能性が上がる | ✅ |
| CBN 自然実験データセット | 薬政策・法規制研究への入口 | ✅ |
| X n=200 検証済み半合成データ | SNS分類の信頼性が上がる | ✅ |
| YouTube JP 新興化合物月次系列 | 動画層のエマージェンス追跡 | ✅ |
| kappa 検証済み分類 | 方法論的信頼性 | ✅ |

### 引用可能性への影響予測

| 現状 | このサイクル後 |
|------|---------------|
| 引用文: CBD vs THC vs CBG vs HHC vs THCH のみ | + CBN, CRDP, HHCH, THC-O, H4CBH, HHBD, THCV の共通スケール比較 |
| 引用文: 「CBX は2026年7月以降急増」(Google Trends のみ) | + YouTube・X でも同じ時期に急増した記述可能 |
| 引用文: 「H4CBH の投稿の55%が宣伝」(n=40, CI 39-69%) | + n=200, CI 約 ±7% で安定した推定 |
| 引用文: なし (CBN 規制効果) | + 「指定薬物化前後の日本語X言及比率」 |
| 引用文: なし (日本語YouTube動画) | + 新興化合物の日本語動画出現系列 |

### 引用確率の高い新しい citation unit 設計

| ID | Citation unit | Primary persona | 引用確率 |
|----|---------------|-----------------|:--------:|
| CU-1 | "In Japan, CBN Google Trends interest [rose/fell] in the weeks following its 2026-06-01 designation as a designated drug, while CBG (control) remained [stable]." | Journalist, Policy | 4/5 |
| CU-2 | "Common-scale Google Trends comparison (JP) shows CBD=47, THC=12, CBG=3, CBN=X, HHC=1, H4CBH=Y (relative, Oct 2026)." | Academic, Policy | 4/5 |
| CU-3 | "Among 200 Japanese X posts mentioning H4CBH (Jul–Sep 2026), X% were product promotion (95% CI: A–B); Cohen's kappa with second coder = C." | Academic | 3/5 |
| CU-4 | "YouTube search results in Japanese for H4CBH increased from 0 videos/month in early 2025 to N videos/month by Q3 2026." | Journalist, Policy | 3/5 |

---

## 9. リスクと限界

| リスク | 影響 | 軽減策 |
|--------|------|--------|
| YouTube 429 の再発 | 日本語データが再び欠落 | 60クエリ/日上限・残20で停止・エラーファイル保持 |
| X のシャドウバン・非対称応答 | 0件が「効果なし」に見える | observed_zero / collection_failed を区別・複数クエリで検証 |
| Google Trends の低ボリューム閾値 | H4CBH/HHBD が0のまま | 個別5年データで初出確認済み。共通スケールでも0の場合は「検出限界」と明記 |
| 多義語 (CBN = 人物名等) | ノイズ混入 | `lang:ja` + 内容分類で除外。YouTube は「CBN オイル」等の複合クエリ |
| COI 感知 | 引用を拒否される | 全成果物に利益相反開示・手法公開・限界明記を継続 |
| 自然実験の交絡 | 規制効果が過大解釈される | 対照系列 (CBG) を必ず併記。「関連」という言語を維持 |
| サンプル偏り (section=latest) | 新着に偏る | 期間指定クエリでカバレッジ確保。標本の非ランダム性を限界に明記 |
| 単一コーダー | 分類比率が引用不能 | kappa 再コーディングを **本サイクルで必須完了** |

---

## 10. Chair Decision

### 総合判定

**APPROVED WITH LIMITATIONS**

**理由:**
- リソース制約内で、最優先のエビデンスギャップ（G1・G2・G3）を埋めるデータ収集計画である
- Google Trends common-scale 拡張と CBN 自然実験は、引用文が明確に増える高価値投資である
- X 拡張は小コストで方法論的弱点（n=40, kappa 未測定）を直接是正する
- YouTube はクォータ制約下で再失敗リスクがあるため、日次上限とバッファを条件付きで承認

**制限条件:**
1. YouTube は1日60クエリ上限。429検知で即停止
2. X は records.json の件数を正とする。chargedEventCounts を使わない
3. CBN 自然実験の結果は「関連」として記述し、因果的表現を禁止
4. kappa 再コーディングが完了するまで、H4CBH/HHBD の比率は「暫定定値」として扱う
5. 全成果物に COI 開示・Google Trends 相対指数の限界を明記

### 即時実行タスク (今日)

| # | タスク | リソース | 完了条件 |
|:-:|--------|---------|---------|
| 1 | Google Trends common-scale 3セット取得 | GT MCP、5クエリ、¥0 | comparison_setB/C/D.json 保存 |
| 2 | CBN + CBG の規制前後 X 収集 (各 n=200/100) | Apify、$1.50 | records.json で件数確認済み |
| 3 | 既存 H4CBH/HHBD n=40 の第二コーダー再分類 | 労働、$0 | kappa 算出値をレポートに記録 |
| 4 | YouTube Day 1 計画の承認・クォータ確認 | — | 残クォータ確認記録 |

### 次回 Chair レビュー条件

| 条件 | 判定 |
|------|------|
| Google Trends common-scale 拡張が完了し、新 citation unit が最低3つ書ける | ✅ → Early Warning Index v2 更新へ |
| CBN 自然実験データが揃い、対照系列付きで記述レポートが書ける | ✅ → 薬政策向け research note へ |
| X kappa 測定値が得られ、n=200 の比率推定が CI 付きで提示できる | ✅ → SNS 検証セクション更新へ |
| YouTube JP 新興化合物で月次系列が得られる | ✅ → マルチプラットフォーム比較へ |

---

## 11. Research Backlog Update

```yaml
research_backlog:

  high_priority:

    - id: CHAIR-20261005-01
      topic: Google Trends common-scale 拡張 (Set B/C/D)
      status: approved
      resources: Google Trends MCP, ¥0
      deadline: immediate
      chair_note: |
        最高引用価値・ゼロコスト。Early Warning Index の比較可能性を直接向上させる。

    - id: CHAIR-20261005-02
      topic: CBN 自然実験 (規制前後 X + CBG対照)
      status: approved
      resources: Apify $1.50
      deadline: this week
      chair_note: |
        本プログラム唯一の因果的推論可能な問い。対照系列必須。因果言語禁止。

    - id: CHAIR-20261005-03
      topic: H4CBH/HHBD インターコーダー再コーディング (kappa)
      status: approved
      resources: 労働のみ
      deadline: this week
      chair_note: |
        収集ではなく分析タスクだが、他タスクの前提条件。完了まで比率は暫定扱い。

    - id: CHAIR-20261005-04
      topic: X 半合成拡張 (H4CBH/HHBD n=200, CRDP n=100, HHC n=100)
      status: approved
      resources: Apify $1.30
      deadline: this week
      chair_note: |
        kappa 完了後の実行を推奨。n=200 で CI±7%。

    - id: CHAIR-20261005-05
      topic: YouTube JP 新興化合物月次 (HHC/CRDP/H4CBH/HHBD)
      status: approved
      resources: YouTube quota 51 queries
      deadline: day 1
      chair_note: |
        クォータ60/日上限・残40バッファ。429検知で即停止。

  medium_priority:

    - id: CHAIR-20261005-06
      topic: YouTube JP コア化合物 (CBD オイル/カンナビノイド/CBN オイル)
      status: approved
      resources: YouTube quota 9 queries (day 1残)
      deadline: day 1-2

    - id: CHAIR-20261005-07
      topic: マルチプラットフォーム比較 (CBX: GT × X × YouTube)
      status: planned
      resources: 既存データ分析のみ
      note: 既存データで即実行可能

    - id: CHAIR-20261005-08
      topic: Early Warning Index v2 (common-scale + SNS検証層)
      status: planned
      depends_on: [CHAIR-20261005-01, CHAIR-20261005-02, CHAIR-20261005-03]

  monitoring:

    - id: CHAIR-20261005-09
      topic: マルチ化合物 X 横断 (12化合物×n=100)
      status: deferred
      reason: 優先化合物の深掘り完了後に実施。横断の前に CI 幅を縮小すべき。
      cost_if_activated: ~$3.00

    - id: CHAIR-20261005-10
      topic: Early Warning Index 外部検証
      status: monitoring
      reason: 時間依存。v2 リリース後の外部反応を待つ。

  completed: []

next_research:

  priority_1:
    question: CBN 指定薬物化前後の日本語X言及はCBG対照と比較してどう変化したか？
    reason: 本プログラムの因果的推論可能性を実証する最初のケース
    expected_value: 薬政策研究者への引用単位が生まれる

  priority_2:
    question: 日本のGoogle Trendsで新興7化合物を共通スケールで比較するとどう見えるか？
    reason: Early Warning Index の引用可能性を直接高める
    expected_value: citation unit が一気に増える

  priority_3:
    question: 新興化合物の日本語YouTube動画はGoogle Trendsの検索出現に追随するか？
    reason: マルチプラットフォーム早期警戒の検証
    expected_value: 「3プラットフォーム一致」という引用可能な発見
```

---

## 12. 次に何を研究すべきか (Chair の最重要問い)

1. **CBN 自然実験が完了したら、規制前後の SNS 内容差分（宣伝 vs 情報共有 vs 会話）を深掘りするか？**
   - 理由: 規制が「宣伝を減らした」のか「会話を減らした」のかで政策的含意が変わる
   - 期待価値: 薬政策研究で最も引用される構造になり得る

2. **Early Warning Index v2 で「検出 → SNS出現 → 動画出現 → 規制」のラグを定量化できるか？**
   - 理由: 現在は初出日と規制日の対応表のみ。プラットフォーム間のラグ指標があれば、早期警戒としての実用性が上がる
   - 期待価値: OPP-001 の核心価値を一段引き上げる

3. **YouTube JP コア系列が揃ったら、日本語圏と英語圏のコンテンツ量比を定量化できるか？**
   - 理由: 英語CBDデータ（11% JP）と日本語コアデータの比較は、国際研究者への独自性になる
   - 期待価値: 「Japanese YouTube cannabinoid content is X% of global English content for CBD queries」
   - 制約: 比較には同一クエリの英語・日本語収集が必要。クォータ計画に含める

---

*このレビューは CHAIR-20261005-PRIORITIES として research/ に記録される。次回データ収集サイクルの開始時に本ファイルを参照すること。*
