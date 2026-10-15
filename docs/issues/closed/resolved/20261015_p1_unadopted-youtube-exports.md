# Issue: 未採用の YouTube dataset export 7 件の実採用判断が未了

**ID:** ISS-20261015-COL-033  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `docs/reports/20261015b-youtube-csv-staging-driver.md`、
`src/collection/core/staging.py`（`staging-declaration-v1`）、
`datasets/youtube-consistency/data/raw/`、`ISS-20261015-COL-017`（RESOLVED）、
`ISS-20261015-COL-018`、`ISS-20261015-PRV-013`

## 概要

2026-10-14 にダウンロードした実 YouTube dataset export 7 件（Apify `youtube-scraper`、
`~/Downloads/dataset_youtube-scraper_*.csv`）は、**stage → adopt → 厳格検証までの rehearsal は済んでいるが、
実採用は未実施**である。採用判断には宣言事実の確認が 6 点必要で、それが先
（`docs/reports/20261015b-youtube-csv-staging-driver.md` §5）。

`ISS-20261015-COL-017`（staging ドライバ + `stage` CLI）は RESOLVED だが、
その完了条件のうち「実採用」が残っており、追跡先が無かった。

## 確認された観測（rehearsal の記録）

- rehearsal はリポジトリ外 scratch workspace（`/tmp/yt-staging-rehearsal-20261015/`）で
  7/7 stage → 7/7 adopt → `validate_full(verify_artifacts=True)` valid →
  `audit-new-runs` new=7 / failures=0。payload は `~/Downloads` 原本と byte 一致。
- **リポジトリの `datasets/` は未変更**（本採用はしていない）。
- 宣言値（窓 / `date_filter` / status / 時刻）は確認前の placeholder。
  5 件は `date_filter: all` と矛盾しないが、2 件（`13-50-24` / `19-19-00`）は
  bounded の可能性を排除できない。

## 影響

- 取得済みで検証可能な YouTube データが公開物に反映されない
  （`publication/research_*.html` の YouTube 節は 2026-10-08〜09 の値のまま）。
- 「取得したが未採用」の状態が続き、何が未了かが issue から見えない。

## 対応方針

確認する 6 点（同レポート §5）:

1. 各 export の actor run ID / dataset ID（`ISS-20261015-PRV-013` の取得依頼リスト）
2. 各 run の `dateFilter`（`13-50-24` / `19-19-00` は要確認）
3. 実行 status（SUCCEEDED か）と startedAt / finishedAt
4. ファイル名 stamp の意味と timezone（run 時刻 / export 時刻、UTC / JST）
5. 実採用の可否（配置先は方針上無追跡。`ISS-20261015-COL-018` の
   「決定先送り中は実 run を catalog しない」を YouTube にも適用するか）
6. 宣言の絶対窓（研究側観測区間）の確定

採用する場合は `staging-declaration-v1` の宣言ファイルを commit して `stage` → `adopt`。
採用しない場合は理由を記録する（**失敗を 0 件に変換しない**）。

## 完了条件

- [x] 上記 6 点の確認記録（日付付き）— Q1/Q2/Q3/Q4/Q5/Q6 すべて確定（下記）
- [x] 宣言ファイルの commit と `stage` → `adopt`（下記「正式採用の記録」）
- [x] 監査スナップショットの再生成と `audit-new-runs` / `audit-publication` の確認

## 正式採用の記録（2026-10-15）

オーナー指示: 採用対象 6 件の正式採用を進める。Q6 は動画公開日の最小〜最大を観測範囲として承認。
ただし API の `dateFilter` と観測範囲は区別して記録し（宣言の `limitations` に明記）、
観測範囲を API 検索条件として扱わない。COL-018(a) source 階層を使用し、非公開データ管理方針を維持する。

- 宣言: `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`
  （sha256 `423e8c15…11e3c1`。コミット `7c51f76`）。`13-50-24` は対象外。
- `stage`: exit 0、6 staged / 0 stopped。`adopt`: 6/6 ADOPTED →
  `datasets/youtube-consistency/data/raw/youtube/<run-id>/`（無追跡。方針どおり commit 対象外）。
  L1 は `COLLECTOR_LEGACY_REFERENCE` の info のみ（collector unverified は意図どおり可視）。
- 検証: 6 run すべて `validate_full(verify_artifacts=True)` valid・error 0。
  catalog payload は `~/Downloads` 原本と byte 一致（sha256 照合 6/6）。
- 監査: `audit-new-runs` 47 runs / new=18 / failures=0（内 6 件が本採用分）。
  `audit-publication` 16 artifacts / findings 0。監査スナップショット再生成済み。
- 研究ページへの反映: **未反映**。`publication/research_cbx.html` の YouTube 節は 2026-10-04 の
  v3 取得値のまま。反映は公開契約 PC-2 / PC-8 の範囲の別作業（本 issue の完了条件には含まない）。

## 依存

- `ISS-20261015-COL-018`（無追跡 raw の catalog 方針）の決定。
- 公開物への反映は公開契約 PC-2 / PC-8 の範囲（run_id を持たない旧契約の収集とは別扱い）。

## 確認記録（2026-10-15、再検証）

メンテナの `go` 指示を受け、採用可否の前提を証拠から再確認した。結論: **採用はしない**（下記の未確認項目が残るため。placeholder での採用は推測の記録になる）。

### 証拠から確定したこと

| # | 項目 | 証拠 |
|---|---|---|
| E1 | 7 ファイルの同一性 | `~/Downloads/dataset_youtube-scraper_*.csv`、sha256 記録済み（`67d82052…` / `98617d1c…` / `7eece62b…` / `cc2dfbf4…` / `f644cb03…` / `2d9f0b1c…` / `77aae411…`）。mtime は全件 2026-10-14 20:58〜20:59 +0900（ダウンロード時刻） |
| E2 | record 数・クエリ対応 | reader 計数で 24 / 224 / 395 / 456 / 468 / 352 / 393。各ファイルの `input` 列は単一 keyword（CBD / HHBD / H4CBH / CBD / CBN / CRDH / CBD＋リキッド）で、5 件の `query_id`（`cbd-liquid-ja` / `hhbd-liquid-ja` / `h4cbh-liquid-ja` / `cbn-liquid-ja` / `crdh-liquid-ja`）は registry に登録・active・canonical 一致 |
| E3 | `date` 列の意味 | 動画の公開日時（収集日時ではない）。範囲はファイルごとに 2008〜2026 に分散 |
| E4 | 列構成の不均一 | 列数が 101 / 135 / 135 / 189 / 155 / 135 / 487 とばらつく（export 設定差の可能性。provenance 上の注意点として記録） |
| E5 | 配置先の方針 | `datasets/youtube-consistency/data/` は `.gitignore`（`*`）で無追跡。storage policy `raw-social-default` は storage=private / git_tracking=ignored。採用しても commit されず CI に載らない |
| E6 | 実行パスの現状 | staging schema・`stage` CLI・`csv-record-reader`・契約テストは green（`test_csv_reader` + `test_staging_driver` 35 passed）。rehearsal 時とコードは変わっていない |
| E7 | Apify 証拠の探索 | repo・履歴・スキルを探索: skill の検証実績にあるのは無関係の 5 件テスト run のみ。履歴に run ID 一覧・dataset UUID なし。CSV 本体に ID 列なし。**本家 checkout（`local`）の `datasets/youtube-consistency/data/trends.db` に `runs` テーブルがあり、全 7 件の run ID・dataset ID・収集時刻・`max_videos` を記録していた**（2026-10-15 確認。read-only 照会。DB 自体は gitignore のため本 worktree には無い）。ファイルの検疫メタデータの dataset ID と DB が相互に一致し、record 数も CSV と一致した |

### 未確認のため採用しない項目（§5 の 1〜6 に対応）

| # | 項目 | 状態 |
|---|---|---|
| Q1 | actor run ID / dataset ID | **7/7 確定**（本家 `trends.db` の `runs` テーブル。下表）。検疫メタデータの dataset ID・CSV の record 数と相互に一致した |

**確定した run ID / dataset ID**（2026-10-15 確認。`trends.db` 読み取り＋検疫 URL＋CSV 計数の三点照合）:

| export（stamp） | keyword | records | actor run ID | dataset ID | DB 収集時刻 |
|---|---|---:|---|---:|---|
| 13-50-24 | CBD リキッド | 24 | `Focww0tHFA1TjwJgZ` | `641iqooVNvVRb9KxY` | 13:50:26 |
| 14-19-47 | HHBD リキッド | 224 | `P6Fd5BGjiR0qqrbMO` | `yrzTkTmakOVdQXNNU` | 14:19:59 |
| 14-34-29 | H4CBH リキッド | 395 | `KfZADENLkkauQBlX5` | `qXUt9LbuJrH7esPUc` | 14:34:42 |
| 14-44-21 | CBD リキッド | 456 | `4sp0DTonaTlGihAfc` | `1IU9x7a0fR6OcDaAa` | 14:44:33 |
| 14-57-27 | CBN リキッド | 468 | `rlwl2NvYNp1SJgbmW` | `CObrnRDoGsgFS41LY` | 14:57:35 |
| 16-49-15 | CRDH リキッド | 352 | `p7OnoebbWpOpcJOZT` | `XvOYiyeyKBxBbYvwB` | 16:49:26 |
| 19-19-00 | CBD リキッド | 393 | `VwsJXaOmn3HMsiSxN` | `aDwsmXz6MTfT4Dh47` | 19:19:13 |

※ `13-50-24` は 2026-10-15 のオーナー指示で採用対象外（下記 Q2 追補2）。run ID・dataset ID 自体の確定に影響はない。

全 7 件の `max_videos` は 999999（旧 run は 100）。`4sp0DTonaTlGihAfc` の導出相関も DB で裏付けられた。なお同 DB には今回の 7 件以外に 10-11 の HHCH（50 件）・CRDP（214 件）run もあるが、ダウンロードされた CSV が無いため本 issue の対象外 |
| Q2 | `dateFilter` | **確定**（オーナー回答 2026-10-15。下記「Q2 オーナー回答の記録」）。`14-44-21`=all、`19-19-00`=year（オーナー表現 "last year"）、他 4 件=all |
| Q3 | 実行 status・startedAt/finishedAt | **全 7 件の startedAt/finishedAt をコンソール記録から確定**（オーナー提示 2026-10-15。下表、UTC 換算済み）。status は全件成功。actor build は全件 `0.0.313`、origin API。費用合計 $5.94 |

**コンソール記録（Apify Runs 一覧。表示は JST のため UTC に -9h 換算。stamp/DB との差は秒単位）**:

| export | startedAt (UTC) | finishedAt (UTC) | stamp との差 | DB との差 | requests | 件数 | 費用 |
|---|---|---|---|---|---|---|
| 13-50-24 ※除外 | 13:49:56 | 13:50:25 | -1s | +1s | 27（27/0） | 24 | $0.07 |
| 14-19-47 | 14:15:44 | 14:19:48 | -1s | +11s | 239（239/0） | 224 | $0.67 |
| 14-34-29 | 14:26:03 | 14:34:30 | -1s | +12s | 417（417/0） | 395 | $1.19 |
| 14-44-21 | 14:35:13 | 14:44:22 | -1s | +11s | 482（482/0） | 456 | $1.37 |
| 14-57-27 | 14:47:52 | 14:57:29 | -2s | +6s | 494（494/0） | 468 | $1.40 |
| 16-49-15 | 16:40:25 | 16:49:17 | -2s | +9s | 372（372/0） | 352 | $1.06 |
| 19-19-00 | 19:09:08 | 19:19:02 | -2s | +11s | 416（416/0） | 393 | $1.18 |

（日付は 10-10 が 6 件、`19-19-00` のみ 10-11。`13-50-24` は採用対象外だが照合のため記載） |
| Q4 | ファイル名 stamp の意味・timezone | **意味は確定: 収集（run）時刻**。DB の `collection_timestamp` が stamp と 8〜13 秒差で一致する（stamp は DL 時刻ではなく収集時刻）。**timezone は UTC で確定**（オーナー回答 2026-10-15「JSTなわけないだろ」＋測定による裏付け）。コンソール表示（JST）から -9h した 7 件の finishedAt が stamp と 1〜2 秒差・DB と 6〜12 秒差で**全件一致**するパターンは、stamp が JST である可能性を排除する（JST なら表示は stamp と一致するはず）。`streamers/youtube-scraper` の Store ページ全文にも timezone 記述は無いことを確認済み |
| Q5 | COL-018 の YouTube への適用可否 | **確定・実装済み**（(a) source 階層を適用。COL-018 は 2026-10-15 RESOLVED。採用時の配置は `data/raw/<source>/<run-id>/` で確定） |
| Q6 | 宣言の絶対窓（開始・粒度・timezone） | 研究側の決定が必要 |

宣言 schema は `date_filter` / `started_at` / `finished_at` / `status` / 絶対窓を必須とし、`unknown` 値を持たない。未確認のまま placeholder で採用すると推測を記録に格上げすることになるため、確認が揃うまで `datasets/` は変更しない。

## 追記（2026-10-15、オーナー回答への対応）

- **Q2（重複＝テストラン判定）**: 動画 ID 突合の実測 — `13-50-24` の 24 件中 7 件のみが `14-44-21`（456 件）に含まれ、`19-19-00` の 393 件中 37 件のみが同 run に含まれる（356 件は固有）。レコード単位の完全重複ではない。`13-50-24` は同一クエリ・包含期間の小規模スナップショット、`19-19-00` は 356 件固有の実質別スナップショット。除 外するかは研究設計の判断であり、ここでは除外しない（除外する場合は理由を記録する）。
- **Q2 追補（全期間の 2 分割の有無）**: CBD リキッドの年別分布は `13-50-24`=2026 年のみ 24 件、`14-44-21`=2014:1/2015:3/2016:12/2017:13/2018:24/2019:55/2020:27/2021:152/2022:59/2023:31/2024:19/2025:33/2026:27、`19-19-00`=2025 年 118 件・2026 年 275 件。「2025 以前／以降の 2 分割」に相当するファイル構成は存在しない。全期間に最も近いのは `14-44-21` 単独（2014〜2026）。突合はペア単位で行い、結合版も確認済み: `union(13-50-24, 19-19-00)` は `14-44-21` の部分集合ではなく（`14-44-21` のみに 419 件）、逆方向にも固有レコードがある。
- **Q2 追補2（`13-50-24` の除外、オーナー指示 2026-10-15）**: `13-50-24`（CBD リキッド 24 件）は採用対象から外す。残り 2 件（`14-44-21` 456 件＋`19-19-00` 393 件）を CBD の根拠として使う。除外理由: 同一クエリ・包含期間の小規模スナップショットであり、`14-44-21` と期間が重複する（レコード重複は 7/24 のみだが、カバレッジとしては包含される）。ファイル自体は `~/Downloads` に残し、削除も改変もしない。採用対象は 7→6 件になる。`dateFilter` 確認の残りは 6 件分（特に `19-19-00`）。
- **Q3（status・時刻）**: `SUCCEEDED` 確認済み（オーナー回答）。startedAt/finishedAt はコンソール記録 7 件分で確定（上記 Q3 表）。
- **Q4（timezone）**: UTC で確定（オーナー回答＋7 件の一致パターンによる測定裏付け）。
- **Q6（絶対窓）**: 「データ実体を踏襲」に従い、各ファイルの動画公開日の最小〜最大（日境界・UTC）を窓とする。下表。粒度は day（動画日付が日単位のため。rehearsal の month から変更）。timezone は動画日付自体が Z 付きのため UTC。

| export | 宣言 window start | 宣言 window end_exclusive | granularity | timezone |
|---|---|---|---|---|
| 14-19-47 | 2020-09-30T00:00:00Z | 2026-10-06T00:00:00Z | day | UTC |
| 14-34-29 | 2020-10-01T00:00:00Z | 2026-10-02T00:00:00Z | day | UTC |
| 14-44-21 | 2014-11-17T00:00:00Z | 2026-10-10T00:00:00Z | day | UTC |
| 14-57-27 | 2008-08-01T00:00:00Z | 2026-09-24T00:00:00Z | day | UTC |
| 16-49-15 | 2022-09-29T00:00:00Z | 2026-09-12T00:00:00Z | day | UTC |
| 19-19-00 | 2025-10-11T00:00:00Z | 2026-10-10T00:00:00Z | day | UTC |

※ `13-50-24` 行は採用対象外のため削除（上記 Q2 追補2。値は `2026-09-10T00:00:00Z` → `2026-10-10T00:00:00Z` であったことをここに残す）。

## オーナーへの依頼（2026-10-15）: Q2 `dateFilter` の確認手順

既貼付の Runs 一覧には startedAt / finishedAt / status / 件数 / 費用は載るが、
入力条件の `dateFilter` は載らない。`dateFilter` は各 run の詳細ページの **Input タブ**にのみあるため、
下記のいずれかで 6 件分の値を知らせる（値の例: `all` / `thisYear` / `custom`＋期間。
項目自体が無い場合は「なし」と知らせる。それ自体が確定情報になる）。

手順 A（確実）: Apify Console → 使った Actor を開く → **Runs** → 下表の Started 時刻の行をクリック →
**Input** タブ → `dateFilter` の値をコピー。

手順 B（直接リンク。Actor 部分が表示と違う場合は手順 A を使う）:
`https://console.apify.com/actors/streamers~youtube-scraper/runs/<run ID>`

| export | run ID | Started（コンソールの JST 表示） | Finished（同） |
|---|---|---|---|
| 14-19-47 | `P6Fd5BGjiR0qqrbMO` | 10-10 23:15:44 | 10-10 23:19:48 |
| 14-34-29 | `KfZADENLkkauQBlX5` | 10-10 23:26:03 | 10-10 23:34:30 |
| 14-44-21 | `4sp0DTonaTlGihAfc` | 10-10 23:35:13 | 10-10 23:44:22 |
| 14-57-27 | `rlwl2NvYNp1SJgbmW` | 10-10 23:47:52 | 10-10 23:57:29 |
| 16-49-15 | `p7OnoebbWpOpcJOZT` | 10-11 01:40:25 | 10-11 01:49:17 |
| 19-19-00 | `VwsJXaOmn3HMsiSxN` | 10-11 04:09:08 | 10-11 04:19:02 |

回答形式は `run ID: 値` の 6 行でよい（例: `VwsJXaOmn3HMsiSxN: all`）。

## Q2 オーナー回答の記録（2026-10-15）

オーナー回答原文: 「dateFilter はCBDだけAllとlast year。あとはall」

採用対象 6 件への割当て（CBD 2 件の内訳はデータ実体との整合で割当て。導出根拠を付記する）:

| export | keyword | `dateFilter` | 割当ての根拠 |
|---|---|---|---|
| 14-19-47 | HHBD | `all` | 「あとはall」 |
| 14-34-29 | H4CBH | `all` | 「あとはall」 |
| 14-44-21 | CBD | `all` | 動画日付が 2014〜2026 に分散。フィルタ無しと整合 |
| 14-57-27 | CBN | `all` | 「あとはall」 |
| 16-49-15 | CRDH | `all` | 「あとはall」 |
| 19-19-00 | CBD | `year` | 動画日付が 2025-10-11〜2026-10-10（実行 2026-10-11 の直近約365日）。`year` の実挙動（直近365日）と整合 |

表記上の注意: オーナーは "last year" と述べたが、スキル（`apify-youtube-scraper` SKILL.md §日付フィルタ）の
実スキーム値は `year`（enumTitle "This year"、実挙動は直近365日のローリング窓）。宣言にはスキーム値 `year` を
記録し、オーナー表現との対応をここに残す。`14-44-21` / `19-19-00` のどちらがどちらかは上表のとおり
データ実体で割当てた（推測ではなく日付範囲の一致による）。

## Actor ID に関する記録（2026-10-15）

オーナー回答: 「アクターIDの更新は不要」。検討されていた Actor ID の差し替えは行わない。
`h7sDV53CddomktSi5`（streamers/youtube-scraper）を正として維持し、スキル・`config/collectors.json`・
README の記載は変更しない。本件に関する残作業は無い。

## オーナーへの依頼（2026-10-15）: Q5・Q6 の確定判断

### Q5: COL-018 の YouTube への適用可否

- 背景: `ISS-20261015-COL-018`（`docs/issues/active/30-production-collection-expansion/20261015_p1_new-run-tracking-policy-mismatch.md`）は
  「決定先送り中は実 run を catalog しない」を定め、配置は (a) source 階層（`datasets/<study>/data/raw/<source>/<run-id>/`）で
  決定済み・実装待ち。YouTube にも同じ規律を適用するかが未決。
- YouTube 側の事実: `datasets/youtube-consistency/data/` は `.gitignore`（`*`）で無追跡。
  保存方針 `raw-social-default`（`config/storage-policies.json`）は storage=private / git_tracking=ignored。
  採用しても commit されず CI に載らない（上記 E5）。つまり YouTube の採用は「無追跡の raw を増やす」ことになる。
- 選択肢: **(i)** COL-018(a) の実装完了まで YouTube の採用も待つ / **(ii)** YouTube は元々無追跡方針なので
  COL-018 の適用外とし、先行採用する（無追跡のまま置くことを明示の決定として記録する）。
- 回答: 「(i)」か「(ii)」の一言でよい。

### Q6: 宣言の絶対窓の確定

- 候補値: 上記「Q6（絶対窓）」追補の表（採用対象 6 件、日境界・粒度 day・timezone UTC。`13-50-24` 除外済み）。
  「データ実体を踏襲」（動画公開日の最小〜最大）に由来する。
- 回答: 「表のとおりでよい」か、変更する行の正値（開始・終了・粒度・timezone）。

## Q5 オーナー回答の記録（2026-10-15）

オーナー回答: 「(a)」（COL-018 で回答済みの (a) が YouTube にも適用される）。
帰結: YouTube の実 run も (a) source 階層（`datasets/<study>/data/raw/<source>/<run-id>/`）で catalog する。
COL-018(a) の実装完了後に採用する（実装待ちが解消条件。決定自体の残りは無い）。
