// Enums
export type CompanyStage = 'seed' | 'series_a' | 'series_b' | 'series_c' | 'growth';
export type MethodName = 'last_round' | 'comparables';
export type Confidence = 'high' | 'medium' | 'low';

// Company models
export interface Company {
  id: string;
  name: string;
  sector: string;
  stage: CompanyStage;
  founded_date?: string;
}

export interface Financials {
  revenue_ttm?: string;
  revenue_growth_yoy?: string;
  gross_margin?: string;
  burn_rate?: string;
  runway_months?: number;
}

export interface LastRound {
  date: string;
  valuation_pre: string;
  valuation_post: string;
  amount_raised: string;
  lead_investor?: string;
}

export interface Adjustment {
  name: string;
  factor: string;
  reason: string;
}

export interface CompanyData {
  company: Company;
  financials: Financials;
  last_round?: LastRound;
  adjustments: Adjustment[];
}

// Result models
export interface AuditStep {
  step_number: number;
  description: string;
  inputs: Record<string, unknown>;
  calculation?: string;
  result?: string;
}

export interface MethodResult {
  method: MethodName;
  value: string;
  confidence: Confidence;
  audit_trail: AuditStep[];
  warnings: string[];
}

export interface MethodSkipped {
  method: MethodName;
  reason: string;
}

export interface MethodComparisonItem {
  method: MethodName;
  value: string;
  confidence: Confidence;
  is_primary: boolean;
}

export interface MethodComparisonData {
  methods: MethodComparisonItem[];
  spread_percent?: string;
  spread_warning?: string;
  selection_steps: string[];
}

export interface ValuationSummary {
  primary_value: string;
  primary_method: MethodName;
  value_range_low?: string;
  value_range_high?: string;
  overall_confidence: Confidence;
  summary_text: string;
  selection_reason: string;
  method_comparison?: MethodComparisonData;
}

export interface ValuationResult {
  company_id: string;
  company_name: string;
  valuation_date: string;
  summary: ValuationSummary;
  method_results: MethodResult[];
  skipped_methods: MethodSkipped[];
  cross_method_analysis?: string;
  config_snapshot: Record<string, unknown>;
}

// API models
export interface CompanyListItem {
  id: string;
  name: string;
  sector: string;
  stage: string;
}

export interface ErrorResponse {
  error_type: string;
  message: string;
  details?: Record<string, unknown>;
}

// New types for saved valuations

export interface ValuationListItem {
  id: string;
  company_name: string;
  primary_value: string;
  primary_method: MethodName;
  overall_confidence: Confidence;
  valuation_date: string;
  created_at: string;
}

// SavedValuation from database - uses flexible types for JSONB fields
export interface SavedValuation {
  id: string;
  portfolio_company_id: string;
  company_name: string;
  input_snapshot: Record<string, unknown>;
  primary_value: string;
  primary_method: string;
  value_range_low?: string;
  value_range_high?: string;
  overall_confidence: string;
  summary: {
    primary_value: string;
    primary_method: string;
    value_range_low?: string;
    value_range_high?: string;
    overall_confidence: string;
    summary_text: string;
    selection_reason: string;
    method_comparison?: {
      methods: Array<{
        method: string;
        value: string;
        confidence: string;
        is_primary: boolean;
      }>;
      spread_percent?: string;
      spread_warning?: string;
      selection_steps: string[];
    };
  };
  method_results: Array<{
    method: string;
    value: string;
    confidence: string;
    audit_trail: AuditStep[];
    warnings: string[];
  }>;
  skipped_methods: Array<{
    method: string;
    reason: string;
  }>;
  config_snapshot: Record<string, unknown>;
  valuation_date: string;
  created_at: string;
}

export interface PortfolioCompany {
  id: string;
  name: string;
  sector_id: string;
  stage: CompanyStage;
  founded_date?: string;
  financials: Financials;
  last_round?: LastRound;
  adjustments: Adjustment[];
  created_at?: string;
}

export interface SavedValuationResponse {
  id: string;
  company_id: string;
  company_name: string;
  valuation_date: string;
  summary: ValuationSummary;
  method_results: MethodResult[];
  skipped_methods: MethodSkipped[];
  cross_method_analysis?: string;
  config_snapshot: Record<string, unknown>;
}
