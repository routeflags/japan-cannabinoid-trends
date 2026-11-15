# Data Dictionary

**Version:** 1.0.0
**Last Updated:** 2026-10-02
**Purpose:** 各データセットのカラム定義、型、単位、欠損値の扱いを文書化

---

## 1. X (Twitter) データ

### 1.1 処理済みデータ（2026-10-13 公開取り下げ）: `x_cbx_202608_summary.csv`

> **本ファイルは公開されていない。** 2026-10-13 に追跡を外し、非公開の
> `datasets/cbx-social-trends/data/private/` へ退避した（露出範囲と経緯は
> `docs/issues/closed/mitigated/20261013_p0_x-identity-published-in-all-releases.md`）。
> 2026-10-15 以降、**投稿単位の X データは匿名化後も公開しない**（§1.2）ため、
> X の処理済み成果物として公開されているものは**無い**。以下のスキーマは
> **取り下げ前の記録**として保持する（来歴を消さないため）。

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `tweet_id` | string | — | X (Twitter) のユニークなツイート ID | 欠損なし |
| `createdAt` | string (ISO 8601) | — | ツイートの投稿日時（UTC） | 欠損なし |
| `lang` | string | — | 言語コード（例: `ja` = 日本語） | 欠損なし |
| `username` | string | — | 投稿者のユーザー名（@なし） | 欠損なし |
| `author_name` | string | — | 投稿者の表示名 | 欠損なし |
| `views` | integer | 回 | ツイートの表示回数 | 欠損なし |
| `likes` | integer | 個 | いいね数 | 欠損なし |
| `reposts` | integer | 個 | リポスト（リツイート）数 | 欠損なし |
| `replies` | integer | 個 | 返信数 | 欠損なし |
| `url` | string (URL) | — | ツイートへの直接リンク | 欠損なし |
| `text` | string | — | ツイート本文（全角・絵文字含む） | 欠損なし |

**データ完全率:** 全カラム 147/147 (100%)

**注意事項:**
- `username` と `author_name` は個人情報を含む。**このファイルは公開しない。**
  2026-10-15 以降は匿名化版も公開しない（§1.2）: 再配布できるのは集計値（§1.3）であり、
  投稿単位の表ではない。変換規則は `src/processing/anonymize.py` にある。
- `views` は取得時点の値であり、変動する
- `createdAt` は UTC 表記

### 1.2 匿名化版（2026-10-15 公開取り下げ）: `x_cbx_202608_summary_anonymized.csv`

> **本ファイルは公開されていない。** 2026-10-15 のメンテナ決定（`ISS-20261015-COL-030`
> §4.1「匿名化した場合でも、投稿単位の研究CSVは公開しない」）で追跡を外した
> （経緯・露出は `ISS-20261015-PUB-035`、記録は `src/processing/reproduce.py` の
> `WITHDRAWN`）。以下のスキーマは**取り下げ前の記録**として保持する。

**用途:** なし（投稿単位のため非公開。公開できるのは集計値 = §1.3 と収集メタデータ）

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `tweet_id_hash` | string | — | ツイート ID の SHA256 ハッシュ（先頭16文字） | 欠損なし |
| `createdAt` | string (ISO 8601) | — | ツイートの投稿日時（UTC） | 欠損なし |
| `week` | string | — | 週分類（W1-W6） | 欠損なし |
| `lang` | string | — | 言語コード（例: `ja` = 日本語） | 欠損なし |
| `author_id` | string | — | 匿名化された著者 ID（author_001 等） | 欠損なし |
| `views` | integer | 回 | ツイートの表示回数 | 欠損なし |
| `likes` | integer | 個 | いいね数 | 欠損なし |
| `reposts` | integer | 個 | リポスト数 | 欠損なし |
| `replies` | integer | 個 | 返信数 | 欠損なし |
| `has_text` | string | — | 本文が存在するか（yes/no） | 欠損なし |
| `text_length` | integer | 文字 | 本文の文字数 | 欠損なし |
| `topic_id` | string | — | 話題分類 ID（SKOS Concept notation） | `unclassified` |
| `intent_id` | string | — | 投稿意図 ID（SKOS Concept notation） | `unclassified` |
| `format_id` | string | — | 投稿形式 ID（SKOS Concept notation） | `unclassified` |
| `platform` | string | — | プラットフォーム名 | `x_twitter` |
| `language` | string | — | 言語コード（BCP 47） | `ja` |

**データ完全率:** 全カラム 147/147 (100%)

**分類フィールドの値:**

| フィールド | 許容値 | タクソノミー |
|-----------|--------|-------------|
| `topic_id` | `topic_ingredient`, `topic_product`, `topic_effect`, `topic_promotion`, `topic_review`, `topic_store`, `unclassified` | `metadata/taxonomy/content-taxonomy.skos.jsonld` |
| `intent_id` | `intent_informational`, `intent_commercial`, `intent_experiential`, `intent_harm_report`, `unclassified` | 同上 |
| `format_id` | `format_text`, `format_image`, `format_video`, `format_link`, `unclassified` | 同上 |

**分類フィールドの参考:**

| フィールド | Schema.org 対応 | SKOS 対応 |
|-----------|----------------|-----------|
| `topic_id` | `schema:about` | `skos:notation` |
| `intent_id` | カスタム | `skos:notation` |
| `format_id` | カスタム | `skos:notation` |
| `platform` | `schema:isPartOf` | — |
| `language` | `schema:inLanguage` | — |

**匿名化内容:**

| 元のフィールド | 匿名化後 | 方法 |
|---------------|---------|------|
| `tweet_id` | `tweet_id_hash` | SHA256 ハッシュ（先頭16文字） |
| `username` | `author_id` | 連番 ID（author_001 等）に置換 |
| `author_name` | （削除） | 個人情報のため削除 |
| `text` | `text_length` | 文字数のみ保持、本文は削除 |
| `url` | （削除） | 個人情報のため削除 |

**匿名化マッピング:**
- ローカル専用: `datasets/cbx-social-trends/data/private/x_anonymization_mapping.json`
- gitignore 対象（公開不可）

### 1.3 集計統計（ガイドページ掲載値）

| 指標 | 中央値 | P90 | 最大値 | 合計 | 算出方法 |
|------|--------|-----|--------|------|---------|
| Views | 963 | 4,904 | 17,247 | 282,478 | 全147件の統計 |
| Likes | 7 | 23 | 110 | 1,715 | 同上 |
| Reposts | 2 | 6 | 127 | 495 | 同上 |

**週別推移:**

| 週 | 期間 | 投稿数 | ユニーク著者数 |
|----|------|:------:|:--------------:|
| W1 | 8/3〜8/9 | 12 | 7 |
| W2 | 8/10〜8/16 | 10 | 9 |
| W3 | 8/17〜8/23 | 48 | 22 |
| W4 | 8/24〜8/30 | 28 | 17 |
| W5 | 8/31〜9/6 | 33 | 18 |
| W6 | 9/7〜9/8 | 13 | 8 |

---

## 2. YouTube データ

### 2.1 フィルタ済みデータ: `youtube_filtered_202607/records_filtered.csv`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `videoId` | string | — | YouTube のユニークな動画 ID | 欠損なし |
| `title` | string | — | 動画タイトル（ハッシュタグ含む） | 欠損なし |
| `channel` | string | — | チャンネル名 | 欠損なし |
| `views` | integer | 回 | 動画の表示回数 | 欠損なし |
| `duration` | string | — | 動画の長さ（例: "5:30"） | 欠損なし |
| `timestamp` | string | — | 公開時期（相対表記: "2 weeks ago"） | 欠損なし |
| `url` | string (URL) | — | 動画への直接リンク | 欠損なし |

**データ完全率:** 全カラム 24/24 (100%)

**フィルタ情報:**

| 項目 | 値 |
|------|-----|
| フィルタ日 | 2026-10-01 |
| 元データ件数 | 26 |
| フィルタ後件数 | 24 |
| 除外件数 | 2 |
| 除外基準 | `timestamp` に "years ago" を含む（2年以上前） |

---

## 3. Google Trends データ

### 3.1 raw データ: `google_trends/{run_id}/records.json`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `query` | string | 検索クエリ（例: "CBX"） |
| `geo` | string | 地域コード（例: "JP"） |
| `timeframe` | string | 観測期間（例: "today 12-m"） |
| `collected_at` | string (ISO 8601) | 収集日時（UTC） |
| `source` | string | データソース（"google-trends-mcp"） |
| `data` | array | 週次データポイントの配列 |

**`data` 配列の各要素:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | string (ISO 8601) | 週の開始日 |
| `interest` | integer (0-100) | 検索関心度（相対指数） |

**注意:** Google Trends の値は相対指数であり、絶対検索数ではない。

### 3.2 比較データ: `google_trends/{run_id}/comparison.json`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `terms` | array | 比較対象のクエリ一覧 |
| `geo` | string | 地域コード |
| `timeframe` | string | 観測期間 |
| `data` | array | クエリ別の週次データポイント |

---

## 4. COA データ

### 4.1 分析結果（ガイドページ掲載値）

| 分析項目 | 単位 | KCA Labs | Anresco | 判定 |
|----------|------|----------|---------|------|
| CBG | % | 30.4 | 30.28 | 一致 |
| CBD | % | 5.74 | 5.27 | ほぼ一致 |
| Total Cannabinoids | % | 36.1 | 35.55 | ほぼ一致 |
| Δ9-THC | % (ppm) | 0.000045 (0.45 ppm) | ND | 微量検出 |
| Δ8-THC | % | ND | ND | 未検出 |
| HHC | % | ND | ND | 未検出 |
| HHCH | % | ND | ND | 未検出 |
| THCP | % | ND | ND | 未検出 |

**ND = Not Detected（未検出）**

**注意:**
- 分析対象は原料（Concentrate-Distillate）であり、成品ではない
- Δ9-THC の限度値は原料 10 ppm、成品（その他）1 ppm

---

## 5. キーワード辞書: `metadata/keywords.yaml`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `display_name` | string | 表示名 |
| `category` | string | カテゴリ（例: "minor_phytocannabinoid"） |
| `keywords` | array | 検索に使用するキーワード一覧 |
| `polysemy_warning` | string / null | 多義性に関する警告 |
| `discriminating_queries` | array | 多義性を排除する判別クエリ |
| `search_notes` | object | プラットフォーム別の検索ノート |

---

## 6. 主要カンナビノイドトレンドデータ: `cannabinoid-raw-collection`

**Study ID:** cannabinoid-raw-collection
**作成日:** 2026-10-02
**対象化合物:** CBD, THC, CBG, HHC, THCV, THC-O, THCH

### 6.1 Google Trends データ

**パス:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `keyword` | string | — | 収集キーワード（化合物名） | 欠損なし |
| `geo` | string | — | 地域コード（JP = 日本） | 欠損なし |
| `timeframe` | string | — | 観測期間（例: `today 12-m`, `today 5-y`） | 欠損なし |
| `date` | date | — | データポイントの日付（週開始日） | 欠損なし |
| `value` | number | — | 興味度スコア（0-100） | 低ボリュームでは `0`（`observed_zero`） |

**データ期間:**
- 12ヶ月データ: 2025-09-28 〜 2026-10-03
- 5年データ: 2021-09-26 〜 2026-10-03

**注意事項:**
- Google Trends は相対指数（0-100）であり、絶対検索数ではない
- 低ボリュームクエリ（HHC, THCH, THCV, THC-O）はデータが不安定
- THCV/THC-O は12ヶ月データでは閾値未満の可能性がある

### 6.2 X (Twitter) データ

**パス:** `datasets/cannabinoid-raw-collection/data/raw/x/`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `tweet_id` | string | — | ツイート ID | 欠損なし |
| `screen_name` | string | — | 投稿者ユーザー名 | 欠損なし |
| `created_at` | string (ISO 8601) | — | 投稿日時（UTC） | 欠損なし |
| `text` | string | — | ツイート本文 | 欠損なし |
| `lang` | string | — | 言語コード | 欠損なし |
| `views` | integer / string | 回 | 表示回数（string 型の場合あり） | 欠損なし |
| `favorites` | integer | 個 | いいね数 | 欠損なし |
| `retweets` | integer | 個 | リポスト数 | 欠損なし |
| `replies` | integer | 個 | 返信数 | 欠損なし |

**観測期間:** 2026-09-01 〜 2026-10-01
**注意事項:**
- `views` は string 型で返る場合がある（`int()` 変換が必要）
- シャドウバンにより 0 件の可能性あり（`observed_zero` として記録）
- 個人情報を含むため、公開時は匿名化が必要

### 6.3 YouTube データ

**パス:** `datasets/cannabinoid-raw-collection/data/raw/youtube/`

| カラム名 | 型 | 単位 | 説明 | 欠損値の扱い |
|----------|-----|------|------|-------------|
| `videoId` | string | — | YouTube 動画 ID | 欠損なし |
| `title` | string | — | 動画タイトル | 欠損なし |
| `channelTitle` | string | — | チャンネル名 | 欠損なし |
| `views` | integer | 回 | 再生数 | 欠損なし |
| `duration` | integer | 秒 | 動画の長さ | 欠損なし |
| `timestamp` | string | — | 相対公開日（例: "3 days ago"） | 欠損なし |

**取得日:** 2026-10-02（スナップショット）
**注意事項:**
- `timestamp` は相対表記（絶対日付ではない）
- ページング重複あり、`videoId` で重複排除必須
- 再生数は取得時点の値（変動する）

### 6.4 化合物カテゴリ

**正本:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`。本表はその写しであり、
一致は `tests/validation/test_taxonomy_consistency.py` が検査する（以前は taxonomy が 6 カテゴリ 18 化合物
であるのに本表は 3 カテゴリ 7 化合物しか載せておらず、カテゴリ ID も独自のものだった）。

| カテゴリ（notation） | カテゴリ名（ja） | 成分 |
|-------------|------|--------------|
| `compound_major` | 主要フィトカンナビノイド | `compound_cbd`, `compound_thc` |
| `compound_minor` | 主要フィトカンナビノイド以外のフィトカンナビノイド | `compound_cbg`, `compound_cbn`, `compound_cbc`, `compound_cbe`, `compound_thcv`, `compound_cbdv`, `compound_cbx`, `compound_thch`, `compound_cbl`, `compound_cbga` |
| `compound_rare` | レアカンナビノイド | （なし。**意図的に空**。`skos:scopeNote` 参照） |
| `compound_identity_unverified` | 同一性未確認の登録語（登録状態） | `compound_thcb`, `compound_thcp`, `compound_thcjd`, `compound_thcpo`, `compound_hhcpo`, `compound_cbnd`, `compound_cbp`, `compound_10_oh_hhc`, `compound_thxe`, `compound_thca`, `compound_delta9_thca_a`, `compound_thca_b`, `compound_delta8_thca`, `compound_delta8_thcb`, `compound_delta9_thcb`, `compound_thcb_o_acetate`, `compound_delta8_thcp`, `compound_delta9_thcp`, `compound_delta8_thcjd`, `compound_delta9_thcjd`, `compound_delta8_thcp_o_acetate`, `compound_delta9_thcp_o_acetate`, `compound_delta8_thcb_o_acetate`, `compound_delta9_thcb_o_acetate`, `compound_delta8_thc`, `compound_delta6a_10a_thc`, `compound_delta6a_7_thc`, `compound_delta7_thc`, `compound_delta10_thc`, `compound_delta9_11_thc`, `compound_delta9_thcv`, `compound_delta8_thcv`, `compound_thcjd_o_acetate`, `compound_delta8_thch`, `compound_delta9_thch`, `compound_9_r_hhc`, `compound_9_s_hhc`, `compound_6as_9s_10as_hhc`, `compound_6as_9r_10as_hhc`, `compound_6as_9s_10ar_hhc`, `compound_6as_9r_10ar_hhc`, `compound_6ar_9s_10as_hhc`, `compound_6ar_9r_10as_hhc` |
| `compound_semisynthetic` | 半合成カンナビノイド | `compound_hhc`, `compound_thc_o`, `compound_h4cbh`, `compound_hhbd`, `compound_thcnm` |
| `compound_synthetic` | 合成カンナビノイド | `compound_hhch`, `compound_crdp`, `compound_crdh` |
| `compound_endocannabinoid` | エンドカンナビノイド | `compound_anandamide`, `compound_2ag` |

> **注:** カテゴリは**製造経路**による分類である。化学構造による分類（水素化カンナビノイド等）とは
> 別物であり、`research/google-trends/20261004-google-trends-compound-summary.md` の「カテゴリ」列
> は化学クラスを指すため本表とは一致しない。両者を混同しないこと。
> 化学クラスの正式な所属は §6.5（第 2 次元）を参照。
> `compound_thcnm` は化学的同一性が未確認のまま登録した概念であり（THA は別名・商業名）、
> その `skos:broader` 配置は暫定である。識別子と未決事項は ISS-20261104-TAX-028 を参照。
> `compound_identity_unverified` は**経路分類ではなく管理上の登録状態カテゴリ**である
> （ISS-20261111-TAX-040）。members は owner が名指しした検索語のうち化学的同一性が
> 未確認のもので、この配置は経路・由来、天然存在、化学クラス、構造、別名、規制状態に
> ついて**何も主張しない**。**カテゴリ所属自体は同義関係を確立しない**：member の
> `skos:altLabel` は概念レベルの記録であり、owner が確認した別名・検索トピックの表記には
> その概念の scopeNote に独自の根拠を要する（`compound_thcpo` の英語
> `skos:altLabel` `THCP-O-acetate` はこの規則による検索スコープの別名で、単一構造の
> 同義語ではない）。ただし、異性体未指定のファミリーとして登録した語の
> scopeNote は、異性体ごとの物質が法令上の構造グループに該当することを記録する場合が
> ある。それは当該異性体についての記載であり、この配置が規制分類を行うものではない。希少・マイナー・半合成・合成のいずれの分類の代替でもなく、
> 根拠が得られた語はその根拠が支えるカテゴリへ移す。`compound_thcp` は 2026-10-15 の
> TAX-027 が「登録しない」と判断した語だが、2026-11-11 の owner 指示がその判断を
> 置換した（ISS-20261111-TAX-040）。`compound_rare` は引き続き空である。
> `compound_cbe` は 2026-11-11 に owner が cannabielsoin と確認した語で、FDA GSRS
> （UNII 2ERD6V6652、CAS 52025-76-0、PubChem CID 162113、C21H30O3）と
> Wikidata Q22668702 を根拠に `compound_minor` へ移した。`compound_cbl` は同日
> cannabicyclol と確認し（Wikidata Q907909、FDA GSRS UNII MP5WZK8M5U、PubChem CID
> 30607 / 59444380、C21H30O2）、`compound_cbga` は cannabigerolic acid（標準表記
> CBGA）と確認した（ChEBI 67081、Wikidata Q27135612、FDA GSRS UNII 80I4ZM847Y、
> PubChem CID 6449999、C22H32O4）。両語も `compound_minor` へ移した。CBL の 2 つの
> CAS 番号（21366-63-2 / 67920-00-7）は立体化学の扱いが異なるため、単一の CAS を
> 識別子として断定しない。CBG は CBGA の脱炭酸体であり別名ではない。Google Trends /
> YouTube の系列は `CBE` / `CBE リキッド`、`CBL` / `CBL リキッド`、`CBGa` /
> `CBGa リキッド` の文字列一致を測るもので、意図された同一性が確認されても各結果の
> 内容を保証しない（ISS-20261111-TAX-040 追記）。`compound_thcp`・`compound_thcjd` は
> 2026-11-11 に owner が意図された範囲を、それぞれ tetrahydrocannabiphorol（C7）同族体
> ファミリー・THC-JD / 3-octyl-THC（C8）同族体ファミリー（Δ8/Δ9 未指定）と確認した。
> `compound_thcpo` は owner が確認質問「`THCPO` は THCP-O-acetate を指しますか？」に `y`
> と回答し、異性体を指定しなかったため、登録を**異性体未指定の THCP-O-acetate ファミリー**
> として扱う（ファミリー扱いは回答の登録上の整理であり、owner がファミリーを明示的に
> 確認したものではない）。いずれも単一物質の同定ではなく、Δ8 体と Δ9 体は別物質であるため、3 語には単一
> レコードを指す `exactMatch` も識別子も付けず、各異性体の識別子は
> `docs/provenance/compound-taxonomy.md` に記録する。`THCPO` の Δ8/Δ9 両異性体は
> 2024 年の厚生労働省令の構造グループに該当するが、それは省令の**「麻薬を除く」除外規定**
> の下での法令上の構造の事実であり、個々の製品・検索結果の分類ではなく、規制判断でも、
> owner の同一性確認の一部でもない。系列は
> `THCP` / `THCP リキッド`、`THCJD` / `THCJD リキッド`、`THCPO` / `THCPO リキッド` の
> 文字列一致を測るもので、各結果をどの異性体に帰属させられるかは未確認である。

> `compound_thca` / `compound_thcb` は、2026-11-11 の owner 確認により総称の化学解釈から 6 つの検索トピック概念へ分かれた
> （`Δ9-THCA-A` / `THCA-B` / `Δ8-THCA`、`Δ8-THCB` / `Δ9-THCB` / `THCB-O-acetate`。ISS-20261111-TAX-041）。6 概念はすべて
> `compound_identity_unverified` に置き、単一の検証済み外部識別子を選択していないため `exactMatch` を張らず、
> `compound_thca` / `compound_thcb` / `compound_thc` や相互の `skos:related` も張らない。総称の 2 概念は文字列 `THCA` / `THCB` の
> 登録として残り、既存の run とクエリは付け替えない。Google Trends / YouTube の系列は各登録文字列の一致を測るもので、
> Δ8/Δ9 や A/B の内容を保証しない。
>
> 2026-11-15 の owner 指示で、study README の「未登録・未収集の候補形式」27 行を検索トピックとして
> 登録した（`ISS-20261115-TAX-045`）。内訳は THC の位置異性体 6 形式、THCP・THCJD・THCPO・
> THCB-O-acetate・THCH・THCV の個別異性体と `THCJD-O-acetate`（異性体未指定）の 13 形式、HHC の
> 立体異性体 8 形式である（6 + 13 + 8 = 27）。27 概念はいずれも `compound_identity_unverified` に置き、単一の
> 検証済み外部レコードを選択していないため、27 概念には識別子プロパティも `skos:exactMatch` も割り当てず、
> `skos:related` も張らない。棚卸し上の親語（`THC`・`THCP`・`HHC` 等）との
> 関係は整理上の対応であり、構造・同義の主張ではない。証拠の種類は registry record・法令の
> 構造グループ（令和6年厚生労働省令第81号、消費者庁の THCH 指定薬物資料）・命名標準と知識グラフ・
> WHO 47th ECDD (2024) §2C の可能な配置のレビュー・製品分析に分かれ、法令上の列挙は製品検出ではなく、
> WHO のレビューは配置ごとの registry record でも製品同定でもない。27 語はいずれも未収集で、
> 0 観測でも欠測でもない。既存の query・run の割当ては変更していない。

### 6.5 化学クラス（第 2 次元）

**正本:** `metadata/taxonomy/chemical-class-taxonomy.skos.jsonld`（オーナー判断 (a)、ISS-20261015-TAX-026、2026-10-15）。
本表はその写しであり、一致は `tests/validation/test_chemical_class_dimension.py` が検査する。
製造経路の次元（§6.4）とは `skos:related` のみで結合し、`skos:broader` / `skos:narrower` は次元を跨がない。

| 化学クラス（notation） | 化学クラス名（ja） | 成分 |
|-------------|------|--------------|
| `chemclass_hydrogenated` | 水素化カンナビノイド | `compound_hhc`, `compound_hhch`, `compound_h4cbh`, `compound_hhbd` |
| `chemclass_acetate` | アセテート体カンナビノイド | `compound_thc_o` |

> **注:** 収載は意図的に部分的である。リンクを持たない化合物は化学クラスが未形式化であることを意味する。
> `compound_crdp` / `compound_crdh` は化学構造不明と記録されているため、研究文書側の「ヒドロキシ酸類似体」は
> クラスとして採用しない。研究文書は独自語彙を保ち、根拠のあるクラスのみを形式化する。

---

## 7. 欠損値の扱い

### 7.1 状態定義

| 状態 | 意味 | 表記 |
|------|------|------|
| `observed_zero` | 観測されたが、値がゼロ | 0 |
| `observed_nonzero` | 観測され、値が存在 | 実際の値 |
| `missing` | データが存在しない | 空文字または "NA" |
| `collection_failed` | 収集が失敗した | "collection_failed" |
| `partial` | 部分的なデータ | 実際の値 + 注記 |
| `unknown` | 不明 | "unknown" |

### 7.2 各データセットの欠損値状況

| データセット | 欠損値 | 状態 |
|-------------|--------|------|
| X データ (147件) | なし | 全カラム 100% |
| YouTube データ (24件) | なし | 全カラム 100% |
| Google Trends | 低ボリュームクエリで 0 件 | `observed_zero` または `no_data` |
| 26週 X データ | 空週あり | `observed_zero`（製品投入前） |

---

## 8. カラム名の正規化

### 8.1 X データ

| 元のフィールド（Apify） | 正規化後 | 理由 |
|------------------------|---------|------|
| `tweet_id` | `tweet_id` | そのまま |
| `created_at` | `createdAt` | キャメルケースに統一 |
| `user_info.screen_name` | `username` | ネスト解除 |
| `user_info.name` | `author_name` | ネスト解除 |
| `favorites` | `likes` | 意味が明確な名前に変更 |
| `retweets` | `reposts` | 意味が明確な名前に変更 |
| `text` | `text` | そのまま |

---

## 9. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `methodology.md` | 収集・処理方法の詳細 |
| `datasets/cbx-social-trends/methodology.md` | ソーシャルデータの方法論 |
| `datasets/cbx-search-trends/methodology.md` | 検索トレンドの方法論 |
| `docs/provenance.md` | データ来歴の詳細 |
| `metadata/datapackage.json` | データパッケージ定義 |
| `metadata/keywords.yaml` | キーワード辞書 |
