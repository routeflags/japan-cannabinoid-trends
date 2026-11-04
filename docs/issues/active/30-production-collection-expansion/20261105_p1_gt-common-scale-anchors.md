# Issue: 共通スケール比較のアンカー（CBD/THC）が必須化されておらず、THCNM の 5年比較が未被覆

**ID:** ISS-20261105-GT-030  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/metadata/query-design.json`,
`datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-common-scale-thcnm.json`,
`metadata/queries/query-registry.json`,
`src/validation/comparison_scale.py`,
`src/validation/gates.py`,
`docs/specs/gt-boundary-verification.md` §8  
**GitHub:** 未起票（ローカル記録。起票時にこの行へ追記する）

## 概要

Google Trends の単独系列は各語のピーク=100 に正規化されるため、化合物間で値を
比べられない。比較できるのは 1 回の `compare_terms` で測った共通スケールだけで、
その要求に study のアンカー（この study は CBD と THC）が**同一リクエスト**に
含まれることが条件である。

5年の共通スケール setA〜D は CBD/THC を含んでいたが、この規則は plan / 収集前
ゲート / 採用ゲート / 監査のどこにも宣言・強制されていなかった。したがって:

- アンカーの無い `compare_terms` plan も、宣言の無い複数語 plan も通れた。
- 単独系列 run を共通スケールと誤認しても、機械的に止まらなかった。
- 新しい化合物 THCNM は 5年の単独系列しか持たず、アンカー付き common-scale run が
  無いまま被覆表から抜け落ちていた。

## 実測（読み取り専用、2026-11-05）

| 観測 | 値 | 証拠 |
|---|---|---|
| 5年 common-scale run | 4（setA〜D）。すべて CBD/THC を含む | `data/raw/google_trends/20261023T1717*-5y-common-scale-set*/run_metadata.json` |
| setA〜D の窓・語数 | `2021-10-17_2026-10-18`、各 262 週 | 同上の `temporal_provenance` と `comparison_*.json` |
| THCNM の 5年 common-scale run | **0** | 上記 4 run に THCNM が無い |
| THCNM の 5年単独系列 | 1（`20261104T115431Z-google-trends-thcnm-5y`） | 単独正規化であり化合物間比較に使えない |
| 12ヶ月の legacy comparison sets | `common-scale-expansion` setB/setD と `common-scale-missing` は CBD/THC を含まない | `comparison_set{B,C,D}.json` / `comparison.json` の `terms` |
| 宣言前の 5年 comparison run | 4（setA〜D） | `comparison` ブロックが無い（legacy） |

監査コマンド（この変更後）:

```bash
make audit-comparison-scale
# => policy gt-5y-common-scale-cbd-thc anchors=CBD,THC runs=59 compliant=0 ...
#    missing compound: cbd-general-ja ... thcnm-general-ja（現行窓の被覆が無い）
#    legacy missing anchor set: 20261005T100000Z-google-trends-common-scale-expansion ...
#    out of scope: 20261023T171700Z-google-trends-5y-common-scale-setA (legacy_out_of_scope; window=2021-10-17_2026-10-18)
#    not comparable: 20261012T054920Z-google-trends-notation-presurvey (legacy_unknown)
```

## 新規則（この変更で宣言・強制）

1. **宣言（正本）**: `datasets/cannabinoid-raw-collection/metadata/query-design.json` の
   `comparison_scales` にポリシー `gt-5y-common-scale-cbd-thc` を追加。anchor query
   `cbd-general-ja` / `thc-general-ja`、anchor term `CBD` / `THC`、request
   `compare_terms` / `geo=JP` / `locale=ja` / `today 5-y`、window
   `2021-10-31_2026-11-08`（owner 決定 B。旧窓 `2021-10-17_2026-10-18` の setA〜D は
   legacy として残す）。必須化合物集合は query registry の active
   `compound_general` を権威とし、除外は `excluded_compound_ids` に理由付きで記録
   （CBX は `ISS-20261024-COL-016` の決定まで除外）。
2. **plan**: `collection-plan-v1` に任意の `comparison` ブロック
   （`comparison_scale` / `policy_id` / `anchor_query_ids` / `anchor_terms` /
   `locale` 等）を追加。
3. **収集前ゲート**: `gate-plan` は common-scale plan で
   - 両アンカーが同一 `compare_terms` 要求に無い、
   - anchor query が未登録、または canonical_text が anchor_terms に無い、
   - geo / timeframe / window / locale がポリシーと一致しない、
   - 複数語なのに宣言が無い
   場合に **stop**（fail closed）。単独系列 plan は許可し、run に
   `single_series` / `cross_compound_comparable: false` を記録する。
4. **収集後 / 採用ゲート**: L1 は、宣言済み run の request と comparison artifact の
   両方にアンカーがあり、window / request metadata が一致することを検証する。
   宣言の無い comparison-shaped run は warning（legacy）とし、raw は変更しない。
5. **監査**: `audit-comparison-scale` がポリシーごとの missing anchor sets /
   compound coverage を報告する。比較に使えない run は `not_comparable_runs`、
   要求条件がポリシーの外にある run は `out_of_scope_runs`、宣言前だがアンカーが
   揃う run は `legacy_undeclared_runs` に分ける。`--require-complete` で
   missing compound を exit 1 にする。`make gates GATE=comparison` は宣言だけを
   検証する。
6. **THCNM**: `metadata/plans/gt-5y-common-scale-thcnm.json`（CBD + THC + THCNM、
   現行窓・geo JP・locale ja）と query registry の `comparison-thcnm-anchored` を追加
   （query id は語の集合と意図を登録し timeframe は登録しないため、5年・12ヶ月・3ヶ月の
   アンカー付き計画が同じ id を共有する。旧 `comparison-5y-thcnm` はどの run も参照する
   前に改名した）。
   現行窓の setD（`comparison-5y-current-setD` = CBD + THC + HHCH + THC-O + THCNM）も
   THCNM を含む。どちらかを採用すれば THCNM の被覆は `complete` になる（他 13
   化合物は別 run の採用が必要）。

## legacy の扱い

- 5年 setA〜D（旧窓 `2021-10-17_2026-10-18`）は CBD/THC を含むが、ポリシーの
  現行窓の外にあるため `legacy_out_of_scope`。raw は書き換えず、新規準拠とも
  現行窓の被覆とも扱わない。共通スケールとしては有効なので `not_comparable_runs`
  には入れず、`out_of_scope_runs` として別に報告する。
  現行窓の再収集計画 `metadata/plans/gt-5y-common-scale-current-set{A..D}.json` は
  plan ゲートで `PROCEED` だが、未収集なので被覆には数えない。
- その結果、現行窓の被覆は 0/14。監査は必須 14 化合物を `missing` と報告する
  （旧窓の被覆では代替しない）。
- 12ヶ月の legacy comparison sets は 5年ポリシーの範囲外（`legacy_out_of_scope`）だが、
  アンカー欠落は `legacy_missing_anchor_sets` に残す。12ヶ月を同じ規則で扱うには
  別の `comparison_scales` ポリシーが必要（この issue の範囲外）。
- `docs/audits/` のスナップショットは再生成していない（partial checkout のため）。

## 現状の未被覆と blocker

- **現行窓 `2021-10-31_2026-11-08` の common-scale run は未収集**。計画は 5 本
  （`gt-5y-common-scale-current-set{A..D}` と `gt-5y-common-scale-thcnm`）とも
  `make gate-plan` で `PROCEED`。ライブ経路は `make collect ... --live`
  （`google-trends-mcp@0.1.1`）。
- MCP ツール列挙は 2026-11-04T17:20:57Z に成功している（`interest_over_time` /
  `compare_terms` / `related_queries` を公開。レポート
  `.staging/tooling_logs/google_trends/20261104T172057Z-gt-probe/report.json`）。
  ただし観測の取得は行っていない。`gt-boundary-verification` §4 によりライブ収集は
  メンテナの承認後に限るため、この変更では実行していない。したがって THCNM は
  5年ポリシーでは missing のまま。
- 2026-11-04、オーナーの依頼で 12ヶ月と 3ヶ月のアンカー付き run を `make collect
  --live` で採用した（`20261104T175032Z-google-trends-cannabinoid-raw-collection`、
  `20261104T175220Z-google-trends-cannabinoid-raw-collection`）。両方とも L1 は
  CATALOG、`audit-comparison-scale` は `compliant`。12ヶ月の THCNM は全週 0（窓内最大
  値が CBD の 2026-05 の週 = 100 のため）。3ヶ月は 2026-10-21 以降に 1、2026-08-13 に
  孤立した 12 を返した。5年の現行窓（setA〜D / THCNM）は未収集。
- 収集・採用後に `make audit-comparison-scale ARGS=--require-complete` が
  exit 0（CLI）になることを完了条件とする。

## 完了条件

- [x] study の `comparison_scales` 宣言と plan / run の `comparison` ブロック
- [x] 収集前・収集後ゲートと監査コマンド（テスト付き）
- [x] THCNM の common-scale plan / query registry 登録
- [x] 現行窓再収集計画 setA〜D の登録と plan ゲート通過
- [ ] 現行窓 common-scale run（setA〜D / THCNM）の収集・採用
- [ ] `make audit-comparison-scale ARGS=--require-complete` が exit 0
- [x] 12ヶ月 / 3ヶ月 comparison sets を同じ規則に載せる（別ポリシー
  `gt-12m-common-scale-cbd-thc` / `gt-3m-common-scale-cbd-thc`、owner 決定
  2026-11-04）
- [ ] 12ヶ月・3ヶ月とも THCNM 以外の化合物は未被覆（監査が missing として報告）

## 検証コマンド

```bash
make gates GATE=registries
make gates GATE=comparison
make gate-plan PLAN=datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-common-scale-thcnm.json
make gate-plan PLAN=datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-common-scale-current-setA.json
make audit-comparison-scale
make audit-comparison-scale ARGS=--require-complete   # 現行窓 run の採用まで exit 1
python3 -m pytest -q tests/validation/test_comparison_scale.py
```

## 関連

- `ISS-20261023-GT-009`（5年 common-scale setA〜D の収集）
- `ISS-20261024-GT-012`（5年の製品語 common-scale が無い）
- `ISS-20261024-COL-016`（CBX を対象集合に含めるか）
- `docs/specs/gt-boundary-verification.md` §8（アンカー規則）
- `docs/specs/collection-pipeline.md` §3.5（plan / run の `comparison` ブロック）
