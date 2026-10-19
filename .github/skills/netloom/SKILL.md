---
name: netloom
description: |
  第三者 API（Google Trends / Apify / X API v2 / GA4 / GSC / news / article / cache / contact / ga4-orders）への接続を netloom に集約するスキル。
  Google Trends はキーワード・地域・期間を指定して検索興味度（0–100 の相対指数）を取得し、
  2–5 語の相対比較も 1 回の呼び出しで取る。Apify は任意の actor を実行して dataset を読む。
  X API v2 は検索（直近 7 日 / 全期間）と投稿 1 件を取る。
  GA4 は Google Analytics Data API（HTTP）からレポート・リアルタイム・メタデータを取る
  （1 コマンド = 認証 1 + データ 1 の 2 往復。credential は Google の refresh grant）。
  GSC（Google Search Console）は searchAnalytics のクエリとプロパティ一覧を取り、netloom 自身が
  トークンを交換する（1 コマンド = 認証 1 + データ 1 の 2 往復）。
  news / cache は EC-CUBE 自サイトのニュース API（CRUD・サムネイル画像）とキャッシュクリアを扱い、
  article はガイド記事 API（CRUD・画像とそのメタデータ）を扱う（`--env dev|prod`。
  本番への書き込みは `--allow-prod-write` が要る）。
  contact はお問い合わせ API（CRUD。PII を含む）、ga4-orders は GA4 受注同期 API（CRUD。
  GA4 Data API の ga4 とは別物。売上データを含む）を扱う（同じ `--env dev|prod`）。
  openseo はローカル Docker の OpenSEO MCP（HTTP）からプロジェクト一覧・キーワードメトリクス・
  ランクキーワード・ドメイン概観・SERP 競合を取る（1 コマンド = 1 往復。credential 不要。Docker は呼び出し側）。
  gmail は既存の Gmail MCP サーバー（stdio）からメールを送る（1 コマンド = 1 MCP 往復。
  **送信は副作用**。OAuth はサーバー側で、netloom は credential を読まない）。
  meta-page / meta-instagram は Meta Graph API（Facebook Page / Instagram）から投稿・インサイトを取る
  （送信元を 2 つに分ける: Page 側は PAGE_TOKEN、Instagram 側は USER_TOKEN。1 コマンド = 1 往復。
  ページングは呼び出し側が応答の paging.next で回す）。
  mysql は EC-CUBE の MySQL を SSH トンネル経由で **読み取り専用**で見る
  （`mysql tunnel` でトンネルを起動（冪等）・`mysql tunnel-status` で状態・`mysql query --sql 'SELECT …'` で 1 文 = 1 往復。
  書き込みは無い。証跡はカセットに残り `--replay` でオフライン再現できる）。
  bigquery は BigQuery の**読み取り専用クエリ**を jobs.query の REST で直接実行する
  （`bigquery query --sql 'SELECT …' [--dry-run] [--max-rows N] [--project ID]`。**1 コマンド = 認証 1 + クエリ 1 の 2 往復**。
  `SELECT` / `WITH … SELECT` だけ。書き込みは無い。**BigQuery は課金が発生しうる**: まず `--dry-run`（課金なしの見積もり）。
  project は `--project` → `GOOGLE_CLOUD_PROJECT` → `GCLOUD_PROJECT`。証跡はカセットに残り `--replay` でオフライン再現できる）。
  calendar は Google Calendar API v3 からカレンダーと予定を扱う
  （`calendar list-calendars|list-events|get-event|create-event|update-event|delete-event`。**1 コマンド = 認証 1 + データ 1 の 2 往復**。
  **書き込み 3 つは副作用**（予定が作られる / 置き換えられる / 消える）— live の書き込みは owner 承認が前提。
  `update-event` は PATCH = 1 往復。calendar id は `--calendar-id` → `GOOGLE_CALENDAR_ID` → `primary`。証跡はカセットに残り `--replay` でオフライン再現できる）。
  apps-script は Google Apps Script API v1 からプロジェクト・ソース・バージョン・デプロイ・プロセスを扱い、任意の関数を実行する
  （`apps-script create-project|get-project|get-project-content|update-project-content|list-project-versions|create-version|list-deployments|get-deployment|create-deployment|update-deployment|delete-deployment|run-script|list-processes`。**1 コマンド = 認証 1 + データ 1 の 2 往復**。
  **書き込み 7 つと run-script は副作用** — とくに run-script は任意の関数を実行する（メール・シート等が起こりうる）。live は owner 承認が前提。
  script id は `--script-id`（推測しない）。証跡はカセットに残り `--replay` でオフライン再現できる）。
  site は自サイト（EC-CUBE）の**死活監視とデバッグ**を担う
  （`site check --env local|dev|prod --target front|mypage|admin|all`。Basic → CSRF 抽出 → ログイン POST → セッション確立 → 本リクエストを内部化し、
  各 URL の判定（200 を基本、保護ページの未ログイン 302 → ログインは正常、それ以外とエラー画面は NG）/ 応答時間 / 失敗段（basic·csrf·login·session·request）を一覧と `--format json` で返す。
  **1 コマンド = 面の URL 数 + ログイン段数（+ リダイレクトの hop）の往復**。exit 0 = 全件 OK / 1 = 1 件以上 NG / 2 = 前提不足。証跡はカセットに残り `--replay` で credential 無しに再現できる）。
  psi / crux は**非公開 API**（issue #24: 既定の導線に出さない。consumer の測定系 = ローカル Lighthouse が正で、明示指示があるときだけ使う。置き換えを意図しない）:
  psi は PageSpeed Insights API v5 からページの Lighthouse 測定を取り、crux は Chrome UX Report API v1 から実ユーザーのメトリクス（日次 / 履歴）を取る
  （`psi run --url URL [--strategy mobile|desktop] [--categories a,b,c]` / `crux query --origin ORIGIN | --url URL [--form-factor PHONE|DESKTOP|TABLET] [--metrics M1,M2]` /
  `crux history --origin ORIGIN | --url URL [--form-factor …] [--collection-periods N]`。**1 コマンド = 1 往復**。
  **credential は query の `key`**（`PAGESPEED_API_KEY` / `CRUX_API_KEY`。同じ値でも変数名は両方設定する。未設定なら 1 往復も送らず exit 2、`--replay` でも要る）。
  **キーはカセットの URL に残るので `.cassettes/` のみ・コミットしない**。**PSI は quota を消費する**。**キャッシュ回避は呼び出し側**（URL にダミーのクエリを付ける等。netloom は URL をそのまま送る）。
  **ローカル Lighthouse とは別測定系**（数値を混ぜて比較しない）。csv は無い。
  auth google はローカルコマンド（対話専用の Google OAuth 同意フロー）で、ブラウザ同意から
  トークンファイル（$HOME/.config/netloom/google-<source>.json、0600）を書き、GSC と GA4 はそのファイルを
  GOOGLE_TOKEN_FILE で読める（値は stdout / stderr / カセットに出ない）。
  交換の証跡（2 frame）は `--cassette FILE` で caller の記録置き場に置ける（例: `data/gsc/cassettes/<YYYYMMDD>-auth-gsc.jsonl`。issue #22）。
  すべての往復は VCR カセットに残り、カセットからオフライン再現できる（証跡付きの収集）。
netloom-version: 0.4.3
---

# netloom（第三者 API の収集プロキシ）

このスキル自身は netloom のバイナリに埋め込まれている（正本は `internal/usecase/skill/netloom/SKILL.md`）。配布と確認は `netloom skill install` / `netloom skill check` で行い、手でコピーしない（CI の 1 ステップと複数 checkout への一括配布は下の「このスキルの配布」、README「スキルの配布」）。

第三者のデータ取得は netloom のコマンドだけで行う。provider の MCP サーバーを直接叩いたり、
actor を curl で呼んだりしない（証跡とオフライン再現が失われるため）。

`--replay` は同じ request の記録が複数あるとき、**その request の n 回目の要求に n 番目の記録**で答える（記録を順に消費する。**その request の記録を使い切ったら最初の記録** = issue #14 の規則）。site の mypage のように **1 コマンドが同じ URL を複数回要求する flow** はこの規則で live と同じ判定になる（設計書 §5.1）。**新しい証跡で再現したいときは `--cassette` を分ける**（`--cassette <新しいファイル>` で記録し、そのカセットを `--replay` する）。

同じ request を `--cassette` で 2 回記録すると、**追記の前に stderr へ 1 行で知らされる**（`netloom: <file> already holds a record for this request: a replay answers with the first one`。値は出ない。初回記録・`--replay` では出ない。通知は答えを変えない — 答えは §5.1 の規則（その request を 1 回だけ要求するコマンドでは最初の記録）が決める。issue #17）。
**カセットの検査はコマンドで行う**: `netloom cassette show --path FILE`（frame 一覧。payload 本文は出さず sha256 とバイト数で示す）と `netloom cassette check --path FILE [--path FILE ...] [--env-file FILE]` — **live 実行後のレダクト検査はこのコマンドにする**（手作業の grep ではなく。env の実値をレダクタと同じ値の集合から**変数名と件数だけで**数え、ヒット 1 件でもあれば exit 1 / credential が 1 つも解決できなければ exit 2。`grep -Fc '\[REDACTED\]'` のように -F なのにエスケープを付けると「0 件」の誤検知を起こす — issue #18 の実測。設計書 付録 A.28）。

netloom は起動時に **cwd の env ファイルを自動で読む**（`<cwd>/.env` → `<cwd>/.env.d/*.env` の順。`NETLOOM_ENV_FILE` で明示もできる — **1 つ、または `:` 区切りで複数**（`a.env:b.env`。全部を順に読み、先に定義されたものが勝つ。issue #25）。探索順・構文は設計書 §7.5）。だから **`set -a; source .env.d/xxx.env; set +a` を書かなくてよい**（書いてあっても動く）。**プロセスの環境変数が常に勝つ**ので、後から `export KEY=…` した値で上書きできる（値が空の env エントリでも勝つ）。読み込んだ値はこのプロセスの env に入り、**stdout / stderr / カセットには出ない**（レダクトされる — stderr に出るのは読み込んだファイル名と件数の 1 行だけ）。env ファイルは**ワークスペース外か gitignore の場所**に `chmod 600` で置き、コミットしない。

- **Google Trends**（MCP stdio）: `google-trends interest-over-time` / `compare-terms`
- **Apify**（HTTP）: `apify run` / `apify dataset` / `apify run-status`
- **X API v2**（HTTP）: `x search-recent` / `x search-all` / `x tweet`
- **GA4**（HTTP。Google Analytics Data API）: `ga4 run-report` / `ga4 run-realtime-report` / `ga4 get-metadata`（**1 コマンド = 認証 1 + データ 1 の 2 往復**。`--property` または `GA4_PROPERTY_ID`）
- **GSC**（HTTP。Google Search Console）: `gsc query` / `gsc sites`（**1 コマンド = 認証 1 + データ 1 の 2 往復**）
- **news / cache**（HTTP。EC-CUBE 自サイト API）: `news list|get|create|update|delete|image-upload|image-delete` / `cache clear`（**1 コマンド = 1 往復**。`--env dev|prod`）
- **article**（HTTP。EC-CUBE ガイド記事 API）: `article list|get|create|update|delete|image-upload|image-delete`（**1 コマンド = 1 往復**。同じ環境・同じ認証）
- **contact**（HTTP。EC-CUBE お問い合わせ API）: `contact list|get|create|update|delete`（**1 コマンド = 1 往復**。同じ環境・同じ認証。**応答に顧客の PII が入る**）
- **ga4-orders**（HTTP。EC-CUBE GA4 受注同期 API）: `ga4-orders list|get|create|update|delete`（**1 コマンド = 1 往復**。`X-GA4-API-Key` + `GA4_API_KEY`。**GA4 Data API の `ga4` とは別物**。応答に売上が入る）
- **openseo**（HTTP。ローカル OpenSEO の MCP over HTTP）: `openseo list-projects` / `keyword-metrics` / `ranked-keywords` / `domain-overview` / `serp-competitors`（**1 コマンド = 1 往復**。credential 不要。Docker コンテナは呼び出し側が起動・停止する）
- **gmail**（MCP stdio。既存の Gmail サーバーの再利用）: `gmail send-email`（**1 コマンド = 1 MCP 往復**。**送信は副作用** — live は実メールが飛ぶ。OAuth はサーバー側）
- **meta-page / meta-instagram**（HTTP。Meta Graph API v25.0。Facebook Page / Instagram）: `meta-page posts|post|post-insights` / `meta-instagram media|media-insights`（**1 コマンド = 1 往復**。`PAGE_TOKEN` / `USER_TOKEN` は別のトークン。**ページングは回さない**。csv は無い）
- **`auth google`**（ローカルコマンド。provider を呼ばない）: 対話専用の Google OAuth 同意フロー（ループバック + PKCE）でトークンファイルを書く。GSC / GA4 の credential をこのファイルでも渡せる（`GOOGLE_TOKEN_FILE`）
- **site**（自サイトの死活監視。HTTP）: `site check --env local|dev|prod --target front|mypage|admin|all [--product-id ID]`（**1 コマンド = 面の URL 数 + ログイン段数（+ hop）の往復**。**判定を送信元定義に持つ唯一の送信元**。exit 0 / 1 / 2）
- **bigquery**（BigQuery の読み取り専用クエリ。HTTP 直叩き）: `bigquery query --sql SQL|@FILE [--dry-run] [--max-rows N] [--project ID]`（**1 コマンド = 認証 1 + クエリ 1 の 2 往復**。`SELECT` / `WITH … SELECT` だけ。**書き込みは無い**。**BigQuery は課金が発生しうる** — まず `--dry-run`。project は `--project` → `GOOGLE_CLOUD_PROJECT` → `GCLOUD_PROJECT`。`--replay` はネット・credential 無し）
- **calendar**（Google Calendar API v3。HTTP 直叩き）: `calendar list-calendars` / `list-events` / `get-event` / `create-event` / `update-event` / `delete-event`（**1 コマンド = 認証 1 + データ 1 の 2 往復**。**書き込み 3 つは副作用** — live の書き込みは owner 承認が前提。`update-event` は **PATCH = 1 往復**。`list-events` は**与えたフラグだけ**を送る（既定値は発明しない）。calendar id は `--calendar-id` → `GOOGLE_CALENDAR_ID` → `primary`。csv は無い。カセットは予定・参加者を含む — `.cassettes/` のみ・コミットしない。`--replay` はネット・credential 無し）
- **apps-script**（Google Apps Script API v1。HTTP 直叩き）: `apps-script create-project` / `get-project` / `get-project-content` / `update-project-content` / `list-project-versions` / `create-version` / `list-deployments` / `get-deployment` / `create-deployment` / `update-deployment` / `delete-deployment` / `run-script` / `list-processes`（**1 コマンド = 認証 1 + データ 1 の 2 往復**。**書き込み 7 つと run-script は副作用** — live は owner 承認が前提（**run-script は任意の関数の実行**）。script id は `--script-id` 必須（netloom は推測しない。`list-processes` のみフィルタとして任意）。`--files` / `--parameters` は JSON であることだけを見てそのまま送る（**update-project-content は全ファイル置換**）。`pageSize` / `manifestFileName` / `devMode` は**与えたときだけ**送る（既定値は発明しない）。csv は無い。カセットはソースコード・デプロイメント・プロセスを含む — `.cassettes/` のみ・コミットしない。`--replay` はネット・credential 無し）
- **`cassette`**（ローカルコマンド。provider を呼ばない。カセットを読むだけ）: `cassette show --path FILE`（frame 一覧: seq / direction / method or status / url / payload の sha256 とバイト数 / at。**本文は出さない**）と `cassette check --path FILE [--path FILE ...] [--env-file FILE]`（カセットに env の実値が残っていないかを機械検査。**名前と件数だけ**を出して exit 1（ヒット）/ 0（0 件）/ 2（credential が 1 つも無）/ 3（読めない）。読み取り専用 — 往復しない・書き換えない。env の解決は §7.5 と同じ。設計書 付録 A.28）

---

# このスキルの配布（CI での drift 検出と複数 checkout への一括配布）

このスキル自身は netloom のバイナリに埋め込まれている（正本は `internal/usecase/skill/netloom/SKILL.md`。配布済みコピーが `.github/skills/netloom/SKILL.md`）。**手でコピーしない**。古いコピーは `netloom skill check` の exit code で検出できる（一致 = 0 / 不一致 = 1 / ファイルが無い・読めない = 3）。

## CI に 1 ステップ入れて drift を検出する

```yaml
# GitHub Actions（例。private module なので GOPRIVATE と取得の認証が要る）
- run: go install github.com/routeflags/netloom/cmd/netloom@latest
- run: netloom skill check --path .github/skills/netloom/SKILL.md
```

手元（`make install-go` 済み）は同じ 1 行:

```sh
netloom skill check --path .github/skills/netloom/SKILL.md
```

## 複数 checkout への一括配布

```sh
netloom skill install --scan <parent-dir>                  # プレビュー（既定。何も書かない）
netloom skill install --scan <parent-dir> --write          # 一致は UP-TO-DATE、異なるコピーは拒否（exit 1）
netloom skill install --scan <parent-dir> --write --force  # 異なるコピーも置き換える
```

- `<parent-dir>` **自身とその配下**を**辞書順**に走査し、`.github/skills/netloom/SKILL.md` を持つリポジトリだけを対象にする（コピーが無いリポジトリには置かない — 新規導入は `--to`）。**`.git` とシンボリックリンクは辿らず**、深さは**リポジトリで 6 段**まで（`.delta/worktrees/<id>/<repo>` の 4 段は届く）
- 書き込みの規則（プレビュー既定・`--force` 無しの拒否・`UP-TO-DATE` は触らない）は単一 `--to` と同じ。報告は対象ごとに 1 行（`TARGET:` + `STATUS:`。`UP-TO-DATE` / `INSTALLED` / `PREVIEW` / `REFUSED` / `FAILED`）、0 件は `NO TARGETS:` の 1 行で exit 0。どれか拒否 = exit 1、I/O 失敗 = exit 3（最も重いもの）。`--to` と `--scan` は併用できない（exit 2）

---

# Google Trends（2 コマンド）

## いつ使うか（トリガー）

- 「Google Trends のデータを取って」「〈語〉の検索推移を見て」
- 「〈語 A〉と〈語 B〉を検索ボリュームで比較して」
- 「検索興味度を期間指定で」「Google トレンド」

## 前提

- netloom リポジトリの root で作業する（`make build` で `bin/netloom` を作る）。PATH に置くなら
  `make install`（`bin/netloom` へのシンボリックリンク。開発用）か `make install-go`（`go install` で実体。恒久版）で、`make update` が入れ替える
- 入っている版は `netloom version`（`--version` / `-v` も同じ）で確認できる。**版と送信元の確認は `netloom version --json`**（1 行の JSON。`sources` は常に含まれる。`--sources` は 2 行目に id を並べる。同時指定は exit 2）
- live 実行には Node / `npx` が必要（`npx --version` で確認）。**API キーは不要**
- ネットワークが無い・再現したいときは `REPLAY=<カセット>` を使う

## 実行（既定は live）

```sh
# 1 語の推移（既定: live / 構造化 json）
make trends KEYWORD="CBD オイル"

# 期間と出力形式を指定（ファイルへ）
make trends KEYWORD="CBD オイル" TIMEFRAME="today 5-y" FORMAT=csv OUT=/tmp/cbd.csv

# 2–5 語の相対比較（1 回の呼び出し。同一 run 内だけ共通スケール）
make compare TERMS="CBD オイル,CBN オイル"
make compare TERMS="CBD オイル,CBN オイル,カンナビノイド" FORMAT=text
```

| 変数 | 既定 | 値 |
|---|---|---|
| `KEYWORD` | （必須。`trends`） | 検索語 1 つ |
| `TERMS` | （必須。`compare`） | 2–5 語のカンマ区切り |
| `GEO` | `JP` | ISO 3166-1 alpha-2（空 = 全世界） |
| `TIMEFRAME` | `today 12-m` | `today 1-m`（30日）/ `today 3-m`（90日）/ `today 12-m` / `today 5-y`（5年）**この 4 語彙のみ** |
| `FORMAT` | `json` | `json` / `csv` / `text` / `verbatim` |
| `OUT` | （stdout） | 出力ファイル |
| `REPLAY` | （live） | カセットからオフライン再現 |

- `make help` が全ターゲットを表示。stdout は**データのみ**（ビルド表示は stderr）
- 実行ごとに往復が `.cassettes/<UTC>-google-trends-….jsonl` に追記される（stderr にパスが出る）
- バイナリを直接叩く場合は `bin/netloom google-trends interest-over-time --keyword …` /
  `bin/netloom google-trends compare-terms --terms …`（フラグは `--help`）

## 出力形式（`FORMAT`）

| 値 | 内容 | 使いどころ |
|---|---|---|
| `json`（既定） | `{source, tool, geo, timeframe, terms:[{term, average?, series:[{date,value}]}]}` | エージェント / プログラム（jq でそのまま扱える） |
| `csv` | `term,geo,timeframe,date,value` | 表・スプレッドシート |
| `text` | provider の表をそのまま（エスケープなし） | 人が読む |
| `verbatim` | 受信した生バイト | 生データの確認（証跡用） |

`average` は **provider が返したときだけ**入る（`interest_over_time` には無い。計算で埋めない）。

## 値の読み方（誤読しやすい点）

- **0–100 の相対指数**。絶対検索数ではない（系列内の最大が 100）
- **run をまたいだ比較はできない**。語の比較は `compare` の 1 回の呼び出し（共通スケール）だけ
- 週次・日曜開始。`value: 0` は「その週に検索が無かった」で、**収集失敗ではない**
- `timeframe` は**要求条件**。観測された範囲ではない。`today 5-y` は実行時刻基準のローリング 5 年
  （実測: 1-m=31 週 / 3-m=93 週 / 5-y=261 週）

## 証跡とオフライン再現

```sh
# 記録済みカセットから再生（ネットも npx も使わない。request が一致しなければ exit 1）
make trends KEYWORD="CBX リキッド" REPLAY=.cassettes/20261017T144703Z-google-trends-interest-over-time-cbd-オイル.jsonl FORMAT=csv
```

- カセットは**追記のみ。編集・削除しない**（証跡）
- 記録前にレダクトされる（秘密情報の実値は入らない）
- `raw/` にカセットを置かない（呼び出し側の `raw/` は取得データ専用）
- 再現は**記録と同じ request**（keyword/terms・geo・timeframe）でのみ成功する

## 失敗の見分け

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 成功 | — |
| 1 | 失敗・拒否（replay 不一致、ツールがエラー、解釈できない応答） | stderr の 1 行を読む。応答形が変わった可能性は設計の付録 A.7 を確認 |
| 2 | 引数・語彙（timeframe 語彙外、terms が 1 語/6 語、`--replay` と `--cassette` 併用） | 引数を直す |
| 3 | I/O（`--out` に書けない） | パスを直す |
| 124 | timeout（既定 300 秒） | 再実行、または owner に相談 |
| 127 | `npx` 不在 | Node を導入する |

### 失敗を追う（カセットを見る）

実行のたびに往復が `.cassettes/<UTC>-….jsonl` に記録される（**失敗も記録される**）。原因はこのカセットで追える:

```sh
C=$(ls -t .cassettes/*.jsonl | head -1)
jq -r '[.seq,.direction,(.method//.status//.stream//""),(.url//"")]|@tsv' "$C"   # frame 一覧
jq -r 'select(.direction=="recv")
  | (.payload | if type=="string" then (fromjson? // .) else . end) as $p
  | ($p.result.content[0].text // ($p.result.data | arrays | tostring)
     // ($p.data | objects | tostring) // $p.error.message // empty)' "$C"   # 応答 / 失敗理由
grep -nE 'Bearer [^[]|apify_api_[A-Za-z0-9]' "$C"            # 実値の形を探す（Authorization という名前と [REDACTED] が残るのは正しい）
```

HTTP の `recv` の `payload` は、コンパクトでバイトが変わらない JSON なら値のまま、整形済み JSON・CSV なら
**JSON 文字列**で入っている（`--format verbatim` / `--as csv` はどちらでも元バイトに戻る）。
`make` 経由の exit 2 は make 自身のもので、ツールの exit code は `bin/netloom …; echo $?` で確認する。詳しくは README §デバッグ。

**429（provider 側の制限）** は数分置いて再実行するか、過去の成功カセットを `--replay` する。
自動リトライはしない（決定どおり）。

---

# Apify（3 コマンド）

Apify は **VCR を通すだけの薄いプロキシ**。allow-list・入力スキーマ検証・コスト上限・ポーリングは
**無い**。actor は任意の ID、Apify が返したエラーはそのまま返る。

## いつ使うか（トリガー）

- 「YouTube / X / TikTok / Instagram の動画・投稿を Apify で集めて」
- 「〈採用済み actor〉を実行して、その dataset を読んで」
- 「Apify の run が終わったか」「いくらかかったか」（`run-status`）

## 前提: `APIFY_TOKEN`

- 値は**環境変数**で渡す。netloom は `APIFY_TOKEN` を読んで `Authorization: Bearer …` を組む
- env ファイルは**ワークスペース外**に置く（JCT のスクリプトは `APIFY_ENV`。この環境の既定は
  `/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env`）
- **コミットしない**。`chmod 600` にする。値は stdout / stderr / カセットのどこにも出ない
- 未設定なら netloom は 1 往復も送らず exit 2（リクエストも課金も発生しない）

```sh
# 例: env ファイルを読んでから実行（JCT は src/collection/run-with-env.sh <env-file> <command> が担う）
set -a; source "${APIFY_ENV:-/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env}"; set +a
```

## 実行（1 コマンド = 1 往復 = カセット 1 往復）

```sh
# 1) actor を実行（入力は JSON 文字列 or @FILE。actor は任意の ID）
make apify-run ACTOR=gJvjeCYNraSfhIaNd INPUT='{"search_term":"CBXリキッド","max_videos":5}'
#    → {"data":{"id","status","defaultDatasetId",…}} が返る（既定 json。FORMAT=text で要約）
#    → defaultDatasetId を 2) に渡す。WAIT=SEC は waitForFinish（既定は TIMEOUT と同じ値）

# 2) dataset の items を取る（provider の表現のまま）
make apify-dataset DATASET=<defaultDatasetId> LIMIT=5
make apify-dataset DATASET=<defaultDatasetId> LIMIT=5 ITEM_FORMAT=csv OUT=/tmp/items.csv   # CSV は Apify のバイトそのまま

# 3) run の状態と課金
make apify-run-status RUN=<runId> FORMAT=text
#    → status: SUCCEEDED / usageTotalUsd: 0.0026
```

make の変数名は CLI のフラグ名とは少し違う（`FORMAT` / `CASSETTE` / `OUT` / `REPLAY` は Google Trends と共通）:
`ACTOR`=`--actor` / `INPUT`=`--input` / `WAIT`=`--wait` / `DATASET`=`--dataset-id` / `LIMIT`=`--limit` /
`ITEM_FORMAT`=`--as` / `RUN`=`--run-id` / `TIMEOUT`=`--timeout`。
バイナリを直接叩くこともできる（`bin/netloom apify run --actor … --input …`）。

| フラグ | 意味 |
|---|---|
| `--actor ID` | 実行する actor（**任意の ID**。allow-list も name→ID 変換も無い） |
| `--input JSON` \| `@FILE` | run の入力（JSON であることだけを見る。スキーマは検証しない） |
| `--wait SEC` | `waitForFinish`。既定は `--timeout` と同じ値。**ポーリングはしない**（待つか待たないかだけ） |
| `--dataset-id ID` | dataset の ID（`apify run` の `defaultDatasetId`） |
| `--limit N` | items の上限（provider に渡すだけ。netloom は切り詰めない） |
| `--as json\|csv` | dataset の返り値（既定 `json` = items を整形、`csv` = Apify の CSV バイトそのまま） |
| `--run-id ID` | `run-status` が見る run |
| `--format json\|text\|verbatim` | `run` / `run-status` の出力（既定 `json` = 応答を整形、`text` = 1〜3 行の要約、`verbatim` = 受信バイト） |
| `--out` / `--cassette` / `--replay` / `--timeout` | Google Trends と同じ意味（`--timeout` は HTTP の context に当たる） |

### 採用済み actor の例（**例示であって制限ではない**）

JCT `config/collectors.json` と各 skill に実在する 5 件。**netloom は任意の ID を受け付ける**ので、
新しい actor を使うのに netloom の変更は要らない（どの actor を採用するかは呼び出し側が決める）。

| 用途 | actor ID（例） |
|---|---|
| YouTube 検索（`youtube-search`） | `gJvjeCYNraSfhIaNd` |
| YouTube スクレイプ（`youtube-scraper`） | `h7sDV53CddomktSi5` |
| X 検索（`x-search`） | `cPYLH3QT9GyzKhB4S` |
| TikTok 検索（`tiktok-search`） | `jQfZ1h9FrcWcliKZX` |
| Instagram 検索（`instagram-search`） | `TxU0ZBQIHdR20dr9C` |

- 入力の形（`search_term` / `max_videos` / `dateFilter` など）は**各 actor の skill / Actor ページ**で確認する
  （netloom は検証も補完もしない）
- actor ID はそのまま URL の path に入る（`user~actor` 形式も可）

## 課金の確認

- 実行前に: Actor ページ / JCT の skill にある単価。netloom は**コスト上限を持たない**
- 実行後に: `make apify-run-status RUN=<id> FORMAT=text` の `usageTotalUsd`
- `apify run` の応答（`status` / `usageTotalUsd`）はカセットにも残る（後から検算できる）

## 失敗の見分け（Apify）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx | — |
| 1 | 4xx / 5xx / 接続失敗 / DNS / TLS（stderr に `HTTP <status>` + 応答本文の先頭） | 本文は出力されない。`--cassette` を見れば応答全体が残っている。引数（actor ID・入力）を確認 |
| 2 | 引数・設定（`--actor` / `--input` の欠落や JSON でない入力、`APIFY_TOKEN` 未設定、`--replay` と `--cassette` の併用） | 引数と env を直す |
| 3 | I/O（`--out` / カセット / `@FILE` が読めない） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | run は Apify 側で続いている可能性がある。`run-status` で確認する |

## 証跡とオフライン再現（Apify）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-apify-run-<actor>.jsonl）
make apify-run ACTOR=gJvjeCYNraSfhIaNd INPUT=@input.json

# 同じ request で再生（ネットも credential も使わない。method + url + payload が一致しないと exit 1）
make apify-dataset DATASET=<id> ITEM_FORMAT=csv REPLAY=.cassettes/20261017T150000Z-apify-run-gjvjecynrasfhiand.jsonl
```

- カセットには `send`（method / url / headers / payload）と `recv`（status / payload）の 2 行
- `Authorization` は記録前に `[REDACTED]` になる（実値は入らない）
- 4xx / 5xx を記録したカセットを再生すると、**同じ失敗**になる（成功に偽装されない）
- カセットは**追記のみ**。編集・削除しない。`raw/` に置かない

---

# X API v2（3 コマンド）

X も **VCR を通すだけの薄いプロキシ**。allow-list・field 名の検証・ページングの自動化・リトライ・
レート制限の待ち・費用上限は**無い**。検索式・期間・page token・field はそのまま送られ、X が返した
エラーはそのまま返る。**live は owner 決定で禁止中**（当面 0 円。JCT `ISS-20261015-COL-030`）。

## いつ使うか（トリガー）

- 「X（旧 Twitter）の投稿を公式 API で集めて」（スクレイピング actor ではなく）
- 「この検索式の投稿を直近 7 日 / 全期間で」（`search-recent` / `search-all`）
- 「この投稿 ID の本文・日時を取って」（`tweet`）
- 「X の取得を request-only の証跡付きで再現したい」（カセットの `--replay`。ただし Request-only VCR の分離は未実装、下の「まだ無いもの」参照）

## 前提: `X_BEARER_TOKEN`

- 値は**環境変数**で渡す（app-only の Bearer）。netloom は `X_BEARER_TOKEN` を読んで `Authorization: Bearer …` を組む
- env ファイルは**ワークスペース外**に置く（`APIFY_ENV` と同じ扱い。**このマシンには X の env ファイルが無い**）
- **コミットしない**。`chmod 600` にする。値は stdout / stderr / カセットのどこにも出ない
- 未設定なら netloom は 1 往復も送らず exit 2
- **live request は owner 承認まで禁止**（JCT `ISS-20261015-COL-030` §3.4）。今できるのはテスト（偽 X API）とカセットの `--replay`

## 実行（1 コマンド = 1 往復 = カセット 1 往復）

```sh
# 1) 直近 7 日の検索（search-recent）
make x-search-recent QUERY='CBX lang:ja' MAX_RESULTS=100 TWEET_FIELDS=created_at,public_metrics
#    GET https://api.x.com/2/tweets/search/recent?query=…。既定 json。FORMAT=text で result_count・newest_id・oldest_id・next_token

# 2) 全期間の検索（search-all。上位 tier が無いと provider が 403 を返す）
make x-search-all QUERY='CBX lang:ja' START_TIME=2025-01-01T00:00:00Z END_TIME=2025-02-01T00:00:00Z
#    ページングは回さない: NEXT_TOKEN=<前の meta.next_token> で次の 1 往復を自分で実行する

# 3) 投稿 1 件
make x-tweet ID=<post-id> TWEET_FIELDS=created_at,text
#    FORMAT=text で id: / created_at: / text: の要約
```

make の変数は `QUERY` / `MAX_RESULTS` / `START_TIME` / `END_TIME` / `NEXT_TOKEN` / `TWEET_FIELDS` /
`USER_FIELDS` / `EXPANSIONS` / `ID`（`FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` は共通）。
バイナリを直接叩く場合は `bin/netloom x search-recent --query …`。

| フラグ | 意味 |
|---|---|
| `--query TEXT` | search-recent / search-all: 検索式（必須。そのまま送る。`since:` / `until:` もそのまま） |
| `--max-results N` | search: `max_results`（0 以下は exit 2。X の 10〜100・10〜500 は netloom は検証しない） |
| `--start-time` / `--end-time` | search: `start_time` / `end_time`（RFC3339 のまま。解釈しない） |
| `--next-token TOKEN` | search: `next_token`（**ページングは回さない**） |
| `--tweet-fields` / `--user-fields` / `--expansions` | search / tweet: field セレクタ（カンマ区切りのまま。未知の名前もそのまま） |
| `--id ID` | tweet: 投稿 ID（必須） |
| `--format json\|text\|verbatim` | 出力（既定 json = 応答を整形、text = 要約、verbatim = 受信バイト）。**csv は無い** |
| `--out` / `--cassette` / `--replay` / `--timeout` | 他と同じ意味（`--replay` と `--cassette` は併用しない） |

## 出力の読み方

- `json` は X の生構造のまま（検索 = `{"data":[…],"meta":{…}}`、投稿 = `{"data":{…}}`）。**0 件（`result_count: 0`）は失敗ではない**
- `text` は search = `result_count` / `newest_id` / `oldest_id` / `next_token`、tweet = `id` / `created_at` / `text`。**応答に無い項目は出ない**（1 つも無ければ exit 1）
- **値を解釈しない**: 件数・期間・言語の判定は呼び出し側。`next_token` を渡して続きを取るのも呼び出し側

## 失敗の見分け（X）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx（0 件の検索を含む） | — |
| 1 | 4xx / 5xx（**429 を含む**。リトライしない）/ 接続失敗 / replay 不一致（stderr に `HTTP <status>` + 本文先頭） | 本文は出力されない。`--cassette` を見れば応答全体が残っている。403 なら search-all の tier を確認。429 は数分置いて再実行 |
| 2 | 引数・設定（`--query` / `--id` 欠落、`--max-results <= 0`、`X_BEARER_TOKEN` 未設定、`--replay` と `--cassette` の併用） | 引数と env を直す |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |

## 証跡とオフライン再現（X）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-x-<command>-<target>.jsonl）
make x-search-recent QUERY='CBX lang:ja' MAX_RESULTS=100

# 同じ request で再生（ネットも token も使わない。method + url + payload が一致しないと exit 1）
make x-search-recent QUERY='CBX lang:ja' MAX_RESULTS=100 REPLAY=.cassettes/20261018T120000Z-x-search-recent-cbx-lang-ja.jsonl FORMAT=text
```

- カセットには `send`（method / url / headers。GET なので payload は無い）と `recv`（status / payload）の 2 行
- `Authorization` は記録前に `[REDACTED]` になる（実値は入らない）
- 4xx / 5xx を記録したカセットを再生すると、**同じ失敗**になる（成功に偽装されない）
- **X のカセットは応答本文に投稿データ（本文・ID・`next_token` 原値）を含む**。**コミットしない**。`raw/` に置かない。共有・貼り付けもしない（JCT `ISS-20261015-COL-030` §4.1: X 元投稿データをリポジトリに保存しない）
- カセットは**追記のみ**。編集・削除しない

---

# GA4（3 コマンド）

GA4 も **VCR を通すだけの薄いプロキシ**。dimension / metric の allow-list・ページングの自動化・
リトライ・レート制限の待ち・値の解釈は**無い**。相手は **Google Analytics Data API**（`https://analyticsdata.googleapis.com/v1beta`）で、
**1 コマンド = 認証 1 + データ 1 の 2 往復（カセット 4 frame）**。credential は Google の
refresh grant（netloom 自身がトークンを交換する。GSC と同じ道）。

> 0.4.0 までは既存の GA4 MCP サーバー（`ga4_mcp_server.py`）を wrapper 越しに実行していた。
> その配線はこのマシンの絶対パス（wrapper / env ファイル / venv python）を含む唯一の箇所だったので、
> 送信元を HTTP に移して消した。**当時の MCP カセットは新しい実装では再生できない**（証跡としては有効）。
> 2026-10-19 に `GOOGLE_TOKEN_FILE` で 3 コマンドを実測した（`get-metadata` は 200、report 2 つは
> property 0 を report に使えないため API の 403 = 転送・記録は実測）。

## いつ使うか（トリガー）

- 「GA4 のセッション / ユーザー数を取って」「アナリティクスのレポートを見て」
- 「直近 7 日の推移」「日別のセッション」（`run-report`。日付は `7daysAgo` などの相対値もそのまま）
- 「いまのリアルタイムのユーザー」（`run-realtime-report`）
- 「このプロパティで使える dimension / metric を確認して」（`get-metadata`）
- 「GA4 の取得を証跡付きで残したい」（netloom 経由。カセットが証跡になる）

## 前提

- **`mcp_ga4_*` や Analytics Data API を直接叩かない**（seo の `ga4-analytics` skill は直接使う手順だが、
  それではリポジトリ側に証跡が残らない）。**GA4 の取得は netloom 経由**にする（往復がカセットに残る）
- **credential は Google の refresh grant**（GSC と同じ変数）: `GOOGLE_TOKEN_FILE`（env のパス。
  `netloom auth google --source ga4` が書くファイル）→ その `client_id` / `client_secret` / `refresh_token`、
  無ければ `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`。**どちらも無ければ 1 往復も送らず exit 2**
- **プロパティは `--property ID` か env `GA4_PROPERTY_ID`**: どちらも無ければ 1 往復も送らず exit 2
  （値は裸の id = `123456789` の形。URL は `/v1beta/properties/<id>:runReport` になる）
- live は**読み取り専用**（`analytics.readonly` スコープ）。書き込み・設定変更（Admin API）は無い
  （2026-10-19 に `GOOGLE_TOKEN_FILE` で 3 コマンドを実測。`--property 0` は metadata 専用なので、report の live には実 property id が要る）

## 実行（1 コマンド = 認証 1 + データ 1 = カセット 4 frame）

```sh
# 0) 合意（owner が 1 回だけ）とプロパティ
netloom auth google --source ga4 --client-secrets /path/to/credentials.json
#    → $HOME/.config/netloom/google-ga4.json（0600）
export GOOGLE_TOKEN_FILE="$HOME/.config/netloom/google-ga4.json"
export GA4_PROPERTY_ID=123456789          # または毎回 --property 123456789

# 1) レポート（既定: 直近 7 日 / 構造化 json）
make ga4-report METRICS=sessions DIMENSIONS=date
make ga4-report METRICS=sessions DIMENSIONS=date START_DATE=30daysAgo END_DATE=today FORMAT=csv OUT=/tmp/sessions.csv
#    METRICS は必須（空は exit 2）。DIMENSIONS は空可（次元なしレポート）。
#    LIMIT（既定 100）/ OFFSET（既定 0）/ KEEP_EMPTY_ROWS / PROPERTY もそのまま渡る

# 2) リアルタイム（直近のスナップショット）
make ga4-realtime DIMENSIONS=deviceCategory METRICS=activeUsers LIMIT=10

# 3) メタデータ（dimension / metric の語彙）
make ga4-metadata OUT=/tmp/ga4-metadata.json          # 入れ子なので csv は無い（FORMAT=csv は exit 2）
```

バイナリを直接叩く場合は `bin/netloom ga4 run-report --metrics sessions --dimensions date --property 123456789`（他のフラグも同じ語）。
make 変数は `DIMENSIONS` / `METRICS` / `START_DATE` / `END_DATE` / `PROPERTY` / `OFFSET` /
`KEEP_EMPTY_ROWS`（`FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` / `LIMIT` は共通）。

| フラグ | 意味 |
|---|---|
| `--dimensions T` | run-report / realtime: dimension（カンマ区切りのまま。**空可**） |
| `--metrics T` | run-report（**必須**）/ realtime（既定 `activeUsers`）: metric（カンマ区切りのまま） |
| `--start-date` / `--end-date` | run-report: 期間（既定 `7daysAgo` / `today`。解釈しない） |
| `--property ID` | 3 コマンド共通: プロパティ（**省略時は env `GA4_PROPERTY_ID`**。どちらも無ければ exit 2） |
| `--limit` / `--offset` / `--keep-empty-rows` | run-report（`limit` は realtime も）: そのまま渡す（**ページングは回さない**） |
| `--format` | json（既定）/ csv（run-report と realtime のみ。rows を平坦化）/ text / verbatim |
| `--out` / `--cassette` / `--replay` / `--timeout` | 他と同じ（`--replay` と `--cassette` は併用しない） |

## 出力の読み方

- `json`（既定）は **API の応答文書をそのまま**（キー順は受信のまま）: `dimensionHeaders` / `metricHeaders` /
  `rows`（各 row は `dimensionValues[].value` と `metricValues[].value`）/ `rowCount` / `kind`。
  metadata は `name` / `dimensions` / `metrics`
- `csv` は `rows` を平坦化した表（列 = **呼び出し側が名指した** `--dimensions` と `--metrics` の順。
  応答のヘッダから列を推測しない）。**0 行でもヘッダは出る**。`totals` / `maximums` / `minimums` は含まれない
- `text` は行数の要約（`rows: N`。0 行は `rows: 0`）。metadata は `dimensions: N` / `metrics: N`
- `verbatim` は受信バイトそのまま（証跡）
- **値を解釈しない**: 指標の意味・比較・集計は呼び出し側。未知の dimension / metric 名は GA4 が返した
  エラーがそのまま出る（allow-list は netloom に無い）

## 失敗の見分け（GA4）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 成功（0 行のレポートを含む） | — |
| 1 | 4xx / 5xx、交換の失敗（`invalid_grant` など）、replay 不一致（stderr に GA4 のメッセージがそのまま出る） | メッセージを読む。401 なら credential（`GOOGLE_*` / トークンファイル）。403 ならスコープか権限。dimension / metric 名の誤りは 400 に出る |
| 2 | 引数・設定（`--metrics` 欠落、`--property` も `GA4_PROPERTY_ID` も無い、credential 未設定、`get-metadata` の `csv`、`--replay` と `--cassette` の併用） | 引数と env を直す |
| 3 | I/O（`--out` / カセット / トークンファイルが読めない） | パスを直す |
| 124 | timeout（既定 300 秒。交換 + データの合計） | 再実行、または owner に相談 |

## 証跡とオフライン再現（GA4）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-ga4-<command>-<列 or property>.jsonl）
make ga4-report METRICS=sessions DIMENSIONS=date

# 同じ request で再生（ネットも credential も使わない。method + url + body が一致しないと exit 1）
make ga4-report METRICS=sessions DIMENSIONS=date REPLAY=.cassettes/20261017T173613Z-ga4-run-report-date-sessions.jsonl FORMAT=text
```

- カセットには HTTP の frame が 4 つ残る（**交換の send / recv**、**データの send / recv**。§5.1）。
  交換も証跡として残る（`client_secret` / `refresh_token` / `Authorization` は `[REDACTED]`）
- `--replay` は**交換をしない**（credential もネットも使わない）。データ要求（method + url + body）だけで答える
- **0.4.0 までの MCP カセットは再生できない**（frame の形が違う）。証跡としては有効なので削除しない
- **GA4 のカセットはプロパティの集計値を含む**ので `.cassettes/`（gitignore）にだけ置き、**コミットしない**。
  `raw/` に置かない。テストは偽 API（`httptest`。実データを fixture に置かない）
- 失敗（401 などの 4xx を含む）もカセットに残る（証跡）。再生すると**同じ失敗**になる（成功に偽装されない）
- カセットは**追記のみ**。編集・削除しない

---

# GSC（Google Search Console。2 コマンド）

GSC も **VCR を通すだけの薄いプロキシ**。クエリ body の検証・dimensions の allow-list・ページングの
自動化・リトライ・レート制限の待ち・値の解釈・正規化は**無い**。site と body はそのまま送られ、GSC が
返したエラーはそのまま返る。**1 コマンド = 2 往復**（認証 + データ。netloom 自身がトークンを交換する）。

## いつ使うか（トリガー）

- 「Search Console の検索パフォーマンスを見て」「このサイトの検索クエリ / クリック / 表示回数を取って」
- 「SC のプロパティ一覧を確認して」（`sites`）
- 「サーチコンソールのデータを証跡付きで取って」（カセットが証跡になる）

## 前提: `GOOGLE_*` の 3 つ（netloom が交換する）

- 値は**環境変数**で渡す。netloom は `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`
  を読み、`https://oauth2.googleapis.com/token` に form-encoded で exchange して access token にする
- env ファイルは**ワークスペース外**に置く（seo の `.env.d/google_search_console.env` と同じ変数名。
  **値は読まない・出力しない**）。**コミットしない**。`chmod 600` にする
- **3 つのどれかが欠けていれば netloom は 1 往復も送らず exit 2**（リクエストも課金も発生しない）
- **代わりに `GOOGLE_TOKEN_FILE`（env のパス）でもよい**: そのファイル（`netloom auth google` が書く google-auth の authorized user JSON）の `client_id` / `client_secret` / `refresh_token` を使う。**両方あればファイルが勝つ**（1 つの解決順）。無い = exit 3 / 壊れた JSON = exit 2。`--replay` は交換をしないのでどちらも読まない（設計書 §7.2 / 付録 A.22）
- 任意で `GOOGLE_CLOUD_QUOTA_PROJECT`（または `--quota-project`）→ `x-goog-user-project`。無ければ送らない

```sh
# 例: env ファイルを読んでから実行（値は出力しない）
set -a; source /path/to/.env.d/google_search_console.env; set +a
```

## 実行（1 コマンド = 認証 1 + データ 1 = カセット 4 frame）

```sh
# 1) searchAnalytics のクエリ（site と body は呼び出し側が書く。**日付は ISO の YYYY-MM-DD** —
#    GSC は GA4 と違って `7daysAgo` / `today` を受け付けず 400 を返す（実測: 実装メモ §9）)
make gsc-query SITE='sc-domain:example.com' BODY='{"startDate":"2026-10-10","endDate":"2026-10-17","dimensions":["query"],"rowLimit":5}'
#    POST https://searchconsole.googleapis.com/webmasters/v3/sites/sc-domain%3Aexample.com/searchAnalytics/query
#    dimensions / rowLimit / dimensionFilterGroups / startRow はそのまま送る（ページングは回さない）
make gsc-query SITE='sc-domain:example.com' BODY=@body.json FORMAT=csv OUT=/tmp/gsc.csv
#    csv の列 = body の dimensions の順 + clicks,impressions,ctr,position（body に dimensions が無ければ exit 2）

# 2) プロパティ一覧
make gsc-sites            # FORMAT=csv は siteUrl,permissionLevel / FORMAT=text は sites: N
```

バイナリを直接叩く場合は `bin/netloom gsc query --site … --body …` / `bin/netloom gsc sites`。
make 変数は `SITE` / `BODY` / `QUOTA_PROJECT`（`FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` は共通）。
`BODY` は `INPUT` と同じ扱い（JSON を make の展開に通さない。`$` を含む値は `BODY=@body.json`）。

| フラグ | 意味 |
|---|---|
| `--site URL` | `query`: プロパティ（必須。`sc-domain:example.com` / `https://example.com/`。そのまま送る） |
| `--body JSON\|@FILE` | `query`: searchAnalytics の body（必須。JSON であることだけを見て送る） |
| `--quota-project ID` | 両方: `x-goog-user-project`（既定は env `GOOGLE_CLOUD_QUOTA_PROJECT`） |
| `--format` | json（既定）/ csv（query と sites）/ text / verbatim |
| `--out` / `--cassette` / `--replay` / `--timeout` | 他と同じ（`--timeout` は**認証 + データの合計**。`--replay` と `--cassette` は併用しない） |

## 出力の読み方

- `json`（既定）は GSC の生構造のまま: `{"rows":[{"keys":[…],"clicks":…,"impressions":…,"ctr":…,"position":…}],"responseAggregationType":…}`。
  **0 行のとき GSC は `{}` を返すことがある**（`text` はそのとき exit 1、json / csv / verbatim は成功）
- `csv` は `rows` を平坦化した表（列 = body の `dimensions` の順 + metrics）。`keys` が dimensions と
  合わない行は表にしない（exit 1）
- `text` は `rows: N`（+ `responseAggregationType`）、sites は `sites: N`
- **値を解釈しない**: 検索クエリの意味・期間比較・集計は呼び出し側。`startRow` を書いて続きを取るのも
  呼び出し側（netloom はページングしない）

## 失敗の見分け（GSC）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx | — |
| 1 | **交換の失敗（`invalid_grant` = credential の期限切れ / 失効）**・データの 4xx / 5xx / 接続失敗 / replay 不一致 | stderr の 1 行を読む。`invalid_grant` なら credential を更新する（seo 側の作業）。それ以外は `--cassette` で応答全体を見る |
| 2 | 引数・設定（`--site` / `--body` 欠落、JSON でない body、`dimensions` 無しの csv、`GOOGLE_*` 未設定、`--replay` と `--cassette` の併用） | 引数と env を直す |
| 3 | I/O（`--out` / カセット / `@FILE`） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |

**`invalid_grant`（HTTP 400）は credential の問題**（netloom の設定ではない）。トークン端点が
request / response ともカセットに残るので、そこで確認できる。

## 証跡とオフライン再現（GSC）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-gsc-<command>-<target>.jsonl）
make gsc-query SITE='sc-domain:example.com' BODY=@body.json

# 同じ request で再生（ネットも credential も使わない。**交換はしない**。method + url + payload が
# 一致しないと exit 1）
make gsc-query SITE='sc-domain:example.com' BODY=@body.json REPLAY=.cassettes/20261018T120000Z-gsc-query-sc-domain-example-com.jsonl FORMAT=csv
```

- カセットには **4 frame**: 交換の `send`（`/token`、form body） / `recv` → データの `send` / `recv`
- 交換の request body は **form-encoded のテキスト**で入る（`grant_type=refresh_token` は残り、
  `client_id` / `client_secret` / `refresh_token` の値は `[REDACTED]`）。応答の `access_token`（`ya29.…`）も伏せられる
- データの `Authorization` と `x-goog-user-project` は記録前に `[REDACTED]` になる（実値は入らない）
- 4xx / 5xx を記録したカセットを再生すると、**同じ失敗**になる（成功に偽装されない）
- **交換しか記録していないカセット**（credential が古く `invalid_grant` で終わった run）は、データ要求に
  答える frame が無いので再生できない（exit 1）
- **GSC のカセットは自分のサイトの検索語と数値を含む**ので `.cassettes/`（gitignore）にだけ置き、
  **コミットしない**。`raw/` に置かない。共有・貼り付けもしない
- カセットは**追記のみ**。編集・削除しない

---

# auth google（ローカルコマンド。Google OAuth の同意フロー。**対話専用**）

provider を呼ばない netloom 自身のコマンド（`skill` と同じ族。source を名指さない）。**人がブラウザで同意する 1 回だけのコマンド**で、GSC の refresh token（`.github/bin` の 3 本が取っていたもの）を netloom 自身で取る（issue #11）。

```sh
# 同意（1 回だけ。ブラウザが開く。開かなければ stderr に出た URL を開く）
make auth-google AUTH_CLIENT_SECRETS=/path/to/credentials.json AUTH_SOURCE=gsc
bin/netloom auth google --source gsc --client-secrets /path/to/credentials.json   # make と同じ

# できたトークンファイルだけでデータを取る（GOOGLE_REFRESH_TOKEN は不要）
GOOGLE_TOKEN_FILE="$HOME/.config/netloom/google-gsc.json" bin/netloom gsc sites
```

| フラグ | 意味 |
|---|---|
| `--source NAME` | 既定スコープの表: `gsc` → webmasters / `ga4` → analytics.readonly / `calendar` → calendar / `gas` → script.* + spreadsheets。**`calendar` / `gas` は送信元ではない**（スコープ名。`gas` の 6 スコープは `apps-script` 送信元の live トークンが使う — 付録 A.27） |
| `--scopes A,B` | 既定を上書き（カンマ区切り。空要素は exit 2） |
| `--client-secrets FILE` | OAuth クライアント JSON（`{"installed":{…}}`。**必須・既定パスなし**。netloom は推測しない） |
| `--token-file FILE` | 書き出し先（既定 `$HOME/.config/netloom/google-<source>.json`。dir 0700・file 0600） |
| `--cassette FILE` | 交換の証跡（2 frame）の記録先（issue #22。**caller の記録置き場に置く** — 例: `data/gsc/cassettes/<YYYYMMDD>-auth-gsc.jsonl`。他コマンドと同じ意味・同じ規則。既定は `.cassettes/<UTC>-auth-google-<source>.jsonl`） |

- **対話専用**: stdin / stdout / stderr が端末で `CI` が未設定のときだけ動く。**CI・自動テストは exit 2**（listener も開かない）
- ループバック（`http://127.0.0.1:<ephemeral>/`）+ PKCE（S256）。待ち時間は既定 300 秒（専用フラグは無い）。Ctrl-C で中断できる
- トークンファイルは google-auth の authorized user JSON と互換（`client_id` / `client_secret` / `refresh_token` / `token` / `scopes` / `expiry` の 6 つ。**1 行・末尾改行なし**）。書き込みは一時ファイル + rename（原子的）
- **値は stdout / stderr / カセットに出ない**。交換の往復はカセット（既定 `.cassettes/<UTC>-auth-google-<source>.jsonl`、`--cassette FILE` で caller の記録置き場に変更可 = issue #22）に残るが、form の `client_id` / `client_secret` / `code` / `code_verifier` と応答の `access_token` / `refresh_token` は `[REDACTED]`
- **同意の redirect（ブラウザ → ループバック）は記録しない**（URL に code が載るため）
- 失敗の写像: 同意キャンセル・state 不一致・`invalid_grant` = exit 1 / `--client-secrets` が読めない・トークンファイルを書けない = exit 3 / 引数と client JSON の形 = exit 2 / 300 秒超過 = exit 124


---

# news / cache（EC-CUBE 自サイト API。8 コマンド）

ショップ自身のニュースの CRUD・サムネイル画像・キャッシュクリアを、**VCR を通す薄いプロキシ**として扱う。
フィールドの検証・allow-list・画像の形式やサイズの検査・ページングの自動化・リトライ・レート制限の待ち・
値の解釈・キャッシュの状態管理は**無い**（API が返したエラーはそのまま返る）。仕様の正は seo-operations の
`ec-news-api` スキル。

## いつ使うか（トリガー）

- 「ショップのニュース（新着情報）を一覧 / 取得したい」「ニュースを登録 / 修正 / 削除したい」
- 「ニュースにサムネイル画像を付けたい / 外したい」
- 「更新がフロントに出ないのでキャッシュをクリアしたい」
- 「本番ではなく開発サーバーで試したい」（`ENV=dev`。本番は `ENV=prod`）

## 前提: `SEO_API_KEY`（+ 開発環境は Basic 認証）

- live は環境変数 `SEO_API_KEY`（`X-API-Key` ヘッダ）と、**開発サーバーでは** `HTTP_BASIC_AUTH_USER` /
  `HTTP_BASIC_AUTH_PASS`（netloom が `Authorization: Basic <base64(user:pass)>` を組む）が要る
- env ファイルは**ワークスペース外**に置く。**コミットしない**。`chmod 600` にする。値は stdout / stderr /
  カセットのどこにも出ない（`X-API-Key` と `Authorization` は名前を残して `[REDACTED]`）
- **どれか欠けていれば netloom は 1 往復も送らず exit 2**（カセットも作らない）
- **開発サーバーの base URL は env `EC_DEV_BASE_URL` から読む**（news / article / cache / contact / ga4-orders の 5 送信元共通。**コードに値は無い**）。未設定なら `--env dev` のコマンドは **exit 2**（メッセージに変数名が出る。1 往復も送らない）。`--replay` でも要る（URL がカセットの照合に要る）
- **値は credential ではない**ので、カセットの URL にはそのまま載る（証跡として必要。レダクトされない）。呼び出し側（seo-operations）は同じ値に `ADMIN_DEV_URL` の名前を付けて `.env.d/admin_dev.env` に置く
- `cache clear` はニュースと記事 API の共用キャッシュクリア（同じ場所・同じ認証）

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
# 一覧（`--format csv` は固定の列。LIMIT / OFFSET は API に渡すだけ）
make news-list LIMIT=10 OFFSET=0
make news-list FORMAT=csv OUT=/tmp/news.csv

# 1 件（`--format text` は id / title / publish_date の要約）
make news-get ID=1239

# 作成 → 更新 → 削除（CLEAR_CACHE=1 で書き込み後のクリアを同じ往復に載せる）
make news-create INPUT='{"title":"invented","top_page_notice":true}' CLEAR_CACHE=1
make news-update ID=1239 INPUT=@body.json
make news-delete ID=1239 CLEAR_CACHE=1

# サムネイル（multipart。形式・5MB は API の判定。**派生バリアントはサーバー側で生成されない**）
make news-image-upload ID=1239 FILE=thumb.jpg CLEAR_CACHE=1
make news-image-delete ID=1239

# 共用キャッシュクリア（同期実行。200 が返ればクリア済み）
make cache-clear

# 本番への書き込みは明示フラグが要る（読み取りは不要。読み取りに付けると exit 2）
make news-delete ID=1239 ENV=prod ALLOW_PROD_WRITE=1
```

| 変数 | 既定 | 値 |
|---|---|---|
| `ID` | （get / update / delete / image-* で必須） | ニュース ID |
| `INPUT` | （create / update で必須） | 本文の JSON 1 文書（または `INPUT=@body.json`） |
| `FILE` | （image-upload で必須） | 画像のパス（jpeg / png / webp・5MB 以内は API の判定） |
| `LIMIT` / `OFFSET` | （省略 = API の既定） | 一覧の件数 / 読み飛ばし（`list` のみ） |
| `CLEAR_CACHE` | （未指定） | `1` で書き込みの URL に `clear_cache=1` |
| `NEWS_ENV` | `dev`（未指定なら dev） | `dev` / `prod` |
| `ALLOW_PROD_WRITE` | （未指定） | `1` で本番への書き込みを確認 |
| `FORMAT` | `json` | list: `json` / `csv` / `text` / `verbatim`、get と書き込み系: `json` / `text` / `verbatim` |
| `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | 他と同じ | |

## 出力の読み方

- `json`（既定）は API の文書のまま（`success` / `total` / `items` / `item` / `message` など）。
  **値を解釈しない**: ニュースの内容・公開日時の意味・キャッシュの状態は呼び出し側が読む
- `csv` は**一覧のみ**。列は `id,title,description,citation,url,link_method,publish_date,top_page_notice,creator_id`
  の固定で、API が述べていない項目は空セルになる（実測: 一覧は `citation` を返さない）
- `text` は要約: 一覧 = `total` / `limit` / `offset` / `items: N`、1 件 = `id` / `title` / `publish_date`、
  書き込み = `success` / `message` / `cache_cleared`（`cache clear` は `duration_ms`）
- **`title` は API の必須項目**。netloom は JSON であることしか見ないので、欠けた本文は API の 400 になる
- 画像の応答の `item.thumbnail_path` に保存値が入る（一覧ページでは未使用）

## 失敗の見分け（news / cache）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx | — |
| 1 | 400 / 401 / 404 / 405 / 500（API の応答のまま）・接続失敗・replay 不一致 | stderr の 1 行とカセットを読む。401 はキー、404 は ID、405 はメソッドを確かめる |
| 2 | 引数・設定（`--id` / `--input` / `--file` 欠落、JSON でない本文、語彙外の `--env`、**本番書き込みのフラグ無し**、読み取りのフラグ、dev ホスト未記入、credential 未設定） | 引数と env を直す |
| 3 | I/O（`--out` / カセット / `@FILE` / `--file`） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |

## 証跡とオフライン再現（news / cache）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-news-<command>-<target>.jsonl）
make news-list LIMIT=10

# 同じ request で再生（ネットも credential も使わない。method + url + 本文 / 証跡の一致が要る）
make news-list LIMIT=10 REPLAY=.cassettes/20261019T120000Z-news-list-all.jsonl
make news-image-upload ID=1239 FILE=thumb.jpg REPLAY=.cassettes/…-news-image-upload-1239.jsonl
```

- 1 コマンド = **2 frame**（`send` / `recv`）。失敗もカセットに残る
- **画像の `send` の `payload` は本文ではなく識別 JSON**（`{"kind":"multipart","fields":{…},"file":{"field":"file","sha256":…,"size":…}}`）。
  **本文・boundary・ファイル名はカセットに入らない**（boundary は毎回変わる）。replay は sha256 で照合するので、
  **同じ画像ならファイル名が違っても答える**。別の画像を渡すと exit 1（他の画像の応答を返さない）
- `X-API-Key` と dev の `Authorization` は記録前に `[REDACTED]`。**netloom が組む `Basic <base64>` の値も
  どこにも出ない**（provider がエコーしても伏せる）
- **news / cache のカセットはショップのニュースを含む**ので `.cassettes/`（gitignore）にだけ置き、
  **コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**（編集・削除しない）

---

# article（EC-CUBE ガイド記事 API。7 コマンド）

ガイド記事（物質辞典などの本体）の CRUD と画像を、news と同じ形で扱う。環境・認証・prod ガード・
multipart の証跡・カセットの規則は **news と同じ**（上の節）。**netloom は slug を解釈せず、slug → id の
解決もしない**（呼び出し側が `list` の `offset` を進めて見つける）。**大きな本文も切り詰めない**（カセットが
証跡で、切り詰めると replay の本文一致が失われる）。

## いつ使うか（トリガー）

- 「ガイド記事を公開 / 更新 / 削除したい」（原稿 → `loom md build` → intro/body/summary/citation の 4 分割 → PUT）
- 「公開済みの記事を slug で確かめたい」（`list` で id を引き、`get` で `status` と本文を見る）
- 「記事のヒーロー画像 / 記事内画像を入れ替えたい、alt / caption / position を直したい」

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
make article-list LIMIT=100                          # 一覧（`--format csv` は固定の列）
make article-get ID=169                              # 1 件（text は id / title / slug / status）
make article-create INPUT='{"title":"invented","slug":"invented-guide","body_html":"<p>invented</p>"}'
make article-update ID=169 INPUT=@body.json CLEAR_CACHE=1     # 部分更新（述べたフィールドだけ）
make article-delete ID=169 CLEAR_CACHE=1

# 画像（--type は thumbnail（既定）/ image。type=image のメタデータは form field で送る）
make article-image-upload ID=169 FILE=hero.webp ARTICLE_TYPE=image ALT='説明' CAPTION='キャプション' POSITION=middle
#   ※ alt / caption を *クリア* するときは make ではなくバイナリで: bin/netloom article image-upload --id 169 --file hero.jpg --type image --alt ""
make article-image-delete ID=169 ARTICLE_TYPE=image
make cache-clear                                    # ニュースと共用（article でも同じ 1 本）
```

| 変数 | 既定 | 値 |
|---|---|---|
| `ID` | （必須） | 記事 ID |
| `INPUT` | （create / update で必須） | 本文の JSON（`title` / `slug` / `body_html` は API の必須。slug の形式・一意性も API の判定） |
| `FILE` | （image-upload で必須） | 画像（jpeg / png / webp・5MB 以内は API の判定。派生バリアントは API が生成） |
| `ARTICLE_TYPE` | （API の既定 = thumbnail） | `thumbnail` / `image` |
| `ALT` / `CAPTION` / `POSITION` | （API の既存値） | `type=image` のメタデータ（position は `after_intro` / `middle` / `after_summary`） |
| `LIMIT` / `OFFSET` | （API の既定） | 一覧の件数 / 読み飛ばし（100 件上限は API の仕様） |
| `CLEAR_CACHE` / `NEWS_ENV` / `ALLOW_PROD_WRITE` / `FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | news と同じ | |

## 失敗の見分け（article）

news と同じ（exit 1 / 2 / 3 / 124。付録 A.16）。**401** はキー、**404** は ID、**400** は
「必須（title / slug / body_html）・slug 形式/重複・status 値・カテゴリ slug・citation の型/長さ（>65,535
バイト）・画像の形式/サイズ/未設定」——どれも **API の文面がそのまま返る**ので、stderr の 1 行とカセットで読む。

## 証跡とオフライン再現（article）

```sh
make article-list LIMIT=100                          # 記録（.cassettes/<UTC>-article-list-all.jsonl）
make article-list LIMIT=100 REPLAY=.cassettes/20261019T120000Z-article-list-all.jsonl
make article-update ID=169 INPUT=@body.json REPLAY=.cassettes/…-article-update-169.jsonl
```

- 画像の `send` の `payload` は証跡 JSON で、**`fields` に `type` / `alt` / `caption` / `position` が入る**
  （本文・boundary・ファイル名は入らない。replay は sha256 とフィールドの一致で答える）
- **未公開（`status=draft`）の原稿本文を含む**ので `.cassettes/`（gitignore）にだけ置き、
  **コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**。

---

# contact（EC-CUBE お問い合わせ API。5 コマンド）

ショップのお問い合わせ（ContactManagement42 の `dtb_contact`）の CRUD を、news と同じ形で扱う。環境・
認証（`X-API-Key` + dev の Basic）・prod ガード・カセットの規則は **news と同じ**（上の節）。**画像と
キャッシュクリアのエンドポイントは無い**ので `--file` / `--clear-cache` / image コマンドは存在しない。

**PII の扱い**: 応答には氏名・メール・電話・住所・問い合わせ本文が入る。**netloom はレダクトしない**
（`list` / `get` の応答にも PII が入るため、レダクトするなら replay の同一結果が壊れる。付録 A.17 の
設計相談 1 への回答）。**だからこそカセットは `.cassettes/`（gitignore）にだけ置き、コミット・共有・
`raw/` 配置をしない**（shop 側の規約: 顧客レベルのデータをリポジトリに残さない）。

## いつ使うか（トリガー）

- 「お問い合わせを一覧 / 取得したい」「お問い合わせの対応状況（`status_id`）や備考を更新したい」
- 「外部フォームからのお問い合わせを登録したい」（`contact create`。API の必須は `name01` / `name02` / `email`）
- 「開発サーバーで試したい」（`NEWS_ENV=dev`。本番は `NEWS_ENV=prod` + 書き込みは `ALLOW_PROD_WRITE=1`）

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
make contact-list LIMIT=10 OFFSET=0          # 一覧（`--format csv` は固定の列。API の既定は limit=20・最大 100）
make contact-get ID=41                       # 1 件（text は id / name01 / name02 / status_id）
make contact-create INPUT='{"name01":"invented","name02":"one","email":"invented@example.test"}'
make contact-update ID=41 INPUT='{"status_id":2,"note":"invented"}'   # 部分更新（述べたフィールドだけ）
make contact-delete ID=41
```

| 変数 | 既定 | 値 |
|---|---|---|
| `ID` | （get / update / delete で必須） | お問い合わせ ID |
| `INPUT` | （create / update で必須） | 本文の JSON（または `INPUT=@body.json`。`name01` / `name02` / `email` は API の必須） |
| `LIMIT` / `OFFSET` | （API の既定） | 一覧の件数 / 読み飛ばし（`list` のみ） |
| `NEWS_ENV` / `ALLOW_PROD_WRITE` / `FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | news と同じ | |

- `text` は要約: 一覧 = `total` / `limit` / `offset` / `items: N`、1 件 = `id` / `name01` / `name02` /
  `status_id`、書き込み = `success` / `message`（`cache_cleared` は無い）
- `csv` の列は `id,name01,name02,email,kana01,kana02,phone_number,postal_code,addr01,addr02,contents,note,contact_type,status_id`
  の固定で、**API が述べていない項目は空セル**（`status_name` / `create_date` などは json / verbatim で読む）
- `--env prod` の書き込み（create / update / delete）は `--allow-prod-write` が無ければ exit 2。読み取りは不要

## 証跡とオフライン再現（contact）

```sh
make contact-list LIMIT=10                   # 記録（.cassettes/<UTC>-contact-list-all.jsonl）
make contact-list LIMIT=10 REPLAY=.cassettes/20261019T120000Z-contact-list-all.jsonl
```

- 1 コマンド = **2 frame**（`send` / `recv`）。失敗（400 / 401 / 404 / 500）もカセットに残り、replay は**同じ失敗**を返す
- `X-API-Key` と dev の `Authorization` は記録前に `[REDACTED]`
- **カセットは顧客の PII を含み、レダクトされない**。`.cassettes/`（gitignore）にだけ置き、**コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**（編集・削除しない）

---

# ga4-orders（EC-CUBE GA4 受注同期 API。5 コマンド）

ショップの GA4 受注同期（SalesReport42 の `plg_sales_report42_ga4_order`。`sync_status` = pending /
`eccube_order_id` の紐づけ）の CRUD を、news と同じ形で扱う。環境（`--env dev|prod`）・dev の Basic・
prod ガード・カセットの規則は **news と同じ**。**認証だけが違う**: **`X-GA4-API-Key` ヘッダで
`GA4_API_KEY` を送る**（`SEO_API_KEY` ではない）。

**GA4 Data API の `ga4` とは別物**: あちらは集計レポートを Analytics Data API（HTTP。Google の refresh grant）で読む送信元で、こちらは
ショップの受注テーブルを HTTP で管理する送信元。名前が似ているが、コマンドも認証も別（`--property` などは
取らない）。

**実運用**: `list` / `get` / `update` / `delete` が主。**`create` はバックフィルとテスト用**（本来は GA4
側の連携が POST する）。**画像・キャッシュクリアのエンドポイントは無い**。

**売上の扱い**: 応答には売上額・`transaction_id`・`user_id`・商品明細が入る。**netloom はレダクトしない**
（理由は contact と同じ。付録 A.18 の設計相談 2 への回答）。**カセットは `.cassettes/`（gitignore）に
だけ置き、コミット・共有・`raw/` 配置をしない**。

## いつ使うか（トリガー）

- 「GA4 の受注が同期されているか確認したい」（`ga4-orders list` / `get`）
- 「`sync_status` を `synced` にし、`eccube_order_id` を紐づけたい」（`ga4-orders update`）
- 「バックフィル / テストで受注を 1 件登録したい」（`ga4-orders create`。必須は `transaction_id` / `value`）

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
make ga4-orders-list LIMIT=10 OFFSET=0       # 一覧（`--format csv` は固定の列）
make ga4-orders-get ID=7                     # 1 件（text は id / transaction_id / sync_status）
make ga4-orders-update ID=7 INPUT='{"sync_status":"synced","eccube_order_id":1234}'
make ga4-orders-delete ID=7
make ga4-orders-create INPUT='{"transaction_id":"invented-tx-1","value":1500.00}'   # バックフィル・テスト用
```

| 変数 | 既定 | 値 |
|---|---|---|
| `ID` | （get / update / delete で必須） | GA4 受注 ID（`ga4_order_id`） |
| `INPUT` | （create / update で必須） | 本文の JSON（または `INPUT=@body.json`。create の必須は `transaction_id` / `value`） |
| `LIMIT` / `OFFSET` | （API の既定） | 一覧の件数 / 読み飛ばし（`list` のみ） |
| `NEWS_ENV` / `ALLOW_PROD_WRITE` / `FORMAT` / `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | news と同じ | |

- `csv` の列は `id,transaction_id,value,tax,shipping,coupon,user_id,device_category,referrer,source,medium,campaign,items`
  の固定（`items` の入れ子配列は 1 セル。`sync_status` / `eccube_order_id` は json / verbatim で読む）
- `text` の書き込み要約は `status` / `message` / `ga4_order_id` / `sync_status`（実装済みの受信端点は
  `{"status":"accepted",…}` の形を返す — 実測。応答に無い項目は出ない）
- `--env prod` の書き込み（create / update / delete）は `--allow-prod-write` が無ければ exit 2。読み取りは不要
- **応答の封筒は完全には観測できていない**: 実装済みなのは受信（POST）だけで、一覧 / 詳細 / 更新 / 削除は
  まだ shop 側の実装が見当たらない（2026-10-19 時点の読み取り）。json / verbatim はそのまま渡すが、
  **csv / text が exit 1 になる場合は封筒が仮定（news / contact 型）と違う** — 呼び出し側は json を使う
  （付録 A.18）

## 証跡とオフライン再現（ga4-orders）

```sh
make ga4-orders-update ID=7 INPUT='{"sync_status":"synced"}'   # 記録（.cassettes/<UTC>-ga4-orders-update-7.jsonl）
make ga4-orders-update ID=7 INPUT='{"sync_status":"synced"}' REPLAY=.cassettes/…-ga4-orders-update-7.jsonl
```

- 1 コマンド = **2 frame**（`send` / `recv`）。400 / 401 / 404 / **405** / 500 もカセットに残り、replay は**同じ失敗**を返す
- **`X-GA4-API-Key` と dev の `Authorization` は記録前に `[REDACTED]`**（値はカセット・stdout・stderr に出ない）
- **カセットは売上・受注を含み、レダクトされない**。`.cassettes/`（gitignore）にだけ置き、**コミット・共有しない**。`raw/` に置かない

---

---

# openseo（ローカル OpenSEO の MCP over HTTP。5 コマンド）

OpenSEO（ローカル Docker のコンテナ `repo-open-seo-1`。`ghcr.io/every-app/open-seo`）の MCP エンドポイントを、
**VCR を通す薄いプロキシ**として扱う。プロジェクト一覧の解釈・キーワードの語彙検証・ページングの自動化・
リトライ・レート制限の待ち・値の解釈・正規化は**無い**（サーバーが返したエラーはそのまま返る）。仕様の正は
seo-operations の `openseo-mcp` スキル。**1 コマンド = 1 往復**（`initialize` なしで `tools/call` を 1 回 POST。
実測 2026-10-19）。

## いつ使うか（トリガー）

- 「OpenSEO のプロジェクト id を知りたい」（`list-projects`）
- 「〈キーワード〉の検索ボリューム / KD / CPC / intent を取りたい」（`keyword-metrics`）
- 「このドメインがどのクエリで上位にいるか見たい」（`ranked-keywords`）
- 「このドメインのオーガニック流入 / キーワード数 / 被リンクの概観を見たい」（`domain-overview`）
- 「〈キーワード〉の SERP で競合しているドメインを見たい」（`serp-competitors`）
- 「OpenSEO の取得を証跡付きで残したい」（カセットが証跡になる）

## 前提: ローカル Docker（credential は無い）

- 相手は**このマシンの Docker コンテナ**（`repo-open-seo-1`、`http://127.0.0.1:3001/mcp`）。**netloom は
  起動・停止しない** — `docker start repo-open-seo-1`（または seo の `start_openseo.sh`）は呼び出し側の作業
- **credential は要らない**（API キーもトークンも無い。netloom は環境変数を読まない）
- **落ちていれば exit 1**（`Connection refused` / `HTTP <status>` の 1 行。その失敗もカセットに残る）
- エンドポイントはコードの定数（`internal/adapters/sources` の 1 か所）。別マシンではそこを直す

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
# 1) プロジェクト一覧（id は次の 4 コマンドが取る。json / text / verbatim）
make openseo-list-projects

# 2) キーワードメトリクス（KEYWORDS はカンマ区切り → 配列で送られる）
make openseo-keyword-metrics PROJECT_ID=<id> KEYWORDS='h4cbh,h4cbh 副作用'
make openseo-keyword-metrics PROJECT_ID=<id> KEYWORDS='h4cbh' FORMAT=csv OUT=/tmp/kwm.csv

# 3) ランクキーワード（行は深い入れ子。json / text / verbatim。csv は無い）
make openseo-ranked-keywords PROJECT_ID=<id> TARGET=thch-vape.shop

# 4) ドメイン概観（1 オブジェクト。json / text / verbatim。csv は無い）
make openseo-domain-overview PROJECT_ID=<id> DOMAIN=thch-vape.shop

# 5) SERP 競合（KEYWORDS はカンマ区切り → 配列。行は provider の自由形式。json / text / verbatim。csv は無い）
make openseo-serp-competitors PROJECT_ID=<id> KEYWORDS='h4cbh,h4cbh 副作用'
```

バイナリを直接叩く場合は `bin/netloom openseo list-projects` /
`bin/netloom openseo keyword-metrics --project-id … --keywords …` /
`bin/netloom openseo ranked-keywords --project-id … --target …` /
`bin/netloom openseo domain-overview --project-id … --domain …` /
`bin/netloom openseo serp-competitors --project-id … --keywords …`。

| 変数 | 既定 | 値 |
|---|---|---|
| `PROJECT_ID` | （keyword-metrics / ranked-keywords / domain-overview / serp-competitors で必須） | OpenSEO のプロジェクト id（`list-projects` の `projects[].id`） |
| `KEYWORDS` | （keyword-metrics / serp-competitors で必須） | カンマ区切りのキーワード（配列で送る。個数の上限は server 側） |
| `TARGET` | （ranked-keywords で必須） | ドメインまたは URL（そのまま送る） |
| `DOMAIN` | （domain-overview で必須） | 概観を取るドメイン（そのまま送る） |
| `FORMAT` | `json` | keyword-metrics: `json` / `csv` / `text` / `verbatim`、他の 4 つ: `json` / `text` / `verbatim` |
| `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | 他と同じ | |

## 出力の読み方

- `json`（既定）は**ツール結果の構造化文書**（`structuredContent`）: list-projects = `{projects:[…], meta}`、
  keyword-metrics = `{keywords:[…], meta}`（`search_volume` / `keyword_difficulty`（null あり）/ `cpc`（null あり）/
  `main_intent` / `competition` / `monthly_searches`）、ranked-keywords = `{keywords:[…], totalCount, meta}`（行は
  `keyword_data` / `ranked_serp_element` の深い入れ子）、domain-overview = **1 オブジェクト**
  （`domain` / `organicTraffic` / `organicKeywords` / `backlinks` / `referringDomains` / `hasData` / `fetchedAt` / `meta`。
  null の値あり。実測 2026-10-19）、serp-competitors = `{competitors:[…], meta}`（**行は provider の自由形式**。
  実測では空の配列）。`_meta` は `verbatim` で読める
- `csv` は **keyword-metrics のみ**。列は `keyword,search_volume,keyword_difficulty,cpc,competition,main_intent`
  の固定で、null（スキルで `—` の値）は空セル。他の 4 コマンドの `--format csv` は exit 2
  （ranked-keywords は深い入れ子、domain-overview は 1 オブジェクト、serp-competitors は行が自由形式 — 列の選択 = 解釈になるため）
- `text` は provider のテキスト（人が読む表。`keyword | volume | KD | CPC | competition | intent`）
- **値を解釈しない**: プロジェクトの意味・キーワードの採否・順位の比較は呼び出し側

## 失敗の見分け（openseo）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx（JSON-RPC の result） | — |
| 1 | **Docker が落ちている / 接続失敗**・4xx / 5xx・JSON-RPC の error・ツールの isError・replay 不一致 | `docker ps \| grep open-seo` → `docker start repo-open-seo-1`。それ以外は stderr の 1 行とカセットを読む |
| 2 | 引数・設定（`--project-id` / `--keywords` / `--target` / `--domain` 欠落、空のキーワード、csv の語彙外、`--replay` と `--cassette` の併用） | 引数を直す |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |

## 証跡とオフライン再現（openseo）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-openseo-<command>-<target>.jsonl）
make openseo-keyword-metrics PROJECT_ID=<id> KEYWORDS='h4cbh'

# 同じ request で再生（ネットも Docker も使わない。method + url + payload が一致しないと exit 1）
make openseo-keyword-metrics PROJECT_ID=<id> KEYWORDS='h4cbh' REPLAY=.cassettes/…-openseo-keyword-metrics-h4cbh.jsonl
make openseo-domain-overview PROJECT_ID=<id> DOMAIN=thch-vape.shop REPLAY=.cassettes/…-openseo-domain-overview-thch-vape-shop.jsonl
make openseo-serp-competitors PROJECT_ID=<id> KEYWORDS='h4cbh,h4cbh 副作用' REPLAY=.cassettes/…-openseo-serp-competitors-h4cbh.jsonl
```

- 1 コマンド = **2 frame**（`send` = JSON-RPC の `tools/call`、`recv` = JSON-RPC の応答）。失敗もカセットに残る
- **カセットはプロジェクト id と実キーワードのメトリクスを含む**ので `.cassettes/`（gitignore）にだけ置き、
  **コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**（編集・削除しない）

---

# gmail（送信。既存の Gmail MCP サーバーを再利用）

Gmail の送信（`@gongrzhe/server-gmail-autoauth-mcp`、stdio）を **VCR を通す薄いプロキシ**として扱う。
宛先の形式・件名・本文の検証は**無い**（値はそのまま送る）。**OAuth はサーバー側**で、credential は
サーバーが `~/.gmail-mcp/` から読む（netloom は読まない）。**1 コマンド = 1 MCP 往復**（`tools/call` 1 回。
実測 2026-10-19）。

**送信は副作用**（実メールが 1 通飛ぶ）。live の送信は owner の承認があるときだけ実行する。

## いつ使うか（トリガー）

- 「メールを送って」「アラートをメールで出して」（`send-email`）
- 「送信の証跡をカセットに残したい」（1 コマンド = 1 往復が記録される）

## 前提: サーバー側の OAuth（netloom は credential を読まない）

- 相手は **`npx -y @gongrzhe/server-gmail-autoauth-mcp`**（stdio）。`npx` が PATH に要る
- **OAuth はサーバー側**で、credential はサーバーが `HOME` の `~/.gmail-mcp/`
  （`gcp-oauth.keys.json` / `credentials.json`）から読む。**netloom は読まない**（環境変数も無い）
- **送信は副作用**: live は実メールが飛ぶ。owner の承認なしに実行しない
- ネットワークが無い・再現したいときは `REPLAY=<カセット>`（メールは飛ばない）

## 実行（1 コマンド = 1 往復 = カセット 1 セッション）

```sh
# 送信（live = 実際にメールが飛ぶ。owner 承認のうえで）
make gmail-send-email TO='alert@example.test' SUBJECT='日次アラート' BODY='本文です'
make gmail-send-email TO='a@example.test, b@example.test' SUBJECT='…' BODY='…'   # 宛先はカンマ区切り → 配列

# 記録済みカセットから再現（ネットも npx も使わない。メールは飛ばない）
make gmail-send-email TO='alert@example.test' SUBJECT='日次アラート' BODY='本文です' REPLAY=.cassettes/…-gmail-send-email-alert-example-test.jsonl
```

バイナリを直接叩く場合は `bin/netloom gmail send-email --to … --subject … --body …`。

| 変数 | 既定 | 値 |
|---|---|---|
| `TO` | （必須） | 宛先。カンマ区切り（1 件でも配列で送る。形式はサーバーの判定） |
| `SUBJECT` | （必須） | 件名（そのまま送る） |
| `BODY` | （必須） | 本文（そのまま送る。`@FILE` は無い。長文はシェルで渡す） |
# Meta Graph API（Facebook Page / Instagram。2 送信元。5 コマンド）

Meta Graph API（base URL は `https://graph.facebook.com/v25.0`。呼び出し側の `fetch_meta_metrics.py` の `API_VER` と同じ）を**VCR を通す薄いプロキシ**として扱う。fields / metric の語彙検証・ページングの自動化・リトライ・レート制限の待ち・値の解釈・正規化は**無い**（Meta が返したエラーはそのまま返る）。**1 コマンド = 1 往復**。

**送信元が 2 つあるのは credential が 2 系統だから**: netloom の送信元は「host + credential」が 1 対 1。Facebook Page の投稿は `PAGE_TOKEN`、Instagram は `USER_TOKEN` を読む（呼び出し側の `PAGE_ID` / `IG_ACCOUNT_ID` は**credential ではなく対象** — `--page-id` / `--ig-account-id` で渡す）。

## いつ使うか（トリガー）

- 「Facebook Page の投稿一覧がほしい」（`meta-page posts`）
- 「この Facebook 投稿 1 件の中身/インサイトがほしい」（`meta-page post` / `post-insights`）
- 「Instagram のメディア一覧/インサイトがほしい」（`meta-instagram media` / `media-insights`）
- 「Meta の取得を証跡付きで残したい」（カセットが証跡になる）

## 前提: `PAGE_TOKEN` / `USER_TOKEN`（別々のトークン）

- **meta-page は `PAGE_TOKEN`、meta-instagram は `USER_TOKEN`** を環境変数で渡す（netloom が読む。値はコマンドラインに書かない — シェル履歴に残る）。**未設定なら 1 往復も送らず exit 2**
- 呼び出し側の置き場は env ファイル（例: `thch-vape.shop/.env.d/issues.env`）で、**ワークスペース外・chmod 600・コミットしない**。**このマシンにはまだ無いので live は未実行**（設計書 付録 A.21 の未確認 / §11 N18）
- トークンは **`Authorization: Bearer` ヘッダ**で送る（呼び出し側の `access_token` クエリではない）。理由: URL はカセットに記録されるため（ヘッダは名前ごと `[REDACTED]` になる）。**Graph API が Bearer を受け付けるかは live で未確認** — 401 が返ったら owner に相談（クエリ方式 + URL レダクトへの切替になる）
- base URL はコードの定数（`internal/adapters/sources` の 1 か所。2 送信元が共有）。別マシン・別バージョンではそこを直す

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
# 1) Facebook Page の投稿一覧（--fields / --limit はそのまま送る。ページングは回さない）
make meta-page-posts PAGE_ID=<page-id> FIELDS='id,message,created_time' LIMIT=100

# 2) Facebook 投稿 1 件 / そのインサイト（METRICS は必須。PERIOD は任意）
make meta-page-post POST_ID=<post-id> FIELDS='id,message'
make meta-page-post-insights POST_ID=<post-id> METRICS='post_fan_reach,post_engagements' PERIOD=lifetime

# 3) Instagram のメディア一覧 / メディアのインサイト（USER_TOKEN）
make meta-instagram-media IG_ACCOUNT_ID=<ig-id> FIELDS='id,caption,media_type,permalink,timestamp' LIMIT=100
make meta-instagram-media-insights MEDIA_ID=<media-id> METRICS='reach,likes,comments'
```

バイナリを直接叩く場合は `bin/netloom meta-page posts --page-id … [--fields …] [--limit N]` /
`bin/netloom meta-page post --post-id …` / `bin/netloom meta-page post-insights --post-id … --metrics … [--period P]` /
`bin/netloom meta-instagram media --ig-account-id …` / `bin/netloom meta-instagram media-insights --media-id … --metrics …`。

| 変数 | 既定 | 値 |
|---|---|---|
| `PAGE_ID` / `POST_ID` / `IG_ACCOUNT_ID` / `MEDIA_ID` | （それぞれのコマンドで必須） | 対象の id（呼び出し側が渡す。netloom は一覧も対応表も持たない） |
| `FIELDS` | （任意） | `--fields` のカンマ区切り（post / posts / media）。**語彙検証は無い** |
| `METRICS` | （insights で必須） | `--metrics` のカンマ区切り（post-insights / media-insights） |
| `PERIOD` | （任意） | `--period`（post-insights のみ。呼び出し側の例は `lifetime`） |
| `LIMIT` | （任意） | `--limit`（posts / media。そのまま渡す。0 以下も netloom は判定しない） |
| `FORMAT` | `json` | `json` / `text` / `verbatim`（**csv は無い**） |
| `CASSETTE` / `OUT` / `REPLAY` / `TIMEOUT` | 他と同じ | |

## 出力の読み方

- `json`（既定）は**ツール結果のテキストを JSON 文書として**書く: テキストが JSON 文書ならパースしてインデント 2、
  そうでなければ**文字列としての JSON 表現**（サーバーの成功応答は `Email sent successfully with ID: …` の文）
- `text` は provider のテキストそのまま（人が読む）。`verbatim` は受信した result のバイトそのまま（証跡用）
- **送信の成否は exit code と `isError` で見る**（失敗は exit 1 で、provider の文言が stderr の 1 行）

## 失敗の見分け（gmail）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 送信できた（result の text に message id） | — |
| 1 | ツールの isError・JSON-RPC の error（サーバー側の OAuth 失敗・宛先の拒否など）・replay 不一致 | stderr の 1 行とカセットを読む。OAuth なら `~/.gmail-mcp/` の状態を（サーバーの領分として）確認する |
| 2 | 引数・設定（`--to` / `--subject` / `--body` 欠落、`--format csv`、`--replay` と `--cassette` の併用） | 引数を直す |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |
| 127 | `npx` が無い | Node / `npx` を入れる（`npx --version`） |

## 証跡とオフライン再現（gmail）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-gmail-send-email-<宛先>.jsonl）
make gmail-send-email TO='alert@example.test' SUBJECT='…' BODY='…'

# 同じ request で再生（ネットも npx も使わない。tools/call の params が一致しないと exit 1）
make gmail-send-email TO='alert@example.test' SUBJECT='…' BODY='…' REPLAY=.cassettes/…-gmail-send-email-alert-example-test.jsonl
```

- 1 コマンド = init / initialized / tools/call の send と 2 つの recv。失敗もカセットに残る
- **カセットは宛先・件名・本文を含む**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有しない**。
  `raw/` に置かない。カセットは**追記のみ**（編集・削除しない）
- `json`（既定）は provider の応答を整形したもの: 一覧 = `{data:[…], paging:{…}}`、単一 = `{id, message, created_time, …}`、insights = `{data:[{name, period, values:[{value}]}]}`
- `text` は 1〜2 行の要約: 一覧・insights は `data: <件数>` と、あれば `paging.next`（次の 1 往復に使う URL。**netloom は回さない**）、単一 post は `id` / `created_time`
- `verbatim` は受信バイトそのまま（証跡用）
- **値を解釈しない**: どの metric を採用するか・DB への投入（`platform_data.db`）・前回値との比較は呼び出し側（現行の `fetch_meta_metrics.py` の側）

## 失敗の見分け（meta）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 2xx | — |
| 1 | 4xx / 5xx（401 は token、403 は権限/承認、429 はレート制限）・接続失敗・replay 不一致 | stderr の 1 行とカセットを読む。**live の 401 は Bearer 未確認の可能性**（owner に相談） |
| 2 | 引数・設定（id / `--metrics` の欠落、`PAGE_TOKEN` / `USER_TOKEN` 未設定、csv、`--replay` と `--cassette` の併用） | 引数・env を直す |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 再実行、または owner に相談 |

## 証跡とオフライン再現（meta）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-<source>-<command>-<target>.jsonl）
make meta-page-post-insights POST_ID=<post-id> METRICS='post_fan_reach,post_engagements'

# 同じ request で再生（ネットも token も使わない。method + url + payload が一致しないと exit 1）
make meta-page-post-insights POST_ID=<post-id> METRICS='post_fan_reach,post_engagements' REPLAY=.cassettes/…-meta-page-post-insights-<post-id>.jsonl
```

- 1 コマンド = **2 frame**（`send` = GET + url、`recv` = status + 応答）。失敗もカセットに残る
- **カセットは投稿本文と指標を含む**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**（編集・削除しない）

---

# mysql（EC-CUBE の MySQL。SSH トンネル + **読み取り専用**クエリ）

## いつ使うか（トリガー）

- 「商品データを確認して」「在庫を見て」「コンポーネントをコピーして」（コピー元の確認まで）
  「注文を調べて」「この URL（`/strainadmin/product/165/…`）の商品は？」のような **EC-CUBE の DB を見る依頼**
- 既存の `.github/skills/eccube-db` の手順（`lsof` で確認 → `start_mysql_tunnel.sh` → `mysql -h 127.0.0.1 -P <port> … -e "SELECT …"`）を置き換える用途
- **使わない場面**: 書き込み（INSERT / UPDATE / DELETE / DDL / `CALL`）。**netloom には書き込みが無い**（呼び出し側のスクリプトに残る）。商品・記事の更新は管理画面か呼び出し側の資産で行う

## 前提: `MYSQL_*` と `SSH_ALIAS`（値は env ファイル、netloom は名前だけ知る）

- `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_DATABASE`（**接続の同一性**。credential ではない）/ `MYSQL_USER` / `MYSQL_PASSWORD`（live の credential）/ `SSH_ALIAS`（ssh config の alias）
- **`SSH_ALIAS` は env ファイルに無い**ことが多い（移管元のスキルも `SSH_ALIAS=<alias> bash start_mysql_tunnel.sh` の形で渡していた）— `export SSH_ALIAS=<alias>` で渡す
- **コードに既定値は無い**: 1 つでも未設定なら **1 往復も送らず exit 2**（メッセージに変数名。値は出ない）
- **ポートは `MYSQL_PORT` の 1 か所**（トンネルのローカル側 = クエリが繋ぐ先。`LOCAL_PORT` は無い）。far end は定義の定数（`127.0.0.1:3306`）
- 本番 / DEV は**呼び出し側の env ファイル**の違いだけ（同じ変数名）。`--env dev|prod`（既定 dev）はカセットの同一性とトンネルの系統を表す

```sh
# 例: env ファイルを読んでから実行（値は出力しない）
set -a; source /path/to/.env.d/mysql_xs_dev.env; set +a && export SSH_ALIAS=<dev の alias>
```

## 実行（トンネル → 1 クエリ = 1 往復）

```sh
# 1) トンネル（**冪等**。既に listening なら何も起動せず同じ 1 行で exit 0）
make mysql-tunnel MYSQL_ENV=dev
make mysql-tunnel-status          # dial で判定（listening = exit 0 / そうでない = exit 1）

# 2) 読み取り（**SELECT / SHOW / DESCRIBE / DESC / EXPLAIN の 1 文だけ**）
make mysql-query SQL='SELECT id, name, product_status_id FROM dtb_product WHERE id = 165' FORMAT=csv
make mysql-query SQL='SELECT COUNT(*) AS products FROM dtb_product' FORMAT=csv MYSQL_ENV=dev
make mysql-query SQL=@query.sql FORMAT=json CASSETTE=.cassettes/local.jsonl
```

- 送れる語彙は **5 語だけ**。`INSERT` / `UPDATE` / `DELETE` / DDL / `CALL` / `WITH … SELECT` / **複文**は **1 往復も送らず exit 2**（カセットも作らない）。加えて接続は **`START TRANSACTION READ ONLY`** で開く
- **`--sql @FILE` のファイルのバイトが文**（末尾改行も含む）。同じ文を再生するには同じバイトで渡す
- `--sql` はシェルの引用に注意（値に `'` を含む文は `@FILE` が安全）
- トンネルは **netloom が起動してデタッチするだけ**（`ssh -N -f`）で、netloom はプロセスを所有しない。止めるのは呼び出し側（openseo の Docker と同じ）

## 出力形式（`FORMAT` / `--format`）

| 値 | 内容 |
|---|---|
| `json`（既定） | 結果文書: `{"columns":["id","name"],"rows":[[165,"…"]]}`（行 = 列順の値の配列。NULL は `null`） |
| `csv` | 列をヘッダにした表（表計算にそのまま入る。**NULL は空セル**） |
| `text` | `columns: id, name` と `rows: 1` の要約（人が読む。値を読むのは csv / json） |

- **`verbatim` は無い**（`FORMAT=verbatim` は exit 2）
- 値の型は DB が返したまま: 数値は数値、文字列は文字列、NULL は null。**バイナリ列はテキストになる**（UTF-8 でないバイトは置換文字。base64 は作らない）
- 1 応答の上限は 16 MiB（超えたら拒否。**切り詰めない**）— 広い表は `LIMIT` で絞る（netloom はページングを回さない）

## 失敗の見分け（mysql）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 読み取り成功 / トンネル起動・listening | — |
| 1 | DB が返したエラー（表が無い 1146 など）・接続失敗・ssh の失敗・`tunnel-status` = していない・replay 不一致 | stderr の 1 行（DB / ssh の言葉）とカセットを読む。表名・文の誤りは呼び出し側で直す |
| 2 | 読み取り専用でない文 / 複文 / `--sql` 欠落 / `MYSQL_*` 未設定 / `--env` の語彙外 / `verbatim` / tunnel に `--cassette` | 引数と env を直す（**何も送っていない**） |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`。既定 300 秒） | 文を絞る・トンネルを確かめる |
| 127 | `ssh` が無い | ssh を入れるか PATH を直す |

- **`tunnel-status` は exit code が答え**（0 = listening / 1 = していない）。stderr の 1 行がアドレスを述べる
- 失敗の frame も残る: DB のエラーは `recv` の `error`、接続失敗は `send` だけ

## 証跡とオフライン再現（mysql）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-mysql-query-<env>.jsonl）
make mysql-query SQL='SELECT COUNT(*) AS products FROM dtb_product' FORMAT=csv

# 同じ文で再生（**ssh も MySQL もネットも使わない**。SQL + 接続の同一性（env / host / port / database）が一致しないと exit 1）
make mysql-query SQL='SELECT COUNT(*) AS products FROM dtb_product' FORMAT=csv REPLAY="$C"
```

- 1 コマンド = **2 frame**: `send` = `{sql, env, host, port, database}`、`recv` = `{columns, rows}`（または `error` / `partial`）
- **照合キーは SQL + 接続の同一性**なので、**DEV のカセットが本番のクエリに答えない**。同じ文を 2 回記録したカセットは**最初の記録**が返る（§5.1 の規則 = このコマンドは文を 1 回だけ要求するので最初の記録。issue #14）
- **credentials はカセットに入らない**（`MYSQL_PASSWORD` の実値は stdout / stderr / カセットのどこにも出ない。接続の同一性にも password / user を入れていない）
- **カセットはショップの行（PII・売上を含みうる）を持つ**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有しない**。`raw/` に置かない。カセットは**追記のみ**（編集・削除しない）
- **本番 DB への読み取りは owner の承認が前提**（呼び出し側の本番 env ファイルを使う）。netloom 側の実測は DEV の読み取りだけ（2026-10-19。付録 A.23）

---

# site（自サイトの死活監視とデバッグ。判定を送信元定義に持つ唯一の送信元）

## いつ使うか（トリガー）

- 「サイトの動作確認をして」『デプロイ後に 500 が出ていないか見て』『キャッシュクリア後に確認して』
- 「フロント / マイページ / 管理画面の死活を見て」（面を変えて同じ語彙で）
- **流用の curl 手順（`curl_ec_check.sh` / ローカル検証ガイド / スキル 3 本 / AGENTS.md の curl 例）を置き換える用途**
- **使わない場面**: 常駐監視・スケジューラ・通知（cron / UptimeRobot 等は呼び出し側） / HTML の解釈・SEO 判定・スクレイピング / ログイン以外のフォーム送信・破壊的操作 / 負荷試験（netloom は逐次実行）

## 前提: 環境ごとの root と credential（名前だけを知る）

| 環境 | root | Basic | ログイン（環境別の名前 / 旧名はフォールバック） |
|---|---|---|---|
| `--env local` | `EC_LOCAL_BASE_URL`（未設定 = exit 2） | 送らない | `EC_LOCAL_ADMIN_ROUTE` + `EC_LOCAL_ADMIN_USER` / `EC_LOCAL_ADMIN_PASS`（旧名 `ECCUBE_ADMIN_ROUTE` / `ECCUBE_ADMIN_USER` / `ECCUBE_ADMIN_PASS`） |
| `--env dev`（既定） | `EC_DEV_BASE_URL`（EC-CUBE API と同じ変数） | `HTTP_BASIC_AUTH_USER` / `HTTP_BASIC_AUTH_PASS` | `EC_DEV_ADMIN_ROUTE` + `EC_DEV_ADMIN_USER` / `EC_DEV_ADMIN_PASS`（旧名は local と同じ 3 つ） |
| `--env prod` | 定数（live の shop） | 送らない | `EC_PROD_ADMIN_ROUTE` + `EC_PROD_ADMIN_USER` / `EC_PROD_ADMIN_PASS`（読み取りのみ。旧名は local と同じ 3 つ） |

- **管理画面と会員の credential は環境別の名前が先、旧名はフォールバック**（issue #25）: `EC_<ENV>_ADMIN_ROUTE` / `_ADMIN_USER` / `_ADMIN_PASS` / `_MEMBER_EMAIL` / `_MEMBER_PASSWORD`（`<ENV>` = `LOCAL` / `DEV` / `PROD`。`--env` が選ぶ。`EC_DEV_BASE_URL` と同じ family）。**旧名はその環境の環境別名が未設定のときだけ読み、変数ごとに「最初に設定されている名前が勝つ」**（混在も 1 組 — 環境別名の email + 旧名の password は pair）。旧名は**互換（移行期）および dev と prod で同じ値の店舗のための共有セット**（推奨の名前は環境別名）。**管理ルートは公開値ではない**（隠しパス）ので prod でも定数のままにしない。
- **マイページの会員ログインは任意**: `EC_<ENV>_MEMBER_EMAIL` / `EC_<ENV>_MEMBER_PASSWORD`（または旧名）の**両方**があるときだけログイン後も見る。無ければ未ログイン範囲（`/mypage/login` の 200 と保護ページの 302 → login）だけ。**片方だけは exit 2**
- **必須が欠けたら 1 往復も送らず exit 2**（カセットも作らない。メッセージは欠けた変数名を両方の綴りで出す。値は出さない。`--target front` は credential 不要で回せる）
- **`--replay` は route の名前だけを読む**（URL = 照合キー）し、credential は読まない
- **値はカセットにも stdout / stderr にも出ない**（password 系と Cookie の値は `[REDACTED]`。Set-Cookie は `Path` / `HttpOnly` などの属性だけ残る）

```sh
# 例: env ファイルを読んでから実行（値は出力しない）
set -a; source /path/to/.env.d/site.env; set +a
```

## 実行（面 × 環境。URL は定義 1 か所）

```sh
make site-check SITE_ENV=local SITE_TARGET=front SITE_PRODUCT_ID=1   # 人が読む一覧（既定 format = text）
make site-check SITE_ENV=dev   SITE_TARGET=all                       # 3 面（ログイン込み）
make site-check SITE_ENV=prod  SITE_TARGET=front                     # credential 無しで回せる読み取り
make site-check SITE_ENV=dev   SITE_TARGET=admin SITE_FORMAT=json    # 機械可読
```

- 面の語彙は **front / mypage / admin / all**（既定 all）、環境は **local / dev / prod**（既定 dev）
- **何を待つか**（送信元定義に固定）: front = `/`・`/products/list`・`/products/detail/<id>`（`--product-id`。省略時は `skipped`）・`/guide/articles`・`/contact`・`/ingredient/cbd` の 200 / mypage = `/mypage/login` の 200 と（未ログインで）`/mypage` の **302 → login** / admin = CSRF 付きログイン（GET → POST 302 → セッション確立）と `/{route}/`・`/{route}/product`・`/{route}/order` の 200
- リダイレクトは最大 5 hop まで追って履歴を出す（**ループ / 5 hop 超過 / Location なしは NG**）。**Symfony / PHP のエラー画面は 200 でも NG**（本文の既知のマーカーだけを見る）
- **応答時間は計るが、しきい値は無い**

## 出力形式（`SITE_FORMAT` / `--format`）

| 値 | 内容 |
|---|---|
| `text`（**既定**。site だけの例外） | 面ごとの一覧（判定 / status / 応答時間 / URL）。NG は最終 URL・リダイレクト履歴・主なヘッダ・段・本文の先頭・hint |
| `json` | `{source, env, target, round_trips, verdict, logins:[…], checks:[{face,url,expected,status,first_status,verdict,duration_ms,final_url,redirects,stage,error}]}` |
| `verbatim` | 受信した応答本文を順に（1 本文 = 末尾改行 1 つ。判定と証跡を分ける） |

## 失敗の見分け（site）

| exit | 意味 | 次の行動 |
|---|---|---|
| 0 | 全件 OK（ログインも確立） | — |
| 1 | 1 件以上 NG（ログイン失敗を含む） | stdout の一覧と `stage` を読む。`session` なら `ECCUBE_AUTH_MAGIC`、`csrf` ならログインルートと `_csrf_token`、`basic` なら Basic の 2 変数、`html/.cache-version` の hint は 500 の本文で出る |
| 2 | 前提不足（root / ルート / credential の未設定、接続不能） | メッセージの変数名を直す（**何も送っていない**。カセットも無い） |
| 3 / 124 / 127 | I/O / timeout / 依存（既存の共通規則） | 既存の表と同じ |

- **401 は exit 1**（stage = `basic`。dev のみ）。**credential の誤りでも値は出ない** — どの段で失敗したかだけが出る
- 判定は**決定的・機械可読**（監視からは exit code と `--format json` だけ読めばよい）

## 証跡とオフライン再現（site）

```sh
# 記録（live。CASSETTE 省略時は .cassettes/<UTC>-site-check-<env>-<target>.jsonl）
make site-check SITE_ENV=dev SITE_TARGET=all CASSETTE=.cassettes/site-dev.jsonl

# 同じコマンドで再生（**ネットも credential も使わない**。method + url + payload が一致しないと exit 1）
make site-check SITE_ENV=dev SITE_TARGET=all REPLAY=.cassettes/site-dev.jsonl
```

- **1 コマンド = 面の URL 数 + ログイン段数（+ リダイレクトの hop）の往復**。各往復は send / recv の 2 frame（`recv` は応答ヘッダも持つ — `Location` で hop をたどり、`Set-Cookie` で cookie jar を組み直す）
- ログイン POST の送信本文は**記録されない**（フィールド名と `_csrf_token` だけの evidence。password は `[REDACTED]`）。だから **`--replay` は credential 無しで同じ判定を返す**
- **カセットは管理画面・会員ページの内容とセッション状態を持つ**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有・`raw/` 配置をしない**。カセットは**追記のみ**
- **prod の live は owner の承認が前提**（読み取りのみ）。netloom 側の実測は local / dev だけ（2026-10-19。付録 A.24）

---

# bigquery（BigQuery の読み取り専用クエリ）

## いつ使うか（トリガー）

- 「BigQuery のデータを見て」「このクエリの結果を取って」（**読み取りの依頼**）
- thch-vape の `.github/bin/bigquery_mcp_server.py`（FastMCP / stdio）を置き換える用途（issue #19）
- **使わない場面**: 書き込み（INSERT / UPDATE / DELETE / MERGE / DDL）。**netloom には書き込みが無い**（呼び出し側のツールに残る）
- **課金の注意**: BigQuery は**クエリがスキャンした量に応じて課金される**。実行前に必ず `--dry-run`（課金なしの見積もり）で `total_bytes_processed` を確認し、`WHERE` で絞る。`--max-rows` は返る行数の上限であり**スキャン量の上限ではない**

## 前提: project と credential（名前だけを知る）

- **project**: `--project` → env `GOOGLE_CLOUD_PROJECT` → `GCLOUD_PROJECT`（移管元の python が読んでいた 2 つをそのまま）。**どちらも無ければ 1 往復も送らず exit 2**。`--replay` も project を要る（照合キー）
- **credential は GSC / GA4 と同じ** `GOOGLE_TOKEN_FILE` → `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`（netloom 自身が refresh grant を交換し、その往復も記録する）
- **live のトークンには bigquery スコープが要る**: `netloom auth google --source bigquery`（owner のブラウザ操作、1 回だけ。現行の ga4 / gsc 用トークンには無い。無ければ live は 403）

```sh
# 0) スコープの同意（owner が 1 回だけ。対話専用）
make auth-google AUTH_CLIENT_SECRETS=/path/to/credentials.json AUTH_SOURCE=bigquery
export GOOGLE_TOKEN_FILE="$HOME/.config/netloom/google-bigquery.json"

# 1) dry-run（**課金なし**。まずスキャン量を確認）
make bigquery-query SQL='SELECT * FROM `dataset.INFORMATION_SCHEMA.COLUMNS`' PROJECT=<project-id> DRY_RUN=1
#    → json の total_bytes_processed を読む（大きいなら WHERE で絞る）

# 2) 小さい SELECT を 1 回（パーティション・限定を推奨）
make bigquery-query SQL='SELECT 1 AS answer' PROJECT=<project-id>

# 3) オフライン再現（ネットも credential も使わない）
make bigquery-query SQL='SELECT 1 AS answer' PROJECT=<project-id> REPLAY="$C"
```

## 実行（1 コマンド = 2 往復 = カセット 4 frame）

- wire = `POST /bigquery/v2/projects/<project>/queries`、body は `{"query":…,"useLegacySql":false,"maxResults":N,"dryRun":bool}` を常に明示（standard SQL は移管元と同じ）
- **読み取り専用の門**: `SELECT` と **`WITH … SELECT`（CTE。本体が SELECT のときだけ）** で始まる 1 文だけ。`INSERT` / `UPDATE` / `DELETE` / `MERGE` / DDL / 複文 / `WITH … DML` は **1 往復も送らず exit 2**（カセットも作らない）
- **`jobComplete=false` はポーリングせず exit 1**（メッセージに `jobId`。続きは呼び出し側のツールで。設計書 §11 N26）

## 出力形式（`FORMAT` / `--format`）

- `json`（既定）= 結果文書（`fields` = schema の列名 / `rows` = 行（列順の JSON 値の配列）/ `job_id` / `total_rows` / `total_bytes_processed` / `cache_hit`。インデント 2）
- `csv` = fields をヘッダにした表（値は mysql の csv と同じ JSON 値のレンダリング。NULL は空セル）
- `text` = `rows:` と統計の要約
- `verbatim` = 受信バイトそのまま（証跡形。replay でも同じ）

## 証跡とオフライン再現（bigquery）

- **1 コマンド = 4 frame**: 交換（HTTP の send / recv）+ クエリ（`method: "query"` の send / recv。`send` = `{sql, project, dry_run?, max_rows?}`、`recv` = `{fields, rows, …, body}`）
- **照合キーは SQL + project + dry-run**。**ある project のカセットが別の project のクエリに答えない**。dry-run の記録が実行の replay に答えず、その逆も同じ。同じクエリの複数記録は**最初の記録**が返る（§5.1 の規則 = このコマンドはクエリを 1 回だけ要求するので最初の記録）
- **`--replay` はネットも credential も使わない**（交換をしない）
- **カセットはクエリ結果（業務データ）を持つ**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有・`raw/` 配置をしない**。カセットは**追記のみ**
- **live は owner 承認が前提**（課金が発生しうる）。netloom 側は BigQuery への往復を 1 回も行っていない（テストは偽 BigQuery（`httptest`）で固定。手順は `docs/plan/20261019-bigquery.md` §7）

## 失敗の見分け（bigquery）

| exit | 何が起きたか | 直し方 |
|---|---|---|
| 0 | クエリの成功 / `--dry-run` の見積もり | — |
| 1 | BigQuery のエラー（4xx / 5xx。provider の言葉が 1 行）/ `jobComplete=false`（`jobId` つき）/ replay の不一致 / 接続失敗 / 16 MiB 超 | stderr の 1 行を読む。`jobId` は呼び出し側のツールで追える / replay は同じ SQL + project + dry-run で |
| 2 | 読み取り専用でない文 / 複文 / `--sql` 欠落 / project 未設定 / `--max-rows` 0 以下 / `--format` の語彙外 | 引数と env を直す（**何も送っていない**） |
| 3 | I/O（`--out` / カセット / `@FILE` が読めない） | パスを直す |
| 124 | timeout（`--timeout`。交換 + クエリの合計） | クエリを絞る |

---

# calendar（Google Calendar。6 コマンド）

## いつ使うか（トリガー）

- 「カレンダーを見て」「予定を調べて」「予定を作って / 直して / 消して」（**読み書きの依頼**）
- thch-vape の `.github/bin/google_calendar_mcp_server.py`（FastMCP / stdio）を置き換える用途（issue #20）
- **副作用の注意**: **create / update / delete はカレンダーに影響します**（予定が作られ / 置き換えられ / 消える）。**live の書き込みは owner の承認のうえで**実行する（gmail の送信と同じ扱い）。読み取り（list / get）は副作用なし

## 前提: calendar id と credential（名前だけを知る）

- **calendar id**: `--calendar-id` → env `GOOGLE_CALENDAR_ID` → **`primary`**（Google 自身が「自分のカレンダー」を指すエイリアス。**仮定**として置いた既定 — 付録 A.26 判断 D2）。**credential ではない**ので値はカセットの URL に載る。`list-calendars` は `--calendar-id` 不要（認証が誰の一覧かを決める）
- **credential は GSC / GA4 / bigquery と同じ** `GOOGLE_TOKEN_FILE` → `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`（netloom 自身が refresh grant を交換し、その往復も記録する）
- **live のトークンには calendar スコープが要る**: `netloom auth google --source calendar`（owner のブラウザ操作、1 回だけ。書き込みにも足りる）

```sh
# 0) スコープの同意（owner が 1 回だけ。対話専用）
make auth-google AUTH_CLIENT_SECRETS=/path/to/credentials.json AUTH_SOURCE=calendar
export GOOGLE_TOKEN_FILE="$HOME/.config/netloom/google-calendar.json"

# 1) 読み取り（副作用なし）
make calendar-list-calendars                                     # カレンダー一覧（id / summary / timeZone / primary / accessRole）
make calendar-list-events TIME_MIN=2026-10-19T00:00:00Z MAX_RESULTS=10 SINGLE_EVENTS=1 FORMAT=text
make calendar-get-event EVENT_ID=<event-id>                      # 1 件

# 2) 書き込み（**副作用。owner 承認のうえで**）
make calendar-create-event INPUT='{"summary":"invented","start":{"dateTime":"2026-10-20T10:00:00+09:00"},"end":{"dateTime":"2026-10-20T11:00:00+09:00"}}'
make calendar-update-event EVENT_ID=<event-id> INPUT='{"summary":"invented (updated)"}'   # PATCH = 1 往復
make calendar-delete-event EVENT_ID=<event-id>                   # 204 本文なし = 出力なし・exit 0

# 3) オフライン再現（ネットも credential も使わない。3 形で一致）
make calendar-list-calendars REPLAY="$C"
```

## 実行（1 コマンド = 2 往復 = カセット 4 frame）

- wire = `GET /users/me/calendarList` / `GET|POST /calendars/<id>/events` / `GET|PATCH|DELETE /calendars/<id>/events/<eventId>`（base = `https://www.googleapis.com/calendar/v3`）
- **`list-events` は素通し**: `--time-min` / `--time-max` / `--max-results` / `--query` / `--single-events` / `--order-by` / `--page-token` は**与えたときだけ** query に載る（移管元 python の `timeMin=now` / `maxResults=20` / `singleEvents=true` は持ち込まない）。`--max-results` 0 以下は exit 2
- **`--input` は JSON であることだけ**を見て compact して送る（`@FILE` 可。**イベントのフィールドは語彙検証しない** — provider の答えが判定）
- **`update-event` は PATCH = 1 往復**（移管元の read-modify-write は採らない。パッチ本文は呼び出し側が書く）
- id は 1 パスセグメントにエスケープ（`:` は `%3A`）

## 出力形式（`FORMAT` / `--format`）

- `json`（既定）= 応答本文をインデント 2（`delete` の 204 は出力なし）
- `text` = リストは `calendars: N` / `events: N`（items が無い = 0 = **成功**）、イベントは `id:` / `summary:` / `status:`（答えが主張する member だけ。1 つも無ければ拒否）
- `verbatim` = 受信バイトそのまま（証跡形。replay でも同じ）
- **`csv` は無い**（`start` / `end` が date と dateTime の 2 形、`attendees` は配列 — 列を固定すると netloom が解釈することになる。`--format csv` は exit 2）

## 証跡とオフライン再現（calendar）

- **1 コマンド = 4 frame**: 交換（HTTP の send / recv）+ データ（HTTP の send / recv。**新しい frame は無い**）
- **照合キーは method + url + payload**（HTTP の規則そのまま）。calendar id / event id は URL に載る。**ある calendar / event のカセットが別の予定に答えない**。同じ request の複数記録は**最初の記録**が返る（§5.1 の規則 = このコマンドはデータ要求を 1 回だけ行うので最初の記録）
- **`--replay` はネットも credential も使わない**（交換をしない）
- **カセットは予定の本文・参加者・カレンダー名（業務・個人データ）を持つ**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有・`raw/` 配置をしない**。カセットは**追記のみ**
- **live は 1 往復も未実行**（書き込みは副作用 = owner 承認が前提。読み取りも、calendar スコープの同意が実在するか不明のため未実行。手順は `docs/plan/20261019-calendar.md` §7）

## 失敗の見分け（calendar）

| exit | 何が起きたか | 直し方 |
|---|---|---|
| 0 | 6 コマンドの成功（**0 件のリストを含む**。delete の 204 = 出力なし） | — |
| 1 | Calendar のエラー（4xx / 5xx。provider の言葉が 1 行）/ `invalid_grant`（交換の失敗）/ replay の不一致 / 接続失敗 | stderr の 1 行を読む。replay は同じ calendar / event / query で |
| 2 | `--event-id` / `--input` 欠落 / `--input` が JSON でない / `--max-results` 0 以下 / `--format` の語彙外 / credential 未設定 | 引数と env を直す（**何も送っていない**） |
| 3 | I/O（`--out` / カセット / `@FILE` が読めない） | パスを直す |
| 124 | timeout（`--timeout`。交換 + データの合計） | 窓を絞る |


# apps-script（Google Apps Script API。13 コマンド）

## いつ使うか（トリガー）

- 「Apps Script のプロジェクトを見て / 作って / ソースを更新して / バージョンとデプロイを管理して」「スクリプトの関数を実行して」（**読み書きと実行の依頼**）
- thch-vape の `.github/bin/gas-mcp-server-server.py`（FastMCP / stdio）を置き換える用途（issue #21）
- **副作用の注意**: **書き込み 7 つは Projects に影響します**（プロジェクトが作られ / ソースが置き換えられ / バージョン・デプロイが作られ / 消える）。とくに **`run-script` は任意の関数を実行します** — スクリプトができること（メール送信・シート書き込み等）はすべて起こりうる。**live の書き込みと実行は owner の承認のうえで**実行する（gmail の送信と同じ扱い）。読み取り（get / list）は副作用なし

## 前提: script id と credential（名前だけを知る）

- **script id**: `--script-id` が**必須**（`list-processes` のみ省略可 = `userProcessFilter.scriptId` のフィルタ）。**netloom は script id を推測しない・一覧も持たない** — id は呼び出し側が知っている（Drive のファイル id）
- **credential は GSC / GA4 / bigquery / calendar と同じ** `GOOGLE_TOKEN_FILE` → `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`（netloom 自身が refresh grant を交換し、その往復も記録する）
- **live のトークンには script スコープが要る**: `netloom auth google --source gas`（owner のブラウザ操作、1 回だけ。**6 スコープ = 旧 `gas-mcp-server-auth.py` と同じ**。送信元名が `apps-script` なのは A.0「略称を使わない」ため — `gas` はスコーププロファイルの名前）

```sh
# 0) スコープの同意（owner が 1 回だけ。対話専用）
make auth-google AUTH_CLIENT_SECRETS=/path/to/credentials.json AUTH_SOURCE=gas
export GOOGLE_TOKEN_FILE="$HOME/.config/netloom/google-gas.json"

# 1) 読み取り（副作用なし）
make apps-script-get-project SCRIPT_ID=<script-id>                     # メタデータ
make apps-script-get-project-content SCRIPT_ID=<script-id>             # ソースファイル一覧
make apps-script-list-project-versions SCRIPT_ID=<script-id> PAGE_SIZE=10
make apps-script-list-deployments SCRIPT_ID=<script-id>
make apps-script-get-deployment SCRIPT_ID=<script-id> DEPLOYMENT_ID=<id>
make apps-script-list-processes PAGE_SIZE=10                           # 全 script のプロセス

# 2) 書き込みと実行（**副作用。owner 承認のうえで**）
make apps-script-create-project TITLE='invented'
make apps-script-update-project-content SCRIPT_ID=<id> FILES=@content.json   # **全ファイル置換**
make apps-script-create-version SCRIPT_ID=<id> DESCRIPTION='v1'
make apps-script-create-deployment SCRIPT_ID=<id> VERSION_NUMBER=1
make apps-script-run-script SCRIPT_ID=<id> FUNCTION=hello PARAMETERS='["world"]'   # **関数の実行**
make apps-script-delete-deployment SCRIPT_ID=<id> DEPLOYMENT_ID=<id> # 204 本文なし = 出力なし・exit 0

# 3) オフライン再現（ネットも credential も使わない。3 形で一致）
make apps-script-get-project SCRIPT_ID=<script-id> REPLAY="$C"
```

## 実行（1 コマンド = 2 往復 = カセット 4 frame）

- wire = `POST|GET /projects` / `GET /projects/{id}` / `GET|PUT /projects/{id}/content` / `GET|POST /projects/{id}/versions` / `GET|POST /projects/{id}/deployments` / `GET|PUT|DELETE /projects/{id}/deployments/{deploymentId}` / `POST /scripts/{id}:run` / `GET /processes`（base = `https://script.googleapis.com/v1`）
- **`--files` / `--parameters` は JSON であることだけ**を見て compact して送る（`@FILE` 可。**ファイル・パラメータの語彙検証はしない** — provider の答えが判定）。`--files` は `{"files": …}` の envelope に包まれる（endpoint のスキーマの形）
- **素通し**: `--page-size` / `--page-token` / `--manifest-file-name` / `--description` / `--dev-mode` は**与えたときだけ** wire に載る（移管元の pageSize=50 / manifestFileName="appsscript" / devMode=false は持ち込まない）。`--page-size` / `--version-number` の 0 以下は exit 2（typo 検査のみ）
- id は 1 パスセグメントにエスケープ（`:` は `%3A`。`/scripts/{id}:run` の `:run` は API 自身の接尾辞）
- **`update-project-content` は全ファイル置換**: 既存ファイルはすべて消えて files の配列どおりになる（netloom は検証もマージもしない。呼び出し側が全ファイルを含めた配列を渡す）

## 出力形式（`FORMAT` / `--format`）

- `json`（既定）= 応答本文をインデント 2（`delete-deployment` の 204 は出力なし）
- `text` = リストは `versions: N` / `deployments: N` / `processes: N` / `files: N`（member が無い = 0 = **成功**）、プロジェクトは `scriptId:` / `title:`、デプロイは `deploymentId:` / `updateTime:`（答えが主張する member だけ。1 つも無ければ拒否）、`run-script` は封筒の `result:` / `error:`（**そのまま。解釈しない**）
- `verbatim` = 受信バイトそのまま（証跡形。replay でも同じ）
- **`csv` は無い**（description はテキスト、deploymentConfig はオブジェクト — 列を固定すると netloom が解釈することになる。`--format csv` は exit 2）
- **`run-script` の封筒 `{response:{result,error}}` は解釈しない**: HTTP 200 で error が返っても **exit 0**（provider の応答のまま。text / json で error を読む）

## 証跡とオフライン再現（apps-script）

- **1 コマンド = 4 frame**: 交換（HTTP の send / recv）+ データ（HTTP の send / recv。**新しい frame は無い**）
- **照合キーは method + url + payload**（HTTP の規則そのまま）。script id / deployment id は URL に載る。**ある script のカセットが別の script に答えない**。同じ request の複数記録は**最初の記録**が返る（§5.1 の規則 = このコマンドはデータ要求を 1 回だけ行うので最初の記録）
- **`--replay` はネットも credential も使わない**（交換をしない）
- **カセットはソースコード・デプロイメント・プロセス（業務データ）を持つ**ので `.cassettes/`（gitignore）にだけ置き、**コミット・共有・`raw/` 配置をしない**。カセットは**追記のみ**
- **live は 1 往復も未実行**（書き込み 7 つと run-script は副作用 = owner 承認が前提。読み取りも、6 スコープのトークンが実在するか不明。手順は `docs/plan/20261019-apps-script.md` §7）

## 失敗の見分け（apps-script）

| exit | 何が起きたか | 直し方 |
|---|---|---|
| 0 | 13 コマンドの成功（**0 件のリストを含む**。delete の 204 = 出力なし。run-script の封筒内 error も exit 0） | — |
| 1 | Apps Script API のエラー（4xx / 5xx。provider の言葉が 1 行）/ `invalid_grant`（交換の失敗）/ replay の不一致 / 接続失敗 | stderr の 1 行を読む。replay は同じ script / deployment / query で |
| 2 | `--script-id` / `--title` / `--files` / `--function` / `--version-number` / `--deployment-id` 欠落 / JSON でない `--files` / `--parameters` / `--page-size`・`--version-number` の 0 以下 / `--format` の語彙外 / credential 未設定 | 引数と env を直す（**何も送っていない**） |
| 3 | I/O（`--out` / カセット / `@FILE` が読めない） | パスを直す |
| 124 | timeout（`--timeout`。交換 + データの合計） | 窓を絞る |

---

# PageSpeed Insights / CrUX（psi / crux。1 コマンド = 1 往復。**非公開 API**）

**非公開 API（issue #24。owner 決定 2026-10-18）**: **consumer（seo-operations）の測定系（ローカル Lighthouse）が正**で、`psi` / `crux` は**明示指示があるときだけ**使う（**置き換えを意図しない**）。理由 = **別測定系**なので Before/After に混ぜられない（Source Separation）。**コマンドは残る** = ローカル Lighthouse が使えないとき（CI・別マシン）の緊急手段。

## いつ使うか（トリガー）

- **明示指示があるときだけ**（下の注記。既定の導線ではない）。ローカル Lighthouse が使えない環境（CI・別マシン）でページの測定が必要 / PSI の生 JSON（`lighthouseResult` / `loadingExperience` / `analysisUTCTimestamp`）が要る → **`psi run`**
- 実ユーザーのコア バイタル（CrUX データセット）が要る（日次のレコード = `crux query`、約 6 か月の履歴（週次の系列）= `crux history`）→ **`crux`**
- どちらも**ローカル Lighthouse とは別測定系**: 数値を混ぜて比較しない（consumer の AGENTS.md「Source Separation」）。ローカル Lighthouse が使えるならそれが正

## 前提: query キー（credential はヘッダではなくクエリ）

- `psi` は **`PAGESPEED_API_KEY`**、`crux` は **`CRUX_API_KEY`**（**同じ値でも変数名は両方設定する** — netloom は「このコマンドが読む変数」を推測しない）
- env ファイル（ワークスペース外・`chmod 600`・コミットしない）に置き、netloom が cwd の env ファイルから自動で読む（`export` でもよい）
- **未設定なら 1 往復も送らず exit 2（カセットも作らない）。`--replay` でも要る**（キーがカセットの URL の一部 = 照合キーだから）
- **キーはカセットの URL に残る**（意図的 = replay の URL 照合のため）。stdout と stderr の失敗行には出ない（`key=[REDACTED]`）。だから **カセットは `.cassettes/`（gitignore）にだけ置き、コミット・共有しない**

## 実行（1 コマンド = 1 往復 = カセット 2 frame）

```sh
# ページの Lighthouse 測定（PSI は quota を消費する。キャッシュ回避は呼び出し側）
make psi-run PSI_URL=https://www.thch-vape.shop/ PSI_STRATEGY=mobile \
  PSI_CATEGORIES=performance,accessibility,best-practices,seo CASSETTE=data/psi/cassettes/$(date -u +%Y%m%dT%H%M%SZ)-psi-run.jsonl
#   category は各 1 つの query パラメータとして送られる（カンマ区切りを netloom が翻訳）
#   --format text でカテゴリ score と lab 監査の displayValue の要約（判定はしない）

# CrUX: 日次のレコード / 履歴
make crux-query   CRUX_ORIGIN=https://www.thch-vape.shop CRUX_FORM_FACTOR=PHONE CASSETTE=data/crux/cassettes/$(date -u +%Y%m%dT%H%M%SZ)-crux-query.jsonl
make crux-history CRUX_ORIGIN=https://www.thch-vape.shop CRUX_FORM_FACTOR=PHONE COLLECTION_PERIODS=5 CASSETTE=data/crux/cassettes/$(date -u +%Y%m%dT%H%M%SZ)-crux-history.jsonl

# オフライン再現（ネットなし。キーは要る。request が一致しなければ exit 1）
make psi-run PSI_URL=https://www.thch-vape.shop/ REPLAY=data/psi/cassettes/<記録>.jsonl FORMAT=verbatim
```

## キャッシュと quota（呼び出し側の仕事）

- **PSI は同一 URL をキャッシュする**。新鮮な測定が必要なら**呼び出し側が URL にダミーのクエリを付ける**（consumer の運用 = `?psrun=N` 等）。**netloom は URL をそのまま送る**（書き換えない）
- **PSI はキーの quota を消費する**（キーなし実行は共有クォータを枯渇させる — だから consumer はキー必須で運用する。同じ理由で netloom も未設定を exit 2 で止める）。crux も Google Cloud 側の quota。**live は owner 承認が前提**（現時点では 1 往復も未実行）

## 失敗の見分け

| exit | 何が起きたか | 直し方 |
|---|---|---|
| 0 | 2xx（要約の材料が無い応答も text では exit 1 になる点を除く） | — |
| 1 | API のエラー（400 / 404 / 429。provider の言葉が 1 行、キーは `key=[REDACTED]`）/ replay の不一致 / text 要約の材料なし | stderr の 1 行を読む。replay は同じ url / origin とキーで |
| 2 | `--url` 無し / origin と url 両方無し / `--collection-periods` 0 以下 / 語彙外 `--format` / **キー未設定** | 引数と env を直す（**何も送っていない**） |
| 3 | I/O（`--out` / カセット） | パスを直す |
| 124 | timeout（`--timeout`） | PSI は測定に 1 分超をかけることがある。窓を広げる |

---

# してはいけないこと

- netloom に**解釈・比較・正規化**を求める（プロキシは判定しない。Apify の items も X の投稿も GA4 の集計値も同じ）
- カセットを書き換える・削除する
- 取得値をそのまま publication に使う（採用は呼び出し側の pipeline とゲートを通す）
- `raw/` にカセットを置く
- provider（google-trends-mcp / Apify API / X API / GA4 Analytics Data API / OpenSEO の MCP エンドポイント）を直接実行する（証跡が残らない）
- `APIFY_TOKEN` / `X_BEARER_TOKEN` の実値をコマンドライン・メモ・カセットに書く
- GA4 の credential（トークンファイルの中身）を出力・貼り付け・コミットする（netloom は `GOOGLE_TOKEN_FILE` / `GOOGLE_*` から読むだけ。値は stdout / stderr / カセットに出ない）
- **X のカセットをコミットする・共有する**（投稿データを含む）
- **GA4 のカセットをコミットする・共有する**（プロパティの集計値を含む）
- **GSC のカセットをコミットする・共有する**（自分のサイトの検索語と数値を含む）
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` の実値をコマンドライン・メモ・カセットに書く（netloom が環境変数から読む）
- `SEO_API_KEY` / `HTTP_BASIC_AUTH_USER` / `HTTP_BASIC_AUTH_PASS` の実値をコマンドライン・メモ・カセットに書く（netloom が環境変数から読む）
- **`GA4_API_KEY`（ga4-orders の `X-GA4-API-Key`）の実値をコマンドライン・メモ・カセットに書く**（netloom が環境変数から読む。`SEO_API_KEY` とは別の資格情報）
- **本番（`NEWS_ENV=prod`）への書き込みを `ALLOW_PROD_WRITE=1` なしで実行する**（exit 2 で止まる。書き込みだと知らずに出すのを避けるための門）
- **news / cache のカセットをコミット・共有する**（ショップのニュースを含む）
- **article のカセットをコミット・共有する**（未公開の原稿本文を含む）
- **contact / ga4-orders のカセットをコミット・共有する**（顧客の PII / 売上を含み、**レダクトされない**）
- **`X-GA4-API-Key` / `GA4_API_KEY` を ga4（GA4 Data API）の送信元と混同する**（別物。あちらは Analytics Data API を Google の refresh grant で読む）
- **openseo のカセットをコミット・共有する**（プロジェクト id と実キーワードのメトリクスを含む）
- **gmail のカセットをコミット・共有する**（宛先・件名・本文を含む）
- **gmail の live 送信を owner 承認なしに実行する**（実メールが飛ぶ。gmail の節）
- **gmail の credential（`~/.gmail-mcp/` の中身）を読む・出力する**（サーバーの領分。netloom は関知しない）
- **`PAGE_TOKEN` / `USER_TOKEN` の実値をコマンドライン・メモ・カセットに書く**（netloom が環境変数から読む。`Authorization: Bearer` として送る）
- **meta-page / meta-instagram のカセットをコミット・共有する**（投稿本文と指標を含む）
- **トークンファイル（`$HOME/.config/netloom/google-*.json`）の値を出力・貼り付け・コミットする**（credential そのもの。`netloom auth google` の stdout / stderr はパスとスコープだけ）
- **`netloom auth google` を CI・自動テスト・スクリプトから実行する**（対話専用。exit 2 で止まる。同意は人が 1 回だけ行う）
- **OpenSEO コンテナの起動・停止を netloom に期待する**（プロセス管理は呼び出し側。落ちていれば exit 1 で、その失敗もカセットに残る）
- **X の live request を owner 承認なしに実行する**（当面禁止）
- **`MYSQL_PASSWORD` / `MYSQL_USER` の実値をコマンドライン・メモ・カセットに書く**（netloom が環境変数から読む。接続の同一性にも password / user は入らない）
- **mysql のカセットをコミット・共有する**（ショップの行 = PII・売上を含みうる）
- **本番 DB への読み取りを owner の承認なしに実行する**（`--env prod` は呼び出し側の本番 env ファイルを使う。実測は DEV の読み取りだけ）
- **netloom に DB の書き込みを求める**（INSERT / UPDATE / DELETE / DDL / `CALL` は**作っていない**。exit 2 で止まる。ショップの書き込みは呼び出し側の資産）
- **ssh の鍵・パスフレーズを netloom に渡す**（ssh 自身が `~/.ssh/config` と agent を使う。netloom は credential を読まない）

# 研究リポジトリ（japan-cannabinoid-trends）への取り込み

netloom は **producer**。採用は JCT 側の staging declaration / collection pipeline
（`make stage` → `make adopt-all`）が行う。netloom は採用判定・publication・release をしない。

# まだ無いもの（欲しくなったら owner に相談）

- **mysql の書き込み**（INSERT / UPDATE / DELETE / DDL / `CALL`）: **作らないと決めている**（owner 決定 6。呼び出し側に残る）。`WITH … SELECT`（CTE の読み取り）も語彙外（必要になったら owner 判断）
- **mysql のアカウント分離（読み取り専用ユーザー）**: **推奨だが netloom の作業ではない**（DB 側 = consumer の運用判断。netloom の門は語彙 + `START TRANSACTION READ ONLY` の 2 層）
- **mysql の停止コマンド（`tunnel-stop`）**: 作っていない（トンネルは `ssh -N -f` でデタッチし、プロセスは呼び出し側のもの。§付録 A.23）
- **mysql の本番 live**: **未実行**（owner 承認が前提。手順は `docs/plan/20261019-mysql.md` §7）
- **apps-script の live は未実行**（書き込み 7 つと run-script は副作用 = owner 承認が前提。読み取りも、6 スコープのトークンが実在するか不明。手順は `docs/plan/20261019-apps-script.md` §7）。呼び出し側（thch-vape.shop の `.github/bin/gas-mcp-server-server.py` と `.mcp.json` の gas エントリ）の置き換えは**未処理**（設計 §11 N28。認証側の `gas-mcp-server-auth.py` は #11 で置き換え済み）
- **mysql の UNIX socket 接続 / far end が別ホストの系**: 未対応（TCP のみ。`internal/adapters/sources` の `mysqlRemoteAddr` 1 行が定義）
- `google-trends related-queries`（Phase 1.5）、`trending-now` / `interest-by-region`（予約）
- Apify の allow-list / 入力スキーマ検証 / コスト上限 / ポーリング / リトライ（**作らない**と決めている。必要なら呼び出し側で）
- X の allow-list / field 名の検証 / ページングの自動化 / リトライ / レート制限の待ち / 費用上限（**作らない**と決めている）
- X の予約コマンド: `x user` / `x user-tweets` / `x tweets`（必要になったら 1 コマンド = 1 endpoint として追加）
- X の Request-only evidence（応答本文・投稿 ID・`next_token` 原値を含まない証跡の分離）は**未決**（設計書 §11 N7。必要になったら owner に相談）
- GA4 の dimension / metric の allow-list（**作らない**と決めている。未知の名前は GA4 のエラーがそのまま出る。語彙は `get-metadata` で確認する）
- GA4 の Admin API（設定変更）と書き込みは netloom では**作らない**（読み取り専用スコープの access token を既存の refresh grant で取るだけ。設計書 §2.2）
- **GA4 の live 成功応答の形**: metadata は 2026-10-19 に実測済み（`dimensions` 375 / `metrics` 86 / `name`。dimension は `apiName` / `uiName` / `description` / `category`、metric は それに `type`）。**report（`dimensionHeaders` / `metricHeaders` / `rows`）の実応答は未観測** — 実 property id での live は owner の 1 回で判明する（手順は `docs/plan/20261018-ga4-support.md` の追補節）
- **seo / JCT の `ga4-analytics` skill は `mcp_ga4_*` を直接使う手順のまま** — 「GA4 の取得は netloom 経由（証跡が残る）」への手順更新は**呼び出し側の作業**（設計書 §11 N11）
- **GA4 の 0.4.0 以前の MCP カセットは新しい実装では再生できない**（frame の形が違う。証跡としては有効なので削除しない）
- **seo の `fetch_gsc_monthly.py` は直接 API を叩く手順のままかもしれない** — netloom 経由（証跡が残る）への載せ替えは**呼び出し側の作業**（設計書 §11 N12）
- GSC の予約コマンド: `gsc site`（`GET /sites/{site}`）/ `gsc inspect`（URL Inspection API。別サービスなので transport と base URL の設計から）。必要になったら 1 コマンド = 1 endpoint として追加
- GSC の vcrpy（YAML）カセットの読み書きは**作らない**（このマシンに既存カセットは 1 つも無いと実測で確認。設計書 §11 N4）
- GSC の live 成功応答の形（`rows[].keys` の並び、`clicks`/`ctr`/`position` の型、`responseAggregationType` の有無）は、**このマシンの credential の状態による**（実装メモ §9）
- GSC の `service account` / ADC（Application Default Credentials）の grant は**作らない**（refresh_token grant のみ。設計書 付録 A.12）
- **news / cache の dev ホストは env `EC_DEV_BASE_URL` から読む**（**5 送信元共通**。値はコードに無い。未設定なら `--env dev` は exit 2。issue #7）
- **news / cache の live は 2026-10-18 に consumer（thch-vape スレッド）が `--env dev` で実施済み**（全コマンド exit 0・live と `--replay` はバイト一致・`--env prod` の書き込みは exit 2・カセットに実値なし。付録 A.15）
- **article の live も 2026-10-18 に実施済み**（CRUD + 画像（thumbnail / image、メタ付き）すべて exit 0・replay 一致。付録 A.16）
- **contact の live は 2026-10-18 に実施済み**（CRUD すべて exit 0・replay 一致。付録 A.17）。**ga4-orders の読み取りは 405**（shop 側にルートが無い。shop#313 待ち）、**`create` は実在する `dtb_order.id` 用**（合成 id は実態と食い違う `skipped` が返る。付録 A.18）
- **contact / ga4-orders のカセットはレダクトしない**（付録 A.17 / A.18 の設計相談への回答 = owner 決定 1。`--redact-pii` や `payload_sha256` は作らない）
- **ga4-orders の一覧 / 詳細 / 更新 / 削除のルートは shop 側にまだ無い**（live 実測 2026-10-18: `GET /api/ga4/orders` = **405 `Allow: POST`**。shop は受信の POST だけを実装。ルートが足されれば netloom のコマンドはそのまま動き、405 もカセットに残る）
- **ga4-orders の `X-GA4-API-Key` は shop 側で `.env` の `SEO_API_KEY` と比較する実装**（live は `GA4_API_KEY = SEO_API_KEY` の同値で 401 を通過。2026-10-18 実測）
- **slug → id の解決・slug での一覧フィルタは作らない**（呼び出し側が `list` の `offset` を進める。設計書 付録 A.16）
- **大きな本文の切り詰めは作らない**（カセットが M7 の証跡。切り詰めると replay の本文一致が失われる。付録 A.16）
- slug から id を引くような解釈・一覧のページングの自動化・画像の形式 / サイズの検査・派生バリアントの生成は**作らない**（呼び出し側が `list` / `get` を組み合わせる。派生はデプロイ時のバッチ）
- **OpenSEO は実装済み**（`openseo` 5 コマンド。上の節。1 コマンド = 1 往復。domain-overview / serp-competitors は issue #10 で 2026-10-19 に追加、live と replay のバイト一致を実測）。**呼び出し側（seo-operations の `fetch_openseo_monthly.py`）の載せ替えは未処理** — 証跡付きの取得への切替は seo-operations の作業（設計書 §11 N16）
- **OpenSEO の Docker の起動・停止は呼び出し側の作業**（netloom はプロセスを管理しない。設計書 付録 A.19）
- OpenSEO の `initialize` の往復は**送らない**（実測で不要。1 コマンド = 1 往復を崩さない）
- 実行時に `tools/list` は呼ばない（schema は開発時に 1 回だけ確認して設計 付録 A.7 に記録）
- **gmail は実装済み**（`gmail send-email` の 1 コマンド。上の節。1 コマンド = 1 MCP 往復）。**送信の live は未実行**（実メールが飛ぶため owner 承認待ち。手順は `docs/plan/20261019-gmail.md` §7）。**呼び出し側（seo-operations の `daily_alert.py` / `test_gmail_mcp.py`）の載せ替えは未処理** — 証跡付きの送信への切替は seo-operations の作業（設計書 §11 N17）
- gmail の他のツール（`draft_email` / `read_email` / `search_emails` / `list_email_labels` / ラベル / フィルタ / 添付の 18 ツール）は**予約（作らない）**（必要になった時点で 1 コマンド = 1 ツール。設計書 付録 A.20）
- gmail の `cc` / `bcc` / `htmlBody` / 添付は**送らない**（呼び出し側が名指した `to` / `subject` / `body` の 3 つだけ。付録 A.20）
- **Meta Graph API の live は未実行**（このマシンに `PAGE_TOKEN` / `USER_TOKEN` / `PAGE_ID` / `IG_ACCOUNT_ID` が無い。手順は `docs/plan/20261019-meta-graph.md` §7）
- **Graph API が `Authorization: Bearer` を受け付けるかは未確認**（live の 401 で判明する。クエリ方式（`access_token`）+ URL レダクトへの切替は owner 判断。設計書 §11 N18）
- **Meta のページング自動化・リトライ・metric / fields の allow-list は作らない**（薄いプロキシ。次のページは応答の `paging.next` で呼び出し側が回す）
- **Meta の csv は作らない**（`--fields` が列名になるため表を固定できない。json / text / verbatim だけ）
- **bigquery のカセットをコミット・共有する**（クエリ結果 = 業務データを含む。`.cassettes/`（gitignore）にだけ置く。付録 A.25）
- **BigQuery へ `--dry-run` なしで大きいクエリを実行する**（課金が発生する。まず `DRY_RUN=1` でスキャン量を確認する）
- **calendar の live 書き込みを owner 承認なしに実行する**（create / update / delete はカレンダーに予定を作り / 直し / 消す。副作用 = gmail の送信と同じ扱い。付録 A.26）
- **calendar のカセットをコミット・共有する**（予定の本文・参加者・カレンダー名 = 業務・個人データを含む。`.cassettes/`（gitignore）にだけ置く）
- **`GOOGLE_CALENDAR_ID` の実値をコマンドライン・メモ・カセットに書く**（netloom が環境変数から読む。credential ではないのでカセットの URL には載る）
- **calendar のイベント本文を netloom に検証させる**（`--input` は JSON であることだけを見る — フィールドの語彙検証は無い。不正な本文は provider のエラーが返る）
- **apps-script の live 書き込みと run-script を owner 承認なしに実行する**（create-project / update-project-content / create-version / create-deployment / update-deployment / delete-deployment は Projects に影響し、**run-script は任意の関数を実行する** — メール送信・シート書き込み等が起こりうる。gmail の送信と同じ扱い。付録 A.27）
- **apps-script のカセットをコミット・共有する**（ソースコード・デプロイメント・プロセス = 業務データを含む。`.cassettes/`（gitignore）にだけ置く）
- **apps-script の `--files` / `--parameters` を netloom に検証させる**（JSON であることだけを見る — 語彙検証は無い。不正な本文は provider のエラーが返る）
- **`update-project-content` を「部分更新」と思い込む**（**全ファイル置換** — 配列に含めたファイルだけが残る。呼び出し側が全ファイルを含める）
- **`PAGESPEED_API_KEY` / `CRUX_API_KEY` の実値をコマンドライン・メモ・カセットに書く**（netloom が環境変数から query の `key` として読む。実行例は env ファイル経由にする — シェル履歴と ps に残る）
- **psi / crux のカセットをコミット・共有する**（**URL に query キーが残る**（意図的 = replay 照合のため）+ 測定結果を含む。`.cassettes/`（gitignore）か呼び出し側の記録置き場にだけ置く）
- **PSI の live を owner 承認なしに実行する**（**キーの quota を消費する**。リトライを繰り返すと当日中に枯渇する（429））
- **netloom に PSI のキャッシュ回避を期待する**（netloom は URL をそのまま送る。新鮮な測定は呼び出し側が URL にダミーのクエリを付ける（例: `?psrun=N`））
- **psi / crux の値を netloom に判定・比較・正規化させる**（score は 0–1 のまま、histogram はそのまま。text 要約は「述べられたものを並べる」だけ。**ローカル Lighthouse との数値比較も呼び出し側の仕事**）
- **consumer の測定系（ローカル Lighthouse）を psi / crux で置き換える・Before/After に混ぜる**（psi / crux は**非公開 API** = 明示指示があるときだけ。issue #24 / 設計書 付録 A.29）
- **bigquery に書き込みを実行させようとする**（門が exit 2 で止める。書き込みは呼び出し側のツールに残る）
- **`auth google` の live の同意は未実行**（2026-10-19 時点。ブラウザ同意は owner が 1 回だけ実行する。手順は `docs/plan/20261019-google-auth.md` §9）。`.github/bin` の 3 本（`ga4_auth.py` / `google_calendar_auth.py` / `gas-mcp-server-auth.py`）の置き換えと、追跡下トークン JSON の追跡解除は**呼び出し側（thch-vape.shop）の作業**（設計書 §11 N19）
- **psi / crux の live は未実行**（2026-10-19 時点。**owner 承認が前提 — PSI は quota を消費する**。手順は `docs/plan/20261019-psi-crux.md` §5。実キーでの応答形（loadingExperience の有無、quota エラーの本文、CrUX のレート制限）はその 1 回で判明する）
- **呼び出し側（seo-operations）の置き換えはしない（決定）**（owner 決定 2026-10-18 = ローカル Lighthouse を正とし、psi / crux では置き換えない。PSI / CrUX は別測定系として `data/psi/cassettes/`・`data/crux/cassettes/` に証跡を残す運用を seo-operations が決める。issue #24 / 設計書 付録 A.29・§11 N29）
- **crux history の `--metrics` は無い**（issue のフラグ集合のまま。必要になったら 1 フラグ追加。設計書 §11 N29 予約）
- **psi / crux の csv は作らない**（応答が深い入れ子（Lighthouse result / histogram）で、列の選択が netloom の解釈になる。meta / calendar と同じ判断。json / text / verbatim のみ）
- **同意フローのトークン更新（refresh だけを行うモード）は作らない**（データコマンドが毎回交換するので不要。`auth google` は同意 1 回。設計書 付録 A.22）

# 正本（仕様を確認したいとき）

- 設計書 `docs/design/netloom-development-design.md`（CLI と出力形式は付録 A。Apify は §5.1 / §7 / 付録 A.9、X は §5.1 / §7 / 付録 A.10、GA4 は §5.1 / §7 / 付録 A.11、GSC は §5.1 / §7 / 付録 A.12、news / cache は §5.1 / §7 / 付録 A.15、article は付録 A.16、contact は §5.1 / §7 / 付録 A.17、ga4-orders は §5.1 / §7 / 付録 A.18、openseo は §5.1 / §7 / 付録 A.19、gmail は §5.1 / §7 / 付録 A.20）
- 実装メモ `docs/plan/20261017-mvp-implementation-notes.md`（実測した応答形と判断。GA4 は §8、GSC は §9）
- Apify の計画・レビュー・QA: `docs/plan/20261017-apify-support.md`
- X API v2 の計画・レビュー・QA: `docs/plan/20261018-x-api-support.md`
- GA4 の計画・レビュー・QA: `docs/plan/20261018-ga4-support.md`
- GSC の計画・レビュー・QA: `docs/plan/20261018-gsc-support.md`
- news / cache / article の計画・レビュー・QA（issue #2 / #5。live の手順は §7 / §8）: `docs/plan/20261019-news-api.md`
- contact / ga4-orders の計画・レビュー・QA（issue #3 / #4。live の手順は §7）: `docs/plan/20261019-contact-ga4-orders.md`
- openseo の計画・レビュー・QA（issue #1 第 2 弾 / #6。live の実測は §7 / §8。**issue #10 の 2 コマンドは追補節**）: `docs/plan/20261019-openseo.md`
- gmail の計画・レビュー・QA（issue #1 第 2 弾 / #6。live は読み取りのみ実測、送信の手順は §7）: `docs/plan/20261019-gmail.md`
- meta-page / meta-instagram（Meta Graph API）の計画・レビュー・QA（issue #1 第 2 弾。live の手順は §7 / 未確認は §9）: `docs/plan/20261019-meta-graph.md`
- Google OAuth 認証（`auth google`）の計画・レビュー・QA（issue #11。live の同意の手順は §9）: `docs/plan/20261019-google-auth.md`
- bigquery（BigQuery 読み取り専用クエリ）の計画・レビュー・QA（issue #19。**live は未実行** — owner 承認が前提。手順は §7）: `docs/plan/20261019-bigquery.md`
- calendar（Google Calendar）の計画・レビュー・QA（issue #20。**live は未実行** — owner 承認が前提。手順は §7）: `docs/plan/20261019-calendar.md`
- apps-script（Google Apps Script API 13 コマンド）の計画・レビュー・QA（issue #21。**live は未実行** — owner 承認が前提。手順は §7）: `docs/plan/20261019-apps-script.md`
- psi / crux（PageSpeed Insights API v5 と CrUX API）の計画・レビュー・QA（issue #23。**live は未実行** — owner 承認が前提（PSI は quota 消費）。手順は §5。**非公開 API 化（issue #24）の追補節を含む**）: `docs/plan/20261019-psi-crux.md`
