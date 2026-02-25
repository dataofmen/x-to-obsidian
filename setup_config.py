#!/usr/bin/env python3
"""
대화형 설정 스크립트.

실행: python3 setup_config.py
"""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"

# 기본값
DEFAULTS = {
    "obsidian_inbox": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Inbox",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "bookmark_fetch_count": 5,
    "verify_ssl": True,
}

# 설정 항목 정의
CONFIG_ITEMS = [
    {
        "key": "obsidian_inbox",
        "label": "Obsidian Inbox 경로",
        "description": "씨앗 노트가 저장될 Obsidian vault의 inbox 폴더 경로",
        "type": "path",
    },
    {
        "key": "ollama_url",
        "label": "Ollama 서버 URL",
        "description": "Ollama API 서버 주소",
        "type": "str",
    },
    {
        "key": "ollama_model",
        "label": "Ollama 모델",
        "description": "사용할 LLM 모델명 (예: llama3.2, glm-5:cloud)",
        "type": "str",
    },
    {
        "key": "bookmark_fetch_count",
        "label": "북마크 가져오기 개수",
        "description": "한 번에 가져올 X.com 북마크 수",
        "type": "int",
    },
    {
        "key": "verify_ssl",
        "label": "SSL 인증서 검증",
        "description": "VPN/프록시 환경에서 SSL 오류 발생 시 false로 설정",
        "type": "bool",
    },
]


def load_settings() -> dict:
    """설정 파일을 로드합니다."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict):
    """설정을 파일에 저장합니다."""
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def print_current_settings(settings: dict):
    """현재 설정을 출력합니다."""
    print("\n현재 설정:")
    print("─" * 50)
    for item in CONFIG_ITEMS:
        key = item["key"]
        value = settings.get(key, DEFAULTS[key])
        print(f"  {item['label']}: {value}")
    print("─" * 50)


def get_available_models() -> list[str]:
    """로컬 Ollama에서 사용 가능한 모델 목록을 가져옵니다."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def prompt_for_value(item: dict, current_value) -> tuple:
    """사용자에게 값을 입력받습니다. (새 값, 변경 여부)"""
    key = item["key"]
    label = item["label"]
    description = item["description"]
    value_type = item["type"]

    print(f"\n[{label}]")
    print(f"  설명: {description}")
    print(f"  현재 값: {current_value}")

    # 모델 선택 시 목록 표시
    if key == "ollama_model":
        models = get_available_models()
        if models:
            print(f"  로컬 모델: {', '.join(models)}")

    while True:
        raw = input(f"  새 값 (Enter=유지, q=취소): ").strip()

        if raw.lower() == "q":
            return current_value, False
        if raw == "":
            return current_value, False  # 변경 없음

        try:
            if value_type == "int":
                return int(raw), True
            elif value_type == "bool":
                if raw.lower() in ("true", "t", "yes", "y", "1"):
                    return True, True
                elif raw.lower() in ("false", "f", "no", "n", "0"):
                    return False, True
                else:
                    print("  ✗ true/false로 입력하세요.")
                    continue
            elif value_type == "path":
                return raw, True
            else:
                return raw, True
        except ValueError:
            print("  ✗ 올바른 값을 입력하세요.")


def interactive_setup():
    """대화형 설정을 진행합니다."""
    print("\n" + "=" * 50)
    print("  X.com → Obsidian 설정")
    print("=" * 50)

    settings = load_settings()
    print_current_settings(settings)

    print("\n설정을 변경하려면 번호를 선택하세요.")
    print("0: 모두 보기/수정")
    for i, item in enumerate(CONFIG_ITEMS, 1):
        print(f"{i}: {item['label']}")
    print("q: 종료")

    while True:
        choice = input("\n선택: ").strip().lower()

        if choice == "q":
            print("설정을 종료합니다.")
            break

        if choice == "0":
            # 모든 항목 순차 수정
            changed = False
            for item in CONFIG_ITEMS:
                key = item["key"]
                current = settings.get(key, DEFAULTS[key])
                new_value, was_changed = prompt_for_value(item, current)
                if was_changed:
                    settings[key] = new_value
                    changed = True
                    print(f"  ✓ {item['label']} 변경됨")

            if changed:
                save_settings(settings)
                print("\n✓ 설정이 저장되었습니다.")
                print_current_settings(settings)
            break

        elif choice.isdigit() and 1 <= int(choice) <= len(CONFIG_ITEMS):
            # 단일 항목 수정
            item = CONFIG_ITEMS[int(choice) - 1]
            key = item["key"]
            current = settings.get(key, DEFAULTS[key])
            new_value, was_changed = prompt_for_value(item, current)

            if was_changed:
                settings[key] = new_value
                save_settings(settings)
                print(f"\n✓ {item['label']}이(가) 변경되었습니다: {new_value}")

            print_current_settings(settings)

        else:
            print("올바른 번호를 입력하세요.")


def show_status():
    """현재 설정 상태를 표시합니다."""
    settings = load_settings()
    print("\n" + "=" * 50)
    print("  현재 설정 상태")
    print("=" * 50)
    print_current_settings(settings)

    # Obsidian 경로 확인
    inbox_path = Path(settings.get("obsidian_inbox", DEFAULTS["obsidian_inbox"])).expanduser()
    print(f"\nInbox 경로 존재: {'✓' if inbox_path.exists() else '✗'}")
    if inbox_path.exists():
        print(f"  → {inbox_path}")

    # Ollama 확인
    ollama_url = settings.get("ollama_url", DEFAULTS["ollama_url"])
    try:
        import httpx
        r = httpx.get(f"{ollama_url}/api/tags", timeout=5)
        if r.status_code == 200:
            print(f"\nOllama 서버: ✓ 연결됨 ({ollama_url})")
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                print(f"  로컬 모델: {', '.join(models)}")
        else:
            print(f"\nOllama 서버: ✗ 응답 없음 ({ollama_url})")
    except Exception as e:
        print(f"\nOllama 서버: ✗ 연결 실패 ({ollama_url})")
        print(f"  오류: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        interactive_setup()