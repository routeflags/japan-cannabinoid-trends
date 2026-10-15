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
