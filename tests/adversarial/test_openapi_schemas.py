"""Adversarial Verification Suite for OpenAPI 3.1 Schemas (Milestone 1).

Tests schema validation against valid and invalid payloads:
- Tax multipliers (valid 0.88, 1.0 vs invalid values)
- Stakes (positive vs negative/zero stakes)
- Probabilities (bounds in [0, 1])
- Target odds ranges and limits
- Kelly stake fractions
- Structural edge cases (empty arrays, missing required keys)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import pytest
import yaml

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OPENAPI_PATH = REPO_ROOT / "packages" / "contracts" / "openapi.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> Dict[str, Any]:
    """Loads the authoritative OpenAPI 3.1 YAML document."""
    assert OPENAPI_PATH.exists(), f"OpenAPI contract missing at {OPENAPI_PATH}"
    with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    assert spec.get("openapi") == "3.1.0", "Expected OpenAPI version 3.1.0"
    return spec


@pytest.fixture(scope="module")
def schema_validator(openapi_spec: Dict[str, Any]):
    """Creates a Draft 2020-12 validator factory with referencing registry."""
    resource = DRAFT202012.create_resource(openapi_spec)
    registry = Registry().with_resource("https://quantkupon.pl/openapi.yaml", resource)

    def _get_validator(schema_name: str) -> Draft202012Validator:
        ref_schema = {
            "$ref": f"https://quantkupon.pl/openapi.yaml#/components/schemas/{schema_name}"
        }
        return Draft202012Validator(ref_schema, registry=registry)

    return _get_validator


# ==============================================================================
# 1. SlipGenerateRequest Tests
# ==============================================================================


def test_slip_generate_request_valid_payload(schema_validator):
    """Verifies that a well-formed SlipGenerateRequest passes validation."""
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": ["football", "basketball"],
        "risk_profile": "balanced",
        "target_odds_min": 2.5,
        "target_odds_max": 5.0,
        "stake": 100.0,
        "bookmaker_mode": "standard_088",
        "min_legs": 2,
        "max_legs": 5,
        "min_leg_prob": 0.55,
        "only_plus_ev": True,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) == 0, f"Expected valid payload to pass, got: {errors}"


@pytest.mark.parametrize("invalid_stake", [-10.0, -0.01, 0.0, 0.99])
def test_slip_generate_request_rejects_non_positive_or_sub_minimum_stake(
    schema_validator, invalid_stake
):
    """Verifies that stake < 1.0 is rejected by minimum constraint."""
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": ["football"],
        "risk_profile": "conservative",
        "target_odds_min": 2.0,
        "target_odds_max": 4.0,
        "stake": invalid_stake,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0
    assert any("minimum" in e.message.lower() for e in errors)


@pytest.mark.parametrize("invalid_prob", [-0.1, -0.0001, 1.0001, 1.5, 2.0])
def test_slip_generate_request_rejects_out_of_bound_min_leg_prob(
    schema_validator, invalid_prob
):
    """Verifies that min_leg_prob outside [0.0, 1.0] is rejected."""
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": ["football"],
        "risk_profile": "balanced",
        "target_odds_min": 1.5,
        "target_odds_max": 3.0,
        "min_leg_prob": invalid_prob,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0
    assert any("minimum" in e.message.lower() or "maximum" in e.message.lower() for e in errors)


@pytest.mark.parametrize("invalid_mode", ["superbet_illegal", "pinnacle_no_tax", "custom_075", ""])
def test_slip_generate_request_rejects_invalid_bookmaker_mode(schema_validator, invalid_mode):
    """Verifies that bookmaker_mode not in allowed enum is rejected."""
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": ["football"],
        "risk_profile": "balanced",
        "target_odds_min": 1.5,
        "target_odds_max": 3.0,
        "bookmaker_mode": invalid_mode,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0
    assert any("enum" in e.message.lower() or "is not one of" in e.message.lower() for e in errors)


@pytest.mark.parametrize("min_legs,max_legs", [(0, 5), (1, 11), (-1, 4), (12, 15)])
def test_slip_generate_request_rejects_out_of_range_legs_count(
    schema_validator, min_legs, max_legs
):
    """Verifies that legs count outside [1, 10] is rejected."""
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": ["football"],
        "risk_profile": "balanced",
        "target_odds_min": 1.5,
        "target_odds_max": 3.0,
        "min_legs": min_legs,
        "max_legs": max_legs,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0


def test_slip_generate_request_empty_sports_adversarial_finding(schema_validator):
    """Adversarial probe: sports has no minItems constraint, so empty list is accepted.
    
    FINDING: SlipGenerateRequest.sports should logically enforce minItems: 1.
    """
    validator = schema_validator("SlipGenerateRequest")
    payload = {
        "sports": [],  # Empty sports selection
        "risk_profile": "balanced",
        "target_odds_min": 1.5,
        "target_odds_max": 3.0,
    }
    errors = list(validator.iter_errors(payload))
    # Note: schema does NOT define minItems, so this passes validation
    is_schema_lax = len(errors) == 0
    assert is_schema_lax, "Contract was updated with minItems"


# ==============================================================================
# 2. SlipEvaluateRequest Tests
# ==============================================================================


def test_slip_evaluate_request_valid_payload(schema_validator):
    """Verifies valid evaluate request payload."""
    validator = schema_validator("SlipEvaluateRequest")
    payload = {
        "selections": [
            {
                "event_id": "ev_01",
                "market_key": "1x2",
                "outcome_key": "home",
                "odds_override": 1.95,
                "bookmaker_key": "sts",
            }
        ],
        "stake": 50.0,
        "bookmaker_mode": "betclic_tax_free",
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) == 0


@pytest.mark.parametrize("invalid_stake", [-50.0, 0.0, 0.999])
def test_slip_evaluate_request_rejects_non_positive_stake(schema_validator, invalid_stake):
    """Verifies that stake < 1.0 is rejected in evaluate request."""
    validator = schema_validator("SlipEvaluateRequest")
    payload = {
        "selections": [{"event_id": "ev_01", "market_key": "1x2", "outcome_key": "home"}],
        "stake": invalid_stake,
        "bookmaker_mode": "standard_088",
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0


def test_slip_evaluate_request_empty_selections_adversarial_finding(schema_validator):
    """Adversarial probe: SlipEvaluateRequest.selections lacks minItems: 1.
    
    FINDING: SlipEvaluateRequest allows empty selections `[]`.
    """
    validator = schema_validator("SlipEvaluateRequest")
    payload = {
        "selections": [],  # Empty list of legs
        "stake": 100.0,
        "bookmaker_mode": "standard_088",
    }
    errors = list(validator.iter_errors(payload))
    # Currently passes because minItems: 1 is missing
    assert len(errors) == 0, "Expected empty selections to pass schema due to missing minItems: 1"


# ==============================================================================
# 3. GeneratedCoupon & SlipEvaluateResponse Schema Tests
# ==============================================================================


def test_generated_coupon_valid_payload(schema_validator):
    """Verifies a fully populated GeneratedCoupon response object."""
    validator = schema_validator("GeneratedCoupon")
    payload = {
        "id": "slip_001",
        "title": "Optymalny AKO",
        "risk_tier": "balanced",
        "selections": [
            {
                "event_id": "ev_01",
                "event_name": "Team A vs Team B",
                "sport": "football",
                "league_name": "Premier League",
                "start_time_utc": "2026-11-13T20:00:00Z",
                "market_key": "1x2",
                "market_label": "Wynik meczu",
                "outcome_key": "home",
                "outcome_label": "1",
                "bookmaker_key": "sts",
                "odds_gross": 2.10,
                "p_model": 0.52,
                "p_sharp": 0.50,
                "p_true": 0.51,
                "ev_net": 0.05,
                "applied_tax_multiplier": 1.0,
            }
        ],
        "total_odds_gross": 2.10,
        "tax_multiplier": 1.0,
        "total_odds_net": 2.10,
        "joint_probability": 0.51,
        "stake": 100.0,
        "potential_payout_gross": 210.0,
        "potential_payout_net": 210.0,
        "pit_10_applies": False,
        "pit_10_deduction": 0.0,
        "pit_warning": None,
        "slip_ev_net": 0.071,
        "kelly_stake_fraction": 0.035,
        "kelly_recommended_stake_pln": 35.0,
        "anti_correlation_passed": True,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) == 0, f"Valid coupon failed validation: {errors}"


@pytest.mark.parametrize("invalid_tax", [0.70, 0.85, 0.90, 1.12, 0.0, -0.88])
def test_generated_coupon_enforces_tax_multiplier_enum(schema_validator, invalid_tax):
    """Verifies that GeneratedCoupon strictly rejects tax_multiplier outside [0.88, 1.0]."""
    validator = schema_validator("GeneratedCoupon")
    payload = {
        "id": "slip_001",
        "title": "Optymalny AKO",
        "risk_tier": "balanced",
        "selections": [],
        "total_odds_gross": 2.10,
        "tax_multiplier": invalid_tax,  # INVALID
        "total_odds_net": 2.10,
        "joint_probability": 0.51,
        "stake": 100.0,
        "potential_payout_gross": 210.0,
        "potential_payout_net": 210.0,
        "pit_10_applies": False,
        "pit_10_deduction": 0.0,
        "slip_ev_net": 0.05,
        "kelly_stake_fraction": 0.03,
        "kelly_recommended_stake_pln": 30.0,
        "anti_correlation_passed": True,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) > 0
    assert any("enum" in e.message.lower() or "is not one of" in e.message.lower() for e in errors)


def test_slip_evaluate_response_tax_multiplier_inconsistency_adversarial_finding(schema_validator):
    """Adversarial probe: SlipEvaluateResponse.tax_multiplier lacks enum constraint.
    
    FINDING: Unlike GeneratedCoupon which enforces enum: [0.88, 1.0], SlipEvaluateResponse
    defines tax_multiplier as plain number without enum, allowing invalid values like 0.70.
    """
    validator = schema_validator("SlipEvaluateResponse")
    payload = {
        "selections": [],
        "total_odds_gross": 3.0,
        "tax_multiplier": 0.70,  # Invalid tax multiplier (not 0.88 or 1.0)
        "total_odds_net": 2.10,
        "joint_probability": 0.40,
        "stake": 100.0,
        "potential_payout_gross": 300.0,
        "potential_payout_net": 210.0,
        "pit_10_applies": False,
        "pit_10_deduction": 0.0,
        "slip_ev_net": 0.02,
        "kelly_stake_fraction": 0.02,
        "is_correlated": False,
        "validation_warnings": [],
    }
    errors = list(validator.iter_errors(payload))
    # It passes because SlipEvaluateResponse.tax_multiplier lacks enum [0.88, 1.0]
    assert len(errors) == 0, "Expected schema laxity to allow 0.70 in SlipEvaluateResponse"


def test_coupon_selection_probabilities_unbounded_adversarial_finding(schema_validator):
    """Adversarial probe: CouponSelection probabilities lack minimum: 0.0 and maximum: 1.0.
    
    FINDING: MarketOutcome has minimum: 0.0 and maximum: 1.0, but CouponSelection
    (p_model, p_sharp, p_true) and GeneratedCoupon (joint_probability) omit them.
    """
    validator = schema_validator("CouponSelection")
    payload = {
        "event_id": "ev_01",
        "event_name": "Team A vs Team B",
        "sport": "football",
        "league_name": "Premier League",
        "start_time_utc": "2026-11-13T20:00:00Z",
        "market_key": "1x2",
        "market_label": "Wynik meczu",
        "outcome_key": "home",
        "outcome_label": "1",
        "bookmaker_key": "sts",
        "odds_gross": 2.10,
        "p_model": 1.85,  # Impossible probability > 1.0
        "p_sharp": -0.20,  # Impossible probability < 0.0
        "p_true": 5.0,  # Impossible probability > 1.0
        "ev_net": 0.05,
        "applied_tax_multiplier": 1.0,
    }
    errors = list(validator.iter_errors(payload))
    # Schema omits min/max on CouponSelection, so this invalid mathematical state passes
    assert len(errors) == 0, "Expected missing min/max bounds in CouponSelection schema"


def test_market_outcome_enforces_probability_bounds(schema_validator):
    """Contrast probe: MarketOutcome DOES enforce minimum: 0.0 and maximum: 1.0."""
    validator = schema_validator("MarketOutcome")
    invalid_payload = {
        "outcome_key": "home",
        "label": "1",
        "odds_decimal": 2.10,
        "p_model": 1.85,  # > 1.0
        "p_sharp": 0.50,
        "p_true": 0.51,
        "fair_odds": 1.96,
        "ev_net": 0.05,
        "is_value": True,
    }
    errors = list(validator.iter_errors(invalid_payload))
    assert len(errors) > 0
    assert any("maximum" in e.message.lower() for e in errors)
