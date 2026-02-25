"""
X.com 북마크를 쿠키 기반으로 가져옵니다 (공식 API 키 불필요).
"""

import asyncio
import ssl
from dataclasses import dataclass

import httpx


@dataclass
class Tweet:
    id: str
    text: str
    author_name: str
    author_handle: str
    url: str
    created_at: str
    media_urls: list[str]


async def fetch_bookmarks(cookies: dict, count: int = 20, verify_ssl: bool = True) -> list[Tweet]:
    """
    X.com 북마크를 가져옵니다.

    Args:
        cookies: X.com 인증 쿠키
        count: 가져올 북마크 수
        verify_ssl: SSL 인증서 검증 여부 (프록시 환경에서 False 필요)
    """
    from twikit import Client

    # SSL 검증 비활성화가 필요한 경우
    if not verify_ssl:
        # httpx 클라이언트에 SSL 검증 비활성화
        httpx_client = httpx.AsyncClient(verify=False)
        client = Client("en-US", httpx_client=httpx_client)
    else:
        client = Client("en-US")

    client.set_cookies(cookies)

    try:
        result = await client.get_bookmarks(count=count)
    except Exception as e:
        error_msg = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in error_msg or "SSL" in error_msg:
            raise RuntimeError(
                f"SSL 인증서 오류: {e}\n"
                "프록시/VPN 환경인 경우 settings.json에서 'verify_ssl': false로 설정하세요."
            )
        raise RuntimeError(f"북마크 가져오기 실패: {e}\n쿠키가 만료되었을 수 있습니다.")

    tweets = []
    for item in result:
        media_urls = []
        if hasattr(item, "media") and item.media:
            for m in item.media:
                if hasattr(m, "media_url_https"):
                    media_urls.append(m.media_url_https)

        tweets.append(Tweet(
            id=item.id,
            text=item.full_text if hasattr(item, "full_text") else item.text,
            author_name=item.user.name,
            author_handle=item.user.screen_name,
            url=f"https://x.com/{item.user.screen_name}/status/{item.id}",
            created_at=str(item.created_at),
            media_urls=media_urls,
        ))

    return tweets