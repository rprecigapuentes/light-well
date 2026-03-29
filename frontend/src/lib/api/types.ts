export type ISODate = string; // "YYYY-MM-DD"
export type ISODateTime = string; // ISO 8601

export interface TierResult {
  compliant: boolean;
  threshold: number;
  best_continuous_minutes: number;
  missing_minutes: number;
  best_window_start: ISODateTime | null;
  best_window_end: ISODateTime | null;
  required_minutes: number;
  max_gap_min: number;
}

export interface L04Result {
  tier_1: TierResult;
  tier_2: TierResult;
  notes?: string | null;
}

export interface Features {
  count: number;
  duration_s: number;
  edi_min: number | null;
  edi_max: number | null;
  edi_mean: number | null;
  edi_median: number | null;
  edi_std: number | null;
  edi_p10: number | null;
  edi_p90: number | null;
  edi_last: number | null;
  edi_delta_vs_median: number | null;
}

export interface RawRow {
  created_at: ISODateTime;
  edi: number;
}

export interface DailyViewResponse {
  count: number;
  features_global: Features;
  l04_global: { tier_1: TierResult; tier_2: TierResult };
  features_by_day: Record<ISODate, Features>;
  l04_by_day: Record<ISODate, L04Result>;
  rows: RawRow[];
}

export type LLMOutput =
  | string
  | {
      summary?: string;
      recommendations?: string[];
      answer?: string;
      notes?: string;
    };

export interface InsightResponse {
  count: number;
  context: object;
  llm: LLMOutput;
}

export interface AskResponse {
  count: number;
  question: string;
  context: object;
  llm: LLMOutput;
}
