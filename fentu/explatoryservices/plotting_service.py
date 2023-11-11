import statsmodels.api as sm
import matplotlib.pyplot as plt

def qq_plot(x):
    return sm.qqplot(x, line='45')
