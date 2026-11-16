"""
비교 엔진용 정규화 함수 (기간 · 지표 · 금액 단위)

여러 문서의 표(TableData)에서 "같은 지표 × 같은 기간"을 찾아 나란히 놓기 위한 순수 함수 모음.
- 입력은 TableData의 원문 열 이름(columns), 행 라벨(첫 열 값), 단위 문자열이다.
- 저장된 데이터는 바꾸지 않는다. 비교 시점에만 계산한다.
- 근거 데이터: figindex/data/analysis/period_labels.csv, row_labels.csv (2026-11-13 분석)

비교 결과 모델은 schemas.py의 ComparisonCell, ComparisonResult, 기간 성격은 PeriodBasis.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from shared.schemas import PeriodBasis

# ---------------------------------------------------------------------------
# 1. 기간
# ---------------------------------------------------------------------------
# period_key 형식: "2026" (연간) / "2026Q3" (분기)
# period_basis: 원문 접미사 A/E/F/P → PeriodBasis. 접미사가 없으면 None (실적/추정 판단하지 않음)

_BASIS_MAP = {
    "A": PeriodBasis.ACTUAL,
    "E": PeriodBasis.ESTIMATE,
    "F": PeriodBasis.ESTIMATE,
    "P": PeriodBasis.PRELIM,
}

# 기간과 함께 붙으면 "그 기간의 값"이 아닌 열 (수정 전후, 증감률, 컨센서스 등) → 비교 대상에서 뺀다
_QUALIFIER_TOKENS = (
    "수정전", "수정후", "수정 전", "수정 후", "변경전", "변경후", "변경 전", "변경 후",
    "변경률", "변동률", "변경", "변동", "기존", "신규", "직전", "당시", "이전",
    "컨센", "consensus", "yoy", "qoq", "y-y", "q-q", "차이", "diff", "gap", "대비",
    "증감", "%", "예상치", "추정치", "당사", "발표", "실적발표", "잠정치",
)

_YEAR_FULL = r"(?P<year4>20\d{2})"
_YEAR_SHORT = r"(?P<year2>\d{2})"
_BASIS = r"(?P<basis>[AEFP])?"

_PERIOD_PATTERNS: List[re.Pattern] = [
    # 2026E, 2025, 2026F, 2025A, FY2026E, 2026E_Annual, 2025*_Annual
    re.compile(rf"^(?:FY)?{_YEAR_FULL}{_BASIS}\*?(?:_Annual)?$"),
    # 2025년
    re.compile(rf"^{_YEAR_FULL}년$"),
    # 26E, 25, FY25, '26E, ’25
    re.compile(rf"^(?:FY|['’])?{_YEAR_SHORT}{_BASIS}$"),
    # 3Q26, 3Q26P, 4Q26E, 3Q.26P, 3Q 25, 3Q2025
    re.compile(rf"^(?P<q>[1-4])Q[.\s]?(?:{_YEAR_FULL}|{_YEAR_SHORT}){_BASIS}$"),
    # 2025.3Q, 25.3Q, 25Q3, 2025Q3
    re.compile(rf"^(?:{_YEAR_FULL}|{_YEAR_SHORT})[.\s]?(?:(?P<q2>[1-4])Q|Q(?P<q3>[1-4])){_BASIS}$"),
    # 2025 1Q, 2026F 2Q, 2025_1Q*, 2026_3QP, 2026_4QE
    re.compile(rf"^{_YEAR_FULL}(?P<basis_y>[AEFP])?[\s_](?P<q4>[1-4])Q{_BASIS}\*?$"),
]


def normalize_period(label: str) -> Optional[Dict[str, object]]:
    """열 이름을 기간으로 해석한다. 기간이 아니거나 수식어가 붙은 열이면 None.

    >>> normalize_period("3Q26P")["period_key"]
    '2026Q3'
    """
    if label is None:
        return None
    raw = str(label)
    text = raw.strip()
    if not text:
        return None

    lowered = text.lower()
    if any(token in lowered for token in _QUALIFIER_TOKENS):
        return None

    for pattern in _PERIOD_PATTERNS:
        m = pattern.match(text)
        if not m:
            continue
        groups = m.groupdict()
        if groups.get("year4"):
            year = int(groups["year4"])
        else:
            year = 2000 + int(groups["year2"])
            # 두 자리 숫자 열(나이·번호 등)을 연도로 오인하지 않도록 범위를 좁힌다
            if not 2010 <= year <= 2035:
                return None
        quarter_text = groups.get("q") or groups.get("q2") or groups.get("q3") or groups.get("q4")
        quarter = int(quarter_text) if quarter_text else None
        basis_char = groups.get("basis") or groups.get("basis_y")
        period_basis = _BASIS_MAP.get(basis_char.upper()) if basis_char else None
        period_key = f"{year}Q{quarter}" if quarter else f"{year}"
        return {
            "period_key": period_key,
            "year": year,
            "quarter": quarter,
            "period_basis": period_basis,
            "raw": raw,
        }
    return None


# ---------------------------------------------------------------------------
# 2. 행 라벨 → 지표
# ---------------------------------------------------------------------------
# 대표 지표명: 별칭 목록. 비교 분석 리포트의 18개 묶음에서 시작하되,
# 의미가 다른 것은 분리했다 (당기순이익 ≠ 지배주주순이익, 매출액 ≠ 총매출액).
METRIC_ALIASES: Dict[str, List[str]] = {
    "매출액": ["매출액", "순매출액", "매출", "연결 매출액", "영업수익", "revenue", "sales"],
    "영업이익": ["영업이익", "영업손익", "op", "operating profit"],
    "영업이익률": ["영업이익률", "영업이익율", "opm", "%opm", "op 마진", "op margin"],
    "세전이익": ["세전이익", "세전순이익", "세전손익", "세전계속사업이익", "법인세차감전순이익",
             "법인세비용차감전순이익", "ebt"],
    "당기순이익": ["당기순이익", "순이익", "총당기순이익", "net income", "np"],
    "지배주주순이익": ["지배주주순이익", "지배순이익", "지배지분순이익", "지배주주당기순이익",
                "지배주주 당기순이익", "지배기업 순이익", "지배기업 당기순이익", "지배이익", "지배순익",
                "[지배주주]순이익"],
    "순이익률": ["순이익률", "당기순이익률", "npm", "%npm", "np margin"],
    "매출총이익": ["매출총이익", "gross profit"],
    "매출원가": ["매출원가", "cogs"],
    "EBITDA": ["ebitda", "조정 ebitda", "에비타"],
    "EPS": ["eps", "주당순이익", "수정eps"],
    "BPS": ["bps", "주당순자산"],
    "ROE": ["roe", "자기자본이익률"],
    "ROA": ["roa", "총자산이익률"],
    "PER": ["per", "p/e", "주가수익비율"],
    "PBR": ["pbr", "p/b", "주가순자산비율"],
    "EV/EBITDA": ["ev/ebitda", "ev/에비타"],
    "배당수익률": ["배당수익률", "배당수익율", "시가배당률"],
    "부채비율": ["부채비율", "부채/자본"],
}

# 지표별 단위 성격. 원화 환산은 AMOUNT만 한다 (EPS·BPS는 원이지만 주당 값이라 환산하지 않음).
METRIC_UNIT_GROUP: Dict[str, str] = {
    "매출액": "AMOUNT", "영업이익": "AMOUNT", "세전이익": "AMOUNT", "당기순이익": "AMOUNT",
    "지배주주순이익": "AMOUNT", "매출총이익": "AMOUNT", "매출원가": "AMOUNT", "EBITDA": "AMOUNT",
    "영업이익률": "PERCENT", "순이익률": "PERCENT", "ROE": "PERCENT", "ROA": "PERCENT",
    "배당수익률": "PERCENT", "부채비율": "PERCENT",
    "PER": "MULTIPLE", "PBR": "MULTIPLE", "EV/EBITDA": "MULTIPLE",
    "EPS": "PER_SHARE", "BPS": "PER_SHARE",
}
_GROUP_DEFAULT_UNIT = {"PERCENT": "%", "MULTIPLE": "배", "PER_SHARE": "원"}

_ALIAS_INDEX: Dict[str, str] = {
    alias.lower(): metric for metric, aliases in METRIC_ALIASES.items() for alias in aliases
}

# 행 라벨 괄호 안의 단위 힌트로 인정하는 값
_UNIT_HINTS = ("원", "천원", "백만원", "억원", "십억원", "조원", "%", "배", "x", "X", "천주", "만주")

_PAREN = re.compile(r"\s*[\(\[]([^\)\]]*)[\)\]]\s*")
_LEADING_MARK = re.compile(r"^\s*(?:[·•\-\*]|[①-⑳]|\d+(?:\.\d+)*[.)]|[A-Z][.)])\s*")


def clean_row_label(label: str) -> Tuple[str, Optional[str]]:
    """행 라벨에서 단위 괄호·번호·불릿을 떼고 (정리된 라벨, 단위 힌트)를 돌려준다.

    >>> clean_row_label("영업이익(십억원)")
    ('영업이익', '십억원')
    """
    text = str(label or "").strip()
    text = _LEADING_MARK.sub("", text)
    unit_hint: Optional[str] = None
    for inner in _PAREN.findall(text):
        candidate = inner.strip().replace(" ", "")
        if candidate in _UNIT_HINTS:
            unit_hint = candidate
    cleaned = _PAREN.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
    return cleaned, unit_hint


def normalize_metric(label: str) -> Optional[str]:
    """행 라벨을 대표 지표명으로 바꾼다. 사전에 없으면 None.

    "[지배주주]순이익"처럼 괄호 자체가 의미인 라벨은 정리 전 원문으로 먼저 찾는다.
    """
    raw = str(label or "").strip()
    # 단위 괄호만 뗀 형태로 먼저 찾는다 ("[지배주주]순이익 (억원)" → "[지배주주]순이익")
    without_unit = _PAREN.sub(
        lambda m: " " if m.group(1).strip().replace(" ", "") in _UNIT_HINTS else m.group(0), raw
    )
    without_unit = re.sub(r"\s+", " ", without_unit).strip()
    for candidate in (raw, without_unit):
        if candidate.lower() in _ALIAS_INDEX:
            return _ALIAS_INDEX[candidate.lower()]
    cleaned, _ = clean_row_label(raw)
    return _ALIAS_INDEX.get(cleaned.lower())


# ---------------------------------------------------------------------------
# 3. 셀 값 → 숫자
# ---------------------------------------------------------------------------
# glossary 9절: 숫자는 숫자로 저장하는 게 규칙이지만, 추출 결과에 "5,470", "△1.2", "(3.0)", "4.0%"
# 같은 문자열이 남아 있을 수 있다. 비교할 때만 읽고, 저장값은 바꾸지 않는다.
_NUMBER = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
_EMPTY_MARKS = {"", "-", "–", "—", "n/a", "na", "nm", "n.m.", "적지", "흑전", "적전", "적확", "흑지"}


def parse_number(value: object) -> Optional[float]:
    """셀 값을 숫자로 읽는다. 읽을 수 없으면 None.

    >>> parse_number("5,470"), parse_number("△1.2"), parse_number("(3.0)"), parse_number("4.0%")
    (5470.0, -1.2, -3.0, 4.0)
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace(" ", "")
    if text.lower() in _EMPTY_MARKS:
        return None
    negative = False
    if text.startswith("△") or text.startswith("▽"):
        negative, text = True, text[1:]
    elif text.startswith("(") and text.endswith(")"):
        negative, text = True, text[1:-1]
    elif text.startswith("▲"):
        text = text[1:]
    text = text.rstrip("%")
    if not _NUMBER.match(text):
        return None
    number = float(text)
    return -abs(number) if negative else number


# ---------------------------------------------------------------------------
# 4. 금액 단위 환산 (원화만)
# ---------------------------------------------------------------------------
KRW_SCALE: Dict[str, float] = {
    "원": 1.0,
    "천원": 1e3,
    "백만원": 1e6,
    "억원": 1e8,
    "십억원": 1e9,
    "조원": 1e12,
}


def normalize_unit(unit: Optional[str]) -> Optional[str]:
    """단위 표기 흔들림을 정리한다. "십억 원" → "십억원", "(억원, %)" 같은 묶음은 None."""
    if unit is None:
        return None
    text = str(unit).strip().strip("()[]").replace(" ", "")
    if not text or "," in text:
        return None
    if text.lower() in ("x",):
        return "배"
    return text


def extract_krw_unit(text: Optional[str]) -> Optional[str]:
    """"십억원 (단위별 상이)", "(십억원)", "십억 원" 같은 글에서 원화 단위를 찾는다."""
    if not text:
        return None
    compact = str(text).replace(" ", "")
    for unit in sorted(KRW_SCALE, key=len, reverse=True):
        if unit in compact:
            return unit
    return None


def resolve_unit(
    metric_name: str,
    row_label: str,
    explicit_row_unit: Optional[str],
    explicit_column_unit: Optional[str],
    table_unit: Optional[str],
    header_label: Optional[str] = None,
) -> Optional[str]:
    """셀 단위를 정한다. 우선순위:
    unit_by_row → 행 라벨 괄호 단위 → unit_by_column → 지표 성격 기본값(%·배·원) → 표 단위·첫 열 머리글의 원화 단위
    """
    if explicit_row_unit:
        return normalize_unit(explicit_row_unit)
    _, hint = clean_row_label(row_label)
    if hint:
        return normalize_unit(hint)
    if explicit_column_unit:
        return normalize_unit(explicit_column_unit)
    group = METRIC_UNIT_GROUP.get(metric_name)
    if group in _GROUP_DEFAULT_UNIT:
        return _GROUP_DEFAULT_UNIT[group]
    return extract_krw_unit(table_unit) or extract_krw_unit(header_label) or normalize_unit(table_unit)


def convert_krw(value: object, from_unit: Optional[str], to_unit: str) -> Optional[float]:
    """원화 금액을 다른 원화 단위로 환산한다. 숫자가 아니거나 원화 단위가 아니면 None."""
    src = normalize_unit(from_unit)
    dst = normalize_unit(to_unit)
    if src not in KRW_SCALE or dst not in KRW_SCALE:
        return None
    number = parse_number(value)
    if number is None:
        return None
    return number * KRW_SCALE[src] / KRW_SCALE[dst]
