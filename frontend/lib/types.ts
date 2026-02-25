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

// --- Public data types ---

export interface PredictorResponse {
  id: string;
  name: string;
  slug: string;
  type: string;
  parent_id: string | null;
  designation: string | null;
  bio: string | null;
  avatar_url: string | null;
  website: string | null;
  social_links: Record<string, string>;
  sebi_reg_no: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface StockResponse {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  bse_code: string | null;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  current_price: string | null;
  price_updated_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LeaderboardEntry {
  predictor_id: string;
  predictor_name: string;
  predictor_slug: string;
  predictor_type: string;
  total_predictions: number;
  hits: number;
  misses: number;
  partial_hits: number;
  accuracy_pct: string | null;
  avg_deviation_pct: string | null;
  streak_current: number;
}

export interface ScorecardResponse {
  predictor_id: string;
  total_predictions: number;
  hits: number;
  misses: number;
  partial_hits: number;
  pending: number;
  accuracy_pct: string | null;
  avg_deviation_pct: string | null;
  avg_upside_predicted: string | null;
  best_sector: string | null;
  worst_sector: string | null;
  sector_accuracy: Record<string, number>;
  streak_current: number;
  last_prediction_date: string | null;
  last_updated: string;
}

export interface PredictionOutcomeResponse {
  id: string;
  prediction_id: string;
  outcome_status: string;
  actual_price: string | null;
  highest_price: string | null;
  lowest_price: string | null;
  deviation_pct: string | null;
  evaluated_at: string | null;
  evaluation_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchHit {
  id: string;
  name: string;
  slug_or_symbol: string;
  type: "predictor" | "stock";
  sub_type: string | null;
}

export interface SearchResponse {
  predictors: SearchHit[];
  stocks: SearchHit[];
}

// --- Auth types ---

export interface AuthUser {
  id: string;
  email: string | null;
  phone: string | null;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  auth_methods: string[];
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface OTPSendResponse {
  message: string;
  identifier: string;
  expires_in_seconds: number;
}

export interface OTPVerifyResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface GoogleAuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}
