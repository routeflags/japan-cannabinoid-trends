#!/usr/bin/env python3
"""
X データ コンテンツ分類 + kappa 検証
CBD, CBG, CBN, THC の X データを分類し、信頼性を検証する。
"""

import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple

# 分類カテゴリ
CATEGORIES = ["製品宣伝・販売", "製品レビュー", "会話・引用", "その他"]

# コーダー1（メイン分類）
def classify_coder1(text: str, screen_name: str = "") -> str:
    """コーダー1: 詳細ルールベース分類"""
    text_lower = text.lower()
    
    # 販売キーワード
    sale_kw = [
        "取扱", "再入荷", "新規", "価格", "円", "品揃え", "発送", "販売",
        "在庫", "通販", "注文", "購入", "お届け", "セール", "限定", "特価"
    ]
    
    # レビューキーワード
    review_kw = [
        "使って", "使用感", "効果", "感じ", "味", "香り",
        "お気に入り", "試した", "レビュー", "感想", "好み", "飲んだ", "食べた"
    ]
    
    # 会話キーワード
    conv_kw = ["@", "リプ", "返信", "質問", "教えて", "どう", "何", "どの"]
    
    # カウント
    sale_count = sum(1 for kw in sale_kw if kw in text)
    review_count = sum(1 for kw in review_kw if kw in text)
    conv_count = sum(1 for kw in conv_kw if kw in text)
    
    # メンションがあれば会話
    if "@" in text and conv_count > 0:
        return "会話・引用"
    
    # 最多カテゴリ選択
    counts = {
        "製品宣伝・販売": sale_count,
        "製品レビュー": review_count,
        "会話・引用": conv_count
    }
    
    max_count = max(counts.values())
    
    if max_count == 0:
        return "その他"
    
    max_cats = [k for k, v in counts.items() if v == max_count]
    if len(max_cats) > 1:
        return "その他"
    
    return max_cats[0]

# コーダー2（簡易分類）
def classify_coder2(text: str) -> str:
    """コーダー2: 簡易ルールベース分類"""
    # 販売
    sale_markers = ["円", "通販", "販売", "取扱", "価格", "在庫"]
    if any(m in text for m in sale_markers):
        return "製品宣伝・販売"
    
    # レビュー
    review_markers = ["使って", "効果", "感想", "レビュー", "味"]
    if any(m in text for m in review_markers):
        return "製品レビュー"
    
    # 会話
    if "@" in text:
        return "会話・引用"
    
    return "その他"

def cohen_kappa(c1: List[str], c2: List[str]) -> Tuple[float, Dict]:
    """Cohen's kappa 計算"""
    n = len(c1)
    if n == 0:
        return 0.0, {}
    
    agreements = sum(1 for a, b in zip(c1, c2) if a == b)
    obs_agreement = agreements / n
    
    counter1 = Counter(c1)
    counter2 = Counter(c2)
    
    exp_agreement = sum(
        (counter1[cat] / n) * (counter2[cat] / n)
        for cat in CATEGORIES
    )
    
    if exp_agreement == 1:
        kappa = 1.0
    else:
        kappa = (obs_agreement - exp_agreement) / (1 - exp_agreement)
    
    stats = {
        "n": n,
        "observed_agreement": obs_agreement,
        "expected_agreement": exp_agreement,
        "kappa": kappa,
        "coder1_dist": dict(counter1),
        "coder2_dist": dict(counter2)
    }
    
    return kappa, stats

def interpret_kappa(k: float) -> str:
    """kappa 値の解釈"""
    if k < 0:
        return "Poor"
    elif k < 0.20:
        return "Slight"
    elif k < 0.40:
        return "Fair"
    elif k < 0.60:
        return "Moderate"
    elif k < 0.80:
        return "Substantial"
    else:
        return "Almost perfect"

def main():
    """メイン処理"""
    base_dir = Path("datasets/cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds")
    
    print("=" * 60)
    print("X データ コンテンツ分類 + kappa 検証")
    print("=" * 60)
    
    results = {}
    
    for compound in ["cbd", "cbg", "cbn", "thc"]:
        filepath = base_dir / f"{compound}.json"
        if not filepath.exists():
            print(f"\n⚠️  {compound}: ファイルなし")
            continue
        
        with open(filepath) as f:
            records = json.load(f)
        
        # 分類実行
        coder1 = [classify_coder1(r.get("text", ""), r.get("screen_name", "")) for r in records]
        coder2 = [classify_coder2(r.get("text", "")) for r in records]
        
        # kappa 計算
        kappa, stats = cohen_kappa(coder1, coder2)
        
        print(f"\n--- {compound.upper()} (n={stats['n']}) ---")
        print(f"  観測一致率: {stats['observed_agreement']:.1%}")
        print(f"  期待一致率: {stats['expected_agreement']:.1%}")
        print(f"  Cohen's kappa: {kappa:.3f} ({interpret_kappa(kappa)})")
        print()
        
        print("  コーダー1 の分布:")
        for cat in CATEGORIES:
            count = stats['coder1_dist'].get(cat, 0)
            pct = count / stats['n'] * 100
            print(f"    {cat}: {count} ({pct:.1f}%)")
        
        results[compound] = {
            "kappa": kappa,
            "interpretation": interpret_kappa(kappa),
            "stats": stats,
            "classifications": coder1
        }
    
    print("\n" + "=" * 60)
    print("サマリー")
    print("=" * 60)
    
    for compound, data in results.items():
        dist = data['stats']['coder1_dist']
        n = data['stats']['n']
        print(f"\n{compound.upper()} (n={n}, kappa={data['kappa']:.3f}):")
        for cat in CATEGORIES:
            count = dist.get(cat, 0)
            pct = count / n * 100
            print(f"  {cat}: {count} ({pct:.1f}%)")
    
    # 結果を保存
    output = {
        compound: {
            "kappa": data["kappa"],
            "interpretation": data["interpretation"],
            "n": data["stats"]["n"],
            "distribution": data["stats"]["coder1_dist"]
        }
        for compound, data in results.items()
    }
    
    output_path = Path("research/20261006-x-content-classification.json")
    with open(output_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果を保存しました: {output_path}")

if __name__ == "__main__":
    main()
