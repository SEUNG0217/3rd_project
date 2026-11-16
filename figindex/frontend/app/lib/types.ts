export interface TableData {
  columns: string[];
  rows: Record<string, any>[];
  unit?: string;
  unit_by_row?: Record<string, string>;
  unit_by_column?: Record<string, string>;
  period_labels?: string[];
}

export interface ConfidenceSignals {
  layout?: number;
  ocr?: number;
  clip?: number;
  text_match?: number;
}

export interface VisualElement {
  element_id: string;
  doc_id?: string;
  doc_name: string;
  page_number: number;
  bbox: number[];
  element_type: "TABLE" | "CHART" | "DIAGRAM";
  image_path: string;
  caption: string;
  summary?: string;
  table_data?: TableData;
  hashtags?: string[];
  confidence_score: number;
  signals?: ConfidenceSignals;
  review_status: string;
  doc_title?: string;
  doc_type: string;
  domain?: string;
  source_org?: string;
  authors?: string[];
  publish_date?: string;
  collection_id?: string;
  pipeline_version?: string;
  model_name?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  qdrant_url: string;
  qdrant_connected: boolean;
  collection_name: string;
  collection_exists: boolean;
  total_elements?: number;
  error?: string;
}

export interface FilterOptions {
  doc_types: string[];
  source_orgs: Record<string, string[]>;
  targets: Record<string, string[]>;
  publish_dates: string[];
  element_types: string[];
}

