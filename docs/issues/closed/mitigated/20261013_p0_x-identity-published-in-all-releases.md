# Issue: X の個別アカウント情報が全リリースに公開されている

**ID:** ISS-20261013-CBX-001  
**優先度:** P0 (Critical)  
**ステータス:** MITIGATED (2026-10-13)

**対象:** `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv`（削除済み）、
`datasets/x-26week-trends/analysis/x_26week_trend_report.md`、
`datasets/cbx-social-trends/analysis/cbx_data_collection_report.md`、
`publication/guide_cbx_rewrite.html`

## 概要

X の投稿本文・アカウント handle・表示名・投稿 URL を含むファイルが、少なくとも
2026-10-01 以降 **全 14 タグ / 全 14 GitHub Release に含まれたまま公開**されていた。
Release は `release: published` を契機に `datasets/` と `publication/` を含むクリーン
アーカイブを Zenodo へ送信するため、DOI 付き公開アーカイブにも含まれている。

本リポジトリは自らこの状態が望ましくないと文書化していたにもかかわらず、検査が無かった
ために阻止できなかった。

## 文書化されていた方針（実効性が無かった）

| 文書 | 日付 | 記載 |
|------|------|------|
| `docs/specs/sns-redistribution-assessment.md` §1.4 | 2026-10-01 | 「DOI アーカイブには含めるべきでない: ツイート本文 / ユーザー名 / 個別ツイート URL」 |
| `docs/data-dictionary.md` §1.1 | 2026-10-02 | 「`username` と `author_name` は個人情報を含む可能性があるため、再配布時は注意が必要」 |
| `docs/specs/validation-framework.md` §改訂 | 2026-10-13 | 人工ゲートのみで、コミット時に機械的に止める仕組みは無かった |

## 実測した公開範囲

| 項目 | 実測 |
|------|------|
| リポジトリ公開状態 | GitHub `visibility: public` |
| CSV 追加 | commit `2dae15b`（2026-10-01） |
| 含まれていたタグ | **14 / 14**（v1.5.0〜v1.12.0） |
| GitHub Releases | 14 件 |
| Zenodo | `10.5281/zenodo.23253840`（v1.12.0、**open access**）。アーカイブ内に該当 CSV を実物確認 |
| 露出した内容 | 147 件の投稿本文、55 アカウントの handle・表示名、55 件の投稿 URL |
| 他の露出箇所 | 公開ページ `publication/guide_cbx_rewrite.html` が 5 アカウントを実名でランキング表示、分析レポート 2 件が計 13 アカウントを掲載 |

## 実施した対応（前向き修正）

1. CSV を追跡から外し、非公開の `datasets/cbx-social-trends/data/private/` へ退避（`.gitignore`
   済み、 clone と CI には存在しない）。削除は `src/processing/reproduce.py` の
   `WITHDRAWN` に理由・代替成果物・露出期間とともに記録（黙って消さない）。
2. 公開ページと分析レポートのアカウント名を疑似名化（本文書内の通し記号 `アカウントA…`）。
   文書間で対応が取れないようにして、リンクによる再識別を防いでいる。
3. 再発防止ゲート `src/validation/x_identity.py` を追加。追跡ファイルの識別列・
   投稿パーマリンク・既知 handle（ソルト付きダイジェスト照合）を検査し、CI と
   pre-commit で fail させる。

## 残る露出（未決）

前向き修正は再配布を止めるが、**既公開の 14 Release と Zenodo アーカイブは残る**。
AGENTS.md は「公開済みリリースを書き換えて隠さない」と定めているため履歴書き換えは
方針と矛盾し、fork/clone/Zenodo に残るため効果も限定的である（ただし後述のとおり
B は別の理由で実施した）。

残る選択肢への判断（2026-10-13）:

- **A → 実施済み**: 前向き修正。
- **B → 実施済み**: 履歴書き換え + force-push。AGENTS.md との矛盾は、既公開リリースの
  「内容の訂正」ではなく「個人情報の除去」であり、除去後の内容は同一であることを
  検証してから push した（`docs/specs/validation-framework.md` §21）。
- **C → 不要と判断**: GitHub Release 資産の差し替えと Zenodo への制限・削除依頼は
  行わない。GitHub Release はアセット 0 件で、タグ書き換えにより自動生成のソース
  アーカイブはクリーンになった。**Zenodo の既公開アーカイブ
  （`10.5281/zenodo.23095153` = v1.7.0、`10.5281/zenodo.23253840` = v1.12.0。
  いずれも該当ファイルを含むことを実物確認済み）は残るが、これは受容済みの残存
  リスクとして記録する。**

## 次のアクション

- [ ] 新リリースに CHANGELOG エントリを付ける（CHANGELOG の先頭見出しは最新タグと一致
      させる必要があるため、リリース作業と同時に行う）。
- [x] Zenodo への制限依頼 → **不要と判断**（2026-10-13）。既公開アーカイブの残存を受容。
- [ ] 閲覧者が本件を追えるように、公開ページから本 issue へ言及するか判断する。

---

## 履歴の書き換え（B）— 2026-10-13 実施

前向き修正（A）だけでは、作業ツリーから消えるだけで git 履歴からは取り出せていた
（`git show bc651ca:<path>` で 148 行が取得できる状態）。そこで履歴そのものを書き換えた。

### 実施方法

`git filter-repo` を bare mirror（`/tmp/jct-b.git`）に対して実行し、検証してから
force-push した。作業中の clone を直接書き換えず、mirror で検証してから push する手順を
取っている。

| 手順 | 内容 |
|------|------|
| 1 | **54** 件の handle を全履歴で `[x-account]` に置換（`--replace-text`。内容ベースなので旧パスにも効く） |
| 2 | 投稿 CSV の**全パス変種**を全履歴から除去（`--invert-paths`） |
| 3 | 過去の logbook を全履歴から除去 |

### 履歴走査で判明した対象（作業ツリーのゲートでは見えないもの）

| パス | 備考 |
|------|------|
| `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv` | 55 handle + 36 表示名 |
| `datasets/cbx-x-trends/data/processed/x_cbx_202608_summary.csv` | study 改名前の同一ファイル |
| `data/processed/x/x_cbx_202608_summary.csv` | さらに古いパス |
| `artifacts/daily/20261001_logbook.md` | 14 handle。**HEAD に存在しない**（v1.5.1 で削除済み）ため、作業ツリーの検査では原理的に検出できない |
| `publication/guide_cbx_rewrite.html`、分析レポート 2 件 | 内容置換で除去 |

改名・移動を経たファイルは複数パスを持つため、1 パスだけ除去すると別パスに残る。実際に
1 回目の除去では `cbx-x-trends` 側と `data/processed/x/` 側が残り、追加の除去が必要だった。

### 意図的に残したもの

1 件の handle は書き換え対象から除外した。YouTube の動画タイトル（および 26 週
レポートの旧リビジョン）に現れるもので、「YouTube は現状維持」というメンテナ判断に
従っている。実名はここに書かない（このゲート自身が検出してしまうため）。対象は
`src/validation/x_identity.py` の `ACKNOWLEDGED` にダイジェストで記録している。
書き換え後の全 1,211 blob を走査した結果、handle を含む blob はこの 1 handle のみで、
表示名を含む blob も同一の 1 件だけであった。

### 復旧手段

書き換え前の全 ref を `/tmp/jct-before-b.bundle`（約 1.6 MB）に保存した。内容を確認して
問題がなければ削除する。**この bundle には PII が含まれる**ため、残す場合は取り扱いに
注意すること。

### 副作用

- 全コミット SHA が変わった。既存のリンク・参照は無効になる。
- 14 タグも書き換えたため、**DOI が参照するスナップショットとリポジトリは一致しなくなった**。
- 既存の clone / fork には旧履歴が残る。手元のコピーは再 clone、または
  `git fetch --tags --force` のうえ `git reset --hard <origin>/main` が必要。
- GitHub Release のアーカイブと Zenodo の DOI アーカイブは**残る**（削除・制限は C の範囲で未実施）。
