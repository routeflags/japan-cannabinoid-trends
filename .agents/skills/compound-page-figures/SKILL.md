---
name: compound-page-figures
description: Generate, refresh, or embed the three per-compound figures (5-year Google Trends line, yearly YouTube count bars, common-scale annual search-volume bubble matrix) on publication/research_<compound>.html using this repository's verified, page-checked generator and embedder. Use when adding a compound page, refreshing figures after a page or run change, or explaining where figure artifacts live and why embedding needs re-approval.
---

# Compound page figures

`publication/research_<compound>.html` の系列を、ページに埋め込む図（SVG / PNG）にする。
**新しい数値は作らない**。ページ記載値と raw を照合し、食い違えば生成を中止する。

3つの図：検索関心度の5年推移（単独系列）、動画の年次公開件数（返却サンプル）、
年間検索ボリュームのバブルマトリクス（`compare_terms` 共通スケール）。

## 生成物と場所

```text
scripts/analysis/compound_page_charts.py        # 図の生成（検証込み。stdlib のみ）
scripts/publication/embed_compound_figures.py   # 図をページへ差し込む

publication/figures/<compound>/                 # 図の実体（ページから相対参照）
    trends-5y-standalone.{svg,png}
    youtube-yearly-<slug>.{svg,png}
    bubble-matrix-<set>.{svg,png}

datasets/cannabinoid-raw-collection/analysis/
    README.md                                   # 物質別の索引（スクリプトが生成）
    <compound>-page-charts/
        README.md
        provenance.json                         # 出所・検証・出力 hash（図の正本）
        trends-5y-standalone.csv
        youtube-yearly-<slug>.csv
        bubble-matrix-<set>.csv
```

図の実体を `publication/figures/` に置くのは、ページが `figures/<compound>/…` を相対参照するため。
派生元の CSV と出所記録は study 側に残す（図とその導出を同じ場所に二重で置かない）。

### 3 つの図と差し込み位置

| 図 | id | 差し込み位置 |
|---|---|---|
| 検索関心度の 5 年推移（折れ線） | `trends-5y-standalone` | `5年データサマリー` 表の後の最初の見出しの前 |
| 動画の年次公開件数（縦棒） | `youtube-yearly-<slug>` | 対応する `年次分布` 表の直後（文書順） |
| 年間検索ボリューム（バブルマトリクス） | `bubble-matrix-<set>` | 5年 `共通スケール` の表の直後 |

図番号は文書順に探る（YouTube 節が Trends 節より前にあるページでは年次図が図1 になる）。

`<slug>` は年次表の見出しから決まる（`収集 A` → `collection-a`、`HHC` → `hhc`、
`HHC リキッド` → `hhc-liquid`）。

## 手順

1. 対象ページのデータ節を確認する。図の材料は次の3つだけである。
   - `5年データサマリー` 表と、その直後に引用された Google Trends run（推移図）
   - `の月次公開日件数` 節にある `年次分布` 表（年次図、複数あり得る）
   - 5年 `共通スケール` 節の `compare_terms` 表と、その出所に引用された run（マトリクス）
   欠ける材料の図は作らない（THCNM は年次表が無く、推移図とマトリクスのみ）。
2. 図を生成する（ページ記載値と raw の照合を含む）。
   ```bash
   python3 scripts/analysis/compound_page_charts.py            # 全物質
   python3 scripts/analysis/compound_page_charts.py cbd thc    # 指定物質だけ
   ```
3. ページに差し込む。位置は構造で決まる（推移図は5年サマリー表の後の最初の見出しの前、
   年次図は各年次表の直後、マトリクスは共通スケール表の直後）。図番号は文書順。
   何度実行しても結果は同じ（マーカーの間を置き換える）。
   ```bash
   python3 scripts/publication/embed_compound_figures.py
   ```
4. 失敗したら**コードを曲げずに**原因を見る。検証は次の不変条件で止まる。
   - 5年平均・ピーク日/値・最新値・観測範囲が、ページと raw で一致しない
   - 年次合計が `返却件数` と一致しない、年が昇順でない
   - 共通スケールの語別平均がページの表と一致しない、5年共通スケール run が一意でない
   - ページの年次表の数と `provenance.json` の年次図の数が合わない
   多くは「ページが新しい run に切り替わった」「raw が再保持された」のどちらかである。
   ページか raw のどちらが正しいかを確かめ、**両方を直してから**再生成する。
5. 生成後に目で確認する。年ラベルの衝突、平均線・ピーク・最新注記の重なり、
   値ラベルの切れを見る（PNG を直接開く）。
6. `analysis/README.md`・各ディレクトリの `README.md`・`provenance.json` はスクリプトが
   書くので手で編集しない。物質を増やすときは `publication/research_<compound>.html` を
   先に作り、スクリプトはページを自動発見する（登録リストは持たない）。

## 公開状態の扱い

差し込むとページの SHA-256 が変わる。承認は hash 単位なので、差し込みスクリプトは
公開状態の節を「再承認待ち」に書き換える。

- 承認（`metadata/publication/research-<compound>/decision.json`）は owner の判断であり、
  **エージェントは status や `artifact_sha256` を自分で更新しない**。
- 再承認されたら、その時点の hash と監査結果をページの公開状態節・`decision.json`・
  `evidence.json` に反映する（版表記とリリース日は owner が決める）。
- `validation.cli` は `cerberus` 等の依存が無いと動かない。`.venv` が無い環境では
  監査を実行できないので、実行できなかったことを報告に書く。

## 図に必ず入れる制約（描画側で自動付与）

- 検索推移は単独系列の相対指数（系列最大 = 100）。共通スケール系列とは換算できない。
- バブルマトリクスは同じ `compare_terms` 要求の共通スケール内だけで比較する。要求間・
  単独系列とは換算できない。年間平均は週次値の暦年平均で、部分年は週数で明示し補完しない。
  0 は相対指数の最小値への丸めであり、需要ゼロの観測ではない。
- 年次件数は**返却サンプル内**の公開日件数。YouTube 全体の投稿数ではない。
- `date_filter` の異なる run と比較せず、複数 run を合算しない。
- 公開日がサンプルにない年は棒を作らない（未取得を 0 にしない）。
- 3つの図は異なる現象であり合算しない（source separation）。

## バブルマトリクスの範囲決定

- 描く語は**そのページが共通スケール表に載せている語だけ**にする。ページが「この語は載せない」と
  決めている範囲を図で広げない（例: THCNM の 5年節は CBD・THC・THCNM の 3 語だけを載せる）。
  要求全体の語は `provenance.json` の `source.request_terms` に記録する。
- 要求の選び方は、ページの 5年 `共通スケール` の出所が引用する run。複数候補や 0 件なら停止する。
- 語別 5年平均がページの表（小数第 4 位）と一致することを検証する。
- **CBX の注意**: 研究の `comparison_scales` は CBX を `ISS-20261024-COL-016` の決定まで
  比較セットから除外している。CBX ページは `comparison-cbx-bridge` run（CBX・CBD・THC）を
  5年共通スケールとして掲載しているため、その要求だけを図にしている。方針上の位置づけが
  変わったら run の選択も見直す。

## やってはいけないこと

- `data/raw/` を編集しない。年次表の raw payload は Git 非追跡・非公開で、
  年次図はリポジトリから再計算できない（ページ記載の集計の可視化である）。
- 図の値を手作業で調整しない（欠測を 0 にする、目盛りを変えて差を消す等）。
- 図を別ディレクトリへ手でコピーしない（`publication/figures/` が唯一の置き場）。
- 配布スライス `datasets/cannabinoid-platform-trends/` に図を入れない。
- コスト・金額を図や README に書かない（AGENTS.md のスコープ外）。

## 検証コマンド

```bash
python3 scripts/analysis/compound_page_charts.py          # 照合込みで生成
python3 scripts/publication/embed_compound_figures.py     # 差し込み（冪等）
python3 -m py_compile scripts/analysis/compound_page_charts.py scripts/publication/embed_compound_figures.py
```

再現性は「同じ入力なら同じ SVG / CSV / HTML」で確かめる。2回生成してハッシュが
一致すれば良い。PNG は `rsvg-convert` がある場合だけ生成し、無ければ SVG のみで
`provenance.json` の `png_renderer` にその旨が残る。
