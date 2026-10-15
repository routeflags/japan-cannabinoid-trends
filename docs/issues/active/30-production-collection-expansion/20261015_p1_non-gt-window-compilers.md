# Issue: Google Trends 以外のソースに Window Compiler が無い

**ID:** ISS-20261015-WIN-002  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `src/collection/adapters/__init__.py`（`_WINDOW_COMPILERS`）, `docs/specs/collection-pipeline.md` §3.2, `docs/specs/validation-framework.md` §16.3

## 概要

window compiler は `google-trends-mcp` と YouTube Apify `dateFilter=year` MVP のみ登録されている。
その他のソース / YouTube の未測定 `dateFilter` は compiler 未登録または未実装で、期間パラメータは
adapter 自身の検証に委ねられ、絶対窓から collector パラメータへの compile は行われない（pre-G3 挙動）。

## 確認された観測

- `src/collection/adapters/__init__.py` の `_WINDOW_COMPILERS` は 2 エントリ
  （`google-trends-mcp`, `youtube-apify-scraper`）。
- X の `since:` / `until:`、YouTube の `dateFilter`（相対のみ）といったソース固有の
  期間語彙は registry に表現されていない。
- 相対 rolling 語彙（`dateFilter=month` 等）の実測は 2026-10-10 の手作業記録
  （`.github/skills/apify-youtube-scraper/SKILL.md`）に留まり、機械可読な registry に無い。

## 影響

- 期間の無断切替（P6）を GT 以外では機械的に防げない。
- 他ソースの run を現行契約で取る場合、要求窓と観測範囲の分離（P5）が adapter 任せになる。

## 対応方針

- **owner 決定（2026-10-15）:** 非 GT adapter の着手順に合わせ、まず YouTube Apify CSV
  pattern で request filter（例 `dateFilter`）と observed range を分けて扱う。X の絶対期間
  compiler は mock / dry-run + request-only evidence が整うまで live 実測に進まない。
- 各ソースの adapter（ISS-20261015-COL-016）と同じ設計単位で compiler を追加する。
- ソース固有語彙は**実測で意味を確定してから** registry へ登録する（推測で登録しない）。
- 表現不能な窓は fail closed（既存の拒否コード体系を再利用）。

## 完了条件

- [ ] 対象ソースの期間語彙を registry に表現（`metadata/windows/` との整合を含む）
- [ ] compiler 実装 + 契約テスト（既存 `tests/collection/test_window_compiler.py` と同型）
- [ ] 表現不能ケースの拒否コードを実測で確認

## 対応記録（2026-10-15: YouTube `dateFilter=year` MVP）

owner 指示「X は後回し。YouTube / GT 品質を先に高める」により、YouTube Apify
`dateFilter=year` のみを MVP として実装した。

- 追加: `src/collection/adapters/youtube/compiler.py`
  - `dateFilter=year` を、COL-033 の採用済み宣言に基づく trailing ~365 days の相対要求として compile する。
  - `month` / `week` / `today` / `hour` / `all` は推測せず `no_verified_date_filter_matches` で fail closed。
  - `window.start/end_exclusive` は observed video publish-date range であり、API search condition ではない旨を
    `CompiledWindow.limitations` に残す。
  - `exact=false` / `boundary_semantics=observed_range_consistent_with_measured_year_filter`。capability registry は昇格しない。
- 登録: `_WINDOW_COMPILERS["youtube-apify-scraper"]` のみ。`registered_sources()` に `youtube` は追加しないため、
  live collection 可能には見せない。
- テスト: `tests/collection/test_youtube_window_compiler.py` を追加し、dispatch・CLI・拒否コード・capability conflict を固定。
- 本 issue は **OPEN 維持**。残件は YouTube の未測定 `dateFilter`、X / TikTok / Instagram / LinkedIn compiler、
  およびソース固有語彙の registry 表現。
