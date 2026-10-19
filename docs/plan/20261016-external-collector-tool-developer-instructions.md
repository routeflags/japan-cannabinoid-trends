# 2026-10-16 plan — GT / YouTube 収集ツール外部化 開発指示書

**状態:** 開発指示案（2026-10-16）。本ファイルは、別リポジトリで Google Trends（GT）と YouTube の同等収集機能を持つツールを開発するための指示書である。  
**用途:** 既存リポジトリ内スクリプトとスキルの機能・運用法を開発者へ伝え、外部ツール完成後に既存スクリプトを安全に削除・置換できるようにする。  
**非目的:** 本書は収集を実行しない。raw / interim / processed / publication データを変更しない。既存スクリプトを今すぐ削除しない。APIキー・トークン・MCP設定の実値を保存しない。

## 1. 背景と目的

このリポジトリには、Google Trends と YouTube の収集に関する複数の経路が存在する。

- Google Trends:
  - MCP 経由の `google-trends-mcp`
  - repository pipeline 経由の live guard
  - recorded MCP payload を採用する adapter / boundary
- YouTube:
  - YouTube Data API v3 を直接叩く shell scripts
  - Apify YouTube Search / Scraper skills
  - youtube-mcp セットアップ案

今後、これらと同等以上の機能を持つ収集ツールを**別リポジトリ**で開発する。新ツール完成後、このリポジトリ内の個別収集スクリプトは削除対象になる。削除前に、現行機能・運用・制約・置換条件を本書で固定する。

目的:

1. 開発者が既存スクリプト・スキルの機能を取りこぼさない。
2. 新ツールが raw data rule、run metadata、provenance、missing data の扱いに反しない。
3. 既存スクリプト削除時に、どの機能が置換済みか判断できる。
4. 秘密情報をリポジトリに入れず、環境変数・MCP設定をローカル管理に留める。
5. 後続エージェントが「どのツールを使えばよいか」で迷わない。

## 2. 既存ファイルの記録（削除対象候補）

以下は現在このリポジトリに存在する収集関連ファイルであり、外部ツールが同等機能を提供した後に削除・置換対象になり得る。**現時点では削除しない。**

### 2.0 削除対象ファイル台帳

外部ツール完成後、まず削除候補になるのは「provider API / MCP / curl を直接実行する収集入口」である。adapter / boundary / skill / setup guide は、外部ツールへの移行状況に応じて削除ではなく更新・縮退・参照化する可能性があるため、削除種別を分けて管理する。

| 種別 | repository path | 絶対パス | 削除条件 | 備考 |
|---|---|---|---|---|
| primary deletion candidate | `scripts/collection/google-trends-live-guard.py` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collection/google-trends-live-guard.py` | 外部ツールが Google Trends live probe / fetch / bounded logging / run metadata 出力を提供し、skill が外部ツール利用へ更新済み | repository pipeline 経由の live guard。削除時は代替 CLI を migration note に記録 |
| primary deletion candidate | `scripts/collect-youtube-japanese-keywords.sh` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collect-youtube-japanese-keywords.sh` | 外部ツールが YouTube Data API v3 の絶対日付範囲検索、pagination、quota logging、run metadata 出力を提供済み | `YOUTUBE_API_KEY` を読む直接 curl script。raw へ直接書くため優先置換対象 |
| primary deletion candidate | `scripts/collect-youtube-japanese-keywords-remaining.sh` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collect-youtube-japanese-keywords-remaining.sh` | 外部ツールが残キーワード再収集を通常の parameterized run として表現できる | 固定 run path / 固定 keyword の一回限り再収集 script。外部ツール化後は不要 |
| migration / possible deletion | `docs/specs/youtube-mcp-setup-guide.md` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/docs/specs/youtube-mcp-setup-guide.md` | YouTube Data API backend の利用手順が外部ツール側 docs に移り、このリポジトリ側 skill が外部ツールだけを案内する | すぐ削除せず、外部ツールへの参照 guide に縮退する選択肢あり |
| migration / possible deletion | `.github/skills/research-google-trends/SKILL.md` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/.github/skills/research-google-trends/SKILL.md` | skill を外部ツール repo 側へ移す、またはこの repo で外部ツール facade の案内だけに置換する owner 決定後 | 削除より更新の可能性が高い。使用判断・解釈注意は残す価値がある |
| migration / possible deletion | `.github/skills/apify-youtube-search/SKILL.md` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/.github/skills/apify-youtube-search/SKILL.md` | Apify Search backend の直接呼び出し説明を外部ツールへ移し、skill の役割を backend 選択案内へ縮退または移管済み | token / REST endpoint 直叩き例は削除対象 |
| migration / possible deletion | `.github/skills/apify-youtube-scraper/SKILL.md` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/.github/skills/apify-youtube-scraper/SKILL.md` | Apify Scraper backend の直接呼び出し説明を外部ツールへ移し、skill の役割を backend 選択案内へ縮退または移管済み | rolling dateFilter / ISO date 注意は外部ツール docs へ移す |
| do not delete until adapter replacement | `src/collection/adapters/google_trends/` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/` | repository collection pipeline が外部ツール出力を採用する adapter に置換され、既存 raw runs の replay / boundary tests が不要または移行済み | adapter / boundary は既存 raw provenance と tests に関係する可能性があるため、script より後に判断 |
| do not delete until adapter replacement | `src/collection/adapters/youtube/` | `/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/youtube/` | Apify CSV / request adapter の役割を外部ツール出力 adapter が置換し、既存 tests / processed flows が移行済み | provider raw 変換ロジックを含むため、先に外部ツール側 fixture tests が必要 |

削除時の必須記録:

- 削除するファイル。
- 代替する外部ツールのコマンド。
- 代替ツールの version。
- 旧スクリプトが担っていた入力・出力・metadata がどこへ移ったか。
- 既存 raw run の再現性に影響がないこと、または影響を limitations として記録したこと。

### 2.1 Google Trends

主な実行入口:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collection/google-trends-live-guard.py
```

関連 adapter / boundary:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/adapter.py
```

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/boundary.py
```

その他関連:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/mcp_session.py
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/live_guard.py
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/google_trends/compiler.py
```

### 2.2 YouTube

主な shell scripts:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collect-youtube-japanese-keywords.sh
```

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/scripts/collect-youtube-japanese-keywords-remaining.sh
```

関連 adapter:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/youtube/apify_csv.py
```

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/src/collection/adapters/youtube/request.py
```

関連 setup guide:

```text
/Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends/.delta/worktrees/vh46w1znw6bm/japan-cannabinoid-trends/docs/specs/youtube-mcp-setup-guide.md
```

## 3. 既存スキルが要求している機能

### 3.1 Google Trends skill

対象 skill:

```text
.github/skills/research-google-trends/SKILL.md
```

要求機能:

| 機能 | 既存 skill の要求 | 新ツール要件 |
|---|---|---|
| interest over time | `interest_over_time`。検索興味度の時系列、0–100 の相対指数 | keyword / terms、geo、timeframe を受け、時系列を保存 |
| compare terms | `compare_terms`。2–5語比較 | 最大5語程度の比較を同一スケールで記録 |
| related queries | `related_queries` | 関連語と上昇語を保存できること |
| trending now | `trending_now` | 任意実装。ただし skill 互換を考えるなら対応 |
| interest by region | `interest_by_region` | geo内地域の興味度。任意だが interface を予約 |
| run metadata | keyword、geo、timeframe、study_id、run_id、collection_timestamp | 必須 |
| 低ボリューム対応 | keyword を広げる、期間延長、比較で相対化 | 0件 / 不安定値を failure と混同しない |

重要制約:

- Google Trends は絶対検索数ではない。0–100 の相対指数である。
- 同じ query + parameters でも結果が変動し得る。
- observed zero、missing、collection failed を区別する。
- relative timeframe（例 `today 12-m`）は request 条件であり、観測された日付範囲とは別に記録する。

### 3.2 YouTube Apify Search skill

対象 skill:

```text
.github/skills/apify-youtube-search/SKILL.md
```

Actor:

```text
gJvjeCYNraSfhIaNd / danek/youtube-search
```

要求機能:

| 機能 | 既存 skill の要求 | 新ツール要件 |
|---|---|---|
| keyword search | `search_term` 必須 | keyword / query を受けて動画検索 |
| max videos | `max_videos` 必須、上限100 | 取得上限を明示し metadata に保存 |
| output fields | videoId、title、channel、duration、views、thumbnail、badges 等 | 取得できる範囲を raw payload と parsed record の両方で保存 |
| cost tracking | Apify run の `usageTotalUsd` | 有料 backend の場合は cost / usage を metadata に保存 |
| API fallback | MCP不調時に Apify REST API | backend 実装を抽象化し、MCP / REST を選べるようにする |

注意:

- `timestamp` が相対表記の場合がある。絶対日付として扱わない。
- 1実行1キーワードが基本。複数キーワードは複数 run として分ける。
- API token は `.env.d/apify.env` または環境変数から読む。DB・log・metadata に値を出さない。

### 3.3 YouTube Apify Scraper skill

対象 skill:

```text
.github/skills/apify-youtube-scraper/SKILL.md
```

Actor:

```text
h7sDV53CddomktSi5 / streamers/youtube-scraper
```

要求機能:

| 機能 | 既存 skill の要求 | 新ツール要件 |
|---|---|---|
| searchQueries | 複数 query 可 | 複数 query を個別 run または明示的 batch として扱う |
| dateFilter | hour / today / week / month / year | rolling window であることを metadata に明記 |
| sortingOrder | relevance / rating / date / views | request parameter として保存 |
| maxResults | 件数上限 | metadata に保存 |
| absolute date | output の `date` は ISO8601 | observed field として保存 |
| oldestPostDate | channel URL 専用。検索 query では絶対上下限不可 | UI / CLI で誤用を拒否または warning |

重要制約:

- `dateFilter="month"` は暦月ではなく rolling 30 days として扱う。
- `oldestPostDate` は channel URL 専用で、keyword search の絶対日付範囲には使わない。
- 絶対日付上下限が必要なら YouTube Data API v3 を使う。

### 3.4 youtube-mcp / YouTube Data API v3 setup

対象 guide:

```text
docs/specs/youtube-mcp-setup-guide.md
```

要求機能:

| 機能 | 既存 guide の要求 | 新ツール要件 |
|---|---|---|
| search_videos | query、published_after、published_before、max_results | 絶対日付範囲検索に対応 |
| get_video_details | videoId 詳細取得 | search 結果の補完に使えるようにする |
| get_trending_videos | region_code | 任意。ただし interface を予約 |
| quota accounting | search.list = 100 units | quota 消費を metadata / report に保存 |
| API key | `YOUTUBE_API_KEY` | 秘密情報を保存・出力しない |

既存 shell scripts は YouTube Data API v3 を直接呼び、`publishedAfter` / `publishedBefore` を使って年次・期間指定検索を行っている。新ツールは、この直接 API 経路を第一級 backend として扱うこと。

## 4. 新ツールの機能要件

### 4.1 共通 CLI

別リポジトリのツールは、少なくとも次の CLI を持つ。

```text
collector-tool gt interest-over-time --keyword ... --study-id ... --geo JP --timeframe "today 12-m" --output-dir ...
collector-tool gt compare --terms ... --study-id ... --geo JP --timeframe ...
collector-tool gt related-queries --keyword ... --study-id ... --geo JP

collector-tool youtube search --backend youtube-data-api --query ... --published-after ... --published-before ... --max-results ...
collector-tool youtube search --backend apify-search --query ... --max-videos ...
collector-tool youtube search --backend apify-scraper --query ... --date-filter month --max-results ...
collector-tool youtube video-details --video-id ...

collector-tool validate-run --run-dir ...
collector-tool summarize-run --run-dir ...
```

CLI は dry-run / plan-only を持つこと。

```text
--dry-run
--plan path/to/request.json
--output-dir datasets/<study-id>/data/raw/<source>/
--run-id YYYYMMDDTHHMMSSZ-...
--now 2026-10-16T00:00:00Z
--format json
```

### 4.2 Python API

CLI の内部 API は、後続エージェントが直接 provider API を叩かずに済む facade にする。

```python
collect_google_trends(request: GoogleTrendsRequest) -> CollectionResult
collect_youtube(request: YouTubeRequest) -> CollectionResult
validate_run(run_dir: Path) -> ValidationResult
```

実装方針:

- provider 固有処理は adapter に閉じ込める。
- output schema と run metadata は provider 非依存の facade が作る。
- raw payload は改変せず保存する。
- parsed / normalized record は raw と別ファイルにする。
- collection failure は failure artifact として保存し、observed zero に変換しない。

### 4.3 Backend 抽象化

| source | backend | 用途 | 秘密情報 |
|---|---|---|---|
| Google Trends | google-trends-mcp | 相対検索指数 | 原則不要 |
| YouTube | youtube-data-api-v3 | 絶対日付範囲検索、動画詳細 | `YOUTUBE_API_KEY` |
| YouTube | apify-youtube-search | 軽量 keyword search | `APIFY_TOKEN` |
| YouTube | apify-youtube-scraper | ISO8601 date field、rolling dateFilter | `APIFY_TOKEN` |

backend 選択は request metadata に必ず残す。

## 5. 出力仕様

### 5.1 raw run layout

出力先は source ごとに分ける。

```text
datasets/<study-id>/data/raw/<source>/<run-id>/
├── request.json
├── raw_payload.json
├── records.json
├── run_metadata.json
├── collection_log.json
└── errors.json              # failure / partial の場合のみ
```

複数 query / 複数ページ / 複数 backend の場合:

```text
datasets/<study-id>/data/raw/<source>/<run-id>/
├── request.json
├── pages/
│   ├── page_001_raw.json
│   └── page_002_raw.json
├── records.json
├── run_metadata.json
└── collection_log.json
```

### 5.2 run_metadata 必須項目

| 項目 | 必須 | 説明 |
|---|---:|---|
| `run_id` | yes | `YYYYMMDDTHHMMSSZ-source-study-or-slug` |
| `source` | yes | `google-trends` / `youtube` |
| `backend` | yes | `google-trends-mcp` / `youtube-data-api-v3` / `apify-youtube-search` / `apify-youtube-scraper` |
| `study_id` | yes | study |
| `collection_timestamp` | yes | 実行時刻 |
| `request` | yes | query / geo / timeframe / publishedAfter / publishedBefore / maxResults 等 |
| `observed_period` | when available | payload から観測された範囲。request 条件と混同しない |
| `collector_version` | yes | 外部ツールの version |
| `provider_version` | when available | MCP / Actor / API version |
| `raw_record_count` | yes | raw item count。不明なら null |
| `deduplicated_record_count` | if deduped | dedupe 後 count |
| `status` | yes | `observed_nonzero` / `observed_zero` / `missing` / `collection_failed` / `partial` / `unknown` |
| `errors` | when failure | error code / message。秘密情報は含めない |
| `cost` | if paid backend | usageTotalUsd / quota units |

### 5.3 Google Trends record

Google Trends は provider の raw response を保存したうえで、最低限次を parsed record として出す。

```json
{
  "term": "CBX リキッド",
  "geo": "JP",
  "timeframe": "today 12-m",
  "date": "2026-10-01",
  "value": 42,
  "unit": "relative_interest_0_100"
}
```

注意:

- `value` は絶対検索数ではない。
- 比較 run の場合、同一 run 内の terms は共通スケールであることを metadata に明記する。
- request timeframe と observed date range を分ける。

### 5.4 YouTube record

YouTube は backend ごとの差を保持しつつ、共通 record を出せるようにする。

```json
{
  "video_id": "MSzIYGWRXbE",
  "url": "https://www.youtube.com/watch?v=MSzIYGWRXbE",
  "title": "...",
  "channel_id": "...",
  "channel_title": "...",
  "published_at": "2026-09-01T00:00:00Z",
  "published_at_precision": "timestamp | date | relative_text | unknown",
  "views": 1040971,
  "duration_seconds": 95,
  "source_backend": "youtube-data-api-v3"
}
```

注意:

- Apify Search の相対 timestamp は `published_at_precision="relative_text"` とし、絶対日付に変換したように見せない。
- YouTube Data API v3 の `publishedAt` は絶対 timestamp として保存できる。
- Shorts / streams の扱いは request metadata に残す。

## 6. 運用法

### 6.1 実行前

1. 研究計画または task/issue から query・期間・study_id・source を確認する。
2. backend を選ぶ。
   - Google Trends → `google-trends-mcp`
   - YouTube 絶対日付範囲 → `youtube-data-api-v3`
   - YouTube 軽量 keyword search → `apify-youtube-search`
   - YouTube rolling date filter / ISO8601 date field → `apify-youtube-scraper`
3. API key / token は環境変数か local `.env.d/*.env` で供給する。
4. dry-run で request と output path を確認する。

### 6.2 実行中

- provider response は raw として保存する。
- page / pagination / retry を log に残す。
- API key / token は stdout / stderr / metadata / log に出さない。
- timeout / rate limit / quota exceeded は `collection_failed` または `partial` として記録する。
- 成功 run と失敗 run を同じ run_id で上書きしない。

### 6.3 実行後

1. `run_metadata.json` の必須項目を検査する。
2. raw count と parsed count を確認する。
3. date range / timeframe / query / backend を確認する。
4. duplicate がある場合、dedupe rule と removed count を記録する。
5. 収集結果をこのリポジトリへ取り込む場合は、既存の staging declaration / collection pipeline を使う。外部ツールが adoption を判断しない。

## 7. スキル連携

外部ツール完成後、既存スキルは直接 provider API や古い shell script を案内せず、外部ツールの facade を案内する。

### 7.1 Google Trends skill の置換方針

現行:

- OpenCode MCP tool を直接呼ぶ
- `google-trends-live-guard.py` を使う

置換後:

```text
collector-tool gt interest-over-time --keyword ... --study-id ... --geo JP --timeframe ...
collector-tool gt compare --terms ... --study-id ... --geo JP --timeframe ...
collector-tool gt related-queries --keyword ... --study-id ... --geo JP
```

skill には次を残す。

- いつ Google Trends を使うか
- keyword / geo / timeframe の決め方
- 相対指数の解釈
- low-volume query 対応
- output の読み方

skill から削る。

- provider 固有の MCP 呼び出し詳細
- raw 保存の手書き手順
- shell script 相当の疑似実装

### 7.2 YouTube skill の置換方針

現行:

- Apify actor を直接呼ぶ
- YouTube Data API v3 shell script を実行する
- youtube-mcp setup を参照する

置換後:

```text
collector-tool youtube search --backend youtube-data-api --query ... --published-after ... --published-before ...
collector-tool youtube search --backend apify-search --query ... --max-videos ...
collector-tool youtube search --backend apify-scraper --query ... --date-filter month ...
```

skill には次を残す。

- backend 選択基準
- 料金・quota の注意
- 相対日付と絶対日付の違い
- public / private / redistribution の注意
- output の読み方

skill から削る。

- `curl` 直叩き例
- token を source する手順
- actor 固有の REST endpoint 詳細
- repo 内 shell script の案内

## 8. 削除条件

既存スクリプトは、次の条件をすべて満たすまで削除しない。

1. 外部ツールが GT / YouTube の必要 backend を実装している。
2. 外部ツールが `run_metadata.json`、raw payload、parsed records、collection log を出力する。
3. 失敗・partial・observed_zero・missing を区別できる。
4. 秘密情報を log / metadata / stdout に出さない。
5. dry-run / validate-run がある。
6. 既存スキルが外部ツール利用へ更新されている。
7. 旧スクリプトから外部ツールへの migration note がある。
8. 少なくとも1件の non-sensitive fixture / sample run で検証済み。
9. このリポジトリ側の adoption は従来通り staging declaration / collection pipeline が担う。

削除時は、削除理由と代替コマンドを changelog または issue に記録する。

## 9. テスト・受け入れ条件

### 9.1 Unit / contract tests

- request → run_id / output path が deterministic。
- required metadata 欠落で validation failure。
- API key / token が output に混入しない。
- Google Trends relative timeframe と observed range を分けて記録。
- YouTube relative timestamp を絶対日付に偽装しない。
- pagination / retry / quota exceeded を log に残す。

### 9.2 Fixture tests

外部 API を叩かない fixture を用意する。

- Google Trends MCP response fixture
- YouTube Data API v3 search response fixture
- Apify Search dataset fixture
- Apify Scraper dataset fixture
- failure response fixture

### 9.3 Integration tests

実 API を叩くテストは opt-in にする。

```text
RUN_LIVE_COLLECTION_TESTS=1
YOUTUBE_API_KEY=...
APIFY_TOKEN=...
```

CI の通常テストでは live collection を実行しない。

## 10. 秘密情報・環境変数

環境変数:

| 変数 | 用途 | 保存先 |
|---|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 | local `.env.d/youtube.env` または CI secret |
| `APIFY_TOKEN` | Apify actors | local `.env.d/apify.env` または CI secret |

禁止:

- `.env` / `.env.d/*.env` を commit しない。
- token を log / metadata / exception message に出さない。
- token を run_metadata に保存しない。
- token を task DB や issue body に書かない。

テンプレートは key 名だけにする。

```text
YOUTUBE_API_KEY=
APIFY_TOKEN=
```

## 11. 既存リポジトリとの接続

外部ツールは、このリポジトリの source of truth を置き換えない。

| 項目 | このリポジトリ側 | 外部ツール側 |
|---|---|---|
| study definition | `datasets/<study-id>/README.md` / `methodology.md` | 参照するだけ |
| raw adoption | staging declaration / collection pipeline | raw candidate を出すだけ |
| validation | `make audit-new-runs` / gates | validate-run は事前検査 |
| publication | publication gate | 実行しない |
| issue / task | docs/issues / task manager | path / ID 参照のみ |

外部ツールは「収集 producer」であり、adoption / publication / release の owner ではない。

## 12. 開発タスク分解

### Step 1: CLI / request schema

- GT / YouTube の request model を定義。
- backend enum を定義。
- dry-run を実装。

受け入れ条件:

- request JSON が保存できる。
- run_id が指定または生成できる。
- output path が dry-run で確認できる。

### Step 2: Google Trends backend

- `google-trends-mcp` を呼ぶ adapter。
- interest-over-time / compare / related-queries。
- raw payload + parsed records + metadata。

受け入れ条件:

- fixture で parse test が通る。
- relative index と absolute count を混同しない。

### Step 3: YouTube Data API backend

- `search.list` with `publishedAfter` / `publishedBefore`。
- pagination。
- quota units logging。

受け入れ条件:

- fixture で absolute publishedAt を保存できる。
- quota exceeded を `collection_failed` または `partial` として記録できる。

### Step 4: Apify backends

- apify-youtube-search。
- apify-youtube-scraper。
- cost / actor run id / dataset id logging。

受け入れ条件:

- token が output に出ない。
- relative timestamp と ISO date の違いを保持する。

### Step 5: validation / summary

- validate-run。
- summarize-run。
- required metadata / missing / partial / duplicate / date range を確認。

受け入れ条件:

- missing metadata を failure として返す。
- observed_zero と collection_failed を区別する。

### Step 6: skill migration docs

- `research-google-trends` skill の外部ツール利用版。
- YouTube skills の外部ツール利用版。
- 旧 scripts 削除 migration note。

受け入れ条件:

- skill が provider API 直叩きを案内しない。
- 代替 CLI が明記されている。

## 13. Owner 判断事項

1. 外部ツールのリポジトリ名・配布方法（Python package / standalone binary / Docker）。
2. このリポジトリから呼ぶ方法（Makefile target を追加するか、手動運用に留めるか）。
3. raw candidate を外部ツールが直接 `datasets/` に書くか、export bundle として渡すか。
4. Google Trends の live collection を通常運用で許可する条件。
5. YouTube backend の優先順位（Data API v3 / Apify Search / Apify Scraper）。
6. 既存 shell scripts の削除タイミング。
7. skills をこのリポジトリに残すか、外部ツール側に移すか。
