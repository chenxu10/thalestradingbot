from datetime import date

from fentu.pricingservices.tail_ratio import daily_series


def test_daily_series_matches_dates_across_maturities():
    wing_quotes = {
        "3m": {
            date(2026, 8, 7): 4.46,  # QQQ Nov-20 580 put, Aug 7 2026
            date(2026, 8, 6): 4.20,
            date(2026, 8, 5): 4.00,
        },
        "6m": {
            date(2026, 8, 7): 6.10,
            date(2026, 8, 6): 5.90,
        },
    }
    straddle_quotes = {
        "3m": {
            date(2026, 8, 7): 69.83,  # ATM 725 straddle, Aug 7 2026
            date(2026, 8, 5): 65.00,
        },
        "6m": {
            date(2026, 8, 7): 95.00,
            date(2026, 8, 6): 92.00,
            date(2026, 8, 5): 90.00,
        },
    }

    series = daily_series(wing_quotes, straddle_quotes)

    assert series["3m"] == [
        (date(2026, 8, 5), 4.00 / 65.00),
        (date(2026, 8, 7), 4.46 / 69.83),
    ]
    assert series["6m"] == [
        (date(2026, 8, 6), 5.90 / 92.00),
        (date(2026, 8, 7), 6.10 / 95.00),
    ]
