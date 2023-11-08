"""
This script tries to abstrat a pattern of using bootstrap to generate sample paths
to travel through history of what happened in the past and more importantly what
could hava happened in the past. 

Author: Xu Shen
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import bootstrap
import numpy as np
from scipy.stats import norm
rng = np.random.default_rng()


# Generate sample paths
np.random.seed(42) 
n_paths = 100
n_years = 10
returns = np.random.normal(loc=0.07, scale=0.15, size=(n_paths, n_years))
print(returns.shape)
paths = np.cumprod(np.insert(returns, 0, 1, axis=1), axis=1)
print(paths.shape)


# Add real data 
real_returns = [0.26, 0.15, 0.02, 0.16, 0.32, 0.13, 0.05, 0.11, 0.21, 0.28]
real_path = np.cumprod(np.insert(real_returns, 0, 1))
paths = np.insert(paths, 0, real_path, axis=0)
print(paths.shape)


# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for path in paths:
    ax1.plot(range(n_years+1), path, color='grey', alpha=0.5)
ax1.plot(range(n_years+1), real_path, color='k')

ax1.set_title('Simulated S&P500 Return Paths')
ax1.set_ylabel('Cumulative Return')

ax2.hist(returns.flatten(), bins=30, orientation='horizontal')
ax2.axhspan(np.percentile(returns, 5), np.median(returns), color='grey', alpha=0.5)
ax2.axvline(np.median(returns), color='k', linestyle='dashed')
ax2.set_xlabel('Return')
ax2.set_yticklabels([])
ax2.set_xlabel('Density')

plt.tight_layout()
plt.show()