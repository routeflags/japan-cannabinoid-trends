# Issue: 2026-11-15 candidate-form Google Trends / YouTube collection

**ID:** ISS-20261115-COL-034
**優先度:** P2 (Medium)
**ステータス:** OPEN
**対象:** `datasets/cannabinoid-raw-collection/metadata/plans/`, `data/raw/google_trends/`, `data/raw/youtube/`, `metadata/data-catalog.json`, `metadata/provenance/declarations/`, README / methodology coverage
**関連:** [`ISS-20261115-TAX-045`](../50-taxonomy-standards/20261115_p2_candidate-form-registration.md)（27候補形式の登録。収集とは別工程）

## 収集許可と範囲

登録時の owner 指示は検索トピックの登録だけを許可し、収集や公開を許可しなかった（TAX-045）。その後の別の owner 指示は、登録済み候補形式について次の収集とローカル branch への必要な provenance / data updates を許可した。

- Google Trends: 27 個別 query の `today 12-m` と `today 5-y` の単独系列。
- YouTube: 27 個別 `product_liquid` query の liquid-only primary。
- X: 対象外。
- ローカル branch への commit は許可された。push、外部公開、release は許可されていない。

この別許可は登録指示を遡及的に変更せず、登録・収集・採用・公開を別段階に保つ。化学的同一性や検索結果の内容を確立せず、既存のfamily/general queryやrunへ結果を割り当てない。

## 現在の結果

27 候補形式の個別状態は研究 README の term-to-query map と collection coverage、run-level の adopted Google Trends 情報は `metadata/data-catalog.json`、YouTube 採用情報は各 collection declaration / catalog entry を正本とする。

- **Google Trends 12ヶ月:** 27 query ID / 28 attempts（`(6aR,9R,10aS)-HHC` の修正後 retry を含む）。9 adopted、18 `NO_DATA`。同 query の先行 parse failure は quarantine に残し、採用 retry と同一 payload bytes である。
- **Google Trends 5年:** 27 plan。0 adopted。窓 guard で止まった1試行の後、`(6aR,9R,10aS)-HHC` を3回試し、すべて HTTP 429。残る26 query ID は未試行。単独5年の新窓は `2021-11-14_2026-11-15`。HTTP 429 を0観測や `NO_DATA` に変換しない。
- **YouTube:** 27 query 全て試行。19 adopted、8 `NO_VIDEOS`（未採用）。`NO_VIDEOS` marker は動画行も観測日も持たないため run declaration / raw adoption にせず、世界全体の0と解釈しない。
- **全体被覆:** YouTube audit は primary 50 runs、48/63 compounds、49/64 queries、15 missing compounds、1 retained out-of-scope、0 violations を報告する。候補形式は19/27 adopted、8 `NO_VIDEOS`。

## Retention と再現性

- Google Trendsの採用9 runは`raw-search-tracked` policyに従いGit追跡対象。run metadataとmanifestの全18 artifact hash / byte sizeを再検証済み。9 raw directoriesと対応するcatalog / documentation更新はローカルbranchにcommit済み。

- YouTube の採用19 raw runsは `raw-social-default` に従い `git_untracked`。19 declaration と raw manifest / hash / record count / query ID / catalog entry は相互照合済み。raw payloadは公開・Git追跡しない。
- Google Trends の失敗・停止run（quarantine 22件）、収集ログ、YouTube `NO_VIDEOS` payload はローカルの `.quarantine/` / `.staging/` 証跡であり、tracked rawや採用runではない。元raw・失敗証跡を置換しない。
- `today 12-m` の9新系列は54週（最終観測日 2026-11-15）。inherited baseline 21系列は53週で終端 2026-11-08。登録63トピックの12ヶ月合計30/63はこの異なる週バケット範囲を含む。両群を同じ週次窓の比較可能な系列と扱わず、比較用途は boundary verification の完了まで制限する。
- YouTubeの候補形式19 rawは機械ローカルであり、採用宣言とcatalogは追跡対象。commit後のraw-completeness / retention auditsはretention violation 0、YouTube rawのlocal-only presence 19を報告する。

## 完了済み作業と未解決事項

- 9 adopted Google Trends raw directories、catalog、coverage documentation、監査snapshots、登録時点と採用状態を分けるテストをローカルbranchにcommitした。
- YouTube coverage、raw completeness / retention、adoption、new-run auditsを実行し、YouTube候補19 rawのlocal-only retentionと、Google Trends rawのtracked policyへの適合を確認した。
- 5年候補形式は0/27 adopted。26 queryは未試行であり、1 queryはHTTP 429が3回。現在のplan/windowとrate limitを確認せず再試行しない。再試行する場合は必要に応じ新しいplan/windowとcollection判断を用意する。
- push、外部公開、releaseは許可されておらず、実施していない。

## References

- `datasets/cannabinoid-raw-collection/metadata/plans/gt-*-20261115.json`（54 plans）
- `metadata/provenance/declarations/20261115-youtube-candidate-form-*-cannabinoid-raw-collection.json`（採用19 query）
- `datasets/cannabinoid-raw-collection/metadata/query-design.json`（required primary / coverage rule）
- `docs/specs/raw-data-policy.md`（Google Trends tracked、YouTube untracked）
