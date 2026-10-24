# Issue: YouTube の 8 化合物が raw のみ（2026-10-08 バッチの来歴が未記録）

**ID:** ISS-20261024-YT-013  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/youtube/20261008T12*`（ローカル raw）,
`src/processing/youtube_export.py` の `PUBLISHABLE_RUNS`, `datasets/cannabinoid-raw-collection/README.md` の
「YouTube（公開分）」列, `methodology.md` §2.3  
**GitHub:** [#10](https://github.com/routeflags/japan-cannabinoid-trends/issues/10)

## 概要

`README.md` の「YouTube（公開分）」列で `raw のみ` になっている **8 化合物（THC-O / THCH / CBN / CRDH / CRDP / H4CBH / HHBD / HHCH）** には、
**2026-10-08 のローカル raw が実在する**。ただしこのバッチは **収集条件（actor・`search_term`・`max_videos`）が記録されておらず**、
`staging-declaration-v1` を作れないため採用できない。`PUBLISHABLE_RUNS` の allowlist にも載っていないので、
公開集計（`youtube_videos.csv` 182 行 / `youtube_runs.csv` 7 run）には入っていない。

すなわち `raw のみ` の意味は **「取得済みだが来歴が未記録で採用できない」** であって「未収集」ではない。
`ISS-20261023-YT-010`（#6）は 8 語を「未収集」として再収集を決めているが、その前提はこの実測で置き換わる
（結論として再収集を推奨する点は同じ。理由が「データが無い」から「来歴が無い」に変わる）。

## 実測（2026-10-24、一次 checkout のローカル raw）

raw は gitignored（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）なので Delta worktree には無く、
一次 checkout `datasets/cannabinoid-raw-collection/data/raw/youtube/`（ローカルでは旧 study 名
`cannabinoid-multi-trends`）を読み取り専用で確認した。**この worktree では `youtube-export` を実行していない**ので、
下記の `records.json` 行数は「採用すれば載る行数」の見込みであり、公開 2 表の実測ではない。

そのディレクトリには 25 run があり、うち 2026-10-08 の 9 run が該当する。

| run ディレクトリ | 語（ディレクトリ名から） | `records_raw.json` 行 | `records.json` 行（ユニーク `videoId`） | `run_metadata.json` |
|---|---|---:|---:|---|
| `20261008T122515Z-youtube-hhc` | HHC | 60 | 27 | 3 項目だけの中間生成物 |
| `20261008T122605Z-youtube-thch` | THCH | 60 | 20 | 同上 |
| `20261008T122647Z-youtube-thc-o` | THC-O | 60 | 30 | 同上 |
| `20261008T125306Z-youtube-h4cbh` | H4CBH | 60 | 24 | **なし** |
| `20261008T125348Z-youtube-hhbd` | HHBD | 60 | 22 | **なし** |
| `20261008T125428Z-youtube-hhch` | HHCH | 60 | 20 | **なし** |
| `20261008T125501Z-youtube-crdp` | CRDP | 60 | 27 | **なし** |
| `20261008T125544Z-youtube-crdh` | CRDH | 60 | 21 | **なし** |
| `20261008T145348Z-youtube-cbn` | CBN | 60 | 24 | **なし** |

- 「3 項目だけの中間生成物」の中身は `id` / `status` / **費用フィールド 1 個**（AGENTS.md が禁じるため名称はここに書かない）の 3 キーだけで、
  **Apify の生レスポンスでも、この study の `run_metadata.json` 仕様でもない**。
  - Apify の actor-run オブジェクトは `defaultDatasetId` / `startedAt` / `finishedAt` / `usage` など多くのキーを持つ
    （`.github/skills/apify-youtube-search/SKILL.md` が `.data.defaultDatasetId` と `.data | {status, …}` の投影例を使っており、応答に多くのキーがあることの証拠になる）。
    3 キーはその応答から必要な項目だけを抜き出した投影であり、**中間生成物（派生物）**である。
  - 3 ファイルとも **84 バイト**で、`records_raw.json` / `records.json` の書き込みの **1 秒後**に書かれている
    （例 `20261008T122515Z-youtube-hhc`: payload 21:25:31、metadata 21:25:32 JST）。収集作業の中で
    「payload を保存 → status を 3 項目だけ保存」という順に書かれたことを示す。
  - この 3 キーを書き出すコードはリポジトリに無い（`src/` `scripts/` `config/` を費用フィールド名で検索して 0 件。
    history の `-S` 検索でも該当なし）。当時の実行スクリプトは残っていない（`tmp/` の同種スクリプト
    `gt_phase_a_save.mjs` が `JSON.stringify(..., null, 2) + "\n"` で同じ体裁の metadata を書いており、
    追跡されない一時スクリプトで書かれたとみられるが、そのファイル自体は現存しない）。
  - **`run_metadata.json` という名前が、公開 7 run の同名ファイル（`run_id` / `dataset_id` / `search_term` /
    `max_videos` / `record_count`）と衝突している**ため、収集記録と誤読しやすい。実際に本 issue の初版でも
    「Apify run オブジェクトのみ」と書き違えた。
  - **`search_term` / `max_videos` / `dataset_id` / `record_count` を持たない**ので、この 3 ファイルからは
    収集条件を復元できない。復元できるのは Apify の run id・status と、ディレクトリ名の日時だけである。
- 3 キーのうち 1 つは AGENTS.md「Scope Exclusion: Cost」が禁じる費用フィールドである。raw は未追跡なので現状は追跡物に混入していないが、
  来歴を写す作業をする場合はこの項目を転記しない（本記録にも名称を書かない）。
- ペイロード形状は公開 7 run と同一（`kind: youtube#searchResult`、`snippet` に `description` を含まない）。
  `records_raw.json` はページング重複を含み、`records.json` が `videoId` でユニーク化したもの（両者の差分は重複のみで、
  `records.json` は `records_raw.json` の部分集合）。
- `records_raw.json` が 9 run とも 60 行なのは、公開 run の `max_videos: 50` 群（CBG / HHC / THCV / オイル 2 語）と同じ件数である。
  **同設定の可能性は高いが、記録ではない。**
- HHC は公開済み run（`20261002T064850Z-youtube-hhc`、28 動画）と未記録 run（2026-10-08、27 動画）の 2 回測定になる。
- このバッチを扱った記録はリポジトリに無い（`docs/` と `metadata/provenance/declarations/` を検索して 0 件。
  宣言文書は 2026-10-15 の youtube-consistency 用 1 件のみ）。収集経路の日誌も残っていない。

検証コマンド（一次 checkout で実行・読み取りのみ）:

```bash
ls -1 datasets/cannabinoid-raw-collection/data/raw/youtube/            # ローカルでは旧 study 名のディレクトリ
python3 - <<'EOF'
import json,glob
for d in sorted(glob.glob('datasets/*/data/raw/youtube/20261008T12*')):
    try: meta=json.load(open(f'{d}/run_metadata.json')); keys=sorted(meta)
    except OSError: keys=None
    def uniq(p):
        out=set()
        for it in json.load(open(p)):
            i=it.get('id'); v=i.get('videoId') if isinstance(i,dict) else i
            if v: out.add(v)
        return len(json.load(open(p))), len(out)
    print(d, uniq(f'{d}/records_raw.json'), uniq(f'{d}/records.json'), keys)
EOF
```

## 採用した場合の影響（見込み）

| 成果物 | 現行 | 8 語を採用 | HHC の重複も採用 |
|---|---:|---:|---:|
| `youtube_runs.csv` | 7 行 | 15 行 | 16 行 |
| `youtube_videos.csv` | 182 行 | 370 行（+188 = 30+20+24+21+27+24+22+20） | 397 行（+27） |

2 表の再生成（`python -m processing.cli youtube-export`）は raw を要求するため、raw を持つ checkout でしか行えない。
同時に `src/processing/reproduce.py` の非再現メモ（`182 rows` / `the 7 reviewed 2026-10-02 runs`）と
`collection-summary.md` §3・README の「YouTube の収集と追跡」節の更新が要る。

## 何が問題か

1. raw は存在するのに、収集条件を記録した文書が無い。`staging-declaration-v1` は `unknown` を持たないので、
   actor・`search_term`・`max_videos` を確認できない限り宣言できない（AGENTS.md: 未確認値はブロッカー）。
2. したがって採用も再宣言もできず、raw はローカル証跡のままになる。データ成果物の勘定に入らない。
3. `methodology.md` §2.3 は YouTube の収集条件（actor と `max_videos`）を明記している。来歴不明の run を公開すると
   この記載と実データが食い違う。
4. HHC の 2 回測定、CBN の v3 由来 raw（`ISS-20261024-PRV-005` / #1）との関係が未決のまま併存している。
5. README の `raw のみ` は「provenance のレビュー待ち」とだけ書いており、**レビューしても採用できない理由**（来歴の欠落）に触れていない。
6. raw の中に **`run_metadata.json` という名前の中間生成物**（Apify 応答から 3 項目だけ抜いたもの）が 3 run 分残っており、
   収集記録と課読しやすい。raw は不変なので、改名・削除は owner の判断が必要。

## 選択肢（owner 判断）

1. **再取得** — `ISS-20261023-YT-010`（#6）の決定どおり 8 語を標準経路で収集し、宣言可能な run を作る。
   2026-10-08 の raw はローカル証跡として残し、証拠には使わない。来歴の欠落は raw を編集して直せないため、最も筋が通る。
   Apify トークンの配置が前提。
2. **採用レビュー** — 2026-10-08 の 8 run を `PUBLISHABLE_RUNS` に追加して公開する。記録できない項目は「未記録」として
   limitations に明記する。トークン不要で即日可能だが、§2.3 の記載との整合を別途とる必要がある。
3. **現状維持** — `raw のみ` のまま、理由を README に明記する。#6 の収集が済めば置き換わる。
4. **廃棄** — 2026-10-08 の 9 run を削除する。raw の削除は破壊的操作であり owner のみが実行できる。

推奨は 1。8 語の収集は #6 で既に決まっており、本 issue の実測はその決定の理由を「データが無い」から
「採用できる来歴が無い」へ修正する。トークン配置まで待てない場合のみ 2 を選び、記録できない項目を limitations に落とす。

## 決定依頼

- D1: 1（再取得）/ 2（採用レビュー）/ 3（現状維持）/ 4（廃棄）
- D2: HHC の 2 回測定（28 動画と 27 動画）の記録方法
- D3: CBN の v3 raw（#1）と 2026-10-08 raw の関係
- D4: README の `raw のみ` に「来歴未記録のため採用できない」と書くか
- D5: 3 run 分の `run_metadata.json`（3 キーの中間生成物）をどう扱うか。raw は不変なので、
  ① そのまま残し本記録で注記する、② 別名に改名する（例 `apify_status.json`）、③ 削除する。いずれも owner の目の届く作業になる。

## 完了条件

- [ ] D1 の決定
- [ ] 決定に沿った処理（再取得なら 8 run の収集と宣言 → `make stage` / `make adopt-all` → provenance レビュー。
      採用なら `PUBLISHABLE_RUNS` 追加 + テスト更新 + 2 表の再生成 + `reproduce.py` のメモ更新）
- [ ] README の「YouTube（公開分）」列と `methodology.md` §2.3 が実データと一致している
- [ ] HHC の反復測定の扱いが記録されている
- [ ] 監査スナップショットの再生成
