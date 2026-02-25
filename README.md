# X.com → Obsidian 씨앗 노트 동기화

X.com 북마크를 자동으로 Obsidian inbox에 씨앗 노트로 변환합니다.
비용 없음 · 공식 API 키 불필요 · 완전 로컬 실행.

## 작동 방식

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

## 설치

### 1. 이 폴더를 Mac으로 복사

```bash
cp -r x-to-obsidian ~/
cd ~/x-to-obsidian
```

### 2. 패키지 설치

```bash
pip3 install -r requirements.txt
```

### 3. Full Disk Access 허용 (Safari 쿠키 자동 추출용)

System Settings > Privacy & Security > Full Disk Access > Terminal (또는 iTerm2) 체크

> 이 권한이 없으면 `.env` 파일로 수동 쿠키 설정 가능 (`.env.example` 참고)

### 4. Ollama 모델 확인

```bash
ollama list          # 설치된 모델 확인
ollama pull llama3.2 # 없으면 설치
```

`settings.json`에서 `ollama_model`을 설치된 모델명으로 변경하세요.

### 5. 환경 점검

```bash
python3 check.py
```

모든 항목이 ✓ 이면 준비 완료.

### 6. 테스트 실행

```bash
python3 main.py
```

### 7. 자동 실행 등록

**방법 A: launchd (권장)**
```bash
bash setup_launchd.sh
```
- 컴퓨터 시작/로그인 시 자동 시작
- macOS 권장 방식

**방법 B: cron**
```bash
bash setup_cron.sh
```
- 15분마다 실행

둘 중 하나만 선택하세요.

## 생성되는 노트 구조

```markdown
---
source: x.com
author: "@username"
tags: ["inbox", "🌱", "태그1", "태그2"]
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

## 로그 확인

```bash
tail -f sync.log
```

## 설정 변경

대화형 설정 스크립트를 사용하세요:

```bash
python3 setup_config.py        # 설정 변경
python3 setup_config.py status # 현재 설정 확인
```

설정 가능 항목:
- `obsidian_inbox`: Obsidian Inbox 경로
- `ollama_url`: Ollama 서버 URL
- `ollama_model`: 사용할 LLM 모델
- `bookmark_fetch_count`: 한 번에 가져올 북마크 수

설정은 `settings.json`에 저장됩니다.
