#!/usr/bin/env python3
"""
X Data Content Classification + Wilson Confidence Intervals
Batch 1: A2 (Accuracy) + A3 (Reliability)

Classification categories (consistent with existing methodology):
- 製品宣伝・販売 (Product promotion/sales)
- 製品レビュー (Product review)
- 会話・引用 (Conversation/quotation)
- その他 (Other)

Confidence intervals: Wilson score method (95%)
"""

import json
import os
import re
from pathlib import Path
from math import sqrt

# =============================================================================
# Classification Rules
# =============================================================================

CATEGORY_RULES = {
    "製品宣伝・販売": [
        "販売", "通販", "オンラインショップ", "購入", "カート", "在庫",
        "セール", "割引", "限定", "新作", "新商品", "入荷", "再入荷",
        "発売", "リリース", "予約", "価格", "円", "送料無料",
        "thch-vape", "shop", "store", "buy", "sale", "order",
        "おすすめ商品", "商品一覧", "ポイント還元",
    ],
    "製品レビュー": [
        "レビュー", "評価", "感想", "体感", "使ってみた", "使ってみた",
        "口コミ", "評判", "良かった", "悪かった", "感じた", "効果",
        "満足", "不満", "星", "おすすめ", "非おすすめ",
        "レビュー動画", "レビュー記事", "使用報告",
    ],
    "会話・引用": [
        "RT", "リツイート", "引用", "リプ", "返信", "フォロー",
        "ありがとう", "お疲れ", "同意", "賛成", "反対",
        "質問", "教えて", "知りたい", "教えてください",
        "interesting", "wow", "nice", "good", "bad",
        "?", "！",
    ],
}

# Exclude patterns (if matched, classify as 除外)
EXCLUDE_PATTERNS = [
    r"https?://\S+\.(jpg|png|gif|mp4)",  # Media-only posts
    r"^.{0,10}$",  # Very short posts
]

def classify_tweet(text: str) -> str:
    """Classify a tweet into one of four categories."""
    if not text or len(text.strip()) < 10:
        return "除外"

    # Check exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text):
            return "除外"

    text_lower = text.lower()

    # Score each category
    scores = {}
    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[category] = score

    # Return highest scoring category
    max_score = max(scores.values())
    if max_score == 0:
        return "その他"

    for category, score in scores.items():
        if score == max_score:
            return category

    return "その他"


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple:
    """
    Calculate Wilson score confidence interval.
    Returns (lower_bound, upper_bound) as percentages.
    """
    if n == 0:
        return (0.0, 0.0)

    p = successes / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = (z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denominator

    lower = max(0, (center - margin) * 100)
    upper = min(100, (center + margin) * 100)

    return (round(lower, 1), round(upper, 1))


def analyze_compound(name: str, records: list) -> dict:
    """Analyze a compound's X data with classification and CIs."""
    # Extract texts
    texts = []
    for r in records:
        text = r.get("text", "") or r.get("full_text", "")
        if text:
            texts.append(text)

    # Classify
    classifications = []
    for text in texts:
        cat = classify_tweet(text)
        if cat != "除外":
            classifications.append(cat)

    n = len(classifications)
    if n == 0:
        return {"name": name, "n": 0, "error": "No valid records"}

    # Count categories
    categories = ["製品宣伝・販売", "製品レビュー", "会話・引用", "その他"]
    counts = {cat: classifications.count(cat) for cat in categories}

    # Calculate proportions and CIs
    results = []
    for cat in categories:
        count = counts[cat]
        pct = round(count / n * 100, 1)
        ci_low, ci_high = wilson_ci(count, n)
        results.append({
            "category": cat,
            "count": count,
            "percentage": pct,
            "ci_95": f"[{ci_low}%, {ci_high}%]",
        })

    return {
        "name": name,
        "n": n,
        "raw_count": len(records),
        "excluded": len(records) - n,
        "results": results,
    }


def main():
    """Main classification pipeline."""

    # Define data sources for unclassified compounds
    data_sources = {
        "HHC": "datasets/cannabinoid-multi-trends/data/raw/x/20261002T064454Z-x-hhc/records.json",
        "THCV": "datasets/cannabinoid-multi-trends/data/raw/x/20261002T064532Z-x-thcv/records.json",
        "THC-O": "datasets/cannabinoid-multi-trends/data/raw/x/20261002T064540Z-x-thc-o/records.json",
        "THCH": "datasets/cannabinoid-multi-trends/data/raw/x/20261002T064549Z-x-thch/records.json",
        "H4CBH": "datasets/cannabinoid-social-trends/data/raw/x/20261005T140548Z-h4cbh-hhbd-expanded/h4cbh_expanded.json",
        "HHBD": "datasets/cannabinoid-social-trends/data/raw/x/20261005T140548Z-h4cbh-hhbd-expanded/hhbd_expanded.json",
        "HHCH": "datasets/cannabinoid-social-trends/data/raw/x/20261008T121158Z-hhch/records.json",
        "CRDP": "datasets/cannabinoid-social-trends/data/raw/x/20261008T121238Z-crdp/records.json",
        "CRDH": "datasets/cannabinoid-social-trends/data/raw/x/20261008T102022Z-crdh/records.json",
    }

    # Also re-analyze already classified compounds with CIs
    reclassify_sources = {
        "CBD": "datasets/cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds/cbd.json",
        "CBG": "datasets/cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds/cbg.json",
        "CBN": "datasets/cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds/cbn.json",
        "THC": "datasets/cannabinoid-social-trends/data/raw/x/20261006T104633Z-main-compounds/thc.json",
    }

    all_results = {}

    print("=" * 70)
    print("X Data Content Classification + Wilson CI")
    print("Batch 1: A2 (Accuracy) + A3 (Reliability)")
    print("=" * 70)

    # Process unclassified compounds
    print("\n--- New Classification ---\n")
    for name, path in data_sources.items():
        if not os.path.exists(path):
            print(f"⚠️  {name}: File not found ({path})")
            continue

        with open(path) as f:
            records = json.load(f)

        result = analyze_compound(name, records)
        all_results[name] = result

        if "error" in result:
            print(f"⚠️  {name}: {result['error']}")
        else:
            print(f"✅ {name} (n={result['n']}, raw={result['raw_count']})")
            for r in result["results"]:
                print(f"   {r['category']}: {r['count']} ({r['percentage']}%) CI={r['ci_95']}")

    # Re-analyze with CIs
    print("\n--- Re-analysis with Confidence Intervals ---\n")
    for name, path in reclassify_sources.items():
        if not os.path.exists(path):
            print(f"⚠️  {name}: File not found")
            continue

        with open(path) as f:
            records = json.load(f)

        result = analyze_compound(name, records)
        all_results[name] = result

        print(f"✅ {name} (n={result['n']})")
        for r in result["results"]:
            print(f"   {r['category']}: {r['count']} ({r['percentage']}%) CI={r['ci_95']}")

    # Save results
    output_dir = "research"
    output_path = os.path.join(output_dir, "20261008-x-classification-batch1.json")

    with open(output_path, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_path}")
    print(f"Total compounds analyzed: {len(all_results)}")
    print(f"{'=' * 70}")

    return all_results


if __name__ == "__main__":
    main()
