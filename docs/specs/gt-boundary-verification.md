# Google Trends 境界挙動の検証契約（ISS-20261015-GT-001）

**対象:** `google-trends-mcp` collector の相対 timeframe（`today 1-m` / `3-m` / `12-m` / `5-y`）が
リクエスト時にどの暦区間へ解決されるかの**実測検証**と、`exact=true` への昇格条件。

**役割分担:** 本 spec は「何を検証済みと呼ぶか（昇格規則）」と「ライブ計測の実行プロトコル」を
固定する。計画・レビュー・実行結果は `docs/reports/20261015b-gt-boundary-verification.md`。
実行はメンテナの承認を要する（issue の「ライブ収集（別途承認）」）。

**禁止:** 推測で `exact=true` にしない。raw を改変しない。失敗収集を 0 件に変換しない。
レート制限を無視した連打をしない。資格情報を記録しない。

---

## 1. `exact` の意味（昇格が主張する内容）

`CompiledWindow.exact=true` は、次の**限定された主張**を意味する:

> リクエスト時にコレクタが解決する区間は、`validation.windows` の名目モデルが
> `reference_time` で解く区間と、**週次 1 バケット（`WINDOW_MATCH_TOLERANCE` = 7 日）以内で一致し**、
> その一致は独立な複数回の実測で再現する。

したがって昇格後も `limitations` から「週次バケット量子化による残差（1 週間未満）」を消さない。
暦日一致（0 日残差）の主張はしない — 週次ラベルからは原理的に観測できない。

## 2. 語彙と証拠クラス

- **requested**: 研究が要求した窓。相対 timeframe の場合、絶対形は存在しない。
- **collector nominal**: 名目モデルによる解決値（`validation.windows.resolve_relative_timeframe`）。
  計測 run の `temporal_provenance.requested_*` に入る値はこれであり、**研究要求ではない**
  （run の `limitations` 第 1 項と `submitted_parameters.timeframe` が正を記録する）。
- **observed**: 応答に実際に存在したバケットラベル（first / last）。
- **証拠クラス:**
  - `recorded_legacy`: 旧契約で記録された実行（例: 2026-10-12 の 5y run）。
    reference は session 記録の `collection_timestamp` で、変換 epoch の保証が弱い。**昇格には使わない**（併記のみ）。
  - `measurement`: 本 spec のプロトコルで取得し、`environment.measurement.protocol` を持つ
    adoption 済み run。**昇格規則はこれのみを対象とする。**

## 3. 昇格規則（machine-checkable）

規則の評価は読み取り専用コマンド `python -m validation.cli boundary-report` が行う。
規則を満たす集合を「計測コホート」と呼ぶ。

**計測コホート（cohort）の定義:** `environment.measurement.protocol == "gt-boundary-verification@1"` を持ち、
`datasets/` 配下に adoption 済み（catalog 在）で存在する run。

**条件（全て必須）:**

| # | 条件 |
|---|---|
| R1 | 対象 timeframe は登録語彙の全 4 件（`today 1-m` / `3-m` / `12-m` / `5-y`）。部分昇格はしない |
| R2 | 各 timeframe について、cohort 内の 2 run 以上（run_id が相異なる） |
| R3 | その timeframe の参照時刻が UTC 日として 2 日以上にわたり、かつ最遠の 2 参照時刻の間隔が 7 日以上 |
| R4 | 各 run の verdict が `consistent`（観測 first が名目 start の 7 日以内、観測 last bucket 終端 = last label + バケット幅の 7 日以内。バケット幅はラベル間ギャップの gcd（週次 7 日 / 日次 1 日、欠週で不変）） |
| R5 | 各 run が `execution.status=success` で、生 envelope artifact（`mcp-tool-result.json`）を保持 |
| R6 | cohort に failed run が混入していない（失敗収集は quarantine に保全し、実行記録に残す） |

- R1 の代替案（timeframe 単位の逐次昇格）は検討の上で**採用しない**（compiler の語彙は 1 単位で
  昇格させ、部分的な `exact` の意味論を増やさない）。
- 規則は `boundary-report` の `rule.eligible` が真であることで確認する。**報告書の手書き判定は不可。**

## 4. ライブ計測プロトコル

### 4.1 計測器

- 承認された MCP セッション（`google-trends` server = npm `google-trends-mcp`、MIT、API キー不要）から
  `interest_over_time` を呼び、**verbatim の tool result** を capture する。
- 本リポジトリは自らライブ収集を実行しない（`adapter.py` docstring）。実行はメンテナの承認後に限る。
- Apify 等の有償・資格情報必須の経路は使わない。シークレットをファイルに書かない。
- 付属 harness（`collection.adapters.google_trends.boundary`）は**本プロトコル専用**である。
  汎用のソース別 staging ドライバと `stage` CLI（対象ソース・payload 形式の決定を含む）は
  ISS-20261015-COL-017 のまま。

### 4.2 行列（固定）

| 項目 | 値 |
|---|---|
| term | `CBX`（登録クエリ `cbx-general-ja`） |
| geo | `JP` |
| timeframe | `today 1-m`, `today 3-m`, `today 12-m`, `today 5-y` |
| 反復 | 各 timeframe 2 回。パス 1 とパス 2 の参照時刻は 7 日以上離す（合計 8 call） |
| 保存先 study | `cannabinoid-raw-collection`（`data/raw/google_trends/`）。2026-11-04 の所有移管で `cbx-search-trends` から移した（`ISS-20261024-COL-016`） |
| run_id | `<YYYYMMDDTHHMMSSZ>-google-trends-boundary-<timeframe-slug>`（例: `20261101T030000Z-google-trends-boundary-12m`） |

- 429 応答は 2〜5 分の backoff 後に再試行し、その事実を capture manifest の `notes` に残す
  （既存記録: `20261012T064246Z-google-trends-ja-rikiddo-5y-main5` の `rate_limit_429`）。
- 同一クエリの反復で**値**は変わりうる（非決定性）。本プロトコルの対象は**境界**であり、
  値の差分は観測として記録し不一致とはしない。境界（first / last ラベル）が再現しない場合は
  その run の verdict がそれを示す。

### 4.3 capture manifest（入力形式、`capture_version: 1.0.0`）

```json
{
  "capture_version": "1.0.0",
  "instrument": {"kind": "mcp_session", "server": "google-trends-mcp", "server_version": "0.1.1"},
  "captures": [
    {
      "run_id": "20261101T030000Z-google-trends-boundary-12m",
      "request": {"tool": "interest_over_time",
                  "params": {"terms": ["CBX"], "geo": "JP", "timeframe": "today 12-m"}},
      "started_at": "2026-11-01T03:00:00Z",
      "finished_at": "2026-11-01T03:00:06Z",
      "result": {"content": [{"type": "text", "text": "Interest over time for: CBX\nGeo: JP | Timeframe: today 12-m\n\nDate\tCBX\nOct 13 – 19, 2025\t54\n"}], "isError": false},
      "notes": "optional; 429 retry など"
    }
  ]
}
```

- `result` はセッションが受けた形をそのまま入れる（整形・要約・再構成をしない）。
- manifest は実行中の入力であり、**証拠の正本ではない**（証拠は adoption 済み run）。
  manifest は workspace 外（例: `~/Downloads`）に置いてよい。

### 4.4 応答本文の解釈（parser 規則、`google-trends-mcp@0.1.1`）

期待形式（`dist/index.js` の実装に基づく）:

```
Interest over time for: <term>
Geo: <geo> | Timeframe: <timeframe>

Date	<term>
<label>	<value>
...
```

  - **空白の正規化と両側の年（2026-10-15 追記）**: ライブ応答はダッシュの両側に**細い空白**
    （U+2009、場合により U+202F / U+00A0）を出し、年跨ぎの週は `Dec 26, 2021<U+2009>–<U+2009>Jan 1, 2022`
    のように**両側に年**を書く。parser はラベル内のこれらの空白を半角空白に正規化し、
    両側に年がある形も同じ文法で受け、bucket 開始日は**左側の年月日**から取る（年跨ぎの補正は不要）。
    この不一致は §4.4 の手順（実形式を記録 → parser を更新 → 再開）に従って解消した。
    生 envelope は保全されるため再解釈は再収集なしで可能。
  - **空白の正規化（2026-10-15 追記）**: ライブ応答はダッシュの両側に**細い空白**
    （U+2009、場合により U+202F / U+00A0）を出す（実測: `Dec 26, 2021<U+2009>–<U+2009>Jan 1, 2022`）。
    parser はラベル内のこれらの空白を半角空白に正規化してから解釈する（上記の 1 文法のまま）。
    この不一致は §4.4 の手順（実形式を記録 → parser を更新 → 再開）に従って解消した。
    生 envelope は保全されているため再解釈は再収集なしで可能。
- 上記以外は**拒否**（推測補完しない）。具体的には:
  - 実在しない日付（`Feb 30`、`2025-13-45` 等）→ `label_date_invalid`
    （架空の bucket 開始日を作らない）
  - 系列が昇順でない / 重複ラベル → `labels_out_of_order`（文書化された規則は昇順系列のためのもの）
  - 単一 term なのに value が複数ある行 → `row_shape_unknown`。比較表（複数 term）は
    従来どおり `multi_term_unsupported`
  - value が相対指数の範囲外（0–100 外）→ `value_out_of_range`
- **比較応答（`compare_terms`、2026-10-23 追記）**: 複数語を 1 つの共通スケールで測る唯一の計測で、形式は
  `Comparison: A vs B` / `Geo: … | Timeframe: …` / `Average interest scores (0-100):` の下に
  `  A: 33 <-- highest` 形式の行 / `Date\tA\tB` の表。
  parser は `parse_comparison_tool_result` が担い、語数と列数が一致しない行は `row_shape_unknown`、
  語数が 1 なら `comparison_terms_missing` で拒否する（列を黙って 1 本に減らさない）。
  単独系列とは別の文書（`google-trends-comparison-v1`）として保存し、単独系列の系列文書に混ぜない。
- `isError:true` または本文が `Error:` で始まる場合は
  失敗 capture として記録する（系列を作らない）。
- **no data 応答（2026-10-23 追記）**: 本文が
  `Google Trends returned no data for the given terms and timeframe. Try a broader timeframe or different terms.`
  で始まる場合、それは**閾値未満で系列が存在しない**というソースの回答であり、
  `no_data` という安定した reason code で拒否する（`text_line_unknown` にしない）。
  実測: `20261023T162326Z-google-trends-thc-o-12m-r3`（THC-O / `today 12-m`）。
  系列を作らないのは同じだが、**欠測（missing）であって collection failure ではない**ので、
  アダプタは `errors[].code = NO_DATA` / `reason_codes = ["no_data"]` として記録する。
  なお `status=failed` のままだと L1 は quarantine に置く（採用記録に残せない点は `ISS-20261023-GT-006` §3）。
- **形式検証（必須）:** 行列を回す前に**最初の 1 capture だけ**で `verify` を実行し、
  実形式が parser の許容形と一致することを確認する。不一致の場合は行列を停止し、
  実形式を記録した上で parser を更新（変更として追跡）してから再開する。
  生 envelope は常に保全されるため、解釈の再実行は再収集なしで可能。

### 4.5 実行コマンド列

```bash
# (0) 形式検証: 最初の 1 capture で実行（ライブ 1 回目）
.venv/bin/python -m collection.adapters.google_trends.boundary verify \
  --manifest /path/to/boundary-captures-pass1.json

# (1) staging（capture ごとに run を書く。採用判定はしない）
.venv/bin/python -m collection.adapters.google_trends.boundary stage \
  --manifest /path/to/boundary-captures-pass1.json --datasets-root datasets

# (2) catalog（run_id ごとに L1 → catalog / quarantine）
.venv/bin/python -m collection.core.cli adopt --staged .staging/<run-id> \
  --datasets-root datasets

# (3) 対応表と規則評価（読み取り専用）
.venv/bin/python -m validation.cli boundary-report --datasets-root datasets

# (4) 監査スナップショットの再生成（run 追加で陳腐化するもの。完全なリストと
#     再生成コマンドの正本は tests/validation/test_audit_report_freshness.py の REPORTS 表）
.venv/bin/python -m validation.cli audit-queries     --output docs/audits/g2-query-inventory.json
.venv/bin/python -m validation.cli audit-temporal    --output docs/audits/g3-temporal-inventory.json
.venv/bin/python -m validation.cli audit-artifacts   --output docs/audits/g4-storage-inventory.json
.venv/bin/python -m validation.cli audit-legacy      --output docs/audits/g5-legacy-runs.json
.venv/bin/python -m validation.cli audit-provenance  --output docs/audits/g5-provenance-assessment.json
.venv/bin/python -m validation.cli audit-git-tracking --output docs/audits/g6-git-tracking-inventory.json
.venv/bin/python -m research.cli --repo-root . --datasets-root datasets audit-studies \
  --output docs/audits/g7-study-inventory.json

# (5) 全テスト（再生成コマンドの正本は tests/validation/test_audit_report_freshness.py）
.venv/bin/python -m pytest -q
```

- 採用済み run の run_id と参照時刻の一覧は (3) の出力に含まれる。
- (4) の 7 コマンドは dataset 配下の run を走査するスナップショット（または tracked
  ファイル一覧）を再生成する。g6-private-catalog と g6-publication-eligibility は
  添付データ / 起動記録であり、run 追加では変わらない（AUD-028 の既知制約は別）。
- (5) で既存の失敗数（AUD-028 の 3 件）が増えていたら再生成漏れ。

## 5. 対応表（boundary-report）

各行 = 1 run。列: `run_id` / `evidence_class` / `timeframe` / `reference_time` / 名目 start・end_exclusive /
観測 first・last / first offset（日）/ last-bucket-end offset（日）/ `verdict`。

- `verdict=consistent`: R4 の両 offset が 7 日以内。
- `verdict=inconsistent`: どちらかが 7 日超。
- `verdict=insufficient_evidence`: reference / timeframe / 観測 bounds / 実行状態の欠落、
  ラベルステップが 1 日・7 日以外（`irregular_label_step`）、空系列（`no_series_observed`）。
  欠測・失敗は「観測ゼロ」に変換しない。no-data 応答は missing のまま。
- `rule` セクションが昇格規則の条件別評価（`eligible` と理由）を返す。

## 6. 昇格手続き（evidence 取得後・別変更）

`boundary-report` を実行した後、証拠を伴う**別の変更**で:

1. 証拠 run の run_id 一覧・report 出力のハッシュ・昇格日を collector registry の `evidence` に追記し
   `verified_at` を更新する。
2. compiler の `exact` 判定を検証記録に結び付ける（機構の設計は昇格時に確定する。
   記録なしに `exact=true` を返す変更は禁止）。
3. `docs/specs/collection-pipeline.md` §3.2 / `docs/specs/validation-framework.md` §16.3 を更新する。

## 7. 現状（2026-10-15）

- ライブ計測は**未実行**（承認待ち）。GT-001 は `PENDING`。
- オフライン部分: parser / stager / report 実装・テスト済み。recorded_legacy 行（5y,
  2026-10-12）は `consistent` だが cohort 外（昇格不能）。
- `exact=false` / `boundary_semantics=unverified` は継続（全 compile）。

## 8. 共通スケール比較のアンカー規則（ISS-20261105-GT-030）

### 8.1 単独系列を化合物間で比較できない理由

単独 `interest_over_time` の値は**その語自身のピーク=100** に正規化される。したがって
別 run の単独系列を並べても、値の大小は需要の大小を意味しない。複数語を 1 回の
`compare_terms` で測った系列だけが共通スケールを持ち、化合物間比較の唯一の計測で
ある。

### 8.2 宣言（正本）

study の `datasets/<study>/metadata/query-design.json` の `comparison_scales` が正本。
この study の 5年ポリシーは `gt-5y-common-scale-cbd-thc` で、次を固定する:

| 項目 | 値 |
|---|---|
| anchor query | `cbd-general-ja` / `thc-general-ja` |
| anchor term | `CBD` / `THC` |
| request | `compare_terms` / `geo=JP` / `locale=ja` / `today 5-y` |
| window | `2021-10-31_2026-11-08`（`metadata/windows/` の登録窓。旧窓 `2021-10-17_2026-10-18` の setA〜D は legacy） |
| compound set | query registry の active `compound_general` を権威とする。除外は `excluded_compound_ids` に理由付きで記録（CBX は ISS-20261024-COL-016 の決定まで除外） |

plan は `comparison` ブロックで `policy_id` / anchor query ids / anchor terms / locale を
宣言する。宣言のない複数語 plan は共通スケール比較として扱わない。

### 8.3 ゲートと監査

| 段階 | コマンド | 規則 |
|---|---|---|
| 収集前 | `gate-plan`（`make gate-plan PLAN=<file>`） | `common_scale` は両 anchor を**同一** `compare_terms` 要求に含むこと。geo / timeframe / window / locale がポリシーと一致すること。欠落・不一致・宣言なしの複数語 plan は **stop**（fail closed） |
| 収集後 / 採用 | `gate-run`（L1） | 宣言済み run は request と comparison artifact の**両方**に anchor を含み、window / request metadata が一致すること。宣言のない comparison-shaped run は warning（legacy。raw は変更しない） |
| 監査 | `audit-comparison-scale` | ポリシーごとに missing anchor sets / compound coverage を報告。比較に使えない run は `not_comparable_runs`、要求条件がポリシーの外にある run は `out_of_scope_runs`、宣言前だがアンカーが揃う run は `legacy_undeclared_runs` に分ける。`--require-complete` で missing compound を exit 1。`make gates GATE=comparison` は宣言だけを検証する |

単独系列 plan は引き続き許可するが、run_metadata の `comparison` に
`comparison_scale: single_series` / `cross_compound_comparable: false` を記録し、
比較可能とは扱わない。

### 8.4 現状と legacy の扱い（2026-11-05）

- 5年 common-scale setA〜D（旧窓 `2021-10-17_2026-10-18`）は CBD/THC を含むが、
  ポリシーの現行窓の外にあるため `legacy_out_of_scope` として報告する（共通スケール
  としては有効だが、現行窓の比較・被覆には使えない）。新規準拠とは扱わず、raw も
  書き換えない。`not_comparable_runs` には入れず `out_of_scope_runs` に出す。
  ポリシーの現行窓 `2021-10-31_2026-11-08` の再収集は
  `metadata/plans/gt-5y-common-scale-current-set{A..D}.json` で宣言済み（未収集）。
- 現行窓の common-scale run がまだ無いため、監査は必須 14 化合物を **missing** と
  報告する（旧窓の被覆では代替しない）。
- THCNM は 5年単独系列のみで、アンカー付き common-scale run が無い。したがって
  `thcnm-general-ja` は **missing**。計画は現行窓の
  `datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-common-scale-thcnm.json`
  （CBD + THC + THCNM）と、THCNM を含む `gt-5y-common-scale-current-setD.json` の
  2 つで、どちらかを採用すれば THCNM の被覆は `complete` になる（他 13 化合物は
  別 run の採用が必要）。
- 12ヶ月の legacy comparison sets（`common-scale-expansion` の setB/setD、
  `common-scale-missing`、製品語セット）は 5年ポリシーの範囲外
  (`legacy_out_of_scope`) だが、anchor 欠落は `legacy_missing_anchor_sets` に残る。
  12ヶ月を同じ規則で扱うには別の `comparison_scales` ポリシーが必要である。
- この規則は §1 の `exact` と独立である。共通スケールであることは、境界が暦日一致
  したことを主張しない（`exact_window_match=false` は limitations に残る）。
