# Issue: Apify クラウド側の実行記録・dataset ID が未取得

**ID:** ISS-20261015-PRV-013  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `config/collectors.json`（`x-apify-twitter-search` / `youtube-apify-scraper` / `youtube-apify-search` / `tiktok-apify-search` ほか）, `datasets/*/data/raw/**`, `docs/specs/validation-framework.md` §18.3

## 概要

Apify クラウド側の証拠（actor run ID・dataset ID・実行時の input・開始終了時刻）は
リポジトリに保存されていない。このため X / YouTube の旧 run の実行条件は引き続き `unknown`
であり、2026-10-14 にダウンロードされた YouTube dataset の CSV も、どの run の出力かは
ファイル名以上の根拠を持たない。

## 確認された観測

- `collector.version` は `unknown`、capability は全項目 `unknown`（4 collector）。
- 2026-10-14 のダウンロード（`~/Downloads/dataset_youtube-scraper_*.csv` 7 件）には
  run ID / dataset ID が含まれず、CSV 自身には `input`（検索クエリ）のみがある。
- `datasets/youtube-consistency/data/trends.db` の `runs.apify_dataset_id` が唯一の
  候補だが、Git 管理外のローカル DB であり CI から参照できない。

## 影響

- 収集条件（maxResults / pagination / retry / 実行時刻）を契約の形で記録できない。
- 同一クエリの反復収集を区別する情報が不足し、非決定性の評価が人手に依存する。

## 対応方針

- 取得依頼リスト（run ID / dataset ID / input / 開始・終了時刻）を作る。
- 取得元（Apify コンソール / API）と権限を確認し、**推測で埋めない**（欠損は欠損として記録）。
- 取得できた証拠は evidence registry に登録し、collector の capability 昇格判断に使う。

## 完了条件

- [x] 取得依頼リストの作成
- [ ] 取得した証拠の登録（証拠ハッシュの扱いを含む）
- [ ] capability 昇格判断（昇格しない項目はその理由を記録）

## 実装メモ（2026-10-15、OPEN のまま）

オフラインの要求リスト・マイルストーンのみ実装し、クラウド証拠自体は未取得
のため本 issue は OPEN のまま残す。外部 API は一切呼んでいない。

- 要求リスト: `metadata/provenance/apify-cloud-evidence-requests.json`
  （`20261015-youtube-csv-adoption.json` の 6 run を列挙。各 run に
  actor run ID / dataset ID / actor input / started / finished / status /
  evidence source の 7 項目を持ち、`pending`（宣言から転記・裏付け待ち）か
  `missing`（欠損・null のまま）で記録。`actor_input` と `evidence_source`
  は全 run で `missing`。値は宣言の転記のみで捏造なし）
- 検証モジュール: `src/validation/apify_evidence.py`
  （要求 run が宣言と完全一致すること、`missing` の値が null であること、
  非 null 値が宣言と一字一句一致すること、evidence_source に URL を捏造
  しないことを検査。read-only・offline）
- 契約テスト: `tests/validation/test_apify_evidence.py`（8 件。
  collector の capability が `unknown` / `unverified` のままであることも固定）
- `config/collectors.json` は未変更（capability 昇格なし）。
- 検証: `python3 -m pytest tests/validation/test_apify_evidence.py -q`（8 passed）

残りのオーナー作業: Apify Console / API で各 run の actor input と
開始・終了・status の裏付けを取り、取得時の URL・取得方法・取得時刻を
evidence_source として記録した上で evidence registry へ登録すること。
登録後に capability 昇格の要否を判断する。

## 実装メモ（2026-10-15、OPEN のまま・クラウド証拠は未取得）

この turn でもクラウド証拠は取得できなかった。`APIFY_TOKEN` /
`APIFY_API_TOKEN` のいずれも環境に存在しないため、Apify API は一切
呼ばず、live 収集・actor 起動・dataset 変更も行っていない。捏造なしで
埋められる追加の committed 証拠もないことを確認した：actor run ID /
dataset ID が現れるのは宣言・要求リスト（転記）・旧 issue の対応表のみで、
`actor_input` 全文（特に `dateFilter` 等）は CSV の `input` 列（keyword
のみ）にも宣言にも存在せず、Input タブの取得が必須である。
`config/collectors.json` は未変更（capability 昇格なし）。

代わりに offline の guardrail を再現可能な形にした：

- 報告関数: `src/validation/apify_evidence.py` の `audit_apify_evidence`
  （read-only・offline。要求リストと宣言だけから blocked 状態を導出。
  `violations` が空 = 誠実、`cloud_evidence_obtained` /
  `collector_promotion_allowed` は全 required field が `observed` になるまで
  `False`。`actor_input` 等の宣言に対応物のない field は `observed` 化
  しようとしても拒否される）
- CLI: `PYTHONPATH=src python3 -m validation.cli audit-apify-evidence`
  （`--requests` / `--declaration` は既定で committed 文書を指す。exit 0 は
  「誠実」であって「完了」ではない。違反時のみ exit 1）
- 契約テスト: `tests/validation/test_apify_evidence.py`（12 件。blocked
  内訳 30 pending / 12 missing / 0 observed と promotion 不可を固定）
- 検証: `python3 -m pytest tests/validation/test_apify_evidence.py -q`
  （12 passed）、`audit-apify-evidence --format json`
  （violations 0 件、`cloud_evidence_obtained=false`）

### Blocked チェックリスト（`audit-apify-evidence` の出力と同一）

6 run × 7 field：`pending` 30 件（宣言から転記・裏付け待ち）、
`missing` 12 件（取得必須・null のまま）、`observed` 0 件。

- 全 6 run 共通: `pending` = `actor_run_id` / `apify_dataset_id` /
  `started_at` / `finished_at` / `status`（宣言値の裏付け待ち）、
  `missing` = `actor_input` / `evidence_source`（repo 内に値なし）。
- 対象 run: `20261010T141947Z` / `20261010T143429Z` /
  `20261010T144421Z` / `20261010T145727Z` / `20261010T164915Z` /
  `20261011T191900Z`（いずれも `-youtube-youtube-consistency`）。
  actor run ID・dataset ID の転記値は
  `metadata/provenance/apify-cloud-evidence-requests.json` を正とする
  （ここには書き写さない）。

### オーナー作業手順（残り全部）

1. トークンを用意する。ファイルには書かず、環境変数 `APIFY_TOKEN` に
   設定する（`export APIFY_TOKEN=...`。出力・ログへの表示禁止）。
2. 読み取り専用で取得する（live 収集・actor 起動・dataset の変更や削除は
   禁止）。Apify Console の Runs 一覧で actor `h7sDV53CddomktSi5`
   （`youtube-apify-scraper`）の 6 run を開くか、runs API を GET で参照し、
   各 run について `actor_input` 全文（`dateFilter` を含む）と
   `started_at` / `finished_at` / `status` を、要求リストの転記値と突合する。
3. 突合できた run から、`evidence_source`（参照した console URL または
   API endpoint・取得方法・取得時刻）と共に evidence registry へ登録する。
   推測で埋めない。欠損は欠損のまま残す。
4. 登録後に capability 昇格の要否を判断する（昇格しない項目は理由を記録）。
5. 全 required field が `observed` になり `audit-apify-evidence` が
   `cloud_evidence_obtained=true` を返したときに初めて完了条件を満たす。
   それまでは本 issue を OPEN のまま残す。
