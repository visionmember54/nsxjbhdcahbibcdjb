from __future__ import annotations

import pytest

from app.models.market import Market, MarketCategory
from app.tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def _extra_markets():
    db = TestingSessionLocal()
    for order, (slug, name, status) in enumerate(
        [("STARLINE", "Starline", "OPEN"), ("GALI_DISAWAR", "Gali – Disawar", "OPEN"), ("CUSTOM", "Custom Markets", "UPCOMING")], start=2
    ):
        cat = MarketCategory(slug=slug, name=name, display_order=order)
        db.add(cat)
        db.flush()
        db.add(Market(category_id=cat.id, name=f"{slug}-MKT", slug=slug.lower(), status=status, display_order=order))
    db.commit()
    db.close()


def _names(client, headers, **params):
    resp = client.get("/api/v1/home/dashboard", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return {m["name"] for m in resp.json()["data"]["markets"]}, resp.json()["data"]


def test_default_is_regular_only(client, user_headers):
    names, data = _names(client, user_headers)
    assert names == {"TESTGAME", "CUSTOM-MKT"}
    assert [t["key"] for t in data["marketTypes"]] == ["REGULAR", "STARLINE", "GALI_DISAWAR"]


@pytest.mark.parametrize("market_type,expected", [
    ("GALI_DISAWAR", {"GALI_DISAWAR-MKT"}),
    ("starline", {"STARLINE-MKT"}),
    ("ALL", {"TESTGAME", "CUSTOM-MKT", "STARLINE-MKT", "GALI_DISAWAR-MKT"}),
])
def test_market_type_selects_category(client, user_headers, market_type, expected):
    names, _ = _names(client, user_headers, marketType=market_type)
    assert names == expected


def test_items_carry_market_type(client, user_headers):
    _, data = _names(client, user_headers, marketType="ALL")
    assert {m["marketType"] for m in data["markets"]} == {"MATKA", "CUSTOM", "STARLINE", "GALI_DISAWAR"}


def test_status_filter_applies_within_type(client, user_headers):
    names, _ = _names(client, user_headers, marketType="ALL", filter="UPCOMING")
    assert names == {"CUSTOM-MKT"}


def test_unknown_market_type_rejected(client, user_headers):
    resp = client.get("/api/v1/home/dashboard", params={"marketType": "bogus"}, headers=user_headers)
    assert resp.status_code == 400
