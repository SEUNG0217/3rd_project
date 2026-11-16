# 역할 브리핑: 팀원 D (백엔드)

> AI에게: 이 사용자는 프로젝트에 처음 참여했고 코딩이 익숙하지 않다. 한 번에 한 단계씩, 코드를 쓰기 전에 무엇을 왜 하는지 먼저 설명한다. 각 단계는 사용자가 Swagger에서 직접 눌러 확인하게 한다. 루트 `AGENTS.md`와 `figindex/backend/AGENTS.md`를 따른다.

## 한 줄 요약
화면(E)과 데이터 사이에서 요청을 처리하는 **서버(FastAPI)** 를 만드는 일입니다. 이번에 추가할 것은 PDF 업로드, 처리 진행률, 검수 기록 세 가지입니다.

## 전체에서 내 위치
`★PDF 업로드★ → 오려 내기 → AI 읽기 → 저장 → ★검수 기록★`, 그리고 화면이 부르는 모든 API

## 지금 상황
- 조회 API(목록·상세·검색·필터)와 검수 API는 있습니다: `figindex/backend/app/main.py`
- 없는 것: PDF 업로드 API, 진행률 API, 검수 이력(`ReviewLog`) 저장
- 데이터 모양은 이미 정해져 있습니다: `figindex/shared/schemas.py`의 `Batch`, `Document`, `ReviewLog`

## 알아야 할 말
| 말 | 뜻 |
| --- | --- |
| API | 화면이 서버에 보내는 요청 주소. 예: `GET /api/elements` |
| Swagger | `localhost:8000/docs`. API를 버튼으로 눌러 시험하는 화면 |
| Batch | 한 번에 올린 PDF 묶음. `batch_id`로 구분 |
| doc_hash | 파일 내용으로 만든 지문(SHA-256). 같으면 이미 올린 파일(중복) |
| doc_status | 문서 처리 상태: 업로드됨 → 처리 중 → 완료/실패/중복 |
| ReviewLog | 검수자가 승인·수정·반려한 기록. 지우지 않고 쌓기만 함 |
| BackgroundTasks | 응답은 바로 주고 무거운 처리는 뒤에서 하는 FastAPI 기능 |

## 할 일
| 단계 | 할 일 | 확인 방법 |
| --- | --- | --- |
| 1 | Swagger에서 기존 API를 하나씩 눌러 보고 표로 정리 (주소, 하는 일, 응답 예) | 표 1장 |
| 2 | AI에게 `Batch`, `Document`, `ReviewLog` 모델을 예시 데이터로 설명받기 | 내 말로 각 3줄 요약 |
| 3 | 저장 방식 제안: 문서·묶음·검수 기록을 어디에 저장할지 (후보: SQLite 파일 1개) | 팀장에게 제안 → 결정 |
| 4 | (병합 후) `POST /api/batches`: PDF 여러 개 받기 → 파일 저장 → `doc_hash`로 중복 판정 → `Batch`·`Document` 저장. 파이프라인 실행은 아직 안 함 | Swagger로 PDF 2개 올리고, 같은 파일 다시 올리면 `DUPLICATE` |
| 5 | `GET /api/batches/{batch_id}`: 소속 문서들의 `doc_status`를 세어 진행률 반환 | 4단계 묶음의 진행률이 보임 |
| 6 | 검수 API가 처리할 때마다 `ReviewLog` 한 줄 추가 | 시험용 컬렉션에서 승인 1번 → 기록 1줄 |
| 7 | (4b 완료 후) 업로드 후 `BackgroundTasks`로 파이프라인 실행, 단계마다 `doc_status` 갱신 | PDF 1건 올리고 완료까지 상태 변화 확인 |

## 완료 기준
- 10페이지 PDF가 업로드부터 완료까지 15초 이내 (`doc_latency_sec`)
- 모든 새 API를 Swagger에서 시험 가능, 바뀐 내용은 `docs/migration/api_changes.md`에 기록

## 하면 안 되는 것
- `job_id`, `upload_id` 같은 이름 (→ `batch_id`)
- `ReviewLog` 수정·삭제 API
- 실제 서비스 컬렉션에서 검수 버튼 시험 (→ 시험용 컬렉션)
