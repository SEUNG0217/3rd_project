# 역할 브리핑: 팀원 A (크롭·탐지)

> AI에게: 이 사용자는 프로젝트에 처음 참여했고 코딩이 익숙하지 않다. 한 번에 한 단계씩, 코드를 쓰기 전에 무엇을 왜 하는지 먼저 설명한다. 각 단계는 사용자가 직접 실행하고 눈으로 확인하게 한다. 루트 `AGENTS.md`와 `figindex/pipeline/AGENTS.md`를 따른다.

## 한 줄 요약
PDF 한 페이지를 사진처럼 보고, 그 안에서 **표·차트가 있는 네모 영역(bbox)** 을 찾아 정확히 오려 내는 일입니다. 여기서 잘못 오리면 뒤의 모든 단계가 틀립니다.

## 전체에서 내 위치
`PDF 업로드 → ★표·차트 오려 내기★ → AI가 내용 읽기 → 확신도 → 저장 → 검색`

## 지금 상황
- 지금은 규칙(글자 위치 계산)으로 오려 내고 있습니다: `figindex/pipeline/cropper.py`
- 문서 레이아웃 전용 AI 모델(DocLayout-YOLO)로 바꾸면 더 정확할지 시험하는 스크립트가 있습니다: `figindex/pipeline/yolo_trial.py`
- 목표: 둘을 비교해서 더 나은 쪽을 고르고, YOLO가 낫다면 본 파이프라인에 연결합니다.

## 알아야 할 말
| 말 | 뜻 |
| --- | --- |
| bbox | 오려 낼 네모. `[x0, y0, x1, y1]` = 왼쪽 위 점과 오른쪽 아래 점. 페이지 크기를 1로 봤을 때의 비율(0~1) |
| Detection | YOLO가 찾은 네모 하나 (아직 오리기 전) |
| 캡션 병합 | 표 제목·단위·출처 줄이 잘리지 않게 본 네모와 합치는 것 |
| IoU | 두 네모가 얼마나 겹치는지 (0~1). 0.5 이상이면 "같은 걸 찾았다"고 봄 |
| crop_recall | 정답 표·차트 중 제대로 찾아낸 비율. 목표 0.85 이상 |

## 관련 파일
- `figindex/pipeline/cropper.py`: 지금 쓰는 오리기 코드
- `figindex/pipeline/yolo_trial.py`: YOLO 시험 스크립트
- `figindex/shared/coords.py`: 좌표 계산 함수 모음 (좌표는 반드시 여기 함수로만 계산)
- `figindex/shared/schemas.py`: `Detection`, `LayoutClass`, `LAYOUT_TO_ELEMENT`, `MERGE_CLASSES`
- `docs/glossary.md`: 2절(유형 구분), 3절(탐지 클래스), 8절(좌표), 12절(지표)

## 할 일
| 단계 | 할 일 | 확인 방법 |
| --- | --- | --- |
| 1 | 웹 화면(localhost:3000)에서 카드 20개를 보고, 제목이나 단위가 잘린 크롭을 3개 찾아 메모 | 잘린 예 3개를 팀 채팅에 캡처로 공유 |
| 2 | `docker compose run --rm pipeline python yolo_trial.py --limit 5` 실행 | 결과 폴더에 예전 방식/YOLO 비교 이미지가 생김 |
| 3 | 비교 이미지를 보고 어느 쪽이 더 잘 찾는지 PDF별로 표로 정리 | 표 1장 (PDF, 예전 방식 놓친 것, YOLO 놓친 것) |
| 4 | YOLO 모델의 클래스 이름(`model.names`)이 `schemas.py`의 `LayoutClass` 값과 같은지 확인 | 다른 이름이 있으면 팀장에게 보고 |
| 5 | 탐지 정답셋 만들기: 50페이지에서 진짜 표·차트 위치를 기록 (아래 방법) | `data/gt/detection/`에 50페이지분 파일 |
| 6 | 정답셋으로 예전 방식과 YOLO의 `crop_recall` 계산 | 두 숫자를 팀장에게 보고 → 어느 방식을 쓸지 결정 |
| 7 | (YOLO로 결정되면, 병합 후) YOLO를 `cropper.py`에 연결 | 시험용 컬렉션에 PDF 1건 색인, 화면에서 크롭 확인 |

### 5단계 정답셋 만드는 방법
- 처음부터 네모를 그리지 않습니다. AI에게 "YOLO 결과를 페이지 이미지 위에 번호와 함께 그려 주고, 같은 내용을 JSON 초안으로 저장하는 스크립트"를 만들게 합니다.
- 사람은 그림을 보고 **틀린 것만** 고칩니다: 노이즈면 지우기, 유형이 틀리면 고치기, 놓친 표·차트는 추가.
- 파일 하나 = 페이지 하나: `data/gt/detection/{doc_name}_p{page_number}.json`
  ```json
  {"doc_name": "...", "page_number": 3,
   "elements": [{"element_type": "TABLE", "bbox": [0.08, 0.12, 0.92, 0.45]}]}
  ```
- 50페이지는 서로 다른 PDF 10~15개에서 고릅니다. 표가 많은 페이지, 차트가 많은 페이지, 2단 편집 페이지를 섞습니다.

## 완료 기준
- `crop_recall` ≥ 0.85
- 10페이지 PDF를 오리는 데 15초 이내

## 하면 안 되는 것
- 좌표를 직접 곱하고 나누는 코드 (→ `coords.py` 함수 사용)
- `figindex_elements_v2` 컬렉션에 쓰기
- 전체 PDF 118건을 한꺼번에 돌리기 (1~5건으로 시험)

## 막히면
Docker 실행 오류, 메모리 부족 → `figindex/README.md` 9절. 그래도 안 되면 30분 안에 팀장에게.
