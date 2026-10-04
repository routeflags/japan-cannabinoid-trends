#!/bin/bash
# 12化合物のガイドページ一括生成スクリプト
# substance-dictionary 準拠（flagship/standard tier）

set -e

cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends

SCRIPT=".github/skills/generate-compound-guide/generate_compound_guide.py"

echo "=========================================="
echo "12化合物ガイドページ一括生成"
echo "=========================================="
echo ""

# 1. CBD (flagship)
echo "1. CBD (flagship)"
python3 "$SCRIPT" \
  --compound CBD \
  --japanese "カンナビジェロール" \
  --regulation "非規制（条件付き合法）THCフリー（0.00%）" \
  --characteristics "最も研究されているカンナビノイド" "非精神活性" "広範な市場展開" \
  --compare THC CBG CBN \
  --tier flagship
echo ""

# 2. CBG (flagship)
echo "2. CBG (flagship)"
python3 "$SCRIPT" \
  --compound CBG \
  --japanese "カンナビゲロール" \
  --regulation "非規制（条件付き合法）THCフリー（0.00%）" \
  --characteristics "カンナビノイドの前駆体" "非精神活性" "研究が進みつつある" \
  --compare CBD CBN THC \
  --tier flagship
echo ""

# 3. CBN (flagship)
echo "3. CBN (flagship)"
python3 "$SCRIPT" \
  --compound CBN \
  --japanese "カンナビノール" \
  --regulation "指定薬物（2026年6月1日施行）" \
  --characteristics "THCの酸化で生成" "催眠作用の可能性" "睡眠補助として注目" \
  --compare CBD CBG THC \
  --tier flagship
echo ""

# 4. THC (flagship)
echo "4. THC (flagship)"
python3 "$SCRIPT" \
  --compound THC \
  --japanese "テトラヒドロカンナビノール" \
  --regulation "規制（大麻取締法/麻薬向精神薬取締法）" \
  --characteristics "主要な精神活性カンナビノイド" "規制対象" "医療用途が研究されている" \
  --compare CBD CBN CBG \
  --tier flagship
echo ""

# 5. HHC (standard)
echo "5. HHC (standard)"
python3 "$SCRIPT" \
  --compound HHC \
  --japanese "ヘキサヒドロカンナビノール" \
  --regulation "指定薬物（2022年3月17日施行）" \
  --characteristics "THCの水素化で生成" "規制対象" "国際的にも規制強化" \
  --compare THC CBD CBG \
  --tier standard
echo ""

# 6. HHCH (standard)
echo "6. HHCH (standard)"
python3 "$SCRIPT" \
  --compound HHCH \
  --japanese "ヘキサヒドロカンナビヘキソール" \
  --regulation "指定薬物（2023年12月2日施行）" \
  --characteristics "THC類似の合成カンナビノイド" "規制対象" "規制後は検索需要が激減" \
  --compare THC HHC CBD \
  --tier standard
echo ""

# 7. THCH (standard)
echo "7. THCH (standard)"
python3 "$SCRIPT" \
  --compound THCH \
  --japanese "テトラヒドロカンナビヘキソール" \
  --regulation "指定薬物（2023年8月4日施行）" \
  --characteristics "ヘキシル鎖カンナビノイド" "規制対象" "強い精神活性が報告" \
  --compare THC HHC CBD \
  --tier standard
echo ""

# 8. THC-O (standard)
echo "8. THC-O (standard)"
python3 "$SCRIPT" \
  --compound THC-O \
  --japanese "テトラヒドロカンナビノール-O-アセテート" \
  --regulation "指定薬物（2023年3月20日施行）" \
  --characteristics "THCの半合成誘導体" "規制対象" "強い精神活性" \
  --compare THC HHC CBD \
  --tier standard
echo ""

# 9. THCV (standard)
echo "9. THCV (standard)"
python3 "$SCRIPT" \
  --compound THCV \
  --japanese "テトラヒドロカンナビバリ" \
  --regulation "非規制（監視対象）" \
  --characteristics "プロピル鎖カンナビノイド" "食欲抑制作用が研究されている" "規制候補" \
  --compare CBD CBG CBN \
  --tier standard
echo ""

# 10. CRDP (standard)
echo "10. CRDP (standard)"
python3 "$SCRIPT" \
  --compound CRDP \
  --japanese "CRDP（仮称）" \
  --regulation "非規制（監視対象）" \
  --characteristics "ヒドロキシ酸類似体" "2022年頃から流通" "規制候補" \
  --compare HHC CBD CBG \
  --tier standard
echo ""

# 11. H4CBH (standard)
echo "11. H4CBH (standard)"
python3 "$SCRIPT" \
  --compound H4CBH \
  --japanese "H4CBH（仮称）" \
  --regulation "非規制（監視対象）" \
  --characteristics "水素化カンナビノイド" "2025年頃から流通" "化学構造不明" \
  --compare HHC CBD CBG \
  --tier standard
echo ""

# 12. HHBD (standard)
echo "12. HHBD (standard)"
python3 "$SCRIPT" \
  --compound HHBD \
  --japanese "HHBD（仮称）" \
  --regulation "非規制（監視対象）" \
  --characteristics "水素化カンナビノイド" "2025年末から流通" "化学構造不明" \
  --compare HHC CBD CBG \
  --tier standard
echo ""

echo "=========================================="
echo "✅ 全12化合物のガイドページ生成完了"
echo "=========================================="
echo ""
echo "生成ファイル:"
ls -la publication/guide_*.html 2>/dev/null | awk '{print $NF, $5" bytes"}'
