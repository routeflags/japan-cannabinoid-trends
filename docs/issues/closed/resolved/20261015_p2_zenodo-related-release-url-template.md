# Issue: Zenodo の公開済み related identifier に `${VERSION}` が展開されず残る

**ID:** ISS-20261015-REL-016  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-15)  
**検出日:** 2026-10-15  
**対象:** `.github/workflows/release-zenodo.yml`、Zenodo record `23390595`

## 概要

Zenodo upload workflow が JSON payload を単一引用符で構築しているため、
`related_identifiers` の GitHub Release URL にある `${VERSION}` が shell 展開されない。
公開済み Zenodo record `23390595` は実在する `v1.13.1` release URL ではなく、文字列のままの
`https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/${VERSION}` を
related identifier として保持している。

## 確認された観測

- [workflow](../../../../.github/workflows/release-zenodo.yml) の 124–154 行は
  `-d '{ ... }'` で JSON を渡し、147 行に `${VERSION}` を置いている。
- GitHub Actions は `VERSION="${{ steps.archive.outputs.version }}"` を設定するが、単一引用符内の
  `${VERSION}` は shell により置換されない。
- Zenodo API `https://zenodo.org/api/records/23390595` の
  `metadata.related_identifiers[1].identifier` は、実測で
  `https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/${VERSION}`。

## 影響

- Zenodo 利用者が versioned GitHub Release へ追跡できない。
- データセットと補足 release の関係を示す公開メタデータが壊れ、出荷来歴の辿り直しができない。
- 以後の release でも同じ workflow を使う限り再発する。

## 対応方針

1. JSON を `jq --arg version "$VERSION"` などで生成し、URL の version 部分を明示的に
   JSON escape して注入する。文字列連結で API payload を組み立てない。
2. API 応答の `related_identifiers` が期待する
   `https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v<version>`
   と一致しなければ workflow を失敗させる。
3. 公開済み record `23390595` は不変性を尊重して訂正可否を Zenodo 上で確認し、訂正できない場合は
   次の release の notes と metadata に訂正関係を記録する。

## 完了条件

- [ ] workflow が `${VERSION}` を含まない具体的な GitHub Release URL を Zenodo に送る。
- [ ] 成功時に Zenodo API の保存済み identifier を取得して期待 URL と照合する。
- [ ] 新規 release の Zenodo record から対応する GitHub Release を辿れる。

---

## 解決記録（2026-10-15）

inline shell の単一引用符 JSON を廃し、Zenodo へのメタデータ送信を
`scripts/release/publish-zenodo.py` に移した（`json.dumps` で組み立てるため
`${VERSION}` 展開不能という欠陥は構造的に消滅）。

- workflow は `--version v1.13.2` を渡し、script 側で
  `https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2`
  を組み立てる。
- `publish()` は公開後のレコードから `related_identifiers` を読み、期待 URL と
  完全一致しない場合に exit 1 で失敗する（回帰防止は恒久的な公開後検証）。
- dry-run（`--skip-upload`）で送信予定 URL を確認可能。
