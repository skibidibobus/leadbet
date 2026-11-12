/**
 * @quantkupon/contracts
 * Authoritative TypeScript interfaces and convenience schema aliases generated from OpenAPI 3.1.
 */

export * from './types';
import type { components, paths } from './types';

// API paths and operations
export type ApiPaths = paths;

// Schemas & DTOs
export type SportCategory = components['schemas']['SportCategory'];
export type CategoryListResponse = components['schemas']['CategoryListResponse'];

export type EventSummary = components['schemas']['EventSummary'];
export type EventListResponse = components['schemas']['EventListResponse'];
export type MarketSummary = components['schemas']['MarketSummary'];
export type MarketOutcome = components['schemas']['MarketOutcome'];

export type EventBreakdownResponse = components['schemas']['EventBreakdownResponse'];
export type BayesianFusionSummary = components['schemas']['BayesianFusionSummary'];
export type FootballBreakdown = components['schemas']['FootballBreakdown'];
export type BasketballBreakdown = components['schemas']['BasketballBreakdown'];
export type TennisBreakdown = components['schemas']['TennisBreakdown'];
export type HockeyBreakdown = components['schemas']['HockeyBreakdown'];
export type FactualFactor = components['schemas']['FactualFactor'];
export type CompetitorRatingsSummary = components['schemas']['CompetitorRatingsSummary'];
export type MarketPredictionDetail = components['schemas']['MarketPredictionDetail'];
export type OutcomePredictionDetail = components['schemas']['OutcomePredictionDetail'];
export type BookmakerOddsItem = components['schemas']['BookmakerOddsItem'];

export type SlipGenerateRequest = components['schemas']['SlipGenerateRequest'];
export type SlipGenerateResponse = components['schemas']['SlipGenerateResponse'];
export type GeneratedCoupon = components['schemas']['GeneratedCoupon'];
export type CouponSelection = components['schemas']['CouponSelection'];
export type SplitAdvice = components['schemas']['SplitAdvice'];

export type SlipEvaluateRequest = components['schemas']['SlipEvaluateRequest'];
export type SlipEvaluateResponse = components['schemas']['SlipEvaluateResponse'];
export type LegInput = components['schemas']['LegInput'];

export type SaveSlipRequest = components['schemas']['SaveSlipRequest'];
export type SavedSlip = components['schemas']['SavedSlip'];
export type SavedSlipResponse = components['schemas']['SavedSlipResponse'];
export type SavedSlipListResponse = components['schemas']['SavedSlipListResponse'];

export type CalibrationMetricsResponse = components['schemas']['CalibrationMetricsResponse'];
export type CalibrationMetricsSummary = components['schemas']['CalibrationMetricsSummary'];
export type SportCalibrationMetrics = components['schemas']['SportCalibrationMetrics'];
export type CalibrationBin = components['schemas']['CalibrationBin'];

export type ErrorResponse = components['schemas']['ErrorResponse'];
export type ValidationErrorDetail = components['schemas']['ValidationErrorDetail'];
export type StandardSuccessResponse = components['schemas']['StandardSuccessResponse'];
