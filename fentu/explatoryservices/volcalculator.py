"""
This script calculates volatility and return metrics for financial instruments
"""

import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps
import numpy as np
from scipy.stats import norm, t

class VolatilityCalculator:
    """Base class for different volatility calculation strategies"""
    def calculate_volatility(self, returns_data):
        raise NotImplementedError

class StandardDeviationVolatility(VolatilityCalculator):
    def calculate_volatility(self, returns_data):
        # Handle both Series and DataFrame inputs
        return returns_data.std()

class DailyVolatility:
    def __init__(self, calculator: VolatilityCalculator = None):
        self.calculator = calculator or StandardDeviationVolatility()
    
    def calculate_1std_daily_volatility(self, daily_returns):
        return self.calculator.calculate_volatility(daily_returns)

class VolatilityFacade:
    """
    This class gets daily percentage change of an instrument
    """
    def __init__(self, instrument):
        self.daily_returns = self._get_returns(instrument, 1)
        self.weekly_returns = self._get_returns(instrument, 5)
        self.monthly_returns = self._get_returns(instrument, 21)
        self.yearly_returns = self._get_returns(instrument, 252)
        self.daily_volatility = DailyVolatility()

    def _get_prices(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices
    
    def get_calendar_year_returns(self, instrument):
        """
        Calculate returns for each calendar year from 2003 to present.
        Returns a DataFrame with yearly returns where each return represents
        buying on Jan 1st and selling on Dec 31st of the same year.
        """
        prices = self._get_prices(instrument)
        
        # Create empty list to store yearly returns
        yearly_returns_list = []
        
        # Get unique years from the price data
        years = prices.index.year.unique()
        
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
        
        # Convert to DataFrame and sort by date
        calendar_returns = pd.DataFrame(yearly_returns_list)
        calendar_returns = calendar_returns.sort_values('Date', ascending=False)
        
        return calendar_returns

    def _get_returns(self, instrument, period_length):
        """
        Helper method to get returns for different time periods
        Args:
            instrument: The financial instrument ticker
            period_length: Number of days for the period (1=daily, 5=weekly, 21=monthly, 252=yearly)
        """
        prices = self._get_prices(instrument)
        returns = prices.pct_change(period_length)[period_length:]
        return returns

    def get_past_five_days(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices.tail(5)
    
    def calculate_daily_volatility(self):
        return self.daily_volatility.calculate_1std_daily_volatility(self.daily_returns)
    
    def _visualize_percentage_change(self, returns_data):
        """
        Helper method to visualize percentage changes
        Args:
            returns_data: DataFrame containing the returns data to visualize
        """
        ps.qq_plot(returns_data)
        ps.histgram_plot(returns_data)

    def visualize_daily_percentage_change(self):
        """
        Visualize daily percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.daily_returns)
    
    def visualize_weekly_percentage_change(self):
        """
        Visualize weekly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.weekly_returns)
    
    def visualize_monthly_percentage_change(self):
        """
        Visualize monthly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.monthly_returns)

    def visualize_yearly_percentage_change(self):
        """
        Visualize yearly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.yearly_returns)
    
    def find_worst_k_days(self,k=20):
        return self.daily_returns.sort_values().head(k)
    
    def find_worst_k_months(self,k=3):
        return self.monthly_returns.sort_values().head(k)
    
    def find_worst_k_years(self,k=3):
        return self.yearly_returns.sort_values().head(k)

    def find_worst_k_weeks(self,k=3):
        return self.weekly_returns.sort_values().head(k)

    def find_worst_weeks(self,threshold=-0.1):
        return self.weekly_returns.loc[self.weekly_returns < threshold]
    
    def find_worst_months(self,threshold=-0.2):
        return self.monthly_returns.loc[self.monthly_returns < threshold]

    def show_today_return(self):
        print(self.daily_returns.tail(20))

def black_scholes_put(
        asset_price,
        strike_price,
        time_to_expiration,
        risk_free_rate,
        volatility
):
    """Calculate European put option price using Black-Scholes-Merton model
    
    Args:
        asset_price: Current price of the underlying asset
        strike_price: Option strike price
        time_to_expiration: Time to expiration in years
        risk_free_rate: Annual risk-free interest rate
        volatility: Annualized volatility of underlying asset

    Eurodollar futures traded at the Chicago Mercan-tile Exchange are often 
    used to determine a benchmark interest rate.
    """
    # Calculate d1 component for option pricing
    log_price_ratio = np.log(asset_price / strike_price)
    risk_adjusted_return = (risk_free_rate + 0.5 * volatility**2)
    d1_numerator = log_price_ratio + risk_adjusted_return * time_to_expiration
    d1_denominator = volatility * np.sqrt(time_to_expiration)
    d1 = d1_numerator / d1_denominator

    # d2 is derived from d1 with volatility time adjustment
    d2 = d1 - volatility * np.sqrt(time_to_expiration)

    # Probability calculations for option exercise and delta hedging
    prob_asset_price_above_strike = norm.cdf(-d2)
    prob_delta_hedging = norm.cdf(-d1)

    # Calculate put price components
    discounted_strike = (
        strike_price
        * np.exp(-risk_free_rate * time_to_expiration)
        * prob_asset_price_above_strike
    )
    asset_price_component = asset_price * prob_delta_hedging

    put_price = discounted_strike - asset_price_component
    return put_price

def taleb_result3_put(S, K, T, r, sigma, liquidity_adj=0.0, jump_risk=0.0):
    """
    Taleb Result3 改进的OTM Put定价公式
    核心改进：
    1. 波动率微笑调整
    2. 流动性溢价
    3. 跳跃风险补偿
    """
    # 基础波动率调整（波动率微笑）
    moneyness = K/S
    vol_smile_adj = 0.4 * (1 - moneyness)  # 虚值程度越大波动率越高
    
    # 流动性调整（bid-ask spread补偿）
    liquidity_premium = liquidity_adj * np.sqrt(1/T) if T > 0 else 0
    
    # 合成波动率
    effective_vol = sigma + vol_smile_adj + liquidity_premium
    
    # 跳跃风险补偿（短期期权更敏感）
    jump_adj = jump_risk * (1 / max(T, 1/365)) ** 0.5  # 时间越短跳跃影响越大
    
    # 调整后的定价计算
    d1 = (np.log(S/K) + (r + effective_vol**2/2)*T) / (effective_vol*np.sqrt(T))
    d2 = d1 - effective_vol*np.sqrt(T)
    
    base_price = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
    
    # 加入肥尾补偿
    tail_risk_adj = 0.2 * base_price * jump_adj
    
    return base_price + tail_risk_adj

class LeftTailWeeklyReturnPlotter:
    def __init__(self, ticker):
        self.ticker = ticker
        self.left_tail_weekly_returns = self.get_left_tail_weekly_returns()

    def get_left_tail_weekly_returns(self):
        volatility = VolatilityFacade(self.ticker)
        weekly_returns = volatility.weekly_returns
        negative_returns = weekly_returns[weekly_returns < 0]
        return negative_returns

    def fit_t_distribution_parameters(self):
        params = t.fit(self.left_tail_weekly_returns)
        return params
    
    def simulate_by_t_distribution_to_get_expected_minimal(self):
        params = self.fit_t_distribution_parameters()
        n_times = 10000
        sample_size = len(self.left_tail_weekly_returns)
        
        min_weekly_returns = []
        for _ in range(n_times):
            # Generate samples from t-distribution using the fitted parameters

            simulated_returns = t.rvs(*params, size=sample_size)
            min_weekly_returns.append(np.min(simulated_returns))

        expected_worst_weekly_returns = np.mean(min_weekly_returns)
        assert expected_worst_weekly_returns < -0.4
        return expected_worst_weekly_returns
    
    def plot(self):
        # Get the expected worst weekly return from simulation
        expected_worst = self.simulate_by_t_distribution_to_get_expected_minimal()
        
        params = self.fit_t_distribution_parameters()
        historical_worst = self.left_tail_weekly_returns.min()
        print(historical_worst)
        x = np.linspace(historical_worst, 0.1, 100)  # Only plot up to 0
        pdf = t.pdf(x, *params)
        
        plt.hist(
            self.left_tail_weekly_returns, 
            bins=100, 
            density=True, 
            alpha=0.6, 
            color='r', 
            label='Negative Weekly Returns')
        plt.plot(x, pdf, 'k-', linewidth=2, label='Fitted t-distribution (left tail)')
        
        # Add the expected worst weekly return as a dot
        plt.plot(expected_worst, t.pdf(expected_worst, *params), 'bo', markersize=10, 
                 label=f'Expected Worst Return: {expected_worst:.2%}')
        plt.plot(historical_worst, t.pdf(historical_worst, *params), 'o', color='lightblue', markersize=10, 
                 label=f'Historical Worst Return: {historical_worst:.2%}')
        
        # Add a vertical line at the expected worst return
        plt.axvline(x=expected_worst, color='blue', linestyle='--', alpha=0.5)
        
        plt.title(f'Left Tail Distribution of {self.ticker} Weekly Returns')
        plt.xlabel('Weekly Return')
        plt.ylabel('Density')
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.5)
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()
        plt.savefig("figures/historical_min_vs_expected_min.jpg")
        plt.close()
 

def black_scholes_prob(S, K, T, r, sigma):
    d2 = (np.log(S/K) + (r - 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.cdf(d2)

if __name__ == "__main__":
    S0 = 66
    K1 = 83.5
    K_sell = 70
    K_buy = 76
    sigma = 0.65  # TQQQ波动率
    T = 1/52
    r = 0.05  # 无风险利率
    
    probability_larger_than_K1 = black_scholes_prob(S0,K1,T,r,sigma)
    E1 = 8 + (83.5 - 83) * probability_larger_than_K1
    print("Scenario 1 without any risk gain is {}".format(E1))


    probability_larger_than_K_sell = black_scholes_prob(S0, K_sell,T, r, sigma)
    print(probability_larger_than_K_sell)
    # 70 - 76 
    pnl_in_1std = 100 * (1 - probability_larger_than_K_sell)
    print("Scenario 2 take 1std to 2std risk exposure is {}".format(pnl_in_1std))

    prob_assign2 = black_scholes_prob(S0, K_sell, T, r, sigma)
    prob_otm_assign = black_scholes_prob(S0, K_buy, T, r, sigma)
    pnl_assign_range = (70-83) * (prob_assign2 - prob_otm_assign) * 100 + 100
    print("pnl assign range is {}".format(pnl_assign_range))

    pnl_deep = (100 + 3*(S0*np.exp((r+0.5*sigma**2)*T) - K_buy)*100) * prob_otm_assign 
    
    pnl_exp = pnl_deep + pnl_assign_range + pnl_in_1std
    print("pnl expectation is {}".format(pnl_exp))
    # ltweekplotter = LeftTailWeeklyReturnPlotter("TQQQ")
    # ltweekplotter.plot()
    #histgram_plot_left_tail_monthly_return("TQQQ")
    #plot_extended_tail_distribution("SPY")
    # volatility = VolatilityFacade("TQQQ")
    # print(volatility.find_worst_k_weeks())
    # volatility.visualize_weekly_percentage_change()
    #print(volatility.daily_returns)
    #volatility.visualize_daily_percentage_change()
    #volatility.calculate_daily_volatility()
    #volatility.visualize_monthly_percentage_change()
    #volatility.visualize_yearly_percentage_change()

    #volatility.show_today_return()
    #print(volatility.find_worst_k_days(k=5))
    #print(volatility.find_worst_months(threshold=-0.3))    
    #print(volatility.find_worst_k_months(k=30))
    #print(volatility.find_worst_k_years(k=3))
    # Calendar year Return Check
    #calendar_returns = volatility.get_calendar_year_returns("UVXY")
    #print(calendar_returns)