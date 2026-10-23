# Datasets

`datasets/` の読み方。**1 研究 = 1 ディレクトリ**で、各研究は他の研究を読まなくても理解できるように書く（`AGENTS.md` Dataset Structure）。

全体の規約は [`AGENTS.md`](../AGENTS.md)、収集パイプラインは [`docs/specs/collection-pipeline.md`](../docs/specs/collection-pipeline.md)、公開契約は [`docs/specs/contracts.md`](../docs/specs/contracts.md) が正本。この README は**索引と注意点**だけを持ち、規則を再定義しない。

## 共通レイアウト

```text
datasets/<study-id>/
├── README.md          何を測る研究か（必須）
├── methodology.md     どう測ったか（推奨。無い研究は下記「既知の欠落」）
├── data/
│   ├── raw/<source>/<run-id>/   不変。収集の生記録
│   ├── interim/                 中間生成物（現在はほぼ未使用）
│   └── processed/               再生成できる分析用データ（追跡対象）
├── metadata/          カタログ・schema・収集計画
└── analysis/          研究メモ（研究によっては未作成）
```

実態にはばらつきがある。`data/processed/` の代わりに `schema/` と `queries/` を持つ研究（`x-consistency` / `youtube-consistency`）、`analysis/` を持つ研究（`cbx-search-trends` / `cbx-social-trends` / `x-26week-trends`）がある。

## レイヤと追跡方針

| レイヤ | 場所 | Git | 不変性 |
|---|---|---|---|
| RAW | `data/raw/<source>/<run-id>/` | **原則 管理外**（例外は `google_trends`） | **不変**。書き換えず、修正は下流で行う |
| INTERIM | `data/interim/` | 管理（現状は `.gitkeep` が主） | 作り直せる中間物 |
| PROCESSED | `data/processed/` | 管理 | コミット済み入力から再生成できること（`audit-processed` が検査） |
| ANALYSIS | `analysis/` | 管理 | 解釈。観測事実として扱わない |

追跡方針は [`.gitignore`](../.gitignore) の次の規則で決まる（公開対象の根拠は [`docs/specs/raw-data-policy.md`](../docs/specs/raw-data-policy.md)）。

```text
**/data/raw/*                    # raw は既定で管理外
!**/data/raw/.gitkeep           # 空ディレクトリだけは管理
!**/data/raw/google_trends/     # 例外: Google Trends の raw は公開可
!**/data/raw/google_trends/**   #        （raw-data-policy.md §4.1 の表）
```

**帰結（重要）**: raw は多くが Git 管理外なので、**clone しただけでは raw が存在しない**。研究側の `.gitignore` が `data/` 以下を全除外する研究もある（`x-consistency` / `youtube-consistency`）。raw が手元にしか無い状態は正常だが、「どの run を採取したか」は `run_metadata.json` と宣言・監査で追う（[`docs/audits/g7-study-inventory.json`](../docs/audits/g7-study-inventory.json) が研究ごとの棚卸し）。

## 研究一覧

raw 列は**そのマシンのローカル checkout に存在する source**（Git 管理外を含む）。run 数や件数は変動するのでここには書かない — 正本は `docs/audits/g7-study-inventory.json`。

| study | 何を扱うか | ローカル raw source | 追跡されている成果物 | release |
|---|---|---|---|---|
| [`cannabinoid-platform-trends`](cannabinoid-platform-trends/README.md) | 化合物 × プラットフォームの集計（Google Trends 5年 + YouTube 採用分。X は owner 判断で除外） | 無し（コミット済み証拠から生成） | `data/processed/` 5 ファイル、`metadata/schema/` 4 | ✓ |
| [`cannabinoid-multi-trends`](cannabinoid-multi-trends/README.md) | 主要 7 化合物（+拡張）の Google Trends 5年/12ヶ月、X、YouTube | `google_trends`（追跡）, `x`, `youtube` | `data/raw/google_trends/`、`data/interim/` 1、`data/processed/collection-summary.md`、`metadata/`（data-catalog + 収集計画 9） | ✓ |
| [`cbx-search-trends`](cbx-search-trends/README.md) | CBX / H4CBH / HHBD の検索需要（Google Trends + Search Console） | `google_trends`（追跡）, `gsc` | `data/raw/google_trends/`、`analysis/` 2 | ✓ |
| [`cbx-social-trends`](cbx-social-trends/README.md) | CBX の SNS 言及（X / YouTube / Instagram / TikTok） | `x`, `youtube`, `instagram`, `tiktok` | `analysis/` 8、`data/processed/` 4（YouTube 24 件フィルタ、X 月次粗集計） | ✓ |
| [`cannabinoid-social-trends`](cannabinoid-social-trends/README.md) | 規制前後の X 言及 | `x` | `README.md` / `methodology.md` のみ | — |
| [`cbx-liquid-online-trend`](cbx-liquid-online-trend/README.md) | CBX リキッドの X 投稿 | `x` | 空の `data/processed/`・`data/interim/`・`metadata/runs/` | — |
| [`x-26week-trends`](x-26week-trends/README.md) | CBX リキッド X 26 週トレンド | （空） | `analysis/` 2、`data/{raw,interim}/` は `.gitkeep` | — |
| [`x-consistency`](x-consistency/README.md) | X 収集の一貫性・日付範囲取得 | 無し | `schema/schema.sql` | — |
| [`youtube-consistency`](youtube-consistency/README.md) | YouTube 検索結果の一貫性・重複、COL-033 採用系列の受け皿 | 無し | `schema/schema.sql`、`queries/` 3 | — |
| [`cbx-product-coa`](cbx-product-coa/README.md) | 市流通 CBX 製品の規格分析（COA） | `coa` | `README.md` のみ | — |

`release` 列は `metadata/datapackage.json` の `resources` に載っているか（= 配布データパッケージの対象か）。載っていない研究は調査・支援用で、公開物の根拠には使えるが配布物ではない。

## どこから読むか

1. **横断の集計**（化合物 × プラットフォーム）→ `cannabinoid-platform-trends/data/processed/` とその [methodology.md](cannabinoid-platform-trends/methodology.md)
2. **Google Trends の 5年サマリー**の正本 → `docs/audits/gt-summary.json`（生成: `gt-summary`）
3. **公開ページ**の数値 → [`publication/README.md`](../publication/README.md) と各 `research_*.html`（run_id が書かれている）
4. 個別研究の詳細 → その研究の `README.md` → `methodology.md` → `metadata/`（schema・計画）→ `data/processed/`

## 再生成と検査

`make` は `.venv` を要求する（`check-venv`）。直接叩く場合は `.venv/bin/python -m ...`。

```bash
make platform-trends     # 横断集計（datasets/cannabinoid-platform-trends/data/processed/）を再生成
make audit-snapshots     # 監査スナップショット一式（gt-summary / study inventory / 各 inventory）
make audit-publication   # 公開契約 PC-1〜PC-8 の判定を記録
make audit-new-runs      # 未 catalog の raw run の検出
make gates               # 境界・契約のゲート

# 個別の検査（processed がコミット済み入力から再導出できるか）
.venv/bin/python -m processing.cli audit-processed --datasets-root datasets
```

## 既知の欠落と注意

- **`methodology.md` が無い研究**: `cbx-product-coa`、`x-consistency`、`youtube-consistency`。COA は `README.md` のみで `data/` も未作成。
- **`data/interim/` はほぼ未使用**（実際の中間ファイルは `cannabinoid-multi-trends/data/interim/` の 1 件だけ）。
- **`youtube-consistency` の raw が無い**: README は YouTube データの main store と書くが、追跡層にもローカルにも COL-033 採用 6 run の payload は無く、`data/trends.db`（`*.db` で管理外）に集計が残るのみ。payload の同一性は宣言 [`metadata/provenance/declarations/20261015-youtube-csv-adoption.json`](../metadata/provenance/declarations/20261015-youtube-csv-adoption.json) の sha256 で担保している。
- **再現できない processed**: `cbx-social-trends/data/processed/youtube_filtered_202607/` は `not_reproducible_from_repository`（フィルタ規則は記録、実行するコードが無い）。`cannabinoid-multi-trends/data/processed/collection-summary.md` も手書き。
- **欠測は 0 ではない**: 収集していない化合物 × プラットフォームは `not_collected` として記録する（`observed_zero` と混同しない）。
- **`data/private/` は非公開**: `datasets/*/data/private/` は `.gitignore` で除外（現在は `cbx-social-trends/data/private/x_anonymization_mapping.json` の 1 件）。内容は検査・公開しない。
- **GSC の raw は追跡されない**: `raw-data-policy.md` §4.1 の表は `data/raw/gsc/` を公開扱いと書くが、`.gitignore` の例外は `google_trends` のみ。`cbx-search-trends/data/raw/gsc/202607_queries.csv` はローカルのみ。
- **worktree の盲点**: Git 管理外の raw は作業用 worktree に複製されないため、worktree 内で生成した監査は存在するファイルを `exists:false` と記録することがある。raw を見る監査は raw がある checkout で実行する。

## 研究を追加するとき

1. `datasets/<study-id>/README.md`（問い・範囲・出所）と `methodology.md`（手順・制約・limitations）
2. raw は `data/raw/<source>/<run-id>/` に `run_metadata.json` と payload を置く。手元の payload は推測で置かず [`staging-declaration-v1`](../docs/specs/collection-pipeline.md) を書いて `make stage DECLARATION=<file>` → `make adopt-all`
3. `data/processed/` は**コードで**生成し、`audit-processed` が `reproducible` と言う状態にする
4. `make audit-snapshots` で監査を更新する（`g7-study-inventory.json` に新研究が載る）
5. 配布対象にするなら `metadata/datapackage.json` の `resources` に追加する（release 判断は owner）

## 公開との関係

研究が終わっても配布・公開は別判断。`release` 列に ✓ がある研究でも、公開は公開ゲート（[`AGENTS.md`](../AGENTS.md) の Publication Gate、`make audit-publication`、`make gates`）を通し、privacy と再配布条件のレビューを経る。バージョンと DOI の正本は [`metadata/datapackage.json`](../metadata/datapackage.json) と [`CITATION.cff`](../CITATION.cff)。
