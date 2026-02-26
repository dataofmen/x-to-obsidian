"""
X.com 북마크를 쿠키 기반으로 가져옵니다 (공식 API 키 불필요).
"""

import asyncio
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
        # 텍스트 추출
        raw_text = item.full_text if hasattr(item, "full_text") and item.full_text else item.text

        # Article 형식 확인 (t.co 링크만 있는 경우)
        is_article = raw_text and raw_text.strip().startswith("https://t.co/")

        if is_article and hasattr(item, "urls") and item.urls:
            # Article ID 추출
            for url_info in item.urls:
                expanded_url = url_info.get("expanded_url", "")
                if "/i/article/" in expanded_url:
                    article_id = expanded_url.split("/i/article/")[-1].split("?")[0]
                    article_url = f"https://x.com/i/article/{article_id}"
                    print(f"  ↳ Article 감지, Playwright로 내용 가져오는 중...")

                    try:
                        from playwright.async_api import async_playwright

                        async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=True)
                            context = await browser.new_context(
                                storage_state={
                                    "cookies": [
                                        {"name": "auth_token", "value": cookies.get("auth_token", ""), "domain": ".x.com", "path": "/"},
                                        {"name": "ct0", "value": cookies.get("ct0", ""), "domain": ".x.com", "path": "/"},
                                    ]
                                }
                            )
                            page = await context.new_page()
                            try:
                                await page.goto(article_url, wait_until="domcontentloaded", timeout=60000)
                                await page.wait_for_selector('[data-testid="tweetText"]', timeout=10000)
                            except Exception:
                                pass  # 요소 대기 실패해도 계속 진행

                            # Article 텍스트 추출
                            article_text = await page.evaluate("""() => {
                                const selectors = [
                                    '[data-testid="tweetText"]',
                                    '[data-testid="article"]',
                                    'article [data-testid="tweetText"]',
                                ];
                                for (const selector of selectors) {
                                    const elements = document.querySelectorAll(selector);
                                    if (elements.length > 0) {
                                        return Array.from(elements).map(el => el.innerText).join('\\n\\n');
                                    }
                                }
                                return null;
                            }""")

                            await browser.close()

                            if article_text and len(article_text) > 50:
                                print(f"    ✓ Article 내용 가져옴 ({len(article_text)}자)")
                                raw_text = article_text

                    except ImportError:
                        print(f"    ✗ Playwright 미설치: 'pip install playwright && playwright install chromium'")
                    except Exception as e:
                        print(f"    ✗ Article 가져오기 실패: {e}")
                    break

        media_urls = []
        if hasattr(item, "media") and item.media:
            for m in item.media:
                if hasattr(m, "media_url_https"):
                    media_urls.append(m.media_url_https)

        tweets.append(Tweet(
            id=item.id,
            text=raw_text,
            author_name=item.user.name,
            author_handle=item.user.screen_name,
            url=f"https://x.com/{item.user.screen_name}/status/{item.id}",
            created_at=str(item.created_at),
            media_urls=media_urls,
        ))

    return tweets