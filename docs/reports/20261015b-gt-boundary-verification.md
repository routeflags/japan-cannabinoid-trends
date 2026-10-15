# Google Trends 境界挙動のライブ検証 — 計画・実装・実行手順（ISS-20261015-GT-001）

対象 issue: `docs/issues/20261015_p1_live-boundary-verification.md`（ISS-20261015-GT-001、P1）。
本書は Product Manager が作成した計画（BDD 分解・設計判断・レビュー記録）と、
実装・検証の結果、および**メンテナへの単一の承認質問**を記録する。

判定語彙は repo の慣例に従い **observed / derived / interpretation** を区別する。
未実行のライブ計測を「実施済み」と書かない。

---

## 1. 問題の再確認（issue の主張との照合）

| # | issue の主張 | 本作業開始時の確認（observed） |
|---|---|---|
| 1 | すべての compile が `exact=false` / `boundary_semantics=unverified` | `src/collection/adapters/google_trends/compiler.py` の `compile()` は定数で `exact=False` を返す（`grep`/読解で確認） |
| 2 | `window.exact_required: true` の plan は `WINDOW_EXACTNESS_UNAVAILABLE` で停止 | `src/collection/core/pipeline.py` L431-L444、既存テスト `test_pipeline_stops_when_an_exact_window_is_required` で確認 |
| 3 | `config/collectors.json` の `google-trends-mcp` は `absolute_date_range: unknown` / `relative_date_range: supported` | レジストリ実物を確認 |
| 4 | `metadata/windows/` の 2 件は相対 timeframe 経由でのみ到達可能 | 2 件とも `[2021-10-10, 2026-10-12)` / `[2025-10-12, 2026-10-12)`、compiler は `today 5-y` / `today 12-m` を選ぶ |
| 5 | ライブ収集経路は未接続 | `SessionMcpTransport` は callable 注入時のみ動作。`build_adapter(fixture=None)` は callable なしで fail closed。CLI `collect` は `--fixture` 必須（読解で確認） |
| 6 | 実記録応答（262 点）で形状照合済み・境界は未検証 | tracked 実データを直接 parse: 262 点、`2021-10-10 .. 2026-10-11`、`collected_at=2026-10-12T06:42:46.688Z`（observed） |

## 2. 完了条件の写像

issue の完了条件と、本作業で達成可能な範囲（承認なしで可能 / 承認必須）:

| 完了条件 | 本作業での扱い |
|---|---|
| (1) ライブ収集 1 回以上の実測 run（`run_metadata.json`） | **承認必須**。条件付き成果物 = 実行手順（検証済みの parser/stager/report）。ライブ実行なしでは未達のまま |
| (2) 要求窓と観測境界の対応表（timeframe 別） | オフラインで達成: 記録済み実データの対応表 29 行（§10）+ 手順実行後に増えるライブ行。表生成は実装・テスト済み |
| (3) 昇格条件の文書化 or 非昇格理由の記録 | オフラインで達成: 昇格規則を spec に文書化 + 機械可読な評価器を実装。現状は「証拠未取得のため non-eligible」を記録 |

## 3. BDD 分解（タスク一覧と期待する振る舞い）

各タスクは「Given（データ・前提）/ When（操作）/ Then（期待する振る舞い）」で定義する。

### T1 — `exact_required` 停止経路の維持確認（オフライン・既存）

- **T1.1** Given 登録 window `2025-10-12_2026-10-12` と `reference_time=2026-10-13T00:00:00Z`、When compile、Then `exact=false` / `boundary_semantics=unverified` / limitations 非空。
- **T1.2** Given `window.exact_required=true` の plan、When `run_collection`、Then `WINDOW_EXACTNESS_UNAVAILABLE` で停止し `.staging/` を作らない。
- **T1.3** 実レジストリ（変更しない）で compile したとき `exact=false` のまま（誤昇格がない）。

### T2 — 計測キャプチャの契約（オフライン）

capture は「承認された MCP セッションが得た **verbatim の tool result**」とする。

- **T2.1** Given npm `google-trends-mcp@0.1.1` の tool result envelope（`content[0].text` に `Date\t<term>` ヘッダと `formattedTime\tvalue` 行）、When `parse_tool_result`、Then 週次バケットの開始日 ISO と値の列を返す。ラベル形は仕様で固定: 範囲（`Oct 12 – 18, 2025` / 年跨ぎ `Dec 28 – Jan 3, 2026`）、単日（`Oct 12, 2025`）、ISO（`2025-10-12`）。
- **T2.2** Given 未知ラベル・非整数値・ヘッダ不一致・空系列、When parse、Then 明示エラーコードで拒否（推測補完しない）。
- **T2.3** Given `isError` envelope または `Error:` で始まる本文、Then 「失敗キャプチャ」として区別（0 件への変換禁止）。
- **T2.4** Given 計測用 manifest（`capture_version` / `instrument` / `captures[]`）、When 検証、Then run_id のパス安全性・時刻順序・timeframe が登録語彙内・単一 term・geo 形式を検査。複数 term は計測プロトコル外として拒否。
- **T2.5** Given 正常キャプチャ、Then 生 envelope を byte 単位で保全し、抽出系列との整合（系列の各日付が生テキストのラベルから導出できる）を確認。不一致は拒否。

### T3 — 計測 run の staging / catalog（オフライン replay で検証）

- **T3.1** Given capture（正常）、When `stage`、Then `.staging/<run-id>/` に `run_metadata.json` / `artifact-manifest.json` / 生 envelope / 正規化系列が書かれ、`action=staged`（判定はしない）。
- **T3.2** Given staged run、When `adopt`、Then L1 通過で catalog へ移動し、厳格検証（`verify_artifacts=True`）で issue 0 件。
- **T3.3** 記録される `temporal_provenance`: `requested_*` = 名目解決値（プロトコル上の注記で「研究要求ではなく名目値」と明示）、`submitted_parameters.timeframe`、`reference_time`、`observed_min/max_timestamp`、`boundary_semantics`、`exact_window_match=false`、`limitations` 非空。
- **T3.4** `environment.measurement`（protocol id / instrument / capture index）が記録され、commit / adapter fingerprint と衝突しない。
- **T3.5** Given 失敗キャプチャ、Then `execution.status=failed` として staged（系列 artifact なし、failure evidence として保存）。
- **T3.6** run_id 衝突・study 不在・window 不完全は fail closed（既存 `stage_run` の拒否コード）。

### T4 — 対応表と昇格規則の評価器（オフライン、ライブ後に再実行可能）

- **T4.1** Given run ディレクトリ、When `boundary-report`、Then 1 行 = run_id / timeframe / reference / 名目解決 / 観測 first/last / first offset / last bucket end offset / verdict（`consistent` / `inconsistent` / `insufficient_evidence`）。
- **T4.2** Given tracked 実記録 5y run、Then `consistent` 行が再現される（観測 `2021-10-10 .. 2026-10-11`、名目 `2021-10-12T06:42:46Z .. 2026-10-12T06:42:46Z`、offset −2.28 日 / +5.72 日）。**これは recorded evidence でありライブ計測ではない。**
- **T4.3** Given 計測コホート（`environment.measurement.protocol` を持つ adopted run）、When 規則評価、Then 4 timeframe 全部について「2 run 以上・参照日 2 日以上（かつ 7 日以上間隔）・全行 consistent・失敗 run なし」が揃って初めて `eligible=true`。不足は条件別理由つき `eligible=false`。
- **T4.4** 例外系: 失敗 run / 空系列（no data）/ reference 不明 / 語彙外 timeframe は `insufficient_evidence`（欠測を 0 に変換しない）。
- **T4.5** 評価器は書き込みをしない（レジストリ・issue・run を変更しない）。

### T5 — ライブ手順書（spec）と実行コマンド

- **T5.1** Given `docs/specs/gt-boundary-verification.md`、Then 計測器（承認済み MCP セッション）、行列（4 timeframe × 2 UTC 日以上 = 8 run）、capture 形式、実行コマンド列、採用・報告・監査再生成コマンド、昇格手続き、禁止事項（推測昇格・raw 改変）を記載。
- **T5.2** Given 承認、Then 手順どおり実行すると (1)(2)(3) の証拠が生成される（実行は別作業）。

### T6 — issue の誠実な状態更新

- **T6.1** Given ライブ未実行、Then GT-001 を `PENDING`（理由 + 日付を注記）に更新し、完了条件 checkbox は未チェックのまま。
- **T6.2** `audit-issues` が malformed / duplicate / OPEN P0 を出さない。

### T7 — 関連文書の整合

- **T7.1** `docs/specs/collection-pipeline.md` §3.2 / §9 と `docs/specs/validation-framework.md` §16.3 が「オフライン計測基盤は実装済み・ライブ計測は承認待ち」を正しく反映する。

## 4. オフライン / 承認必須の切り分け

| 区分 | 内容 | 根拠 |
|---|---|---|
| 今すぐ実行可能（オフライン） | parser / stager / report 実装とテスト、spec / report 執筆、issue 状態更新、既存ゲート確認 | ネットワーク・資格情報不要 |
| 承認必須（ライブ） | `interest_over_time` の実呼び出し 8 回（+ 予備）、staging / adopt、`boundary-report` 実行、監査再生成 | issue の「ライブ収集（別途承認）」; repo は「ライブ収集を自ら実行しない」（`adapter.py` docstring） |
| 承認+証拠必須（昇格） | `exact=true` への変更（レジストリ記録 + コード変更。本作業では実装しない） | issue「推測で exact=true にしない」 |

## 5. メンテナへの単一の承認質問（Decision D1）

> **D1: ISS-20261015-GT-001 のライブ境界計測を、`docs/specs/gt-boundary-verification.md` §4 の手順どおり実行してよいか。**
>
> - 対象: `google-trends-mcp`（npm, MIT, API キー不要, 無料）、geo=JP、term=`CBX`（登録クエリ `cbx-general-ja`）。
> - 規模: 4 timeframe × 2 UTC 日 = 8 tool call（+ 429 時の backoff 再試行）。1 パス目と 2 パス目は 7 日以上空ける。
> - 保存先: `cbx-search-trends`（既存 study）の `data/raw/google_trends/` に catalog。
> - 承認する場合: 手順実行 → `boundary-report` が `eligible=true` を出せば、**別コミット**で昇格（手続きは spec §6。本 issue はライブ実行後に `RESOLVED` へ）。
> - 承認しない場合: `exact=false` を継続し、その理由と見直し条件を GT-001 に記録（issue は `PENDING` のまま）。

補足: 実行コストは約 8 call / 無料。レート制限対策として call 間隔を空ける（既存記録: 429 後 2〜5 分の backoff で回復）。

## 6. 設計判断と根拠（recon）

- ライブ経路の現状: `SessionMcpTransport` は注入 callable なしで `TransportError`。CLI `collect` は `--fixture` 前提。→ 計測は「承認済みセッションが取得 → stager で staging → `adopt`」の既存移行パス（§3.3 が MCP セッションを producer として明記）に載せる。
- staging の受け口 `stage_run` は「産出側」であり判定しない（producer / verdict 分離）→ stager は `.staging/` 書き込みまで、`adopt_staged` が L1 と catalog を決める。
- 生データは byte 単位で保全（`stage_run` が copy。manifest の SHA-256 はディスクから計算）。
- 系列 artifact は登録済み schema `google-trends-interest-over-time-v1`（reader `json-timeseries-reader`、`record_count_mode=data_points`）を使い、L1 が件数を機械検証できるようにする。生 envelope 用に schema `google-trends-mcp-tool-result-v1`（reader `json-object-reader`、count なし）を登録する。
- run の `requested_*` は「名目解決値」であることを limitations と spec に明記（P5: requested / collector nominal / observed の分離を破らない）。
- `exact` 判定は compiler が所有し続ける（本作業で compiler は変更しない）。昇格は「レジストリに検証記録 + compiler 変更」の別変更とし、spec に手続きを固定する。
- 観測境界の判定は 1 週次バケット許容（`WINDOW_MATCH_TOLERANCE` = 7 日）を使い、first bucket 開始が名目 start の 7 日以内、last bucket 終端（= last label + バケット幅推定。幅はラベル間ギャップの gcd: 週次 7 日 / 日次 1 日、欠週は不変）が名目 end_exclusive の 7 日以内、の両方が成り立つとき `consistent` とする。週次ラベルは境界を 1 バケット精度でしか観測できない — これは限界であり spec に記録する。
- 使用ツール根拠: `serena`/LSP 系は本環境に未提供のため、`read_file` + `grep` + `.venv` 実行で `compiler.py` / `pipeline.py` / `validation/windows.py` / `model` / テストを直接確認（本節の各主張に出典を付記）。npm パッケージは `npm pack google-trends-mcp@0.1.1` で取得し `dist/index.js` / `dist/trends-client.js` を読解（ライブ呼び出しはしていない）。

## 7. Plan Architect レビュー記録

計画をコードベースのパターン・規約に照らして独立に検査した（reviewer=architect 役を同一セッション内で実施）。指摘と処置:

| # | 指摘 | 重大度 | 処置 |
|---|---|---|---|
| 1 | stager は ISS-20261015-COL-017（ソース別 staging ドライバ / `stage` CLI）と領域が重なる | Medium | 本モジュールは**計測プロトコル専用**（manifest 形式・検証・`stage_run` 組立のみ）とし、汎用ドライバと `stage` CLI は COL-017 のまま残す。spec に境界を明記 |
| 2 | `formattedTime` の実形式はオフラインで確定できない。parser の前提が誤っている可能性 | High | parser は**fail closed**（未知形式は拒否）+ 生 envelope 保全（再導出可能）+ 手順の第 0 段で「最初の 1 capture で形式検証（`verify`）し、形式不一致なら行列実行を停止して記録」を必須化 |
| 3 | 週次バケットからは真の境界を 1 バケット未満の精度で確定できない | High | `exact=true` の意味を spec で「名目モデルとの一致が週次 1 バケット以内で再現する」と定義し、残差を limitations に残す条件とした。過大な主張をしない |
| 4 | 計測 run の `requested_start/end_exclusive` は研究要求ではない（P5） | Medium | limitations 第 1 項と spec に「名目解決値であり研究要求ではない」を明記。分析は `submitted_parameters.timeframe` + `reference_time` を正とする |
| 5 | legacy 29 run を昇格証拠に使うと reference 意味論が弱い（session 記録の時刻、変換 epoch 不明） | Medium | 昇格規則は「計測プロトコルで取得した adoption 済み run」のみ対象。legacy 行は `recorded_legacy` として併記のみ（証拠クラスを出力に含める） |
| 6 | レジストリ・compiler の昇格機構を今実装すると、証拠なしの到達不能経路を増やす | Medium | **実装しない**。spec に手続きのみ固定。評価器は「昇格候補の判定」まで（書き込みなし）。次段の変更要求を spec §6 に記述 |
| 7 | 計測 run が tracked な datasets 配下に落ちるため、絶対パス等のマシン固有情報を混入させない | Medium | `environment` には basename / 相対記述のみ。report は repo 相対パスで表示。テストで絶対パス非混入を検査 |
| 8 | 監査スナップショット（`docs/audits/g2/g3/g4/g5-provenance`）は run 追加後に陳腐化する | Low | 手順書に再生成コマンド（freshness test 登録済みのコマンド）を明記。本作業では run を追加しないため現状維持 |
| 9 | `docs/plans/` は gitignore のため計画を置くと届かない | Info | 本書を `docs/reports/` に置く（遵守） |
| 10 | 新規 artifact schema 登録は `check_artifact_registry` の検査対象 | Low | `validate-registries` で確認。reader は既存 `json-object-reader` を再利用（新実装なし） |

---

## 8. 実装（オフライン） — 2026-10-15

**ライブ収集は実行していない。** 実行には issue の定めどおりメンテナの承認（D1）が必要なため、
今回の作業は「承認が下りたらそのまま実行できる計測基盤と手順」までを実装・検証した。

| ファイル | 種別 | 内容 |
|---|---|---|
| `src/collection/adapters/google_trends/boundary.py` | 新規 | capture manifest の検証、verbatim tool result のパース（fail closed）、`stage_run` への組立。CLI `verify` / `stage` |
| `src/validation/boundary.py` | 新規 | 対応表の抽出と昇格規則の評価（読み取り専用、書き込みなし） |
| `src/validation/cli.py` | 変更 | `boundary-report` サブコマンドを追加 |
| `src/collection/core/pipeline.py` | 変更 | `staging_artifact_id` を公開（`derived_from` の参照規則を 1 箇所に保つため） |
| `src/collection/core/provenance.py` | 変更 | staged run の宣言 `reference_time` / `limitations` を `temporal_provenance` に引き継ぐ（§3.3 の「adapter の temporal block と同様にマージ」を実際に満たす。従来は compiler 経由でのみ記録され、staging 経由では落ちていた） |
| `metadata/artifacts/artifact-registry.json` | 変更 | `google-trends-mcp-tool-result-v1` を登録（reader は既存 `json-object-reader`、新実装なし） |
| `docs/specs/gt-boundary-verification.md` | 新規 | 計測プロトコル・昇格規則・実行コマンド（正本） |
| `docs/specs/collection-pipeline.md` / `docs/specs/validation-framework.md` | 微修正 | 現状（オフライン基盤あり・ライブ未実行）の正確な反映 |
| `docs/issues/20261015_p1_live-boundary-verification.md` | 変更 | `PENDING`（理由 + 日付）。完了条件は未チェックのまま |
| `docs/issues/20261015_p2_gt-legacy-label-year-defect.md` | 新規 | 副産物: 旧 run のラベル年誤り（ISS-20261015-GT-002、P2 OPEN） |
| `tests/collection/test_gt_boundary_capture.py` | 新規 | 21 件（parser / manifest / staging / adopt / CLI） |
| `tests/validation/test_boundary_report.py` | 新規 | 16 件（対応表 / 昇格規則 / CLI / 決定性・非破壊） |

設計上の要点:

- capture の生 envelope は常に run に保全する（`mcp-tool-result.json`。この経路は
  JSON を再直列化するため**値の往復は完全だが byte 同一ではない**。byte 単位のコピーが
  必要な場合は `stage_run` の一般経路を使う）。系列はそこから**導出**したものとして
  別 artifact にする（`derived_from` で参照）。パースできない形式は推測せず拒否する。
- 計測 run の `requested_start/end_exclusive` は名目解決値であることを `limitations` に明記し、
  分析は `submitted_parameters.timeframe` + `reference_time` を正とする（P5 の requested /
  collector nominal / observed 分離を壊さない）。
- 昇格規則は `boundary-report` の `rule.eligible` として機械可読。評価器はレジストリや
  run を書き換えない。`exact` を返す compiler 変更は含まない（証拠取得後の別変更）。

## 9. 検証結果（実行コマンドと結果）

| # | コマンド | 結果 |
|---|---|---|
| 1 | `.venv/bin/python -m pytest -q` | clean checkout（未追跡ローカルデータ無し）で `3 failed, 960 passed, 6 skipped`。失敗 3 件は既知の AUD-028（未追跡ローカルデータ依存）で、親 commit のベースラインと同じ・増えていない（ローカルデータを持つマシンでは `969 passed / 0 failed`）。新規 37 件を含む。2026-10-15 の独立検証で実測し直した値（当初の記載 959 は 1 件ずれ。ローカルデータ依存テストの差） |
| 2 | `.venv/bin/python -m validation.cli validate-registries` | exit 0、`11 target(s), valid`（info 7 件は既存の evidence hash 未記録。新規 artifact schema 登録は strict 通過） |
| 3 | `.venv/bin/python -m validation.cli audit-new-runs` | exit 0、`29 run(s), frozen_legacy_seen=29, new=0, failures=0`（run を追加していないため new=0 のまま） |
| 4 | `.venv/bin/python -m validation.cli audit-issues` | exit 0、`51 issue(s) [OPEN=36, PENDING=2, ...] failures=0`。GT-001 の PENDING 化と GT-002 追加後の値 |
| 5 | `.venv/bin/python -m validation.cli validate-all` | exit 1（legacy 29 run 起因、**期待どおり**。40 targets / error 16） |
| 6 | `bash scripts/validation/validate-version-sync.sh` | exit 0（PASS 13 / WARN 1 — ベースライン同数） |
| 7 | `bash scripts/validation/validate-data-schema.sh` | exit 0（PASS 45 / WARN 2 — ベースライン同数） |
| 8 | `.venv/bin/python scripts/validation/validate-research-pages.py` | exit 0（全ページ最新） |

その他: `git status -- datasets` が空（raw 不変）、`docs/audits/*.json` は未変更（再生成不要）。

## 10. 対応表（オフラインで得られる証拠）

生成コマンド（再現可能・読み取り専用）:

```bash
.venv/bin/python -m validation.cli boundary-report --datasets-root datasets --format json --output /tmp/boundary-report.json
```

- 全 29 run が行になる（relative timeframe を持つ run のみ。timeframe が読めない run は対象外）。
- **計測コホート（`environment.measurement.protocol`）は 0 件**（ライブ未実行のため）。
- `rule.eligible = false`。理由: 4 timeframe すべて `insufficient_consistent_runs` ほか。

timeframe 別サマリ（observed）:

| timeframe | rows | consistent | inconsistent | insufficient_evidence |
|---|---|---|---|---|
| `today 12-m` | 20 | 10 | 2 (phase-a, phase-a-repeat) | 8 |
| `today 5-y` | 9 | 1 (2026-10-12) | 0 | 8 |
| `today 1-m` | 0 | 0 | 0 | 0 |
| `today 3-m` | 0 | 0 | 0 | 0 |

全行（導出値。`class` は証拠クラス、`off` は日）:

| run_id | class | timeframe | reference_time | nominal (start .. end_excl) | observed (first .. last) | first off (d) | last-end off (d) | verdict |
|---|---|---|---|---|---|---|---|---|
| 20261001T115959Z-google-trends-cbx-rikiddo | recorded_legacy | today 12-m | 2026-10-01T11:59:59Z | 2025-10-01 .. 2026-10-01 | - .. - | - | - | insufficient_evidence (label_gap_unknown) |
| 20261001T121949Z-google-trends-h4cbh-hhbd | recorded_legacy | today 12-m | 2026-10-01T12:19:49Z | 2025-10-01 .. 2026-10-01 | - .. - | - | - | insufficient_evidence (label_gap_unknown) |
| 20261002T063821Z-google-trends-cbd | recorded_legacy | today 12-m | 2026-10-02T06:38:21Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.277 | 1.723 | consistent |
| 20261002T063852Z-google-trends-thc | recorded_legacy | today 12-m | 2026-10-02T06:38:52Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.277 | 1.723 | consistent |
| 20261002T063924Z-google-trends-cbg | recorded_legacy | today 12-m | 2026-10-02T06:39:24Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.277 | 1.723 | consistent |
| 20261002T064008Z-google-trends-hhc | recorded_legacy | today 12-m | 2026-10-02T06:40:08Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.278 | 1.722 | consistent |
| 20261002T064118Z-google-trends-thch | recorded_legacy | today 12-m | 2026-10-02T06:41:18Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.279 | 1.721 | consistent |
| 20261002T064135Z-google-trends-nodata | recorded_legacy | today 12-m | 2026-10-02T06:41:35Z | 2025-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T064236Z-google-trends-comparison-setA | recorded_legacy | today 12-m | 2026-10-02T06:42:36Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.28 | 1.72 | consistent |
| 20261002T071255Z-google-trends-thc-o-5y | recorded_legacy | today 5-y | 2026-10-02T07:12:55Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T080652Z-google-trends-h4cbh-5y | recorded_legacy | today 5-y | 2026-10-02T08:06:52Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T080800Z-google-trends-hhbd-5y | recorded_legacy | today 5-y | 2026-10-02T08:08:00Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T081839Z-google-trends-cbn-12m | recorded_legacy | today 12-m | 2026-10-02T08:18:39Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.346 | 1.654 | consistent |
| 20261002T082000Z-google-trends-cbn-5y | recorded_legacy | today 5-y | 2026-10-02T08:20:00Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T085022Z-google-trends-crdp-12m | recorded_legacy | today 12-m | 2026-10-02T08:50:22Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.368 | 1.632 | consistent |
| 20261002T085359Z-google-trends-crdp-5y | recorded_legacy | today 5-y | 2026-10-02T08:53:59Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261002T094657Z-google-trends-hhch-12m | recorded_legacy | today 12-m | 2026-10-02T09:46:57Z | 2025-10-02 .. 2026-10-02 | 2025-09-28 .. 2026-09-27 | -4.408 | 1.592 | consistent |
| 20261002T094730Z-google-trends-hhch-5y | recorded_legacy | today 5-y | 2026-10-02T09:47:30Z | 2021-10-02 .. 2026-10-02 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261005T100000Z-google-trends-common-scale-expansion | recorded_legacy | today 12-m | 2026-10-05 | - .. - | - .. - | - | - | insufficient_evidence (reference_invalid) |
| 20261008T093228Z-google-trends-5y-baseline | recorded_legacy | today 5-y | 2026-10-06 | - .. - | - .. - | - | - | insufficient_evidence (reference_invalid) |
| 20261008T121338Z-google-trends-crdh-5y | recorded_legacy | today 5-y | 2026-10-08 | - .. - | - .. - | - | - | insufficient_evidence (reference_invalid) |
| 20261012T054920Z-google-trends-notation-presurvey | recorded_legacy | today 12-m | 2026-10-12T05:51:23Z | 2025-10-12 .. 2026-10-12 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| 20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m | recorded_legacy | today 12-m | 2026-10-12T05:53:04.363Z | 2025-10-12 .. 2026-10-12 | 2025-10-12 .. 2026-12-28 | -0.245 | 77.755 | inconsistent (offset_outside_one_weekly_bucket) |
| 20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m | recorded_legacy | today 12-m | 2026-10-12T06:05:29.146Z | 2025-10-12 .. 2026-10-12 | 2025-10-12 .. 2026-12-28 | -0.254 | 77.746 | inconsistent (offset_outside_one_weekly_bucket) |
| 20261012T061614Z-google-trends-ja-rikiddo-phase-b-12m | recorded_legacy | today 12-m | 2026-10-12T06:32:38.178Z | 2025-10-12 .. 2026-10-12 | 2025-10-12 .. 2026-10-11 | -0.273 | 5.727 | consistent |
| 20261012T064246Z-google-trends-ja-rikiddo-5y-main5 | recorded_legacy | today 5-y | 2026-10-12T06:42:46.688Z | 2021-10-12 .. 2026-10-12 | 2021-10-10 .. 2026-10-11 | -2.28 | 5.72 | consistent |
| common-scale-missing-20261009 | recorded_legacy | today 12-m | 2026-10-09 | - .. - | - .. - | - | - | insufficient_evidence (reference_invalid) |
| disambiguated_queries | recorded_legacy | today 12-m | 2026-10-01T13:25:00Z | 2025-10-01 .. 2026-10-01 | - .. - | - | - | insufficient_evidence (no_series_observed) |
| variance_check | recorded_legacy | today 12-m | 2026-10-01T13:15:00Z | 2025-10-01 .. 2026-10-01 | - .. - | - | - | insufficient_evidence (no_series_observed) |

読み方（すべて **derived**、一部 **interpretation** を含む）:

- `consistent` 10 行（12-m）+ 1 行（5-y）: 観測 first と last bucket 終端が名目解決の
  ±1 週次バケット以内。2026-10-12 の 5y run が本 issue の「recorded boundary semantics」の実例
  （offset −2.28 / +5.72 日）。
- `inconsistent` 2 行: phase-a / phase-a-repeat の系列に収集時刻より未来のラベル
  `2026-12-28` が混入している（本来は `2025-12-28` の位置）。**ISS-20261015-GT-002** に記録。
  これは legacy 記録の欠陥の検出であり、昇格判断には影響しない（legacy は cohort 外）。
- `insufficient_evidence`: 要約形のみの旧記録（`no_series_observed`）、日付精度のない参照時刻
  （`reference_invalid`）、スラッシュ区切りのレンジラベル（`label_gap_unknown`）、失敗 run
  （`collection_failed`）。欠測・失敗は「観測ゼロ」に変換していない。

**この表は証拠の目録であり、昇格の証拠ではない。** 昇格には spec §3 の計測コホート
（ライブ計測 run、各 timeframe 2 run / 参照日 7 日以上）が必要。

## 11. ライブ実行の前提と手順（ready to execute）

前提:

- メンテナの承認（D1、§5）。
- 承認済み MCP セッション（`google-trends` サーバ = npm `google-trends-mcp`、無料・キー不要）。
  本作業環境では `node v26.8.1` / `npm` / `npx` の存在のみ確認（ライブ呼び出しはしていない）。
- ネットワーク。所要は約 8 tool call + 429 時の backoff。2 パス目は 7 日以上後。

手順（正本は `docs/specs/gt-boundary-verification.md` §4.5）:

1. capture 取得（承認セッション）→ manifest 化（形式は spec §4.3）。
2. 最初の 1 capture で `python -m collection.adapters.google_trends.boundary verify` —
   形式が一致しなければ**ここで停止**（行列を回さない）。
3. パス 1: 4 timeframe を `stage` → `adopt`（`.staging/` → catalog）。
4. 7 日以上あけてパス 2 を同じ手順で取得。
5. `python -m validation.cli boundary-report --datasets-root datasets` で
   `rule.eligible` を確認（合格条件 R1–R6 は spec §3）。
6. run 追加に伴い `docs/audits/` の run 系スナップショットを再生成（spec §4.5 のコマンド）し、
   `pytest -q` が既知の AUD-028 3 件以外で緑であることを確認。
7. `eligible=true` なら、証拠 run_id・report ハッシュ・昇格日を添えた**別変更**で
   `exact=true` 昇格を実施（spec §6）。`eligible=false` の間は promotion しない。

## 12. 未検証・残っている作業

- **ライブ計測そのもの**（8 run の実測）と、その結果に基づく `exact=true` 昇格変更。
- 計測応答本文の実形式（`formattedTime` の表記）。手順の第 0 段（verify）で確定する。
  実形式が想定と異なる場合、行列を停止し parser を実形式に合わせて更新する（生 envelope は
  保全されるため再収集は不要）。
- ISS-20261015-GT-002（旧 run ラベルの年誤り）の原因切り分けと補正方針。
- 他ソースの window compiler（ISS-20261015-WIN-002）は対象外のまま。

## 13. 判定サマリ

| 項目 | 状態 |
|---|---|
| issue 完了条件 (1) 実測 run | **未達**（承認待ち） |
| issue 完了条件 (2) 対応表 | 生成器・テスト実装済み。オフライン 29 行の表を §10 に記録。ライブ行は未取得 |
| issue 完了条件 (3) 昇格条件 / 非昇格理由 | 昇格規則を spec に文書化 + 機械評価器を実装。現状 non-eligible を記録 |
| issue ステータス | `PENDING`（2026-10-15） |

## 14. 独立検証（2026-10-15）と指摘への対応

commit `6d1c624` を独立 worktree・独自スクリプトで検証した（リポジトリ非改変）。
9 主張はすべて**実質 verified**（span 1 件の指摘は下記 D1・D5）。

- verified: 拒否動作（独自 30 入力。未知ラベル・空系列・非数値・形状不明・
  `isError` をそれぞれ拒否、生 envelope の再解釈で同一系列）、staging 境界（`../../evil`
  等の run_id / study_id / パスが既存コードで拒否され何も書かない）、昇格規則（cohort は
  marker 定義。legacy は入れない。手書き判定は不可。現状 `eligible=false`）、
  `boundary-report` の読取専用性（敵対的 root でも exit 0・無書込）、provenance 修正
  （compiler 優先を維持しつつ宣言値が残る。L1 厳格 valid）、テストの非トートロジー性
  （6 種の変異で 1〜2 件が落ちる）、GT-002 の事実（8 ファイル、53 点、
  インデックス 11 のずれ、raw 不変）、衛生（依存・秘密・`docs/audits` 不変）。
- **D1（Medium）→ 修正済み**: 実在しない日付（`Feb 30` 等）を受理し架空の bucket
  開始日を作っていた → `label_date_invalid` で拒否（`datetime.date` 検証）。
- **D2（Low）→ 修正済み**: 昇順でない / 重複ラベルの系列を受理していた →
  `labels_out_of_order` で拒否（spec §4.4 に明記）。
- **D3（Info）→ 修正済み**: 余分な value 列を黙って切り捨てていた → `row_shape_unknown`。
  比較表は従来どおり `multi_term_unsupported`。
- **D4（Info）→ 修正済み**: 負値・100 超を受理していた → `value_out_of_range`。
- **D5（Low）→ 修正済み**: R2「run_id が相異なる」を規則が行数で数えていた →
  評価前に run_id で重複除去（同一 run_id の 2 行では最小数に届かない）。
- **D6（Info）→ 修正済み**: §9 の pytest 件数が clean checkout で再現しなかった →
  実測値（960 passed / 3 failed / 6 skipped）と環境注記に訂正。
- **D7（Info）→ 修正済み**: capture envelope を「byte 単位」と書いていたが、この経路は
  JSON 再直列化（値の往復は完全、byte 同一ではない）→ §8 の記述を訂正し、byte 同一が
  必要な場合は `stage_run` の一般経路を使うと明記。

未検証である旨の指摘: ライブ MCP セッションを要する事項（実形式・8 run 行列・429
挙動・昇格後の `exact=true`）は変更の範囲外で、引き続き承認待ち。

---

## 15. パス 1 のライブ実行（2026-10-15）

メンテナの指示（このスレッドの「go」=増分作業の続行）により、**行列のパス 1**（4 timeframe × 1）を
実行した。パス 2 は参照時刻を **7 日以上**離す必要があるため別途（spec §3）。

### 15.1 実行

| 項目 | 値 |
|---|---|
| 計測器 | `google-trends-mcp@0.1.1`（MIT、API キー不要・無料）を MCP stdio セッションで起動（`collection.adapters.google_trends.mcp_session`） |
| 行列 | term `CBX`（登録クエリ `cbx-general-ja`）/ geo `JP` / `today 1-m`, `today 3-m`, `today 12-m`, `today 5-y` |
| capture manifest | `manifest.json`（ワークスペース外。spec §4.3 により証拠の正本ではない）、sha256 `f39995eb24e3008367ee776b6763037aa704c1a5594f1c413b5bb4410bcdecd8`、絶対パスは記録しない（一時ディレクトリ） |
| 429 / retry | なし（4 call すべて 1 回で成功、`isError` なし） |

### 15.2 検証と採用

```bash
python -m collection.adapters.google_trends.boundary verify --manifest <manifest.json>
# → format_verified=true、4/4 parsed（1m 31 点 / 3m 93 点 / 12m 53 点 / 5y 262 点）
python -m collection.adapters.google_trends.boundary stage --manifest <manifest.json> --study cbx-search-trends
# → 4 staged / 0 stopped
python -m collection.core.cli adopt --staged .staging/<run-id>   # 4 run
# → 4 ADOPTED（L1 通過）
```

| run_id | timeframe | observed（先頭..末尾） | 点 | boundary-report |
|---|---|---|---|---|
| `20261015T042845Z-google-trends-boundary-1m` | today 1-m | 2026-09-15 .. 2026-10-15 | 31 | measurement / consistent |
| `20261015T042849Z-google-trends-boundary-3m` | today 3-m | 2026-07-15 .. 2026-10-15 | 93 | measurement / consistent |
| `20261015T042853Z-google-trends-boundary-12m` | today 12-m | 2025-10-12 .. 2026-10-11 | 53 | measurement / consistent |
| `20261015T042857Z-google-trends-boundary-5y` | today 5-y | 2021-10-10 .. 2026-10-11 | 262 | measurement / consistent |

要求（名目解）との差はすべて**週次 1 バケット以内**で、報告は 4/4 `consistent`。
`exact=true` への昇格には spec §3 の規則（timeframe ごとに 2 run、参照日が 7 日以上離れ、
境界が再現すること）が必要で、**現時点ではコホートが 4 run（timeframe あたり 1）なので
`eligible=false`**（規則は `boundary-report` の `rule` に出力される）。

### 15.3 副次的な影響（実測）

- 監査スナップショットを再生成した（g2 / g3 / g4 / g5-legacy / g5-prov / g6-git / g7）。
  g2 は本件の 4 run のクエリ（`CBX` → `exact_match`）も抽出する。
- `cbx-search-trends` は legacy と契約期の run が混在する study になったため、
  `validate-study --profile legacy` は**凍結リスト外の run を拒否**して exit 2 になる
  （strict は legacy run で exit 1）。テストは id ではなく集合でこれを固定した
  （`tests/validation/test_cli.py`）。

### 15.4 残り

- **パス 2**（同じ行列を参照時刻 7 日以上後に実行）→ その後 `boundary-report` の
  `rule.eligible` を確認し、昇格するかどうかを判断し、昇格する場合は
  `config/collectors.json` / compiler を変更として記録する。

### 15.5 実行手順の記録（パス 1 で行ったこと = パス 2 の手順）

パス 1 は `collection.adapters.google_trends.boundary` のオフライン側（`verify` / `stage`）に、
承認済み MCP セッションの計測結果を capture manifest として渡す形で実行した
（spec §4.1/§4.3。ライブ計測自体は harness の外）。

1. **計測**（1 セッション、4 call、call 間に数秒の間隔。429 が出たら spec §4.2 の backoff）:

   ```python
   from collection.adapters.google_trends.mcp_session import McpStdioSession
   from datetime import datetime, timezone

   session = McpStdioSession()  # google-trends-mcp@0.1.1（MIT、キー不要・無料）
   session.start()
   try:
       for timeframe in ("today 1-m", "today 3-m", "today 12-m", "today 5-y"):
           started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
           result = session.call("interest_over_time", {"terms": ["CBX"], "geo": "JP", "timeframe": timeframe})
           finished = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
           # capture 1 件: run_id / request / started_at / finished_at / result（verbatim）
   finally:
       session.close()
   ```

   - `result` はサーバが返した形のまま（`{content: [...], isError: ...}`）入れる。整形・要約しない。
   - `run_id` は `<YYYYMMDDTHHMMSSZ>-google-trends-boundary-<timeframe slug>`
     （例: `20261015T042845Z-google-trends-boundary-1m`。slug は `today 1-m` → `1m`）。
   - manifest 全体: `capture_version: "1.0.0"` + `instrument: {kind: "mcp_session", server: "google-trends-mcp", server_version: "0.1.1"}`。
   - manifest は実行中の入力であり証拠の正本ではない（正本は採用済み run）。
     パス 1 の manifest sha256 は §15 の表に記録した。
2. **形式検証**: `python -m collection.adapters.google_trends.boundary verify --manifest <manifest.json>`
   （`format_verified=true`、全 capture parsed でなければ行列を止めて parser を更新。spec §4.4）
3. **staging**: `python -m collection.adapters.google_trends.boundary stage --manifest <manifest.json> --study cbx-search-trends`
4. **採用**: staged run ごとに `python -m collection.core.cli adopt --staged .staging/<run-id>`（L1 通過のみ catalog）
5. **評価**: `python -m validation.cli boundary-report --datasets-root datasets`（`rule.eligible` を確認）
6. 監査スナップショットの再生成（g2 / g3 / g4 / g5-legacy / g5-prov / g6-git / g7）と
   `ISS-20261015-GT-001` / 本レポートの更新。
