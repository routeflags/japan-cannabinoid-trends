#!/bin/bash
# 2020-01〜2026-12 の月次データを1ヶ月ずつ収集する（cron 用ラッパー）
#
# 使い方:
#   bash scripts/debug/run_monthly_2020_2026.sh
#
# 動作:
#   - 2020-01 から 2026-12 まで（84ヶ月）を順に処理
#   - 完了済みの月はチェックポイントから API を呼ばずにスキップ（冪等）
#   - API クォータ超過 (exit 2) で中断し、翌日は同じコマンドで続きから再開
#   - 全月完了したら 0 を返す
#
# cron 設定例（毎日 04:00 JST、クォータリセット後）:
#   0 4 * * * cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends && /bin/bash scripts/debug/run_monthly_2020_2026.sh >> /tmp/yt_monthly_cron.log 2>&1

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COLLECTOR="${SCRIPT_DIR}/youtube_api_date_range.py"
SEARCH_TERM="CBD リキッド"
LOG_DIR="${LOG_DIR:-/tmp/yt_monthly}"

mkdir -p "$LOG_DIR"

quota_hit=0
completed=0
pending=0

for y in 2020 2021 2022 2023 2024 2025 2026; do
  for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
    if [ "$m" = "12" ]; then
      next="$((y + 1))-01-01"
    else
      next="${y}-$(printf '%02d' $((10#$m + 1)))-01"
    fi

    # 2026年は現在日（2026-10）までのみ対象
    if [ "$y" = "2026" ] && [ "$m" -gt 10 ]; then
      continue
    fi

    log="${LOG_DIR}/yt_${y}${m}.log"
    python3 "$COLLECTOR" "$SEARCH_TERM" "${y}-${m}-01" "$next" > "$log" 2>&1
    rc=$?

    case $rc in
      0)
        completed=$((completed + 1))
        echo "[OK]    ${y}-${m} (${log})"
        ;;
      2)
        echo "[QUOTA] ${y}-${m} — クォータ超過。翌日この月から再開します。"
        quota_hit=1
        break 2
        ;;
      *)
        echo "[ERROR] ${y}-${m} exit=${rc} (${log})"
        pending=$((pending + 1))
        ;;
    esac
  done
done

echo "----"
echo "完了月: ${completed} / 中断(クォータ): ${quota_hit} / その他エラー: ${pending}"

if [ "$quota_hit" = "1" ]; then
  exit 2
fi
exit 0
