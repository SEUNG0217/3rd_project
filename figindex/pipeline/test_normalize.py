"""
비교 엔진 정규화 함수 (figindex/shared/normalize.py) 단위 테스트.
테스트 값은 v2 컬렉션의 실제 열 이름·행 라벨(period_labels.csv, row_labels.csv)에서 가져왔다.

실행:
  pytest figindex/pipeline/test_normalize.py -v
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGINDEX_DIR = REPO_ROOT / "figindex"
if str(FIGINDEX_DIR) not in sys.path:
    sys.path.insert(0, str(FIGINDEX_DIR))

from shared.schemas import PeriodBasis  # noqa: E402
from shared.normalize import (  # noqa: E402
    parse_number,
    clean_row_label,
    convert_krw,
    normalize_metric,
    normalize_period,
    normalize_unit,
)


# ---------------------------------------------------------------------------
# 기간
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw, period_key, period_basis",
    [
        # 연간
        ("2025", "2025", None),
        ("2026E", "2026", PeriodBasis.ESTIMATE),
        ("2026F", "2026", PeriodBasis.ESTIMATE),
        ("2025A", "2025", PeriodBasis.ACTUAL),
        ("2026P", "2026", PeriodBasis.PRELIM),
        ("2024년", "2024", None),
        ("26E", "2026", PeriodBasis.ESTIMATE),
        ("27F", "2027", PeriodBasis.ESTIMATE),
        ("25", "2025", None),
        ("'26E", "2026", PeriodBasis.ESTIMATE),
        ("’22", "2022", None),
        ("FY25", "2025", None),
        ("FY2026E", "2026", PeriodBasis.ESTIMATE),
        ("2026E_Annual", "2026", PeriodBasis.ESTIMATE),
        ("2025*_Annual", "2025", None),
        # 분기
        ("3Q25", "2025Q3", None),
        ("3Q26P", "2026Q3", PeriodBasis.PRELIM),
        ("4Q26E", "2026Q4", PeriodBasis.ESTIMATE),
        ("4Q26F", "2026Q4", PeriodBasis.ESTIMATE),
        ("1Q25A", "2025Q1", PeriodBasis.ACTUAL),
        ("3Q.26P", "2026Q3", PeriodBasis.PRELIM),
        ("1Q.25", "2025Q1", None),
        ("3Q 25", "2025Q3", None),
        ("3Q2025", "2025Q3", None),
        ("2025.3Q", "2025Q3", None),
        ("25.3Q", "2025Q3", None),
        ("25Q3", "2025Q3", None),
        ("2025 1Q", "2025Q1", None),
        ("2026F 2Q", "2026Q2", PeriodBasis.ESTIMATE),
        ("2025_1Q*", "2025Q1", None),
        ("2026_3QP", "2026Q3", PeriodBasis.PRELIM),
        ("2026_4QE", "2026Q4", PeriodBasis.ESTIMATE),
    ],
)
def test_normalize_period_parses(raw, period_key, period_basis):
    result = normalize_period(raw)
    assert result is not None, raw
    assert result["period_key"] == period_key
    assert result["period_basis"] == period_basis
    assert result["raw"] == raw


@pytest.mark.parametrize(
    "raw",
    [
        # 수식어가 붙은 열: 같은 기간이라도 값의 성격이 달라 비교하지 않는다
        "수정전_2026F", "수정후 2027F", "변경 전 2026E", "변동률_2027E", "2026E_기존대비",
        "컨센서스 2026E", "yoy_2026E", "3Q26 YoY", "3Q26_Consensus", "차이(%)",
        "예상치_2026E", "실적발표_3Q26P",
        # 기간이 아닌 열
        "내용", "비고", "현재", "12M", "1M", "Total", "Class 1", "7월", "'25. 9월",
        "2026년 11월 (A)", "45", "1위", "",
    ],
)
def test_normalize_period_rejects(raw):
    assert normalize_period(raw) is None


def test_normalize_period_none_input():
    assert normalize_period(None) is None


# ---------------------------------------------------------------------------
# 행 라벨
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw, cleaned, unit_hint",
    [
        ("영업이익(십억원)", "영업이익", "십억원"),
        ("매출액(억원)", "매출액", "억원"),
        ("영업이익률 (%)", "영업이익률", "%"),
        ("EPS(원)", "EPS", "원"),
        ("PER (x)", "PER", "x"),
        ("EPS(26)", "EPS", None),
        ("BPS(26.12E)", "BPS", None),
        ("[별도기준] 매출액", "매출액", None),
        ("① 출하량", "출하량", None),
        ("· 상 용", "상 용", None),
        ("4. 소결", "소결", None),
    ],
)
def test_clean_row_label(raw, cleaned, unit_hint):
    assert clean_row_label(raw) == (cleaned, unit_hint)


@pytest.mark.parametrize(
    "raw, metric",
    [
        ("영업이익", "영업이익"),
        ("영업이익(십억원)", "영업이익"),
        ("순매출액", "매출액"),
        ("매출액(억원)", "매출액"),
        ("영업이익률(%)", "영업이익률"),
        ("OPM", "영업이익률"),
        ("EPS (원)", "EPS"),
        ("PER(배)", "PER"),
        ("EV/EBITDA(배)", "EV/EBITDA"),
        ("지배주주순이익(억원)", "지배주주순이익"),
        ("[지배주주]순이익 (억원)", "지배주주순이익"),
        ("지배기업 순이익", "지배주주순이익"),
        ("당기순이익", "당기순이익"),
        ("순이익(십억원)", "당기순이익"),
        ("세전계속사업이익", "세전이익"),
        ("ROE(%)", "ROE"),
        ("배당수익률(%)", "배당수익률"),
    ],
)
def test_normalize_metric(raw, metric):
    assert normalize_metric(raw) == metric


@pytest.mark.parametrize(
    "raw",
    [
        # 비슷해 보여도 다른 지표 → 묶지 않는다
        "총매출액", "영업이익 YoY", "매출총이익률", "매출액_YoY", "목표주가", "Recycled", "기타",
    ],
)
def test_normalize_metric_unknown(raw):
    assert normalize_metric(raw) is None


# ---------------------------------------------------------------------------
# 단위
# ---------------------------------------------------------------------------
def test_normalize_unit():
    assert normalize_unit("십억 원") == "십억원"
    assert normalize_unit("(억원)") == "억원"
    assert normalize_unit("x") == "배"
    assert normalize_unit("억원, %") is None
    assert normalize_unit(None) is None


def test_convert_krw_lotte_shopping_case():
    # 비교 분석 리포트의 롯데쇼핑 2025 영업이익: 하나증권 5,470억원 vs LS증권 547십억원
    assert convert_krw(5470, "억원", "십억원") == pytest.approx(547.0)
    assert convert_krw(547, "십억원", "억원") == pytest.approx(5470.0)
    assert convert_krw(137383, "억 원", "십억원") == pytest.approx(13738.3)


def test_convert_krw_rejects_non_krw():
    assert convert_krw(4.0, "%", "억원") is None
    assert convert_krw(12.3, "배", "억원") is None
    assert convert_krw("n/a", "억원", "십억원") is None
    assert convert_krw("-", "억원", "십억원") is None
    assert convert_krw(True, "억원", "십억원") is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        (5470, 5470.0), (4.0, 4.0), ("5,470", 5470.0), ("137,383", 137383.0), ("△1.2", -1.2),
        ("(3.0)", -3.0), ("-1.2", -1.2), ("4.0%", 4.0), ("▲5", 5.0), (" 12 ", 12.0),
        ("-", None), ("n/a", None), ("적지", None), ("흑전", None), ("텍스트", None), (None, None), (True, None),
    ],
)
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


def test_convert_krw_reads_string_numbers():
    assert convert_krw("5,470", "억원", "십억원") == pytest.approx(547.0)
