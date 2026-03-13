#!/usr/bin/env python3
"""
X.com 북마크 → Obsidian 씨앗 노트 동기화

실행: python3 main.py
스케줄: setup_cron.sh 로 자동 등록 (15분마다)
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from config import DEFAULT_OUTPUT_DIR, BOOKMARK_FETCH_COUNT, VERIFY_SSL, STATE_FILE
from auth import get_x_cookies
from fetcher import fetch_bookmarks
from enricher import enrich_tweet
from writer import write_note
from state import State


async def run(output_dir: Path, fetch_count: int):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] X.com → 로컬 폴더 동기화 시작")
    print(f"저장 경로: {output_dir}")

    state = State(STATE_FILE)

    # 1. 쿠키 추출
    try:
        cookies = get_x_cookies()
    except RuntimeError as e:
        print(f"✗ {e}")
        sys.exit(1)

    # 2. 북마크 가져오기
    try:
        tweets = await fetch_bookmarks(cookies, count=fetch_count, verify_ssl=VERIFY_SSL)
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

        note_path = write_note(tweet, enrichment, output_dir)
        state.mark_processed(tweet.id)
        new_count += 1
        print(f"    ✓ {note_path.name}")

    state.update_last_run()

    if new_count == 0:
        print("  새 북마크 없음")
    else:
        print(f"\n완료: {new_count}개 노트 생성 (누적 {state.total_notes}개)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X.com 북마크 동기화 스크립트")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="스크랩한 노트를 저장할 로컬 디렉토리 경로 (기본값: settings.json 맵핑 경로 혹은 기본 Obsidian Inbox)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=BOOKMARK_FETCH_COUNT,
        help="가져올 북마크 개수 (기본값: settings.json 혹은 5)"
    )
    args = parser.parse_args()

    asyncio.run(run(output_dir=args.output_dir, fetch_count=args.count))
