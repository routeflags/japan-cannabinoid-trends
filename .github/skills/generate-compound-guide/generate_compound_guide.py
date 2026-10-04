#!/usr/bin/env python3
"""
Compound Guide Page Generator
CBX ガイドページと同じ構造で、他のカンナビノイド化合物用ガイドを生成する。

使用例:
    python3 generate_compound_guide.py --compound CBN --japanese カンナビノール \
        --regulation "指定薬物（2026年6月1日施行）" \
        --characteristics "THCの酸化で生成" "催眠作用の可能性" \
        --compare CBD THC CBG
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def generate_compound_guide(
    compound_name: str,
    compound_japanese: str,
    regulation_status: str,
    characteristics: List[str],
    comparison_compounds: Optional[List[str]] = None,
    output_dir: str = "publication",
    template_path: str = ".github/skills/generate-compound-guide/template.html",
) -> Path:
    """化合物ガイドページを生成する"""
    
    if comparison_compounds is None:
        comparison_compounds = ["CBD", "CBG", "CBX"]
    
    if characteristics is None:
        characteristics = []
    
    compound_slug = compound_name.lower()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # テンプレートを読み込み
    template = Path(template_path).read_text()
    
    # プレースホルダーを置換
    replacements = {
        "{{COMPOUND_NAME}}": compound_name,
        "{{COMPOUND_SLUG}}": compound_slug,
        "{{COMPOUND_JAPANESE}}": compound_japanese,
        "{{DATE_PUBLISHED}}": today,
        "{{DATE_MODIFIED}}": today,
        "{{REGULATION_STATUS}}": regulation_status,
        "{{COMPARISON_1}}": comparison_compounds[0],
        "{{GT_DATE}}": today,
    }
    
    for key, value in replacements.items():
        template = template.replace(key, value)
    
    # セクション別のコンテンツを生成
    section_data = {
        "SUMMARY_1": f"{compound_name}（{compound_japanese}）の化学的特徴と市場での位置づけ",
        "SUMMARY_2": f"日本国内での法的位置づけ（{regulation_status}）",
        "SUMMARY_3": "分かっていること・分からないこと",
        "SUMMARY_4": f"{comparison_compounds[0]}との違い",
        "SUMMARY_5": "検索需要データ",
        
        "INTRO_PARAGRAPH_1": f"{compound_name}は大麻に含まれるカンナビノイドの一つです。",
        "INTRO_PARAGRAPH_2": f"このページでは、{compound_name}について現時点で分かっていることを整理します。",
        "INTRO_PARAGRAPH_3": f"分かっていないこと・注意すべき点も含めて解説します。",
        
        "CAVEAT_TEXT": f"{compound_name}に関するデータは限定的な場合があります。この記事は暫定的な記録であり、更新される可能性があります。",
        
        "WHAT_IS_INTRO": f"このセクションでは、学術文献上の{compound_name}と、市場で流通している製品の違いを整理します。",
        
        "ACADEMIC_INFO": f"{compound_japanese}（{compound_name}）は大麻草に含まれる天然のカンナビノイドです。",
        
        "ACADEMIC_SOURCE": "学術文献より",
        
        "ACADEMIC_FEATURES_INTRO": f"{compound_name}の特徴をまとめると、こんな感じです。",
        
        "ACADEMIC_FEATURES_LIST": "\n".join([
            f"    <li><strong>特徴:</strong> {char}</li>" for char in characteristics
        ]),
        
        "MARKET_INFO_INTRO": f"市場で販売されている{compound_name}製品についての情報です。",
        
        "MARKET_FEATURES_LIST": "\n".join([
            f"    <li>{char}</li>" for char in characteristics[:3]
        ]),
        
        "MARKET_SOURCE": "業界メディア・サプライヤー情報",
        
        "UNKNOWN_FACTS": f"{compound_name}の正確な化学構造や純度は、製品によって異なる可能性があります。COA（分析証明書）で確認することを推奨します。",
        
        "REGULATION_INTRO": f"このセクションでは、{compound_name}の法的位置づけを確認します。",
        
        "JAPAN_REGULATION_INTRO": f"日本国内での{compound_name}の規制状況は以下の通りです。",
        
        "REGULATION_LAW_TITLE": "大麻取締法・麻薬及び向精神薬取締法",
        
        "REGULATION_LAW_DESCRIPTION": "大麻由来製品について、THC残留量が一定の限度値を超えると規制対象となります。",
        
        "REGULATION_LAW_DETAILS": "\n".join([
            "      <li><strong>油脂・粉末:</strong> 百万分中10の量（10 ppm）</li>",
            "      <li><strong>水溶液:</strong> 一億分中10の量（0.1 ppm）</li>",
            "      <li><strong>その他（電子タバコ等）:</strong> 百万分中の量（1 ppm）</li>",
        ]),
        
        "REGULATION_SOURCE": "厚生労働省",
        
        "JAPAN_REGULATION_NOTE": f"{compound_name}製品にTHCが含まれる場合、この限度値を超えると法的リスクが生じます。",
        
        "INTERNATIONAL_REGULATION_LIST": "\n".join([
            "    <li><strong>INCB:</strong> 国際的な規制状況</li>",
            "    <li><strong>EU:</strong> 各国の規制が異なる</li>",
            "    <li><strong>米国:</strong> 連邦法と州法の違い</li>",
        ]),
        
        "INTERNATIONAL_REGULATION_NOTE": "各国で規制が異なるため、最新の情報を確認してください。",
        
        "SAFETY_INTRO": f"{compound_name}の安全性に関する現時点での知見を整理します。",
        
        "SAFETY_KNOWN_LIST": "\n".join([
            f"    <li>{char}</li>" for char in characteristics[:3]
        ]),
        
        "SAFETY_UNKNOWN_LIST": "\n".join([
            "    <li><strong>臨床データ:</strong> 人間での安全性データは限定的</li>",
            "    <li><strong>相互作用:</strong> 他の薬剤との相互作用は不明</li>",
            "    <li><strong>長期影響:</strong> 長期使用時の影響は不明</li>",
        ]),
        
        "SAFETY_WARNING": f"{compound_name}製品を使用する前に、COAで含まれる成分を確認し、少量から始めてください。",
        
        "COMPARISON_INTRO": f"{compound_name}を他の主要カンナビノイドと並べて比較します。",
        
        "COMPARISON_HEADER_CELLS": "".join([
            f"        <th>{c}</th>" for c in [compound_name] + comparison_compounds
        ]),
        
        "COMPARISON_TABLE_ROWS": "\n".join([
            "      <tr>",
            "        <td>位置づけ</td>",
            f"        <td>{characteristics[0] if characteristics else '—'}</td>",
            f"        <td>{comparison_compounds[0]}</td>",
            "      </tr>",
        ]),
        
        "GT_INTRO": f"Google Trendsで{compound_name}の検索興味度を確認しました。",
        
        "GT_TABLE_ROWS": "\n".join([
            "        <tr>",
            f"          <td><strong>{compound_name}</strong></td>",
            "          <td class=\"num\">—</td>",
            "          <td class=\"num\">—</td>",
            "          <td class=\"num\">—</td>",
            "          <td>データ収集中</td>",
            "        </tr>",
        ]),
        
        "GT_FINDING": f"{compound_name}のGoogle Trendsデータは収集中です。",
        
        "X_TREND_SECTION": "<!-- X トレンドデータは収集後に追加 -->",
        
        "INGREDIENT_BUTTONS": "\n".join([
            f"""      <a href="/ingredient/{c.lower()}" class="ingredient-btn">
        <span class="name">{c}</span>
        <span class="desc">成分</span>
      </a>""" for c in comparison_compounds
        ]),
        
        "FAQ_LEGAL_ANSWER": f"{regulation_status}",
        "FAQ_COMPARISON_ANSWER": f"{comparison_compounds[0]}と{compound_name}は異なる性質のカンナビノイドです。",
        "FAQ_SAFETY_ANSWER": f"{compound_name}の安全性データは限定的です。",
        "FAQ_PRODUCT_ANSWER": f"{compound_name}製品を選ぶ際はCOAの確認を推奨します。",
        
        "FAQ_LEGAL_ANSWER_1": f"{regulation_status}が適用されます。",
        "FAQ_LEGAL_ANSWER_2": "THC残留量の限度値を確認してください。",
        
        "FAQ_COMPARISON_ANSWER_1": f"{comparison_compounds[0]}と{compound_name}は化学的に異なるカンナビノイドです。",
        "FAQ_COMPARISON_ANSWER_2": "受容体への作用や特性が異なります。",
        
        "FAQ_SAFETY_ANSWER_1": f"{compound_name}の安全性データは限定的です。",
        "FAQ_SAFETY_ANSWER_2": "既知の副作用については、臨床試験が必要です。",
        
        "FAQ_PRODUCT_ANSWER_1": f"{compound_name}製品を選ぶ際はCOAの確認を推奨します。",
        "FAQ_PRODUCT_ANSWER_2": "THC検出結果も必ず確認してください。",
        
        "TRUST_NOTE": f"本ページの内容は、学術文献・公的資料・業界メディアに基づき店長が確認の上で掲載しています。",
    }
    
    for key, value in section_data.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    
    # 出力先を確保
    output_path = Path(output_dir) / f"guide_{compound_slug}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ファイルに保存
    output_path.write_text(template)
    
    print(f"✅ 生成完了: {output_path}")
    print(f"   化合物: {compound_name} ({compound_japanese})")
    print(f"   規制状況: {regulation_status}")
    print(f"   ファイルサイズ: {output_path.stat().st_size:,} bytes")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="カンナビノイド化合物ガイドページを生成")
    parser.add_argument("--compound", "-c", required=True, help="化合物名 (例: CBN)")
    parser.add_argument("--japanese", "-j", required=True, help="日本語名 (例: カンナビノール)")
    parser.add_argument("--regulation", "-r", required=True, help="規制状況")
    parser.add_argument("--characteristics", "-k", nargs="+", required=True, help="特徴のリスト")
    parser.add_argument("--compare", nargs="+", default=["CBD", "CBG", "CBX"], help="比較対象")
    parser.add_argument("--output", "-o", default="publication", help="出力ディレクトリ")
    
    args = parser.parse_args()
    
    generate_compound_guide(
        compound_name=args.compound,
        compound_japanese=args.japanese,
        regulation_status=args.regulation,
        characteristics=args.characteristics,
        comparison_compounds=args.compare,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
