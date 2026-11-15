# Issue: 辞書全体の形式精度の標準化 — 形式辞書・検索語 crosswalk・未登録候補の分離

**ID:** ISS-20261115-TAX-044
**優先度:** P1 (High)
**ステータス:** OPEN
**実装状態:** 文書変更はローカル scope-split commit 済み。owner review pending、未push。
**対象:** `datasets/cannabinoid-raw-collection/README.md`（構造形式辞書・検索語 crosswalk・未登録候補・term-to-query map）、
`docs/provenance/compound-taxonomy.md`（本変更の節）、`docs/provenance/query-inventory.md`（台帳の対象範囲）、
`tests/validation/test_dictionary_form_precision.py`（新規）、`docs/audits/g6-git-tracking-inventory.json`（README ハッシュのみ）
**関連:** `ISS-20261111-TAX-040`（管理カテゴリと owner 確認の範囲）、`ISS-20261111-TAX-041`（THCA / THCB の 6 個別トピック）、
`ISS-20261111-TAX-042`（異性体別根拠レビュー）、`ISS-20261115-TAX-043`（外部識別子 crosswalk と THCV / CBDV の粒度）

## 概要

2026-11-15、owner は study の辞書全体に対し、次の精度基準を一貫して適用することを指示した。

- 各辞書項目は、証拠が支える**個別の構造形式**を表す。位置異性体（Δ8 / Δ9、A / B）、酸／中性／エステル、立体化学は、
  出所が支える粒度までしか区別しない。
- 総称語・ファミリー語・市場語は、個別形式と混ぜない。
- 証拠が形式を支えていても owner が登録語として列挙していないものは、**未登録・未収集の候補**として明示し、
  run や化学的に同定された検索結果があるように見せない。
- 既存の raw run と query / run の割当てを保持し、総称語の履歴を個別形式へ再配分しない。

**本 issue の範囲は文書・台帳・検証だけである。** taxonomy の概念追加・分類変更、query の追加・変更、raw / catalog / 被覆状態の変更、
収集・採用・公開・release は行っていない。変更は TAX-043 と TAX-045 を分けたローカル commit に記録済みで、owner review は pending、push は未実施。

### 以前の README 再編との関係（誤読防止）

README の再編時に「README だけの変更では THC を registry で分割しない」とされた判断は、**その README 変更の範囲**の決定であり、
THC の科学的な恒久判断ではない。本 issue はそれを恒久判断として扱わない。同時に、本 issue も **`THC` を registry で分割しない**。
`THC` は総称文字列の登録のままで、Δ8-THC は登録済み形式ではなく未登録候補である。query ID・run の追加や再割当ても行わない。

## 決定したこと

1. **三つの軸を分離した。** 検索語（登録文字列）／構造形式（位置異性体・酸中性エステル・立体化学）／被覆状態（adopted run の有無）。
   形式と被覆は同じ表の同じ列に置かない。
2. **形式辞書は形式ごとに 1 行。** 登録 36 トピックのうち、概念が個別形式を表す 14 形式（検証済み 9 + owner 命名 5）を
   `構造形式辞書` に置いた。異性体未指定のファミリー（`THCP` / `THCJD` / `THCPO` / `THCB-O-acetate`）と `THCV` / `THCH`、市場語・未確認語は
   形式辞書に置かず、crosswalk で family または「未解決」とした。
3. **crosswalk は語ごとに 1 行（36 行）。** `検索語の範囲` を `個別形式` / `異性体未指定` / `総称リテラル` / `市場・供給元語` /
   `未確認リテラル` の 5 値で記録した。`異性体未指定` は検索語が位置異性体を区別しない場合を指し、立体化学の未指定は構造形式辞書で別記する。`対応する構造形式` が確定しない場合は「未解決」と明記した。
4. **未登録候補を別表にした（27 行）。** 主な証拠は TAX-042 / TAX-043 のレビュー記録、命名標準・知識グラフ、`research/regulatory-status/THCH.md`、HHC の WHO 47th ECDD (2024) §2C と PubChem record である。`Δ8-THC` / `Δ8-THCV` は命名標準・規制資料も参照する。
   登録・query ID・run は無く、`未登録・query なし・run なし（未収集）` を各形式に付し、既存系列を帰属させないと明記した。
5. **被覆表から同一性の列を外した。** term-to-query map は concept・query・被覆だけを持ち、形式・分類は辞書を参照する。

## 変更した層

- `datasets/cannabinoid-raw-collection/README.md`
  - 「概要」を四層（構造形式辞書 / crosswalk / term-to-query map / coverage）に更新。
  - `#### 構造形式辞書 — 概念が表す形式` を新設（14 行）。
  - `#### 検索語 → 構造形式の crosswalk（登録 36 トピック）` を新設（36 行、5 値の語の範囲）。
  - `#### 未登録・未収集の候補形式` を新設（27 行）。THC の他の位置異性体 5 形式、THCH の Δ8/Δ9、HHC の 9(R)/9(S) エピマーと他の 6 立体異性体を各 1 行で列挙し、
    証拠の種類（法令の構造グループ / 命名標準・知識グラフ / registry record / WHO レビュー / 製品分析）と限界を明記。
  - `#### 辞書全体の注記` を既存の注記から再構成し、THCV の未決を追加。
  - `### 登録済みキーワードと収集状態` の表から `skos:broader` 列を外し、被覆だけの表にした（行の語・concept・query ID・被覆状態は不変）。
  - 「関連」に TAX-043 / TAX-044 を追加。
- `docs/provenance/compound-taxonomy.md`: 本変更の節（決定・候補の根拠・変更しない層・未決）を追加。
- `docs/provenance/query-inventory.md`: 台帳が登録済み query だけを対象とし、未登録候補形式は query を持たないことを 1 文で明記。
- `tests/validation/test_dictionary_form_precision.py`: 次の点を固定。
  - crosswalk が registry の 36 concept を 1 回ずつ持ち、語が当該 concept の general canonical text と一致する（`THCNM（別名 THA）` の表示注記は `THCNM` と照合）。
  - 総称・ファミリー・市場語の crosswalk 行が個別形式を主張しない（`未解決` または `異性体未指定`）。
  - 形式辞書が owner 命名の未確認形式を「未確認」として保持する。
  - 候補表が 27 行で、`CANDIDATE_FORMS` の各形式を 1 回ずつ持ち、registry の canonical_text にも taxonomy の prefLabel にも一致しない（登録済みに見せない）。
  - 候補形式が形式辞書の登録形式と重複せず、`Δ9-THC` は形式辞書、`Δ8-THC` と他の THC 位置異性体は候補表にだけ現れる。
  - 各行が「未登録」「run なし」「未収集」を持ち、query ID を持たない。
  - アセテート・THCH・HHC の行が、法令の構造グループ / WHO レビュー / registry record / 製品分析を区別し、製品同定が無い場合は「未確認」と書く。
  - 被覆表が形式・同一性の列を持たず、concept ごとの general / liquid query を列挙する。
- `docs/audits/g6-git-tracking-inventory.json`: README と TAX-045 でも変更した 4 ファイルの tracked SHA-256 を更新した。後続の収集監査（`ISS-20261115-COL-034`）では checkout-local の `state_summary` / `extras` もその checkout の記録として更新された。これらの値は checkout 間で比較しない。

## 候補形式（27 候補）と根拠の範囲

| 親の登録語 | 候補形式 | 根拠の状態 |
|---|---|---|
| `THCP` | `Δ8-THCP` / `Δ9-THCP` | 両形式とも registry record あり。Δ9 は植物からの単離、Δ8 は 2026 年の製品検出（TAX-042） |
| `THCJD` | `Δ8-THCJD` / `Δ9-THCJD` | 両形式とも registry record あり。国内流通製品から NMR 同定（TAX-042） |
| `THCPO` | `Δ8-THCP-O-acetate` / `Δ9-THCP-O-acetate` | 両形式とも令和6年厚生労働省令第81号の別添に構造グループとして列挙。Δ9 は製品同定あり（Tanaka et al. 2025）。Δ8 は法令の構造グループ該当のみで、製品同定は未確認（TAX-042） |
| `THCB-O-acetate` | `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` | 両形式とも令和6年厚生労働省令第81号の別添に列挙。製品中の分析同定は未確認。Tanaka et al. 2025 の `Δ9-THCB-O-butanoate` は別エステルで、本行に含めない（TAX-042） |
| `THC` | `Δ8-THC` | 命名標準の位置異性体（`docs/specs/thc-nomenclature-standard.md` の 7 分類）。2024 年厚生労働省令は Δ9 系列（6a,7,8,10a-テトラヒドロ）と Δ8 系列（6a,7,10,10a-テトラヒドロ）を別の構造グループとして定義する（麻薬を除く）。知識グラフは CAS 5957-75-7 と天然存在 confirmed を記録するが、form-level の外部 record は taxonomy に未選択 |
| `THC` | `Δ6a(10a)-THC` / `Δ6a(7)-THC` / `Δ7-THC` / `Δ10-THC` / `Δ9(11)-THC` | 命名標準の 7 分類と `metadata/taxonomy/thc-regulatory-knowledge-graph.json`。知識グラフは規制区分「麻薬」・天然存在未確認を記録し、Δ10 のみ CAS 50554-36-6。他の 4 形式は form-level 外部識別子を未選択 |
| `THCV` | `Δ9-THCV` / `Δ8-THCV` | Δ9 は検証済み record あり。Δ8 は規制資料の列挙のみで registry record 未確認（TAX-043） |
| `THCJD`（C8） | `THCJD-O-acetate` | MHLW 資料（2024 年の指定薬物関連資料）に記載。法令の構造グループで、製品同定ではない。TAX-042 の 4 family レビュー対象外で、追加は owner 決定を要する |
| `THCH` | `Δ8-THCH` / `Δ9-THCH` | `research/regulatory-status/THCH.md` §1 が消費者庁資料に基づき Δ8/Δ9 を指定薬物の対象として記録（個別指定 2023-08-04、包括指定 2023-09-10）。法令の構造グループで、製品分析同定ではない |
| `HHC` | `9(R)-HHC` | PubChem CID 11067065 / CAS 36403-90-4、立体配置 (6aR,9R,10aR)。WHO 47th ECDD (2024) §2C が CBD 由来製品の主要エピマーの一つとして記録。特定製品の分析同定ではない |
| `HHC` | `9(S)-HHC` | PubChem CID 14378541 / CAS 36403-91-5、立体配置 (6aR,9S,10aR)。WHO 47th ECDD (2024) §2C が CBD 由来製品の主要エピマーの一つとして記録。特定製品の分析同定ではない |
| `HHC` | `(6aS,9S,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=S / 10a=S。(6aR,9R,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9R,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=R / 10a=S。(6aR,9S,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9S,10aR)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=S / 10a=R。(6aR,9R,10aS)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aS,9R,10aR)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=S / 9=R / 10a=R。(6aR,9S,10aS)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aR,9S,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=R / 9=S / 10a=S。(6aS,9R,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |
| `HHC` | `(6aR,9R,10aS)-HHC` | WHO 47th ECDD (2024) §2C が 8 立体異性体の一つとして図示。6a=R / 9=R / 10a=S。(6aS,9S,10aR)-HHC のエナンチオマー。個別 registry record・製品同定は未確認 |

これらは **family 概念の `skos:exactMatch` ではなく**、また登録候補の勧誘でもない。登録・query 化・収集には owner の明示決定を要する。

### 2026-11-15 追記 — 除外注記だった形式を候補表へ列挙

owner は、以前「列挙しない範囲」としていた THC の他の位置異性体 5 形式、THCH の Δ8/Δ9、HHC の立体異性体を、除外注記ではなく候補表の行として列挙するよう明示した。これを受けて、README の候補表に 27 行を列挙した。

- **THC の他の位置異性体**: 命名標準の 7 分類と知識グラフの規制記録を根拠とする。厚労省統制物質一覧への記載は法令・規制の記録であり、製品中の分析同定ではない。Δ10 の CAS 50554-36-6 は知識グラフの記録で、本変更では外部 record を再検証していない。
- **THCH の Δ8/Δ9**: `research/regulatory-status/THCH.md` が引用する消費者庁資料の構造グループの記録であり、製品分析同定ではない。form-level の外部識別子は選択していない。
- **HHC の立体異性体**: リポジトリ内の `research/regulatory-status/HHC.md` は HHC をグループ単位で記録し、立体配置を列挙しない。そこで WHO 47th ECDD (2024) の HHC critical review §2C と PubChem PUG REST を確認した。WHO は 8 立体異性体（4 対のエナンチオマー）を可能な配置として示し、CBD 由来製品の主要成分を (6aR,9R,10aR) と (6aR,9S,10aR) の 2 エピマーとする。PubChem は前者を CID 11067065（CAS 36403-90-4、InChIKey `XKRHRBJLCLXSGE-DJIMGWMZSA-N`）、後者を CID 14378541（CAS 36403-91-5、InChIKey `XKRHRBJLCLXSGE-USXIJHARSA-N`）として返した（2026-11-15 観測）。他の 6 配置も各 1 行で列挙し、各配置とエナンチオマー関係を明記した上で、個別 registry record・製品同定が無いことを記す。WHO の記述は review であり、本 study の製品分析ではない。
- **アセテート体の整理**: `Δ8-THCP-O-acetate` / `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` は法令の構造グループ該当、`Δ9-THCP-O-acetate` は法令該当に加えて文献の製品同定がある。`THCJD-O-acetate` は family の登録も Δ8/Δ9 の指定も無い。既存行は保持し、重複行は追加していない。

## 変更しないもの

- `metadata/taxonomy/compound-taxonomy.skos.jsonld`（概念・分類・label・`exactMatch`・scopeNote）と `exports/taxonomy/*`。
- `metadata/queries/query-registry.json` / `query-variants.json`（query ID・canonical_text・status・variant）。
- raw run、run metadata、catalog、declaration、被覆状態、収集計画、release slice、公開状態。
- `ISS-20261115-TAX-043` の crosswalk 修正、その evidence とテスト（`test_compound_identifier_crosswalk.py`）。
- P1（TAX-040）の経路／カテゴリ評価（`CBX`、`CRDH`、`CRDP`、`H4CBH`、`HHBD`、`HHCH`、`THCNM`、`THC-O`、`THCP`、`THCJD`、`THCPO`、
  THCA / THCB の 6 個別トピック等）。分類の変更は本 issue の対象外である。

## 未決事項

1. **`compound_thcv` の粒度**: Δ9 に狭めるか、Δ8/Δ9・立体化学未指定のままにするか。Δ9 の検証済み record は
   ChEBI 755032 / Wikidata Q76009679（立体化学定義あり）と Q254768（立体化学未指定）。owner 判断待ち（TAX-043）。
2. **`Δ8-THCA` の構造・命名の出所**: A/B のカルボキシル配置を確定する出所が無い。形式辞書では「部分指定」とした。
3. **Δ8 エステル体の分析証拠**: `Δ8-THCP-O-acetate` / `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` は法令の構造グループ該当のみで、
   製品中の同定を確認していない。`Δ8-THCP-O-acetate` を同定した文献は確認していない。
4. **`THCJD-O-acetate` の扱い**: MHLW 資料に記載されるが TAX-042 の 4 family に含めていない。登録する場合は owner の scope 決定を要する。
5. **`Δ8-THC` / `Δ8-THCV` の識別子**: `Δ8-THC` は知識グラフの CAS 5957-75-7 を候補表に記載したが、本変更で外部 record を再検証していない。`Δ8-THCV` は識別子を記載していない。
6. **列挙した候補の未解決点**: THC の他の位置異性体 5 形式は form-level 外部識別子を検証していない（Δ10 は知識グラフの CAS 50554-36-6 のみ）。
   THCH の Δ8/Δ9 は法令の構造グループの記録で、製品分析同定ではない。HHC の他の 6 立体異性体は WHO が可能な配置として図示するが、
   製品成分としての証拠・個別 registry record は無い。いずれも登録・query 化・収集の対象ではない。
7. **`project.json` の `queryDesign.compounds` は registry と一致しない（既知の不一致・本 issue では変更しない）**:
   36 件あるが、registry に無い `Δ8-THC` を含み、registry にある `CBX` を含まない。`Δ8-THC` には query 記述
   （`x` / `youtube` / `googleTrends`）があるが、`metadata/queries/query-registry.json` に query が無く、
   `datasets/cannabinoid-raw-collection/metadata/data-catalog.json` にも run が無い。**安全な既定は「registry を正本とし、`Δ8-THC` を登録済みとして読まない」**こと。
   mirror の同期（`Δ8-THC` の削除と `CBX` の追加）は config の変更であり、本 issue では行わない。別の owner 判断を要する。

## 検証

```sh
.venv/bin/python -m pytest -q tests/validation/test_dictionary_form_precision.py \
  tests/validation/test_registration_state_batch.py tests/validation/test_taxonomy.py \
  tests/validation/test_taxonomy_consistency.py tests/validation/test_compound_identifier_crosswalk.py \
  tests/validation/test_compound_rare_membership.py tests/validation/test_issues.py \
  tests/validation/test_audit_report_freshness.py
make gates GATE=registries
make audit-raw-retention
make audit-raw-completeness
make audit-youtube-coverage
git diff --check
```

README のハッシュを含む `docs/audits/g6-git-tracking-inventory.json` を更新する場合は、`make audit-raw-completeness` の後に
`make audit-snapshots` を実行し、machine-local な状態（`.quarantine` の有無、raw の存在状態）に由来する差分を区別して報告する。

`make test` は raw が machine-local のため、完全な raw checkout でのみ意味を持つ監査を含む。本 issue では対象テストと
`git diff --check` を実行し、raw・被覆・公開状態を変更していないことを確認する。

## 出所

- 2026-11-15 の owner 指示（辞書全体の形式精度の標準化、未登録候補の明示、既存 raw / query 割当ての保持、収集・公開の禁止）。
- 同日の owner 追記指示（除外注記にあった THC の他の位置異性体・THCH の Δ8/Δ9・HHC の立体異性体を候補表へ列挙する）。
- リポジトリ内: `metadata/taxonomy/compound-taxonomy.skos.jsonld`、`metadata/queries/query-registry.json`、
  `datasets/cannabinoid-raw-collection/README.md`、`docs/specs/thc-nomenclature-standard.md`、
  `metadata/taxonomy/thc-regulatory-knowledge-graph.json`、`research/regulatory-status/THCH.md`、
  `research/regulatory-status/HHC.md`、`docs/provenance/compound-taxonomy.md`、`ISS-20261111-TAX-042`、`ISS-20261115-TAX-043`。
- 外部: TAX-042 / TAX-043 が記録した DOI・厚生労働省令・registry record。HHC は WHO 47th ECDD (2024) critical review
  `hexahydrocannabinol-47th-ecdd-critical-review-public-version.pdf` §2C（2026-11-15 参照）と PubChem PUG REST
  （`9(R)-hexahydrocannabinol` → CID 11067065、`9(S)-hexahydrocannabinol` → CID 14378541、CAS 36403-90-4 / 36403-91-5 も同じ CID を返した）。
  PubChem の観測は 2026-11-15 の応答であり、record の変更を監視するものではない。

## 2026-11-15 追記 — 候補 27 行を検索トピックとして登録（ISS-20261115-TAX-045）

owner は同日、本 issue が棚卸しした**候補 27 行を検索トピックとして登録すること**を明示した。登録は
[`ISS-20261115-TAX-045`](20261115_p2_candidate-form-registration.md) が記録する。本 issue の範囲（文書・台帳・
検証）と「候補表は登録ではない」という判断はそのまま有効で、登録によって次が確定した。

- 候補表の 27 行は concept と 2 本の canonical query（`<term>` / `<term> リキッド`、いずれも `active`）を持ち、
  **run を持たない（未収集）**。README の候補表節は「2026-11-15 登録バッチ」節に置き換わり、形式・語・被覆は
  従来どおり 3 つの表に分かれている。
- 本 issue の未決事項 4（`THCJD-O-acetate` の扱い）は、**異性体未指定のアセテートとして登録する**ことで決着した。
  Δ8 / Δ9 の別個の構造は本リポジトリで確認しておらず、分割していない。
- 本 issue の未決事項 6（列挙した候補の未解決点）は、形式ごとの証拠の種類と限界が
  `docs/provenance/compound-taxonomy.md` の 2026-11-15 節と各概念の `skos:scopeNote` に記録され、
  **登録は format-level の外部識別子の選択を意味しない**ことが明示された。
- 既存 query / run の割当て、`THC` の総称性、`project.json` の `CBX` 不一致（未決事項 7）は変わらない。

本追記は本 issue のステータス・履歴を変更しない。
