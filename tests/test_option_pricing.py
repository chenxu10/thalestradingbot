import pytest
import numpy as np

from datetime import date
from fentu.strategyservices.black_scholes_model import BlackScholesPricer, OptionData
from scipy.stats import norm

class TestBlackScholesPricer:
    @pytest.fixture
    def bspricer(self):
        bspricer = BlackScholesPricer()
        return bspricer
        
    def test_price_empty(self, bspricer):
        with pytest.raises(Exception):
            bspricer.price_empty()
    
    def test_how_far_asset_price_to_strike_price(self, bspricer):
        opdata = OptionData(89,91,30,0.05,0.1)
        tol = 0.01
        assert abs(bspricer.how_far_asset_price_to_strike_price(opdata) - (-0.022)) < tol
    
    def test_what_is_expected_return_adjusted_for_riskness(self, bspricer):
        opdata = OptionData(89,91,30,0.05,0.1)
        tol = 0.01
        assert abs(bspricer.what_is_expected_return_adjusted_for_riskness(opdata) - 1.65) < tol

    def test_d1(self, bspricer):
        opdata = OptionData(89,91,30,0.05,0.1)
        tol = 0.01
        result = bspricer.calculate_d1(opdata)
        expected_result = 2.972
        assert abs(result - expected_result) < tol

    def test_d2(self, bspricer):
        opdata = OptionData(89,91,30,0.05,0.1)
        tol = 0.01
        result = bspricer.calculate_d2(opdata)
        expected_result = 2.972 - 0.1 * np.sqrt(30)
        assert abs(result - expected_result) < tol

    def test_nostrike_change_at_expiration(self, bspricer):
        opdata = OptionData(95,95,0,0.041,0.02)
        assert bspricer.nostrike_change_at_expiration(opdata) == 0
    
    def test_calculate_option_price_given(self, bspricer):
        opdata = OptionData(89,91,30,0.05,0.1)
        tol = 0.01
        d1 = 2.972
        d2 = 2.423
        result = bspricer.calculate_option_price_given(opdata, d1, d2)
        expected_result = 89*norm.cdf(2.972) - 91*np.exp(-0.05*30)*norm.cdf(2.423)
        assert abs(result - expected_result) < tol

    def test_option_pricing_formula(self, bspricer):
        opdata = OptionData(42,40,0.5,0.1,0.2)
        tol = 0.01
        expected_price = 4.76
        assert abs(bspricer.option_pricing_formula(opdata,"call") - expected_price) < tol