"""
Live yfinance fetcher for the IV term-structure pipeline.

This is the only module in fentu.pricingservices that touches the network.
It pulls a ticker's expiries + per-expiry option chains via yfinance and
returns the chain dict shape that yfinance_chain_to_detail_rows consumes.

Kept separate from yfinance_adapter.py so the adapter stays offline and
unit-testable; this module is intentionally thin and not unit-tested (it
delegates to yfinance, an external library, exactly as volcalculator.py
delegates price history to yfinance without a network test).
"""

from __future__ import annotations

from curl_cffi import requests
import yfinance as yf


def fetch_yfinance_chain(ticker_symbol, max_expiries=None):
    """Fetch expiries + per-expiry option chains for a ticker via yfinance.

    Args:
        ticker_symbol: e.g. "QQQ".
        max_expiries: optional cap on how many expiries to pull chains for
            (each option_chain() call is one network request; the default
            200-DTE window typically needs only the first ~10-15 expiries).

    Returns: (chain_data, underlying_price) where chain_data is shaped
        {"expiries": ["YYYY-MM-DD", ...],
         "chains": {"YYYY-MM-DD": <yfinance option_chain() result>, ...}}
        and underlying_price is the latest close (float) or None if unavailable.
        The chain entries are the raw yfinance option_chain() return objects
        (namedtuple-like with .calls/.puts), which yfinance_chain_to_detail_rows
        accepts directly.
    """
    session = requests.Session(impersonate="chrome")
    ticker = yf.Ticker(ticker_symbol, session=session)

    expiries = list(ticker.options or [])
    if max_expiries is not None:
        expiries = expiries[:max_expiries]

    chains = {}
    for expiry in expiries:
        try:
            chains[expiry] = ticker.option_chain(expiry)
        except Exception:
            continue

    underlying_price = None
    try:
        hist = ticker.history(period="1d")
        if not hist.empty:
            underlying_price = float(hist["Close"].iloc[-1])
    except Exception:
        pass

    chain_data = {"expiries": expiries, "chains": chains}
    return chain_data, underlying_price
