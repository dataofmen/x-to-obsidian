#!/bin/bash
# X.com → Obsidian 자동 동기화 cron 등록 스크립트
# 실행: bash setup_cron.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
LOG_FILE="$SCRIPT_DIR/sync.log"
MARKER="x-to-obsidian"

echo "=== X.com → Obsidian cron 설정 ==="
echo "스크립트 경로: $SCRIPT_DIR"
echo "Python: $PYTHON"
echo "로그: $LOG_FILE"

# 이미 등록된 경우 스킵
if crontab -l 2>/dev/null | grep -q "$MARKER"; then
    echo ""
    echo "✓ cron job이 이미 등록되어 있습니다."
    echo ""
    echo "현재 등록된 항목:"
    crontab -l | grep "$MARKER"
    echo ""
    echo "제거하려면: crontab -e 에서 해당 줄을 삭제하세요."
    exit 0
fi

# 15분마다 실행
CRON_LINE="*/15 * * * * cd \"$SCRIPT_DIR\" && $PYTHON main.py >> \"$LOG_FILE\" 2>&1 # $MARKER"

(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

echo ""
echo "✓ cron job 등록 완료 (15분마다 실행)"
echo ""
echo "확인: crontab -l"
echo "로그: tail -f $LOG_FILE"
echo ""
echo "즉시 테스트: python3 $SCRIPT_DIR/main.py"
