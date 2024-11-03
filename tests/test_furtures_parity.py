import numpy as np
import matplotlib.pyplot as plt

# Parameters
current_spot_price = 90.85  # Current spot price of TLT
cost_of_carry = 0.5          # Assumed cost of carry per month
months_to_expiration = 3     # Time to expiration in months

# Calculate futures price based on spot price and cost of carry
futures_price = current_spot_price + (cost_of_carry * months_to_expiration)

# Price range for TLT
price_range = np.linspace(70, 110, 500)

# Calculate P/L for short futures position
def short_futures_pl(price):
    return (futures_price - price)

# Calculate total P/L for the short futures position
total_pl = short_futures_pl(price_range)

# Plotting the P/L graph
plt.figure(figsize=(10, 6))
plt.plot(price_range, total_pl, label='Short TLT Futures Position', color='blue')
plt.axhline(0, color='black', lw=0.5, ls='--')
plt.title('Profit and Loss Graph for Short TLT Futures Position')
plt.xlabel('Price of TLT')
plt.ylabel('Profit/Loss')
plt.legend()
plt.grid()
plt.xlim(70, 110)
plt.ylim(-20, 20)
plt.show()