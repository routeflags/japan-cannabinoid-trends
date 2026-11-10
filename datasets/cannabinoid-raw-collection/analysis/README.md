# analysis — 図と集計の派生物

`publication/research_*.html` の系列を可視化した成果物を置く。ここに raw は置かない。

- `<compound>-page-charts/`: 物質ごとの図（推移・年次・バブルマトリクス）の CSV と出所記録
- `cbd-common-scale-5y/`: CBD の共通スケール系列（`scripts/analysis/cbd_common_scale_plot.py`）

## 物質別の図

| 物質 | ディレクトリ | 検索推移 | 動画年次の図 | 共通スケール |
|---|---|---|---|---|
| CBD | `cbd-page-charts/` | 5年 | 2 図 | 5年（同一要求） |
| CBG | `cbg-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| CBN | `cbn-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| CBX | `cbx-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| CRDH | `crdh-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| CRDP | `crdp-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| H4CBH | `h4cbh-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| HHBD | `hhbd-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| HHC | `hhc-page-charts/` | 5年 | 2 図 | 5年（同一要求） |
| HHCH | `hhch-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| THC-O | `thc-o-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| THC | `thc-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| THCH | `thch-page-charts/` | 5年 | 1 図 | 5年（同一要求） |
| THCNM | `thcnm-page-charts/` | 5年 | なし | 5年（同一要求） |
| THCV | `thcv-page-charts/` | 5年 | 1 図 | 5年（同一要求） |

図ごとの出所・検証・制約は各ディレクトリの `README.md` と `provenance.json` にある。
生成は全物質または物質を指定して:

```bash
python3 scripts/analysis/compound_page_charts.py
python3 scripts/analysis/compound_page_charts.py cbd thc
```

スクリプトはページ記載値と raw を照合し、食い違えば生成を止める。図はこの階層の
分析成果物であり、`publication/` への埋め込みは再公開審査の対象になる。
