import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import math

def black_scholes_call(S, K, T, r, sigma):
    """Black-Scholes call option pricing"""
    if T <= 0:
        return max(S - K, 0)
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return call_price

def black_scholes_put(S, K, T, r, sigma):
    """Black-Scholes put option pricing"""
    if T <= 0:
        return max(K - S, 0)
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    put_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return put_price

def fourth_moment_bet_pnl(S_range, S0=100.5, T=0.25, r=0.05, sigma=0.2):
    """
    Calculate P&L for fourth moment bet strategy described in plan.md
    
    Strategy:
    - Buy OTM puts and calls in large amounts
    - Sell smaller amounts of ATM straddles
    - Satisfies credit rule (generates positive cash flow initially)
    """
    
    # Define strikes
    ATM_strike = S0  # At-the-money
    OTM_put_strike = S0 * 0.85  # 15% out-of-the-money put
    OTM_call_strike = S0 * 1.15  # 15% out-of-the-money call
    
    # Position sizes (ratio backspread structure)
    long_otm_puts = 3  # Large amount of OTM puts
    long_otm_calls = 3  # Large amount of OTM calls
    short_atm_straddles = 2  # Smaller amount of ATM straddles
    
    # Calculate initial premiums at t=0
    initial_otm_put_premium = black_scholes_put(S0, OTM_put_strike, T, r, sigma)
    initial_otm_call_premium = black_scholes_call(S0, OTM_call_strike, T, r, sigma)
    initial_atm_call_premium = black_scholes_call(S0, ATM_strike, T, r, sigma)
    initial_atm_put_premium = black_scholes_put(S0, ATM_strike, T, r, sigma)
    
    # Initial cash flow (should be positive - credit rule)
    initial_cash_flow = (
        -long_otm_puts * initial_otm_put_premium
        - long_otm_calls * initial_otm_call_premium
        + short_atm_straddles * (initial_atm_call_premium + initial_atm_put_premium)
    )
    
    # Calculate P&L at time t
    pnl_t = []
    for S in S_range:
        otm_put_value = black_scholes_put(S, OTM_put_strike, T, r, sigma)
        otm_call_value = black_scholes_call(S, OTM_call_strike, T, r, sigma)
        atm_call_value = black_scholes_call(S, ATM_strike, T, r, sigma)
        atm_put_value = black_scholes_put(S, ATM_strike, T, r, sigma)
        
        position_value = (
            long_otm_puts * otm_put_value
            + long_otm_calls * otm_call_value
            - short_atm_straddles * (atm_call_value + atm_put_value)
        )
        
        pnl = initial_cash_flow + position_value
        pnl_t.append(pnl)
    
    # Calculate P&L at time t+3 (assuming 3 days = 3/365 years)
    T_plus_3 = max(T - 3/365, 0.001)  # Avoid negative time
    pnl_t_plus_3 = []
    for S in S_range:
        if T_plus_3 <= 0.001:
            # At expiration
            otm_put_value = max(OTM_put_strike - S, 0)
            otm_call_value = max(S - OTM_call_strike, 0)
            atm_call_value = max(S - ATM_strike, 0)
            atm_put_value = max(ATM_strike - S, 0)
        else:
            otm_put_value = black_scholes_put(S, OTM_put_strike, T_plus_3, r, sigma)
            otm_call_value = black_scholes_call(S, OTM_call_strike, T_plus_3, r, sigma)
            atm_call_value = black_scholes_call(S, ATM_strike, T_plus_3, r, sigma)
            atm_put_value = black_scholes_put(S, ATM_strike, T_plus_3, r, sigma)
        
        position_value = (
            long_otm_puts * otm_put_value
            + long_otm_calls * otm_call_value
            - short_atm_straddles * (atm_call_value + atm_put_value)
        )
        
        pnl = initial_cash_flow + position_value
        pnl_t_plus_3.append(pnl)
    
    return pnl_t, pnl_t_plus_3, initial_cash_flow

def plot_fourth_moment_bet():
    """
    Plot the fourth moment bet P&L profile mimicking Figure 24.1
    """
    # Market parameters
    S0 = 100.5  # Current market price
    
    # Stock price range for plotting - expanded to show extreme profit zones
    S_range = np.linspace(70, 140, 200)
    
    # Calculate P&L profiles
    pnl_t, pnl_t_plus_3, initial_cash_flow = fourth_moment_bet_pnl(S_range, S0)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot both time scenarios
    plt.plot(S_range, pnl_t, 'b-', linewidth=2, label='t (Current Time)')
    plt.plot(S_range, pnl_t_plus_3, 'r--', linewidth=2, label='t+3 (3 Days Later)')
    
    # Add current market price line
    plt.axvline(x=S0, color='green', linestyle=':', alpha=0.7, label=f'Current Price ({S0})')
    
    # Add strike price lines for OTM options
    OTM_put_strike = S0 * 0.85
    OTM_call_strike = S0 * 1.15
    plt.axvline(x=OTM_put_strike, color='red', linestyle='--', alpha=0.5, label=f'OTM Put Strike ({OTM_put_strike:.2f})')
    plt.axvline(x=OTM_call_strike, color='blue', linestyle='--', alpha=0.5, label=f'OTM Call Strike ({OTM_call_strike:.2f})')
    
    # Add break-even line
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Formatting
    plt.xlabel('Stock Price', fontsize=12)
    plt.ylabel('P&L', fontsize=12)
    plt.title('Fourth Moment Bet: Ratio Backspread with OTM Options\n(Long Vol of Vol Strategy)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    
    # Add annotations
    plt.annotate(f'Initial Credit: ${initial_cash_flow:.2f}', 
                xy=(0.02, 0.98), xycoords='axes fraction',
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    # Find approximate profit zones
    OTM_put_strike = S0 * 0.85
    OTM_call_strike = S0 * 1.15
    
    plt.annotate('OTM Put Profit Zone:\nExtreme downside moves\n(Price < $85)', 
                xy=(75, max(pnl_t) * 0.8), xycoords='data',
                fontsize=9, ha='center',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.annotate('OTM Call Profit Zone:\nExtreme upside moves\n(Price > $115)', 
                xy=(130, max(pnl_t) * 0.8), xycoords='data',
                fontsize=9, ha='center',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.annotate('Loss Zone:\nSmall moves around current price\n(Low volatility)', 
                xy=(S0, min(pnl_t) * 0.8), xycoords='data',
                fontsize=9, ha='center',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    
    plt.tight_layout()
    plt.show()
    
    # Print strategy details
    print("="*60)
    print("FOURTH MOMENT BET STRATEGY DETAILS")
    print("="*60)
    print(f"Current Market Price: ${S0}")
    print(f"Strategy: Ratio Backspread (Long Vol of Vol)")
    print(f"Initial Credit Generated: ${initial_cash_flow:.2f}")
    print("\nPosition Structure:")
    print(f"- Long 3 OTM Puts (Strike: ${S0 * 0.85:.2f})")
    print(f"- Long 3 OTM Calls (Strike: ${S0 * 1.15:.2f})")
    print(f"- Short 2 ATM Straddles (Strike: ${S0:.2f})")
    print("\nStrategy Characteristics:")
    print("- Profits from large moves in either direction")
    print("- Loses money in low volatility scenarios")
    print("- Benefits from volatility of volatility")
    print("- Time decay hurts the position")

if __name__ == "__main__":
    plot_fourth_moment_bet() 