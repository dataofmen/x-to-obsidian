#!/usr/bin/env python3
"""
실행 전 환경 점검 스크립트.
setup 완료 후 python3 check.py 로 확인하세요.
"""

import sys
import httpx
from pathlib import Path


def section(title: str):
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print('─' * 40)


def ok(msg): print(f"  ✓ {msg}")
def fail(msg): print(f"  ✗ {msg}")
def warn(msg): print(f"  ⚠ {msg}")


def check_python():
    section("Python 버전")
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python 3.10 이상 필요 (현재: {v.major}.{v.minor})")


def check_packages():
    section("필수 패키지")
    packages = ["browser_cookie3", "twikit", "httpx"]
    for pkg in packages:
        try:
            __import__(pkg)
            ok(pkg)
        except ImportError:
            fail(f"{pkg} 미설치 → pip3 install -r requirements.txt")


def check_ollama():
    section("Ollama")
    from config import OLLAMA_MODEL
    is_cloud = OLLAMA_MODEL.endswith(":cloud")

    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        ok(f"실행 중 · 설정 모델: {OLLAMA_MODEL}")

        if is_cloud:
            ok("클라우드 모델 사용 — 로컬 목록 확인 생략")
        elif OLLAMA_MODEL in models or any(OLLAMA_MODEL in m for m in models):
            ok(f"모델 '{OLLAMA_MODEL}' 확인됨")
        else:
            warn(
                f"모델 '{OLLAMA_MODEL}'이 로컬 목록에 없습니다.\n"
                f"  로컬 모델: {', '.join(models) or '없음'}\n"
                f"  → ollama pull {OLLAMA_MODEL} 또는 config.py 수정"
            )
    except Exception:
        fail("Ollama 미실행 → ollama serve 실행 후 재시도")


def check_cookies():
    section("Safari X.com 쿠키")
    try:
        import browser_cookie3
        jar = browser_cookie3.safari(domain_name=".x.com")
        cookies = {c.name: c.value for c in jar}
        if "auth_token" in cookies and "ct0" in cookies:
            ok("auth_token, ct0 쿠키 확인됨")
        else:
            fail(
                "X.com 쿠키를 찾을 수 없습니다.\n"
                "  1. Safari에서 x.com 에 로그인되어 있는지 확인\n"
                "  2. System Settings > Privacy & Security > Full Disk Access > Terminal 체크\n"
                "  3. 또는 .env 파일에 수동 설정 (README 참고)"
            )
    except Exception as e:
        fail(f"쿠키 추출 오류: {e}")


def check_obsidian():
    section("Obsidian inbox 경로")
    from config import OBSIDIAN_INBOX
    vault = OBSIDIAN_INBOX.parent
    if vault.exists():
        ok(f"vault 존재: {vault}")
        OBSIDIAN_INBOX.mkdir(parents=True, exist_ok=True)
        ok(f"inbox 생성/확인: {OBSIDIAN_INBOX}")
    else:
        fail(
            f"vault 경로를 찾을 수 없습니다: {vault}\n"
            "  Obsidian이 iCloud와 동기화되어 있는지 확인하세요."
        )


if __name__ == "__main__":
    print("X.com → Obsidian 환경 점검")
    check_python()
    check_packages()
    check_ollama()
    check_cookies()
    check_obsidian()
    print(f"\n{'─' * 40}")
    print("  점검 완료. ✗ 항목을 해결한 후 main.py를 실행하세요.")
    print('─' * 40)
