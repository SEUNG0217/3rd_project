# 프론트엔드 폴더 규칙 (figindex/frontend/)

루트 `AGENTS.md`의 규칙이 먼저 적용되고, 이 폴더에서 작업할 때는 아래를 추가로 따른다.
담당: 팀원 1(업로드·검수 화면), 팀장.

## 1. 데이터 이름
- API 응답 타입은 `app/lib/types.ts` 한 곳에만 둔다(백엔드 OpenAPI 명세와 맞춘다). 컴포넌트 파일 안에 같은 타입을 다시 선언하지 않는다.
- API 키는 snake_case 그대로 쓴다(`caption`, `table_data`, `review_status`). camelCase로 바꾸지 않는다.
- 백엔드에 없는 필드를 화면에서 만들어 쓰지 않는다. 필요하면 "백엔드에 추가 필요"로 보고한다. 최신 키 목록은 `docs/migration/api_changes.md`.
- `"APPROVED"` 같은 상태값은 `types.ts`의 상수에서 가져온다.

## 2. 정해진 함수
- 표 셀 단위 표시: `app/lib/tableUnits.ts`의 `unitFor()`만 쓴다.
- 문서 유형 라벨: `app/lib/docTypeLabels.ts`.
- bbox는 `[x0, y0, x1, y1]`, 0~1 정규화, 좌상단 원점이다. 화면 px로 바꿀 때 이미지 너비·높이를 곱한다.

## 3. 화면 문구
- 화면에 보이는 글자는 한국어, 코드 이름은 영어.
- 상태값의 화면 표기는 `docs/glossary.md` 5절을 따른다(예: `PENDING_REVIEW` → "검수 대기").

## 4. 바꾼 뒤 확인
- `npx tsc --noEmit` 통과.
- 백엔드 API가 아직 없으면 `app/lib/mock/`에 가짜 응답을 만들어 화면부터 만든다. API가 생기면 mock을 지운다.
- 개발 서버(`npm run dev`)는 사람이 직접 실행한다.
