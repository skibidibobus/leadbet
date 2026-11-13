/**
 * Adversarial TypeScript Type Verification Suite.
 *
 * Tests type checking on GeneratedCoupon, CouponSelection, SlipEvaluateRequest,
 * and related types from @quantkupon/contracts.
 *
 * Verifies:
 * 1. Positive corner cases compile cleanly.
 * 2. Negative type violations are caught by the TypeScript compiler using `@ts-expect-error`.
 * 3. Type weaknesses and generator quirks are documented.
 */

import type {
  GeneratedCoupon,
  CouponSelection,
  SlipGenerateRequest,
  SlipEvaluateRequest,
  SlipEvaluateResponse,
  LegInput,
  SplitAdvice,
} from "../../packages/contracts/src/index";

// =============================================================================
// 1. Positive Corner Cases (Must compile cleanly without errors)
// =============================================================================

export const validLegInput: LegInput = {
  event_id: "ev_arsenal_chelsea",
  market_key: "1x2",
  outcome_key: "home",
  odds_override: 1.85,
  bookmaker_key: "sts",
};

export const validLegInputNullable: LegInput = {
  event_id: "ev_real_barca",
  market_key: "totals_2_5",
  outcome_key: "over",
  odds_override: null,
  bookmaker_key: null,
};

export const validSelection: CouponSelection = {
  event_id: "ev_arsenal_chelsea",
  event_name: "Arsenal FC vs Chelsea FC",
  sport: "football",
  league_name: "Premier League",
  start_time_utc: "2026-11-13T20:00:00Z",
  market_key: "1x2",
  market_label: "Wynik meczu (1X2)",
  outcome_key: "home",
  outcome_label: "1",
  bookmaker_key: "sts",
  odds_gross: 1.85,
  p_model: 0.582,
  p_sharp: 0.565,
  p_true: 0.572,
  ev_net: 0.058,
  applied_tax_multiplier: 1.0,
};

export const validSelectionWithNulls: CouponSelection = {
  event_id: null, // Nullable in schema
  event_name: "Generic Match",
  sport: "basketball",
  league_name: "NBA",
  start_time_utc: "2026-11-14T02:00:00Z",
  market_key: "moneyline",
  market_label: "Zwycięzca",
  outcome_key: "home",
  outcome_label: "BOS Celtics",
  bookmaker_key: null, // Nullable in schema
  odds_gross: 1.45,
  p_model: 0.72,
  p_sharp: 0.70,
  p_true: 0.71,
  ev_net: 0.029,
  applied_tax_multiplier: 0.88,
};

export const validSplitAdvice: SplitAdvice = {
  recommended: true,
  original_gross_payout: 3500.0,
  original_tax_deduction: 350.0,
  split_tickets_count: 2,
  stake_per_ticket: 250.0,
  payout_per_ticket: 1750.0,
  net_tax_saved: 350.0,
  advice_text: "Podział stawki 500 PLN na 2 kupony po 250 PLN pozwala uniknąć 10% podatku PIT.",
};

// GeneratedCoupon with 0.88 tax multiplier
export const validCouponStandardTax: GeneratedCoupon = {
  id: "slip_opt_standard",
  title: "Optymalny AKO Standard",
  risk_tier: "conservative",
  selections: [validSelection],
  total_odds_gross: 1.85,
  tax_multiplier: 0.88, // Allowed: 0.88 | 1
  total_odds_net: 1.628,
  joint_probability: 0.572,
  stake: 100.0,
  potential_payout_gross: 185.0,
  potential_payout_net: 162.8,
  pit_10_applies: false,
  pit_10_deduction: 0.0,
  pit_warning: null, // nullable
  slip_ev_net: 0.058,
  kelly_stake_fraction: 0.035,
  kelly_recommended_stake_pln: 35.0,
  anti_correlation_passed: true,
};

// GeneratedCoupon with 1.00 promotional tax multiplier, PIT deduction and split advice
export const validCouponPromoTaxWithPIT: GeneratedCoupon = {
  id: "slip_opt_promo_pit",
  title: "Optymalny AKO Promocyjny z PIT",
  risk_tier: "max_value",
  selections: [validSelection, validSelectionWithNulls],
  total_odds_gross: 5.5,
  tax_multiplier: 1, // Allowed: 0.88 | 1
  total_odds_net: 5.5,
  joint_probability: 0.406,
  stake: 500.0,
  potential_payout_gross: 2750.0,
  potential_payout_net: 2475.0,
  pit_10_applies: true,
  pit_10_deduction: 275.0,
  pit_warning: "Uwaga: wygrana brutto przekracza próg 2280 PLN.",
  slip_ev_net: 0.125,
  kelly_stake_fraction: 0.05,
  kelly_recommended_stake_pln: 50.0,
  tax_savings_advice: validSplitAdvice,
  anti_correlation_passed: true,
};

export const validEvaluateRequest: SlipEvaluateRequest = {
  selections: [validLegInput],
  stake: 100.0,
  bookmaker_mode: "standard_088",
};

export const validGenerateRequestFull: SlipGenerateRequest = {
  sports: ["football", "basketball"],
  risk_profile: "balanced",
  target_odds_min: 2.0,
  target_odds_max: 5.0,
  min_legs: 2,
  max_legs: 4,
  min_leg_prob: 0.45,
  stake: 100.0,
  bookmaker_mode: "betclic_tax_free",
  only_plus_ev: false,
};

// =============================================================================
// 2. Negative Type Checks (Must fail type-checking; verified by @ts-expect-error)
// =============================================================================

// Negative 1: Invalid tax_multiplier (0.70 is not in 0.88 | 1)
export const invalidTaxMultiplier: GeneratedCoupon = {
  ...validCouponStandardTax,
  // @ts-expect-error: Type '0.7' is not assignable to type '0.88 | 1'
  tax_multiplier: 0.70,
};

// Negative 2: String tax_multiplier
export const invalidTaxMultiplierString: GeneratedCoupon = {
  ...validCouponStandardTax,
  // @ts-expect-error: Type 'string' is not assignable to type '0.88 | 1'
  tax_multiplier: "0.88",
};

// Negative 3: Invalid risk_tier
export const invalidRiskTier: GeneratedCoupon = {
  ...validCouponStandardTax,
  // @ts-expect-error: Type '"ultra_reckless"' is not assignable to type '"conservative" | "balanced" | "aggressive" | "max_value"'
  risk_tier: "ultra_reckless",
};

// Negative 4: Missing required property anti_correlation_passed
// @ts-expect-error: Property 'anti_correlation_passed' is missing in type
export const missingAntiCorrelation: GeneratedCoupon = {
  id: "slip_incomplete",
  title: "Incomplete",
  risk_tier: "conservative",
  selections: [],
  total_odds_gross: 2.0,
  tax_multiplier: 1,
  total_odds_net: 2.0,
  joint_probability: 0.5,
  stake: 100.0,
  potential_payout_gross: 200.0,
  potential_payout_net: 200.0,
  pit_10_applies: false,
  pit_10_deduction: 0.0,
  slip_ev_net: 0.0,
  kelly_stake_fraction: 0.02,
  kelly_recommended_stake_pln: 20.0,
};

// Negative 5: Invalid boolean type on pit_10_applies
export const invalidBooleanType: GeneratedCoupon = {
  ...validCouponStandardTax,
  // @ts-expect-error: Type 'string' is not assignable to type 'boolean'
  pit_10_applies: "false",
};

// Negative 6: Invalid bookmaker_mode on SlipEvaluateRequest
export const invalidBookmakerMode: SlipEvaluateRequest = {
  selections: [validLegInput],
  stake: 100.0,
  // @ts-expect-error: Type '"unlicensed_bookmaker"' is not assignable to type '"standard_088" | "betclic_tax_free" | "fortuna_promo" | "superbet_boost"'
  bookmaker_mode: "unlicensed_bookmaker",
};

// Negative 7: Missing required selections on SlipEvaluateRequest
// @ts-expect-error: Property 'selections' is missing in type
export const missingSelections: SlipEvaluateRequest = {
  stake: 100.0,
  bookmaker_mode: "standard_088",
};

// Negative 8: String instead of array on SlipGenerateRequest.sports
export const invalidSportsType: SlipGenerateRequest = {
  ...validGenerateRequestFull,
  // @ts-expect-error: Type 'string' is not assignable to type 'string[]'
  sports: "football",
};

// Negative 9: Invalid type for LegInput.odds_override
export const invalidOddsOverrideType: LegInput = {
  event_id: "ev_01",
  market_key: "1x2",
  outcome_key: "home",
  // @ts-expect-error: Type 'string' is not assignable to type 'number | null | undefined'
  odds_override: "high_odds",
};

// =============================================================================
// 3. Documented Type Discrepancies & Weaknesses
// =============================================================================

/**
 * WEAKNESS FINDING 1: SlipEvaluateResponse.tax_multiplier is typed as generic `number`.
 * Notice that unlike GeneratedCoupon (which rejects 0.70 with @ts-expect-error),
 * SlipEvaluateResponse ACCEPTS 0.70 without compile error!
 */
export const evaluateResponseLaxTaxMultiplier: SlipEvaluateResponse = {
  selections: [validSelection],
  total_odds_gross: 2.0,
  tax_multiplier: 0.70, // Compiles without error because type is `number` instead of `0.88 | 1`
  total_odds_net: 1.4,
  joint_probability: 0.5,
  stake: 100.0,
  potential_payout_gross: 200.0,
  potential_payout_net: 140.0,
  pit_10_applies: false,
  pit_10_deduction: 0.0,
  slip_ev_net: -0.05,
  kelly_stake_fraction: 0.0,
  is_correlated: false,
  validation_warnings: [],
};

/**
 * WEAKNESS FINDING 2: openapi-typescript generates `default` fields as required in TypeScript.
 * In openapi.yaml, SlipGenerateRequest only requires [sports, risk_profile, target_odds_min, target_odds_max].
 * However, because min_legs, max_legs, min_leg_prob, stake, bookmaker_mode, only_plus_ev have `default: ...`,
 * openapi-typescript generated them as non-optional in SlipGenerateRequest!
 * Therefore, passing a minimal payload without default fields triggers a TypeScript error:
 */
// @ts-expect-error: Properties with `default:` in openapi.yaml became mandatory in generated TS interface
export const minimalGenerateRequestFailsTS: SlipGenerateRequest = {
  sports: ["football"],
  risk_profile: "conservative",
  target_odds_min: 1.5,
  target_odds_max: 3.0,
};

console.log("Adversarial TypeScript type verification successfully compiled with 100% expected errors!");
