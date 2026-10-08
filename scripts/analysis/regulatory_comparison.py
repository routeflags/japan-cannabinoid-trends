#!/usr/bin/env python3
"""
Regulatory Before/After Comparison Analysis
Batch 2: B2 (Rigor) + B3 (Integration)

Compounds analyzed:
- HHC: Regulated 2022-03-17
- THC-O: Regulated 2023-03-20
- THCH: Regulated 2023-08-04

Control: CBG (non-regulated)
"""

import json
import os
from datetime import datetime
from collections import Counter
import re

# =============================================================================
# Configuration
# =============================================================================

COMPOUNDS = {
    "HHC": {
        "regulation_date": "2022-03-17",
        "pre_period": "2021-09 ~ 2022-03",
        "post_period": "2022-04 ~ 2022-09",
        "data_dir": "datasets/cannabinoid-social-trends/data/raw/x/20261008T124749Z-hhc-pre-post-regulation",
        "pre_file": "hhc_pre.json",
        "post_file": "hhc_post.json",
    },
    "THC-O": {
        "regulation_date": "2023-03-20",
        "pre_period": "2022-09 ~ 2023-03",
        "post_period": "2023-04 ~ 2023-09",
        "data_dir": "datasets/cannabinoid-social-trends/data/raw/x/20261008T124749Z-thco-pre-post-regulation",
        "pre_file": "thco_pre.json",
        "post_file": "thco_post.json",
    },
    "THCH": {
        "regulation_date": "2023-08-04",
        "pre_period": "2023-02 ~ 2023-08",
        "post_period": "2023-09 ~ 2024-02",
        "data_dir": "datasets/cannabinoid-social-trends/data/raw/x/20261008T124749Z-thch-pre-post-regulation",
        "pre_file": "thch_pre.json",
        "post_file": "thch_post.json",
    },
}

CONTROL = {
    "name": "CBG",
    "data_file": "datasets/cannabinoid-social-trends/data/raw/x/20261008T124749Z-hhc-pre-post-regulation/cbg_control.json",
    "period": "2021-09 ~ 2022-09",
}

# =============================================================================
# Analysis Functions
# =============================================================================

def load_tweets(filepath: str) -> list:
    """Load tweets from JSON file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    return data

def extract_metrics(tweets: list) -> dict:
    """Extract engagement metrics from tweets."""
    if not tweets:
        return {"n": 0}

    n = len(tweets)
    
    # Extract likes (favorites)
    likes = []
    for t in tweets:
        like = t.get("favorites", t.get("likes", 0))
        if isinstance(like, str):
            try:
                like = int(like)
            except:
                like = 0
        likes.append(like)

    # Extract retweets
    retweets = []
    for t in tweets:
        rt = t.get("retweets", t.get("retweet_count", 0))
        if isinstance(rt, str):
            try:
                rt = int(rt)
            except:
                rt = 0
        retweets.append(rt)

    # Extract replies
    replies = []
    for t in tweets:
        reply = t.get("replies", t.get("reply_count", 0))
        if isinstance(reply, str):
            try:
                reply = int(reply)
            except:
                reply = 0
        replies.append(reply)

    # Unique users
    users = set()
    for t in tweets:
        user = t.get("screen_name", t.get("user", {}).get("screen_name", ""))
        if user:
            users.add(user)

    return {
        "n": n,
        "unique_users": len(users),
        "total_likes": sum(likes),
        "avg_likes": round(sum(likes) / n, 1) if n > 0 else 0,
        "median_likes": sorted(likes)[n // 2] if n > 0 else 0,
        "max_likes": max(likes) if likes else 0,
        "total_retweets": sum(retweets),
        "avg_retweets": round(sum(retweets) / n, 1) if n > 0 else 0,
        "total_replies": sum(replies),
        "avg_replies": round(sum(replies) / n, 1) if n > 0 else 0,
    }

def calculate_change_rate(pre_val: float, post_val: float) -> str:
    """Calculate percentage change."""
    if pre_val == 0:
        return "N/A"
    change = ((post_val - pre_val) / pre_val) * 100
    return f"{change:+.1f}%"

def main():
    """Main analysis pipeline."""
    
    print("=" * 70)
    print("Regulatory Before/After Comparison Analysis")
    print("Batch 2: B2 (Rigor) + B3 (Integration)")
    print("=" * 70)

    all_results = {}

    # Load control data
    control_tweets = load_tweets(CONTROL["data_file"])
    control_metrics = extract_metrics(control_tweets)
    print(f"\n--- Control: {CONTROL['name']} (n={control_metrics['n']}) ---")
    print(f"  Period: {CONTROL['period']}")
    print(f"  Avg likes: {control_metrics['avg_likes']}")

    # Analyze each compound
    for compound, config in COMPOUNDS.items():
        print(f"\n{'=' * 70}")
        print(f"Compound: {compound}")
        print(f"Regulation date: {config['regulation_date']}")
        print(f"Pre-period: {config['pre_period']}")
        print(f"Post-period: {config['post_period']}")
        print(f"{'=' * 70}")

        # Load data
        pre_tweets = load_tweets(os.path.join(config["data_dir"], config["pre_file"]))
        post_tweets = load_tweets(os.path.join(config["data_dir"], config["post_file"]))

        # Extract metrics
        pre_metrics = extract_metrics(pre_tweets)
        post_metrics = extract_metrics(post_tweets)

        # Calculate changes
        changes = {}
        for key in ["n", "unique_users", "total_likes", "avg_likes", "total_retweets", "avg_retweets"]:
            pre_val = pre_metrics.get(key, 0)
            post_val = post_metrics.get(key, 0)
            changes[key] = calculate_change_rate(pre_val, post_val)

        # Print results
        print(f"\n--- Basic Metrics ---")
        print(f"{'Metric':<20} {'Pre':>10} {'Post':>10} {'Change':>10}")
        print(f"{'-' * 50}")
        for key in ["n", "unique_users", "total_likes", "avg_likes", "total_retweets", "avg_retweets"]:
            print(f"{key:<20} {pre_metrics.get(key, 0):>10} {post_metrics.get(key, 0):>10} {changes[key]:>10}")

        # Compare with control
        print(f"\n--- Control Comparison ---")
        print(f"Post-regulation avg likes vs Control:")
        print(f"  {compound}: {post_metrics['avg_likes']}")
        print(f"  {CONTROL['name']}: {control_metrics['avg_likes']}")
        ratio = post_metrics['avg_likes'] / control_metrics['avg_likes'] if control_metrics['avg_likes'] > 0 else 0
        print(f"  Ratio: {ratio:.2f}x")

        # Store results
        all_results[compound] = {
            "regulation_date": config["regulation_date"],
            "pre_period": config["pre_period"],
            "post_period": config["post_period"],
            "pre_metrics": pre_metrics,
            "post_metrics": post_metrics,
            "changes": changes,
            "control_comparison": {
                "compound_post_avg_likes": post_metrics["avg_likes"],
                "control_avg_likes": control_metrics["avg_likes"],
                "ratio": round(ratio, 2),
            },
        }

    # Save results
    output_dir = "research"
    output_path = os.path.join(output_dir, "20261008-regulatory-comparison-batch2.json")

    with open(output_path, "w") as f:
        json.dump({"control": control_metrics, "compounds": all_results}, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_path}")
    print(f"{'=' * 70}")

    return all_results, control_metrics


if __name__ == "__main__":
    main()
