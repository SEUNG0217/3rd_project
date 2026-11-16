"""
문서 간 비교 엔진 (순수 함수)

같은 대상(extra_metadata.target)의 여러 문서 표에서 "같은 지표 × 같은 기간" 값을 모은다.
Qdrant 조회는 백엔드가 하고, 이 모듈은 받은 payload(dict) 목록만 다룬다.

규칙
- TABLE 요소의 table_data만 본다. 숫자가 아닌 셀은 건너뛴다.
- 행 라벨은 normalize_metric, 열 이름은 normalize_period로 해석한다.
- 같은 문서·같은 기간 값이 여러 개면 앞 페이지 값을 쓴다 (요약 표가 보통 앞에 있음).
- 원화 금액이면 가장 많이 쓰인 원화 단위(또는 지정 단위)로 환산한다. 원문 값은 raw_*에 남긴다.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

from shared.normalize import (
    KRW_SCALE,
    clean_row_label,
    convert_krw,
    normalize_metric,
    normalize_period,
    normalize_unit,
)
from shared.schemas import ComparisonCell, ComparisonResult, ElementType, TableData


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _table_data(payload: Dict[str, Any]) -> Optional[TableData]:
    if payload.get("element_type") != ElementType.TABLE.value:
        return None
    raw = payload.get("table_data")
    if not raw:
        return None
    try:
        return TableData.model_validate(raw)
    except Exception:
        return None


def _period_sort_key(period_key: str) -> Tuple[int, int]:
    if "Q" in period_key:
        year, quarter = period_key.split("Q")
        return int(year), int(quarter)
    return int(period_key), 0


def _collect_cells(payload: Dict[str, Any], metric_name: str) -> List[ComparisonCell]:
    table = _table_data(payload)
    if table is None or len(table.columns) < 2:
        return []
    first_column = table.columns[0]
    extra = payload.get("extra_metadata") or {}
    cells: List[ComparisonCell] = []
    for row in table.rows:
        label = row.get(first_column)
        if label is None or normalize_metric(str(label)) != metric_name:
            continue
        _, unit_hint = clean_row_label(str(label))
        for column in table.columns[1:]:
            period = normalize_period(column)
            if period is None:
                continue
            raw_value = row.get(column)
            if not _is_number(raw_value):
                continue
            raw_unit = table.unit_for(str(label), column) or unit_hint
            cells.append(
                ComparisonCell(
                    element_id=payload["element_id"],
                    doc_id=payload["doc_id"],
                    doc_name=payload.get("doc_name", ""),
                    source_org=payload.get("source_org") or extra.get("broker"),
                    publish_date=payload.get("publish_date"),
                    page_number=payload.get("page_number", 1),
                    metric_name=metric_name,
                    period_key=period["period_key"],
                    period_basis=period["period_basis"],
                    raw_row_label=str(label),
                    raw_column=column,
                    raw_value=raw_value,
                    raw_unit=raw_unit,
                    value=float(raw_value),
                    unit=normalize_unit(raw_unit),
                )
            )
    return cells


def _pick_krw_unit(cells: Iterable[ComparisonCell], requested: Optional[str]) -> Optional[str]:
    requested_unit = normalize_unit(requested)
    if requested_unit in KRW_SCALE:
        return requested_unit
    counts = Counter(c.unit for c in cells if c.unit in KRW_SCALE)
    return counts.most_common(1)[0][0] if counts else None


def build_comparison(
    payloads: Iterable[Dict[str, Any]],
    target: str,
    metric_name: str,
    unit: Optional[str] = None,
) -> ComparisonResult:
    """payload 목록에서 metric_name 값을 모아 문서별·기간별 비교 결과를 만든다."""
    ordered = sorted(payloads, key=lambda p: (p.get("doc_id", ""), p.get("page_number", 0)))

    cells: List[ComparisonCell] = []
    seen: set = set()
    for payload in ordered:
        for cell in _collect_cells(payload, metric_name):
            key = (cell.doc_id, cell.period_key)
            if key in seen:
                continue
            seen.add(key)
            cells.append(cell)

    krw_unit = _pick_krw_unit(cells, unit)
    if krw_unit:
        for cell in cells:
            converted = convert_krw(cell.raw_value, cell.unit, krw_unit)
            if converted is not None:
                cell.value = round(converted, 4)
                cell.unit = krw_unit

    period_keys = sorted({c.period_key for c in cells}, key=_period_sort_key)
    cells.sort(key=lambda c: (_period_sort_key(c.period_key), c.source_org or "", c.doc_id))
    return ComparisonResult(
        target=target,
        metric_name=metric_name,
        unit=krw_unit,
        period_keys=period_keys,
        cells=cells,
    )


def available_metrics(payloads: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """대상의 표들에서 비교할 수 있는 지표와, 그 지표를 가진 문서 수를 센다."""
    docs_by_metric: Dict[str, set] = {}
    for payload in payloads:
        table = _table_data(payload)
        if table is None or not table.columns:
            continue
        first_column = table.columns[0]
        has_period = any(normalize_period(c) for c in table.columns[1:])
        if not has_period:
            continue
        for row in table.rows:
            label = row.get(first_column)
            metric = normalize_metric(str(label)) if label is not None else None
            if metric:
                docs_by_metric.setdefault(metric, set()).add(payload.get("doc_id"))
    return {m: len(d) for m, d in sorted(docs_by_metric.items(), key=lambda kv: (-len(kv[1]), kv[0]))}
