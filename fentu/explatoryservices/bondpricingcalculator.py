import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class TLTFairValuePricing:
    def __init__(self, current_price, coupon_rate, maturity_date, risk_free_rate):
        """
        Initialize TLT Fair Value Pricing Calculator
        
        Parameters:
        - current_price: Current market price of the bond
        - coupon_rate: Annual coupon rate (as a decimal)
        - maturity_date: Maturity date of the bond
        - risk_free_rate: Current risk-free interest rate (as a decimal)
        """
        self.current_price = current_price
        self.coupon_rate = coupon_rate
        self.maturity_date = maturity_date
        self.risk_free_rate = risk_free_rate
    
    def calculate_fair_value(self, face_value=1000):
        """
        Calculate the fair value using discounted cash flow method
        
        Parameters:
        - face_value: Par value of the bond (default 1000)
        
        Returns:
        - Fair value of the bond
        """
        # Calculate time to maturity in years
        today = datetime.now()
        time_to_maturity = (self.maturity_date - today).days / 365.25
        
        # Calculate periodic coupon payment
        annual_coupon_payment = face_value * self.coupon_rate
        
        # Create cash flow series
        cash_flows = []
        for t in range(1, int(time_to_maturity * 2) + 1):
            # Semi-annual coupon payments
            cash_flows.append(annual_coupon_payment / 2)
        
        # Add face value at maturity
        cash_flows[-1] += face_value
        
        # Discount cash flows
        discount_factors = [
            1 / ((1 + self.risk_free_rate/2) ** t) 
            for t in range(1, len(cash_flows) + 1)
        ]
        
        # Calculate present value of cash flows
        present_values = [cf * df for cf, df in zip(cash_flows, discount_factors)]
        fair_value = sum(present_values)
        
        return fair_value
    
    def get_valuation_metrics(self):
        """
        Generate comprehensive valuation metrics
        
        Returns:
        - Dictionary of valuation insights
        """
        fair_value = self.calculate_fair_value()
        
        return {
            'Current Price': self.current_price,
            'Fair Value': fair_value,
            'Pricing Difference': fair_value - self.current_price,
            'Percentage Difference': ((fair_value - self.current_price) / self.current_price) * 100
        }

# Example usage
def main():
    # Sample parameters (these should be updated with real-time data)
    current_price = 90.24  # Current market price
    coupon_rate = 0.0276    # 4.75% annual coupon rate
    maturity_date = datetime(2049, 1, 1)  # Example maturity date
    risk_free_rate = 0.042  # 4.50% risk-free rate
    
    # Create pricing calculator
    tlt_pricing = TLTFairValuePricing(
        current_price, 
        coupon_rate, 
        maturity_date, 
        risk_free_rate
    )
    
    # Get valuation metrics
    valuation_metrics = tlt_pricing.get_valuation_metrics()
    
    # Print results
    for key, value in valuation_metrics.items():
        print(f"{key}: {value:.2f}")

if __name__ == "__main__":
    #
    main()