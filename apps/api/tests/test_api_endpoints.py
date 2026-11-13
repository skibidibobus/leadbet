"""Focused integration tests for QUANTKUPON FastAPI endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_and_categories():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    cat_res = client.get("/api/v1/categories?enabled_only=true")
    assert cat_res.status_code == 200
    slugs = [c["slug"] for c in cat_res.json()["categories"]]
    assert slugs == ["football", "basketball", "tennis", "hockey"]


def test_events_and_breakdown():
    ev_res = client.get("/api/v1/events?sport=football")
    assert ev_res.status_code == 200
    items = ev_res.json()["events"]
    assert len(items) >= 1

    event_id = items[0]["id"]
    bd_res = client.get(f"/api/v1/events/{event_id}/breakdown")
    assert bd_res.status_code == 200
    bd = bd_res.json()
    assert bd["event_id"] == event_id
    assert bd["available_markets"]

    missing_res = client.get("/api/v1/events/does-not-exist/breakdown")
    assert missing_res.status_code == 404


def test_generate_evaluate_and_saved_slips_lifecycle():
    gen_res = client.post(
        "/api/v1/slips/generate",
        json={
            "sports": ["football", "basketball", "tennis", "hockey"],
            "risk_profile": "balanced",
            "target_odds_min": 2.2,
            "target_odds_max": 8.0,
            "min_legs": 2,
            "max_legs": 3,
            "stake": 100.0,
            "bookmaker_mode": "betclic_tax_free",
        },
    )
    assert gen_res.status_code == 200
    coupons = gen_res.json()["coupons"]
    assert len(coupons) >= 1

    first_legs = [
        {
            "event_id": s["event_id"],
            "market_key": s["market_key"],
            "outcome_key": s["outcome_key"],
            "bookmaker_key": "fortuna",
            "odds_override": 2.05,
        }
        for s in coupons[0]["selections"]
    ]
    eval_res = client.post(
        "/api/v1/slips/evaluate",
        json={
            "selections": first_legs,
            "stake": 100.0,
            "bookmaker_mode": "standard_088",
        },
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["tax_multiplier"] == 0.88

    save_res = client.post(
        "/api/v1/slips/saved",
        json={
            "name": "Test Kupon",
            "selections": first_legs,
            "stake": 100.0,
            "bookmaker_mode": "standard_088",
            "bookmaker_key": "fortuna",
        },
    )
    assert save_res.status_code == 201
    slip_id = save_res.json()["slip"]["id"]

    list_res = client.get("/api/v1/slips/saved")
    assert list_res.status_code == 200
    assert any(s["id"] == slip_id for s in list_res.json()["items"])

    del_res = client.delete(f"/api/v1/slips/saved/{slip_id}")
    assert del_res.status_code == 204


def test_calibration_metrics():
    res = client.get("/api/v1/calibration/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "overall" in data
    assert "reliability_bins" in data
    assert "by_sport" in data
