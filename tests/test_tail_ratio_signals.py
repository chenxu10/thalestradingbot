from datetime import date

from fentu.pricingservices.tail_ratio import signals


def test_signals_marks_only_crossing_dates():
    series = [
        (date(2026, 7, 30), 0.30),  # above line
        (date(2026, 7, 31), 0.29),
        (date(2026, 8, 3), 0.25),
        (date(2026, 8, 4), 0.24),  # on the line: not a buy yet
        (date(2026, 8, 5), 0.23),  # CROSS below -> signal
        (date(2026, 8, 6), 0.26),  # re-cross above: no signal
        (date(2026, 8, 7), 0.24),
        (date(2026, 8, 10), 0.23),  # CROSS below again -> new signal
        (date(2026, 8, 11), 0.25),
    ]
    buy_line = 0.24

    assert signals(series, buy_line) == [date(2026, 8, 5), date(2026, 8, 10)]
