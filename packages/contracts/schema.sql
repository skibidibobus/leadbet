-- ============================================================================
-- QUANTKUPON Database Schema
-- Target: Neon PostgreSQL (PostgreSQL 15+)
-- Contract File: packages/contracts/schema.sql
-- Description: Complete idempotent DDL schema covering authentication,
--              sports dictionary, fixtures, ratings, odds snapshots,
--              probabilistic model predictions, and persisted user betting slips.
-- ============================================================================

-- Ensure required cryptographic extensions for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PART 1: AUTH.JS (NEXTAUTH V5) IDENTITY & STATUTORY LEGAL COMPLIANCE
-- ============================================================================

-- 1. users: Core user accounts with mandatory 18+ age and GDPR/RODO consents
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified TIMESTAMPTZ,
    image TEXT,
    accepted_terms_18_plus_at TIMESTAMPTZ NOT NULL,
    accepted_rodo_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. accounts: OAuth provider credentials (e.g. Google OAuth)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    expires_at BIGINT,
    token_type VARCHAR(50),
    scope TEXT,
    id_token TEXT,
    session_state TEXT,
    CONSTRAINT uq_accounts_provider_account UNIQUE (provider, provider_account_id)
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts (user_id);

-- 3. sessions: Web session tokens
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);

-- 4. verification_tokens: Magic links and email verification
CREATE TABLE IF NOT EXISTS verification_tokens (
    identifier VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (identifier, token)
);

-- ============================================================================
-- PART 2: SPORTS REFERENCE DICTIONARY & COMPETITIONS
-- ============================================================================

-- 5. sports_categories: Supported disciplines, activation status, and models
CREATE TABLE IF NOT EXISTS sports_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name_pl VARCHAR(100) NOT NULL,
    is_enabled_v1 BOOLEAN NOT NULL DEFAULT true,
    volatility_tier VARCHAR(20) NOT NULL DEFAULT 'standard',
    active_model VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_sports_volatility CHECK (volatility_tier IN ('low', 'standard', 'high'))
);

-- 6. leagues: Competitions within sports categories
CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    sport_id INTEGER NOT NULL REFERENCES sports_categories(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    country VARCHAR(50),
    tier_weight NUMERIC(4,2) NOT NULL DEFAULT 1.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_leagues_tier_weight CHECK (tier_weight > 0)
);

CREATE INDEX IF NOT EXISTS idx_leagues_sport_id ON leagues (sport_id);

-- ============================================================================
-- PART 3: FIXTURES & COMPETITOR STATISTICAL RATINGS
-- ============================================================================

-- 7. events: Individual sporting match fixtures
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(64) PRIMARY KEY,
    league_id INTEGER NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    home_competitor_id VARCHAR(64) NOT NULL,
    away_competitor_id VARCHAR(64) NOT NULL,
    home_team_name VARCHAR(150) NOT NULL,
    away_team_name VARCHAR(150) NOT NULL,
    start_time_utc TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pre_match',
    surface_or_format VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_events_status CHECK (status IN ('pre_match', 'live', 'finished', 'cancelled', 'postponed'))
);

CREATE INDEX IF NOT EXISTS idx_events_start_status ON events (start_time_utc, status);
CREATE INDEX IF NOT EXISTS idx_events_league_id ON events (league_id);

-- 8. competitor_ratings: Team/Player Elo, Glicko-2, xG, and sport metrics
CREATE TABLE IF NOT EXISTS competitor_ratings (
    competitor_id VARCHAR(64) PRIMARY KEY,
    sport_id INTEGER NOT NULL REFERENCES sports_categories(id) ON DELETE CASCADE,
    competitor_name VARCHAR(150) NOT NULL,
    rating_elo NUMERIC(7,2),
    glicko_r NUMERIC(7,2),
    glicko_rd NUMERIC(7,2),
    glicko_sigma NUMERIC(7,5),
    xg_attack NUMERIC(5,3),
    xg_defense NUMERIC(5,3),
    pace NUMERIC(5,2),
    ortg NUMERIC(6,2),
    drtg NUMERIC(6,2),
    serve_win_pct NUMERIC(5,4),
    return_win_pct NUMERIC(5,4),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_competitor_ratings_sport ON competitor_ratings (sport_id);

-- ============================================================================
-- PART 4: MARKET ODDS SNAPSHOTS & QUANTITATIVE PREDICTIONS
-- ============================================================================

-- 9. odds_snapshots: Time-series market odds from retail & sharp bookmakers
CREATE TABLE IF NOT EXISTS odds_snapshots (
    id BIGSERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_id VARCHAR(64) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    bookmaker_key VARCHAR(50) NOT NULL,
    market_key VARCHAR(50) NOT NULL,
    outcome_key VARCHAR(50) NOT NULL,
    odds_decimal NUMERIC(7,3) NOT NULL,
    is_sharp_benchmark BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT chk_odds_decimal_positive CHECK (odds_decimal > 1.000)
);

CREATE INDEX IF NOT EXISTS idx_odds_lookup ON odds_snapshots (event_id, market_key, outcome_key, time DESC);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_time ON odds_snapshots (time);

-- 10. model_predictions: Mathematical model outputs, de-vigged fair probabilities, Polish tax EV & Kelly
CREATE TABLE IF NOT EXISTS model_predictions (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    market_key VARCHAR(50) NOT NULL,
    outcome_key VARCHAR(50) NOT NULL,
    p_model NUMERIC(6,5) NOT NULL CHECK (p_model >= 0 AND p_model <= 1),
    p_sharp_devigged NUMERIC(6,5) NOT NULL CHECK (p_sharp_devigged >= 0 AND p_sharp_devigged <= 1),
    p_true NUMERIC(6,5) NOT NULL CHECK (p_true >= 0 AND p_true <= 1),
    fair_odds NUMERIC(7,3) NOT NULL CHECK (fair_odds >= 1.000),
    estimated_pl_odds NUMERIC(7,3) NOT NULL CHECK (estimated_pl_odds >= 1.000),
    ev_standard_pl NUMERIC(6,4) NOT NULL,
    ev_taxfree_pl NUMERIC(6,4) NOT NULL,
    kelly_quarter NUMERIC(5,4) NOT NULL CHECK (kelly_quarter >= 0 AND kelly_quarter <= 0.0500),
    model_version VARCHAR(30) NOT NULL,
    factual_factors_json JSONB NOT NULL DEFAULT '{}',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_model_predictions_event_mkt_out_ver UNIQUE (event_id, market_key, outcome_key, model_version)
);

CREATE INDEX IF NOT EXISTS idx_model_predictions_ev_std ON model_predictions (ev_standard_pl DESC);
CREATE INDEX IF NOT EXISTS idx_model_predictions_ev_taxfree ON model_predictions (ev_taxfree_pl DESC);

-- ============================================================================
-- PART 5: USER PERSISTED SLIPS & MATHEMATICAL COUPON ENGINE
-- ============================================================================

-- 11. saved_slips: User coupon history, live odds overrides, tax & PIT calculations
CREATE TABLE IF NOT EXISTS saved_slips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL DEFAULT 'Kupon',
    selections_json JSONB NOT NULL,
    user_profile_params_json JSONB NOT NULL,
    custom_pl_odds_overrides_json JSONB NOT NULL DEFAULT '{}',
    bookmaker_key VARCHAR(50) NOT NULL,
    tax_multiplier NUMERIC(4,2) NOT NULL,
    total_odds_gross NUMERIC(8,3) NOT NULL CHECK (total_odds_gross >= 1.000),
    total_odds_net NUMERIC(8,3) NOT NULL CHECK (total_odds_net >= 1.000),
    stake NUMERIC(10,2) NOT NULL DEFAULT 100.00 CHECK (stake > 0),
    potential_payout_gross NUMERIC(10,2) NOT NULL CHECK (potential_payout_gross >= 0),
    potential_payout_net NUMERIC(10,2) NOT NULL CHECK (potential_payout_net >= 0),
    joint_probability NUMERIC(6,5) NOT NULL CHECK (joint_probability >= 0 AND joint_probability <= 1),
    slip_ev_net NUMERIC(6,4) NOT NULL,
    recommended_kelly_stake_pct NUMERIC(5,4) NOT NULL CHECK (recommended_kelly_stake_pct >= 0 AND recommended_kelly_stake_pct <= 0.0500),
    pit_10_applies BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_slips_user_id ON saved_slips (user_id, created_at DESC);

-- ============================================================================
-- SEED DATA: INITIAL SPORTS DICTIONARY & PRIMARY LEAGUES
-- ============================================================================

INSERT INTO sports_categories (slug, name_pl, is_enabled_v1, volatility_tier, active_model)
VALUES
    ('football', 'Piłka nożna', true, 'standard', 'dixon_coles_xg'),
    ('basketball', 'Koszykówka', true, 'standard', 'pace_possession'),
    ('tennis', 'Tenis ziemny', true, 'standard', 'surface_markov'),
    ('hockey', 'Hokej na lodzie', true, 'standard', 'skellam_empty_net'),
    ('volleyball', 'Siatkówka', false, 'standard', 'hierarchical_markov'),
    ('table_tennis', 'Tenis stołowy', false, 'high', 'glicko2_volatility_guard')
ON CONFLICT (slug) DO UPDATE SET
    name_pl = EXCLUDED.name_pl,
    is_enabled_v1 = EXCLUDED.is_enabled_v1,
    volatility_tier = EXCLUDED.volatility_tier,
    active_model = EXCLUDED.active_model;

-- Seed primary reference leagues for active v1 and phase 2 sports
INSERT INTO leagues (sport_id, name, country, tier_weight)
SELECT s.id, l.name, l.country, l.tier_weight
FROM (VALUES
    ('football', 'Premier League', 'Anglia', 1.20),
    ('football', 'La Liga', 'Hiszpania', 1.15),
    ('football', 'Ekstraklasa', 'Polska', 1.00),
    ('football', 'Champions League', 'Międzynarodowe', 1.25),
    ('basketball', 'NBA', 'USA', 1.20),
    ('basketball', 'EuroLeague', 'Międzynarodowe', 1.10),
    ('tennis', 'ATP Tour', 'Międzynarodowe', 1.15),
    ('tennis', 'WTA Tour', 'Międzynarodowe', 1.10),
    ('hockey', 'NHL', 'USA/Kanada', 1.20),
    ('volleyball', 'PlusLiga', 'Polska', 1.00),
    ('table_tennis', 'TT Elite Series', 'Międzynarodowe', 0.85)
) AS l(sport_slug, name, country, tier_weight)
JOIN sports_categories s ON s.slug = l.sport_slug
WHERE NOT EXISTS (
    SELECT 1 FROM leagues existing 
    WHERE existing.sport_id = s.id AND existing.name = l.name
);
