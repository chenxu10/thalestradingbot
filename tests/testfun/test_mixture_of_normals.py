import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

plt.rcParams['font.sans-serif'] = ['SimHei']  # Chinese display
plt.figure(figsize=(15, 10))

# Example 1: Weather Insurance (Left Skew)
plt.subplot(3, 2, 1)
x = np.linspace(-10, 5, 500)
dist1 = norm(0, 1).pdf(x) * 0.8  # Sunny days N(0,1)
dist2 = norm(-5, 3).pdf(x) * 0.2  # Storms N(-5,3)
plt.plot(x, dist1+dist2, 'r', lw=2)
plt.fill_between(x[x<-3], dist1[x<-3]+dist2[x<-3], color='tomato', alpha=0.3)
plt.title('Weather Insurance Distribution\n(Left Heavy Tail)', fontsize=10)
plt.annotate('Storm Risk Zone', xy=(-6,0.01), xytext=(-9,0.03),
             arrowprops=dict(facecolor='red', shrink=0.05))

# Example 2: Exam Scores (Right Skew)
plt.subplot(3, 2, 3)
x = np.linspace(40, 110, 500)
dist1 = norm(70, 10).pdf(x) * 0.9  # Average students
dist2 = norm(95, 5).pdf(x) * 0.1  # Top students
plt.plot(x, dist1+dist2, 'g', lw=2)
plt.fill_between(x[x>90], dist1[x>90]+dist2[x>90], color='lime', alpha=0.3)
plt.title('Exam Score Distribution\n(Right Heavy Tail)', fontsize=10)
plt.annotate('Top Students Area', xy=(98,0.02), xytext=(80,0.04),
             arrowprops=dict(facecolor='green', shrink=0.05))

# Example 3: Traffic Flow (Bimodal)
plt.subplot(3, 2, 5)
x = np.linspace(0, 80, 500)
dist1 = norm(50, 10).pdf(x) * 0.7  # Weekdays
dist2 = norm(20, 30).pdf(x) * 0.3  # Holidays
plt.plot(x, dist1+dist2, 'b', lw=2)
plt.fill_between(x[x<30], dist1[x<30]+dist2[x<30], color='royalblue', alpha=0.3)
plt.title('Traffic Flow Distribution\n(Bimodal)', fontsize=10)
plt.annotate('Congestion Risk', xy=(15,0.015), xytext=(30,0.03),
             arrowprops=dict(facecolor='blue', shrink=0.05))

# CDF comparison
for i, col in enumerate(['r','g','b']):
    plt.subplot(3, 2, 2*(i+1))
    x = np.linspace(-10 if i==0 else 40 if i==1 else 0, 
                   5 if i==0 else 110 if i==1 else 80, 500)
    dist = eval(f"dist1+dist2")  # Reuse distributions
    plt.plot(x, np.cumsum(dist)/sum(dist), col, lw=2)
    plt.title(['Weather Insurance CDF','Exam Scores CDF','Traffic Flow CDF'][i], fontsize=10)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()