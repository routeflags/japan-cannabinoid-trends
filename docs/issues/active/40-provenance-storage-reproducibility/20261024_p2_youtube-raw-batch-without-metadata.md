# Issue: YouTube 2026-10-08 バッチを再現可能な手順で集計へ統合する

**ID:** ISS-20261024-YT-013  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/cannabinoid-raw-collection/data/raw/youtube/20261008T12*`（ローカル raw）,
`src/processing/youtube_export.py` の `PUBLISHABLE_RUNS`, `datasets/cannabinoid-raw-collection/README.md` の
「YouTube（公開分）」列, `methodology.md` §2.3  
**GitHub:** [#10](https://github.com/routeflags/japan-cannabinoid-trends/issues/10)

## 概要

2026-10-08 の YouTube raw 9 run（HHC / THC-O / THCH / CBN / CRDH / CRDP / H4CBH / HHBD / HHCH）は実在し、
ペイロードは既存のエクスポート処理で読める。owner はこの 9 run を既存の公開集計へ統合し、HHC の 2 run は反復観測として両方残すことを承認した。

判断と実装の基準は、収集時に記録が揃っているかではなく、**実データに対して同じ処理を何度実行しても同じ成果物になること**とする。
収集条件が残っていない項目（actor・検索語・取得上限）は「未記録」と記載し、ディレクトリ名や行数から補わない。
再取得は要件にしない。raw は不変のまま、成果物を作る処理とその規則をコード・methodology に明記する。

## 用語: run と「9 run」の定義

- **run** = `data/raw/youtube/<run-id>/` の 1 ディレクトリ。`run-id` は `<UTC>Z-youtube-<slug>` で、1 run = 1 回の検索実行（1 検索語・1 時点）。
  エクスポートは run 単位で行い、`youtube_runs.csv` の 1 行が 1 run に対応する。
- **「9 run」= エクスポートの allowlist（`PUBLISHABLE_RUNS`）に未登録の 9 run** を指す。**新規収集ではない**。
  いずれも 2026-10-08 に収集済みで、一次 checkout の `data/raw/youtube/` に存在する。
  「新規」は「新しく集めた」ではなく「**集計に新しく加える**」の意味である。
- 9 の内訳は **8 化合物 + HHC の反復 1 run**。HHC は 2026-10-02 の公開 run（`20261002T064850Z-youtube-hhc`、28 行）とは別 run として残す。

| # | run-id | 語 | `records.json` 行（run 内ユニーク `videoId`） |
|---|---|---|---:|
| 1 | `20261008T122515Z-youtube-hhc` | HHC（反復） | 27 |
| 2 | `20261008T122605Z-youtube-thch` | THCH | 20 |
| 3 | `20261008T122647Z-youtube-thc-o` | THC-O | 30 |
| 4 | `20261008T125306Z-youtube-h4cbh` | H4CBH | 24 |
| 5 | `20261008T125348Z-youtube-hhbd` | HHBD | 22 |
| 6 | `20261008T125428Z-youtube-hhch` | HHCH | 20 |
| 7 | `20261008T125501Z-youtube-crdp` | CRDP | 27 |
| 8 | `20261008T125544Z-youtube-crdh` | CRDH | 21 |
| 9 | `20261008T145348Z-youtube-cbn` | CBN | 24 |
| | **合計** | | **215** |

- 集計後は 7 + 9 = **16 run**。動画行は 182 + 215 = **397 行**（ただしこの 9 run の外にある
  `20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01`（v3 由来、50 行）は含めない。後述の別途確認事項）。
- 「run 内重複排除」= 1 run の中の同じ `videoId` を 1 行に畳む（既存の規則）。
  「run 間重複保持」= 別 run に同じ `videoId` が現れても畳まず、それぞれの `run_id` で残す（HHC の 2 run など）。
- 「安定した再実行」= 同じ raw と同じコードで再実行したとき、行の集合だけでなく並び順も一致する（`videos.sort` のキーで固定）。

## 実データ（主証拠）

raw は gitignored（`.gitignore` の `**/data/raw/*`、例外は `google_trends`）なので Delta worktree には無く、
一次 checkout `datasets/cannabinoid-raw-collection/data/raw/youtube/`（ローカルでは旧 study 名
`cannabinoid-multi-trends`）を読み取り専用で確認した。追跡中の CSV は現行の 7 run / 182 行のままであり、
2026-10-08 バッチを追加した成果物はまだ作業対象に反映していない。

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

## 来歴の制約（再現処理の条件にはしない）

- actor・検索語・取得上限は確認できる記録が無いため「未記録」とする。`records_raw.json` の行数や run ディレクトリ名から
  収集パラメータを推定して記録しない。
- 6 run には `run_metadata.json` が無く、残り 3 run の同名ファイルも収集条件を記述していない。raw は変更・改名・削除せず、
  いずれの `run_metadata.json` もエクスポート手順の入力根拠にしない。
- エクスポートで使う検索語が不明な run は `youtube_runs.csv` の `search_term` を空欄にする。run ID は観測の識別に使うが、
  未記録の検索条件を復元したものとは扱わない。

## owner が決定したこと

- 2026-10-08 の **9 run 全件**（8 化合物のうち HHC を含む）を、既存の 7 run と同じ YouTube 集計へ統合する。
- HHC は 2026-10-02（28 動画）と 2026-10-08（27 動画）を別 run として両方残す。共通 `videoId` 7 件も run をまたいで統合・削除せず、反復観測として識別可能にする。
- actor・検索語・取得上限が未記録であることを methodology と limitation に明記する。推測で埋めない。
- raw は不変とし、3 キーの `run_metadata.json` もそのまま残す。名前変更・削除はしない。
- 同じ raw と同じ exporter から再実行したとき、同じ run 別行・同じ順序の CSV が得られることを実装要件とする。videoId の重複除去は run 内だけで行う。

### CBN の YouTube Data API v3 run（別途確認が必要）

owner は v3 由来 CBN run を「統合」と回答した。一方、一次 checkout の
`20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/records.json` は 50 件すべてが
`is_cannabinoid_related: false` であり、CBN の観測としては統合できない内容である。したがって本 issue の成果物には含めない。
「統合」が raw の保管・一覧への統合を指すのか、無関係な 50 件も cannabinoid 集計へ含める指示なのか、owner の確認を要する。
この決定は `ISS-20261024-PRV-005`（#1）の CBN raw 削除決定とも整合させる。確認までは当該 raw に手を加えない。

## 完了条件

- [x] 上表の 9 run を example に、allowlist 指定 run のみを run 内 `videoId` 重複排除・安定ソートで出力する自動テストを追加する。
- [x] 同一 raw での繰り返し実行が同一 CSV を生成し、run 間で同じ動画があっても別観測として保持する。
- [x] 上表の 9 run（2026-10-08 収集・未登録）を追加し、`youtube_runs.csv` 16 run / `youtube_videos.csv` 397 行になることを検算する（一覧外の v3 由来 CBN run は含めない）。
- [x] `search_term` など未記録項目を推測せず空欄で表し、methodology に未記録の収集条件と処理方法を記載する。
- [x] README・`collection-summary.md`・`reproduce.py` の記述を成果物の実測に合わせ、監査スナップショットを再生成する。
- [ ] CBN v3 run の扱いについて owner の確認を得て、#1 と本 issue の方針を一致させる。
