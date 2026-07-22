"""Portfolio signal monitor — Taleb's Bloomberg trick, Fooled by Randomness p.166.

The trick (``teams/2005-01-01-nassim-nicolas-taleb-fooled-by-randomness.pdf``,
PDF page 93 / book page 166):

    "I have set up my Bloomberg monitor to display the price and percentage
    change of all relevant prices in the world ... The trick is to look only
    at the large percentage changes. Unless something moves by more than its
    usual daily percentage change, the event is deemed to be noise. ... the
    interpretation is not linear; a 2% move is not twice as significant an
    event as 1%, it is rather like four times."

Three rules implemented here:

1. FIXED PANEL — the same holdings in the same positions every day, so the
   trader builds the instinctive feel Taleb describes. Default:
   TQQQ upper-left, USO upper-right, IAU lower-left, BRKB lower-right.
2. NOISE FILTER — the "usual daily percentage change" is the MAD of the
   holding's daily log returns (the project's headline volatility metric;
   STD is forbidden under fat tails). Bars inside ±1 MAD are gray noise;
   only moves beyond the band are highlighted (red down / green up). The
   latest move never calibrates its own denominator (same discipline as
   ``morning_brief``).
3. NON-LINEAR SIGNIFICANCE — significance scales with the SQUARE of the
   MAD-multiple: a 2-MAD move is reported as ~4x the event of a 1-MAD move,
   not 2x.

Reuse: all network I/O goes through ``ReturnsRepository`` (Seam 1 of
``volcalculator`` — the only object that touches yfinance); the scale is
computed by ``DailyVolatility`` with its default
``MeanAbsoluteDeviationVolatility`` calculator.

CLI: ``see_change daily portfolio`` (wired in ``seechange.py``).
"""

import matplotlib.pyplot as plt

from fentu.explatoryservices.volcalculator import DailyVolatility, ReturnsRepository

# (display label, yfinance ticker) — fixed positions, per the trick.
DEFAULT_PORTFOLIO = (
    ("TQQQ", "TQQQ"),
    ("USO", "USO"),
    ("IAU", "IAU"),
    ("BRKB", "BRK-B"),
)

PERIOD_LENGTHS = {"daily": 1, "weekly": 5, "monthly": 21, "yearly": 252}
LOOKBACK = 60  # trading days of percentage-change bars per panel

NOISE_COLOR = "0.75"  # gray: inside the usual band, deemed noise
UP_COLOR = "green"
DOWN_COLOR = "red"
BAND_COLOR = "0.9"


def noise_multiple(move, usual):
    """Signed MAD-multiple of a move vs the usual percentage change."""
    if not usual or usual != usual:  # 0.0 or NaN
        return None
    return move / usual


def significance(move, usual):
    """Non-linear (quadratic) significance: a 2x-usual move is a 4x event."""
    multiple = noise_multiple(move, usual)
    if multiple is None:
        return None
    return multiple ** 2


def is_signal(move, usual):
    """True only when the move exceeds its usual daily percentage change."""
    multiple = noise_multiple(move, usual)
    return multiple is not None and abs(multiple) > 1.0


def _bar_color(move, usual):
    if not is_signal(move, usual):
        return NOISE_COLOR
    return UP_COLOR if move > 0 else DOWN_COLOR


class PortfolioMonitor:
    """Taleb-trick monitor over a fixed panel of holdings.

    `repository` is injectable (defaults to a fresh `ReturnsRepository`,
    which does NO I/O until asked). `volatility` defaults to the project's
    headline MAD calculator via `DailyVolatility`.
    """

    def __init__(self, holdings=DEFAULT_PORTFOLIO, period="daily",
                 repository=None, volatility=None, lookback=LOOKBACK):
        if period not in PERIOD_LENGTHS:
            raise ValueError(f"Period must be one of {list(PERIOD_LENGTHS)}")
        self.holdings = holdings
        self.period = period
        self._repository = repository or ReturnsRepository()
        self._volatility = volatility or DailyVolatility()
        self.lookback = lookback

    # --- data (view-model; the only place the network is touched) ----------

    def prepare_panels(self):
        return [self._prepare_panel(label, ticker)
                for label, ticker in self.holdings]

    def _prepare_panel(self, label, ticker):
        data = self._fetch_panel_data(ticker)
        if data is None:
            return {"label": label, "available": False}
        returns, prices = data
        calibration = returns.iloc[:-1]  # the event never sets its own scale
        usual = float(
            self._volatility.calculate_1std_daily_volatility(calibration))
        window = returns.iloc[-self.lookback:]
        last_move = float(returns.iloc[-1])
        return {
            "label": label,
            "available": True,
            "window": window,
            "last_price": float(prices.iloc[-1]),
            "last_move": last_move,
            "usual": usual,
            "multiple": noise_multiple(last_move, usual),
            "significance": significance(last_move, usual),
            "signal": is_signal(last_move, usual),
        }

    def _fetch_panel_data(self, ticker):
        """(returns, prices) in percent, or None on any fetch failure or
        empty history — a spurious yfinance hiccup on one holding must
        never crash the whole monitor (morning_brief discipline)."""
        try:
            returns = self._fetch_returns(ticker) * 100.0  # display in percent
            prices = self._repository.get_prices(ticker)
        except Exception:
            return None
        if returns.empty or prices.empty:
            return None
        return returns, prices

    def _fetch_returns(self, ticker):
        return self._repository.get_returns(ticker, PERIOD_LENGTHS[self.period])

    # --- presentation (pure render from the view-model) --------------------

    def visualize(self):
        panels = self.prepare_panels()
        fig, axes = plt.subplots(2, 2, figsize=(13, 8))
        for ax, panel in zip(axes.flat, panels):
            plot_signal_panel(ax, panel)
        fig.suptitle(
            f"Portfolio {self.period} signal monitor — Taleb filter "
            "(Fooled by Randomness p.166): significance ∝ move²",
            fontsize=11)
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()
        return fig


def plot_signal_panel(ax, panel):
    """Render one holding: gray noise bars inside ±1 MAD, highlighted signals."""
    if not panel.get("available", True):
        ax.text(0.5, 0.5, f"{panel['label']} unavailable",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title(panel["label"])
        return
    window = panel["window"]
    usual = panel["usual"]
    colors = [_bar_color(move, usual) for move in window]
    ax.bar(range(len(window)), window.values, color=colors)
    ax.axhspan(-usual, usual, color=BAND_COLOR, zorder=0)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_title(panel["label"])
    ax.set_ylabel("% change")
    _annotate(ax, panel)


def _annotate(ax, panel):
    verdict = "SIGNAL" if panel["signal"] else "noise"
    verdict_color = "green" if panel["signal"] else "red"
    ax.text(0.99, 0.97, verdict, transform=ax.transAxes, ha="right", va="top",
            fontsize=10, fontweight="bold", color=verdict_color)
    if panel["multiple"] is None:
        reading = "usual change undefined"
    else:
        reading = (f"{panel['last_move']:+.2f}% = {panel['multiple']:+.1f}x usual\n"
                   f"significance {panel['significance']:.1f}x")
    ax.text(0.99, 0.87,
            f"last {panel['last_price']:,.2f}\n{reading}\n"
            f"usual {panel['usual']:.2f}% (MAD)",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            bbox=dict(facecolor="white", alpha=0.8,
                      edgecolor="black" if panel["signal"] else NOISE_COLOR))
