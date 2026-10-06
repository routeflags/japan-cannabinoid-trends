#!/usr/bin/env python3
"""
Research Data Page Generator
化合物の調査データのみを表示するクリーンな HTML ページを生成する。

CSS、インラインスタイル、ヘッダー、フッター、記事構造を含まない。

使用例:
    python3 generate_research_data_page.py \
      --compound CBD \
      --japanese "カンナビジェロール" \
      --regulation "非規制（条件付き合法）" \
      --gt-individual-avg 46.8 \
      --gt-common-scale 47 \
      --coa-url "https://example.com/coa.jpg"
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
    coa_url: Optional[str] = None,
    coa_notes: Optional[str] = None,
    x_records: Optional[int] = None,
    x_period: Optional[str] = None,
    x_findings: Optional[str] = None,
    youtube_records: Optional[int] = None,
    youtube_period: Optional[str] = None,
    youtube_findings: Optional[str] = None,
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
  <p>Google Trends から、{compound_name} の日本国内検索興味度（相対指数 0-100）を取得しました。</p>

  <div>
    <p><strong>用語の定義:</strong></p>
    <ul>
      <li><strong>単独平均（個別正規化値）</strong>: 各キーワードを個別に取得した際の12ヶ月平均値。各キーワードのピークを100とする正規化であり、<strong>キーワード間の比較には使用できない</strong>。</li>
      <li><strong>比較平均（共通スケール値）</strong>: 複数キーワードを同時取得した際の12ヶ月平均値。比較セット内の最大値を100とする正規化であり、<strong>キーワード間の相対的な検索需要を示す</strong>。</li>
      <li><strong>興味度スコア</strong>: Google Trends が返す相対指数（0-100）。絶対検索数ではなく、期間内の最大検索量を100とした相対値。</li>
    </ul>
  </div>

  <h3>キーワード別サマリー（個別正規化値）</h3>
  <table>
    <thead>
      <tr>
        <th>キーワード</th>
        <th>12ヶ月平均</th>
        <th>12ヶ月最高</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>{compound_name}</strong></td>
        <td>{gt_individual_avg}</td>
        <td>100</td>
      </tr>
    </tbody>
  </table>
"""
        if gt_common_scale is not None:
            gt_section += f"""
  <h3>共通スケール比較</h3>
  <p>CBD = 100 基準の相対値</p>
  <table>
    <thead>
      <tr>
        <th>化合物</th>
        <th>共通スケール値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>{compound_name}</strong></td>
        <td><strong>{gt_common_scale}</strong></td>
      </tr>
    </tbody>
  </table>
"""
        gt_section += """
  <p><strong>制約:</strong> Google Trends は相対指数であり、絶対検索数ではない。</p>
</div>
"""
    
    # 規制状況セクション
    regulation_section = ""
    if regulation_date or regulation_law:
        # CBD/CBG の場合、正しい条件を表示
        if compound_name in ["CBD", "CBG"]:
            regulation_section = f"""
<!-- ===== 規制状況 ===== -->
<div>
  <h2 id="data-regulation">規制状況: {compound_name} の日本法での法的扱い <span>一次資料の整理</span></h2>
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
      <tr>
        <td>規制基準</td>
        <td>部位ではなく <strong>製品中のΔ9-THC残留量</strong></td>
      </tr>
      <tr>
        <td>葉・花穂由来</td>
        <td>✅ 可（2024-12-12以降）</td>
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

  <h3>THC 残留限度値</h3>
  <table>
    <thead>
      <tr>
        <th>製品種別</th>
        <th>限度値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>油脂・粉末</td>
        <td><strong>10 ppm</strong> (0.0010%)</td>
      </tr>
      <tr>
        <td>水溶液</td>
        <td><strong>0.10 ppm</strong> (0.000010%)</td>
      </tr>
      <tr>
        <td>その他</td>
        <td><strong>1 ppm</strong> (0.0001%)</td>
      </tr>
    </tbody>
  </table>

  <p><strong>注意:</strong> 限度値超過品は麻薬として所持・使用・販売等が禁止されます。</p>
</div>
"""
        else:
            # その他の化合物
            regulation_section = f"""
<!-- ===== 規制状況 ===== -->
<div>
  <h2 id="data-regulation">規制状況: {compound_name} の日本法での法的扱い <span>一次資料の整理</span></h2>
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
  <p><strong>注意:</strong> 法的状況は調査時点の結果。法改正の可能性あり。</p>
</div>
"""
    
    # COA データセクション
    coa_section = ""
    if coa_url:
        coa_notes_text = coa_notes or "サプライヤー提供の分析証明書。当店自身による分析ではありません。"
        coa_section = f"""
<!-- ===== 独自データ：COA 分析結果 ===== -->
<div>
  <h2 id="data-coa">独自データ: {compound_name} 製品の COA 分析結果 <span>一次データ</span></h2>
  <p>データソース: サプライヤー提供 COA / 取得日: {today}</p>
  <p>COA（Certificate of Analysis）は、製品に含まれる成分を分析した証明書です。</p>
  <h3>分析結果</h3>
  <figure>
    <img src="{coa_url}" alt="{compound_name} COA 分析結果">
    <figcaption>{compound_name} 製品の COA 分析結果</figcaption>
  </figure>
  <p><strong>注意:</strong> {coa_notes_text}</p>
  <p><strong>COA の限界:</strong> 原料 COA ≠ 販売製品ごとの検査結果。サプライヤー分析 ≠ 当店分析。</p>
</div>
"""
    
    # X (Twitter) データセクション
    x_section = ""
    if x_records is not None:
        x_period_text = x_period or "直近3ヶ月"
        x_findings_text = x_findings or "データ分析中"
        x_section = f"""
<!-- ===== 独自データ：X (Twitter) トレンド ===== -->
<div>
  <h2 id="data-x">独自データ: {compound_name} の X (Twitter) トレンド <span>一次データ</span></h2>
  <p>データソース: X (Twitter) via Apify / 期間: {x_period_text} / 取得日: {today}</p>
  <p>X (Twitter) から、{compound_name} に関する日本語投稿を収集しました。</p>
  <h3>収集結果</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>日本語投稿数</td>
        <td>{x_records}件</td>
      </tr>
      <tr>
        <td>観測期間</td>
        <td>{x_period_text}</td>
      </tr>
    </tbody>
  </table>
  <p><strong>所見:</strong> {x_findings_text}</p>
  <p><strong>制約:</strong> X 検索結果のサンプルであり、全投稿を網羅するものではない。</p>
</div>
"""
    
    # YouTube データセクション
    youtube_section = ""
    if youtube_records is not None:
        youtube_period_text = youtube_period or "観測期間"
        youtube_findings_text = youtube_findings or "データ分析中"
        youtube_section = f"""
<!-- ===== 独自データ：YouTube トレンド ===== -->
<div>
  <h2 id="data-youtube">独自データ: {compound_name} の YouTube トレンド <span>一次データ</span></h2>
  <p>データソース: YouTube / 期間: {youtube_period_text} / 取得日: {today}</p>
  <p>YouTube から、{compound_name} に関する動画を収集しました。</p>
  <h3>収集結果</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>動画数</td>
        <td>{youtube_records}件</td>
      </tr>
      <tr>
        <td>観測期間</td>
        <td>{youtube_period_text}</td>
      </tr>
    </tbody>
  </table>
  <p><strong>所見:</strong> {youtube_findings_text}</p>
  <p><strong>制約:</strong> YouTube 検索結果のサンプルであり、全動画を網羅するものではない。</p>
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
  <li><strong>検索データ:</strong> Google Trends（日本、過去12ヶ月）</li>
  <li><strong>規制資料:</strong> 厚生労働省</li>
</ul>
{gt_section}
{regulation_section}
{coa_section}
{x_section}
{youtube_section}
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
    parser.add_argument("--compound", "-c", required=True, help="化合物名")
    parser.add_argument("--japanese", "-j", required=True, help="日本語名")
    parser.add_argument("--regulation", "-r", required=True, help="規制状況")
    parser.add_argument("--gt-individual-avg", type=float, help="Google Trends 個別平均値")
    parser.add_argument("--gt-common-scale", type=float, help="共通スケール値")
    parser.add_argument("--regulation-date", help="規制施行日")
    parser.add_argument("--regulation-law", help="関連法令")
    parser.add_argument("--regulation-source", help="一次資料の URL")
    parser.add_argument("--coa-url", help="COA 画像の URL")
    parser.add_argument("--coa-notes", help="COA の注意事項")
    parser.add_argument("--x-records", type=int, help="X 投稿数")
    parser.add_argument("--x-period", help="X 観測期間")
    parser.add_argument("--x-findings", help="X 所見")
    parser.add_argument("--youtube-records", type=int, help="YouTube 動画数")
    parser.add_argument("--youtube-period", help="YouTube 観測期間")
    parser.add_argument("--youtube-findings", help="YouTube 所見")
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
        coa_url=args.coa_url,
        coa_notes=args.coa_notes,
        x_records=args.x_records,
        x_period=args.x_period,
        x_findings=args.x_findings,
        youtube_records=args.youtube_records,
        youtube_period=args.youtube_period,
        youtube_findings=args.youtube_findings,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
