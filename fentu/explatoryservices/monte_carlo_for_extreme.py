import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, t
from fentu.explatoryservices.volcalculator import VolatilityFacade

def find_std_crossover_point(ticker, start=0.1, end=1.5, step=0.05, n_times=10000, filter_returns=None):
    """
    Find the quantile where the expected standard deviation crosses below historical standard deviation.
    
    Args:
        ticker (str): The stock ticker symbol
        start (float): Starting quantile for search
        end (float): Ending quantile for search
        step (float): Step size for quantile increments
        n_times (int): Number of simulations for each quantile
        filter_returns (callable, optional): Function to filter returns data
        
    Returns:
        tuple: (crossover_quantile, expected_std, historical_std)
              If no crossover is found, returns (None, None, historical_std)
    """
    analyzer = RightTailWeeklyReturnAnalyzer(ticker)
    if filter_returns:
        analyzer.returns = filter_returns(analyzer.returns)
    
    return analyzer.find_crossover_quantile(start, end, step, n_times)


class WeeklyReturnAnalyzer:
    """Base class for analyzing weekly returns distributions"""
    def __init__(self, ticker):
        self.ticker = ticker
        self.returns = self._get_returns()
        
    def _get_returns(self):
        """Get the specific tail of weekly returns based on subclass implementation"""
        volatility = VolatilityFacade(self.ticker)
        weekly_returns = volatility.weekly_returns
        return self._filter_returns(weekly_returns)
    
    def _filter_returns(self, weekly_returns):
        """Filter returns based on tail type - to be implemented by subclasses"""
        raise NotImplementedError
        
    def fit_t_distribution_parameters(self):
        """Fit t-distribution to the returns data"""
        params = t.fit(self.returns)
        return params
    
    def simulate_t_distribution(self, n_times=10000):
        """Simulate returns using fitted t-distribution"""
        params = self.fit_t_distribution_parameters()
        sample_size = len(self.returns)
        
        simulated_stats = []
        for _ in range(n_times):
            simulated_returns = t.rvs(*params, size=sample_size)
            # Statistic calculation to be implemented by subclasses
            stat = self._calculate_statistic(simulated_returns)
            simulated_stats.append(stat)
            
        expected_value = np.mean(simulated_stats)
        return expected_value
    
    def _calculate_statistic(self, returns):
        """Calculate desired statistic from returns - to be implemented by subclasses"""
        raise NotImplementedError


class RightTailWeeklyReturnAnalyzer(WeeklyReturnAnalyzer):
    """Analyzes the right (positive) tail of weekly returns distribution"""
    
    def _filter_returns(self, weekly_returns):
        """Filter for positive returns (right tail)"""
        return weekly_returns
        #return weekly_returns[weekly_returns > 0]
    
    def _calculate_statistic(self, returns):
        """Calculate standard deviation for right tail distribution"""
        return np.std(returns)
    
    def get_expected_standard_deviation(self):
        """Get the expected standard deviation from simulated right tail returns"""
        return self.simulate_t_distribution()
    
    def get_quantile_standard_deviation(self, quantile, n_times=10000):
        """
        Calculate a specific quantile of standard deviation through simulation.
        
        Args:
            quantile (float): The quantile to find (between 0 and 1)
            n_times (int): Number of simulations to run
            
        Returns:
            float: The standard deviation at the specified quantile
        """
        params = self.fit_t_distribution_parameters()
        sample_size = len(self.returns)
        
        simulated_stds = []
        for _ in range(n_times):
            simulated_returns = t.rvs(*params, size=sample_size)
            simulated_stds.append(np.std(simulated_returns))
        
        # Sort the simulated standard deviations and find the specified quantile
        simulated_stds.sort()
        quantile_index = int(quantile * len(simulated_stds))
        return simulated_stds[quantile_index]
    
    def find_crossover_quantile(self, start=0.1, end=1.5, step=0.05, n_times=10000):
        """
        Find the quantile where the expected standard deviation crosses below historical standard deviation.
        
        Args:
            start (float): Starting quantile for search
            end (float): Ending quantile for search
            step (float): Step size for quantile increments
            n_times (int): Number of simulations for each quantile
            
        Returns:
            tuple: (crossover_quantile, expected_std, historical_std)
                  If no crossover is found, returns (None, None, historical_std)
        """
        historical_std = np.std(self.returns)
        results = []
        
        # Calculate standard deviations at various quantiles
        quantiles = np.arange(start, end + step, step)
        for q in quantiles:
            expected_std = self.get_quantile_standard_deviation(q, n_times)
            results.append((q, expected_std))
            print(f"Quantile {q:.2f}: Expected Std = {expected_std:.4f}, Historical Std = {historical_std:.4f}")
            
            # Check if we've crossed the threshold
            if expected_std < historical_std:
                return q, expected_std, historical_std
        
        # If we reached here, no crossover was found
        return None, None, historical_std
    
    def get_half_standard_deviation(self, n_times=10000):
        """
        Calculate 0.5std through simulation.
        
        Instead of multiplying the full standard deviation by 0.5,
        this method simulates returns and calculates the 0.5 quantile
        of the empirical standard deviation distribution.
        """
        return self.get_quantile_standard_deviation(0.9, n_times)


class LeftTailWeeklyReturnAnalyzer(WeeklyReturnAnalyzer):
    """Analyzes the left (negative) tail of weekly returns distribution"""
    
    def _filter_returns(self, weekly_returns):
        """Filter for negative returns (left tail)"""
        return weekly_returns[weekly_returns < 0]
    
    def _calculate_statistic(self, returns):
        """Calculate minimum value for left tail distribution"""
        return np.min(returns)
    
    def get_expected_minimum(self):
        """Get the expected minimum from simulated left tail returns"""
        return self.simulate_t_distribution()
    
    def plot(self):
        """Plot the left tail distribution with expected minimum value"""
        # Get the expected worst weekly return from simulation
        expected_worst = self.get_expected_minimum()
        
        params = self.fit_t_distribution_parameters()
        historical_worst = self.returns.min()
        print(f"Historical worst return: {historical_worst:.2%}")
        
        x = np.linspace(historical_worst, 0.1, 100)  # Only plot up to 0.1
        pdf = t.pdf(x, *params)
        
        plt.hist(
            self.returns, 
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


if __name__ == "__main__":
    ticker = "TQQQ"
    
    # Analyze right tail (positive) returns
    right_tail_analyzer = RightTailWeeklyReturnAnalyzer(ticker)
    expected_std = right_tail_analyzer.get_expected_standard_deviation()
    historical_std = np.std(right_tail_analyzer.returns)
    
    print(f"Expected standard deviation of weekly returns: {expected_std:.4f}")
    print(f"Historical standard deviation of weekly returns: {historical_std:.4f}")

    # Find the crossover point where expected_std < historical_std
    # Using the standalone function
    print("\nSearching for crossover point...")
    crossover_q, crossover_std, hist_std = find_std_crossover_point(
        ticker, start=0.25, end=1.5, step=0.05)
    
    if crossover_q is not None:
        print(f"\nCrossover found at quantile {crossover_q:.2f}")
        print(f"At this quantile, expected std ({crossover_std:.4f}) < historical std ({hist_std:.4f})")
    else:
        print("\nNo crossover found in the specified range.")
    
    # Analyze left tail (negative) returns
    #left_tail_analyzer = LeftTailWeeklyReturnAnalyzer(ticker)
    #expected_min = left_tail_analyzer.get_expected_minimum()
    #print(f"Expected minimum weekly return: {expected_min:.2%}")
    
    # Visualize the left tail distribution
    #left_tail_analyzer.plot()
    
