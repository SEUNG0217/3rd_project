# 백엔드 폴더 규칙 (figindex/backend/)

루트 `AGENTS.md`의 규칙이 먼저 적용되고, 이 폴더에서 작업할 때는 아래를 추가로 따른다.
담당: 팀원 1(업로드·검수 API), 팀원 2(검색), 팀장.

## 1. API 모양
- 요청·응답 모델은 `shared/schemas.py`의 모델(`ElementSearchPayload`, `TableData`, `Document`, `Batch`, `ReviewLog` 등)을 쓴다. 같은 모양의 모델을 이 폴더에 새로 만들지 않는다.
- JSON 키는 schemas.py 필드명 그대로(snake_case).
- API 응답 키를 바꾸거나 새 API를 만들면 `docs/migration/api_changes.md`에 한 줄 추가한다. 프론트 담당자가 이 파일을 보고 작업한다.
- 새 API는 Swagger(`http://localhost:8000/docs`)에서 바로 시험할 수 있게 요청 예시(`examples`)를 넣는다.

## 2. 데이터를 망가뜨리지 않기
- 검수 API(`POST /api/review/...`)는 실제 Qdrant 데이터를 바꾼다. 시험할 때는 `QDRANT_COLLECTION`을 시험용 컬렉션으로 바꾼 뒤 한다.
- `ReviewLog`는 추가만 한다. 수정·삭제 API를 만들지 않는다.
- 등록 묶음 ID는 `batch_id`. `job_id`, `upload_id`, `task_id`를 쓰지 않는다.
- 진행률은 저장하지 않고 문서의 `doc_status`를 세어 계산한다.

## 3. 바꾼 뒤 확인
- 백엔드 컨테이너 로그에 에러가 없어야 한다: `docker compose logs backend --tail 50`
- `/health`에서 `qdrant_connected: true`.
- 서버 실행(`uvicorn`, `docker compose up`)은 사람이 직접 한다. AI는 실행 방법만 알려준다.
