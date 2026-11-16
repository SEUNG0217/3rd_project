> 이 문서는 덧붙이지 말고 매번 전체를 다시 쓴다.

# FigIndex 프로젝트 종합 현황서 (AI 분석·인수인계용)

- **작성 시각**: 2026-11-16 10:22 (KST)
- **현재 브랜치**: `refactor/schema-unify` (기준 커밋: `b531816`)
- **저장소 루트**: `c:\workAi\workProject\3차플젝`
- **검사기 상태**: `check_state.py --full` PASS=10, WARN=1, FAIL=0 (엄격 금지 이름 0건, 단위 테스트 58건 전원 통과)

---

## 0. 한눈에 보기 (10줄 이내)

1. **지금 단계**: **4a(백엔드/프론트엔드 전환) 및 4b(파이프라인 전환 및 레거시 정리) 전면 완료**, **브랜치 병합(`refactor/schema-unify` ➔ `main`) 직전**입니다.
2. **서비스가 보는 컬렉션**: 백엔드, 프론트엔드, 파이프라인 모두 **새 컬렉션 `figindex_elements_v2`(465건)**를 단일 기준으로 바라보고 있습니다.
3. **새 컬렉션 상태**: `figindex_elements_v2`는 **465건(문서 113개)**으로 서비스 중이며, 파이프라인 색인과 백엔드 조회가 완벽히 `ElementSearchPayload`로 일치합니다.
4. **금지 이름 상태**: `figindex/` 코드베이스 전체에서 **엄격 금지 이름이 기준선 114건에서 0건으로 완전 박멸**되었습니다.
5. **바로 다음 작업**: **브랜치 병합 및 릴리스** — `refactor/schema-unify` 브랜치를 검증하고 화요일(11/17) `main` 브랜치에 병합합니다.
6. **그 다음 작업**: **3주차 과제** — DocLayout-YOLO 파이프라인 정식 이식, 확신도 5개 신호 정규화, ReviewLog 누적 불변화, 지표·기간 정규화 사전 엔진 탑재.
7. **주의사항 (Warning)**:
   - `schemas.py`, `AGENTS.md`, `docs/glossary.md` 무단 수정 금지
   - Qdrant 실서비스 컬렉션(`figindex_elements`, `figindex_elements_v2`) 임의 삭제·수정 금지
   - 루트 `app/`은 `scripts/generate_sample_pdf.py` 참조가 남아있어 삭제 대기 상태로 보존

---

## 1. 프로젝트 개요·실행 환경

- **프로젝트 목적**: PDF 문서(증권 리포트, 공공 보고서, 학술 논문, IR 자료)에서 표(`TABLE`), 차트(`CHART`), 다이어그램(`DIAGRAM`)만 정밀 추출·구조화하여 **"여러 증권사 리포트의 동일 지표·기간을 모아 한눈에 비교·검수하는 지식 도서관"** 구축.
- **기술 스택**:
  - **Frontend**: Next.js 14 (`react-pdf`, Tailwind CSS, TypeScript, 포트 `3000`)
  - **Backend**: FastAPI (`uvicorn`, Python 3.10+, 포트 `8000`)
  - **Vector DB**: Qdrant (`dense` 1536차원 Cosine + `sparse` BM25, 포트 `6333`/`6334`)
  - **Pipeline**: PyMuPDF(`fitz`), `kiwipiepy`, `doclayout-yolo`, Gemini Multimodal API, OpenAI Embeddings (`text-embedding-3-small`)
- **실행 환경 (`figindex/docker-compose.yml`)**:
  - `figindex-qdrant`, `figindex-backend`, `figindex-frontend` 3개 서비스가 로컬 Docker에서 정상 가동 중 (`QDRANT_MODE=server`, `QDRANT_COLLECTION=figindex_elements_v2`).
  - `pipeline` 서비스는 `profiles: ["index"]`로 분리되어 독립 컨테이너 실행 지원 (`docker compose run --rm pipeline ...`).
  - 로컬 프로덕션 검증용 `figindex/docker-compose.prod.yml` 별도 구비 (`QDRANT_COLLECTION=figindex_elements_v2` 적용).

---

## 2. 기준 파일과 규칙

프로젝트의 모든 코드와 에이전트는 아래 6개 단일 기준(Single Source of Truth)을 따르며, 임의 정의는 엄격히 금지됩니다.

1. **`figindex/shared/schemas.py`**: 프로젝트의 유일한 표준 스키마 기준 (`Element`, `ElementSearchPayload`, `TableData`, `ConfidenceSignals`, `Document`, `Batch`, `ReviewLog` 등 11개 표준 모델 및 Enum).
2. **`figindex/shared/coords.py`**: 바운딩 박스 정규화 `[x0, y0, x1, y1]`(좌상단 원점, 0~1) 및 좌표 변환(pt/px, IoU, 패딩)의 유일한 계산 기준.
3. **`docs/glossary.md`**: 표 셀 수치 규칙(7절), 좌표계(8절), 단위 규칙 4원칙(9절), 확신도 가중치(10절), 평가 지표(12절)의 정의 기준.
4. **`AGENTS.md`**: 쓰지 않는 이름 표(2절), schemas.py 필드명 준수, 수정 금지 파일 등 AI 에이전트의 절대 행동 규칙.
5. **`figindex/pipeline/pdf_text.py`**: 증권 리포트 글자 드로잉 순서 꼬임을 해결하기 위해 PDF 텍스트 레이어를 2차원 좌표 순서로 정렬하여 읽는 단일 추출 함수 기준.
6. **`scripts/check_state.py`**: 코드베이스 전체의 금지 이름, 수정 금지 파일 변경, AST 컴파일, 단위 테스트, BBox 유효성을 검증하는 정합성 검사기 기준.

---

## 3. 데이터 현황

| 컬렉션 / 자원 | 건수 | 상태 | 비고 |
| :--- | :---: | :---: | :--- |
| **`figindex_elements_v2` (새 컬렉션)** | **465건** | **실서비스 조회 및 색인** | **백엔드/프론트엔드/파이프라인 단일 기준**, `ElementSearchPayload` 적용 (문서 113개, 승인 386건, 검수 대기 79건) |
| **`figindex_elements` (옛 컬렉션)** | **525건** | 읽기 전용 (보존) | v1 스냅샷 및 롤백 대비용 보존 데이터 |
| **크롭 이미지 (`figindex/data/crops/`)** | 578개 | 정상 보존 | 서빙 경로 `/static/crops/{filename}` 지원 |
| **원본 PDF (`figindex/data/pdfs/`)** | 118건 | 정상 보존 | 색인 완료 113건 + 미색인 5건 (원문 404 누락 0건) |
| **엔티티 사전 (`figindex/data/entity_dictionary.csv`)** | 1건+헤더 | 기본 탑재 | SK하이닉스 및 주요 기업 티커 매핑 지원 |

- **마이그레이션 기록 위치 (`figindex/data/migration/`)**:
  - `api_changes.md`: v1 ➔ v2 API 응답/요청 변경 내역 및 신규 필드 명세
  - `doc_id_map.json`: 고유 문서 113개에 대한 `doc_name` ➔ `doc_id` 단일 발급 맵
  - `execute_v2_20261113-0351.md`: v2 컬렉션 실제 이전 실행 결과 및 검증 리포트
  - `dropped_elements_20261113-0350.csv`: 중복 제외된 60건의 메타데이터 보존 파일
- **데이터 분석 기록 위치 (`figindex/data/analysis/`)**:
  - `comparability_20261113-1633.md`: 교차 증권사 비교 가능성 정량 분석 리포트
  - `targets.csv`: 종목별 리포트/증권사/테이블 집계 (47개 종목)
  - `row_labels.csv`: 표 행 라벨 빈도 및 원문 변형 예시 (1,271개 라벨)
  - `period_labels.csv`: 기간 표기 패턴 유형 및 정규화 제안 (689개 표기)

---

## 4. 완료된 작업 (시간순 압축)

1. **새 파일명 파서 및 다중 문서 유형 지원 (`6711e0d`)**: RPT/PUB/PAP/IR 4대 문서 유형 분류 및 파일명 해석 CLI 지원.
2. **메타데이터 일반화 ("증권사/기업명" ➔ "출처/대상") (`23f8118`)**: `source_org` 및 `extra_metadata.target` 도입 및 프론트 라벨 동적 변경.
3. **로컬 Docker 핫 리로드 환경 정리 (`23f8118`)**: Next.js 및 FastAPI 실시간 reload 구성.
4. **Qdrant 동시성 충돌 해결 및 단일화 (`23f8118`, `2864055`)**: 단일 QdrantClient 인스턴스화 및 동시 40건 API 검증 통과.
5. **DocLayout-YOLO 시험 스크립트 작성 (`3e89a0b`)**: `yolo_trial.py`로 탐지 성능 비교 시험 완료.
6. **스키마 통합 1단계 현황 조사 및 authors 필드 추가 (`fc9becc`)**: 525건 BBox 전수 검사 및 `inventory.md` 작성.
7. **schemas.py 미등재 필드 조사 및 백엔드 즉시 호환 조치 (`2864055`)**: DTO에 표준 필드(`caption`, `table_data` 등) 최우선 수용.
8. **기준 스키마 이전 및 schemas_legacy 분리 (`f5f10c1`)**: `figindex/shared/schemas.py`를 유일한 SSOT로 단일화, 옛 모델은 `schemas_legacy`로 임시 격리.
9. **공통 좌표 모듈 구현 (`d14f974`, `7b0a01b`)**: `figindex/shared/coords.py` 구현 및 단위 테스트 23건 통과.
10. **상태 검사기 check_state.py 및 기준선 체계 구축 (`1be8140`, `89a3e22`)**: A그룹/B그룹 11개 검사기 및 기준선 관리 체계 도입.
11. **doc_name 조사 및 이중 색인 원인 규명 (`688f06f`)**: 옛 이름 29개 이중 색인 및 60건 중복 요소 식별 완료.
12. **v2 컬렉션 마이그레이션 스크립트 구현 (`29c723a`, `7a12e16`)**: `migrate_to_v2.py` 작성 및 dry-run 검증 (465건 이전, 60건 제외).
13. **v2 컬렉션 실제 이전 실행 완료 (`40221f8`, `67ffa9d`)**: `figindex_elements_v2` 생성, 벡터·페이로드 검증 100% 통과 (465건, 113개 문서).
14. **TableData에 행별·열별 단위 필드 및 unit_for() 추가 (`ad9c59f`, `51a39e0`)**: `unit_by_row`, `unit_by_column` 추가 및 검증 로직 구현.
15. **PDF 좌표 순서 정렬 텍스트 추출 함수 구현 (`ed7e285`, `56fd587`)**: `pdf_text.py` 구축으로 드로잉 순서 꼬임(68.6% ➔ 686% .) 해결.
16. **상태 검사기 A1 수정 금지 파일 감시 보강 (`4957d35`, `56fd587`)**: `--allow-protected` 도입 및 경로 정규화 결함 수정.
17. **상태 검사기 A2·A7 보완 (`dd10aef`, `53f35e4`)**: A2 상위 파일별 개수 표기, A7 문법 검사 범위 복원, 일회성 도구 제외.
18. **검사기 기준선 갱신 (`1a90908`)**: 일회성 도구 정리 후 엄격 금지 이름 기준선을 114건으로 갱신.
19. **v2 데이터 비교 가능성 정량 분석 (`9888201`)**: 롯데쇼핑 등 2개 증권사 교차 테이블에서 동일 지표/기간 비교 가능성 실증 완료.
20. **4a 단계: 백엔드·프론트엔드 v2 전환 완료**:
    - 백엔드 `main.py` 컬렉션 기본값 `figindex_elements_v2`로 전환, `schemas_legacy` 제거, `ElementSearchPayload`/`TableData` 응답 모델 적용, `ReviewActionRequest` 표준화, 확신도 임계값 `CONFIDENCE_THRESHOLD` 적용.
    - `docker-compose.yml`, `docker-compose.prod.yml` 환경변수 적용.
    - `docs/migration/api_changes.md`, `lib/types.ts`, `lib/tableUnits.ts` 작성 및 프론트엔드 4개 파일 엄격 금지 이름 70건 전수 제거(0건 달성).
21. **4b 단계: 파이프라인 새 스키마 전환 및 레거시 정리 완료 (현재 단계)**:
    - **파이프라인 5개 파일 스키마 전면 치환**: `extractor.py`, `evaluator.py`, `orchestrator.py`, `run_index.py`, `test_metadata_generalization.py`에서 `VisualElementSchema`, `TableStructure`, `title_or_caption`, `structured_data` 전수 제거 (0건 달성).
    - **역할 분리 구현**: `orchestrator`가 `Document` 1회 메타데이터 추출 및 메모리 유지 (`doc_id_map.json` 연동), `extractor`는 `doc_id`를 받아 `Element` 생성, `orchestrator`가 `ElementSearchPayload`를 조합해 Qdrant upsert.
    - **확신도 평가기 표준화**: `evaluator.py`에서 자체 상수를 제거하고 `SIGNAL_WEIGHTS`, `CONFIDENCE_THRESHOLD` import 및 `ConfidenceSignals` 객체 구성.
    - **좌표 변환 표준화**: `cropper.py` 및 `yolo_trial.py`에서 `coords.py` (`px_to_norm`, `norm_to_px`) 함수 연동 및 `file_name` ➔ `doc_name` 치환.
    - **레거시 파일 삭제**: `figindex/shared/schemas_legacy.py` 영구 삭제 완료.
    - **루트 app/ 참조 조사**: `scripts/generate_sample_pdf.py`의 참조 확인으로 보존 처리.
    - **시험 컬렉션 검증 통과**: `figindex_elements_4b_test` 생성 후 1건 색인(2개 도표) ➔ `ElementSearchPayload.model_validate()` PASS, bbox 0~1 `[x0, y0, x1, y1]` PASS, `doc_id` 일치 PASS 확인 후 컬렉션 안전 삭제 완료.
    - **정합성 검사 통과**: `check_state.py --full` PASS=10, WARN=1, FAIL=0 및 파이프라인 pytest 58건 전원 통과.

---

## 5. 검사기 현재 상태

- **엄격 금지 이름 검사 (A2)**: **0건 (기준선 114건 대비 114건 전면 감소, 개선)**
  - `figindex/backend/app/main.py`: **0건**
  - `figindex/pipeline/extractor.py`: **0건**
  - `figindex/pipeline/evaluator.py`: **0건**
  - `figindex/pipeline/orchestrator.py`: **0건**
  - `figindex/pipeline/run_index.py`: **0건**
  - `figindex/pipeline/test_metadata_generalization.py`: **0건**
  - `figindex/pipeline/rename_reports.py`: **0건**
  - `figindex/pipeline/yolo_trial.py`: **0건**
  - `figindex/frontend/app/components/ReviewTab.tsx`: **0건**
  - `figindex/frontend/app/components/ComparisonModal.tsx`: **0건**
  - `figindex/frontend/app/elements/[id]/page.tsx`: **0건**
  - `figindex/frontend/app/page.tsx`: **0건**
- **A3 직접 쓴 상태 문자열**: **PASS** (6건 감소, 현재 41건)
- **A4 직접 쓴 확신도 임계값**: **PASS** (1건 감소, 현재 4건)
- **A5 Import 규칙**: **PASS** (app.schemas 0건, legacy 참조 0개 파일)
- **A6 모델 중복 정의**: **PASS** (0건)
- **A7 Python 문법 검사**: **PASS** (30개 파일 전체 정상)
- **A8 단위 테스트 검사**: **PASS** (58건 100% 성공)
- **B1 API 상태 검사**: **PASS**
- **B2 Qdrant 데이터 검사**: **PASS** (BBox 위반 0건)
- **B3 프론트엔드 타입 검사**: **PASS** (타입 에러 0건)

---

## 6. 다음 단계 (로드맵)

### 브랜치 병합 (화요일 11/17)
- `refactor/schema-unify` 브랜치 회귀 검증 완료 후 `main` 브랜치 병합.

### 3주차 과제
1. **DocLayout-YOLO 파이프라인 정식 통합**: `yolo_trial.py` 결과를 본 크로퍼(`cropper.py`)에 이식.
2. **확신도 5개 신호 정규화**: `text_match` 계산 시 `pdf_text.py` 기반 좌표 정렬 텍스트 적용.
3. **ReviewLog 누적 저장**: 검수 이력 불변 테이블/컬렉션 연동.
4. **지표·기간 정규화 사전 엔진**: 분석 리포트에서 제안된 지표 18개군 및 기간 정규화 규칙을 검색·비교 엔진에 적용.

---

## 7. 알려진 문제·주의점

1. **루트 app/ 디렉터리 보존 사유**: `scripts/generate_sample_pdf.py` 라인 8에서 `from app.core.config import settings`를 참조하고 있으므로, 해당 스크립트 리팩토링 전까지 루트 `app/`은 임의 삭제하지 않고 유지합니다.
2. **실서비스 Qdrant 컬렉션 보존**: 실서비스 컬렉션인 `figindex_elements_v2`(465건)와 보존용 `figindex_elements`(525건)에 대한 직접적인 데이터 삭제/쓰기는 엄격히 제한됩니다.
