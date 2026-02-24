/** TypeScript interfaces matching backend schemas. */

export interface ExtractionResult {
  predictor_name: string;
  stock_name: string;
  stock_symbol: string;
  target_price: number;
  current_price_mentioned: number | null;
  timeframe: string | null;
  direction: string;
  raw_quote: string | null;
  confidence: number;
  source_type: string;
}

export interface ExtractionResponse {
  url: string;
  predictions: ExtractionResult[];
  source_text_length: number;
}

export interface PredictionResponse {
  id: string;
  predictor_id: string;
  stock_id: string;
  target_price: string;
  price_at_prediction: string;
  prediction_date: string;
  target_date: string | null;
  default_eval_date: string;
  source_url: string;
  source_type: string;
  source_archive_url: string | null;
  raw_quote: string | null;
  submitted_by: string | null;
  extraction_method: string;
  ai_confidence: string | null;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  upside_pct: string;
}

export interface SuggestionResponse {
  id: string;
  url: string;
  note: string | null;
  submitted_by: string;
  status: string;
  promoted_to: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface ApiError {
  detail: string;
}
