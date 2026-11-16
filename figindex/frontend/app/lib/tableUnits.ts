import { TableData } from "./types";

/**
 * 표 내 특정 셀(행 라벨, 열 이름)의 유효 단위를 계산하는 단일 함수입니다.
 * 우선순위:
 * 1. unit_by_row[rowLabel] (행별 단위: 매출액=십억원 등)
 * 2. unit_by_column[column] (열별 단위: 2023=억원 등)
 * 3. tableData.unit (표 전역 단위)
 * 4. 빈 문자열 ""
 */
export function unitFor(
  tableData?: TableData | null,
  rowLabel?: string | null,
  column?: string | null
): string {
  if (!tableData) return "";

  if (rowLabel && tableData.unit_by_row && tableData.unit_by_row[rowLabel]) {
    const rowUnit = tableData.unit_by_row[rowLabel];
    if (typeof rowUnit === "string" && rowUnit.trim()) {
      return rowUnit.trim();
    }
  }

  if (column && tableData.unit_by_column && tableData.unit_by_column[column]) {
    const colUnit = tableData.unit_by_column[column];
    if (typeof colUnit === "string" && colUnit.trim()) {
      return colUnit.trim();
    }
  }

  if (tableData.unit && typeof tableData.unit === "string" && tableData.unit.trim()) {
    return tableData.unit.trim();
  }

  return "";
}

