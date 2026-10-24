# Issue: CBX を cannabinoid-raw-collection の対象に含める（13 → 14 化合物）

**ID:** ISS-20261024-COL-016  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/README.md`（概要・対象化合物・キーワード表）,
`methodology.md` §1.3・§5.1・§6, `metadata/studies/study-registry.json`,
`datasets/cannabinoid-platform-trends/data/processed/`（既に CBX 行あり）,
`datasets/cbx-search-trends/`・`datasets/cbx-social-trends/`  
**GitHub:** [#13](https://github.com/routeflags/japan-cannabinoid-trends/issues/13)

## 概要

`cannabinoid-raw-collection` は現在 **「CBX を除く 13 化合物」**を対象とし、CBX は
[`datasets/cbx-search-trends/`](../cbx-search-trends/)（検索需要）と
[`datasets/cbx-social-trends/`](../cbx-social-trends/)（SNS）が担当すると明記している。
CBX を本 study の対象に含める（**14 化合物**にする）方針への変更依頼。

**ただし配布層は既に CBX を 14 番目の化合物として扱っている。** 本 issue は、その不一致を解消する方向で
対象範囲を決めるための記録である。

## 実測（2026-10-24）

| 層 | CBX の扱い | 根拠 |
|---|---|---|
| 本 study の文書 | **対象外**（13 化合物） | `README.md:14`（「CBX を除く 13 化合物」）、`README.md:48`、`methodology.md` §1.3・§6 |
| 本 study の raw | CBX の run は **0**（`data/raw/google_trends/` に CBX の単独系列が無い） | 64 run の走査 |
| 配布物 `trend_observations.csv` | **CBX 5 行あり**（`gt-cbx-*`、run `20261015T042857Z-google-trends-boundary-5y`） | 同 CSV |
| 配布物 `platform_coverage.csv` | **CBX 2 行あり**（google_trends = observed / youtube = not_collected） | 同 CSV |
| `docs/audits/gt-summary.json` | **14 化合物**（13 + CBX） | 同 JSON |
| taxonomy | `compound_cbx` は既に登録済み | `metadata/taxonomy/compound-taxonomy.skos.jsonld` |
| query registry | `cbx-general-ja` / `cbx-liquid-ja` / `cbx-cannabinoid-ja` / `cbx-cannabis-ja` | `metadata/queries/query-registry.json` |

CBX の既存観測（他 study の raw）:

- `cbx-search-trends` の GT raw 8 run。うち CBX 本体は `20261015T042845Z-*boundary-1m` /
  `-3m` / `-12m` / `-5y`（窓は `2026-09-15_2026-10-15` などの相対窓）と `20261001T115959Z-google-trends-cbx-rikiddo`
  （`CBX リキッド` 12ヶ月 + CBX 比較）、`20261001T135424Z-google-trends-variance-check`（CBX / H4CBH / HHBD / CBD リキッドの比較）。
- `cbx-social-trends` の SNS raw（X / Instagram / TikTok / YouTube）。YouTube の v3 由来 run は
  `ISS-20261024-PRV-005`（#1）の対象。
- **H4CBH と HHBD は既に両 study が収集している**（`20261001T121949Z-google-trends-h4cbh-hhbd`）。
  すなわち「1 化合物を 2 study が観測する」こと自体は前例がある。

## 何が問題か

1. **文書と配布物が矛盾している。** 本 study は CBX を対象外と書くが、その素材から作る配布物は CBX を 14 番目として出している。
   読み手は CBX の出所を本 study の raw だと思うが、実際は `cbx-search-trends` の raw である。
2. **観測の窓が揃っていない。** 本 study の 5年は `2021-10-10_2026-10-11` と `2021-10-17_2026-10-18` の 2 窓、
   CBX の 5年 run は `2021-10-15_2026-10-15`。**窓が違うので、CBX を 14 番目として横並びに比較できない。**
3. **共通スケールに CBX が入っていない。** 本 study の 5年共通スケール（§2.1.4 の setA〜D）はアンカー CBD/THC を含むが CBX を含まない。
   CBX を成分比較に載せるなら、CBX と CBD/THC を同じ run で測るセットが要る。
4. **重複収集の危険。** 何も決めずに「対象に含める」と、同じクエリを 2 study で別々に収集し、窓も設定も違う 2 系統の CBX 系列ができる。

## 選択肢

1. **本 study の対象に含める。観測は既存 raw を参照する（新規収集しない）** — 本 study の文書は CBX を 14 番目として扱い、
   raw の所在は `cbx-search-trends` / `cbx-social-trends` と明記する。窓・共通スケールの不一致は limitations として書く。
   raw は増えない。study をまたぐ参照を認める規則が必要。
2. **本 study で CBX を収集する（14 番目として独立に観測を持つ）** — 窓と共通スケールを 13 化合物と揃えられるが、
   同じ語を 2 study で収集することになり、既存の CBX raw との関係（置換か併存か）を決める必要がある。新規 raw が増える。
3. **両方**: 対象に含めて文書を 14 化合物に直し、成分比較に必要な run（CBX を含む共通スケール）だけを新規に追加収集する。
4. **現状維持（対象外のまま）** — 配布物が CBX を出している理由と、CBX の raw が他 study にあることを文書で明示する。

推奨は **3**。文書と配布物の不一致（問題 1）は選択肢 1 の部分で解消でき、
成分比較に必要な最小限（CBX + CBD/THC の共通スケール 1 本、CBX の 5年単独系列 1 本）だけを足せば問題 2・3 も解ける。

## 決定依頼

- **Q1**: 本 study の対象に CBX を含めるか（含めるなら 13 → 14）。含めない場合も、配布物が CBX を出している理由を文書に書く。
- **Q2**: 観測の取得元をどうするか（1: 既存 raw 参照 / 2: 本 study で収集 / 3: 併用）。
- **Q3**: 語彙はどれを 14 番目の化合物語・製品語にするか。`CBX`（`cbx-general-ja`）を化合物語とし、
  `CBX リキッド`（`cbx-liquid-ja`）を製品語に加えるのか、現行の「アンカー語（対象外）」のまま残すのか。
- **Q4**: 窓を揃えるか。揃えるなら CBX の 5年系列を取り直す（新規収集）か、揃わないことを limitations に書くか。
- **Q5**: `cbx-search-trends` / `cbx-social-trends` との役割分担をどう書き換えるか（統合・併存・参照のどれか）。

## 完了条件

- [ ] Q1〜Q5 の回答
- [ ] `README.md`（概要・対象化合物表・キーワード表）と `methodology.md`（§1.3・§5.1・§6）が 14 化合物として一貫している
- [ ] CBX の観測がどの raw にあるかを文書から辿れる（参照方式ならパスを明記）
- [ ] 窓・共通スケールの不一致が limitations に書かれている（または揃える run を収集した）
- [ ] 配布物（`trend_observations.csv` / `platform_coverage.csv` / `gt-summary.json`）の CBX 行の出所が文書と一致している
- [ ] 監査スナップショットの再生成
