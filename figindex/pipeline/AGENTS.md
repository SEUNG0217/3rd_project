# 파이프라인 폴더 규칙 (figindex/pipeline/)

루트 `AGENTS.md`의 규칙이 먼저 적용되고, 이 폴더에서 작업할 때는 아래를 추가로 따른다.
담당: 팀원 4(크롭), 팀원 3(정답셋), 팀장(추출·확신도).

## 1. 데이터를 망가뜨리지 않기
- Qdrant의 `figindex_elements`, `figindex_elements_v2`에는 쓰지 않는다. 실제 서비스 데이터다.
- 색인을 시험할 때는 `QDRANT_COLLECTION=figindex_test_<이름>` 처럼 내 이름이 들어간 시험용 컬렉션을 새로 만들어 쓰고, 끝나면 그 컬렉션만 지운다.
- PDF는 1~3건으로 시험한다. 전체 PDF를 돌리지 않는다.

## 2. 반드시 정해진 함수를 쓴다
- 좌표 변환·IoU·패딩: `figindex/shared/coords.py` 함수만 쓴다. 직접 계산하지 않는다.
- PDF 글자 읽기: `figindex/pipeline/pdf_text.py` 함수만 쓴다. `page.get_text()`를 직접 부르지 않는다.
- 모델·Enum·상수: `from shared.schemas import ...`. `shared/schemas_legacy.py`는 import하지 않는다.
- 확신도: `SIGNAL_WEIGHTS`, `CONFIDENCE_THRESHOLD`만 쓴다. 적용하지 않은 신호는 `None`.
- YOLO 클래스 처리: `LayoutClass`, `LAYOUT_TO_ELEMENT`, `MERGE_CLASSES`만 쓴다.

## 3. 비용
- Gemini는 무료 티어만 쓴다. 새 유료 API를 추가하지 않는다.
- 같은 이미지를 다시 분석하지 않도록 `extractor.py`의 캐시를 끄지 않는다.

## 4. 바꾼 뒤 확인
- `pytest figindex/pipeline -q`가 모두 통과해야 한다.
- 프롬프트나 후처리(추출 결과가 달라지는 코드)를 바꿨으면 "`PIPELINE_VERSION`을 올려야 함"이라고 보고한다. 직접 올리지 않는다.
- 평가 결과는 `docs/glossary.md` 12절의 지표 코드명(`crop_recall`, `table_valid_rate`, `cell_accuracy`, `token_saving_rate`)을 키로 쓴다.
