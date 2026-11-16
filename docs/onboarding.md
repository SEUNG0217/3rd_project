# 팀원 시작 가이드 (FigIndex)

처음 한 번만 하면 되는 준비와, AI 도구에 일을 시키는 방법을 정리했습니다.
막히면 단계 번호와 화면 캡처를 팀 채팅에 올려 주세요.

---

## 1. 처음 한 번: 내 PC 준비

### 1-1. 저장소 받기
```bash
git clone https://github.com/ghtjsx-web/3rd_project.git
cd 3rd_project
git switch -c 내이름        # 예: git switch -c kim
```
- `main`에는 직접 올리지 않습니다. 항상 내 이름 브랜치에서 작업하고 PR로 합칩니다.

### 1-2. API 키 넣기
```bash
cd figindex
cp .env.example .env        # Windows PowerShell: copy .env.example .env
```
`.env`를 열어 아래 세 줄을 채웁니다. 키 값은 팀장에게 개인 메시지로 받습니다(단체방·Git에 올리지 않기).
```
GEMINI_API_KEY=팀장에게 받은 값
OPENAI_API_KEY=팀장에게 받은 값
QDRANT_COLLECTION=figindex_elements_v2
```

### 1-3. 데이터 받기 (Git에 없음)
PDF 원본, 크롭 이미지, Qdrant 데이터는 용량·저작권 때문에 Git에 올리지 않습니다.
1. 팀 드라이브에서 최신 `figindex_data_날짜.zip`을 받습니다.
2. 압축을 `3rd_project/figindex/data/`에 풉니다. 풀고 나면 `data/pdfs/`, `data/crops/`, `data/qdrant/`가 보여야 합니다.

### 1-4. 실행
Docker Desktop을 켠 뒤 `figindex/` 폴더에서:
```bash
docker compose up -d
```
| 확인할 주소 | 정상일 때 |
| --- | --- |
| http://localhost:3000 | 카드 갤러리가 보임 |
| http://localhost:8000/health | `"qdrant_connected": true` |
| http://localhost:8000/docs | API 목록(Swagger) |

메모리 부족 오류가 나면 `figindex/README.md`의 9절(트러블슈팅)을 봅니다.

---

## 2. AI 도구 설정

규칙 파일은 이미 저장소에 들어 있어서, 저장소 폴더를 열기만 하면 AI가 자동으로 읽습니다.

| 파일 | 내용 |
| --- | --- |
| `AGENTS.md` | 전체 공통 규칙 (쓰면 안 되는 이름, 수정 금지 파일, 보고 형식) |
| `figindex/pipeline/AGENTS.md` | 파이프라인 폴더 규칙 |
| `figindex/backend/AGENTS.md` | 백엔드 폴더 규칙 |
| `figindex/frontend/AGENTS.md` | 프론트엔드 폴더 규칙 |
| `CLAUDE.md` | Claude Code가 `AGENTS.md`를 읽게 하는 연결 파일 |

- **Antigravity**: `3rd_project` 폴더를 열면 `AGENTS.md`(하위 폴더 것 포함)를 자동으로 읽습니다.
- **Cursor**: `AGENTS.md`를 자동으로 읽습니다.
- **Claude Code**: `CLAUDE.md`를 통해 읽습니다.
- **ChatGPT·웹 채팅**: 자동으로 못 읽습니다. `AGENTS.md`, 내 폴더의 `AGENTS.md`, `figindex/shared/schemas.py`를 첨부하고 시작합니다.

규칙 파일은 고치지 않습니다. 바꿔야 할 것 같으면 팀장에게 말해 주세요.

---

## 3. AI에게 일 시키는 방법

### 3-1. 기본 형식
모든 요청은 이 틀로 씁니다. 한 번에 한 가지만 시킵니다.
```
[읽을 것] AGENTS.md, (내 폴더)/AGENTS.md, PROJECT_STATUS_FOR_AI.md
[할 일] (한 문장)
[건드려도 되는 파일] (파일 경로)
[완료 기준] (어떻게 되면 끝인지)
먼저 무엇을 어떻게 바꿀지 3~5줄로 설명하고, 내가 OK하면 시작해.
끝나면 AGENTS.md 8절 형식으로 보고해.
```

### 3-2. 끝난 뒤 확인
```bash
python scripts/check_state.py --quick --expect "바꾼파일1,바꾼파일2"
```
FAIL이 있으면 결과를 AI에게 그대로 붙여 넣고 고치라고 합니다. 모두 PASS면 커밋하고 올립니다.
```bash
git add -A
git commit -m "무엇을 했는지 한 줄"
git push -u origin 내이름
```
GitHub에서 `main`으로 Pull Request를 만들고, 본문에 AI 보고 내용을 붙여 넣습니다.

### 3-3. AI가 이런 걸 하려 하면 멈추기
- `schemas.py`, `glossary.md`, `AGENTS.md`를 고치려 함
- 새 필드 이름·상태값을 만들어 씀 (예: `job_id`, `status`)
- `figindex_elements_v2` 컬렉션에 쓰거나 지우려 함
- 서버를 직접 실행하거나 반복 확인 타이머를 만들려 함
- 유료 API나 새 서비스를 추가하려 함

---

## 4. 내 역할 시작하기

`docs/roles/` 폴더에 역할별 브리핑이 있습니다. 혼자 읽지 말고 **AI에게 읽혀서 설명을 듣는 방식**으로 시작합니다.
첫 메시지는 `docs/roles/README.md`의 "시작하는 법"을 복사해서 보내면 됩니다.

오분류 점검은 `docs/roles/3_정답셋.md`의 2단계입니다. 기준은 `docs/glossary.md` 2절, 기록은 팀 공유 시트에 합니다.

---

## 5. 질문하기
- 규칙·이름 관련: 팀장
- 막힌 지 30분이 넘으면 혼자 붙잡지 말고 바로 물어보기
