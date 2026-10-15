# CBD の X / YouTube 来歴照合記録（CBD-002・CBD-006 の証拠）

| 項目 | 内容 |
|------|------|
| **作成日** | 2026-10-15 |
| **対象 issue** | `ISS-20261012-CBD-002`（X 期間・来歴）、`ISS-20261012-CBD-006`（調査ページ数値） |
| **対象ファイル** | `publication/research_cbd.html` |
| **方針** | raw は変更しない。確認できない値は推測で補完せず unknown とする（AGENTS.md / `docs/collection-gap-analysis.md` §3.5）。 |

## 0. 証拠の出所と制約

- X / YouTube の raw は `.gitignore`（`**/data/raw/*`）により非追跡で、リポジトリには含まれない
  （`docs/collection-gap-analysis.md` §2-2 の G6）。本記録の数値は、ローカルの
  `datasets/` 配下 raw を読み取って照合した**観測**である。第三者検証は raw の再配布が
  承認されるまで不可（同 §4.3）。
- run の識別は run ディレクトリ名と `run_metadata.json` の内容による。
- 記録の無い項目は `unknown` と書き、`observed_zero` と混同しない。

---

## 1. CBD の X run 一覧

対象は `cannabinoid-multi-trends`（4 run）と `cannabinoid-social-trends`（1 run）。

| run ディレクトリ | raw 件数 | 投稿 `created_at` 範囲（UTC） | query / 期間指定 | Actor | 取得上限 | 状態 |
|---|---:|---|---|---|---|---|
| `cannabinoid-multi-trends/data/raw/x/20261002T064331Z-x-cbd` | 60 | 2026-10-01 19:59–21:55（全件 10-01） | `CBD since:2026-09-01 until:2026-10-01`（section=`latest`） | `cPYLH3QT9GyzKhB4S` | `max_pages: 3` | 成功 |
| `.../20261008T165031Z-x-cbd-1year` | 0 | — | unknown（run metadata に query なし） | unknown | unknown | SUCCEEDED・空レスポンス |
| `.../20261008T165122Z-x-cbd-1m` | 60 | 2026-10-01 11:15–21:27（全件 10-01） | unknown | unknown | unknown | SUCCEEDED |
| `.../20261008T165330Z-x-cbd-latest10` | 200 | 2026-10-07 23:40 – 2026-10-08 00:02 | unknown | unknown | unknown | SUCCEEDED |
| `cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds/cbd.json` | 100 | 2026-10-01 08:52–20:14（全件 10-01） | unknown（run_metadata 自体なし） | unknown | unknown | 成功（記録なし） |

補足（`run_metadata.json` にある観測値）:

| run | Apify run id | `usageTotalUsd` |
|---|---|---:|
| `20261008T165031Z-x-cbd-1year` | `oF6ROQ72XgwNk9oGV` | 0.0020 |
| `20261008T165122Z-x-cbd-1m` | `AjPrtAfunbZhQwA3a` | 0.0020 |
| `20261008T165330Z-x-cbd-latest10` | `9lUGIaA0aMabDyAy9` | 0.3058 |

## 2. 判定

- **`cbd-1year` の 0 件は `observed_zero` ではない。** `run_metadata.json` は
  `status: SUCCEEDED` のみを記録し、検索窓・上限・Actor が無い。空レスポンス＋条件不明
  のため `unknown` として扱う（`docs/collection-gap-analysis.md` §3.5）。
- **期間名（`1year` / `1m` / `latest10`）は run 名にのみ存在し、metadata で裏付けられない。**
  実データの `created_at` は 1m・1year とも 2026-10-01 に集中し、指定窓の時系列を構成しない。
- **CBD の X データは長期時系列として使用できない。** 確認できた投稿は 2026-10-01（および
  `latest10` の 2026-10-07/08）の単日スナップショットである。年次・月次の比較には使えない。
- 調査ページが用いる 100 件（`main-compounds/cbd.json`）も投稿は 2026-10-01 のみ。
  ページ記載の検索窓「2026-07-01〜2026-10-01」を裏付ける run metadata は存在しない。

---

## 3. CBD の YouTube run 照合（28 / 23 / 60 の由来）

| 値 | 出所 run | raw ファイル | 定義 |
|---|---|---|---|
| **60** | `cannabinoid-multi-trends/data/raw/youtube/20261005T140054Z-youtube-japanese-apify` | `cbd-oil_raw.json`（2026-10-05 収集） | 検索クエリ「CBD オイル」のレスポンス件数（ページング重複を含む） |
| **28** | 同上 | 同上 | 上記 60 件のユニーク動画 ID 数（重複排除後） |
| **23** | `.../20261002T064905Z-youtube-cbd-オイル` | `records.json`（2026-10-02 収集） | **別取得**。クエリ名は同じでも run が異なり、ページの出所ではない |

### 3.1 調査ページ YouTube 節（クエリ「CBD オイル」）の数値照合

出所 run = `20261005T140054Z-youtube-japanese-apify`。ユニーク 28 件を母集団として再計算した。

| 指標 | ページ記載 | 再計算（ユニーク 28 件） | 判定 |
|---|---:|---:|---|
| 元データ件数 | 60 | 60 | 一致 |
| ユニーク動画数 | 28 | 28 | 一致 |
| 再生数 平均 | 48,100 | 48,100 | 一致 |
| 再生数 中央値 | 14,298 | **14,228**（中央 2 値の平均 14,227.5） | **不一致**。14,298 は元データ 60 件を母集団とした中央値 |
| 再生数 最大 / 最小 | 596,956 / 1,647 | 596,956 / 1,647 | 一致 |
| 動画長 平均 / 最大 / 最小 | 649s / 1,410s / 86s | 649s / 1,410s / 86s | 一致 |
| チャンネル上位 5 | キヨキヨ 8 ほか | 同一 | 一致 |
| 上位動画 5 件 | — | 同一 | 一致 |

### 3.2 調査ページ YouTube 節（クエリ「CBD リキッド」）の数値照合

出所 run = `20261009T065307Z-youtube-cbd-dated`（`records.json` 24 件、2026-10-09 06:53 収集）。
同時刻帯に同一クエリの再取得 run `20261009T160738Z-youtube-cbd-dated`（30 件）があり、
ページは 24 件側を出所とする。

| 指標 | ページ記載 | 再計算（24 件） | 判定 |
|---|---:|---:|---|
| ユニーク動画数 | 24 | 24 | 一致 |
| 投稿日範囲 | 2019-12-20 〜 2026-09-17 | `run_metadata.date_range` と一致 | 一致 |
| 再生数 平均 | 59,102 | 59,102 | 一致 |
| 再生数 中央値 | 22,303 | **21,826** | **不一致**。22,303 は観測値の 13 番目で、中央 2 値の平均ではない |
| 再生数 最大 / 最小 | 598,005 / 240 | 598,005 / 240 | 一致 |
| チャンネル上位 5/上位動画 5 件 | — | 同一 | 一致 |

---

## 4. 調査ページへの反映

`publication/research_cbd.html` を次のように訂正した（詳細は同ファイルの `出所` / `照合` 行）。

- X 節: 収集期間を観測値（2026-10-01、08:52〜20:14 UTC）に一致させ、検索窓の記載を撤回。
  raw の所在（データセット内パス）と分類結果の出所を明記。
- YouTube 節（「CBD オイル」）: 出所 run を記述で示し、`23 件` は別取得であることを明示。
  中央値を母集団（ユニーク 28 件）に合わせて 14,228 に訂正。
- YouTube 節（「CBD リキッド」）: 出所 run を記述で示し、中央値を 21,826 に訂正。
- 最終更新日を 2026-10-15 に更新し、変更理由をページ内に記録。

### 4.1 run_id をページに直接書かない理由（PC-2）

公開ページに現れる run_id は `audit-publication` の PC-2 が監査する。PC-2 は
「値の出所 run はカタログ済み raw メタデータまたは committed staging 宣言に解決できなければ
ならない」とし、解決できない参照を finding にする
（`src/validation/publication_contract.py` の `_catalog_run_ids` / `_RUN_ID_RE`）。

X / YouTube の raw は `.gitignore`（`**/data/raw/*`）により非追跡で、リポジトリの
カタログに存在しない（`docs/collection-gap-analysis.md` §2-2 の G6）。
したがってこれらの run_id をページに書くと恒久的に PC-2 finding になる。
research_cbx.html も同じ理由で、YouTube データは run_id ではなく派生レポート
（`research/youtube/…`）と宣言を引いている。

**決定:** ページには raw の所在（データセット内パス）・ファイル名・収集日を書き、
run_id は本記録に置く。これでページの数値は追跡可能なままで、PC-2 は 0 findings を保つ。

## 5. 本記録で扱わない事項

- **YouTube 旧10年系列**は証拠・公開対象外として `ISS-20261012-CBD-003` で RESOLVED（2026-10-16）。補完・再取得は行わず、本記録では扱わない。
- **Google Trends 5 年 raw の欠落**は `ISS-20261012-CBD-004` の対象。
- **マトリックスのカバレッジ表示**は `ISS-20261012-CBD-001` で訂正した（2026-10-15。表1a・表3・表6）。
- COA の出所照合は `ISS-20261012-CBD-005`（2026-10-15 RESOLVED）。

---

*この記録は `docs/reports/` の報告書であり、issue レコードではない。*
