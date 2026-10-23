# Issue: study 改名（`cannabinoid-multi-trends` → `cannabinoid-raw-collection`）の残作業

**ID:** ISS-20261023-PRV-004  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `publication/research_cbd.html`, `publication/search-emergence-tracker/`, `datasets/cannabinoid-raw-collection/`, `metadata/datapackage.json`

## 概要

「multi」と「platform」が区別できないため、収集側の study を `cannabinoid-multi-trends` から
`cannabinoid-raw-collection` に改名した（ディレクトリと `study_id`、datapackage の resource 名）。
raw は不変なので `run_metadata.json` の `study_id` は旧 ID のままで、`previous_study_ids` で解決する。

配布側の `cannabinoid-platform-trends` は改名していない。これは**公開済みデータセットの名前**
（「Japan Cannabinoid Platform Trends Dataset 2026」、concept DOI `10.5281/zenodo.23390594`）
であり、改名すると 1 つの配布物に 2 つの名前ができるため。

## 残作業

### 1. 公開ページの旧パス（要・再レビュー）

次の公開成果物は旧パスを引用したままだ。PC-7（公開レビューのハッシュ）を通すため、今回の改名では
**あえて触っていない**。パスを直すには再レビューが必要。

- `publication/research_cbd.html`（2 箇所: `datasets/cannabinoid-multi-trends/data/raw/youtube/`）
- `publication/search-emergence-tracker/index.html`（CSV への GitHub URL 2 箇所）
- `publication/search-emergence-tracker/citation-units.md`・`methodology.md`

補足: 引用先の `data/raw/youtube/` はもともと Git 管理外なので、読み手にとって元から解決しないパス
だった（影響はリンク切れの見た目に限られる）。

### 2. 他の checkout にある無追跡 raw の移動

改名は追跡ファイル（改名は Git の rename として記録）に限られる。**Git 管理外の raw**
（例: `datasets/cannabinoid-multi-trends/data/raw/{x,youtube}/`）は各 checkout に残るため、
手元で移動する必要がある。移動しても内容は変えない（raw 不変）。

```bash
# checkout のルートで一度だけ（旧パスが残っている場合）
mkdir -p datasets/cannabinoid-raw-collection/data/raw
mv datasets/cannabinoid-multi-trends/data/raw/* datasets/cannabinoid-raw-collection/data/raw/
rmdir -p datasets/cannabinoid-multi-trends/data/raw 2>/dev/null || true
```

### 3. CHANGELOG / バージョン

リポジトリの `CHANGELOG.md` は「日付付きのリリース版のみ」を前提に検査されている
（`tests/validation/test_version_internal_consistency.py` が最新見出しの日付と CITATION /
datapackage の版一致を要求する）。今回の改名は**未リリースの構造変更**なので、CHANGELOG
エントリとバージョン bump（1.13.3 等）は次のリリース時に owner が決める。

## 完了条件

- [x] study / ディレクトリ / `study_id` の改名と `previous_study_ids` の宣言
- [x] 研究層（research catalog / g7）での旧 ID 解決、storage 層は記録値のまま
- [x] 監査スナップショットの再生成と `pytest` 通過（1454 passed）
- [ ] 公開ページの旧パスを直す（再レビュー後に PC-7 のハッシュを更新）
- [ ] 各 checkout の無追跡 raw を新ディレクトリへ移動
- [ ] 次のリリースで CHANGELOG とバージョンを更新
