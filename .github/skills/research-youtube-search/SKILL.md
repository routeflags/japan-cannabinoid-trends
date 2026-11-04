---
name: research-youtube-search
description: |
  研究用の YouTube 検索スキル。
  研究が宣言したクエリ設計に従って YouTube 動画を収集し、staging 宣言へ渡す。
---

# Research YouTube 検索スキル

研究用の YouTube データ収集スキル。**任意のキーワード・研究ID** で再利用できるよう抽象化されている。
各研究は `datasets/<study-id>/` 配下にデータを保存し、このスキルは収集・重複排除の確認・staging 宣言への受け渡しを担当する。
研究計画書（`docs/plans/` 配下）と study のクエリ設計に定められた値をそのまま入力として使う。

## このスキルの位置づけ

- **1 実行 = 1 クエリ**。複数クエリを 1 run にまとめない。
- **クエリ設計は study が宣言する**。このスキルは「化合物研究なら必ず 2 語」のような普遍規則を持たない。
- 現在の collector は Apify Actor `h7sDV53CddomktSi5`（`streamers/youtube-scraper`）。
- 取得した payload は **byte 単位でローカルに保存**し、`staging-declaration-v1` → `make stage` → `make adopt-all` で採用する。
- raw は不変。重複排除は下流の再現可能な処理で行う。
- raw を Repository Storage（Git 追跡）として保持するかは、収集前に `git_tracked` / `git_untracked` で分類する（後述）。
- 課金は発生するため owner 承認を前提とする。**金額は追跡成果物に記録しない**（AGENTS.md Scope Exclusion）。

---

## トリガー

- 「YouTube の研究用データ取って」
- 「<キーワード> の YouTube 動画収集」
- 「<study-id> の YouTube 収集」
- 「YouTube で <キーワード> 調べて」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | — | 検索語。query registry の `canonical_text` をそのまま使う |
| `query_id` | string | ✅ | — | `metadata/queries/query-registry.json` の ID。宣言に記録する |
| `study_id` | string | ✅ | — | 研究ID。保存先 `datasets/<study_id>/data/raw/youtube/` を決める |
| `max_results` | integer | — | Actor の既定 | Actor input の `maxResults`。取得上限 |
| `date_filter` | string | — | なし | `hour` / `today` / `week` / `month` / `year`。**絶対日付は不可** |
| `output_dir` | string | — | `datasets/<study_id>/data/raw/youtube/` | 保存先 |

> `max_videos` は旧 Actor `gJvjeCYNraSfhIaNd` の入力名であり、現行 Actor には存在しない。
> 新規ワークフローでは使わない。旧宣言に残る `max_videos` は**歴史的記録**としてのみ読む。

---

## クエリ設計は study が宣言する

クエリの種類と数は study の設計事実であり、このスキルに固定しない。
研究ごとに `datasets/<study>/metadata/query-design.json`（または計画書）で次を宣言する。

- どの `intent_id` を primary とするか
- 1 run 1 クエリか
- primary 外の語をどう扱うか（残す / 収集しない）
- どの配布物に含めるか

### この collection の宣言（`cannabinoid-raw-collection`）

宣言ファイル: `datasets/cannabinoid-raw-collection/metadata/query-design.json`
design: `youtube-liquid-only-primary`

| 区分 | 語 | `intent_id` | 扱い |
|---|---|---|---|
| **primary** | `<compound> リキッド` | `product_liquid` | 1 化合物 1 クエリ（1 run）。一次被覆に数える |
| **primary 外** | `HHC` などの裸の化合物語 | `compound_general` | 収集しても **残す証跡**。一次被覆に数えない。必須の対でもない |

理由:

1. この collection の観測は国単位のプラットフォーム件数ではない。
2. Actor 入力に **geo filter はない**（`searchQueries` / `maxResults` / `maxResultsShorts` / `maxResultStreams` / `dateFilter` / `sortingOrder` のみ）。
3. 日本語の製品語「リキッド」が、**検索語ベースで日本市場向け製品コンテンツを近似的に絞り込む**。
4. これは geo 保証ではない。日本語コンテンツでも海外市場向けは混ざり、日本語以外の国内向けコンテンツは拾えない。
5. 裸の化合物語は日本語製品コンテンツに限定されず、同じ観測単位にならない。したがって primary 外。

**重要:**

- 裸の化合物語 run は削除しない（raw は不変）。ただし primary coverage の件数・化合物数に加えない。
- 「HHC と HHC リキッドを必ず対で取る」という規則は**この study にはない**。HHC の裸語 run は残された out-of-scope 証跡であり、liquid coverage を完成させない。
- 別の study は別の設計を宣言できる。この liquid-only 規則を他のキーワード収集へコピーしない。

---

## 保持（Repository Storage / Git 追跡）の分類

収集・staging の前に、raw payload を Repository Storage として保持するかを分類する。
語彙は `docs/specs/raw-data-policy.md` §5 の 2 状態だけを使う。

| `retention_status` | 意味 | このスキルでの扱い |
|---|---|---|
| `git_tracked` | payload を Git 追跡下の Repository Storage として保持する | run ディレクトリを commit し、clone で再現できる状態にする。明示判断がある場合のみ |
| `git_untracked` | payload を Repository Storage として保持しない | payload を Git に追加しない。`datasets/<study>/data/raw/youtube/<run-id>/` のローカル raw は存在してよい（gitignore 済み） |

- **既定:** `config/storage-policies.json` の `raw-social-default`（`source_kind: social` →
  `git_tracking: ignored`）により `git_untracked`。
- **明示判断:** owner / legal / publication review が状態を決める場合のみ
  `metadata/provenance/retention/<date>-<slug>.json`（`record: "raw_retention_decision"`）
  を追加する。`reason` / `decision_reference` / `decided_by` / `decided_at` と、
  保持とは独立した `publication_status` を記録する。法的結論を推測しない。
- **ローカル raw の存在は保持ではない。** `git add -f` をしない。`git ls-files` に
  payload が出ないことを確認する。
- **保持は公開許可ではない。** 行単位の動画データは `git_tracked` でも
  `git_untracked` でも公開しない。集計・派生は別の公開審査による。
- 既存の YouTube run は判断記録が無い限り policy 既定の `git_untracked`。推測で
  判断記録を追加しない。

---

## 現在の Actor 入力

Actor: `h7sDV53CddomktSi5`（`streamers/youtube-scraper`）

| 入力キー | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `searchQueries` | array | ✅ | **1 要素だけ**入れる（1 run 1 クエリ） |
| `maxResults` | integer | — | 取得上限。件数でありページ数ではない |
| `maxResultsShorts` | integer | — | Shorts 上限。`0` で除外 |
| `maxResultStreams` | integer | — | ストリーム上限。`0` で除外 |
| `dateFilter` | string | — | **相対期間のみ**（`hour` / `today` / `week` / `month` / `year`） |
| `sortingOrder` | string | — | `relevance` / `rating` / `date` / `views` |

`dateFilter` を**指定しない**場合、Actor 入力には絶対日付窓もローリング窓も存在しない。
宣言では `date_filter: "all"` を「日付フィルタなし」の宣言語彙として使い、`limitations` に
「Actor の enum 値ではなく、入力に `dateFilter` を渡していないことを表す」と書く。
Actor に `all` という値はないため、`dateFilter: "all"` を送ってはいけない。

---

## request と観測窓は別物

| 事実 | 何を表すか | どこに記録するか |
|---|---|---|
| **request** | Actor に渡した入力（`searchQueries` / `maxResults` / `maxResultsShorts` / `maxResultStreams` / `dateFilter` の有無）と `reference_time` | 宣言の `collection_request` と `run_metadata.json` の `submitted_parameters` |
| **observed window** | payload に含まれた動画の公開日を正規化した半開区間 | 宣言の `window` と `temporal` |

観測窓の正規化（UTC、`[start, end_exclusive)`）:

- `start` = 返された動画の `date` の最小日の `00:00:00Z`
- `end_exclusive` = 返された動画の `date` の最大日 + 1 日の `00:00:00Z`
- これは**返された項目の観測範囲**であり、検索条件でも、全動画が存在した証明でもない。
- 同じ検索語でも run が違えば窓は別。run をまたいで件数を合算しない。

---

## 実行

```bash
# 前提: .env.d/apify.env に APIFY_TOKEN がある（値はコミットしない）
# 1 run = 1 query
KEYWORD="<query registry の canonical_text>"
QUERY_ID="<query_id>"
STUDY_ID="<study_id>"
MAX_RESULTS="${MAX_RESULTS:-10}"   # Actor の既定は 10。研究で決めた上限に置き換える
DATE_FILTER="${DATE_FILTER:-}"    # 空 = dateFilter を送らない（unbounded）

INPUT=$(jq -n \
  --arg q "$KEYWORD" \
  --argjson max "$MAX_RESULTS" \
  --arg filter "$DATE_FILTER" \
  '{
    searchQueries: [$q],
    maxResults: $max,
    maxResultsShorts: 0,
    maxResultStreams: 0
  }
  + (if $filter == "" then {} else {dateFilter: $filter} end)')

R=$(netloom apify run --actor h7sDV53CddomktSi5 --wait 90 --input "$INPUT")
DS=$(echo "$R" | jq -r '.data.defaultDatasetId // .defaultDatasetId')
ACTOR_RUN=$(echo "$R" | jq -r '.data.id // .id')

# 実行状態を控える（status / startedAt / finishedAt / build。無い値は作らない）
netloom apify run-status --run-id "$ACTOR_RUN" > /tmp/youtube-run-status.json

# dataset を flat CSV（id / title / date / ...）で保存する
mkdir -p "datasets/${STUDY_ID}/data/raw/youtube/<run-id>"
netloom apify dataset --dataset-id "$DS" --as csv \
  --out "datasets/${STUDY_ID}/data/raw/youtube/<run-id>/<export>.csv"
```

- `<run-id>` は `YYYYMMDDTHHMMSSZ-youtube-<study-id>` 形式（AGENTS.md Run Identity）。
- CSV は**そのまま**保存する。列を書き換えない。`id` と `title` は必ず含まれる。
- `run_metadata.json` / `artifact-manifest.json` は手書きしない。`make stage` / `make adopt-all` が
  `collection-run-v1` / `artifact-manifest-v1` として生成する。
- `run-status` に build が無い場合は `null` と「未記録」を宣言に書く。推測しない。

---

## 重複排除（raw は変更しない）

YouTube 検索はページングで同じ動画を返すことがある。**raw は変更せず**、件数だけを確認する。

```bash
python3 - "$CSV" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8", newline="")))
ids = [row["id"] for row in rows if row.get("id")]
unique = set(ids)
print("raw_count:", len(rows))
print("deduplicated_count:", len(unique))
print("duplicates_removed:", len(ids) - len(unique))
print("input_values:", sorted({row.get("input", "") for row in rows}))
print("types:", sorted({row.get("type", "") for row in rows}))
PY
```

- キーは **`id`**。`videoId` ではない（現行 CSV の列名）。
- run 内だけで重複排除する。run をまたいで畳まない。
- 排除前・排除後・除去件数は宣言の `environment` に記録する（raw_count / deduplicated_count / duplicates_removed）。
- 分析用の dedup は下流の再現可能な処理で行う。raw を上書きしない。

---

## 保存先と staging レイアウト

```
datasets/<study-id>/data/raw/youtube/<run-id>/
├── <export>.csv              ← Actor の flat CSV（byte 単位でローカル保存）
├── run_metadata.json         ← collection-run-v1（stage / adopt が生成）
└── artifact-manifest.json    ← artifact-manifest-v1（stage / adopt が生成）
```

- 既定は `git_untracked`。この 3 ファイルは gitignore され、ローカルに留まる。
  リポジトリに残すのは、staging 宣言・catalog・集計・保持判断記録。
- `git_tracked` の場合だけ、`.gitignore` の例外と追跡を明示判断に従って行う。
- raw は Git 管理外（`.gitignore` の `**/data/raw/*`、例外は `google_trends` のみ）。
- 採用宣言は `metadata/provenance/declarations/<date>-youtube-<slug>.json`（`staging-declaration-v1`）。
- 宣言には `query` / `window` / `collection_request` / `temporal` / `timestamps` / `execution` /
  `artifacts` / `environment` を書く。`environment` には `actor_run_id` / `apify_dataset_id` /
  `actor_build`（判明した場合）/ `payload_sha256` を記録する。
- 宣言には金額項目を書かない。
- 実行:

```bash
make stage DECLARATION=metadata/provenance/declarations/<file>.json
make adopt-all
```

---

## データ品質チェック

収集後、**読み取り専用**で確認する。

```bash
CSV="<保存先>/<export>.csv"

# 1. CSV record 数（行数ではなく csv の record 数）
python3 -c "
import csv,sys
rows=list(csv.DictReader(open('$CSV', encoding='utf-8', newline='')))
print(len(rows))
"

# 2. id のユニーク数と重複
python3 -c "
import csv,collections
rows=list(csv.DictReader(open('$CSV', encoding='utf-8', newline='')))
c=collections.Counter(r['id'] for r in rows)
print('unique', len(c), 'duplicates', sum(v-1 for v in c.values() if v>1))
"

# 3. 検索語と type の確認（1 query / Shorts・stream 除外の確認）
python3 -c "
import csv,collections
rows=list(csv.DictReader(open('$CSV', encoding='utf-8', newline='')))
print(collections.Counter(r.get('input','') for r in rows))
print(collections.Counter(r.get('type','') for r in rows))
"

# 4. 観測窓（UTC、半開区間）
python3 -c "
import csv,datetime
rows=list(csv.DictReader(open('$CSV', encoding='utf-8', newline='')))
d=sorted(r['date'] for r in rows if r.get('date'))
print('first', d[0], 'last', d[-1])
"
```

確認すること:

- `input` が宣言した 1 クエリだけである。
- `type` が `video` のみ（`maxResultsShorts` / `maxResultStreams` が 0 の場合）。
- `id` の重複数が宣言の `duplicates_removed` と一致する。
- 観測窓が宣言の `window.start` / `window.end_exclusive` と一致する。
- 件数が宣言の `execution.returned_count` / `record_count` と一致する。

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| 検索結果は標本であり census ではない | 件数を YouTube 全体の投稿数として書かない |
| ページング重複 | `id` で run 内 dedup。raw は変更しない |
| 検索結果の非決定性 | 同じ語でも run を分け、run_id で区別する。件数を合算しない |
| `dateFilter` は相対のみ | 絶対日付窓を Actor 入力に書かない。観測窓と request を分離する |
| geo filter がない | 日本語「リキッド」による近似的な市場限定。geo 保証ではないと書く |
| 取得上限 | `maxResults`（件数）。`max_videos` を新規入力に使わない |
| 課金 | owner 承認。金額は追記しない |
| raw の不変性 | 編集・削除・列変更をしない。修正は下流で行う |
| 保持とローカル存在の混同 | `git_tracked` / `git_untracked` で表す。ローカル raw の有無を「保持」と呼ばない |
| 保持を公開許可と誤認 | 保持は Repository Storage の状態。公開は別の公開審査・gate による |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 0 件 | クエリがニッチ / フィルタが強すぎる | クエリ設計を見直す。0 は `observed_zero` であって収集不要ではない |
| 重複が多い | YouTube 検索のページング | `id` で run 内 dedup を確認。raw は変更しない |
| `dateFilter` エラー | 絶対日付を渡した | 相対値のみ使う。絶対窓は観測として記録する |
| `maxResults` が効かない | 旧 `max_videos` を送っている | 現行キー `maxResults` に直す |
| 401 Unauthorized | `APIFY_TOKEN` 無効 | `.env.d/apify.env` を確認（値は表示・コミットしない） |

---

## 収集実績の記録

実行のたびに、次を記録する（金額は記録しない）:

- `datasets/<study-id>/data/raw/youtube/<run-id>/run_metadata.json` … 実行単位（pipeline が生成。`git_untracked` ではローカルのみ）
- `datasets/<study-id>/data/raw/youtube/<run-id>/artifact-manifest.json` … payload の SHA-256 / 件数（`git_untracked` ではローカルのみ）
- `metadata/provenance/declarations/<date>-youtube-<slug>.json` … 宣言（query / request / window / 実行状態。追跡対象）
- `metadata/provenance/retention/<date>-<slug>.json` … 明示判断がある場合のみ（`git_tracked` / `git_untracked`、理由、判断参照、公開状態。追跡対象）
- 研究全体の履歴は study の methodology / issue に残す。

スキル内に特定研究の実績値を固定で書き込まない（別キーワード・別期間での再利用を妨げないため）。

---

## 関連

- **研究計画書:** `docs/plans/` 配下（研究ごとに作成）
- **raw 保持方針:** `docs/specs/raw-data-policy.md` §5（`git_tracked` / `git_untracked`）
- **クエリ設計:** `datasets/<study>/metadata/query-design.json`（study が宣言）
- **methodology:** `datasets/<study>/methodology.md`
- **Actor 仕様:** `apify-youtube-scraper` スキル（入力スキーマ・日付フィルタの実測）
- **上位スキル:** `apify-youtube-search`（旧 Actor。新規収集では使わない）
- **管理スキル:** `apify-mcp`（MCP 起動・認証）
