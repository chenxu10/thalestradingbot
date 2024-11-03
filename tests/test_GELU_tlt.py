import numpy as np
import matplotlib.pyplot as plt

# Parameters
current_price = 90.87  # Current price of TLT
call_strike = 91.00     # Strike price of the ATM call option sold
call_premium = 1.33     # Premium received from selling the ATM call (assumed)
put_strike = 88.50      # Strike price of the OTM put option bought
put_premium = 0.52      # Premium paid for each OTM put
num_puts = 2            # Number of OTM puts bought

# Price range for TLT
price_range = np.linspace(70, 110, 500)

# Calculate P/L for Covered Call
def covered_call_pl(price):
    if price <= call_strike:
        return (price - current_price) + call_premium
    else:
        return (call_strike - current_price) + call_premium

# Calculate P/L for OTM Puts
def otm_puts_pl(price):
    if price >= put_strike:
        return -num_puts * put_premium
    else:
        return (put_strike - price) * num_puts - (num_puts * put_premium)

# Calculate total P/L for the combined strategy
total_pl = []
for price in price_range:
    cc_pl = covered_call_pl(price)
    op_pl = otm_puts_pl(price)
    total_pl.append(cc_pl + op_pl)

# Plotting the P/L graph
plt.figure(figsize=(10, 6))
plt.plot(price_range, total_pl, label='Covered Call + 3 OTM Puts', color='blue')
plt.axhline(0, color='black', lw=0.5, ls='--')
plt.axvline(call_strike, color='red', lw=0.5, ls='--', label='Call Strike ($91.00)')
plt.axvline(put_strike, color='green', lw=0.5, ls='--', label='Put Strike ($85.00)')
plt.title('Profit and Loss Graph for Covered Call + 3 OTM Puts')
plt.xlabel('Price of TLT')
plt.ylabel('Profit/Loss')
plt.legend()
plt.grid()
plt.xlim(70, 110)
plt.ylim(-10, 10)
plt.show()