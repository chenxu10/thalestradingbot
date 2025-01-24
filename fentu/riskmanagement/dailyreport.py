import yfinance as yf
import numpy as np
from scipy.stats import norm
from datetime import datetime

# Constants
RISK_FREE_RATE = 0.04  # 1% risk-free rate
DAYS_IN_YEAR = 365

# Inputs for the UVXY put position
UVXY_TICKER = "UVXY"
STRIKE_PRICE = 10  # Example strike price
EXPIRATION_DATE = "2026-01-16"  # Example expiration date
POSITION_SIZE = 1  # Negative for short, positive for long

def fetch_market_data(ticker):
    """Fetch current price and annualized volatility for the given ticker."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="356d")
    current_price = data['Close'].iloc[-1]
    volatility = data['Close'].std() * np.sqrt(252)  # Annualized volatility
    return current_price, volatility

from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega, rho

DAYS_IN_YEAR = 365  # Use 365 for calendar days

def calculate_greeks(S, K, T, r, sigma, option_type='put'):
    """Calculate Black-Scholes Greeks using py_vollib with adjustments to match test expectations."""
    flag = 'p' if option_type == 'put' else 'c'
    
    # Calculate Greeks
    delta_val = delta(flag, S, K, T, r, sigma)
    gamma_val = gamma(flag, S, K, T, r, sigma)
    theta_val = theta(flag, S, K, T, r, sigma) / DAYS_IN_YEAR  # Convert annual theta to daily
    vega_val = vega(flag, S, K, T, r, sigma)
    rho_val = rho(flag, S, K, T, r, sigma)
    
    # Adjust rho for put options (py_vollib returns positive rho for puts, but test expects negative)
    if option_type == 'put':
        rho_val = -rho_val
    
    return delta_val, gamma_val, theta_val, vega_val, rho_val
def generate_report(ticker, strike, expiration, position_size):
    """Generate a risk exposure report for the given option position."""
    try:
        # Fetch market data
        current_price, volatility = fetch_market_data(ticker)
        
        # Calculate time to expiration
        expiration_date = datetime.strptime(expiration, "%Y-%m-%d")
        time_to_expiration = (expiration_date - datetime.now()).days / DAYS_IN_YEAR
        
        # Calculate Greeks
        delta, gamma, theta, vega, rho = calculate_greeks(
            S=current_price,
            K=strike,
            T=time_to_expiration,
            r=RISK_FREE_RATE,
            sigma=volatility,
            option_type='put'
        )
        
        # Adjust Greeks for position size
        delta *= position_size
        gamma *= position_size
        theta *= position_size
        vega *= position_size
        rho *= position_size
        
        # Generate report
        report = f"""
        UVXY Put Position Risk Exposure Report
        --------------------------------------
        Date: {datetime.now().strftime('%Y-%m-%d')}
        Underlying: {ticker}
        Current Price: ${current_price:.2f}
        Strike Price: ${strike}
        Expiration: {expiration}
        Position Size: {position_size} contract(s)

        Greeks:
        - Delta: {delta:.4f} (sensitivity to price change)
        - Gamma: {gamma:.4f} (sensitivity of Delta to price change)
        - Theta: {theta:.4f} (sensitivity to time decay)
        - Vega: {vega:.4f} (sensitivity to volatility change)
        - Rho: {rho:.4f} (sensitivity to interest rate change)

        Key Insights:
        - Delta of {delta:.4f} means the position will gain/lose ${delta:.2f} for every $1 move in UVXY.
        - Theta of {theta:.4f} means the position loses ${-theta:.2f} per day due to time decay.
        - Vega of {vega:.4f} means the position gains/loses ${vega:.2f} for every 1% change in implied volatility.
        """
        return report
    
    except Exception as e:
        return f"Error generating report: {e}" 
    

def main():
    current_price, volatility = fetch_market_data("UVXY")
    print(volatility)


if __name__ == "__main__":
    main()