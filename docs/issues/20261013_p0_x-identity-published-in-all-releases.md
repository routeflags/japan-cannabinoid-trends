# Issue: X の個別アカウント情報が全リリースに公開されている

**ID:** ISS-20261013-CBX-001  
**優先度:** P0 (Critical)  
**ステータス:** MITIGATED (前向き修正済み。既公開分の扱いは未決)  
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
AGENTS.md は「公開済みリリースを書き換えて隠さない」と定めているため、履歴書き換えは
方針と矛盾するうえ、fork/clone/Zenodo に残るため効果も限定的である。

残る選択肢:

- **A（実施済み）**: 前向き修正 + CHANGELOG + 新リリース。
- **C（未実施）**: GitHub Release 資産の差し替えと、Zenodo へのプライバシー理由による
  制限・削除依頼。Zenodo はレコード単位でファイルを差し替えられず、サポート依頼が必要。
- **B（非推奨）**: 履歴書き換え + force-push。全 commit SHA と DOI 参照が無効になり、
  fork/clone には残る。

## 次のアクション

- [ ] 新リリースに CHANGELOG エントリを付ける（CHANGELOG の先頭見出しは最新タグと一致
      させる必要があるため、リリース作業と同時に行う）。
- [ ] Zenodo への制限依頼の可否を判断する。
- [ ] 閲覧者が本件を追えるように、公開ページから本 issue へ言及するか判断する。
