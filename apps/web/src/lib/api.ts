import {
  buildFallbackBreakdown,
  deleteFallbackSavedSlip,
  evaluateSlipFallback,
  FALLBACK_CALIBRATION,
  FALLBACK_CATEGORIES,
  filterFallbackEvents,
  generateSlipsFallback,
  listFallbackSavedSlips,
  saveFallbackSlip,
} from "./fallback-data";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type ActiveSportSlug = "football" | "basketball" | "tennis" | "hockey";

export type BookmakerMode =
  | "betclic_tax_free"
  | "fortuna_promo"
  | "superbet_boost"
  | "standard_088";

export type RiskProfile = "conservative" | "balanced" | "aggressive" | "max_value";

export interface SportCategoryItem {
  id: number;
  slug: ActiveSportSlug | string;
  name_pl: string;
  is_enabled_v1: boolean;
  volatility_tier: string;
  active_model: string;
  fixtures_count: number;
  updated_at: string;
}

export interface CategoriesResponse {
  categories: SportCategoryItem[];
  total: number;
}

export interface MarketOutcomeDetail {
  outcome_key: string;
  outcome_label: string;
  best_bookmaker: string;
  odds_decimal: number;
  p_model: number;
  p_sharp: number;
  p_true: number;
  fair_odds: number;
  ev_standard_pl: number;
  ev_taxfree_pl: number;
  is_value_bet: boolean;
  kelly_fraction: number;
}

export interface EventMarket {
  market_key: string;
  market_label: string;
  outcomes: MarketOutcomeDetail[];
}

export interface PreMatchEventItem {
  id: string;
  sport_slug: ActiveSportSlug;
  sport_name_pl: string;
  league_id: number;
  league_name: string;
  league_country?: string | null;
  home_team: string;
  away_team: string;
  start_time_utc: string;
  status: string;
  surface_or_format?: string | null;
  primary_market: EventMarket;
  all_markets_count: number;
  max_ev_net: number;
  is_value_bet: boolean;
}

export interface EventsResponse {
  events: PreMatchEventItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EventsQueryParams {
  sport?: string;
  league_id?: number;
  market?: string;
  min_ev?: number;
  limit?: number;
  offset?: number;
}

export interface BayesianFusionInfo {
  model_weight: number;
  sharp_weight: number;
  sharp_bookmaker: string;
}

export interface CompetitorRatingDetail {
  competitor_id?: string;
  rating_elo?: number;
  surface_elo?: number;
  xg_attack?: number;
  xg_defense?: number;
  goals_attack?: number;
  goals_defense?: number;
  pace?: number;
  ortg?: number;
  drtg?: number;
  rest_days?: number;
  serve_win_pct?: number;
  return_win_pct?: number;
  [key: string]: unknown;
}

export interface FactualFactor {
  label: string;
  value: string;
  impact: "positive" | "negative" | "neutral";
}

export interface EventBreakdownResponse {
  event_id: string;
  sport: ActiveSportSlug | string;
  league_name: string;
  home_team: string;
  away_team: string;
  start_time_utc: string;
  status: string;
  model_name: string;
  model_version: string;
  bayesian_fusion: BayesianFusionInfo;
  competitor_ratings: {
    home: CompetitorRatingDetail;
    away: CompetitorRatingDetail;
  };
  factual_factors: FactualFactor[];
  sport_breakdown: Record<string, unknown>;
  available_markets: EventMarket[];
}

export interface CandidateSelection {
  event_id: string;
  event_name: string;
  sport: string;
  league_name: string;
  start_time_utc: string;
  market_key: string;
  market_label: string;
  outcome_key: string;
  outcome_label: string;
  bookmaker_key: string;
  odds_gross: number;
  p_model: number;
  p_sharp: number;
  p_true: number;
  ev_net: number;
  applied_tax_multiplier: number;
}

export interface SplitAdvice {
  recommended: boolean;
  original_gross_payout: number;
  original_tax_deduction: number;
  split_tickets_count: number;
  stake_per_ticket: number;
  payout_per_ticket: number;
  net_tax_saved: number;
  advice_text: string;
}

export interface EvaluatedSlip {
  selections: CandidateSelection[];
  total_odds_gross: number;
  tax_multiplier: number;
  total_odds_net: number;
  joint_probability: number;
  stake: number;
  potential_payout_gross: number;
  potential_payout_net: number;
  pit_10_applies: boolean;
  pit_10_deduction: number;
  pit_warning?: string | null;
  slip_ev_net: number;
  kelly_stake_fraction: number;
  kelly_recommended_stake_pln: number;
  tax_savings_advice?: SplitAdvice | null;
  is_correlated: boolean;
  anti_correlation_passed: boolean;
  validation_warnings: string[];
}

export interface GeneratedSlipProposal extends EvaluatedSlip {
  id: string;
  title: string;
  risk_tier: string;
}

export interface SlipGenerateParams {
  sports: string[];
  markets?: string[] | null;
  risk_profile: RiskProfile;
  target_odds_min: number;
  target_odds_max: number;
  min_legs: number;
  max_legs: number;
  min_leg_prob?: number;
  stake: number;
  bookmaker_mode: BookmakerMode;
  only_plus_ev: boolean;
  custom_overrides?: Record<string, number>;
}

export interface SlipGenerateResponse {
  coupons: GeneratedSlipProposal[];
  candidate_pool_size: number;
  solver_algorithm: string;
  execution_time_ms: number;
}

export interface LegInput {
  event_id: string;
  market_key: string;
  outcome_key: string;
  bookmaker_key?: string;
  odds_override?: number;
}

export interface SlipEvaluateRequest {
  selections: LegInput[];
  stake: number;
  bookmaker_mode: BookmakerMode;
}

export interface SaveSlipRequest {
  name?: string;
  selections: LegInput[];
  stake: number;
  bookmaker_mode: BookmakerMode;
  bookmaker_key?: string;
}

export interface SavedSlipRecord {
  id: string;
  user_id: string;
  name: string;
  selections?: CandidateSelection[];
  selections_json?: string;
  bookmaker_key: string;
  tax_multiplier: number;
  total_odds_gross: number;
  total_odds_net: number;
  stake: number;
  potential_payout_gross: number;
  potential_payout_net: number;
  joint_probability: number;
  slip_ev_net: number;
  recommended_kelly_stake_pct: number;
  pit_10_applies: boolean | number;
  created_at: string;
}

export interface SavedSlipsResponse {
  items: SavedSlipRecord[];
  total: number;
}

export interface SaveSlipResponse {
  slip: SavedSlipRecord;
}

export interface SportCalibrationMetric {
  sport: string;
  sport_name_pl: string;
  model_name: string;
  sample_size: number;
  brier_score: number;
  log_loss: number;
  clv_beat_rate: number;
  avg_clv_percentage: number;
}

export interface ReliabilityBin {
  bin_index: number;
  predicted_prob_lower: number;
  predicted_prob_upper: number;
  mean_predicted_prob: number;
  empirical_win_rate: number;
  sample_count: number;
  brier_contribution: number;
}

export interface CalibrationMetricsResponse {
  time_horizon: string;
  overall: {
    sample_size: number;
    brier_score: number;
    brier_skill_score: number;
    log_loss: number;
    clv_beat_rate: number;
    avg_clv_percentage: number;
  };
  by_sport: SportCalibrationMetric[];
  reliability_bins: ReliabilityBin[];
  last_calculated_at: string;
}

export const ACTIVE_V1_SPORTS: ReadonlyArray<{
  slug: ActiveSportSlug;
  name_pl: string;
  model_label: string;
  short_desc: string;
}> = [
  {
    slug: "football",
    name_pl: "Piłka nożna",
    model_label: "Dixon-Coles xG (70/30)",
    short_desc: "Bivariate Poisson z korektą niskich wyników τ i de-viggingiem Shina",
  },
  {
    slug: "basketball",
    name_pl: "Koszykówka",
    model_label: "Pace × ORtg/DRtg",
    short_desc: "Model tempa posiadań (Pace), efektywności netto i zmęczenia B2B",
  },
  {
    slug: "tennis",
    name_pl: "Tenis",
    model_label: "Surface Elo + Markov",
    short_desc: "Łańcuch Markowa punkt → gem → set → mecz z podziałem na nawierzchnie",
  },
  {
    slug: "hockey",
    name_pl: "Hokej",
    model_label: "Skellam 60m + Empty Net",
    short_desc: "Rozkład różnicy bramek Skellama w czasie regulaminowym i korekta EN",
  },
];

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${errText || res.statusText}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export async function fetchCategories(enabledOnly = true): Promise<CategoriesResponse> {
  const query = enabledOnly ? "?enabled_only=true" : "";
  try {
    return await apiRequest<CategoriesResponse>(`/api/v1/categories${query}`);
  } catch {
    return FALLBACK_CATEGORIES;
  }
}

export async function fetchEvents(params?: EventsQueryParams): Promise<EventsResponse> {
  const search = new URLSearchParams();
  if (params?.sport) search.set("sport", params.sport);
  if (params?.league_id !== undefined) search.set("league_id", String(params.league_id));
  if (params?.market) search.set("market", params.market);
  if (params?.min_ev !== undefined) search.set("min_ev", String(params.min_ev));
  if (params?.limit !== undefined) search.set("limit", String(params.limit));
  if (params?.offset !== undefined) search.set("offset", String(params.offset));
  const qs = search.toString();
  try {
    return await apiRequest<EventsResponse>(`/api/v1/events${qs ? `?${qs}` : ""}`);
  } catch {
    return filterFallbackEvents(params);
  }
}

export async function fetchEventBreakdown(eventId: string): Promise<EventBreakdownResponse> {
  try {
    return await apiRequest<EventBreakdownResponse>(
      `/api/v1/events/${encodeURIComponent(eventId)}/breakdown`
    );
  } catch {
    return buildFallbackBreakdown(eventId);
  }
}

export async function generateSlips(params: SlipGenerateParams): Promise<SlipGenerateResponse> {
  try {
    return await apiRequest<SlipGenerateResponse>("/api/v1/slips/generate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  } catch {
    return generateSlipsFallback(params);
  }
}

export async function evaluateSlip(payload: SlipEvaluateRequest): Promise<EvaluatedSlip> {
  try {
    return await apiRequest<EvaluatedSlip>("/api/v1/slips/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch {
    return evaluateSlipFallback(payload);
  }
}

export async function fetchSavedSlips(userId?: string): Promise<SavedSlipsResponse> {
  const qs = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  try {
    return await apiRequest<SavedSlipsResponse>(`/api/v1/slips/saved${qs}`);
  } catch {
    return listFallbackSavedSlips();
  }
}

export async function saveSlip(payload: SaveSlipRequest): Promise<SaveSlipResponse> {
  try {
    return await apiRequest<SaveSlipResponse>("/api/v1/slips/saved", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch {
    return saveFallbackSlip(payload);
  }
}

export async function deleteSavedSlip(slipId: string): Promise<void> {
  try {
    await apiRequest<void>(`/api/v1/slips/saved/${encodeURIComponent(slipId)}`, {
      method: "DELETE",
    });
  } catch {
    deleteFallbackSavedSlip(slipId);
  }
}

export async function fetchCalibrationMetrics(
  timeHorizon = "90d"
): Promise<CalibrationMetricsResponse> {
  try {
    return await apiRequest<CalibrationMetricsResponse>(
      `/api/v1/calibration/metrics?time_horizon=${encodeURIComponent(timeHorizon)}`
    );
  } catch {
    return FALLBACK_CALIBRATION;
  }
}
