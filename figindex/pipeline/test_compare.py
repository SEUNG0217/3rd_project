"""
문서 간 비교 엔진 (figindex/shared/compare.py) 단위 테스트.
롯데쇼핑 사례(하나증권 억원 vs LS증권 십억원, 비교 분석 리포트 4절)를 본뜬 payload로 검증한다.

실행:
  pytest figindex/pipeline/test_compare.py -v
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGINDEX_DIR = REPO_ROOT / "figindex"
if str(FIGINDEX_DIR) not in sys.path:
    sys.path.insert(0, str(FIGINDEX_DIR))

from shared.compare import available_metrics, build_comparison  # noqa: E402
from shared.schemas import ElementType, PeriodBasis  # noqa: E402


def _payload(element_id, doc_id, source_org, page_number, table_data, element_type=ElementType.TABLE):
    return {
        "element_id": element_id,
        "doc_id": doc_id,
        "doc_name": f"{doc_id}.pdf",
        "source_org": source_org,
        "publish_date": "2026-11-05",
        "page_number": page_number,
        "element_type": element_type.value,
        "table_data": table_data,
        "extra_metadata": {"target": "롯데쇼핑"},
    }


HANA = _payload(
    "fig-hana", "doc-hana", "하나증권", 3,
    {
        "columns": ["구분", "2024", "2025", "2026E", "2027E"],
        "rows": [
            {"구분": "총매출액", "2024": 200000, "2025": 201000, "2026E": 205000, "2027E": 210000},
            {"구분": "순매출액", "2024": 139866, "2025": 137383, "2026E": 143645, "2027E": 148876},
            {"구분": "영업이익", "2024": 4731, "2025": 5470, "2026E": 7624, "2027E": 8597},
            {"구분": "영업이익률", "2024": 2.4, "2025": 2.8, "2026E": 3.7, "2027E": 4.0},
        ],
        "unit": None,
        "unit_by_row": {"총매출액": "억원", "순매출액": "억원", "영업이익": "억원", "영업이익률": "%"},
    },
)

LS = _payload(
    "fig-ls", "doc-ls", "LS증권", 2,
    {
        "columns": ["(십억원)", "2025", "2026E", "2027E", "2026E 변경률"],
        "rows": [
            {"(십억원)": "매출액", "2025": 13738, "2026E": 14365, "2027E": 14888, "2026E 변경률": 1.2},
            {"(십억원)": "영업이익", "2025": 547, "2026E": 762, "2027E": 860, "2026E 변경률": -3.0},
            {"(십억원)": "영업이익률 (%)", "2025": 4.0, "2026E": 5.3, "2027E": 5.8, "2026E 변경률": None},
        ],
        "unit": None,
        "unit_by_column": {"2025": "십억원", "2026E": "십억원", "2027E": "십억원"},
        "unit_by_row": {"영업이익률 (%)": "%"},
    },
)

# 같은 문서 뒷페이지의 상세 표: 앞 페이지 값이 우선이어야 한다
HANA_DETAIL = _payload(
    "fig-hana-detail", "doc-hana", "하나증권", 9,
    {
        "columns": ["구분", "2025", "2026E"],
        "rows": [{"구분": "영업이익", "2025": 9999, "2026E": 9999}],
        "unit": "억원",
    },
)

CHART = _payload("fig-chart", "doc-ls", "LS증권", 4, None, element_type=ElementType.CHART)


def test_operating_profit_converted_to_common_unit():
    result = build_comparison([HANA, LS, HANA_DETAIL, CHART], "롯데쇼핑", "영업이익")
    assert result.metric_name == "영업이익"
    assert result.period_keys == ["2024", "2025", "2026", "2027"]
    by_key = {(c.source_org, c.period_key): c for c in result.cells}

    hana_2025 = by_key[("하나증권", "2025")]
    ls_2025 = by_key[("LS증권", "2025")]
    assert hana_2025.unit == ls_2025.unit == result.unit
    assert hana_2025.value == pytest.approx(ls_2025.value, rel=0.01)
    # 원문은 그대로 남는다
    assert hana_2025.raw_value == 5470 and hana_2025.raw_unit == "억원"
    assert ls_2025.raw_value == 547 and ls_2025.raw_unit == "십억원"
    # 같은 문서의 뒷페이지 값(9999)은 쓰지 않는다
    assert hana_2025.element_id == "fig-hana"


def test_requested_unit_is_used():
    result = build_comparison([HANA, LS], "롯데쇼핑", "영업이익", unit="억원")
    assert result.unit == "억원"
    ls_2026 = next(c for c in result.cells if c.source_org == "LS증권" and c.period_key == "2026")
    assert ls_2026.value == pytest.approx(7620.0)
    assert ls_2026.period_basis == PeriodBasis.ESTIMATE


def test_revenue_uses_net_sales_not_gross():
    result = build_comparison([HANA, LS], "롯데쇼핑", "매출액", unit="십억원")
    hana_2025 = next(c for c in result.cells if c.source_org == "하나증권" and c.period_key == "2025")
    assert hana_2025.raw_row_label == "순매출액"
    assert hana_2025.value == pytest.approx(13738.3)


def test_ratio_is_not_converted_and_differences_stay_visible():
    # 이름이 같아도 기준이 다를 수 있다 (하나 2.8% vs LS 4.0%) → 값을 바꾸지 않고 그대로 보여 준다
    result = build_comparison([HANA, LS], "롯데쇼핑", "영업이익률")
    assert result.unit is None
    values = {(c.source_org, c.period_key): c.value for c in result.cells}
    assert values[("하나증권", "2025")] == 2.8
    assert values[("LS증권", "2025")] == 4.0
    assert all(c.unit == "%" for c in result.cells)


def test_qualifier_columns_are_excluded():
    result = build_comparison([LS], "롯데쇼핑", "영업이익")
    assert all(c.raw_column != "2026E 변경률" for c in result.cells)
    assert len(result.cells) == 3


def test_unknown_metric_returns_empty():
    result = build_comparison([HANA, LS], "롯데쇼핑", "EBITDA")
    assert result.cells == [] and result.period_keys == []


def test_available_metrics_counts_documents():
    metrics = available_metrics([HANA, LS, HANA_DETAIL, CHART])
    assert metrics["영업이익"] == 2
    assert metrics["매출액"] == 2
    assert metrics["영업이익률"] == 2
    assert "총매출액" not in metrics


def test_string_numbers_are_read():
    # 추출 결과에 문자열 숫자가 남아 있어도 비교할 수 있어야 한다
    payload = _payload(
        "fig-str", "doc-str", "하나증권", 2,
        {
            "columns": ["구분", "2025", "2026E", "2027E"],
            "rows": [{"구분": "영업이익", "2025": "5,470", "2026E": "△120", "2027E": "-"}],
            "unit": "억원",
        },
    )
    result = build_comparison([payload], "롯데쇼핑", "영업이익")
    values = {c.period_key: (c.raw_value, c.value) for c in result.cells}
    assert values == {"2025": ("5,470", 5470.0), "2026": ("△120", -120.0)}
    assert available_metrics([payload]) == {"영업이익": 1}


# 실제 v2 데이터(LS증권 롯데쇼핑 리포트 1쪽 "Financial Data")와 같은 모양: 표 단위가 "십억원 (단위별 상이)" 하나뿐
LS_REAL = _payload(
    "fig-72221b254fe1", "doc-ls-real", "LS증권", 1,
    {
        "columns": ["(십억원)", "2024", "2025", "2026E"],
        "rows": [
            {"(십억원)": "영업이익", "2024": "473", "2025": "547", "2026E": "762"},
            {"(십억원)": "EPS (원)", "2024": "-34,241", "2025": "1,824", "2026E": "8,665"},
            {"(십억원)": "PER (x)", "2024": "-1.6", "2025": "39.8", "2026E": "16.2"},
            {"(십억원)": "영업이익률 (%)", "2024": "3.4", "2025": "4.0", "2026E": "5.3"},
        ],
        "unit": "십억원 (단위별 상이)",
        "unit_by_row": {},
        "unit_by_column": {},
    },
)


def test_mixed_unit_table_amount_uses_table_krw_unit():
    result = build_comparison([LS_REAL], "롯데쇼핑", "영업이익", unit="억원")
    assert result.unit == "억원"
    cell = next(c for c in result.cells if c.period_key == "2025")
    assert cell.value == pytest.approx(5470.0)
    assert cell.raw_unit == "십억원 (단위별 상이)"


@pytest.mark.parametrize("metric, unit", [("EPS", "원"), ("PER", "배"), ("영업이익률", "%")])
def test_mixed_unit_table_non_amount_not_converted(metric, unit):
    result = build_comparison([LS_REAL], "롯데쇼핑", metric, unit="억원")
    assert result.unit is None
    assert {c.unit for c in result.cells} == {unit}
    assert all(c.value == pytest.approx(float(str(c.raw_value).replace(",", ""))) for c in result.cells)
