# Issue: CRDH の 12ヶ月系列が summary-only（`avg_12m` 1.9 が raw から検算できない）

**ID:** ISS-20261023-GT-007  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261008T102022Z-google-trends-crdh/`,
`datasets/cannabinoid-raw-collection/methodology.md` §2.1.3  
**GitHub:** [#3](https://github.com/routeflags/japan-cannabinoid-trends/issues/3)

## 概要

CRDH の 12ヶ月単独系列は週次 raw を持たない唯一の欠落（THC-O はソースが系列を返さない `NO_DATA` で別扱い）。
5年側は `20261014T215738Z-google-trends-cannabinoid-multi-trends` に 262 週の系列があるため、**12ヶ月のみの欠落**。
公開ページの 12ヶ月ブロックは共通スケール比較（raw あり）を根拠にしており、ページの数値自体に誤りはない。
`avg_12m` 1.9・ピーク週・非ゼロ週数 2 は引用してはならない（出所不明の数値になる）。

## 事実（実測）

- `20261008T102022Z-google-trends-crdh/` の収蔵は `records_crdh_12m.json` 1 ファイルのみで、`run_metadata.json` は無い。
  同 JSON は `data` 配列を持たず、以下の**記録値**だけからなる（`collected_at` は `"2026-10-06"` で run ディレクトリ名の日付 `20261008` と不一致。来歴の欠落）:
  `compound="CRDH"` / `geo="JP"` / `timeframe="today 12-m"` / `data_points=53` /
  `first_value=0` / `last_value=0` / `peak_value=100` /
  `peak_date="2025-11-09 to 2025-11-15"` / `avg_12m=1.9` / `nonzero_weeks=2`。
- リポジトリ全体の走査（`datasets/*/data/raw/google_trends/` 下の `records_*.json` / `comparison_*.json` /
  `payload.json` 全件。`keyword` または `compound` が `CRDH` かつ `timeframe="today 12-m"` で `data` 配列を持つ
  ファイルを探索）では該当なし。12ヶ月の CRDH 言及は `records_crdh_12m.json`（系列なし）、`CRDH リキッド`系
  （別クエリ。`records_crdh-rikiddo.json` は `data: []`、`comparison_ja4.json` の `CRDH リキッド`平均は 0.0）、
  および 12ヶ月共通スケール `comparison.json`
  （`average_interest: {CRDH: 0, CBD: 47, THC: 12}`、系列なし）のみ。CRDH に言及する `payload.json` 2 件は
  いずれも `today 5-y`（単独系列 / 5年共通スケール比較）。すなわち **CRDH の 12ヶ月週次系列は
  リポジトリ内のどこにも存在しない**。
- `processing.gt_statistics` はこのレコードを `partial` に分類する（`baseline` ではない。`baseline` 形状は
  `avg_5y` を持つ run 用で、`avg_12m` というキーは素通し対象外）。`summarize_record` の結果は `stats.mean=None` /
  `peak_date=None` / `peak_value=None` / `weeks=None` / `nonzero_weeks=None` で、
  `unavailable.mean="run が平均値を記録していない（系列も未保存）"`。すなわち **`avg_12m` 1.9 は処理系にも
  検算・継承されず**、`gt-summary --timeframe 12m --compound CRDH` のブロックは平均・ピーク・最新値すべて
  `算出不能（run に記録なし）` になる
  （`PYTHONPATH=src python3 -m processing.cli gt-summary --datasets-root datasets --timeframe 12m --compound CRDH` で確認）。
- **公開ページはこの値を使っていない**: `publication/research_crdh.html` の「12ヶ月データサマリー（共通スケール）」表
  （CRDH 0 / CBD 47 / THC 12）は `20261008T125719Z-google-trends-common-scale-crdh/comparison.json` の
  `average_interest` と一致し、当該 run は `timeframe="today 12-m"`・`collected_at="2026-10-08"`。
  ページの数値自体は問題ない（同 run も `comparison.json` のみで `run_metadata.json` を持たない legacy 形状だが、
  引用値はファイル内の記録値と一致している）。
- 5年側の系列（`20261014T215738Z-.../records_crdh.json`、`timeframe="today 5-y"`、262 週、`run_metadata.json` の
  `query_id="crdh-general-ja"`）は本件の対象外で、正常。

## 何が問題か

原稿や下流が `avg_12m = 1.9`・ピーク週（2025-11-09 週）・非ゼロ週数 2 を引用すると出所不明の数値になる
（`ISS-20261015-GT-003` と同型）。12ヶ月の他 3 化合物（THCV・H4CBH・HHBD）は 2026-10-23 に系列を取得済みで、
CRDH だけが取り残されている。`methodology.md` §2.1.3 の CRDH 行は括弧付き記録値（（53）・（1.9）・（2））で
区別済みだが、「引用してはならない」旨の明文はまだ無い。

## 選択肢

### (a) 12ヶ月を 1 run 再取得する（推奨）

既存 summary は残し、新しい系列を正本にする（`ISS-20261012-CBD-004` と同じ扱い）。

| 項目 | 値 |
|---|---|
| `study_id` / `source_id` / `collector_id` | `cannabinoid-raw-collection` / `google-trends` / `google-trends-mcp` |
| `query_id`（`metadata/queries/query-registry.json`、状態 `active`） | `crdh-general-ja`（`compound_crdh` / テキスト `CRDH`） |
| 提出パラメータ | `tool=interest_over_time`、`terms=["CRDH"]`、`geo="JP"`、`timeframe="today 12-m"` |
| 窓（`metadata/windows/2025-10-19_2026-10-18.json` が存在） | `window_id="2025-10-19_2026-10-18"`（他 3 化合物 THCV・H4CBH・HHBD の 2026-10-23 再取得と同一窓。窓をまたいだ比較をしない制約（§2.1.3）のため本窓を選ぶ） |
| 計画書 | `metadata/plans/gt-12m-recollect-crdh.json` を新規作成（`gt-12m-recollect-thcv.json` と同型。現時点で同名計画書は無い） |
| 費用 | 無料（`google-trends-mcp` アダプタの live 収集。既存 run の `environment.adapter` と同一手段） |
| 成果物 | `data/raw/google_trends/<YYYYMMDDTHHMMSSZ-google-trends-crdh-12m>/` に `records_crdh.json`（53 週の `data` 配列）・`payload.json`・`run_metadata.json`・`artifact-manifest.json`（2026-10-23 再取得 3 run と同構成）。既存 `records_crdh_12m.json` は残す |

再取得後は `gt-summary --timeframe 12m --compound CRDH` が `shape=series` で平均を算出できることを確認し、
§2.1.3 の CRDH 行の括弧を外す。新 run も Google Trends の相対指数であり、旧窓（2025-09-28〜）の 8 化合物とは
窓違いのため直接比較しない（§2.1.3 の制約どおり）。

### (b) summary-only のまま維持し、`avg_12m` の引用を methodology で禁止する

収集は行わない。`methodology.md` §2.1.3 に以下を追記する（文案。適用は owner / 別変更）:

> CRDH の 12ヶ月値（`data_points` 53・`avg_12m` 1.9・`nonzero_weeks` 2・ピーク週 2025-11-09 週）は
> `records_crdh_12m.json` の**記録値**であり、週次系列を収蔵していないため raw から検算できない。
> `processing.gt_statistics` も `partial` 形状として平均・ピーク・最新値を算出不能とする。
> 原稿・下流はこれらの数値を引用してはならない。12ヶ月の CRDH 言及は共通スケール比較
> （`20261008T125719Z-google-trends-common-scale-crdh/comparison.json`）の範囲でのみ行う。

この場合 §2.1.3 の CRDH 行の括弧付き表記は恒久的な注記になる。

### (c) 12ヶ月の単独系列を使わず、共通スケール比較だけを 12ヶ月の根拠にする

(b) の引用禁止に加え、12ヶ月の CRDH 定量言及は共通スケール値（CRDH 0。比較セット CRDH vs CBD vs THC、
`comparison.json`、`collected_at="2026-10-08"`）に一本化する。失うもの:

- 単独正規化（当該キーワードの最大週=100）の 12ヶ月平均・ピーク週・非ゼロ週数。
  共通スケールは比較セット内最大（CBD ピーク週）を 100 とする別正規化のため、
  他 11 化合物の単独平均（§2.1.3 表）と数値比較できない。
- 観測窓の一致。共通スケール run の収集日は 2026-10-08 で、2026-10-23 再取得窓
  （2025-10-19〜2026-10-18）とも旧窓（2025-09-28〜2026-09-27）とも別観測。

## 完了条件

- [ ] owner が (a) / (b) / (c) を選択
- [ ] (a) の場合: 新 run が catalog され `data` 53 週を持ち、
  `gt-summary --timeframe 12m --compound CRDH` が `shape=series` で平均を返すこと。
  §2.1.3 の CRDH 行が括弧なしの実測値になること。旧 summary は残すこと
- [ ] (b) の場合: §2.1.3 に上記引用禁止の注記が入り、`avg_12m`・ピーク週・非ゼロ週数を引用する原稿・下流が無いこと
- [ ] (c) の場合: (b) に加え、12ヶ月の CRDH 定量言及が共通スケール値のみになり、その正規化の違いが methodology に明記されること
