# Issue: 5年の共通スケールに製品語が無い（リキッド・オイルの5年比較が成立しない）

**ID:** ISS-20261024-GT-012  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/google_trends/`（新規 `compare_terms` run）,
`metadata/queries/query-registry.json`, `metadata/plans/`,
`datasets/cannabinoid-raw-collection/README.md` のキーワード表, `methodology.md` §2.1.4  
**GitHub:** [#9](https://github.com/routeflags/japan-cannabinoid-trends/issues/9)

## 概要

5年の共通スケール（`compare_terms`）は**化合物語 13 語の 4 セット（setA〜D）だけ**で、**製品語（`○○ リキッド` / `○○ オイル`）のセットが 1 本も無い**。
5年の製品語は単独系列しかなく、各 run が自分のピーク=100 に正規化されるため、**製品軸の化合物間比較は 5 年では成立しない**。
12ヶ月は製品語の共通スケールがあるので、欠けているのは 5 年だけである。

## 実測（2026-10-24、収集なし）

| 観測 | 値 | 証拠 |
|---|---:|---|
| 5年の共通スケール run | 4（setA〜D）。語は化合物語 13 語のみ | `data/raw/google_trends/20261023T1717*-5y-common-scale-set*/run_metadata.json` の `query_provenance.submitted_query` |
| 5年の製品語の共通スケール run | **0** | 上の 4 run に製品語が 1 語も無い |
| 5年のリキッド単独系列 | 12 語（main5 の 5 語 + 新規 7 語）。`THC-O リキッド` は系列なし | `20261012T064246Z-google-trends-ja-rikiddo-5y-main5`（`records_{cbd,thc,cbg,cbn,hhc}-rikiddo-5y.json`）、`20261023T1852*`/`1853*`（7 run） |
| 5年のオイル | 0 run | `オイル` を含む raw は `20261012T054920Z-google-trends-notation-presurvey` のみ（比較の片側、単独系列は無い） |
| 12ヶ月のリキッド共通スケール | 4 セット（JA1〜JA4）+ 反復 1 本。アンカー `CBX リキッド` 3.0 / `CBD リキッド` 64.0 | `20261012T055259Z-...phase-a-12m`（JA1）、`20261012T060517Z-...phase-a-repeat-12m`（JA1 反復）、`20261012T061614Z-...phase-b-12m`（JA2/JA3/JA4） |
| 12ヶ月のオイル | 比較 1 本のみ（`CBD リキッド` vs `CBD オイル`） | `20261012T054920Z-...-notation-presurvey/comparison_notation.json` |
| 処理層の GT 製品語行 | 0（GT 70 行はすべて化合物語） | `datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv` |

検証コマンド（`PYTHONPATH=src python3`、`.venv` 不使用）:

```bash
# 5年の共通スケール run の語（4 run とも化合物語のみ）
python3 - <<'EOF'
import json,glob
for f in sorted(glob.glob('datasets/*/data/raw/google_trends/*-5y-common-scale-set*/run_metadata.json')):
    print(json.load(open(f))['query_provenance']['submitted_query'])
EOF

# 処理層の GT 行（70 行）に製品語が無いこと
grep -c 'google_trends' datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv
grep '^gt-' datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv | grep -c 'リキッド\|オイル'  # 0
```

- 5年共通スケールの窓は `2021-10-17_2026-10-18`（262 週）。アンカー CBD 33 / THC 5 が 4 セットで一致するため、セット間の橋渡しが成立している（`ISS-20261023-GT-009`）。
- 12ヶ月の製品語セットは `CBX リキッド`（CBX study の語）をアンカーにしており、5年の化合物語セット（CBD/THC アンカー）とは語集合が違う。**12ヶ月と 5 年を同じ表に並べるには、どちらのアンカー構成を採るかの決定が要る。**

## 何が問題か

1. `README.md` のキーワード表は「Google Trends / 5年の共通スケール（`compare_terms`）/ 製品語: なし」と書いており、製品軸は 5 年で比較できない状態が続いている。
2. `methodology.md` §2.1.4 は「化合物間比較はこの共通スケール内でのみ行う」と定めるが、製品語にはそのスケールが存在しない。定めと実データがずれている。
3. 単独系列の平均を製品語間で横並びにすると誤読を招く（`metric_dictionary.csv` の limitations で禁止済み）。データ側の受け皿が無いのが原因で、文書の注記だけでは解消しない。

## 選択肢（owner 判断。新規 raw を増やすので承認が前提）

1. **12ヶ月セットと同型でリキッド 13 語を 4 セット取得** — アンカー `CBX リキッド` + `CBD リキッド`、各セット 2 アンカー + 3 語（`MAX_COMPARE_TERMS = 5`）。12ヶ月の語割り当て（JA1〜JA4）をそのまま 5 年に写せる。窓は `2021-10-17_2026-10-18`。オイルは打たない（`ISS-20261023-YT-011` のリキッド統一と整合）。
2. **化合物セット setA〜D と同型** — アンカー `CBD リキッド` + `THC リキッド`。化合物軸と同じ語割り当てになり読み比べやすいが、12ヶ月のセットとは語集合が一致せず、12ヶ月と 5 年を同じ表に並べられない。
3. **1 または 2 に混在セットを 1 本追加** — 例 `CBD`, `THC`, `CBD リキッド`, `THC リキッド`。化合物語と製品語の比が測れるが、1 つの比較に別種の語を載せる意味を methodology に明記する必要がある。
4. **オイルも含める** — 5年のオイルは 0 run。`THC オイル` は query registry 未登録（`cbd-oil-ja` のみ）。`ISS-20261023-YT-011` のリキッド統一と方針が割れる。
5. **打たない** — 5年の製品語は単独系列のみと README・methodology に明記し、製品軸の 5 年比較は行わない。コード変更なしで今日から実施できる。

推奨は 1。12ヶ月と同じアンカー・語割り当てで、既存 4 セットの構成をそのまま使い回せる。3 は必要になった時点で追加、5 を選ぶ場合は README のキーワード表と §2.1.4 の明記だけで足りる。

## 決定依頼

- D1: アンカーの構成（選択肢 1 / 2 / 3）
- D2: オイルを 5 年 GT で打つか（`ISS-20261023-YT-011` と整合させるか）
- D3: 12ヶ月の製品語セットを同じアンカーで測り直すか
- D4: 処理層（`trend_observations.csv` / `metric_dictionary.csv`）に GT 製品語を載せるか

## 実行準備（決定後に効く制約）

- 経路は既存 setA〜D と同じ。`make collect ARGS=… --live`（adapter `google-trends-mcp@0.1.1`、tool `compare_terms`、`collection_mode: live`、`transport: mcp`）。`netloom google-trends compare-terms` は探索用で、応答 envelope が pipeline の MCP verbatim 形状と違うため run 作成には使わない（`.github/skills/research-google-trends/SKILL.md`）。API キーは不要（Node/npx で起動）。
- `compare_terms` は 2〜5 語（`src/collection/adapters/google_trends/adapter.py:45` の `MAX_COMPARE_TERMS`）。5 語上限がセット分割の理由。
- 窓は `2021-10-17_2026-10-18` に揃える。`today 5-y` は相対指定なので `temporal_provenance.exact_window_match` は `false` になる（setA〜D と同じ既知の制約）。
- run-id は既存規約 `<UTC>Z-google-trends-5y-common-scale-<セット名>` を継ぐ。
- query registry は化合物セット用の `comparison-5y-setA..D` だけなので、製品語セット用の id 追加が要る（`query_provenance.query_id` が registry を参照する）。
- 計画書は `metadata/plans/gt-5y-common-scale-set{A..D}.json` と同じ形式で用意する（既存 4 本の `terms` / `geo` / `timeframe` / `window_id` を写す）。
- 受け入れ検証は `ISS-20261023-GT-009` と同じ形にする: アンカー（`CBD リキッド`）の平均と週次系列が 4 セットで一致し、各セットの語が共通スケールに載ること。

## 完了条件

- [ ] 方針の決定（owner、D1〜D4）
- [ ] 選んだ構成の収集と、アンカー週次一致の独立検証
- [ ] `README.md` のキーワード表と `methodology.md` §2.1.4 が実データと一致している（打たない選択なら「5年の製品語比較は不可」の明記）
- [ ] 処理層に載せる場合の `src/processing/platform_trends.py` と `metric_dictionary.csv` の更新
- [ ] 監査スナップショットの再生成
