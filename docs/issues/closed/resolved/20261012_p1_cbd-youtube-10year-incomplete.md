# Issue: CBD YouTube 旧10年系列の証拠・公開対象からの除外

**ID:** ISS-20261012-CBD-003
**優先度:** P1 (High)
**ステータス:** RESOLVED (2026-10-16)
**対象:** `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`、採用済み CBD YouTube runs（本文に記載）、および証拠・公開対象から除外する旧10年系列
**決定記録:** `docs/issues/closed/resolved/20261015_p1_cbd-youtube-10year-scope-decision.md` (`ISS-20261015-CBD-007`)

## 概要

禁止済み旧手段由来の CBD YouTube 旧10年系列は、現行の証拠・補完対象・公開説明のいずれにも使わない。後続の誤用を防ぐため、資料・処理対象から除外する。

採用済み Apify CBD CSV の 2 runs は、旧10年系列とは別の YouTube series / snapshot として扱う。旧系列の欠測を直接補完・置換する根拠にはしない。

## 除外範囲

- 旧10年系列（禁止済み旧手段由来）は現行証拠および公開対象から除外する。補完対象・根拠・公開説明として扱わない。
- 除外にあたり旧手段名・使用ログ・error payload を根拠や説明に使わない。本 issue にも記録しない。
- 旧系列の件数・年別内訳・ファイル構成は証拠として保持しない。

## 採用する YouTube 証拠（別系列）

`metadata/provenance/declarations/20261015-youtube-csv-adoption.json` を source of truth とする。CBD に関する採用済み runs は次の 2 件であり、旧10年系列とは別の series / snapshot である。

- `20261010T144421Z-youtube-youtube-consistency`（CBD リキッド、別系列の観測）
- `20261011T191900Z-youtube-youtube-consistency`（CBD リキッド、別系列の観測）

採用済み CSV は旧10年系列の欠測を直接補完・置換する根拠にはしない。両者は study・取得方式・クエリ・期間設計が異なる別の観測である。

## 対応方針

- 旧10年系列を不完全な証拠系列として公開資料に残さない。欠測の列挙による記載訂正ではなく、証拠・公開対象からの除外として扱う。
- 旧系列に状態ラベルを付与しない。
- raw は本 worktree では追跡対象外のため、worktree 内での raw 削除は行わない。外部 checkout には触れない。

## 完了条件

- [x] 旧10年系列を現行証拠・補完対象・公開説明の対象外とした。
- [x] 旧手段名・使用ログ・error payload を本 issue の根拠・説明から除いた。
- [x] 採用済み Apify CBD CSV を旧系列とは別の series / snapshot として記録した（上記 2 runs、宣言ファイルを source of truth とする）。
- [x] 旧10年系列の完成・補完と誤解される説明を公開・matrix の対象外とした（旧系列自体を証拠にしない）。

## オーナー回答

公式 API は禁止。禁止ツール由来データの削除と、後続が失敗しないための資料対応を承認（2026-10-15/16）。

## 対応記録（2026-10-16）

- オーナー指示に基づき、旧10年系列を証拠・補完対象・公開説明から除外した。不完全系列としての温存は行わない。
- 旧系列の件数・年別内訳・ファイル構成・ログ・error payload の詳細は本 issue に記録しない（誤用防止）。
- 採用済み CBD runs（上記 2 件）は宣言ファイルを正とし、旧系列の置換行ではないことを明記した。
- 本 Delta worktree 内に追跡対象の旧 raw ディレクトリは存在しない（`data/raw/youtube/` 自体が存在せず、raw は gitignored のため）。worktree 内での raw 削除は不要・未実施。外部 checkout には触れていない。
- 関連資料（matrix・gap 分析・research 資料・仕様書・由来照合記録）の旧系列言及は本対応で中立化した。CBD-007 には除外への変更を追補した。
