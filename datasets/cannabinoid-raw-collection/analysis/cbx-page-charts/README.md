# CBX の2図

`publication/research_cbx.html` の系列を図にした成果物。数値はページ記載と一致させており、
ここで新しい値は作らない。図本体は `publication/figures/` に置き、このディレクトリには
CSV（元系列）と出所記録を残す。

## 図

| 図 | ファイル | 出所 |
|---|---|---|
| 検索関心度の5年推移（折れ線） | `trends-5y-standalone.{svg,png}` / `.csv` | Google Trends run `20261015T042857Z-google-trends-boundary-5y`（2021-10-10 〜 2026-10-11、262 週） |
| 動画の年次公開件数（329 件） | `youtube-yearly-cbx-liquid.{svg,png}` / `.csv` | YouTube run `20261101T112555Z-youtube-cannabinoid-raw-collection` |
| 年間検索ボリュームのバブルマトリクス | `bubble-matrix-cbx-bridge.{svg,png}` / `.csv` | Google Trends run `20261104T165155Z-google-trends-cannabinoid-raw-collection`（compare_terms、同一要求内で比較） |

## 読み方と制約

- 推移図の値は**単独系列**の相対指数（この系列の最大が 100）。共通スケール要求の値とは
  別の物差しで、換算できない。絶対検索数でもない。
- 年次件数は**返却サンプル内**の公開日件数であり、YouTube 全体の投稿数ではない。
  公開日がサンプルにない年は行を作らず、0 として埋めない。観測範囲が年を覆わない年は
  部分年として `*` を付け、その年の日数分の件数であることを図に明記する。
- 年次表は `publication/` の公開済み集計からの機械抽出である。raw payload は Git
  非追跡・非公開のため、本リポジトリの raw からは再計算できない。
- バブルマトリクスは同じ `compare_terms` 要求の共通スケール内だけで比較する。要求間・単独系列とは
  換算できない（各要求はその中の最大 = 100 で正規化される）。年間平均は週次値の暦年平均で、
  部分年は週数で明示し、欠測を補わない。
- 3 つの図は異なる現象の測定値であり、合算・比較しない（source separation）。

## 生成

```bash
python3 scripts/analysis/compound_page_charts.py cbx
```

stdlib のみで動き、SVG に生成時刻を埋め込まない。PNG は `rsvg-convert` がある場合のみ
生成し、無ければ SVG のみを作って `provenance.json` に記録する。

## 公開スコープ

- 図本体は `publication/figures/cbx/` にあり、ページから
  `figures/<compound>/…` で相対参照する。差し込みは
  `scripts/publication/embed_compound_figures.py` が行う。
- ページは hash 単位の公開承認であり、図を差し込むと SHA-256 が変わるため再承認が要る。
- 配布スライス `datasets/cannabinoid-platform-trends/` には含めない。
