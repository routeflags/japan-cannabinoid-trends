# Issue: 5年の「○○ リキッド」が 5/13 語しか無い

**ID:** ISS-20261023-GT-008  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-24) — 8 語を 5年で収集し、7 語が系列・THC-O リキッドは NO_DATA（欠測）として確定した  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T064246Z-google-trends-ja-rikiddo-5y-main5/`、
`README.md` のキーワード表  
**GitHub:** [#4](https://github.com/routeflags/japan-cannabinoid-trends/issues/4)

## 決定（owner, 2026-10-24）

**選択肢 1（8 語を 5年で収集）**を採用する。窓は `2021-10-17_2026-10-18` で、main5 の観測範囲とは 1 週ずれる別観測になる。plan は下記「収集仕様」の 8 件を作成し、各 1 run を収集した（結果は下記「実施」）。

## 実施（2026-10-24）

8 plan（`datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-rikiddo-*.json`）を作成し、1 語 1 run で live 収集した（`today 5-y` / geo JP、窓 `2021-10-17_2026-10-18`）。429 は発生せず、全 8 run が 1 回の fetch で確定した。7 語は 262 週の系列を catalog し、THC-O リキッドは系列なし（`NO_DATA`、quarantine。欠測であって 0 観測ではない）。新規 8 run は main5（`2021-10-10 .. 2026-10-11`）とは別窓の別観測であり、単独系列の値を main5 と直接比較しない。

| クエリ | run | 系列 | 週数 | 平均 | 非ゼロ週 |
|---|---|---|---|---|---|
| THCV リキッド | `20261023T185238Z-google-trends-ja-rikiddo-5y-thcv` | あり | 262 | 0.3817 | 1 |
| THC-O リキッド | `20261023T185246Z-google-trends-ja-rikiddo-5y-thco` | なし（`NO_DATA`、quarantine） | — | — | — |
| THCH リキッド | `20261023T185305Z-google-trends-ja-rikiddo-5y-thch` | あり | 262 | 6.0802 | 52 |
| CRDH リキッド | `20261023T185311Z-google-trends-ja-rikiddo-5y-crdh` | あり | 262 | 0.6069 | 2 |
| CRDP リキッド | `20261023T185317Z-google-trends-ja-rikiddo-5y-crdp` | あり | 262 | 1.1603 | 4 |
| H4CBH リキッド | `20261023T185325Z-google-trends-ja-rikiddo-5y-h4cbh` | あり | 262 | 0.8168 | 4 |
| HHBD リキッド | `20261023T185332Z-google-trends-ja-rikiddo-5y-hhbd` | あり | 262 | 0.8168 | 4 |
| HHCH リキッド | `20261023T185339Z-google-trends-ja-rikiddo-5y-hhch` | あり | 262 | 1.9008 | 14 |

平均は系列値の単純平均（derived）。観測範囲はいずれも `2021-10-17 .. 2026-10-18`、`window_id` は `2021-10-17_2026-10-18`。

## 概要

「リキッド」系クエリの 5年系列は、main5 の 5 語（CBD / CBG / CBN / HHC / THC リキッド）に加え、
新規 8 run で 7 語（THCV / THCH / H4CBH / HHBD / HHCH / CRDP / CRDH リキッド）が系列を持つ。
THC-O リキッドは 5年でも系列なし（`NO_DATA`、quarantine。欠測であって 0 観測ではない）。
すなわち 5年リキッドは 13 語中 12 語が系列あり、1 語が系列なしである。
12ヶ月は 13 語すべてを照会済みだが、12ヶ月の有無から 5年の有無は推定できない（下記）。

## 実測（tracked raw のみ）

### 5年: main5 のみが系列を持つ

`20261012T064246Z-google-trends-ja-rikiddo-5y-main5`（`timeframe: today 5-y`, `geo: JP`）。
全 5 ファイルが 262 週、観測範囲 `2021-10-10 .. 2026-10-11`。
平均は系列値の単純平均（derived、再計算済み）。

| クエリ | ファイル | 週数 | 観測範囲 | 平均 | 非ゼロ週 |
|---|---|---|---|---|---|
| CBD リキッド | `records_cbd-rikiddo-5y.json` | 262 | 2021-10-10 .. 2026-10-11 | 36.527 | 257 |
| CBG リキッド | `records_cbg-rikiddo-5y.json` | 262 | 2021-10-10 .. 2026-10-11 | 0.683 | 4 |
| CBN リキッド | `records_cbn-rikiddo-5y.json` | 262 | 2021-10-10 .. 2026-10-11 | 4.401 | 27 |
| HHC リキッド | `records_hhc-rikiddo-5y.json` | 262 | 2021-10-10 .. 2026-10-11 | 2.992 | 25 |
| THC リキッド | `records_thc-rikiddo-5y.json` | 262 | 2021-10-10 .. 2026-10-11 | 8.550 | 87 |

`run_metadata.json` の `queries` は上記 5 語のみ。`zero_status` は 5 語すべて `low_volume`。
rate-limit 注記: CBD リキッド初回 429 → 約5分 backoff 後に成功（`rate_limit_429` に記録あり）。

### 5年: 新規 8 語（別窓）の収集結果

窓 `2021-10-17_2026-10-18`（`today 5-y`、geo JP）の 1 語 1 run。観測範囲はいずれも `2021-10-17 .. 2026-10-18`。
平均は系列値の単純平均（derived）。

| クエリ | run | 週数 | 観測範囲 | 平均 | 非ゼロ週 |
|---|---|---|---|---|---|
| THCV リキッド | `20261023T185238Z-google-trends-ja-rikiddo-5y-thcv` | 262 | 2021-10-17 .. 2026-10-18 | 0.3817 | 1 |
| THCH リキッド | `20261023T185305Z-google-trends-ja-rikiddo-5y-thch` | 262 | 2021-10-17 .. 2026-10-18 | 6.0802 | 52 |
| CRDH リキッド | `20261023T185311Z-google-trends-ja-rikiddo-5y-crdh` | 262 | 2021-10-17 .. 2026-10-18 | 0.6069 | 2 |
| CRDP リキッド | `20261023T185317Z-google-trends-ja-rikiddo-5y-crdp` | 262 | 2021-10-17 .. 2026-10-18 | 1.1603 | 4 |
| H4CBH リキッド | `20261023T185325Z-google-trends-ja-rikiddo-5y-h4cbh` | 262 | 2021-10-17 .. 2026-10-18 | 0.8168 | 4 |
| HHBD リキッド | `20261023T185332Z-google-trends-ja-rikiddo-5y-hhbd` | 262 | 2021-10-17 .. 2026-10-18 | 0.8168 | 4 |
| HHCH リキッド | `20261023T185339Z-google-trends-ja-rikiddo-5y-hhch` | 262 | 2021-10-17 .. 2026-10-18 | 1.9008 | 14 |

THC-O リキッドは系列なし: `20261023T185246Z-google-trends-ja-rikiddo-5y-thco` は `execution.status = failed` / `errors[].code = NO_DATA` のため quarantine され、catalog されない。窓 `window_id` は `2021-10-17_2026-10-18`。

H4CBH と HHBD は平均・非ゼロ週が一致するが、週次値は異なる別系列である（payload で確認）。

### 12ヶ月: phase-a（5 語）+ phase-b（8 語）で 13 語を照会、系列あり 8/13

いずれも `timeframe: today 12-m`, `geo: JP`、観測範囲 `2025-10-12 .. 2026-10-11`。
「系列あり」= `data` が 53 要素、「系列なし」= `data: []`（空配列、observed_zero ではなく閾値未満の無系列）。

phase-a `20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m`:

| クエリ | 週数 | 非ゼロ週 | 状態 |
|---|---|---|---|
| CBD リキッド | 53 | 50 | 系列あり |
| CBG リキッド | 53 | 2 | 系列あり |
| CBN リキッド | 53 | 5 | 系列あり |
| THC リキッド | 53 | 2 | 系列あり |
| HHC リキッド | 0 | 0 | 系列なし（`zero_status: unknown`） |

phase-a-repeat `20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m` は同一パターンを再現
（CBD 53/50、CBG 53/2、CBN 53/5、THC 53/2、HHC 0。HHC の `zero_status` 表記のみ `unknown` → `below_threshold`）。
`repeat_diff.json` によれば CBD 平均 64.02 → 64.08、変動週は 1 週のみ。HHC の空系列は一過性ではない。

phase-b `20261012T061614Z-google-trends-ja-rikiddo-phase-b-12m`:

| クエリ | 週数 | 非ゼロ週 | 状態 |
|---|---|---|---|
| THCV リキッド | 0 | 0 | 系列なし（`zero_status: unknown`） |
| THC-O リキッド | 0 | 0 | 系列なし（`unknown`） |
| THCH リキッド | 53 | 3 | 系列あり（`low_volume`） |
| H4CBH リキッド | 53 | 3 | 系列あり（`low_volume`） |
| HHBD リキッド | 53 | 2 | 系列あり（`low_volume`） |
| HHCH リキッド | 53 | 1 | 系列あり（`low_volume`） |
| CRDP リキッド | 0 | 0 | 系列なし（`unknown`） |
| CRDH リキッド | 0 | 0 | 系列なし（`unknown`） |

12ヶ月合計: 系列あり 8 語（CBD / CBG / CBN / THC / H4CBH / HHBD / HHCH / THCH）、
系列なし 5 語（HHC / CRDH / CRDP / THC-O / THCV）。

### 12ヶ月の有無から 5年の有無は推定できない

**HHC リキッドは 12ヶ月で系列なし、5年では 262 週の系列がある**（平均 2.992、非ゼロ 25 週）。
閾値と正規化は期間依存のため、未収集の 8 語は**照会するまで分からない**。
特に option 3 の「12ヶ月で系列がある 4 語だけ先行」は命中率が高いと期待できるが保証はなく、
残り 4 語（12ヶ月でも空の THCV / THC-O / CRDP / CRDH）については 5年照会が唯一の確認手段である。

## CBX リキッドの 5年系列は存在しない（evidence）

- リポジトリ全体の `datasets/*/data/raw/**/*.json` を走査した結果、`timeframe: today 5-y` かつ
  キーワードに `リキッド` を含む records は **main5 の 5 ファイルのみ**である（全 25 liquid records 中）。
- `CBX リキッド` の payload はすべて `today 12-m` のみ:
  `datasets/cbx-search-trends/data/raw/google_trends/20261001T115959Z-google-trends-cbx-rikiddo/records.json`
  （53 週、12ヶ月系列あり）と variance-check の run2（全系列ではなく `nonzero_data` のみ）である。
- CBX study の 5年 run `20261015T042857Z-google-trends-boundary-5y` は bare `CBX` のみ:
  `query_provenance.query_id = cbx-general-ja`、`submitted_query = CBX`、262 週、
  観測範囲 `2021-10-10 .. 2026-10-11`。`CBX リキッド`（`cbx-liquid-ja` / `product_liquid`）とは別クエリである。
- よって「CBX リキッド 5年」は未収集であるが、本 issue の 13 語（CBX を含まないリキッド 13 化合物）の数には影響しない。
  CBX を 5年リキッド比較に含めるかは別判断（本 issue の option には含めない）。

## query registry: 8 語の `*-liquid-ja` はすべて登録済み（追加不要）

`metadata/queries/query-registry.json`（`schema_version 1.0.0`）に 8 語すべてが `active` で存在する。
不足している registry エントリは無い。

| 収集すべきクエリ文 | 必要な `query_id` | `compound_id` | `intent_id` | 登録状態 |
|---|---|---|---|---|
| THCV リキッド | `thcv-liquid-ja` | `compound_thcv` | `product_liquid` | active（存在） |
| THC-O リキッド | `thc-o-liquid-ja` | `compound_thc_o` | `product_liquid` | active（存在） |
| THCH リキッド | `thch-liquid-ja` | `compound_thch` | `product_liquid` | active（存在） |
| CRDH リキッド | `crdh-liquid-ja` | `compound_crdh` | `product_liquid` | active（存在） |
| CRDP リキッド | `crdp-liquid-ja` | `compound_crdp` | `product_liquid` | active（存在） |
| H4CBH リキッド | `h4cbh-liquid-ja` | `compound_h4cbh` | `product_liquid` | active（存在） |
| HHBD リキッド | `hhbd-liquid-ja` | `compound_hhbd` | `product_liquid` | active（存在） |
| HHCH リキッド | `hhch-liquid-ja` | `compound_hhch` | `product_liquid` | active（存在） |

参考: `comparison-5y-setA..D` は bare 化合物の比較セットであり、リキッド比較セットではない。
既存 plan `datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-recollect-*.json` は
すべて `*-general-ja`（bare）用であり、リキッド用 plan は存在しない。

## 収集仕様

option 1 は owner 承認済みで、下記の 8 plan を `datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-rikiddo-*.json` に作成し、各 1 run を収集した（結果は上記「実施」)。

- 共通フィールド（8 plan 共通）: `study_id = cannabinoid-raw-collection`、`source_id = google-trends`、
  `collector_id = google-trends-mcp`（`config/collectors.json` で `active` の唯一の collector）、
  `query.geo = JP`、`query.timeframe = today 5-y`、
  `required_capabilities = ["geo_filter", "relative_date_range"]`（既存 plan と同一）、
  `window.window_id = 2021-10-17_2026-10-18`（`metadata/windows/2021-10-17_2026-10-18.json` に登録済み:
  `start 2021-10-17T00:00:00Z` / `end_exclusive 2026-10-18T00:00:00Z` / `granularity week` /
  `week_start sunday` / `timezone Asia/Tokyo`）。
- 窓の注意: 現在収集すると窓は `2021-10-17_2026-10-18` となり、既存 main5 の観測範囲
  `2021-10-10 .. 2026-10-11` とは約 1 週ずれる。**別窓の別観測**であり、単純な追補ではない。
  各単独系列はピーク=100 正規化のため 8 語と main5 の 5 語を直接比較できない。
  化合物間比較には common-scale 収集が別途必要（bare 化合物分は ISS-20261023-GT-009 の
  `gt-5y-common-scale-setA..D` が担当。リキッド common-scale は本 issue の範囲外）。
- `run_id` 規約: `<収集時刻>Z-google-trends-ja-rikiddo-5y-<slug>`（1 語 1 run。
  例: `20261023T185238Z-google-trends-ja-rikiddo-5y-thcv`。時刻部分は実行時に確定するため plan には書かない）。
- `google-trends-mcp` は npm パッケージ v0.1.1 で API キー不要
  （`docs/provenance/collector-inventory.md`: 「API キー不要」、`config/collectors.json` の evidence 同旨）。
- 8 plan の差分は `plan_id` / `query_id` / `query.text` / `query.compound_id` のみ。代表 1 件の全文と残り 7 件の差分表を下記に示す。

代表例（`THCV リキッド`。ファイル名案 `gt-5y-rikiddo-thcv.json`）:

```json
{
  "plan_id": "gt-5y-rikiddo-thcv",
  "study_id": "cannabinoid-raw-collection",
  "source_id": "google-trends",
  "collector_id": "google-trends-mcp",
  "query_id": "thcv-liquid-ja",
  "query": {
    "text": "THCV リキッド",
    "geo": "JP",
    "timeframe": "today 5-y",
    "compound_id": "compound_thcv"
  },
  "required_capabilities": ["geo_filter", "relative_date_range"],
  "window": {
    "window_id": "2021-10-17_2026-10-18",
    "start": "2021-10-17T00:00:00Z",
    "end_exclusive": "2026-10-18T00:00:00Z",
    "granularity": "week",
    "week_start": "sunday",
    "timezone": "Asia/Tokyo"
  },
  "purpose": "5年リキッド系列の新規収集（THCV リキッド）。ISS-20261023-GT-008 option 1。main5 に含まれない 8 語のうちの 1 語。別窓（2021-10-17_2026-10-18）の別観測として記録する。"
}
```

残り 7 件（共通部は代表例と同一。`plan_id` は `gt-5y-rikiddo-<slug>`）:

| `plan_id` 案 | `query_id` | `query.text` | `query.compound_id` |
|---|---|---|---|
| `gt-5y-rikiddo-thco` | `thc-o-liquid-ja` | `THC-O リキッド` | `compound_thc_o` |
| `gt-5y-rikiddo-thch` | `thch-liquid-ja` | `THCH リキッド` | `compound_thch` |
| `gt-5y-rikiddo-crdh` | `crdh-liquid-ja` | `CRDH リキッド` | `compound_crdh` |
| `gt-5y-rikiddo-crdp` | `crdp-liquid-ja` | `CRDP リキッド` | `compound_crdp` |
| `gt-5y-rikiddo-h4cbh` | `h4cbh-liquid-ja` | `H4CBH リキッド` | `compound_h4cbh` |
| `gt-5y-rikiddo-hhbd` | `hhbd-liquid-ja` | `HHBD リキッド` | `compound_hhbd` |
| `gt-5y-rikiddo-hhch` | `hhch-liquid-ja` | `HHCH リキッド` | `compound_hhch` |

`purpose` の文面は各語のクエリ文に読み替える（例: 「（THC-O リキッド）。… 8 語のうちの 1 語。」）。

## 選択肢（定量化）

1. **8 語を 5年で収集する**: 上記 8 plan を新規収集し、5年リキッドを 13/13 にする。
   結果は空系列の可能性もある（特に 12ヶ月でも空の 4 語）。別窓・別正規化のため main5 の 5 語と直接比較はできない。
   新規収集のため owner 承認が必要。
2. **5 語を意図的な範囲として methodology / README に明記する**: 収集しない。
   5年カバレッジは 5/13 のまま。文書案（適用せず、案のみ）:
   「5年の ○○リキッド系列は CBD / CBG / CBN / HHC / THC リキッドの 5 語のみを収録する
   （`20261012T064246Z-google-trends-ja-rikiddo-5y-main5`、観測範囲 2021-10-10 .. 2026-10-11）。
   THCV / THC-O / THCH / H4CBH / HHBD / HHCH / CRDP / CRDH リキッドの 5年系列は未収集であり、
   12ヶ月の有無から 5年の有無を推定しない。」
3. **12ヶ月で系列がある 4 語（H4CBH / HHBD / HHCH / THCH リキッド）だけ先行収集する**:
   上記 8 plan のうち該当 4 件のみ実施。命中期待は高いが保証はなく、カバレッジは 9/13 になる。
   残り 4 語の方針は別途必要。

補足:

- main5 は legacy 形状（`payload.json` 無し、`metadata/windows/` の窓を持たない）。新規 run は現行 pipeline 形状で作る。
- CBX リキッド 5年を含めるかは本 issue の範囲外（CBX study 側の判断）。

## 検証コマンド（実施済み、読取のみ）

```sh
PYTHONPATH=src python3 -m json.tool datasets/cannabinoid-raw-collection/data/raw/google_trends/20261012T064246Z-google-trends-ja-rikiddo-5y-main5/run_metadata.json
PYTHONPATH=src python3 - <<'EOF'
import json, glob
# main5: 各 records_*.json の len / 平均 / 非ゼロ週 / 範囲
# phase-a / repeat / phase-b: 各 records_*.json の len / 非ゼロ週 / 範囲 + run_metadata.json の zero_status
# repo 全体: datasets/*/data/raw/**/*.json の keyword+timeframe 走査（today 5-y + リキッドは main5 の 5 件のみ）
EOF
grep -rl "リキッド" datasets/cbx-search-trends/data/raw --include="*.json"
PYTHONPATH=src python3 -c "import json; print([q['query_id'] for q in json.load(open('metadata/queries/query-registry.json'))['queries'] if 'liquid' in q['query_id']])"
```

## 完了条件

- [x] 方針の決定（owner）: option 1（8 語を 5年で収集、2026-10-24）
- [x] 決定に応じた実施（8 語の収集 run: 7 語が系列あり、THC-O は系列なしとして記録）
- [x] `README.md` のキーワード表の「未収集」注記が解消（または恒久的な範囲注記になる）

## owner への決定依頼

以下を owner が決定すること。agent は承認なしに収集・文書編集を行わない。

1. option 1（8 語収集）/ option 2（5 語を範囲として明記）/ option 3（4 語先行）のいずれを選ぶか。
2. option 1 / 3 を選ぶ場合: 上記 plan 案（窓 `2021-10-17_2026-10-18`、別窓の別観測になること）を承認するか。
   承認する場合は収集の実行指示を別途出すこと（本 issue の更新は収集の承認ではない）。
3. option 2 を選ぶ場合: 上記文書案の文面で `methodology.md` / `README.md` に記載してよいか
   （記載作業自体は本 issue の完了条件であり、別途指示が必要）。
