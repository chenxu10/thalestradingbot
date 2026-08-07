from datetime import date, datetime, timedelta

import pandas as pd

from fentu.pricingservices.option_quotes import (
    atm_strike,
    days_to_expiry,
    mid,
    otm_put_mid,
    otm_strike,
    pick_expiry,
    straddle_mid,
)


def fake_chain():
    strikes = [710.0, 715.0, 720.0, 725.0, 730.0]
    rows = pd.DataFrame(
        {
            "strike": strikes,
            "bid": [1.0, 2.0, 3.0, 4.0, 5.0],
            "ask": [2.0, 3.0, 4.0, 5.0, 6.0],
            "impliedVolatility": [0.15, 0.16, 0.17, 0.18, 0.19],
        }
    )
    return type("Chain", (), {"calls": rows, "puts": rows})()


def test_mid_averages_bid_ask():
    assert mid({"bid": 4.0, "ask": 6.0}) == 5.0


def test_atm_strike_nearest_to_spot():
    assert atm_strike(fake_chain(), 723.03) == 725.0


def test_straddle_mid_sums_call_and_put():
    assert straddle_mid(fake_chain(), 725.0) == 9.0


def test_otm_strike_rounded_to_step():
    assert otm_strike(723.03, 0.25) == 540.0
    assert otm_strike(723.03, 0.20) == 580.0


def test_otm_put_mid_at_strike():
    assert otm_put_mid(fake_chain(), 720.0) == 3.5


def test_pick_expiry_nearest_to_target():
    today = datetime.now().date()
    expirations = [
        (today + timedelta(days=40)).isoformat(),
        (today + timedelta(days=70)).isoformat(),
        (today + timedelta(days=105)).isoformat(),
    ]
    ticker = type("Ticker", (), {"options": expirations})()
    assert pick_expiry(ticker, 63) == (today + timedelta(days=70)).isoformat()


def test_pick_expiry_none_when_too_far():
    today = datetime.now().date()
    expirations = [(today + timedelta(days=200)).isoformat()]
    ticker = type("Ticker", (), {"options": expirations})()
    assert pick_expiry(ticker, 63) is None


def test_days_to_expiry():
    today = datetime.now().date()
    expiry = (today + timedelta(days=70)).isoformat()
    assert days_to_expiry(expiry) == 70
