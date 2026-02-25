"""
트윗을 분석해서 씨앗 노트용 메타데이터를 생성합니다.
"""

import re
import httpx
from config import OLLAMA_URL, OLLAMA_MODEL

PROMPT_TEMPLATE = """당신은 텍스트 분석 전문가입니다. 아래 트윗을 깊이 있게 분석하세요.

## 작성자
@{author_handle}

## 트윗 내용
{text}

---

## 분석 지침

1. **TITLE**: 이 트윗이 핵심적으로 주장하는 명제를 간결한 한 문장으로 작성하세요.
   - 내용을 보고 대략적인 본문을 상상할 수 있도록 구체적으로 작성하세요.
   - 예: "성공한 인물들의 공통점은 에이전시", "창업자가 피칭에서 자주 범하는 실수"
   - 반드시 35자 이내로 작성하세요.

2. **CLAIM**: 트윗에 명시되지 않았지만 함의된 주장이나 전제를 2-3문장으로 작성하세요.
   - 글쓴이가 당연하게 여기는 가정은 무엇인가?
   - 이 주장이 참이라면 어떤 결론이 따라오는가?

3. **Q1, Q2, Q3**: 이 주장을 발전시킬 수 있는 씨앗 질문을 세 개 작성하세요.
   - 비판적 사고를 자극하는 질문
   - 다른 분야나 맥락과 연결할 수 있는 질문

4. **LINKS**: 이 내용과 연결될 수 있는 개념 3개를 작성하세요. (Obsidian 위키링크용)

5. **TAGS**: 분류를 위한 태그 2-3개를 작성하세요.

---

반드시 아래 형식으로만 답변하세요:

TITLE: [핵심 명제 한 문장]
CLAIM: [함의된 주장 2-3문장]
Q1: [씨앗 질문 1]
Q2: [씨앗 질문 2]
Q3: [씨앗 질문 3]
LINKS: [개념1], [개념2], [개념3]
TAGS: [태그1], [태그2]"""


def _parse(text: str) -> dict:
    """LLM 응답을 파싱합니다."""
    def get(key: str) -> str:
        # 대소문자 구분 없이 매칭
        pattern = rf"^{key}:\s*(.+?)(?=^(?:TITLE|CLAIM|Q[123]|LINKS|TAGS):|\Z)"
        m = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # 단순 패턴으로 재시도
        m = re.search(rf"^{key}:\s*(.+)", text, re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    links_raw = get("LINKS")
    # 대괄호 제거하고 콤마로 분리
    links_raw = re.sub(r'[\[\]]', '', links_raw)
    links = [x.strip() for x in links_raw.split(",") if x.strip()]

    tags_raw = get("TAGS")
    tags_raw = re.sub(r'[\[\]]', '', tags_raw)
    tags = [x.strip() for x in tags_raw.split(",") if x.strip()]

    return {
        "title":          get("TITLE"),
        "core_claim":     get("CLAIM"),
        "seed_questions": [get("Q1"), get("Q2"), get("Q3")],
        "wiki_links":     links,
        "tags":           tags,
    }


def _truncate_text(text: str, max_chars: int = 6000) -> str:
    """텍스트가 너무 길면 자릅니다."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... 내용이 길어 일부만 표시 ...]"


def enrich_tweet(tweet_text: str, author_handle: str, author_name: str) -> dict:
    """트윗을 분석해서 씨앗 노트용 메타데이터를 생성합니다."""
    # 텍스트가 너무 길면 자르기
    truncated_text = _truncate_text(tweet_text)

    prompt = PROMPT_TEMPLATE.format(
        author_handle=author_handle,
        text=truncated_text,
    )

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 8000,  # thinking 모델은 더 많은 토큰 필요
                }
            },
            timeout=300.0,
        )
        response.raise_for_status()
        json_response = response.json()
        print(f"  API 응답 JSON: {json_response}")

        raw = json_response.get("response", "")
        print(f"  모델 응답 (전체):\n{raw}\n{'─'*40}")

        result = _parse(raw)
        if result["title"]:
            print(f"  파싱 성공: TITLE='{result['title']}'")
            return result

        print("  파싱 실패 — TITLE 없음, 폴백 사용")
        return _fallback_enrichment(tweet_text)

    except Exception as e:
        print(f"  Ollama 오류: {e}")
        return _fallback_enrichment(tweet_text)


def _fallback_enrichment(text: str) -> dict:
    """LLM 실패 시 기본값을 반환합니다."""
    # 줄바꿈 제거하고 한 줄로 만들기
    single_line = " ".join(text.split())
    title = single_line[:35].rstrip() + ("..." if len(single_line) > 35 else "")
    return {
        "title":          title,
        "core_claim":     "(LLM 처리 실패 — 직접 작성 필요)",
        "seed_questions": [
            "이 내용이 왜 중요한가?",
            "어떤 맥락에서 성립하는가?",
            "연결되는 기존 생각은?"
        ],
        "wiki_links":     [],
        "tags":           ["처리필요"],
    }