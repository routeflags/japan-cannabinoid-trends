# Issue: YouTube の化合物語が 5/13 語しか無い

**ID:** ISS-20261023-YT-010  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/processed/youtube_runs.csv`,
`youtube_videos.csv`, `methodology.md` §2.3  
**GitHub:** [#6](https://github.com/routeflags/japan-cannabinoid-trends/issues/6)

## 制約

YouTube raw ペイロードは gitignored（`.gitignore` の `**/data/raw/*`、例外は `google_trends` のみ）かつローカル限定であり、
本 worktree の `datasets/cannabinoid-raw-collection/data/raw/` には `youtube/` が存在しない。
以下は追跡対象の集計 2 表とコミット済み specs からの検証であり、raw 自体の確認は含まない。

## 検証済み事実

- `youtube_runs.csv`（8 行 = ヘッダ + 7 run、化合物語 5 + 製品語 2）:
  CBD 22 / THC 25 / CBG 34 / HHC 28 / THCV 23 / CBD オイル 23 / THC オイル 27。合計 182。
- `youtube_videos.csv` は 183 行（ヘッダ + **182 動画行**）で、run 別内訳は `youtube_runs.csv` の `video_rows` と一致する。
  確認コマンド: `PYTHONPATH=src python3 -c "import csv,collections; ..."`（`collections.Counter` で run 別集計）。
- 両表の生成器は `python -m processing.cli youtube-export`
  （`src/processing/youtube_export.py` の `build_video_export` + `write_export`。
  デフォルト `--study-dir datasets/cannabinoid-raw-collection` / `--output-dir .../data/processed`）。
  導出不能宣言は `src/processing/reproduce.py` の `NonReproducible`（raw がリポジトリ外のため clone では再導出不可。
  README も「生成は raw を要求するので、clone では再導出できない」と記載）。
- **未収集（8 語）**: THC-O, THCH, CBN, CRDH, CRDP, H4CBH, HHBD, HHCH。
  README §対象化合物の YouTube 列はこの 8 語を「raw のみ」と記すが、raw がローカル限定のため本 worktree では検証不能。
  追跡層（2 表）に 8 語の行は存在しない。
- `EXCLUSION_REASONS` は新規 run に影響しない。新規 run id は `PUBLISHABLE_RUNS` にも
  `EXCLUSION_REASONS` にも載らないため `_status()` は `"provenance not reviewed for publication"` を返し、
  `build_video_export` はその run を **withhold（2 表のどちらにも書かない）** する
 （`tests/processing/test_youtube_export.py::test_unreviewed_and_withheld_with_a_reason` がこの規則を固定）。
  新規 8 語を追跡層に載せるには `PUBLISHABLE_RUNS` への追加（コード変更 + テスト更新 + provenance レビュー）が必須。
  `EXCLUSION_REASONS` の 6 件（10-year 不完全系列 5 件 + methodology test 1 件）は既存の除外理由であり、新規収集とは無関係。

## 収集条件（既存と同じ）

Actor `gJvjeCYNraSfhIaNd`（`danek/youtube-search`）、1 run = 1 `search_term`、`max_videos` 50〜100。
入力スキーマは当該 2 フィールドのみ（`.github/skills/apify-youtube-search/SKILL.md`）:

> `"required": ["search_term", "max_videos"]`（Input Schema、Build `lcBfQ1sbz5bx58c1X` 時点）
> `| max_videos | ✅ | \`10\` (default 10, 1-100) | 取得上限。100超は要相談 (support@) |`
> `> \`max_videos\` は **件数** (ページ数ではない) で課金も件数比例。`

課金（同 SKILL）:

> `課金: **PAY_PER_EVENT** — \`Actor Start $0.00005\` + \`result $0.0005/件\` (FREE) → GOLD以上 \`$0.0002/件\``
> `計算例: \`max_videos=10\` で10件取得 → \`0.00005 + 10×0.0005 = $0.00505\` (FREE)`
> `| 予算超過防止 | \`max_videos\` を5-20に制限。100が上限, 1回で100件→ $0.05 (FREE) 程度。 |`

8 語分の上限コスト（FREE、start 込み）: `max_videos` 50 → 1 run $0.02505 × 8 = **約 $0.20**、
100 → 1 run $0.05005 × 8 = **約 $0.40**。GOLD 以上なら約 4 割（50 件 × 8 で約 $0.08）。
既存 run の `max_videos` は methodology §2.3 の表が正本（CBD / THC 100、他 50）。比較可能性のため方針は既存に合わせる。

## 収集経路: パイプラインではなく外部収集 + `make stage`

新規 8 語は `collect --live` では収集できない。外部 collector（netloom 経由の Apify 実行）で取得し、
`staging-declaration-v1` 文書 → `make stage` → `make adopt-all`（L1 ゲート判定）で採用する経路になる。根拠:

- `src/collection/adapters/__init__.py`: `_FACTORIES` と `_LIVE_SESSIONS` は `google-trends` のみ。
  `get_adapter_factory('youtube')` / `get_live_session('youtube')` はいずれも `AdapterUnavailable` を送出する（本 worktree で実測）。
- `src/collection/adapters/youtube/apify_csv.py`: YouTube adapter は handover 専用。
  `collect` は常に `LIVE_TRANSPORT_UNIMPLEMENTED` で fail-closed（`returned_count=0` を発明しない）。
  `stage_csv` / `build_csv_run` は既存の宣言ドライバ（`stage_declaration` → `adopt_staged`）への薄いラッパであり、
  新規 catalog / 採用 / 件数規則を追加しない。
- actor の不一致に注意: パイプライン側 handover（`build_csv_run` の `COLLECTOR_ID`）は
  `youtube-apify-scraper`（`h7sDV53CddomktSi5`、streamers/youtube-scraper）に固定されているが、
  既存 7 run の収集 actor は `youtube-apify-search`（`gJvjeCYNraSfhIaNd`、danek/youtube-search）である。
  `youtube-apify-search` 用の handover builder は存在しない（registry エントリ + SKILL のみ）。
  既存と同じ actor で 8 語を取る場合、宣言文書は手書き（スキーマ `staging-declaration-v1`、AGENTS.md: `unknown` 不可・
  未確認値は採用ブロック）となり、`date_filter` 等の request 事実は宣言者が明示する。
  パイプラインの request/response 語彙（`dateFilter` 等）は scraper 側のものであり、danek actor の入力語彙は
  `search_term` + `max_videos` のみ。混同しないこと。

## 選択肢と帰結

### 1. 8 語を追加収集する（新規収集のため owner 承認が必要: 実費 + 新スナップショットの採用判断）

手順: ① 同一 actor（`gJvjeCYNraSfhIaNd`）で 8 語 × 1 run を外部実行（`max_videos` は既存方針に合わせる）
→ ② 1 語 1 文書の `staging-declaration-v1` で `make stage` / `make adopt-all`（request と観測範囲を分離記録）
→ ③ `PUBLISHABLE_RUNS` に 8 run を追加（provenance レビュー後、テスト更新つき）
→ ④ `youtube-export` で 2 表を再生成。
帰結: `youtube_runs.csv` は 15 行、`youtube_videos.csv` は 182+N 行になる。
新規 run は 2026-10-02 スナップショットと別時点の観測であり、run 間で窓が違えば別観測として扱う
（AGENTS.md: 同一クエリの再実行は非決定的になりうる）。README のキーワード表と methodology §2.3 は別途更新が必要
（本 issue 記録者の編集権限外のため、文案は下記「文書更新の文案」を owner / 編集者に渡す）。

### 2. YouTube は 5 語を意図的な範囲として methodology に明記する（収集なし）

手順: methodology §2.3 に範囲限定の旨と理由を追記し、README の YouTube 列の「raw のみ」表示と整合させる
（raw が実在するなら local 証跡として残し、追跡層には載せない。raw が無い語は「未収集」と読み替える）。
帰結: コード変更なし・コストなし。ただし Google Trends 13 語 / X 7 語との被覆差は恒久的な制約として残り、
化合物間比較での YouTube エビデンスは 5 語に限定される。

## 文書更新の文案（README / methodology は編集権限外のため提案のみ）

- 選択肢 1 が実施された場合、README「収集したキーワード」YouTube 行を
  `| YouTube | 2026-10-02（公開集計に入る 7 run）+ 2026-10-2x（8 run 追加） | 13 語すべて | オイル 2 語 | ... |`
  の形に更新し、methodology §2.3 の表に 8 語（`max_videos` 実績値つき）を追加する。
- 選択肢 2 の場合、methodology §2.3 に `YouTube の収集範囲は化合物語 5 語 + オイル 2 語に限定する（ISS-20261023-YT-010、owner 判断 YYYY-MM-DD）。
  残り 8 語の YouTube エビデンスは存在しない。` を追記し、README の「raw のみ」8 語の扱い（local 証跡の有無）を確定させる。

## 完了条件

- [ ] 方針の決定（owner: 選択肢 1 か 2 か。選択肢 1 なら `max_videos` 方針と費用承認を含む）
- [ ] 実施: 選択肢 1 なら 8 run の外部収集 + stage/adopt（L1 通過）+ `PUBLISHABLE_RUNS` 追加 + `youtube-export` 再生成。
  選択肢 2 なら methodology への範囲明記
- [ ] README のキーワード表・methodology §2.3・`youtube_runs.csv` の三者が一致している
