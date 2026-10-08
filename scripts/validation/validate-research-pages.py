#!/usr/bin/env python3
"""
Research Page Completeness Validator

調査ページの必須セクションが揃っているかを検証する。
利用可能なデータがあるのにページに反映されていない場合、
ページ更新遅延を検出する。

Usage:
    python3 scripts/validation/validate-research-pages.py
    python3 scripts/validation/validate-research-pages.py --compound CBD
    python3 scripts/validation/validate-research-pages.py --fix-report
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
PUBLICATION_DIR = REPO_ROOT / "publication"
DATASETS_DIR = REPO_ROOT / "datasets"
RESEARCH_DIR = REPO_ROOT / "research"

# Required sections in research pages
REQUIRED_SECTIONS = {
    "methodology": "調査方法",
    "data-search": "Google Trends",
    "data-regulation": "規制状況",
    "citation": "引用情報",
}

# Conditional sections (required if data exists)
CONDITIONAL_SECTIONS = {
    "data-x": {
        "name": "X (Twitter)",
        "data_paths": [
            "datasets/cannabinoid-social-trends/data/raw/x/*-{compound}*",
            "datasets/cannabinoid-multi-trends/data/raw/x/*-{compound}*",
        ],
    },
    "data-youtube": {
        "name": "YouTube",
        "data_paths": [
            "datasets/cannabinoid-multi-trends/data/raw/youtube/*-{compound}*",
        ],
    },
    "data-coa": {
        "name": "COA",
        "data_paths": [
            "datasets/cbx-product-coa/data/raw/coa/{compound}*",
        ],
    },
}

# Data depth requirements (minimum quantitative content)
DATA_DEPTH_REQUIREMENTS = {
    "data-youtube": {
        "min_tables": 2,
        "required_keywords": ["再生数", "チャンネル", "動画"],
    },
    "data-x": {
        "min_tables": 1,
        "required_keywords": ["製品宣伝", "会話", "95%"],
    },
    "data-search": {
        "min_tables": 2,
        "required_keywords": ["5年", "12ヶ月", "平均"],
    },
}

# Compounds to check
COMPOUNDS = [
    "cbd", "thc", "cbg", "cbn", "thcv", "thch",
    "hhc", "thc-o", "h4cbh", "hhbd", "hhch", "crdp", "crdh"
]


# =============================================================================
# Detection Functions
# =============================================================================

def find_page(compound: str) -> Path | None:
    """Find research page for compound."""
    page_path = PUBLICATION_DIR / f"research_{compound}.html"
    if page_path.exists():
        return page_path
    # Try alternative naming
    alt_path = PUBLICATION_DIR / f"research_{compound.replace('-', '_')}.html"
    if alt_path.exists():
        return alt_path
    return None


def check_section_exists(html_content: str, section_id: str) -> bool:
    """Check if section exists in HTML."""
    return f'id="{section_id}"' in html_content


def count_tables_in_section(html_content: str, section_id: str) -> int:
    """Count tables in a specific section."""
    # Find section start
    section_pattern = f'id="{section_id}"'
    section_start = html_content.find(section_pattern)
    if section_start == -1:
        return 0

    # Find next section or end
    next_section = re.search(r'<h2 id="[^"]*">', html_content[section_start + len(section_pattern):])
    if next_section:
        section_end = section_start + len(section_pattern) + next_section.start()
    else:
        section_end = len(html_content)

    section_content = html_content[section_start:section_end]
    return section_content.count("<table")


def check_keywords_in_section(html_content: str, section_id: str, keywords: List[str]) -> Tuple[bool, List[str]]:
    """Check if required keywords exist in section."""
    section_pattern = f'id="{section_id}"'
    section_start = html_content.find(section_pattern)
    if section_start == -1:
        return False, keywords

    next_section = re.search(r'<h2 id="[^"]*">', html_content[section_start + len(section_pattern):])
    if next_section:
        section_end = section_start + len(section_pattern) + next_section.start()
    else:
        section_end = len(html_content)

    section_content = html_content[section_start:section_end]

    found = []
    missing = []
    for kw in keywords:
        if kw in section_content:
            found.append(kw)
        else:
            missing.append(kw)

    return len(missing) == 0, missing


def has_data_for_section(compound: str, section_id: str) -> bool:
    """Check if data exists for a conditional section."""
    section_config = CONDITIONAL_SECTIONS.get(section_id)
    if not section_config:
        return False

    import glob

    for data_path_template in section_config["data_paths"]:
        # Replace compound placeholder
        data_path = data_path_template.replace("{compound}", compound)

        # Use glob pattern matching
        matches = glob.glob(str(REPO_ROOT / data_path))

        # Filter matches to avoid false positives (e.g., HHC matching HHCH)
        filtered_matches = []
        for match in matches:
            filename = os.path.basename(match).lower()
            compound_lower = compound.lower()

            # For COA files, check if filename starts with compound name
            # followed by a non-alphanumeric character or end of string
            if section_id == "data-coa":
                if filename.startswith(compound_lower):
                    rest = filename[len(compound_lower):]
                    # Check that next char is not alphanumeric (avoid HHC matching HHCH)
                    if not rest or not rest[0].isalnum():
                        filtered_matches.append(match)
            else:
                filtered_matches.append(match)

        if filtered_matches:
            return True

        # Also try uppercase compound
        data_path_upper = data_path_template.replace("{compound}", compound.upper())
        matches_upper = glob.glob(str(REPO_ROOT / data_path_upper))

        filtered_upper = []
        for match in matches_upper:
            filename = os.path.basename(match)
            compound_upper = compound.upper()

            if section_id == "data-coa":
                if filename.startswith(compound_upper):
                    rest = filename[len(compound_upper):]
                    if not rest or not rest[0].isalnum():
                        filtered_upper.append(match)
            else:
                filtered_upper.append(match)

        if filtered_upper:
            return True

    return False


# =============================================================================
# Validation Main
# =============================================================================

def validate_compound(compound: str) -> Dict:
    """Validate a single compound's research page."""
    result = {
        "compound": compound.upper(),
        "page_exists": False,
        "issues": [],
        "warnings": [],
        "passed": True,
    }

    # Find page
    page_path = find_page(compound)
    if not page_path:
        result["issues"].append(f"調査ページが存在しない: research_{compound}.html")
        result["passed"] = False
        return result

    result["page_exists"] = True
    result["page_path"] = str(page_path.relative_to(REPO_ROOT))

    # Read HTML content
    html_content = page_path.read_text(encoding="utf-8")

    # Check required sections
    for section_id, section_name in REQUIRED_SECTIONS.items():
        if not check_section_exists(html_content, section_id):
            result["issues"].append(f"必須セクション欠落: {section_name} (id={section_id})")
            result["passed"] = False

    # Check conditional sections (data exists but not in page = update delay)
    for section_id, section_config in CONDITIONAL_SECTIONS.items():
        section_name = section_config["name"]
        data_exists = has_data_for_section(compound, section_id)
        page_has_section = check_section_exists(html_content, section_id)

        if data_exists and not page_has_section:
            result["issues"].append(
                f"ページ更新遅延: {section_name} データはあるがセクションがない"
            )
            result["passed"] = False
        elif page_has_section:
            # Check data depth requirements
            depth_req = DATA_DEPTH_REQUIREMENTS.get(section_id, {})
            min_tables = depth_req.get("min_tables", 1)
            required_keywords = depth_req.get("required_keywords", [])

            # Count tables
            table_count = count_tables_in_section(html_content, section_id)
            if table_count < min_tables:
                result["warnings"].append(
                    f"{section_name}: テーブル不足 ({table_count}/{min_tables})"
                )

            # Check keywords
            if required_keywords:
                has_all, missing = check_keywords_in_section(html_content, section_id, required_keywords)
                if not has_all:
                    result["warnings"].append(
                        f"{section_name}: 必須キーワード欠落 {missing}"
                    )

    return result


def main():
    """Main validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate research page completeness")
    parser.add_argument("--compound", help="Validate single compound")
    parser.add_argument("--fix-report", action="store_true", help="Generate fix report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    compounds = [args.compound.lower()] if args.compound else COMPOUNDS

    print("=" * 70)
    print("Research Page Completeness Validator")
    print("=" * 70)
    print()

    all_results = []
    total_issues = 0
    total_warnings = 0

    for compound in compounds:
        result = validate_compound(compound)
        all_results.append(result)

        # Print result
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['compound']}")

        if args.verbose or not result["passed"]:
            for issue in result["issues"]:
                print(f"   ❌ {issue}")
            for warning in result["warnings"]:
                print(f"   ⚠️  {warning}")

        total_issues += len(result["issues"])
        total_warnings += len(result["warnings"])

    print()
    print("=" * 70)
    print("サマリー")
    print("=" * 70)
    print(f"  検証化合物数: {len(compounds)}")
    print(f"  合格: {sum(1 for r in all_results if r['passed'])}")
    print(f"  不合格: {sum(1 for r in all_results if not r['passed'])}")
    print(f"  イシュー: {total_issues}")
    print(f"  警告: {total_warnings}")

    # Generate fix report
    if args.fix_report and total_issues > 0:
        print()
        print("=" * 70)
        print("修正レポート")
        print("=" * 70)

        for result in all_results:
            if result["issues"]:
                print(f"\n{result['compound']}:")
                for issue in result["issues"]:
                    print(f"  - {issue}")

    # Exit code
    if total_issues > 0:
        print()
        print("❌ ページ更新遅延または必須セクション欠落を検出しました")
        sys.exit(1)
    else:
        print()
        print("✅ 全ページが最新です")
        sys.exit(0)


if __name__ == "__main__":
    main()
