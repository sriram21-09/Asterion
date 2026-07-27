export type SearchResultType = 'cdr_record' | 'tower' | 'case';

export interface CDRSearchResult {
  result_type: 'cdr_record';
  id: number;
  import_job_id: number;
  case_id?: number;
  operator: string;
  target_number?: string;
  b_party_number?: string;
  call_type?: string;
  service_type?: string;
  timestamp?: string;
  duration?: number;
  latitude?: number;
  longitude?: number;
  first_cgi?: string;
  last_cgi?: string;
  imei?: string;
  imsi?: string;
}

export interface TowerSearchResult {
  result_type: 'tower';
  id: number;
  tower_name: string;
  cgi?: string;
  ci?: string;
  mcc?: string;
  mnc?: string;
  lac?: string;
  operator?: string;
  latitude?: number;
  longitude?: number;
}

export interface CaseSearchResult {
  result_type: 'case';
  id: number;
  title: string;
  description?: string;
  status: string;
}

export type SearchResultItem = CDRSearchResult | TowerSearchResult | CaseSearchResult;

export interface PaginatedSearchResponse {
  results: SearchResultItem[];
  total: number;
  limit: number;
  offset: number;
  query: string;
}
