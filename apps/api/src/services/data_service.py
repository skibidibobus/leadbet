"""Quant data orchestration service bridging adapters, sport models, optimizer, and API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bookmaker_adapters.feeds import SnapshotFixtureAdapter
from bookmaker_adapters.tax import BookmakerMode, PolishTaxEngine
from quant_engine.core.bayesian import fuse_market_probabilities
from quant_engine.core.calibration import evaluate_calibration
from quant_engine.core.devig import devig_shin
from quant_engine.core.kelly import calculate_kelly_fraction_pl
from quant_engine.optimizer import (
    CandidateSelection,
    SlipGenerateParams,
    SlipOptimizer,
)
from quant_engine.sports.base import CompetitorInput, MatchContext, SportPredictionResult
from quant_engine.sports.basketball import BasketballModel
from quant_engine.sports.football import FootballModel
from quant_engine.sports.hockey import HockeyModel
from quant_engine.sports.tennis import TennisModel


SPORT_MODELS = {
    "football": FootballModel,
    "basketball": BasketballModel,
    "tennis": TennisModel,
    "hockey": HockeyModel,
}

MARKET_LABELS_PL: Dict[str, str] = {
    "1x2": "Wynik meczu (1X2)",
    "totals_2_5": "Liczba goli (O/U 2.5)",
    "btts": "Obie drużyny strzelą (BTTS)",
    "moneyline": "Zwycięzca meczu (ML)",
    "spread": "Handicap punktowy (Spread)",
    "totals": "Suma punktów / bramek",
    "totals_5_5": "Liczba bramek (O/U 5.5)",
    "set_handicap": "Handicap setowy",
}

OUTCOME_LABELS_PL: Dict[str, str] = {
    "home": "1 (Gospodarz)",
    "draw": "X (Remis)",
    "away": "2 (Gość)",
    "over": "Powyżej",
    "under": "Poniżej",
    "yes": "Tak",
    "no": "Nie",
}


class QuantDataService:
    """In-memory / fixture-backed service implementing all QUANTKUPON API use cases."""

    def __init__(self, adapter: Optional[SnapshotFixtureAdapter] = None) -> None:
        self.adapter = adapter or SnapshotFixtureAdapter()
        self._saved_slips: Dict[str, Dict[str, Any]] = {}
        self._seed_saved_slips()

    def _seed_saved_slips(self) -> None:
        try:
            items = self.adapter._read_json("saved_slips.json")
            for item in items:
                self._saved_slips[item["id"]] = item
        except FileNotFoundError:
            pass

    def get_categories(self, enabled_only: bool = False) -> Dict[str, Any]:
        cats = self.adapter.load_categories()
        leagues = {lg["id"]: lg for lg in self.adapter.load_leagues()}
        events = self.adapter.load_events()

        counts_by_sport: Dict[int, int] = {}
        for ev in events:
            sport_id = leagues.get(ev["league_id"], {}).get("sport_id")
            if sport_id is not None:
                counts_by_sport[sport_id] = counts_by_sport.get(sport_id, 0) + 1

        now_iso = datetime.now(timezone.utc).isoformat()
        formatted: List[Dict[str, Any]] = []
        for c in cats:
            if enabled_only and not c.get("is_enabled_v1", False):
                continue
            formatted.append(
                {
                    "id": c["id"],
                    "slug": c["slug"],
                    "name_pl": c["name_pl"],
                    "is_enabled_v1": bool(c.get("is_enabled_v1", False)),
                    "volatility_tier": c.get("volatility_tier", "standard"),
                    "active_model": c.get("active_model", "dixon_coles_xg_v1"),
                    "fixtures_count": counts_by_sport.get(c["id"], 0),
                    "updated_at": now_iso,
                }
            )
        return {"categories": formatted, "total": len(formatted)}

    def _build_competitor(self, comp_id: str, name: str, ratings: Dict[str, Dict[str, Any]]) -> CompetitorInput:
        r = ratings.get(comp_id, {})
        return CompetitorInput(
            competitor_id=comp_id,
            name=name,
            elo=r.get("rating_elo"),
            surface_elo=r.get("surface_elo"),
            glicko_r=r.get("glicko_r"),
            glicko_rd=r.get("glicko_rd"),
            glicko_sigma=r.get("glicko_sigma"),
            xg_attack=r.get("xg_attack"),
            xg_defense=r.get("xg_defense"),
            goals_attack=r.get("goals_attack"),
            goals_defense=r.get("goals_defense"),
            pace=r.get("pace"),
            ortg=r.get("ortg"),
            drtg=r.get("drtg"),
            rest_days=r.get("rest_days"),
            serve_win_pct=r.get("serve_win_pct"),
            return_win_pct=r.get("return_win_pct"),
        )

    def _run_model_for_event(
        self,
        ev: Dict[str, Any],
        sport_slug: str,
        ratings: Dict[str, Dict[str, Any]],
    ) -> Optional[SportPredictionResult]:
        model_cls = SPORT_MODELS.get(sport_slug)
        if model_cls is None:
            return None
        ctx = MatchContext(
            event_id=ev["id"],
            sport=sport_slug,
            home_competitor=self._build_competitor(ev["home_competitor_id"], ev["home_team_name"], ratings),
            away_competitor=self._build_competitor(ev["away_competitor_id"], ev["away_team_name"], ratings),
            surface_or_format=ev.get("surface_or_format"),
        )
        return model_cls.predict(ctx)

    def _compute_event_markets(
        self,
        ev: Dict[str, Any],
        sport_slug: str,
        ratings: Dict[str, Dict[str, Any]],
        odds_rows: List[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Optional[SportPredictionResult]]:
        pred = self._run_model_for_event(ev, sport_slug, ratings)
        if pred is None:
            return [], None

        # Group snapshots by market_key -> bookmaker_key -> outcome_key
        by_market: Dict[str, Dict[str, Dict[str, float]]] = {}
        for row in odds_rows:
            if row["event_id"] != ev["id"]:
                continue
            mkt = row["market_key"]
            bk = row["bookmaker_key"]
            out = row["outcome_key"]
            by_market.setdefault(mkt, {}).setdefault(bk, {})[out] = float(row["odds_decimal"])

        markets_out: List[Dict[str, Any]] = []
        for mkt_key, mkt_pred in pred.markets.items():
            outcomes_keys = list(mkt_pred.outcomes.keys())
            bk_map = by_market.get(mkt_key, {})

            # Sharp benchmark (Pinnacle if present, else average)
            sharp_odds_map = bk_map.get("pinnacle")
            if sharp_odds_map and all(k in sharp_odds_map for k in outcomes_keys):
                sharp_probs_list = devig_shin([sharp_odds_map[k] for k in outcomes_keys])
                sharp_probs = dict(zip(outcomes_keys, sharp_probs_list))
            else:
                sharp_probs = dict(mkt_pred.outcomes)

            p_model_vec = [float(mkt_pred.outcomes[k]) for k in outcomes_keys]
            p_sharp_vec = [float(sharp_probs.get(k, mkt_pred.outcomes[k])) for k in outcomes_keys]
            fused_vec = fuse_market_probabilities(p_model_vec, p_sharp_vec, sport_slug)
            fused_probs = dict(zip(outcomes_keys, [float(v) for v in fused_vec]))

            outcomes_detail: List[Dict[str, Any]] = []
            for ok in outcomes_keys:
                p_mod = float(mkt_pred.outcomes[ok])
                p_shp = float(sharp_probs.get(ok, p_mod))
                p_true = float(fused_probs[ok])
                fair_odds = round(1.0 / max(p_true, 1e-4), 3)

                # Pick best non-sharp Polish bookmaker odds if available, else estimate from fair_odds
                best_bk = "betclic"
                best_odd = round(max(1.05, fair_odds * 0.96), 2)
                for bk_name, bk_outcomes in bk_map.items():
                    if bk_name == "pinnacle":
                        continue
                    if ok in bk_outcomes and bk_outcomes[ok] > best_odd:
                        best_odd = float(bk_outcomes[ok])
                        best_bk = bk_name
                if bk_map and best_bk == "betclic" and "betclic" not in bk_map:
                    for bk_name, bk_outcomes in bk_map.items():
                        if ok in bk_outcomes:
                            best_odd = float(bk_outcomes[ok])
                            best_bk = bk_name
                            break

                ev_std = round(p_true * (best_odd * 0.88) - 1.0, 4)
                ev_tf = round(p_true * best_odd - 1.0, 4)
                kelly_f = round(
                    calculate_kelly_fraction_pl(
                        odds_gross=best_odd,
                        probability=p_true,
                        tax_multiplier=1.00,
                        is_pit_taxed=False,
                        gamma=0.25,
                        max_cap=0.05,
                    ),
                    4,
                )

                outcomes_detail.append(
                    {
                        "outcome_key": ok,
                        "outcome_label": OUTCOME_LABELS_PL.get(ok, ok),
                        "best_bookmaker": best_bk,
                        "odds_decimal": round(best_odd, 2),
                        "p_model": round(p_mod, 4),
                        "p_sharp": round(p_shp, 4),
                        "p_true": round(p_true, 4),
                        "fair_odds": fair_odds,
                        "ev_standard_pl": ev_std,
                        "ev_taxfree_pl": ev_tf,
                        "is_value_bet": ev_tf > 0.0,
                        "kelly_fraction": kelly_f,
                    }
                )

            markets_out.append(
                {
                    "market_key": mkt_key,
                    "market_label": MARKET_LABELS_PL.get(mkt_key, mkt_pred.market_label),
                    "outcomes": outcomes_detail,
                }
            )
        return markets_out, pred

    def get_events(
        self,
        sport: Optional[str] = None,
        league_id: Optional[int] = None,
        market: Optional[str] = None,
        min_ev: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        cats = {c["id"]: c for c in self.adapter.load_categories()}
        leagues = {lg["id"]: lg for lg in self.adapter.load_leagues()}
        events = self.adapter.load_events()
        ratings = self.adapter.load_competitor_ratings()
        odds_rows = self.adapter.load_odds_snapshots()

        items: List[Dict[str, Any]] = []
        for ev in events:
            lg = leagues.get(ev["league_id"], {})
            cat = cats.get(lg.get("sport_id"), {})
            sport_slug = cat.get("slug", "")
            if not cat.get("is_enabled_v1", False):
                continue
            if sport and sport_slug != sport:
                continue
            if league_id is not None and ev["league_id"] != league_id:
                continue

            markets, _ = self._compute_event_markets(ev, sport_slug, ratings, odds_rows)
            if not markets:
                continue
            if market:
                matching = [m for m in markets if m["market_key"] == market]
                if not matching:
                    continue
                primary = matching[0]
            else:
                primary = markets[0]

            all_evs = [o["ev_taxfree_pl"] for m in markets for o in m["outcomes"]]
            max_ev = max(all_evs) if all_evs else 0.0
            if min_ev is not None and max_ev < min_ev:
                continue

            items.append(
                {
                    "id": ev["id"],
                    "sport_slug": sport_slug,
                    "sport_name_pl": cat.get("name_pl", sport_slug),
                    "league_id": ev["league_id"],
                    "league_name": lg.get("name", "Liga"),
                    "league_country": lg.get("country"),
                    "home_team": ev["home_team_name"],
                    "away_team": ev["away_team_name"],
                    "start_time_utc": ev["start_time_utc"],
                    "status": ev.get("status", "pre_match"),
                    "surface_or_format": ev.get("surface_or_format"),
                    "primary_market": primary,
                    "all_markets_count": len(markets),
                    "max_ev_net": round(max_ev, 4),
                    "is_value_bet": max_ev > 0.0,
                }
            )

        total = len(items)
        return {
            "events": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_event_breakdown(self, event_id: str) -> Optional[Dict[str, Any]]:
        cats = {c["id"]: c for c in self.adapter.load_categories()}
        leagues = {lg["id"]: lg for lg in self.adapter.load_leagues()}
        events = {ev["id"]: ev for ev in self.adapter.load_events()}
        ev = events.get(event_id)
        if not ev:
            return None

        lg = leagues.get(ev["league_id"], {})
        cat = cats.get(lg.get("sport_id"), {})
        sport_slug = cat.get("slug", "")
        ratings = self.adapter.load_competitor_ratings()
        odds_rows = self.adapter.load_odds_snapshots()
        markets, pred = self._compute_event_markets(ev, sport_slug, ratings, odds_rows)
        if pred is None:
            return None

        home_r = ratings.get(ev["home_competitor_id"], {})
        away_r = ratings.get(ev["away_competitor_id"], {})
        return {
            "event_id": ev["id"],
            "sport": sport_slug,
            "league_name": lg.get("name", "Liga"),
            "home_team": ev["home_team_name"],
            "away_team": ev["away_team_name"],
            "start_time_utc": ev["start_time_utc"],
            "status": ev.get("status", "pre_match"),
            "model_name": cat.get("active_model", pred.model_version),
            "model_version": pred.model_version,
            "bayesian_fusion": {
                "model_weight": 0.45 if sport_slug == "football" else 0.40,
                "sharp_weight": 0.55 if sport_slug == "football" else 0.60,
                "sharp_bookmaker": "pinnacle",
            },
            "competitor_ratings": {
                "home": home_r,
                "away": away_r,
            },
            "factual_factors": [
                {
                    "label": "Model bazowy",
                    "value": pred.model_version,
                    "impact": "neutral",
                },
                {
                    "label": "Różnica Elo",
                    "value": f"{(home_r.get('rating_elo', 1500) - away_r.get('rating_elo', 1500)):+.0f} pkt",
                    "impact": "positive" if home_r.get("rating_elo", 1500) > away_r.get("rating_elo", 1500) else "negative",
                },
            ],
            "sport_breakdown": pred.breakdown,
            "available_markets": markets,
        }

    def _build_candidate_pool(self) -> List[CandidateSelection]:
        cats = {c["id"]: c for c in self.adapter.load_categories()}
        leagues = {lg["id"]: lg for lg in self.adapter.load_leagues()}
        events = self.adapter.load_events()
        ratings = self.adapter.load_competitor_ratings()
        odds_rows = self.adapter.load_odds_snapshots()

        pool: List[CandidateSelection] = []
        for ev in events:
            lg = leagues.get(ev["league_id"], {})
            cat = cats.get(lg.get("sport_id"), {})
            if not cat.get("is_enabled_v1", False):
                continue
            sport_slug = cat["slug"]
            markets, _ = self._compute_event_markets(ev, sport_slug, ratings, odds_rows)
            for mkt in markets:
                for out in mkt["outcomes"]:
                    pool.append(
                        CandidateSelection(
                            event_id=ev["id"],
                            event_name=f"{ev['home_team_name']} vs {ev['away_team_name']}",
                            sport=sport_slug,
                            league_name=lg.get("name", "Liga"),
                            start_time_utc=ev["start_time_utc"],
                            market_key=mkt["market_key"],
                            market_label=mkt["market_label"],
                            outcome_key=out["outcome_key"],
                            outcome_label=out["outcome_label"],
                            bookmaker_key=out["best_bookmaker"],
                            odds_gross=out["odds_decimal"],
                            p_model=out["p_model"],
                            p_sharp=out["p_sharp"],
                            p_true=out["p_true"],
                            ev_net=out["ev_taxfree_pl"],
                            applied_tax_multiplier=1.0,
                        )
                    )
        return pool

    def generate_slips(self, params: SlipGenerateParams) -> Dict[str, Any]:
        pool = self._build_candidate_pool()
        proposals, pool_size, elapsed_ms = SlipOptimizer.generate_slips(pool, params)
        return {
            "coupons": [p.model_dump() for p in proposals],
            "candidate_pool_size": pool_size,
            "solver_algorithm": "beam_search_max_p_joint",
            "execution_time_ms": elapsed_ms,
        }

    def evaluate_slip(
        self,
        legs: List[Dict[str, Any]],
        stake: float,
        bookmaker_mode: str,
    ) -> Dict[str, Any]:
        pool = {
            f"{c.event_id}:{c.market_key}:{c.outcome_key}": c
            for c in self._build_candidate_pool()
        }
        selected: List[CandidateSelection] = []
        for leg in legs:
            key = f"{leg['event_id']}:{leg['market_key']}:{leg['outcome_key']}"
            cand = pool.get(key)
            if cand is None:
                # Allow evaluating custom/synthetic legs seamlessly
                cand = CandidateSelection(
                    event_id=leg["event_id"],
                    event_name=leg["event_id"],
                    sport="football",
                    league_name="Własny",
                    start_time_utc=datetime.now(timezone.utc).isoformat(),
                    market_key=leg["market_key"],
                    market_label=leg["market_key"],
                    outcome_key=leg["outcome_key"],
                    outcome_label=leg["outcome_key"],
                    bookmaker_key=leg.get("bookmaker_key") or "betclic",
                    odds_gross=float(leg.get("odds_override") or 1.80),
                    p_model=0.55,
                    p_sharp=0.55,
                    p_true=0.55,
                )
            else:
                updates: Dict[str, Any] = {}
                if leg.get("odds_override") is not None:
                    updates["odds_gross"] = float(leg["odds_override"])
                if leg.get("bookmaker_key"):
                    updates["bookmaker_key"] = leg["bookmaker_key"]
                if updates:
                    cand = cand.model_copy(update=updates)
            selected.append(cand)

        evaluated = SlipOptimizer.evaluate_slip(selected, stake, bookmaker_mode)
        return evaluated.model_dump()

    def list_saved_slips(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._saved_slips.values())
        if user_id:
            items = [i for i in items if i.get("user_id") == user_id]
        return {"items": items, "total": len(items)}

    def save_slip(self, payload: Dict[str, Any], user_id: str = "00000000-0000-0000-0000-000000000001") -> Dict[str, Any]:
        evaluated = self.evaluate_slip(
            legs=payload["selections"],
            stake=float(payload["stake"]),
            bookmaker_mode=payload["bookmaker_mode"],
        )
        slip_id = str(uuid.uuid4())
        record = {
            "id": slip_id,
            "user_id": user_id,
            "name": payload.get("name") or "Kupon LeadBet",
            "selections": evaluated["selections"],
            "bookmaker_key": payload.get("bookmaker_key") or "betclic",
            "tax_multiplier": evaluated["tax_multiplier"],
            "total_odds_gross": evaluated["total_odds_gross"],
            "total_odds_net": evaluated["total_odds_net"],
            "stake": evaluated["stake"],
            "potential_payout_gross": evaluated["potential_payout_gross"],
            "potential_payout_net": evaluated["potential_payout_net"],
            "joint_probability": evaluated["joint_probability"],
            "slip_ev_net": evaluated["slip_ev_net"],
            "recommended_kelly_stake_pct": evaluated["kelly_stake_fraction"],
            "pit_10_applies": evaluated["pit_10_applies"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._saved_slips[slip_id] = record
        return {"slip": record}

    def delete_saved_slip(self, slip_id: str) -> bool:
        return self._saved_slips.pop(slip_id, None) is not None

    def get_calibration_metrics(self, time_horizon: str = "90d") -> Dict[str, Any]:
        samples = self.adapter.load_calibration_samples()
        probs = [float(s["p_model"]) for s in samples]
        outcomes = [int(s["outcome"]) for s in samples]
        model_odds = [float(s["bet_odds"]) for s in samples]
        closing_odds = [float(s["closing_odds_devigged"]) for s in samples]

        summary = evaluate_calibration(probs, outcomes, model_odds, closing_odds)
        by_sport_map: Dict[str, List[Dict[str, Any]]] = {}
        for s in samples:
            by_sport_map.setdefault(s["sport"], []).append(s)

        sport_names = {"football": "Piłka nożna", "basketball": "Koszykówka", "tennis": "Tenis ziemny", "hockey": "Hokej na lodzie"}
        sport_models = {"football": "dixon_coles_xg_v1", "basketball": "pace_ortg_drtg_v1", "tennis": "markov_surface_elo_v1", "hockey": "skellam_emptynet_v1"}
        by_sport = []
        for sp, rows in by_sport_map.items():
            sp_sum = evaluate_calibration(
                [float(r["p_model"]) for r in rows],
                [int(r["outcome"]) for r in rows],
                [float(r["bet_odds"]) for r in rows],
                [float(r["closing_odds_devigged"]) for r in rows],
            )
            by_sport.append(
                {
                    "sport": sp,
                    "sport_name_pl": sport_names.get(sp, sp),
                    "model_name": sport_models.get(sp, sp),
                    "sample_size": sp_sum.sample_size,
                    "brier_score": round(sp_sum.brier_score, 4),
                    "log_loss": round(sp_sum.log_loss, 4),
                    "clv_beat_rate": round(sp_sum.clv_beat_rate, 4),
                    "avg_clv_percentage": round(sp_sum.avg_clv_percentage, 4),
                }
            )

        return {
            "time_horizon": time_horizon,
            "overall": {
                "sample_size": summary.sample_size,
                "brier_score": round(summary.brier_score, 4),
                "brier_skill_score": round(summary.brier_skill_score, 4),
                "log_loss": round(summary.log_loss, 4),
                "clv_beat_rate": round(summary.clv_beat_rate, 4),
                "avg_clv_percentage": round(summary.avg_clv_percentage, 4),
            },
            "by_sport": by_sport,
            "reliability_bins": [
                {
                    "bin_index": b.bin_index,
                    "predicted_prob_lower": b.predicted_prob_lower,
                    "predicted_prob_upper": b.predicted_prob_upper,
                    "mean_predicted_prob": round(b.mean_predicted_prob, 4),
                    "empirical_win_rate": round(b.empirical_win_rate, 4),
                    "sample_count": b.sample_count,
                    "brier_contribution": round(b.brier_contribution, 5),
                }
                for b in summary.reliability_bins
            ],
            "last_calculated_at": datetime.now(timezone.utc).isoformat(),
        }
