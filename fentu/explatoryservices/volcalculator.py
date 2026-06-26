"""
This script calculates volatility and return metrics for financial instruments.

Topology Diagram (ASCII)
========================

 External Dependencies
 +---------------------------------------------------------------------------+
 | yfinance | pandas | numpy | scipy.stats(norm,t) | curl_cffi.requests     |
 | matplotlib.pyplot | plotting_service (ps) | see_power_law (spl)          |
 +---------------------------------------------------------------------------+
      |            |          |            |               |
      | prices     | data     | tails/log  | (unused)      | plotting
      v            v          v            v               v

 Class Hierarchy & Relationships
 +-------------------------------+
 |   VolatilityCalculator        |  <<abstract base>>
 |   calculate_volatility()      |  -> NotImplementedError
 +---------------+---------------+
                 |  inherits
                 v
 +-------------------------------+
 | StandardDeviationVolatility   |
 | calculate_volatility()        |  -> returns_data.std()
 +---------------+---------------+
                 |  used-by (Strategy pattern)
                 v
 +-------------------------------+
 | DailyVolatility               |  <<context>>
 | - calculator: VolatilityCalc  |
 | calculate_1std_daily_vol()    |
 +---------------+---------------+
                 |  composition
                 v
 +---------------------------------------------------------------------------+
 |                          VolatilityFacade                                 |
 |  instrument | start_date | end_date                                       |
 |  return_periods = {daily, weekly, monthly, yearly}                       |
 |                                                                           |
 |  [Data Acquisition]                    [Volatility]                       |
 |  _get_prices() ----> yf.Ticker          calculate_daily_volatility()      |
 |        |                 + curl_cffi            |                         |
 |        |                 session                v                         |
 |        +---> _get_returns() ----> DailyVolatility                          |
 |                  |  pct_change(period)                                     |
 |                  v                                                         |
 |            daily/weekly/monthly/yearly returns ----+                       |
 |                                                    |                     |
 |  [Calendar Returns]                                |                     |
 |  get_calendar_year_returns()                       |                     |
 |     +-> _get_prices()                              |                     |
 |     +-> calculate_yearly_return_list()             |                     |
 |                                                    |                     |
 |  [Extreme Returns]  <------------------------------+                     |
 |  find_negative_extreme_returns() (k | threshold)                         |
 |  find_positive_extreme_returns() (k | threshold)                         |
 |                                                                           |
 |  [Visualization: data-view-model pattern]                                 |
 |  visualize_percentage_change(period, tail_percent)                       |
 |     |                                                                     |
 |     +-> _prepare_percentage_change_data()  <<data prep>>                  |
 |     |       +-> return_periods, numpy (left/right tails)                  |
 |     |       +-> returns dict {returns, tails, period, instrument}         |
 |     |                                                                     |
    |     +-> _plot_percentage_change()  <<visualization>>                      |
    |             +-> ps.qq_plot()              (axes[0,0])                     |
    |             +-> ps.histgram_plot()        (axes[0,1])                     |
    |             +-> spl.plot_loglog_with_fit  (axes[1,0/1] - tail fits)       |
    |             +-> _plot_term_structure_panel (axes[2,:] - IV term struct)   |
    |             +-> _plot_vix_panel()          (axes[3,:] - ^VIX 1990->today) |
    |                  +-> _get_vix_ohlc() -> _get_raw_ohlc(^VIX) [unfiltered]  |
    |                  +-> _get_current_vix_value() -> _now_eastern()           |
    |                       (today open if >=9:30 ET, else last close)         |
    |             +-> _show_panel_unavailable()  (shared fallback note)         |
    |             +-> matplotlib subplots (4x2 gridspec) + suptitle             |
 |                                                                           |
 |  [Reporting]                                                              |
 |  show_today_return()                       -> daily_returns.tail(20)      |
 |  get_past_week_price_and_log_returns()     -> _get_prices + np.log       |
 |  get_past_year_price_and_log_returns()     -> _get_prices + np.log       |
 +---------------------------------------------------------------------------+

 Entry Point
 +---------------------------------------------------------------------------+
 | __main__: VolatilityFacade("ILS")                                         |
 |   -> get_past_week_price_and_log_returns()                                |
 |   -> calculate_daily_volatility()                                         |
 |   -> find_negative/positive_extreme_returns() (threshold=+-0.2)           |
 +---------------------------------------------------------------------------+
"""

import yfinance as yf
import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps
import fentu.explatoryservices.see_power_law as spl
import matplotlib.pyplot as plt
import numpy as np
from curl_cffi import requests
from datetime import datetime, timezone, timedelta, time as _dtime

VIX_TICKER = "^VIX"
TIME_MARKET_OPEN = _dtime(9, 30)  # US equity market open, Eastern Time


def _is_us_dst(dt_utc):
    """True if `dt_utc` (tz-aware UTC) falls within US daylight saving time.

    US DST: second Sunday of March -> first Sunday of November. Stdlib-only so
    this works on Python 3.8 (no zoneinfo).
    """
    year = dt_utc.year
    mar1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    first_sunday_mar = mar1 + timedelta(days=(6 - mar1.weekday()) % 7)
    second_sunday_mar = first_sunday_mar + timedelta(days=7)
    nov1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    first_sunday_nov = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    return second_sunday_mar <= dt_utc < first_sunday_nov


def _now_eastern():
    """Current time in US Eastern Time (EST/EDT), tz-aware."""
    now_utc = datetime.now(timezone.utc)
    offset_h = -4 if _is_us_dst(now_utc) else -5
    return now_utc.astimezone(timezone(timedelta(hours=offset_h), "ET"))


class VolatilityCalculator:
    """Base class for different volatility calculation strategies"""
    def calculate_volatility(self, returns_data):
        raise NotImplementedError

class MeanAbsoluteDeviationVolatility(VolatilityCalculator):
    """Headline daily-volatility metric.

    Per the taleb-convexity-tailhedge skill: SD breaks under fat tails
    (one day = 80% of SP500 kurtosis over 56 years), while MAD exists
    whenever the mean exists. MAD is the headline; STD is kept only for a
    `*_gaussian_only` comparison via StandardDeviationVolatility below.
    """
    def calculate_volatility(self, returns_data):
        return (returns_data - returns_data.mean()).abs().mean()

class StandardDeviationVolatility(VolatilityCalculator):
    """Gaussian-only comparison volatility (kept for reference, not headline).

    Per the skill, this metric loses scientific validity once the data leaves
    the Gaussian basin (fat tails). Use MeanAbsoluteDeviationVolatility above
    as the headline.
    """
    def calculate_volatility(self, returns_data):
        # Handle both Series and DataFrame inputs
        return returns_data.std()

class DailyVolatility:
    def __init__(self, calculator: VolatilityCalculator = None):
        self.calculator = calculator or MeanAbsoluteDeviationVolatility()
    
    def calculate_1std_daily_volatility(self, daily_returns):
        return self.calculator.calculate_volatility(daily_returns)

class VolatilityFacade:
    """
    This class gets daily percentage change of an instrument
    """
    def __init__(self, instrument, start_date=None, end_date=None):
        self.instrument = instrument
        self.start_date = start_date
        self.end_date = end_date
        self.daily_returns = self._get_returns(instrument, 1)
        self.weekly_returns = self._get_returns(instrument, 5)
        self.monthly_returns = self._get_returns(instrument, 21)
        self.yearly_returns = self._get_returns(instrument, 252)
        self.daily_volatility = DailyVolatility()
        self.return_periods = {
            'daily': self.daily_returns,
            'weekly': self.weekly_returns,
            'monthly': self.monthly_returns,
            'yearly': self.yearly_returns
        }

    def _get_raw_ohlc(self, instrument):
        """Fetch full OHLC history for `instrument` with no date filtering.

        The shared network fetch; callers that want the facade's date window
        apply start_date/end_date themselves.
        """
        session = requests.Session(impersonate="chrome")
        ticker = yf.Ticker(instrument, session=session)
        ohlc = ticker.history(period="max")
        if ohlc.index.tz is not None:
            ohlc.index = ohlc.index.tz_localize(None)
        return ohlc

    def _get_prices(self, instrument):
        ohlc = self._get_raw_ohlc(instrument)
        prices = ohlc['Close']

        if self.start_date is not None:
            prices = prices[prices.index >= pd.Timestamp(self.start_date)]
        if self.end_date is not None:
            prices = prices[prices.index <= pd.Timestamp(self.end_date)]

        return prices

    def calculate_yearly_return_list(self, prices, yearly_returns_list, years):
        for year in years:
            # Get first and last trading day prices for each year
            year_data = prices[prices.index.year == year]
            if not year_data.empty:
                first_price = year_data.iloc[0]
                last_price = year_data.iloc[-1]
                
                # Calculate return
                year_return = (last_price - first_price) / first_price
                
                yearly_returns_list.append({
                    'Date': pd.Timestamp(f'{year}-12-31'),
                    'Close': year_return
                })
        return yearly_returns_list
    
    def get_calendar_year_returns(self, instrument=None):
        """
        Calculate returns for each calendar year from 2003 to present.
        Returns a DataFrame with yearly returns where each return represents
        buying on Jan 1st and selling on Dec 31st of the same year.
        """
        instrument = instrument or self.instrument
        prices = self._get_prices(instrument)
        
        # Create empty list to store yearly returns
        yearly_returns_list = []
        
        # Get unique years from the price data
        years = prices.index.year.unique()
        
        yearly_returns_list = self.calculate_yearly_return_list(
            prices, yearly_returns_list, years)
        calendar_returns = pd.DataFrame(yearly_returns_list)
        calendar_returns = calendar_returns.sort_values('Date', ascending=False)
        
        return calendar_returns

    def _get_vix_ohlc(self):
        """Full ^VIX OHLC history (1990 -> today), unfiltered.

        The VIX subplot deliberately ignores the ETF's start/end window so the
        trader sees the complete VIX context.
        """
        return self._get_raw_ohlc(VIX_TICKER)

    def _get_vix_prices(self):
        """Full ^VIX daily close history (1990 -> today), unfiltered."""
        return self._get_vix_ohlc()['Close']

    def _get_current_vix_value(self, vix_ohlc=None, now_et=None):
        """Return (label, value) for the VIX "current value" annotation.

        If the US market has opened today — i.e. the data's last trading day is
        today and the time is >= 9:30 ET — return today's open (the 9:30 ET
        print). Otherwise return the last trading day's close.

        Args:
            vix_ohlc: optional OHLC DataFrame (injected for tests); fetched if
                omitted.
            now_et: optional tz-aware Eastern Time datetime (injected for
                tests); current time if omitted.
        """
        if vix_ohlc is None:
            vix_ohlc = self._get_vix_ohlc()
        if now_et is None:
            now_et = _now_eastern()
        if vix_ohlc.empty:
            return None

        last_row = vix_ohlc.iloc[-1]
        last_date = vix_ohlc.index[-1].date()
        market_opened_today = (
            last_date == now_et.date() and now_et.time() >= TIME_MARKET_OPEN
        )
        if market_opened_today:
            return (
                f"VIX @ open {last_date.isoformat()} 9:30 ET",
                float(last_row['Open']),
            )
        return (
            f"VIX @ last close {last_date.isoformat()}",
            float(last_row['Close']),
        )

    def _get_returns(self, instrument, period_length):
        """
        Helper method to get log returns for different time periods
        Args:
            instrument: The financial instrument ticker
            period_length: Number of days for the period (1=daily, 5=weekly, 21=monthly, 252=yearly)
        """
        prices = self._get_prices(instrument)
        returns = np.log(prices / prices.shift(period_length))[period_length:]
        return returns
    
    def calculate_daily_volatility(self):
        return self.daily_volatility.calculate_1std_daily_volatility(self.daily_returns)
    
    def _prepare_percentage_change_data(self, period='daily'):
        """
        Prepare data for percentage change visualization.

        Returns:
            dict with 'returns', 'tails', 'period', 'instrument'
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")

        returns_data = self.return_periods[period]
        left_tail = np.abs(returns_data[returns_data < 0].values)
        right_tail = returns_data[returns_data > 0].values

        return {
            'returns': returns_data,
            'tails': [
                {'data': left_tail, 'x_min': np.min(left_tail) if len(left_tail) > 0 else None,
                 'title': 'Left Tail (Negative Returns)'},
                {'data': right_tail, 'x_min': np.min(right_tail) if len(right_tail) > 0 else None,
                 'title': 'Right Tail (Positive Returns)'},
            ],
            'period': period,
            'instrument': self.instrument,
        }

    def _plot_tail_fits(self, tails, axes, tail_percent):
        """Render left/right tail log-log fits onto the two bottom-row axes."""
        for tail, ax in zip(tails, axes):
            if tail['x_min'] is not None:
                spl.plot_loglog_with_fit(
                    tail['data'], tail['x_min'], ax=ax,
                    title=tail['title'],
                    tail_percent=tail_percent
                )

    def _build_percentage_change_figure_layout(self):
        """Build the 2x2-on-top + full-width term-structure + VIX figure.

        Returns: (fig, ax_qq, ax_hist, ax_left, ax_right, ax_term, ax_vix) where
        ax_term and ax_vix each span the full width of their bottom rows.
        """
        fig = plt.figure(figsize=(12, 15))
        gs = fig.add_gridspec(
            4, 2,
            height_ratios=[1, 1, 1, 1],
            hspace=0.45, wspace=0.25,
        )
        ax_qq = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])
        ax_left = fig.add_subplot(gs[1, 0])
        ax_right = fig.add_subplot(gs[1, 1])
        ax_term = fig.add_subplot(gs[2, :])
        ax_vix = fig.add_subplot(gs[3, :])
        return fig, ax_qq, ax_hist, ax_left, ax_right, ax_term, ax_vix

    def _plot_percentage_change(self, data, tail_percent):
        """
        Plot percentage change visualizations.

        Layout: a 2x2 block of QQ / histogram / left-tail / right-tail on top,
        with the IV term-structure curve occupying the full-width row beneath.

        Args:
            data: dict from _prepare_percentage_change_data
            tail_percent: Fraction of extreme tail to fit for alpha estimation
        """
        fig, ax_qq, ax_hist, ax_left, ax_right, ax_term, ax_vix = self._build_percentage_change_figure_layout()

        ps.qq_plot(data['returns'], ax=ax_qq, show=False)
        ps.histgram_plot(data['returns'], ax=ax_hist, show=False)
        self._plot_tail_fits(data['tails'], [ax_left, ax_right], tail_percent)
        self._plot_term_structure_panel(ax_term, data['instrument'])
        self._plot_vix_panel(ax_vix)

        fig.suptitle(f"{data['instrument']} {data['period'].capitalize()} Returns")
        plt.show()

    def _plot_term_structure_panel(self, ax, instrument):
        """Fetch the yfinance option chain for `instrument` and render the ATM
        IV term-structure curve on `ax`. Network-failure-safe: on any error the
        panel shows a short note instead of breaking the rest of the figure.
        """
        from datetime import date as _date

        from fentu.pricingservices.yfinance_fetcher import fetch_yfinance_chain
        from fentu.pricingservices.yfinance_adapter import yfinance_chain_to_detail_rows
        from fentu.pricingservices.iv_term_structure import build_bucket_rows
        from fentu.pricingservices.term_structure_plotting import plot_term_structure

        try:
            chain_data, underlying_price = fetch_yfinance_chain(instrument)
            if not chain_data.get("expiries") or underlying_price is None:
                self._show_panel_unavailable(ax, "IV Term Structure", "IV term structure unavailable")
                return

            detail_rows = yfinance_chain_to_detail_rows(
                chain_data,
                underlying_price=underlying_price,
                anchor_date=_date.today(),
            )
            buckets = build_bucket_rows(detail_rows)
            plot_term_structure(
                buckets, ax=ax, show=False,
                title=f"{instrument} IV Term Structure",
            )
        except Exception as exc:
            self._show_panel_unavailable(ax, "IV Term Structure", "IV term structure unavailable", type(exc).__name__)

    def _plot_vix_panel(self, ax):
        """Render the ^VIX full-history close plus a current-value annotation.

        Network-failure-safe: on any error the panel shows a short note instead
        of breaking the rest of the figure, mirroring _plot_term_structure_panel.
        """
        try:
            vix_ohlc = self._get_vix_ohlc()
            if vix_ohlc.empty:
                self._show_panel_unavailable(ax, "VIX Index", "VIX unavailable")
                return
            close = vix_ohlc['Close']
            ax.plot(close.index, close.values, color="purple", lw=1.2, label="VIX close")
            ax.set_title("VIX Index")
            ax.set_ylabel("VIX")
            ax.legend(loc="upper left")
            ax.grid(True, alpha=0.3)

            current = self._get_current_vix_value(vix_ohlc=vix_ohlc)
            if current is not None:
                label, value = current
                ax.text(
                    0.99, 0.95, f"{label}\n{value:.2f}",
                    transform=ax.transAxes, ha="right", va="top",
                    bbox=dict(facecolor="white", alpha=0.8, edgecolor="purple"),
                )
        except Exception:
            self._show_panel_unavailable(ax, "VIX Index", "VIX unavailable")

    def _show_panel_unavailable(self, ax, title, message, detail=""):
        """Render a centered 'unavailable' note on `ax` (shared by the
        term-structure and VIX panels)."""
        text = message
        if detail:
            text = f"{message}\n{detail}"
        ax.text(0.5, 0.5, text, ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)

    def visualize_percentage_change(self, period='daily', tail_percent=0.10):
        """
        Visualize percentage changes for a specific period using QQ plot, histogram,
        and log-log plots for left and right tail analysis.

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            tail_percent: Fraction of extreme tail to fit for alpha estimation (default 0.1)
        """
        data = self._prepare_percentage_change_data(period)
        self._plot_percentage_change(data, tail_percent)

    def _find_extreme_returns(self, period='daily', k=None, threshold=None, side='negative'):
        """
        Find extreme returns for a specific period either by count (k) or threshold.

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of extreme returns to find (mutually exclusive with threshold)
            threshold: float, threshold beyond which returns are considered extreme
            side: str, 'negative' (worst, sorted ascending) or 'positive' (best, sorted descending)

        Returns:
            pandas.Series: Filtered returns sorted from most extreme to least extreme
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")
        returns = self.return_periods[period]
        ascending = (side == 'negative')
        compare = (lambda r, t: r < t) if side == 'negative' else (lambda r, t: r > t)
        if k is not None:
            return returns.sort_values(ascending=ascending).head(k)
        if threshold is not None:
            return returns.loc[compare(returns, threshold)].sort_values(ascending=ascending)
        raise ValueError("Either k or threshold must be specified")

    def find_negative_extreme_returns(self, period='daily', k=None, threshold=None):
        """
        Find negative extreme returns for a specific period either by count (k) or threshold

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of worst returns to find (mutually exclusive with threshold)
            threshold: float, threshold below which returns are considered "worst"

        Returns:
            pandas.Series: Filtered returns sorted from worst to best
        """
        return self._find_extreme_returns(period, k, threshold, side='negative')

    def find_positive_extreme_returns(self, period='daily', k=None, threshold=None):
        """
        Find positive extreme returns for a specific period either by count (k) or threshold

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of best returns to find (mutually exclusive with threshold)
            threshold: float, threshold above which returns are considered "best"

        Returns:
            pandas.Series: Filtered returns sorted from best to worst
        """
        return self._find_extreme_returns(period, k, threshold, side='positive')

    def show_today_return(self):
        """Show recent daily returns"""
        print(self.daily_returns.tail(20))

    def get_past_week_price_and_log_returns(self):
        """Get most recent 5 trading days prices with daily log returns"""
        prices = self._get_prices(self.instrument).tail(5)
        log_returns = np.log(prices / prices.shift(1))
        return pd.DataFrame({'price': prices, 'log_return': log_returns})

    def get_past_year_price_and_log_returns(self):
        """Get most recent ~252 trading days prices with daily log returns"""
        prices = self._get_prices(self.instrument).tail(252)
        log_returns = np.log(prices / prices.shift(1))
        return pd.DataFrame({'price': prices, 'log_return': log_returns})

if __name__ == "__main__":
    volatility = VolatilityFacade("ILS")
    # Visualize different time-frame return distributions
    # volatility.visualize_percentage_change('weekly')
    print(volatility.get_past_week_price_and_log_returns())

    # Calculate volatility metrics
    print(f"Daily volatility (MAD): {volatility.calculate_daily_volatility()}")

    # Find extreme returns
    #print(f"Worst months: {volatility.find_negative_extreme_returns('monthly', k=3)}")
    print(f"Worst days (below -20%): {volatility.find_negative_extreme_returns('daily', threshold=-0.2)}")
    print(f"Worst months (below -20%): {volatility.find_negative_extreme_returns('monthly', threshold=-0.2)}")
    print(f"Best days (above +20%): {volatility.find_positive_extreme_returns('daily', threshold=0.2)}")
    print(f"Best months (above +20%): {volatility.find_positive_extreme_returns('monthly', threshold=0.2)}")

    # Calculate calendar year returns
    #calendar_returns = volatility.get_calendar_year_returns(ticker)
    
    


