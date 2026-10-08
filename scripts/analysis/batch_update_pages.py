#!/usr/bin/env python3
"""
Batch update research pages with X and YouTube sections.
"""
import json
import os
from pathlib import Path
from collections import Counter
import glob

REPO_ROOT = Path(__file__).parent.parent.parent

# Load X classification data
with open(REPO_ROOT / "research/20261008-x-classification-batch1.json") as f:
    x_data = json.load(f)

# YouTube data paths per compound
YOUTUBE_PATHS = {
    "thc": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064821Z-youtube-thc/records.json",
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142508Z-youtube-thc-10years",
    ],
    "cbg": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064828Z-youtube-cbg/records.json",
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142430Z-youtube-cbg-10years",
    ],
    "cbn": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T132844Z-youtube-cbn-2026-09-01-to-2026-10-01/records.json",
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142547Z-youtube-cbn-10years",
    ],
    "thcv": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064857Z-youtube-thcv/records.json",
    ],
    "hhc": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T122515Z-youtube-hhc/records.json",
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064850Z-youtube-hhc/records.json",
    ],
    "thch": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T122605Z-youtube-thch/records.json",
    ],
    "thc-o": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T122647Z-youtube-thc-o/records.json",
    ],
    "h4cbh": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T125306Z-youtube-h4cbh/records.json",
    ],
    "hhbd": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T125348Z-youtube-hhbd/records.json",
    ],
    "hhch": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T125428Z-youtube-hhch/records.json",
    ],
    "crdp": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T125501Z-youtube-crdp/records.json",
    ],
    "crdh": [
        "datasets/cannabinoid-multi-trends/data/raw/youtube/20261008T125544Z-youtube-crdh/records.json",
    ],
}

def load_youtube_data(compound):
    """Load YouTube data for compound."""
    all_videos = []
    for path_template in YOUTUBE_PATHS.get(compound, []):
        # Handle glob patterns
        if "*" in path_template:
            matches = glob.glob(str(REPO_ROOT / path_template))
            for match in matches:
                if os.path.isfile(match):
                    try:
                        with open(match) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                all_videos.extend(data)
                    except:
                        pass
        elif os.path.isfile(REPO_ROOT / path_template):
            try:
                with open(REPO_ROOT / path_template) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_videos.extend(data)
            except:
                pass
    
    # Deduplicate by videoId
    seen = set()
    unique = []
    for item in all_videos:
        vid = item.get("id", {}).get("videoId")
        if vid and vid not in seen:
            seen.add(vid)
            unique.append(item)
    
    return unique

def analyze_youtube(videos):
    """Analyze YouTube videos."""
    if not videos:
        return None
    
    views = []
    durations = []
    channels = []
    
    for item in videos:
        sn = item.get("snippet", {})
        
        view = sn.get("views", 0)
        if isinstance(view, str):
            try: view = int(view)
            except: view = 0
        views.append(view)
        
        dur = sn.get("duration", 0)
        if isinstance(dur, str):
            try: dur = int(dur)
            except: dur = 0
        durations.append(dur)
        
        channels.append(sn.get("channelTitle", "Unknown"))
    
    # Top videos
    top_videos = sorted(videos, key=lambda x: x.get("snippet", {}).get("views", 0), reverse=True)[:5]
    
    # Channel distribution
    channel_counts = Counter(channels)
    
    return {
        "total": len(videos),
        "avg_views": sum(views) / len(views) if views else 0,
        "median_views": sorted(views)[len(views) // 2] if views else 0,
        "max_views": max(views) if views else 0,
        "min_views": min(views) if views else 0,
        "avg_duration": sum(durations) / len(durations) if durations else 0,
        "top_channels": channel_counts.most_common(5),
        "top_videos": [
            {
                "title": v.get("snippet", {}).get("title", "")[:50],
                "channel": v.get("snippet", {}).get("channelTitle", ""),
                "views": v.get("snippet", {}).get("views", 0),
                "duration": v.get("snippet", {}).get("duration", 0),
                "url": f"https://youtube.com/watch?v={v.get('id', {}).get('videoId', '')}"
            }
            for v in top_videos
        ]
    }

def generate_x_section(compound):
    """Generate X section HTML."""
    if compound not in x_data:
        return ""
    
    d = x_data[compound]
    results = d["results"]
    
    rows = ""
    for r in results:
        rows += f"""      <tr>
        <td>{r['category']}</td>
        <td>{r['count']}</td>
        <td>{r['percentage']}%</td>
        <td>{r['ci_95']}</td>
      </tr>
"""
    
    return f"""
<!-- ===== 独自データ：X (Twitter) 言及分析 ===== -->
<div>
  <h2 id="data-x">独自データ: {compound} の X (Twitter) 言及分析 <span>一次データ</span></h2>
  <p>データソース: X (Twitter) via Apify / 言語: 日本語 (lang:ja) / 有効件数: {d['n']}件 / 取得日: 2026-10-08</p>

  <h3>収集結果サマリー</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>元データ件数</td>
        <td>{d['raw_count']}件</td>
      </tr>
      <tr>
        <td>有効分類数</td>
        <td><strong>{d['n']}件</strong>（{d['excluded']}件除外）</td>
      </tr>
      <tr>
        <td>言語フィルタ</td>
        <td>日本語 (lang:ja)</td>
      </tr>
    </tbody>
  </table>

  <h3>コンテンツ分類結果（信頼区間付き）</h3>
  <table>
    <thead>
      <tr>
        <th>カテゴリ</th>
        <th>件数</th>
        <th>比率</th>
        <th>95% CI</th>
      </tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>

  <p><strong>方法:</strong> キーワードベースのルール分類。信頼区間は Wilson スコア法による95%信頼区間。</p>
  <p><strong>制約:</strong> ルールベース分類のため、文脈による誤分類の可能性がある。X 検索結果のサンプルであり、全投稿を網羅するものではない。</p>
</div>
"""

def generate_youtube_section(compound, yt_data):
    """Generate YouTube section HTML."""
    if not yt_data:
        return ""
    
    # Format numbers
    avg_views = f"{yt_data['avg_views']:,.0f}"
    median_views = f"{yt_data['median_views']:,}"
    max_views = f"{yt_data['max_views']:,}"
    min_views = f"{yt_data['min_views']:,}"
    avg_dur_min = yt_data['avg_duration'] / 60
    
    # Channel rows
    channel_rows = ""
    for ch, count in yt_data['top_channels']:
        pct = count / yt_data['total'] * 100
        channel_rows += f"""      <tr>
        <td>{ch}</td>
        <td>{count}</td>
        <td>{pct:.1f}%</td>
      </tr>
"""
    
    # Top videos rows
    video_rows = ""
    for i, v in enumerate(yt_data['top_videos'], 1):
        dur_min = v['duration'] // 60
        dur_sec = v['duration'] % 60
        views = f"{v['views']:,}" if isinstance(v['views'], int) else str(v['views'])
        video_rows += f"""      <tr>
        <td>{i}</td>
        <td>{v['title']}</td>
        <td>{v['channel']}</td>
        <td>{views}</td>
        <td>{dur_min}:{dur_sec:02d}</td>
      </tr>
"""
    
    return f"""
<!-- ===== 独自データ：YouTube トレンド ===== -->
<div>
  <h2 id="data-youtube">独自データ: {compound} の YouTube トレンド <span>一次データ</span></h2>
  <p>データソース: YouTube Search via Apify / 取得日: 2026-10-08</p>

  <h3>収集結果サマリー</h3>
  <table>
    <thead>
      <tr>
        <th>指標</th>
        <th>値</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>ユニーク動画数</td>
        <td><strong>{yt_data['total']}件</strong></td>
      </tr>
    </tbody>
  </table>

  <h3>再生数統計</h3>
  <table>
    <thead>
      <tr>
        <th>統計量</th>
        <th>再生数</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>平均</td>
        <td><strong>{avg_views}</strong></td>
      </tr>
      <tr>
        <td>中央値</td>
        <td>{median_views}</td>
      </tr>
      <tr>
        <td>最大</td>
        <td>{max_views}</td>
      </tr>
      <tr>
        <td>最小</td>
        <td>{min_views}</td>
      </tr>
    </tbody>
  </table>

  <h3>動画長統計</h3>
  <table>
    <thead>
      <tr>
        <th>統計量</th>
        <th>動画長</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>平均</td>
        <td><strong>{avg_dur_min:.1f}分</strong>（{yt_data['avg_duration']:.0f}秒）</td>
      </tr>
    </tbody>
  </table>

  <h3>チャンネル分布（上位5）</h3>
  <table>
    <thead>
      <tr>
        <th>チャンネル</th>
        <th>件数</th>
        <th>比率</th>
      </tr>
    </thead>
    <tbody>
{channel_rows}    </tbody>
  </table>

  <h3>上位動画（再生数順）</h3>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>タイトル</th>
        <th>チャンネル</th>
        <th>再生数</th>
        <th>長さ</th>
      </tr>
    </thead>
    <tbody>
{video_rows}    </tbody>
  </table>

  <p><strong>制約:</strong> YouTube 検索結果のサンプルであり、全動画を網羅するものではない。再生数は取得日時点の値であり、変動する可能性がある。</p>
</div>
"""

def update_page(compound):
    """Update a research page."""
    page_path = REPO_ROOT / f"publication/research_{compound}.html"
    if not page_path.exists():
        print(f"⚠️  {compound}: ページが存在しない")
        return False
    
    content = page_path.read_text(encoding="utf-8")
    original = content
    
    # Generate X section
    x_section = generate_x_section(compound.upper())
    
    # Generate YouTube section
    yt_videos = load_youtube_data(compound)
    yt_data = analyze_youtube(yt_videos)
    yt_section = generate_youtube_section(compound.upper(), yt_data) if yt_data else ""
    
    # Insert X section before regulation section
    if x_section and 'id="data-x"' not in content:
        if '<!-- ===== 規制状況 ===== -->' in content:
            content = content.replace('<!-- ===== 規制状況 ===== -->', x_section + '\n\n<!-- ===== 規制状況 ===== -->')
        elif '</body>' in content:
            content = content.replace('</body>', x_section + '\n\n</body>')
    
    # Insert YouTube section before citation section
    if yt_section and 'id="data-youtube"' not in content:
        if '<!-- ===== 引用情報 ===== -->' in content:
            content = content.replace('<!-- ===== 引用情報 ===== -->', yt_section + '\n\n<!-- ===== 引用情報 ===== -->')
        elif '</body>' in content:
            content = content.replace('</body>', yt_section + '\n\n</body>')
    
    if content != original:
        page_path.write_text(content, encoding="utf-8")
        print(f"✅ {compound}: 更新完了")
        return True
    else:
        print(f"⚠️  {compound}: 変更なし")
        return False

# Main
compounds = ["thc", "cbg", "cbn", "thcv", "thch", "hhc", "thc-o", "h4cbh", "hhbd", "hhch", "crdp", "crdh"]

print("=" * 60)
print("Research Pages Batch Update")
print("=" * 60)
print()

updated = 0
for compound in compounds:
    if update_page(compound):
        updated += 1

print()
print(f"更新完了: {updated}/{len(compounds)}")
