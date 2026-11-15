# data/raw/google_trends

この研究で追跡するGoogle Trends raw。**109 run directories**（1 directory = 1 run）。run-id形式は`<UTC>Z-google-trends-<slug>`（AGENTS.md "Run Identity"）。

このディレクトリだけが Git 追跡対象なのは `.gitignore` の例外による（`**/data/raw/*` は原則 untracked、`google_trends/` のみ追跡）。**YouTube raw はこの study の `data/raw/youtube/` に machine-local で置き、Git 非追跡・公開対象外**（このディレクトリには無い）。X raw はこの study の raw に保持していない。YouTube の集計物は [`data/processed/`](../../../data/processed) にある。

## 現在の構成

- **catalog採用77 run**: `artifact-manifest.json`を持ち、[`metadata/data-catalog.json`](../../../metadata/data-catalog.json)に載る。登録63トピックのGoogle Trends被覆は5年29/63・12ヶ月30/63（追加15語は5年14/15・12ヶ月7/15）。候補形式27は12ヶ月9 adopted /18 `NO_DATA`、5年0 adopted（窓guard停止1回後に1 queryをHTTP 429で3回、26 queryは未試行）。12ヶ月のinherited baseline 21/63は既存値。2026-11-11登録の6検索topicは未収集。
- **manifestを持たない32 run**: catalog外（2026-10-01 / 10-02 / 10-05 / 10-08 / 10-12のrun）。rawは不変の証跡として残す。
- **追加15語の21 adopted run**: 12ヶ月7 + 5年14。窓は12ヶ月`2025-11-09_2026-11-15`（観測2025-11-09〜2026-11-08）、5年`2021-11-07_2026-11-15`（観測2021-11-07〜2026-11-08）で、いずれも`today 12-m` / `today 5-y`をreference timeでnominalに解決した**近似窓**。
- **候補形式の9 adopted 12ヶ月run**: 9 run全ての宣言窓は`2025-11-09_2026-11-15`、54週で最終観測日2026-11-15。前記の既存21/63 baselineは53週で最終観測日2026-11-08であり、週バケット範囲が異なる。これらの系列を同一窓の比較可能データとして扱わず、boundary verificationの完了まではcoverageとseries shapeを区別する。各系列は自分のピーク=100に正規化され、化合物間で比較できない。
- **採用外 9 本**: 失敗窓 13 件（13 語バッチ 12 本と CBDV 12ヶ月）を各 1 回再取得し、10-OH-HHC 5年・THXE 5年・THCA 12ヶ月・THCA 5年の 4 系列を採用した。残る 9 試行は NO_DATA として `.quarantine/` に残り、catalog にも raw にも入らない（先行の HTTP 429 run も保持）。**0 観測でも欠測でもない**。

**CBX の Google Trends raw もここが正本**（2026-11-04 の owner 決定で `datasets/cbx-search-trends/` から所有を移管）。移管は run id と payload バイトを変えずに行った。`20261001` の 4 run は legacy 形状のまま移動し、`20261015T0428*Z-…-boundary-*` の 4 run は `staging-declaration-v1` で study 付きの run_metadata を再発行した（観測のやり直しではない）。宣言は [`20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json`](../../../../../metadata/provenance/declarations/20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json)、条件は [`methodology.md`](../../../methodology.md) §2.1.6。

## 照合

- 目録（現在の採用 run）: [`metadata/data-catalog.json`](../../../metadata/data-catalog.json)
- 採用宣言: [`metadata/provenance/declarations/`](../../../../../metadata/provenance/declarations/)
- クエリ登録: [`metadata/queries/query-registry.json`](../../../../../metadata/queries/query-registry.json)
- 収集条件・窓・制約: [`methodology.md`](../../../methodology.md)、[`README.md`](../../../README.md)
- 現行契約の適合: `make audit-new-runs`（manifest を持つ run は全適合が必須）
- 宣言待ちの棚卸し: `make audit-adoption`（manifest の無い legacy 3 件が出る）
