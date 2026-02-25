#!/usr/bin/env python3
"""
X.com 북마크 → Obsidian 씨앗 노트 동기화

실행: python3 main.py
스케줄: setup_cron.sh 로 자동 등록 (15분마다)
"""

import asyncio
import sys
from datetime import datetime

from config import OBSIDIAN_INBOX, BOOKMARK_FETCH_COUNT, VERIFY_SSL, STATE_FILE
from auth import get_x_cookies
from fetcher import fetch_bookmarks
from enricher import enrich_tweet
from writer import write_note
from state import State


async def run():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] X.com → Obsidian 동기화 시작")

    state = State(STATE_FILE)

    # 1. 쿠키 추출
    try:
        cookies = get_x_cookies()
    except RuntimeError as e:
        print(f"✗ {e}")
        sys.exit(1)

    # 2. 북마크 가져오기
    try:
        tweets = await fetch_bookmarks(cookies, count=BOOKMARK_FETCH_COUNT, verify_ssl=VERIFY_SSL)
        print(f"✓ 북마크 {len(tweets)}개 가져옴")
    except RuntimeError as e:
        print(f"✗ {e}")
        sys.exit(1)

    # 3. 신규 북마크만 처리
    new_count = 0
    for tweet in tweets:
        if state.is_processed(tweet.id):
            continue

        short = tweet.text[:50].replace("\n", " ")
        print(f"  ↳ 처리: @{tweet.author_handle} — {short}...")

        enrichment = enrich_tweet(
            tweet_text=tweet.text,
            author_handle=tweet.author_handle,
            author_name=tweet.author_name,
        )

        note_path = write_note(tweet, enrichment, OBSIDIAN_INBOX)
        state.mark_processed(tweet.id)
        new_count += 1
        print(f"    ✓ {note_path.name}")

    state.update_last_run()

    if new_count == 0:
        print("  새 북마크 없음")
    else:
        print(f"\n완료: {new_count}개 노트 생성 (누적 {state.total_notes}개)")


if __name__ == "__main__":
    asyncio.run(run())
