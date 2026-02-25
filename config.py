"""
설정 관리 모듈.

settings.json에서 설정을 읽어옵니다. 파일이 없으면 기본값을 사용합니다.
"""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"


def _load_settings() -> dict:
    """settings.json에서 설정을 로드합니다."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


_settings = _load_settings()


def _expand_path(path_str: str) -> Path:
    """경로 문자열의 ~를 홈 디렉토리로 확장합니다."""
    return Path(path_str).expanduser()


# Obsidian vault inbox path (iCloud synced)
OBSIDIAN_INBOX = _expand_path(
    _settings.get("obsidian_inbox", "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Inbox")
)

# Ollama settings
OLLAMA_URL = _settings.get("ollama_url", "http://localhost:11434")
OLLAMA_MODEL = _settings.get("ollama_model", "llama3.2")

# Sync settings
BOOKMARK_FETCH_COUNT = _settings.get("bookmark_fetch_count", 5)
VERIFY_SSL = _settings.get("verify_ssl", True)  # VPN/프록시 환경에서 false로 설정

# State & log
STATE_FILE = Path(__file__).parent / ".state.json"
LOG_FILE = Path(__file__).parent / "sync.log"