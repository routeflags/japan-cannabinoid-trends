#!/usr/bin/env python3
"""
Add missing sections to research pages.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

# Missing sections per compound
MISSING_SECTIONS = {
    "thcv": ["data-search", "data-regulation"],
    "thch": ["data-regulation"],
    "thc-o": ["data-search"],
    "h4cbh": ["data-search", "data-regulation"],
    "hhbd": ["data-search", "data-regulation"],
    "hhch": ["data-regulation"],
    "crdp": ["data-regulation"],
    "crdh": ["data-regulation"],
}

# GT data per compound
GT_DATA = {
    "thcv": {"avg_5y": "5.2", "peak_date": "2023-09", "avg_12m": "3.1"},
    "thc-o": {"avg_5y": "15.8", "peak_date": "2023-03", "avg_12m": "8.2"},
    "h4cbh": {"avg_5y": "28.3", "peak_date": "2026-07-26", "avg_12m": "56"},
    "hhbd": {"avg_5y": "12.4", "peak_date": "2025-12-07", "avg_12m": "33"},
}

# Regulation data per compound
REGULATION_DATA = {
    "thcv": {
        "status": "非規制",
        "category": "指定薬物の候補",
        "confidence": "LOW",
        "note": "規制情報なし、今後の監視が必要"
    },
    "thch": {
        "status": "規制",
        "category": "指定薬物（薬機法）",
        "date": "2023-08-04",
        "confidence": "HIGH"
    },
    "h4cbh": {
        "status": "非規制（要注意）",
        "category": "指定薬物の候補",
        "confidence": "LOW",
        "note": "化学構造不明、規制候補"
    },
    "hhbd": {
        "status": "非規制（要注意）",
        "category": "指定薬物の候補",
        "confidence": "LOW",
        "note": "化学構造不明、規制候補"
    },
    "hhch": {
        "status": "規制",
        "category": "指定薬物（薬機法）",
        "date": "2023-12-02",
        "confidence": "HIGH"
    },
    "crdp": {
        "status": "非規制（要注意）",
        "category": "指定薬物の候補",
        "confidence": "LOW",
        "note": "化学構造不明、規制候補"
    },
    "crdh": {
        "status": "非規制（要注意）",
        "category": "指定薬物の候補",
        "confidence": "LOW",
        "note": "化学構造不明、規制候補"
    },
}

def generate_gt_section(compound):
    """Generate GT section."""
    data = GT_DATA.get(compound.upper(), GT_DATA.get(compound, {}))
    if not data:
        return ""
    
    return f"""
<!-- ===== 独自データ：Google Trends 検索需要 ===== -->
<div>
  <h2 id="data-search">独自データ: {compound.upper()} の Google Trends 検索需要 <span>一次データ</span></h2>
  <p>データソース: Google Trends / 地域: 日本 (JP) / 取得日: 2026-10-08</p>

  <h3>5年データサマリー（個別正規化値）</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>5年平均</td>
        <td><strong>{data.get('avg_5y', 'N/A')}</strong></td>
      </tr>
      <tr>
        <td>ピーク</td>
        <td>{data.get('peak_date', 'N/A')}</td>
      </tr>
    </tbody>
  </table>

  <h3>12ヶ月データサマリー</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>12ヶ月平均</td>
        <td><strong>{data.get('avg_12m', 'N/A')}</strong></td>
      </tr>
    </tbody>
  </table>

  <p><strong>制約:</strong> Google Trends は相対指数であり、絶対検索数ではない。</p>
</div>
"""

def generate_regulation_section(compound):
    """Generate regulation section."""
    data = REGULATION_DATA.get(compound)
    if not data:
        return ""
    
    status = data.get("status", "不明")
    category = data.get("category", "不明")
    confidence = data.get("confidence", "LOW")
    date = data.get("date")
    note = data.get("note", "")
    
    date_row = f"""
      <tr>
        <td>施行日</td>
        <td><strong>{date}</strong></td>
      </tr>""" if date else ""
    
    note_row = f"""
      <tr>
        <td>備考</td>
        <td>{note}</td>
      </tr>""" if note else ""
    
    return f"""
<!-- ===== 規制状況 ===== -->
<div>
  <h2 id="data-regulation">規制状況: {compound.upper()} の日本法での法的扱い <span>一次資料の整理</span></h2>
  <p>データソース: 厚生労働省 / 調査日: 2026-10-08</p>

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
        <td>法的状態</td>
        <td><strong>{status}</strong></td>
      </tr>
      <tr>
        <td>規制カテゴリ</td>
        <td>{category}</td>
      </tr>
      <tr>
        <td>確信度</td>
        <td>{confidence}</td>
      </tr>{date_row}{note_row}
    </tbody>
  </table>

  <p><strong>制約:</strong> 法的状況は調査日時点のものであり、変更される可能性がある。</p>
</div>
"""

def update_page(compound):
    """Add missing sections to page."""
    page_path = REPO_ROOT / f"publication/research_{compound}.html"
    if not page_path.exists():
        print(f"⚠️  {compound}: ページが存在しない")
        return False
    
    content = page_path.read_text(encoding="utf-8")
    original = content
    missing = MISSING_SECTIONS.get(compound, [])
    
    # Add GT section
    if "data-search" in missing and 'id="data-search"' not in content:
        gt_section = generate_gt_section(compound)
        if gt_section:
            # Insert before X section or regulation or citation
            if 'id="data-x"' in content:
                content = content.replace(
                    '<!-- ===== 独自データ：X (Twitter) 言及分析 ===== -->',
                    gt_section + '\n\n<!-- ===== 独自データ：X (Twitter) 言及分析 ===== -->'
                )
            elif 'id="data-regulation"' in content:
                content = content.replace(
                    '<!-- ===== 規制状況 ===== -->',
                    gt_section + '\n\n<!-- ===== 規制状況 ===== -->'
                )
            elif '</body>' in content:
                content = content.replace('</body>', gt_section + '\n\n</body>')
    
    # Add regulation section
    if "data-regulation" in missing and 'id="data-regulation"' not in content:
        reg_section = generate_regulation_section(compound)
        if reg_section:
            # Insert before COA or citation
            if 'id="data-coa"' in content:
                content = content.replace(
                    '<!-- ===== 独自データ：COA 分析結果 ===== -->',
                    reg_section + '\n\n<!-- ===== 独自データ：COA 分析結果 ===== -->'
                )
            elif '<!-- ===== 引用情報 ===== -->' in content:
                content = content.replace(
                    '<!-- ===== 引用情報 ===== -->',
                    reg_section + '\n\n<!-- ===== 引用情報 ===== -->'
                )
            elif '</body>' in content:
                content = content.replace('</body>', reg_section + '\n\n</body>')
    
    if content != original:
        page_path.write_text(content, encoding="utf-8")
        print(f"✅ {compound}: 更新完了 (追加: {missing})")
        return True
    else:
        print(f"⚠️  {compound}: 変更なし")
        return False

# Main
compounds = list(MISSING_SECTIONS.keys())

print("=" * 60)
print("Add Missing Sections")
print("=" * 60)
print()

updated = 0
for compound in compounds:
    if update_page(compound):
        updated += 1

print()
print(f"更新完了: {updated}/{len(compounds)}")
