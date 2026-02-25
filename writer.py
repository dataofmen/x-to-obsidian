"""
Obsidian inbox에 씨앗 노트(Markdown)를 생성합니다.
"""

import re
from datetime import datetime
from pathlib import Path

from fetcher import Tweet


NOTE_TEMPLATE = """\
---
source: x.com
author: "@{author_handle}"
author_name: "{author_name}"
url: {url}
captured: {captured}
tweet_id: "{tweet_id}"
tags:
{tags_yaml}
---

# {title}

## 원문

> {quoted_text}
>
> — [@{author_handle}](https://x.com/{author_handle}) · {created_at}
{media_section}
## 이 내용이 실제로 주장하는 것

{core_claim}

## 씨앗 질문

{seed_questions}

## 연결 후보

{wiki_links}
"""


def write_note(tweet: Tweet, enrichment: dict, inbox: Path) -> Path:
    inbox.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")

    # 안전한 파일명 생성
    raw_title = enrichment.get("title", tweet.text[:40])
    # 줄바꿈과 특수문자 제거
    safe_title = re.sub(r'[\n\r\t]', " ", raw_title)  # 줄바꿈 → 공백
    safe_title = re.sub(r'[\\/:*?"<>|]', "", safe_title)  # 금지 문자 제거
    safe_title = re.sub(r'\s+', " ", safe_title).strip()[:40]  # 연속 공백 정리
    filename = f"{timestamp} {safe_title}.md"

    # 태그 YAML
    base_tags = ["inbox", "🌱"] + enrichment.get("tags", [])
    tags_yaml = "\n".join(f'  - "{t}"' for t in base_tags)

    # 씨앗 질문
    seed_questions = "\n".join(
        f"- {q}" for q in enrichment.get("seed_questions", [])
    )

    # 위키링크
    wiki_links = "  ".join(
        f"[[{link}]]" for link in enrichment.get("wiki_links", [])
    )

    # 미디어
    media_section = ""
    if tweet.media_urls:
        lines = ["\n## 첨부 미디어\n"]
        for url in tweet.media_urls:
            lines.append(f"![]({url})")
        media_section = "\n".join(lines) + "\n"

    # 트윗 원문 인용 (줄바꿈 처리)
    quoted_text = tweet.text.replace("\n", "\n> ")

    content = NOTE_TEMPLATE.format(
        author_handle=tweet.author_handle,
        author_name=tweet.author_name,
        url=tweet.url,
        captured=now.isoformat(timespec="seconds"),
        tweet_id=tweet.id,
        tags_yaml=tags_yaml,
        title=enrichment.get("title", raw_title),
        quoted_text=quoted_text,
        created_at=tweet.created_at,
        media_section=media_section,
        core_claim=enrichment.get("core_claim", ""),
        seed_questions=seed_questions,
        wiki_links=wiki_links,
    )

    note_path = inbox / filename
    note_path.write_text(content, encoding="utf-8")
    return note_path
