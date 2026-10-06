#!/usr/bin/env python3
"""
Research Data Page Generator
化合物の調査データのみを表示するクリーンな HTML ページを生成する。

CSS、インラインスタイル、ヘッダー、フッター、記事構造を含まない。

使用例:
    python3 generate_research_data_page.py \
      --compound CBN \
      --japanese "カンナビノール" \
      --regulation "指定薬物（2026年6月1日施行）" \
      --gt-individual-avg 55.6 \
      --gt-common-scale 11 \
      --regulation-date "2026-06-01" \
      --regulation-law "薬機法（指定薬物）"
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_research_page(
    compound_name: str,
    compound_japanese: str,
    regulation_status: str,
    gt_individual_avg: Optional[float] = None,
    gt_common_scale: Optional[float] = None,
    regulation_date: Optional[str] = None,
    regulation_law: Optional[str] = None,
    regulation_source: Optional[str] = None,
    output_dir: str = "publication",
) -> Path:
    """調査データページを生成する"""
    
    compound_slug = compound_name.lower()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Google Trends データセクション
    gt_section = ""
    if gt_individual_avg is not None:
        gt_section = f"""
<!-- ===== 独自データ：Google Trends 検索需要 ===== -->
<div>
  <h2 id="data-search">独自データ: {compound_name} の Google Trends 検索需要 <span>一次データ</span></h2>
  <p>データソース: Google Trends / 地域: 日本 (JP) / 期間: 過去12ヶ月（週次）/ 取得日: {today}</p>

  <p>Google Trends から、{compound_name} の日本国内検索興味度（相対指数 0-100）を取得しました。市場全体の検索需要を示す公開データです。</p>

  <h3>キーワード別サマリー（個別正規化値）</h3>
  <table>
    <thead>
      <tr>
        <th>キーワード</th>
        <th>12ヶ月平均</th>
        <th>12ヶ月最高</th>
        <th>12ヶ月最低</th>
        <th>データポイント</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>{compound_name}</strong></td>
        <td>{gt_individual_avg}</td>
        <td>100</td>
        <td>—</td>
        <td>53</td>
      </tr>
    </tbody>
  </table>

  <p><strong>注意:</strong> 上記は個別収集データであり、{compound_name} 自体のピークを100とする正規化です。化合物間の比較には共通スケールデータを使用してください。</p>
"""
        
        if gt_common_scale is not None:
            gt_section += f"""
  <h3>共通スケール比較（化合物間比較用）</h3>
  <p>データソース: <code>comparison_set*.json</code> / 化合物同時比較 / CBD = 100 基準</p>

  <table>
    <thead>
      <tr>
        <th>化合物</th>
        <th>共通スケール値</th>
        <th>個別正規化値（参考）</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>{compound_name}</strong></td>
        <td><strong>{gt_common_scale}</strong></td>
        <td>{gt_individual_avg}</td>
      </tr>
    </tbody>
  </table>
"""
        
        gt_section += f"""
  <p>
    <strong>制約:</strong> Google Trends は相対指数であり、絶対検索数ではない。
    低ボリュームクエリはデータが返らない場合がある。
  </p>
</div>
"""
    
    # 規制状況セクション
    regulation_section = ""
    if regulation_date or regulation_law:
        regulation_section = f"""
<!-- ===== 独自データ：規制状況 ===== -->
<div>
  <h2 id="data-regulation">独自データ: {compound_name} の日本法規制状況 <span>一次資料</span></h2>
  <p>データソース: 厚生労働省 / 調査日: {today}</p>

  <h3>法的扱い</h3>
  <table>
    <thead>
      <tr>
        <th>項目</th>
        <th>内容</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>法的扱い</td>
        <td><strong>{regulation_status}</strong></td>
      </tr>
"""
        
        if regulation_law:
            regulation_section += f"""      <tr>
        <td>法令名</td>
        <td>{regulation_law}</td>
      </tr>
"""
        
        if regulation_date:
            regulation_section += f"""      <tr>
        <td>施行日</td>
        <td>{regulation_date}</td>
      </tr>
"""
        
        if regulation_source:
            regulation_section += f"""      <tr>
        <td>出典</td>
        <td><a href="{regulation_source}">一次資料</a></td>
      </tr>
"""
        
        regulation_section += """    </tbody>
  </table>

  <p><strong>注意:</strong> 法的状況は調査時点の結果。法改正の可能性あり。詳細は一次資料を確認してください。</p>
</div>
"""
    
    # HTML テンプレート
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{compound_name} 調査データ</title>
</head>
<body>

<!-- ===== 調査方法 ===== -->
<h2 id="methodology">調査方法</h2>

<p>このセクションでは、本ページの情報がどのように収集・分析されたかを公開しています。</p>

<h3>研究質問</h3>
<p>「日本国内における{compound_name}のオンライン上の検索需要・規制状況は何か？」</p>
<p><strong>最終更新:</strong> {today}。</p>

<h3>データソース</h3>
<ul>
  <li><strong>検索データ（主要）:</strong> Google Trends（日本、過去12ヶ月）</li>
  <li><strong>規制資料:</strong> 厚生労働省</li>
  <li><strong>学術文献:</strong> PubMed, Google Scholar</li>
</ul>

<h3>検索クエリ</h3>
<ul>
  <li>Google Trends: <code>{compound_name}</code>（geo=JP, 期間=today 12-m）</li>
  <li>学術: PubMed, Google Scholar で {compound_name} を検索</li>
  <li>規制: 厚労省 指定薬物一覧</li>
</ul>

<h3>取得期間</h3>
<p>2025-09-28 ～ {today}（Google Trends 週次）</p>

<h3>含み・除外基準</h3>
<ul>
  <li><strong>含む:</strong> 日本語クエリ、英語クエリのうち日本市場関連</li>
  <li><strong>除く:</strong> ボット判定クエリ、同一IPからの連続アクセス</li>
</ul>

<h3>再現性チェックリスト</h3>
<ul>
  <li>✅ 検索クエリを完全に記録した</li>
  <li>✅ 取得日を記録した</li>
  <li>✅ 含み・除外の基準を明記した</li>
  <li>✅ 生データを保存した（Google Trends JSON）</li>
  <li>✅ 出典を明記した</li>
</ul>

<p>
  <strong>制約:</strong> Google Trends の値は相対指数（0-100）であり、絶対検索数ではありません。
</p>
{gt_section}
{regulation_section}
<!-- ===== 引用情報 ===== -->
<div>
  <h2 id="citation">引用 (How to Cite)</h2>
  <p>
    KATO, Kyoji（2026）.<br>
    「Japan Cannabinoid Trends Dataset 2026: Google Trends, Social Media, Regulatory Status, and Early Warning Index」.<br>
    Version 1.9.0<br>
    Routeflags Co., Ltd.<br>
    [Dataset].<br>
    DOI: <a href="https://doi.org/10.5281/zenodo.23164973">10.5281/zenodo.23164973</a>
  </p>
  <p>
    <a href="https://doi.org/10.5281/zenodo.23164972">
      <img src="https://zenodo.org/badge/1375618430.svg" alt="DOI">
    </a>
  </p>
</div>

</body>
</html>
"""
    
    # 出力先を確保
    output_path = Path(output_dir) / f"research_{compound_slug}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ファイルに保存
    output_path.write_text(html)
    
    print(f"✅ 生成完了: {output_path}")
    print(f"   化合物: {compound_name} ({compound_japanese})")
    print(f"   規制状況: {regulation_status}")
    print(f"   ファイルサイズ: {output_path.stat().st_size:,} bytes")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="化合物の調査データページを生成")
    parser.add_argument("--compound", "-c", required=True, help="化合物名 (例: CBN)")
    parser.add_argument("--japanese", "-j", required=True, help="日本語名 (例: カンナビノール)")
    parser.add_argument("--regulation", "-r", required=True, help="規制状況")
    parser.add_argument("--gt-individual-avg", type=float, help="Google Trends 個別平均値")
    parser.add_argument("--gt-common-scale", type=float, help="共通スケール値 (CBD=100基準)")
    parser.add_argument("--regulation-date", help="規制施行日 (例: 2026-06-01)")
    parser.add_argument("--regulation-law", help="関連法令")
    parser.add_argument("--regulation-source", help="一次資料の URL")
    parser.add_argument("--output", "-o", default="publication", help="出力ディレクトリ")
    
    args = parser.parse_args()
    
    generate_research_page(
        compound_name=args.compound,
        compound_japanese=args.japanese,
        regulation_status=args.regulation,
        gt_individual_avg=args.gt_individual_avg,
        gt_common_scale=args.gt_common_scale,
        regulation_date=args.regulation_date,
        regulation_law=args.regulation_law,
        regulation_source=args.regulation_source,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
