# データ取得・保存のギャップ分析とMECE整理

**作成日:** 2026-10-13
**目的:** 成分の市場トレンドと各メディアの相違を問う研究において、データ取得・保存のギャップが信頼性を損なわないよう、原因・現状・用語を整理する。
**対象:** Google Trends / X (Twitter) / YouTube の3ソース（本リポジトリの主要縦断データ）
**方針:** 本資料は診断と整理のみ。raw データの改変・削除は行わない。

---

## 0. 研究目的の確認

> 日本国内におけるカンナビノイド関連トレンドを、複数データソースから縦断的に追跡する。
> 成分ごとの市場トレンドと、各メディアの相違を問う。

この目的に必要なデータ条件は次の3点である。

| # | 条件 | 意味 |
|---|------|------|
| C1 | 成分軸の同一性 | 比較する成分の定義（クエリー表記）がメディア間で一致している |
| C2 | 期間軸の同一性 | 比較する期間窓（開始〜終了・粒度）がメディア間で一致している |
| C3 | 単位・来歴の明示 | 値の単位（相対指数／件数／動画数）と取得条件・欠測理由が記録されている |

ギャップとは、C1〜C3 のいずれかが満たされず、成分間・メディア間の比較が成立しない状態を指す。

---

## 1. なぜギャップが生まれるのか（原因7分類）

| # | 原因 | 内容 | 実例 |
|---|------|------|------|
| G1 | 収集ツールの複数化 | ソースごとに異なる Actor・MCP・API を時期ごとに追加し、旧手段を残したまま新手段を導入した | X: `cPYLH3QT9GyzKhB4S` → `rBaTEHzveTxZPraGv` → `qrmKEcWmE4WGXuuvd`。YouTube: `gJvjeCYNraSfhIaNd` → `h7sDV53CddomktSi5` ＋ v3（削除済み） |
| G2 | クエリー表記の不統一 | 英語名・日本語リキッド・オイル表記が混在し、同一成分でも別クエリーとして収集された | `CBD` vs `CBD リキッド` vs `CBD オイル`。X旧runには英語ノイズ混入実例あり（Durban CBD） |
| G3 | 期間指定方式の相違 | ソースごとに期間の指定方法と窓の意味が異なる | GT: `today 12-m`/`5-y`（収集日基準の相対窓）。X: `since:`/`until:` または `timeSince`/`timeUntil`（絶対日付）。YouTube: `dateFilter`（相対）／`publishedAfter`（絶対・廃止） |
| G4 | ファイル形式の不統一 | 同一ソース内でも時期により保存形式が異なる | GT: `records_{kw}.json`（フル時系列）vs `{compound}_5y_summary.json`（要約のみ）vs `records_{kw}-5y.json`（新規フル）。X: `records.json` vs `{compound}.json` vs `pre/post/control` 3分割。YouTube: `records.json` vs `records_raw.json` vs 年別ページ vs SQLite |
| G5 | 来歴記録の濃淡 | run_metadata の有無・項目が run ごとに異なる | 旧run: actor/query/section/max_pages のみ。新規GT run: anchor_terms/zero_status/purpose 付き。一部runは metadata 自体なし |
| G6 | Git追跡方針の差 | GT のみ追跡、他はローカル保持のため、第三者の検証可能性が異なる | 追跡101件は全てGT。X/YouTube/TikTok/IG/COA のrawは `.gitignore` で除外 |
| G7 | study 分割 | 同一成分のデータが複数 study に分散している | `cannabinoid-multi-trends`（成分横断）vs `cannabinoid-social-trends`（規制前後）vs `cbx-search-trends`（CBX製品軸） |

G1〜G5 は取得設計の問題、G6〜G7 は保存・公開設計の問題である。
いずれも「後から追加した手段・軸が、既存の手段・軸と整合していない」ことが根本原因である。

---

## 2. MECE整理表

### 表2-1. ソース × クエリー種別 × 期間窓（取得カバレッジ）

行＝成分、列＝ソース別のクエリー種別と期間。`●`=フル時系列あり、`△`=要約・部分のみ、`×`=なし、`?`=未検証。

**Google Trends（geo=JP）**

| 成分 | 英語名 12m | 英語名 5y | 日本語リキッド 12m | 日本語リキッド 5y | 比較セット |
|---|---|---|---|---|---|
| CBD | ● 53週全非ゼロ | △ summary 261点 | ● 53週（非ゼロ50） | ● 262週（非ゼロ257） | setA・setC・JA-1 |
| THC | ● 53週全非ゼロ | △ summary 261点 | ● 53週（非ゼロ2） | ● 262週（非ゼロ87） | setA・JA-1 |
| CBG | ● 53週全非ゼロ | △ summary 261点 | ● 53週（非ゼロ2） | ● 262週（非ゼロ4） | setA・setC・JA-1 |
| CBN | ● 53週全非ゼロ | △ summary形式 | ● 53週（非ゼロ5） | ● 262週（非ゼロ27） | setB・setC・JA-1 |
| HHC | ● 53週（非ゼロ32） | △ summary 261点 | × no-data | ● 262週（非ゼロ25） | setA・JA-2 |
| THCV | × | △ summary 261点 | × no-data | × | setB・JA-2 |
| THCH | ● 53週（非ゼロ3） | × | ● 53週（非ゼロ3） | × | JA-3 |
| THC-O | × | △ summary形式 | × no-data | × | setB・JA-2 |
| H4CBH | × | △ summary形式 | ● 53週（非ゼロ3） | × | setD・JA-3 |
| HHBD | × | △ summary形式 | ● 53週（非ゼロ2） | × | setD・JA-3 |
| HHCH | ● 53週（非ゼロ2） | △ summary形式 | ● 53週（非ゼロ1） | × | setB・JA-4 |
| CRDP | ● 53週（非ゼロ18） | △ summary形式 | × no-data | × | setB・setD・JA-4 |
| CRDH | △ summary形式 | △ summary形式 | × no-data | × | JA-4・CRDH比較 |
| CBX | —（別study） | — | ● 既存（別study） | — | JA-1〜JA-4アンカー |

**X (Twitter)**

| 成分 | snapshot系 | 期間指定系 | 規制前後系 | 言語フィルタ |
|---|---|---|---|---|
| CBD | ● 60件（2026-10-01） | △ 1m 60件・1y 0件・latest10 200件 | — | 旧runなし／新Actor `ja` 可 |
| THC | ● 60件 | — | — | 同上 |
| CBG | ● 40件 | — | 対照系列として使用 | 同上 |
| CBN | — | — | ● pre/post各100件＋CBG対照 | 同上 |
| HHC | ● 40件 | — | ● pre/post系 | 同上 |
| THCV/THC-O/THCH | ● 36〜40件 | — | THCH/THC-O pre/post系あり | 同上 |
| H4CBH/HHBD | ● 40件＋拡大200件 | — | — | 同上 |
| HHCH/CRDP/CRDH | ● 各種 | — | CRDH拡大あり | 同上 |

**YouTube**

| 成分 | snapshot系 | dated系 | 10年系列 | DB統合 |
|---|---|---|---|---|
| CBD | ● 22件 | ● 24・30件 | 対象外（旧10年系列は証拠・公開対象から除外） | ● 21run・1,319件 |
| THC | ● 25件 | ● 21件 | △ 2023年のみ50件 | × |
| CBG | ● 34件 | ● 21件 | △ 2017年のみ50件 | × |
| CBN | ● 24件＋50件 | ● 22件 | × 0件 | ● 468件1run |
| HHC | ● 28＋27件 | ● 23件 | × | × |
| THCV/THCH/THC-O | ● 20〜30件 | ● 22〜24件 | × | × |
| H4CBH/HHBD/CRDH | ● 21〜24件 | ● 20〜23件 | × | ● 各1run |
| HHCH/CRDP | ● 20・27件 | ● 30・21件 | × | ● 各1run（2026-10-11追加） |
| CBX | —（別study、12ヶ月月次あり） | — | — | — |

### 表2-2. ファイル形式マトリックス（保存方式）

| ソース | フル時系列 | 要約のみ | ページ分割 | DB統合 | 判定 |
|---|---|---|---|---|---|
| GT英語12m | `records_{kw}.json` | — | — | — | ✅ 統一 |
| GT英語5y | —（新規日本語のみ） | `{compound}_5y_summary.json` | — | — | ⚠️ 要約のみ・rawなし |
| GT日本語12m | `records_{slug}.json` | — | — | — | ✅ 統一（新規） |
| GT日本語5y | `records_{slug}-5y.json` | — | — | — | ✅ 統一（新規・主要5語） |
| GT比較 | `comparison_*.json` | summary内包あり | — | — | ⚠️ 形式混在 |
| X snapshot | `records.json` | — | — | `posts`（一部） | △ 形式2種 |
| X pre/post | `{compound}_{pre,post}.json`＋対照 | — | — | — | △ 専用形式 |
| YT snapshot | `records.json`＋`records_raw.json` | — | — | `videos` | △ 2層＋DB |
| YT 10年 | — | — | 対象外（旧10年系列は除外） | — | 証拠・公開対象外 |

### 表2-3. 来歴記録マトリックス（run_metadata充実度）

| 時期 | 必須9項目 | anchor/zero_status | 判定 |
|---|---|---|---|
| GT旧run（〜10-08） | actor/query/相当のみ | なし | △ 最低限 |
| GT新規run（10-12〜） | 全9項目 | あり | ✅ 充実 |
| X旧run | actor/query/section/max_pages | なし | △ 最低限 |
| X新Actor run | 同上＋lang/search_type/cookies有無 | —（DB行のみ） | △ ファイル記録なし |
| YT旧run | actor/search_term/max_videos | なし | △ 最低限 |
| YT 10年run | 対象外 | — | 証拠・公開対象外（補完しない） |

必須9項目＝run_id・study_id・source・収集手段・collection_timestamp・queries・件数・purpose相当・エラー記録。

---

## 3. 用語定義（混乱しやすい順）

### 3.1 収集単位

| 用語 | 定義 | 例 |
|---|---|---|
| run | 1回の収集実行。クエリー×期間×手段の単位 | `20261002T063821Z-google-trends-cbd` |
| run-id | runの一意識別子。`YYYYMMDDTHHMMSSZ-<内容>` 形式 | 上記 |
| run_metadata.json | runの来歴記録ファイル。クエリー・期間・手段・件数・状態を保持 | 各runディレクトリに1件 |
| checkpoint | 中断再開用の中間状態（Apify系）。完了前の一時保存 | `data/checkpoints/` |

### 3.2 保存ファイル

| 用語 | 定義 | 注意 |
|---|---|---|
| records.json | 取得そのままの時系列・件数リスト（フル） | GTは `{date,value}`、Xは投稿配列、YTは動画配列 |
| records_raw.json | フィルタ前の生レスポンス（YT snapshot系のみ） | `records.json` はここからの抽出・整形版 |
| summary（要約） | 集計値のみのファイル。時系列rawを含まない | GT英語5yの `{compound}_5y_summary.json`。再検証不可 |
| comparison_*.json | 複数語の同一スケール比較結果 | 値はセット内相対（最大語=100）。セット間比較不可 |
| 旧10年系列の取得ログ | 対象外の系列の記録（証拠・公開対象外のため来歴記録に使わない） | metadataの代替にしない |

### 3.3 期間窓

| 用語 | 定義 | 注意 |
|---|---|---|
| today 12-m | 収集日基準の直近約12ヶ月（週次53点） | 収集日が変わると窓がずれる。絶対期間ではない |
| today 5-y | 収集日基準の直近約5年（週次261〜262点） | 同上。初出判定は窓起点に依存する |
| since/until | X検索演算子の絶対日付指定 | Actorにより query内埋め込みか分離フィールドかが異なる |
| timeSince/timeUntil | 新X Actorの分離日付フィールド（`yyyy-mm-dd`） | 上記と同義。両方指定で閉区間 |
| dateFilter | YouTube Actorの相対期間（`all/month/year`等） | `month`=直近30日のローリング窓。暦月ではない |
| publishedAfter/Before | YouTube Data API v3の絶対日付（廃止済み） | 現行手段では使用不可 |
| snapshot | 時点取得。期間を区切らない全期間・関連度順の取得 | 時系列ではない。母集団の代表でもない |
| 期間系列 | 期間窓を区切った時系列取得 | 比較の基本単位 |
| 全期間 | `all` 窓・上限なしの取得 | 関連度・日付ソート＋上限打ち切りの影響を受ける |

### 3.4 値の単位

| 用語 | 定義 | 比較可否 |
|---|---|---|
| 相対指数（0-100） | GTの値。同一取得内の最大週=100に正規化 | 同一セット内のみ可。セット間はアンカー換算が必要 |
| 件数（投稿数・動画数） | X・YouTubeの取得件数 | 上限・関連度・言語条件が同一の場合のみ可 |
| アンカー語 | セット間換算の基準語（本計画では `CBX リキッド`＋`CBD リキッド`） | 全比較セットに含有させ換算係数を記録 |
| 共通スケール | 同一比較取得内のスケール | 上記と同義 |

### 3.5 欠測・ゼロの区別

| 用語 | 定義 | 扱い |
|---|---|---|
| observed_zero | 収集成功かつ対象範囲に0件と判断できる根拠あり | 0として集計可 |
| below_threshold | GTの閾値未満抑制（需要があっても0表示） | 0として集計不可。欠測として記録 |
| low_volume | 部分週0の断続需要 | 実測値として記録。解釈に注意 |
| unknown | 取得失敗・429・空レスポンス・条件不明 | 0として扱わない。再取得対象 |
| 欠落 | 期間内に取得自体がない（runなし） | unknown と同等。補完計画が必要 |

### 3.6 証拠レベル

| 用語 | 定義 | 置き場所 |
|---|---|---|
| observed（観測） | 収集データに直接 present な値 | raw |
| derived（派生） | raw から再現可能に計算された値 | interim/processed/analysis（手順付き） |
| interpretation（解釈） | 研究者の説明・仮説 | analysis（「所見」ラベル付き） |

### 3.7 品質概念

| 用語 | 定義 |
|---|---|
| 一貫性 | 同一クエリーの複数回取得の一致率（Jaccard等） |
| 冪等 | 再実行しても重複しない性質（`INSERT OR IGNORE` 等） |
| 非決定性 | 同一クエリーでも再実行結果が変わる性質（検索API共通）。再取得で記録する |
| 再現性 | 同じ手順で同じ結果を得られること。raw＋metadata＋手順の3点セットが必要 |
| 来歴（provenance） | 値がどこから来たかの追跡可能性（raw→処理→公開の鎖） |

---

## 4. 信頼性評価（研究目的に照らして）

### 4.1 メディア内比較（同一メディア内の成分比較）

| メディア | 判定 | 根拠 |
|---|---|---|
| GT英語名 | ⚠️ 条件付き可 | 同一12m窓・同一形式。ただしセット間比較はアンカー換算が必要で、旧セットにアンカーなし |
| GT日本語 | ✅ 可（新規13語） | 同一12m窓・同一形式・アンカー付きJA-1〜JA-4。no-data 4語は比較対象外として明示 |
| X | ⚠️ 条件付き可 | snapshot系は同一形式だが期間が単日中心。規制前後系は設計が異なるため別枠比較 |
| YouTube | ⚠️ 条件付き可 | snapshot＋datedは同一形式。旧10年系列は証拠・公開対象外。他成分の年次比較は不可 |

### 4.2 メディア間比較（同一成分のメディア差）

| 成分群 | 判定 | 根拠 |
|---|---|---|
| CBD | ✅ 可 | GT日英両系・X snapshot・YT snapshot＋dated・DB統合あり（旧10年系列は対象外） |
| 主要4成分（THC/CBG/CBN/HHC） | ⚠️ 条件付き可 | GT日英・X snapshot・YT snapshot＋datedあり。X時系列・YT年次系列なし |
| 新興5成分 | ⚠️ 条件付き可 | GT（英語summary＋日本語12m）・X snapshot・YT snapshot＋dated＋DB一部あり。時系列は2022年以降のみ |
| THCV/THC-O | ❌ 不可に近い | GT閾値以下・X snapshotのみ・YT snapshotのみ。量的に比較不能 |

### 4.3 信頼できない使い方（禁止リスト）

| # | 禁止 | 理由 |
|---|---|---|
| 1 | セットの異なるGT値の直接比較 | スケール基準が異なる（最大語=100がセット毎に違う） |
| 2 | summary値からの時系列再構成 | raw点がなく検証不能 |
| 3 | snapshot件数の母集団比較 | 上限・関連度・言語条件が異なる |
| 4 | 空白月の `observed_zero` 断定 | 未取得と言語混入の区別がつかない（実証済み） |
| 5 | 旧runの期間外挿 | 収集窓外の値は存在しない |

---

## 5. ギャップ解消ロードマップ

| # | 対策 | 対象ギャップ | 状態 |
|---|---|---|---|
| 1 | 日本語13語＋JA-1〜JA-4＋5y主要5語の取得 | G2（クエリー不統一） | ✅ 完了（2026-10-12） |
| 2 | run_metadata 9項目＋anchor/zero_statusの標準化 | G5（来歴濃淡） | ✅ 新規runで適用済み。旧runは未遡及 |
| 3 | 用語定義の固定（本資料§3） | 混乱防止 | ✅ 本資料で実施 |
| 4 | 旧10年系列の証拠・公開対象からの除外を維持 | G4・G5 | 対象外（補完・統合は行わない） |
| 5 | 英語5yのrawタイムライン再取得 | G4 | 未着手（CBD日本語5yで代替済み1件） |
| 6 | no-data 4語の再取得（below_threshold確定） | 表2-1の× | 未着手 |
| 7 | 旧runの来歴遡及（不明値はunknown明示） | G5 | 未着手 |
| 8 | matrix・first-mentionの本資料準拠への改訂 | 信頼性表示 | 未着手 |

---

## 付録A. run-id命名規則

```
<UTC時刻>-<ソース>-<内容>-<期間>
例: 20261012T064246Z-google-trends-ja-rikiddo-5y-main5
```

- 時刻: `YYYYMMDDTHHMMSSZ`（収集開始時のUTC）
- ソース: `google-trends` / `x-<...>` / `youtube-<...>`
- 内容: スラッグ（日本語は `<romaji>-rikiddo` に統一。二重接尾辞・日本語混じり禁止）
- 期間: `12m` / `5y` / 比較は `compare-ja<N>-12m` 等

## 付録B. 必須run_metadata 9項目

`run_id`・`study_id`・`source`・収集手段（`mcp_server`＋版 or `actor`）・`collection_timestamp`・`queries`（term/geo/timeframe/type）・件数・`purpose`・エラー記録。比較runは `anchor_terms`＋換算式、GT runは `zero_status` を追加。
