import type {
  BookmakerMode,
  CalibrationMetricsResponse,
  CandidateSelection,
  CategoriesResponse,
  EvaluatedSlip,
  EventBreakdownResponse,
  EventsQueryParams,
  EventsResponse,
  GeneratedSlipProposal,
  PreMatchEventItem,
  SavedSlipRecord,
  SaveSlipRequest,
  SlipEvaluateRequest,
  SlipGenerateParams,
  SlipGenerateResponse,
  SplitAdvice,
} from "./api";

export const FALLBACK_CATEGORIES: CategoriesResponse = {
  total: 4,
  categories: [
    {
      id: 1,
      slug: "football",
      name_pl: "Piłka nożna",
      is_enabled_v1: true,
      volatility_tier: "standard",
      active_model: "dixon_coles_xg_v1",
      fixtures_count: 2,
      updated_at: "2026-11-13T00:00:00Z",
    },
    {
      id: 2,
      slug: "basketball",
      name_pl: "Koszykówka",
      is_enabled_v1: true,
      volatility_tier: "standard",
      active_model: "pace_ortg_drtg_v1",
      fixtures_count: 1,
      updated_at: "2026-11-13T00:00:00Z",
    },
    {
      id: 3,
      slug: "tennis",
      name_pl: "Tenis",
      is_enabled_v1: true,
      volatility_tier: "standard",
      active_model: "markov_surface_elo_v1",
      fixtures_count: 2,
      updated_at: "2026-11-13T00:00:00Z",
    },
    {
      id: 4,
      slug: "hockey",
      name_pl: "Hokej",
      is_enabled_v1: true,
      volatility_tier: "standard",
      active_model: "skellam_emptynet_v1",
      fixtures_count: 1,
      updated_at: "2026-11-13T00:00:00Z",
    },
  ],
};

export const FALLBACK_EVENTS: PreMatchEventItem[] = [
  {
    id: "ev_fb_ars_che",
    sport_slug: "football",
    sport_name_pl: "Piłka nożna",
    league_id: 1,
    league_name: "Premier League",
    league_country: "England",
    home_team: "Arsenal FC",
    away_team: "Chelsea FC",
    start_time_utc: "2026-11-15T15:00:00Z",
    status: "pre_match",
    surface_or_format: "Grass",
    all_markets_count: 3,
    max_ev_net: 0.0482,
    is_value_bet: true,
    primary_market: {
      market_key: "1x2",
      market_label: "Wynik meczu (1X2)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.75,
          p_model: 0.608,
          p_sharp: 0.592,
          p_true: 0.599,
          fair_odds: 1.669,
          ev_standard_pl: -0.0775,
          ev_taxfree_pl: 0.0482,
          is_value_bet: true,
          kelly_fraction: 0.0161,
        },
        {
          outcome_key: "draw",
          outcome_label: "X (Remis)",
          best_bookmaker: "fortuna",
          odds_decimal: 3.65,
          p_model: 0.224,
          p_sharp: 0.238,
          p_true: 0.232,
          fair_odds: 4.31,
          ev_standard_pl: -0.255,
          ev_taxfree_pl: -0.1532,
          is_value_bet: false,
          kelly_fraction: 0,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "superbet",
          odds_decimal: 4.6,
          p_model: 0.168,
          p_sharp: 0.17,
          p_true: 0.169,
          fair_odds: 5.917,
          ev_standard_pl: -0.3162,
          ev_taxfree_pl: -0.2226,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
  {
    id: "ev_fb_rma_val",
    sport_slug: "football",
    sport_name_pl: "Piłka nożna",
    league_id: 2,
    league_name: "La Liga",
    league_country: "Spain",
    home_team: "Real Madrid",
    away_team: "Valencia CF",
    start_time_utc: "2026-11-15T20:00:00Z",
    status: "pre_match",
    surface_or_format: "Grass",
    all_markets_count: 3,
    max_ev_net: 0.0368,
    is_value_bet: true,
    primary_market: {
      market_key: "1x2",
      market_label: "Wynik meczu (1X2)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.38,
          p_model: 0.762,
          p_sharp: 0.743,
          p_true: 0.7513,
          fair_odds: 1.331,
          ev_standard_pl: -0.0876,
          ev_taxfree_pl: 0.0368,
          is_value_bet: true,
          kelly_fraction: 0.0242,
        },
        {
          outcome_key: "draw",
          outcome_label: "X (Remis)",
          best_bookmaker: "sts",
          odds_decimal: 4.9,
          p_model: 0.158,
          p_sharp: 0.169,
          p_true: 0.1641,
          fair_odds: 6.094,
          ev_standard_pl: -0.2925,
          ev_taxfree_pl: -0.1959,
          is_value_bet: false,
          kelly_fraction: 0,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "fortuna",
          odds_decimal: 8.2,
          p_model: 0.08,
          p_sharp: 0.088,
          p_true: 0.0846,
          fair_odds: 11.82,
          ev_standard_pl: -0.3897,
          ev_taxfree_pl: -0.3063,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
  {
    id: "ev_bb_bos_nyk",
    sport_slug: "basketball",
    sport_name_pl: "Koszykówka",
    league_id: 4,
    league_name: "NBA",
    league_country: "USA",
    home_team: "Boston Celtics",
    away_team: "New York Knicks",
    start_time_utc: "2026-11-16T00:30:00Z",
    status: "pre_match",
    surface_or_format: "Hardcourt",
    all_markets_count: 3,
    max_ev_net: 0.0542,
    is_value_bet: true,
    primary_market: {
      market_key: "moneyline",
      market_label: "Zwycięzca meczu (ML)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.48,
          p_model: 0.725,
          p_sharp: 0.704,
          p_true: 0.7123,
          fair_odds: 1.404,
          ev_standard_pl: -0.0721,
          ev_taxfree_pl: 0.0542,
          is_value_bet: true,
          kelly_fraction: 0.0282,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "superbet",
          odds_decimal: 2.75,
          p_model: 0.275,
          p_sharp: 0.296,
          p_true: 0.2877,
          fair_odds: 3.476,
          ev_standard_pl: -0.3038,
          ev_taxfree_pl: -0.2088,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
  {
    id: "ev_ten_alc_sin",
    sport_slug: "tennis",
    sport_name_pl: "Tenis",
    league_id: 6,
    league_name: "ATP Finals",
    league_country: "International",
    home_team: "Carlos Alcaraz",
    away_team: "Jannik Sinner",
    start_time_utc: "2026-11-16T13:00:00Z",
    status: "pre_match",
    surface_or_format: "Clay",
    all_markets_count: 2,
    max_ev_net: 0.0621,
    is_value_bet: true,
    primary_market: {
      market_key: "moneyline",
      market_label: "Zwycięzca meczu (ML)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.92,
          p_model: 0.568,
          p_sharp: 0.543,
          p_true: 0.5532,
          fair_odds: 1.808,
          ev_standard_pl: -0.0653,
          ev_taxfree_pl: 0.0621,
          is_value_bet: true,
          kelly_fraction: 0.0169,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "fortuna",
          odds_decimal: 1.95,
          p_model: 0.432,
          p_sharp: 0.457,
          p_true: 0.4468,
          fair_odds: 2.238,
          ev_standard_pl: -0.2335,
          ev_taxfree_pl: -0.1287,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
  {
    id: "ev_ten_swi_sab",
    sport_slug: "tennis",
    sport_name_pl: "Tenis",
    league_id: 7,
    league_name: "WTA Tour Finals",
    league_country: "International",
    home_team: "Iga Świątek",
    away_team: "Aryna Sabalenka",
    start_time_utc: "2026-11-16T16:00:00Z",
    status: "pre_match",
    surface_or_format: "Hard",
    all_markets_count: 2,
    max_ev_net: 0.0419,
    is_value_bet: true,
    primary_market: {
      market_key: "moneyline",
      market_label: "Zwycięzca meczu (ML)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.68,
          p_model: 0.631,
          p_sharp: 0.613,
          p_true: 0.6202,
          fair_odds: 1.612,
          ev_standard_pl: -0.082,
          ev_taxfree_pl: 0.0419,
          is_value_bet: true,
          kelly_fraction: 0.0154,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "superbet",
          odds_decimal: 2.25,
          p_model: 0.369,
          p_sharp: 0.387,
          p_true: 0.3798,
          fair_odds: 2.633,
          ev_standard_pl: -0.248,
          ev_taxfree_pl: -0.1455,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
  {
    id: "ev_hk_edm_cgy",
    sport_slug: "hockey",
    sport_name_pl: "Hokej",
    league_id: 8,
    league_name: "NHL",
    league_country: "USA/Canada",
    home_team: "Edmonton Oilers",
    away_team: "Calgary Flames",
    start_time_utc: "2026-11-17T02:00:00Z",
    status: "pre_match",
    surface_or_format: "Ice",
    all_markets_count: 3,
    max_ev_net: 0.0451,
    is_value_bet: true,
    primary_market: {
      market_key: "1x2",
      market_label: "Wynik meczu 60 min (1X2)",
      outcomes: [
        {
          outcome_key: "home",
          outcome_label: "1 (Gospodarz)",
          best_bookmaker: "betclic",
          odds_decimal: 1.88,
          p_model: 0.569,
          p_sharp: 0.547,
          p_true: 0.5559,
          fair_odds: 1.799,
          ev_standard_pl: -0.0803,
          ev_taxfree_pl: 0.0451,
          is_value_bet: true,
          kelly_fraction: 0.0128,
        },
        {
          outcome_key: "draw",
          outcome_label: "X (Remis 60m)",
          best_bookmaker: "fortuna",
          odds_decimal: 4.2,
          p_model: 0.212,
          p_sharp: 0.219,
          p_true: 0.2162,
          fair_odds: 4.625,
          ev_standard_pl: -0.2009,
          ev_taxfree_pl: -0.092,
          is_value_bet: false,
          kelly_fraction: 0,
        },
        {
          outcome_key: "away",
          outcome_label: "2 (Gość)",
          best_bookmaker: "sts",
          odds_decimal: 3.45,
          p_model: 0.219,
          p_sharp: 0.234,
          p_true: 0.2279,
          fair_odds: 4.388,
          ev_standard_pl: -0.308,
          ev_taxfree_pl: -0.2137,
          is_value_bet: false,
          kelly_fraction: 0,
        },
      ],
    },
  },
];

export function filterFallbackEvents(params?: EventsQueryParams): EventsResponse {
  let filtered = [...FALLBACK_EVENTS];
  if (params?.sport) {
    filtered = filtered.filter((e) => e.sport_slug === params.sport);
  }
  if (params?.league_id !== undefined) {
    filtered = filtered.filter((e) => e.league_id === params.league_id);
  }
  if (params?.min_ev !== undefined) {
    filtered = filtered.filter((e) => e.max_ev_net >= (params.min_ev ?? -999));
  }
  const offset = params?.offset ?? 0;
  const limit = params?.limit ?? 50;
  return {
    events: filtered.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

export function buildFallbackBreakdown(eventId: string): EventBreakdownResponse {
  const ev = FALLBACK_EVENTS.find((e) => e.id === eventId) || FALLBACK_EVENTS[0];
  const isFootball = ev.sport_slug === "football";
  return {
    event_id: ev.id,
    sport: ev.sport_slug,
    league_name: ev.league_name,
    home_team: ev.home_team,
    away_team: ev.away_team,
    start_time_utc: ev.start_time_utc,
    status: ev.status,
    model_name:
      ev.sport_slug === "football"
        ? "dixon_coles_xg_v1"
        : ev.sport_slug === "basketball"
        ? "pace_ortg_drtg_v1"
        : ev.sport_slug === "tennis"
        ? "markov_surface_elo_v1"
        : "skellam_emptynet_v1",
    model_version:
      ev.sport_slug === "football"
        ? "dixon_coles_xg_v1"
        : ev.sport_slug === "basketball"
        ? "pace_ortg_drtg_v1"
        : ev.sport_slug === "tennis"
        ? "markov_surface_elo_v1"
        : "skellam_emptynet_v1",
    bayesian_fusion: {
      model_weight: isFootball ? 0.45 : 0.4,
      sharp_weight: isFootball ? 0.55 : 0.6,
      sharp_bookmaker: "pinnacle",
    },
    competitor_ratings: {
      home: {
        competitor_id: `${ev.id}_home`,
        rating_elo: 1865,
        surface_elo: 1890,
        xg_attack: 1.94,
        xg_defense: 0.88,
        pace: 99.4,
        ortg: 118.2,
        drtg: 109.5,
        serve_win_pct: 0.678,
        return_win_pct: 0.412,
      },
      away: {
        competitor_id: `${ev.id}_away`,
        rating_elo: 1742,
        surface_elo: 1755,
        xg_attack: 1.42,
        xg_defense: 1.21,
        pace: 97.1,
        ortg: 113.8,
        drtg: 112.4,
        serve_win_pct: 0.654,
        return_win_pct: 0.384,
      },
    },
    factual_factors: [
      {
        label: "Model bazowy",
        value:
          ev.sport_slug === "football"
            ? "Dixon-Coles Bivariate Poisson (70% xG)"
            : ev.sport_slug === "basketball"
            ? "Pace × ORtg/DRtg Gaussian"
            : ev.sport_slug === "tennis"
            ? "Hierarchical Markov Chain + Surface Elo"
            : "Skellam 60m + Empty Net Pull",
        impact: "neutral",
      },
      {
        label: "Różnica Elo",
        value: "+123 pkt",
        impact: "positive",
      },
      {
        label: "De-vigging rynku",
        value: "Shin (Pinnacle benchmark)",
        impact: "positive",
      },
    ],
    sport_breakdown: {
      lambda_home: 1.88,
      lambda_away: 1.04,
      expected_total: 2.92,
      surface_or_format: ev.surface_or_format || "Standard",
    },
    available_markets: [ev.primary_market],
  };
}

function resolveTaxMultiplier(mode: BookmakerMode, legOdds: number[]): number {
  if (mode === "standard_088") return 0.88;
  if (mode === "betclic_tax_free") {
    return legOdds.length >= 2 && legOdds.every((o) => o >= 1.2) ? 1.0 : 0.88;
  }
  if (mode === "fortuna_promo") {
    return legOdds.length >= 3 && legOdds.every((o) => o >= 1.3) ? 1.0 : 0.88;
  }
  if (mode === "superbet_boost") {
    return legOdds.length >= 3 && legOdds.every((o) => o >= 1.25) ? 1.0 : 0.88;
  }
  return 0.88;
}

export function evaluateSlipFallback(payload: SlipEvaluateRequest): EvaluatedSlip {
  const selections: CandidateSelection[] = payload.selections.map((leg) => {
    const ev =
      FALLBACK_EVENTS.find((e) => e.id === leg.event_id) || FALLBACK_EVENTS[0];
    const out =
      ev.primary_market.outcomes.find((o) => o.outcome_key === leg.outcome_key) ||
      ev.primary_market.outcomes[0];
    const oddsGross =
      leg.odds_override !== undefined ? Number(leg.odds_override) : out.odds_decimal;
    return {
      event_id: ev.id,
      event_name: `${ev.home_team} vs ${ev.away_team}`,
      sport: ev.sport_slug,
      league_name: ev.league_name,
      start_time_utc: ev.start_time_utc,
      market_key: leg.market_key || ev.primary_market.market_key,
      market_label: ev.primary_market.market_label,
      outcome_key: out.outcome_key,
      outcome_label: out.outcome_label,
      bookmaker_key: leg.bookmaker_key || out.best_bookmaker,
      odds_gross: Number(oddsGross.toFixed(2)),
      p_model: out.p_model,
      p_sharp: out.p_sharp,
      p_true: out.p_true,
      ev_net: Number((out.p_true * oddsGross - 1).toFixed(4)),
      applied_tax_multiplier: 1.0,
    };
  });

  const legOdds = selections.map((s) => s.odds_gross);
  const totalOddsGross = Number(
    legOdds.reduce((acc, v) => acc * v, 1).toFixed(2)
  );
  const taxMultiplier = resolveTaxMultiplier(payload.bookmaker_mode, legOdds);
  const totalOddsNet = Number((totalOddsGross * taxMultiplier).toFixed(4));
  const jointProb = Number(
    selections.reduce((acc, s) => acc * s.p_true, 1).toFixed(4)
  );
  const stake = Number(payload.stake);
  const payoutGross = Number((stake * totalOddsNet).toFixed(2));
  const pitApplies = payoutGross > 2280.0;
  const pitDeduction = pitApplies ? Number((payoutGross * 0.1).toFixed(2)) : 0.0;
  const payoutNet = Number((payoutGross - pitDeduction).toFixed(2));

  let splitAdvice: SplitAdvice | null = null;
  if (pitApplies) {
    const tickets = Math.max(2, Math.ceil(payoutGross / 2250));
    const stakePerTicket = Number((stake / tickets).toFixed(2));
    const payoutPerTicket = Number((payoutGross / tickets).toFixed(2));
    splitAdvice = {
      recommended: true,
      original_gross_payout: payoutGross,
      original_tax_deduction: pitDeduction,
      split_tickets_count: tickets,
      stake_per_ticket: stakePerTicket,
      payout_per_ticket: payoutPerTicket,
      net_tax_saved: pitDeduction,
      advice_text: `Podziel stawkę ${stake.toFixed(2)} PLN na ${tickets} kupony po ${stakePerTicket.toFixed(
        2
      )} PLN (wygrana ${payoutPerTicket.toFixed(
        2
      )} PLN na kupon ≤ 2280 PLN), aby legalnie uniknąć 10% podatku PIT (${pitDeduction.toFixed(
        2
      )} PLN).`,
    };
  }

  const effectiveMultiplier = payoutNet / Math.max(stake, 0.01);
  const slipEvNet = Number((jointProb * effectiveMultiplier - 1).toFixed(4));
  const b = Math.max(effectiveMultiplier - 1, 0.0001);
  const rawKelly = (jointProb * (b + 1) - 1) / b;
  const kellyFraction = Number(
    Math.max(0, Math.min(0.05, rawKelly * 0.25)).toFixed(4)
  );

  return {
    selections: selections.map((s) => ({
      ...s,
      applied_tax_multiplier: taxMultiplier,
    })),
    total_odds_gross: totalOddsGross,
    tax_multiplier: taxMultiplier,
    total_odds_net: totalOddsNet,
    joint_probability: jointProb,
    stake,
    potential_payout_gross: payoutGross,
    potential_payout_net: payoutNet,
    pit_10_applies: pitApplies,
    pit_10_deduction: pitDeduction,
    pit_warning: pitApplies
      ? `Wygrana przekracza 2280 PLN — naliczono 10% podatku PIT (-${pitDeduction.toFixed(
          2
        )} PLN).`
      : null,
    slip_ev_net: slipEvNet,
    kelly_stake_fraction: kellyFraction,
    kelly_recommended_stake_pln: Number((kellyFraction * 1000).toFixed(2)),
    tax_savings_advice: splitAdvice,
    is_correlated: false,
    anti_correlation_passed: true,
    validation_warnings: [],
  };
}

export function generateSlipsFallback(
  params: SlipGenerateParams
): SlipGenerateResponse {
  const allowedEvents = FALLBACK_EVENTS.filter((e) =>
    params.sports.includes(e.sport_slug)
  );
  const pool = allowedEvents.length >= 2 ? allowedEvents : FALLBACK_EVENTS;
  const count = Math.min(Math.max(params.min_legs, 2), Math.min(params.max_legs, pool.length));
  const chosen = pool.slice(0, count);

  const evalRes = evaluateSlipFallback({
    selections: chosen.map((e) => ({
      event_id: e.id,
      market_key: e.primary_market.market_key,
      outcome_key: e.primary_market.outcomes[0].outcome_key,
      bookmaker_key: e.primary_market.outcomes[0].best_bookmaker,
    })),
    stake: params.stake,
    bookmaker_mode: params.bookmaker_mode,
  });

  const proposal: GeneratedSlipProposal = {
    ...evalRes,
    id: "prop_quant_optimal_1",
    title: "Kupon Optymalny Beam-Search #1 (Max P)",
    risk_tier: params.risk_profile,
  };

  return {
    coupons: [proposal],
    candidate_pool_size: pool.length * 3,
    solver_algorithm: "beam_search_max_p_joint",
    execution_time_ms: 4.2,
  };
}

let fallbackSavedSlipsStore: SavedSlipRecord[] = [
  {
    id: "slip_betclic_zero_tax",
    user_id: "usr_compliant_adult",
    name: "Kupon Betclic Bez Podatku (AKO 2)",
    bookmaker_key: "betclic",
    tax_multiplier: 1.0,
    total_odds_gross: 2.59,
    total_odds_net: 2.59,
    stake: 100,
    potential_payout_gross: 259,
    potential_payout_net: 259,
    joint_probability: 0.4267,
    slip_ev_net: 0.1051,
    recommended_kelly_stake_pct: 0.0165,
    pit_10_applies: false,
    created_at: "2026-11-12T18:00:00Z",
    selections: [
      {
        event_id: "ev_fb_ars_che",
        event_name: "Arsenal FC vs Chelsea FC",
        sport: "football",
        league_name: "Premier League",
        start_time_utc: "2026-11-15T15:00:00Z",
        market_key: "1x2",
        market_label: "Wynik meczu (1X2)",
        outcome_key: "home",
        outcome_label: "1 (Gospodarz)",
        bookmaker_key: "betclic",
        odds_gross: 1.75,
        p_model: 0.608,
        p_sharp: 0.592,
        p_true: 0.599,
        ev_net: 0.0482,
        applied_tax_multiplier: 1.0,
      },
      {
        event_id: "ev_bb_bos_nyk",
        event_name: "Boston Celtics vs New York Knicks",
        sport: "basketball",
        league_name: "NBA",
        start_time_utc: "2026-11-16T00:30:00Z",
        market_key: "moneyline",
        market_label: "Zwycięzca meczu (ML)",
        outcome_key: "home",
        outcome_label: "1 (Gospodarz)",
        bookmaker_key: "betclic",
        odds_gross: 1.48,
        p_model: 0.725,
        p_sharp: 0.704,
        p_true: 0.7123,
        ev_net: 0.0542,
        applied_tax_multiplier: 1.0,
      },
    ],
  },
];

export function listFallbackSavedSlips(): { items: SavedSlipRecord[]; total: number } {
  return {
    items: [...fallbackSavedSlipsStore],
    total: fallbackSavedSlipsStore.length,
  };
}

export function saveFallbackSlip(payload: SaveSlipRequest): { slip: SavedSlipRecord } {
  const evaluated = evaluateSlipFallback({
    selections: payload.selections,
    stake: payload.stake,
    bookmaker_mode: payload.bookmaker_mode,
  });
  const record: SavedSlipRecord = {
    id: `slip_${Date.now()}`,
    user_id: "usr_compliant_adult",
    name: payload.name || "Kupon LeadBet",
    selections: evaluated.selections,
    bookmaker_key: payload.bookmaker_key || "betclic",
    tax_multiplier: evaluated.tax_multiplier,
    total_odds_gross: evaluated.total_odds_gross,
    total_odds_net: evaluated.total_odds_net,
    stake: evaluated.stake,
    potential_payout_gross: evaluated.potential_payout_gross,
    potential_payout_net: evaluated.potential_payout_net,
    joint_probability: evaluated.joint_probability,
    slip_ev_net: evaluated.slip_ev_net,
    recommended_kelly_stake_pct: evaluated.kelly_stake_fraction,
    pit_10_applies: evaluated.pit_10_applies,
    created_at: new Date().toISOString(),
  };
  fallbackSavedSlipsStore = [record, ...fallbackSavedSlipsStore];
  return { slip: record };
}

export function deleteFallbackSavedSlip(slipId: string): void {
  fallbackSavedSlipsStore = fallbackSavedSlipsStore.filter((s) => s.id !== slipId);
}

export const FALLBACK_CALIBRATION: CalibrationMetricsResponse = {
  time_horizon: "90d",
  overall: {
    sample_size: 420,
    brier_score: 0.1842,
    brier_skill_score: 0.1425,
    log_loss: 0.5481,
    clv_beat_rate: 0.6429,
    avg_clv_percentage: 0.0284,
  },
  by_sport: [
    {
      sport: "football",
      sport_name_pl: "Piłka nożna",
      model_name: "dixon_coles_xg_v1",
      sample_size: 160,
      brier_score: 0.1815,
      log_loss: 0.541,
      clv_beat_rate: 0.6563,
      avg_clv_percentage: 0.0312,
    },
    {
      sport: "basketball",
      sport_name_pl: "Koszykówka",
      model_name: "pace_ortg_drtg_v1",
      sample_size: 110,
      brier_score: 0.1864,
      log_loss: 0.552,
      clv_beat_rate: 0.6364,
      avg_clv_percentage: 0.0268,
    },
    {
      sport: "tennis",
      sport_name_pl: "Tenis ziemny",
      model_name: "markov_surface_elo_v1",
      sample_size: 90,
      brier_score: 0.1798,
      log_loss: 0.539,
      clv_beat_rate: 0.6556,
      avg_clv_percentage: 0.0295,
    },
    {
      sport: "hockey",
      sport_name_pl: "Hokej na lodzie",
      model_name: "skellam_emptynet_v1",
      sample_size: 60,
      brier_score: 0.1935,
      log_loss: 0.569,
      clv_beat_rate: 0.6,
      avg_clv_percentage: 0.0219,
    },
  ],
  reliability_bins: [
    {
      bin_index: 1,
      predicted_prob_lower: 0.1,
      predicted_prob_upper: 0.2,
      mean_predicted_prob: 0.158,
      empirical_win_rate: 0.152,
      sample_count: 28,
      brier_contribution: 0.0112,
    },
    {
      bin_index: 2,
      predicted_prob_lower: 0.2,
      predicted_prob_upper: 0.3,
      mean_predicted_prob: 0.254,
      empirical_win_rate: 0.261,
      sample_count: 46,
      brier_contribution: 0.0214,
    },
    {
      bin_index: 3,
      predicted_prob_lower: 0.3,
      predicted_prob_upper: 0.4,
      mean_predicted_prob: 0.352,
      empirical_win_rate: 0.344,
      sample_count: 58,
      brier_contribution: 0.031,
    },
    {
      bin_index: 4,
      predicted_prob_lower: 0.4,
      predicted_prob_upper: 0.5,
      mean_predicted_prob: 0.456,
      empirical_win_rate: 0.463,
      sample_count: 74,
      brier_contribution: 0.0392,
    },
    {
      bin_index: 5,
      predicted_prob_lower: 0.5,
      predicted_prob_upper: 0.6,
      mean_predicted_prob: 0.551,
      empirical_win_rate: 0.548,
      sample_count: 86,
      brier_contribution: 0.0378,
    },
    {
      bin_index: 6,
      predicted_prob_lower: 0.6,
      predicted_prob_upper: 0.7,
      mean_predicted_prob: 0.648,
      empirical_win_rate: 0.659,
      sample_count: 72,
      brier_contribution: 0.0265,
    },
    {
      bin_index: 7,
      predicted_prob_lower: 0.7,
      predicted_prob_upper: 0.85,
      mean_predicted_prob: 0.754,
      empirical_win_rate: 0.768,
      sample_count: 56,
      brier_contribution: 0.0171,
    },
  ],
  last_calculated_at: "2026-11-13T00:00:00Z",
};
