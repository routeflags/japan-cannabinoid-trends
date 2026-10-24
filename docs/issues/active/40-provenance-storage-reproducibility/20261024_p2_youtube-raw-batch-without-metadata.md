# Issue: YouTube の 8 化合物が raw のみ（実データは揃っている。欠けているのは記録だけ）

**ID:** ISS-20261024-YT-013  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/youtube/20261008T12*`（ローカル raw）,
`src/processing/youtube_export.py` の `PUBLISHABLE_RUNS`, `datasets/cannabinoid-raw-collection/README.md` の
「YouTube（公開分）」列, `methodology.md` §2.3  
**GitHub:** [#10](https://github.com/routeflags/japan-cannabinoid-trends/issues/10)

## 概要

`README.md` の「YouTube（公開分）」列で `raw のみ` になっている 8 化合物（THC-O / THCH / CBN / CRDH / CRDP / H4CBH / HHBD / HHCH）には、
2026-10-08 の raw が存在する。**実データ（ペイロード）は完全で、公開 7 run と同じ形をしている**。
欠けているのは **収集条件の記録**（actor・検索語・取得上限）だけである。

したがって判断の土台は実データに置く。**実データが揃っているのに記録の欠落を理由に公開集計から外すのは本末転倒**であり、
未記録の項目を limitations に明記したうえで採用するのが筋である。再取得は、記録を揃えたい場合の代替手段にすぎない
（同一クエリの再実行は非決定的なので、今ある実データを置き換える保証もない）。

## 実データ（主証拠）

raw は gitignored（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）なので Delta worktree には無く、
一次 checkout `datasets/cannabinoid-raw-collection/data/raw/youtube/`（ローカルでは旧 study 名
`cannabinoid-multi-trends`）を読み取り専用で確認した。**この worktree では `youtube-export` を実行していない**ので、
下記の `records.json` 行数は「採用すれば載る行数」の見込みであり、公開 2 表の実測ではない。

| run ディレクトリ | 語 | `records_raw.json` 行（重複込み） | ユニーク `videoId`（= `records.json` 行） | タイトルに語を含む本数（ユニーク中） |
|---|---|---:|---:|---:|
| `20261008T122515Z-youtube-hhc` | HHC | 60 | 27 | 24 |
| `20261008T122605Z-youtube-thch` | THCH | 60 | 20 | 5 |
| `20261008T122647Z-youtube-thc-o` | THC-O | 60 | 30 | 15 |
| `20261008T125306Z-youtube-h4cbh` | H4CBH | 60 | 24 | 17 |
| `20261008T125348Z-youtube-hhbd` | HHBD | 60 | 22 | 17 |
| `20261008T125428Z-youtube-hhch` | HHCH | 60 | 20 | 15 |
| `20261008T125501Z-youtube-crdp` | CRDP | 60 | 27 | 15 |
| `20261008T125544Z-youtube-crdh` | CRDH | 60 | 21 | 7 |
| `20261008T145348Z-youtube-cbn` | CBN | 60 | 24 | 18 |

実データから直接確かめられること:

- **`records.json` は `records_raw.json` の `videoId` 重複除去**であり、別の選別はしていない（両者の集合は一致し、行数差は重複のみ）。
  これは公開 7 run と同じ扱いである（例 `20261002T064739Z-youtube-cbd` は raw 100 行 → 22 本）。
- **エラーペイロードは無い**（各 run のファイルは payload 2 つのみ、`{"error": ...}` を含む文書なし）。
  取得失敗を 0 件と読み替える心配はない。
- **ペイロード形状は公開 7 run と同一**（`kind: youtube#searchResult`、`snippet` に `description` を含まない）。
  説明文（連絡先メールを含みうる項目）は元から入っていない。
- **語はペイロード自身で裏づけられる**。検索語そのものは記録されていないが、タイトルに化合物語を含む動画が
  20 本中 5〜24 本ある（用語の揺れ・英字表記の差があるため 100% にはならない）。ディレクトリ名の語と整合する。
- 9 run 合計で **215 行**、run をまたぐ重複が **41 件**あるが、これは公開済みの run 同士でも起きている
  （例: 公開 CBD run ∩ THCH run = 1 件）。重複除去は run 単位という既存の規則のままでよい。
- `snippet.timestamp`（投稿日時）は大半の項目で null（60 行中 5〜14 件のみ非 null）。README の
  「公開日は含まれない」という記載と矛盾しない。

検証コマンド（一次 checkout で実行・読み取りのみ）:

```bash
python3 - <<'EOF'
import json,glob
for d in sorted(glob.glob('datasets/*/data/raw/youtube/20261008T12*')):
    raw=json.load(open(f'{d}/records_raw.json')); flt=json.load(open(f'{d}/records.json'))
    def u(rows):
        s=set()
        for it in rows:
            i=it.get('id'); v=i.get('videoId') if isinstance(i,dict) else i
            if v or (v:=it.get('videoId')): s.add(v)
        return s
    term=d.split('-youtube-',1)[1]
    hits=sum(1 for it in flt if term.replace('-','') in ((it.get('snippet') or {}).get('title') or '').lower().replace('-','').replace(' ',''))
    print(d, len(raw), len(u(raw)), len(flt), len(u(flt)), hits)
EOF
```

## 記録側の欠け（判断には使わない。limitations に落とす）

- 9 run のうち **6 run に `run_metadata.json` が無い**。残り 3 run の `run_metadata.json` は
  `id` / `status` / 費用フィールド 1 個（AGENTS.md が禁じるため名称は書かない）の **3 キーだけの中間生成物**である。
  これは Apify の生レスポンスでも、公開 7 run の同名ファイル（`run_id` / `dataset_id` / `study_id` / `source` /
  `search_term` / `max_videos` / `record_count`）でもない。3 ファイルとも 84 バイトで、payload の 1 秒後に書かれている
  （例: payload 21:25:31、metadata 21:25:32 JST）。
- **この派生物は判断に使わない。** 実データは別に揃っているので、収集条件の欠落は記録の欠落として limitations に書けば足りる。
- 復元できない項目は **actor・取得上限（`max_videos`）・Apify dataset id**。復元できるのは Apify の run id・status と
  ディレクトリ名の日時である。`records_raw.json` が 9 run とも 60 行なのは公開 run の `max_videos: 50` 群と同じ件数だが、
  これは**推測であって記録ではない**（methodology には「未記録」と書く）。

## 何が問題か

1. **実データが揃っているのに公開集計に入っていない**（`youtube_videos.csv` は 5 化合物 + オイル 2 語の 182 行のみ）。
   観測があるのに証拠として使っていない状態で、8 化合物は YouTube 側が空白に見える。
2. その理由が「実データが無い」ではなく「記録が欠けている」ことである以上、欠落を理由に実データを捨てるのは順序が逆。
3. `README.md` の `raw のみ` は「provenance のレビュー待ち」とだけ書いており、**実データの状態（完全・未採用）**を書いていない。
4. HHC の 2 回測定（2026-10-02 の 28 本と 2026-10-08 の 27 本、共通 `videoId` 7 件）と、
   CBN の v3 由来 raw（`ISS-20261024-PRV-005` / #1）の併存が未決のまま。
5. `methodology.md` §2.3 は actor と `max_videos` を明記している。未記録の run を採用すると記載と食い違うため、
   §2.3 側に「2026-10-08 バッチは未記録」と追記する必要がある。

## 選択肢（実データに従う順）

1. **公開集計に入れる（推奨）** — 8 run を `PUBLISHABLE_RUNS` に追加し、未記録項目を limitations と §2.3 に明記する。
   `youtube_runs.csv` 7 → 15 行、`youtube_videos.csv` 182 → 370 行（+188）。HHC の重複を採るなら 397 行 / 16 run。
   観測を捨てずに済み、記録の欠落は記録側で表現できる。
2. **現状維持** — `raw のみ` のまま、README に実データの状態と採用しない理由を明記する。コード変更なし。
3. **再取得** — 記録の揃った run を作る。実データは既に完全で、同一クエリの再実行は非決定的なので、
   今の実データを置き換える保証はない。記録の完全性を最優先する場合の手段。
4. **廃棄** — 2026-10-08 の 9 run を削除する。観測を捨てる選択であり推奨しない（raw の削除は owner のみ）。

## オーナーへの質問（この 5 件への回答で決まる）

- **Q1（採用可否）**: 2026-10-08 の 8 run を公開集計に入れてよいか。推奨は「入れる」。
  影響: `youtube_runs.csv` 7 → 15 行、`youtube_videos.csv` 182 → 370 行。公開レビュー（COL-030 §4.1）の対象。
- **Q2（HHC の重複）**: 既存の 2026-10-02 run（28 本）と 2026-10-08 run（27 本、共通 7 本）をどうするか。
  ① 既存のみ公開（推奨） ② 2026-10-08 に置き換え ③ 両方公開して反復測定として注記。
- **Q3（CBN の v3 raw）**: 公開には 2026-10-08 の run を使い、v3 由来の raw（2026-10-04、#1 の削除対象）は据え置きでよいか。
  推奨は「据え置き（公開には使わない）」。
- **Q4（未記録項目の書き方）**: actor・取得上限を「未記録」として `methodology.md` §2.3 と limitations に書く形でよいか。
  推奨は「それで書く」。取得上限の推測値（50）は記録として書かない。
- **Q5（raw 内の派生物）**: 3 キーの `run_metadata.json` をどうするか。① そのまま残す（推奨。判断には使わないと記録する）
  ② 別名に改名 ③ 削除。いずれも raw を触るので owner の作業。

## 完了条件

- [ ] Q1〜Q5 の回答
- [ ] 採用する場合: `PUBLISHABLE_RUNS` 追加 + テスト更新 + 2 表の再生成 + `reproduce.py` の非再現メモ更新
      （`182 rows` / `the 7 reviewed 2026-10-02 runs`）+ `collection-summary.md` §3 の更新
- [ ] `methodology.md` §2.3 と README の「YouTube（公開分）」列が実データと一致している
- [ ] HHC の反復測定の扱いが記録されている
- [ ] 監査スナップショットの再生成
