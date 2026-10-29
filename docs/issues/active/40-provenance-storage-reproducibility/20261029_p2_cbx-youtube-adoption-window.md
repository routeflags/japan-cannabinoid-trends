# Issue: CBX YouTube 4 run の採用方法（payload に絶対公開日が無い）

**ID:** ISS-20261029-PRV-016
**優先度:** P2 (Medium)
**ステータス:** OPEN
**GitHub:** [#14](https://github.com/routeflags/japan-cannabinoid-trends/issues/14)
**対象:** `datasets/cbx-social-trends/data/raw/youtube/`（一次 checkout、4 run ＋ 4 の loose ファイル）、
`datasets/cbx-social-trends/{README.md, methodology.md}`、`src/validation/adoption.py`、
`src/collection/core/staging.py`（`staging-declaration-v1`）

## 背景

採用が進まない原因を「作業量」ではなく「構造」で特定するため、raw 層を 1 ディレクトリずつ棚卸しした（`validation.cli audit-adoption`、`src/validation/adoption.py`）。
一次 checkout（`datasets/` を読み取り専用で走査）の実測は次のとおり。

```text
adoption audit: 86 run dir(s) in 12 source dir(s),
  run_metadata=46, no_run_metadata=40 (vendor_envelope=10, metadata_missing=29, metadata_unrecognized=1),
  request_unrecorded=4, window_unrecorded=43, run_id_mismatch=17,
  uncatalogued=86, empty=2, loose_files=19, violations=2
```

この監査は、それまでの `audit-new-runs` / `audit-provenance` が**見ていなかった** raw ディレクトリを列挙する。
両監査は `run_metadata.json` を起点に run を発見するため、これを持たないディレクトリはどちらの監査にも現れず、
採用の停滞が失敗としても件数としても見えなかった（不可視であって「停止」ではない）。

`cannabinoid-raw-collection` の raw を置く `cannabinoid-multi-trends/data/raw/youtube/`（25 ディレクトリ）でも同じ形が出る:
`run_metadata` 8 / `metadata_missing` 13 / `vendor_envelope` 3 / `metadata_unrecognized` 1。

補足（別件の観測）: 一次 checkout では study 名の改名が raw のディレクトリ名に追従しておらず、
カタログ（`metadata/data-catalog.json`）は改名後の study 側、raw は旧名側にある。
そのため `catalogued` は全件 false（`sources_without_catalog=12`）となり、カタログとの照合は現状機能しない。
raw の移動は別途の判断（`previous_study_ids` による解決で足りるかを含む）。

### CBX YouTube の 4 run（本 issue の中心）

| run ディレクトリ | 状態 | 内容 |
|---|---|---|
| `20261001T074851Z-youtube-cbx-rikiddo` | `vendor_envelope` | Apify run envelope（`id`/`status`）のみ。`records.json` 20 件 |
| `20261001T075500Z-youtube-cbx-rikiddo-v2` | `vendor_envelope` | 同上。`records.json` 26 件（採用済みの公開数値 24 件の出所） |
| `20261004T135232Z-youtube-cbx-12months` | `run_metadata` | v3 経路（他 study の残存と同じ）。`request_recorded`/`window_recorded` = true |
| `20261004T135457Z-youtube-cbx-rikiddo-12months` | `run_metadata` | 同上 |

`data/raw/youtube/` 直下には run ディレクトリに入っていない payload ファイルが 4 つある（`youtube_cbx_rikiddo_20261001.csv` / `_v2.csv` / `.json`、`youtube_domestic_20260907_50.csv`）。

## 停滞の実体（実測）

1. **payload に絶対公開日が無い。** Apify の 2 run は `publishedAt` を持たず、`snippet.timestamp` は `"2 weeks ago"` / `"3 years ago"` のような相対表記のみ（ISO 日時の出現 0 件）。
2. **`staging-declaration-v1` は絶対窓を必須とする。** `window.start` / `window.end_exclusive` は必須で、既存の採用済み宣言（`metadata/provenance/declarations/20261015-youtube-csv-adoption.json`）は
   *payload の公開日レンジ* を窓として記録している。CBX の payload からはその値を導けない。
3. **run envelope に検索条件が無い。** `search_term` / `max_videos` は envelope に無い（`id`/`status`/`startedAt`/`finishedAt` のみ）。
   検索語は methodology §3.4 と README に `CBX リキッド` として残るが、**取得上限は未記録**。 envelope にはコスト項目もあるが、これは採用成果物に転記しない（AGENTS.md のコスト表記禁止）。
4. **既存文書の帰属がまちがっていた。** `methodology.md` §3.4 は `Max videos: 50` / `Run date 2026-09-07` を YouTube のパラメータ表として載せていたが、
   これは 2026-09-07 の初回試行（run ディレクトリを持たない loose ファイル `youtube_domestic_20260907_50.csv`）の値であり、データを産んだ 2026-10-01 の 2 run の値ではない。
   §3.4 は実行 4 件（初回試行、run 1、run 2、v3 の 2 run）を分けて記録する形に直した。

つまり停滞は「宣言を書く手間」ではなく、**窓を payload から確定できないのに窓が必須**という仕様と payload の不整合にある。

## 仕様での位置づけ

- `temporal.collector_window_type` には `unbounded` が既にある（`src/validation/schemas/temporal.py`）。schema 変更は不要。
- よって CBX の 2 run は**現行 schema のまま宣言できる**。残るのは「窓に何を書くか」の意味づけだけで、それは運用判断であり、この issue が決める。
- raw は変更しない。`run_metadata.json` を後付け生成しない。再収集も要件にしない（再収集しても相対時刻しか返らないため、同じ不整合が再発する）。

## 決定依頼

**Q1. 窓の意味づけ → 回答: (c) 不採用（owner 2026-10-29）。** CBX YouTube の 4 run は採用しない。公開済みの 24 件は「記録値であり再計算しない」として methodology に留保する。以下は検討時の選択肢の記録である。

- (a) `window` = 要求の広がりを表す `1970-01-01` .. 収集時刻、`collector_window_type: unbounded`、
  `boundary_semantics` に「payload に絶対公開日が無いため、この窓は観測レンジではなく無制限の要求を表す」と明記し、`limitations` に相対時刻のみであることを書く。
- (b) `window` = 収集日 1 日。単純だが「その日の動画だけを探した」と誤読される。
- (c) この 2 run は採用しない。公開済みの 24 件は「記録値であり再計算しない」として methodology に留保する。← 採用

**Q2. v1 の扱い。** 不採用決定により両 run とも採用対象外。v1 が v2 に置き換えられた初回実行であることは methodology §3.4 に記録済み。

**Q3. `max_videos`。** 不採用決定により回答不要。取得上限は未記録のまま残る。

**Q4. YouTube 以外の停滞 run。** 本 issue の対象は CBX YouTube だが、同型の停滞は
`cannabinoid-raw-collection` の YouTube 25 run にもある（`metadata_missing` 13 / `vendor_envelope` 3 / `metadata_unrecognized` 1）。
同じ規則で一括して扱うか、別 issue に分けるか。

## 完了条件

- Q1 の回答がこのファイルに記録されている（(c) 不採用、owner 2026-10-29）。
- 公開済み 24 件を「記録値であり再計算しない」として methodology に留保する。
- `methodology.md` §3.4 の帰属誤りが直っている（本 issue で対応済み）。
- Q4（`cannabinoid-raw-collection` の YouTube 25 run の扱い）は別途判断する。本 issue は Q4 の回答まで OPEN のまま残す。

## 参照

- `src/validation/adoption.py`（本 issue で追加した棚卸し。仕様は `docs/specs/validation-framework.md` §22.6）
- `docs/issues/active/40-provenance-storage-reproducibility/20261024_p1_youtube-v3-residual-raw.md`（v3 残存 raw）
- `docs/issues/active/40-provenance-storage-reproducibility/20261024_p2_youtube-raw-batch-without-metadata.md`（#10。未記録を明示したまま採用する前例）
- `docs/issues/active/40-provenance-storage-reproducibility/20261024_p2_run-id-versus-recorded-time.md`（#12。`run_id_mismatch` 17 件の一部）
- `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`（採用済み宣言の書式）
