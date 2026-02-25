#!/bin/bash
# X.com → Obsidian 자동 동기화 launchd 등록 스크립트
# 실행: bash setup_launchd.sh
#
# launchd는 macOS 권장 방식:
# - 컴퓨터 시작 시 자동 로드
# - 로그인 시 자동 시작
# - 놓친 작업 실행 가능

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
LOG_FILE="$SCRIPT_DIR/sync.log"
PLIST_NAME="com.user.x-to-obsidian"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "=== X.com → Obsidian launchd 설정 ==="
echo "스크립트 경로: $SCRIPT_DIR"
echo "Python: $PYTHON"
echo "로그: $LOG_FILE"

# plist 파일 생성
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/main.py</string>
    </array>

    <key>StartInterval</key>
    <integer>900</integer>

    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>

    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
</dict>
</plist>
EOF

echo ""
echo "plist 파일 생성: $PLIST_PATH"

# 기존에 로드되어 있으면 언로드
if launchctl list "$PLIST_NAME" &>/dev/null; then
    echo "기존 서비스 언로드 중..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

# 새 서비스 로드
echo "새 서비스 로드 중..."
launchctl load "$PLIST_PATH"

echo ""
echo "✓ launchd 서비스 등록 완료!"
echo ""
echo "설정:"
echo "  - 15분마다 실행 (900초)"
echo "  - 컴퓨터 시작/로그인 시 자동 시작"
echo ""
echo "관리 명령어:"
echo "  상태 확인:   launchctl list $PLIST_NAME"
echo "  즉시 실행:   launchctl start $PLIST_NAME"
echo "  중지:        launchctl unload $PLIST_PATH"
echo "  시작:        launchctl load $PLIST_PATH"
echo "  제거:        launchctl unload $PLIST_PATH && rm $PLIST_PATH"
echo "  로그 확인:   tail -f $LOG_FILE"