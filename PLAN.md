# X.com → Obsidian 씨앗 노트 동기화

## 프로젝트 개요

X.com 북마크를 자동으로 Obsidian inbox에 씨앗 노트로 변환하는 동기화 도구.

**핵심 특징:**
- 비용 없음 (공식 API 키 불필요)
- 완전 로컬 실행
- Ollama 로컬 LLM 활용

## 아키텍처

```
[모바일] X.com 북마크 저장
              ↓ (X.com 서버 자동 동기화)
[Mac cron, 15분마다]
   Safari 쿠키로 인증 → 신규 북마크 수집
              ↓
   Ollama 로컬 LLM으로 씨앗 노트 생성
   (Verbatim Trap 회피 · 함의된 주장 추출)
              ↓
   ~/Library/.../iCloud~md~obsidian/.../inbox/ 저장
```

## 모듈 구조

| 파일 | 역할 | 주요 기능 |
|------|------|-----------|
| `main.py` | 진입점 | 전체 워크플로우 오케스트레이션 |
| `auth.py` | 인증 | Safari 쿠키 추출 / .env 폴백 |
| `fetcher.py` | 수집 | twikit으로 북마크 조회 |
| `enricher.py` | 분석 | Ollama LLM으로 씨앗 노트 생성 |
| `writer.py` | 출력 | Obsidian 마크다운 파일 작성 |
| `state.py` | 상태 | 중복 처리 방지 (processed_ids 추적) |
| `check.py` | 진단 | 환경 점검 스크립트 |
| `config.py` | 설정 | settings.json 읽기 (기본값 폴백) |
| `setup_config.py` | 설정 UI | 대화형 설정 변경 스크립트 |
| `setup_cron.sh` | 스케줄 | cron 등록 (15분마다) |
| `setup_launchd.sh` | 스케줄 | launchd 등록 (macOS 권장) |

## 기술 스택

- **Python 3.10+**
- **twikit**: X.com 비공식 API 클라이언트
- **browser_cookie3**: Safari 쿠키 추출
- **httpx**: Ollama API 통신
- **Ollama**: 로컬 LLM 서버 (기본: glm-5:cloud)

## 개선 계획

### 우선순위 높음
- [ ] `.gitignore` 추가 (.env, .state.json, __pycache__ 등)
- [ ] `logging` 모듈로 로그 체계화 (print → logging)
- [ ] OLLAMA_MODEL 설정 검증 (README와 불일치)

### 우선순위 중간
- [ ] enricher.py: LLM 출력 파싱 안정화 (JSON 모드?)
- [ ] writer.py: 동일 제목 파일 중복 처리
- [ ] 에러 알림 기능 (이메일/슬랙?)

### 우선순위 낮음
- [ ] 테스트 코드 작성
- [ ] 타입 힌트 추가

## 생성되는 노트 구조

```markdown
---
source: x.com
author: "@username"
author_name: "표시 이름"
url: https://x.com/...
captured: 2026-02-21T...
tweet_id: "..."
tags:
  - "inbox"
  - "🌱"
  - "태그1"
---

# 트윗이 함의하는 핵심 주장 한 문장

## 원문
> 트윗 원문...

## 이 내용이 실제로 주장하는 것
원문에 없지만 함의된 주장...

## 씨앗 질문
- 이 주장이 맞다면 무엇이 달라져야 하는가?
- 어떤 반례가 이 주장을 약화시키는가?
- 이것이 연결되는 더 큰 패턴은?

## 연결 후보
[[개념1]] [[개념2]] [[개념3]]
```

## 설정 관리

설정은 `settings.json`에 저장됩니다.

```bash
# 대화형 설정
python3 setup_config.py

# 현재 설정 확인
python3 setup_config.py status
```

설정 가능 항목:
- `obsidian_inbox`: Obsidian Inbox 경로
- `ollama_url`: Ollama 서버 URL
- `ollama_model`: 사용할 LLM 모델
- `bookmark_fetch_count`: 한 번에 가져올 북마크 수

## 참고

- README.md: 설치 및 사용법
- .env.example: 수동 쿠키 설정 예시
- setup_cron.sh: cron 자동 등록 스크립트