"""
Safari 쿠키에서 X.com 인증 정보를 추출합니다.

필요 조건:
  macOS System Settings > Privacy & Security > Full Disk Access > Terminal 체크
"""

import os
from pathlib import Path


def get_x_cookies() -> dict:
    """
    Safari에서 X.com 쿠키를 추출합니다.
    실패 시 .env 파일의 수동 설정으로 폴백합니다.
    """
    # 1차: Safari 쿠키 자동 추출
    try:
        import browser_cookie3
        jar = browser_cookie3.safari(domain_name=".x.com")
        cookies = {c.name: c.value for c in jar}

        # x.com이 없으면 twitter.com도 확인
        if "auth_token" not in cookies:
            jar2 = browser_cookie3.safari(domain_name=".twitter.com")
            cookies.update({c.name: c.value for c in jar2})

        if "auth_token" in cookies and "ct0" in cookies:
            print("✓ Safari에서 X.com 쿠키 자동 추출 완료")
            return cookies

    except Exception as e:
        print(f"  Safari 자동 추출 실패: {e}")

    # 2차: .env 파일 수동 설정으로 폴백
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")

    if auth_token and ct0:
        print("✓ .env 파일에서 X.com 쿠키 로드 완료")
        return {"auth_token": auth_token, "ct0": ct0}

    raise RuntimeError(
        "X.com 쿠키를 찾을 수 없습니다.\n"
        "방법 1: System Settings > Privacy & Security > Full Disk Access > Terminal 체크\n"
        "방법 2: .env 파일에 X_AUTH_TOKEN=... 과 X_CT0=... 설정\n"
        "  (X.com 로그인 후 브라우저 DevTools > Application > Cookies 에서 확인)"
    )
