# data/raw/google_trends

この研究で追跡する Google Trends raw。**96 run ディレクトリ**（1 ディレクトリ = 1 run）。run-id 形式は `<UTC>Z-google-trends-<slug>`（AGENTS.md "Run Identity"）。

このディレクトリだけが Git 追跡対象なのは `.gitignore` の例外による（`**/data/raw/*` は原則 untracked、`google_trends/` のみ追跡）。**YouTube raw はこの study の `data/raw/youtube/` に machine-local で置き、Git 非追跡・公開対象外**（このディレクトリには無い）。X raw はこの study の raw に保持していない。YouTube の集計物は [`data/processed/`](../../../data/processed) にある。

## 現在の構成

- **catalog 採用 64 run**: `artifact-manifest.json` を持ち、[`metadata/data-catalog.json`](../../../metadata/data-catalog.json) に載る。登録 30 語の Google Trends 被覆は 5年 26/30・12ヶ月 20/30（追加 15 語は 5年 11/15・12ヶ月 6/15）。
- **manifest を持たない 32 run**: catalog 外（2026-10-01 / 10-02 / 10-05 / 10-08 / 10-12 の run）。raw は不変の証跡として残す。
- **追加 15 語の 17 adopted run**: 12ヶ月 6 + 5年 11。窓は 12ヶ月 `2025-11-09_2026-11-15`（観測 2025-11-09 〜 2026-11-08）、5年 `2021-11-07_2026-11-15`（観測 2021-11-07 〜 2026-11-08）で、いずれも `today 12-m` / `today 5-y` を reference time で nominal に解決した**近似窓**。各系列は自分のピーク=100 に正規化され、化合物間で比較できない。
- **採用外 13 本**: 13 語バッチの 12 本（NO_DATA 6・HTTP 429 6）と CBDV 12ヶ月（429 が 2 回の後 NO_DATA）。`.quarantine/` に残り、catalog にも raw にも入らない。**0 観測でも欠測でもない**。

**CBX の Google Trends raw もここが正本**（2026-11-04 の owner 決定で `datasets/cbx-search-trends/` から所有を移管）。移管は run id と payload バイトを変えずに行った。`20261001` の 4 run は legacy 形状のまま移動し、`20261015T0428*Z-…-boundary-*` の 4 run は `staging-declaration-v1` で study 付きの run_metadata を再発行した（観測のやり直しではない）。宣言は [`20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json`](../../../../../metadata/provenance/declarations/20261104-cbx-google-trends-ownership-cannabinoid-raw-collection.json)、条件は [`methodology.md`](../../../methodology.md) §2.1.6。

## 照合

- 目録（現在の採用 run）: [`metadata/data-catalog.json`](../../../metadata/data-catalog.json)
- 採用宣言: [`metadata/provenance/declarations/`](../../../../../metadata/provenance/declarations/)
- クエリ登録: [`metadata/queries/query-registry.json`](../../../../../metadata/queries/query-registry.json)
- 収集条件・窓・制約: [`methodology.md`](../../../methodology.md)、[`README.md`](../../../README.md)
- 現行契約の適合: `make audit-new-runs`（manifest を持つ run は全適合が必須）
- 宣言待ちの棚卸し: `make audit-adoption`（manifest の無い legacy 3 件が出る）
