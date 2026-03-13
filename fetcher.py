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
        # 1. 북마크된 트윗 원본 조회 (Long tweet 등 상세 정보 확보)
        try:
            detailed_tweet = await client.get_tweet_by_id(item.id)
            if not detailed_tweet:
                detailed_tweet = item
        except Exception as e:
            print(f"  ↳ 개별 트윗 상세 조회 실패: {e}")
            detailed_tweet = item

        # 텍스트 추출 (note_tweet, full_text 우선 탐색)
        raw_text = ""
        if hasattr(detailed_tweet, "note_tweet") and detailed_tweet.note_tweet:
            raw_text = detailed_tweet.note_tweet.get("note_tweet_results", {}).get("result", {}).get("text", "")

        if not raw_text:
            raw_text = detailed_tweet.full_text if hasattr(detailed_tweet, "full_text") and detailed_tweet.full_text else detailed_tweet.text

        # Thread(쓰레드) 텍스트 수집 (답글들)
        author_screen_name = detailed_tweet.user.screen_name
        thread_texts = []
        current_tweet = detailed_tweet

        # 2. 쓰레드(답글) 가져오기 로직
        try:
            # client.get_tweet_by_id(...) 호출 시 replies 에 접근 가능한 경우가 있음
            if hasattr(current_tweet, "replies") and current_tweet.replies:
                replies = current_tweet.replies
                for reply in replies:
                    if reply.user.screen_name == author_screen_name:
                        reply_text = reply.full_text if hasattr(reply, "full_text") and reply.full_text else reply.text
                        thread_texts.append(reply_text)
        except Exception as e:
            print(f"  ↳ 쓰레드 답글 조회 실패: {e}")

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

        if thread_texts:
            print(f"    ✓ 쓰레드(답글) {len(thread_texts)}개 병합")
            raw_text = raw_text + "\n\n---\n\n" + "\n\n---\n\n".join(thread_texts)

        media_urls = []
        if hasattr(detailed_tweet, "media") and detailed_tweet.media:
            for m in detailed_tweet.media:
                if hasattr(m, "media_url_https"):
                    media_urls.append(m.media_url_https)

        tweets.append(Tweet(
            id=detailed_tweet.id,
            text=raw_text,
            author_name=detailed_tweet.user.name,
            author_handle=detailed_tweet.user.screen_name,
            url=f"https://x.com/{detailed_tweet.user.screen_name}/status/{detailed_tweet.id}",
            created_at=str(detailed_tweet.created_at),
            media_urls=media_urls,
        ))

    return tweets