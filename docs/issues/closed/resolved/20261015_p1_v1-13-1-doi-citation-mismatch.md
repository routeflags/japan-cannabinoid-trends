# Issue: v1.13.1 の配布物内引用 DOI が公開済み Zenodo version DOI と一致しない

**ID:** ISS-20261015-REL-015  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**検出日:** 2026-10-15  
**対象:** `v1.13.1`、`CITATION.cff`、`metadata/datapackage.json`、`README.md`、`publication/guide_cbx_rewrite.html`

## 概要

公開済み `v1.13.1` の GitHub Release は Zenodo version DOI
[`10.5281/zenodo.23390595`](https://doi.org/10.5281/zenodo.23390595) を示す一方、同じ
タグで配布済みの引用・データパッケージ・公開ページは旧 concept DOI
`10.5281/zenodo.23253840` を `v1.13.1` の DOI として示している。

このため、配布アーカイブを取得してその引用指示に従う利用者は、今回のリリースではない
記録を引用する。`audit-publication` はリポジトリ内宣言同士の一致（PC-1）だけを確認する
ため、外部で確定した version DOI との不一致を検出できなかった。

## 確認された観測

- GitHub Release `v1.13.1` の release notes は DOI
  `10.5281/zenodo.23390595` を記載し、添付アーカイブの SHA-256 は
  `0c8dd2ab5062ef3fb3cb648634667b400ea0fc20dd074f418b76fc16ffc3884b`。
- Zenodo record `23390595` は published で、metadata DOI は
  `10.5281/zenodo.23390595`、concept DOI は `10.5281/zenodo.23390594`。
- `v1.13.1:CITATION.cff` の `identifiers[doi]` と
  `preferred-citation.doi` は `10.5281/zenodo.23253840`。
- `v1.13.1:metadata/datapackage.json` のトップレベル `doi` と `citation` 内 DOI、
  `README.md` の DOI badge、`publication/guide_cbx_rewrite.html` の DOI も
  `10.5281/zenodo.23253840`。
- `bash scripts/validation/validate-version-sync.sh --json` を 2026-10-15 に実行すると、
  DOI 不一致 6 件（PASS 7 / WARN 1 / FAIL 6）となる。

## 影響

- `v1.13.1` の永続識別子を引用メタデータから再現できない。
- GitHub Release、Zenodo、アーカイブ内メタデータが同一リリースを指すという出荷契約が破れる。
- 既に公開済みのタグと Zenodo record は不変であり、既存アーカイブを後から訂正できない。

## 原因

リリースアーカイブを作成・タグ付けした後に Zenodo workflow が新規 deposition を作成して
DOI を確定する設計である。予約 DOI または既存 concept DOI をリリース準備段階で確定して
いないため、アーカイブ内メタデータへ今回の DOI を入れられない。

## 対応方針

1. `v1.13.1` を書き換えず、訂正内容を含む新しい patch release を作成する。
2. Zenodo の version DOI を release preparation の前に予約し、または既存の正しい
   concept DOI 配下で version を作成する。
3. 予約／確定済み DOI を `CITATION.cff`、`metadata/datapackage.json`、README badge、
   publication citation、release metadata に同じ意味で反映してからアーカイブを作る。
4. version DOI・concept DOI のどちらを各フィールドが表すかを明示し、`audit-publication`
   または release gate が GitHub Release/Zenodo の実値との不一致を失敗として扱うようにする。

## 完了条件

- [ ] 新しい公開リリースのアーカイブ内すべての引用先が、そのリリースの DOI 方針と一致する。
- [ ] `validate-version-sync.sh` が対象タグ・GitHub Release・Zenodo record を基準に FAIL 0。
- [ ] CI またはリリース前ゲートで、アーカイブ内 DOI と公開予定 Zenodo DOI の不一致を検出する。
- [ ] `v1.13.1` は履歴として保持し、訂正の関係と制約を新しい release notes に明記する。

---

## 解決記録（2026-10-15）

v1.13.1 の不整合を、**公開済みリリースは書き換えず v1.13.2 で訂正**した。

### 即時訂正

- 全引用先（`CITATION.cff` / `metadata/datapackage.json` / README badge /
  methodology / guide / 全 research ページ）の DOI を、削除済み concept
  `10.5281/zenodo.23253840`（410 Gone）から、存続する series concept
  `10.5281/zenodo.23390594` へ付け替え。
- publication envelope の hash を再固定し、`gate-publication` は
  research-cbx / guide-cbx-rewrite とも SUPPORTED。

### 恒久対策（機械強制）

- `scripts/validation/check-release-archive.py`（+ importable module
  `src/validation/release_archive_check.py`、tests 5 件）を新設。
  リリース workflow は clean archive 作成後にアーカイブ内 `CITATION.cff` /
  `metadata/datapackage.json` / README の version・concept DOI を検証し、
  不一致ならアーカイブを Zenodo に送る前に失敗する（REL-015 の再発防止）。
- `scripts/release/publish-zenodo.py` を新設し、inline shell の Zenodo API
  呼び出しを置換。concept record に `newversion` で公開するため series
  concept DOI はリリースをまたいで固定。公開後に `--expect-concept-doi` で
  保存済み concept DOI を照合し、不一致なら失敗する。
- `scripts/validation/validate-version-sync.sh` の Zenodo 検索を、旧タイトル
  固定クエリから `CITATION.cff` の concept DOI による `conceptrecid:` 検索へ変更。
- `docs/specs/release-process.md` と `.github/skills/release-zenodo/SKILL.md`
  に新フロー（DOI はタグ前に concept 固定 → workflow が newversion 公開 →
  アーカイブ内 DOI を workflow が検証）を反映。
- 旧 v1.5.x〜v1.13.0 レコードは削除済み（410）。引用は series concept
  `10.5281/zenodo.23390594` を使う。

v1.13.1 は履歴として保持し、GitHub Release notes に訂正関係を記載する。

### 残存（記録。恒久対策とは別）

v1.13.2 の Zenodo record `23392789`（version DOI `10.5281/zenodo.23392789` /
concept DOI `10.5281/zenodo.23390594`）は、newversion ドラフトが継承した
`japan-cannabinoid-trends-v1.13.1-clean.zip` を自身の
`japan-cannabinoid-trends-v1.13.2-clean.zip` と併せて保持している。

- 公開済み record のファイル削除は Zenodo API では拒否される（測定: 2026-10-15、
  `DELETE /api/deposit/depositions/23392789/files/<id>` → HTTP 403。
  workflow run 38745740554）。メタデータのみ編集可。
- 影響は限定的（同一 series のクリーンアーカイブが 1 件多く入るだけ。per-post
  X データや非公開物は含まない）。record とアーカイブは不変のため遡及訂正しない。
- 再発防止は恒久対策側で担保: `publish-zenodo.py` はアップロード前にドラフトの
  継承ファイルを削除する（`tests/validation/test_publish_zenodo.py` が
  「DELETE が upload より先」を固定）。次回 release で実地確認する。
