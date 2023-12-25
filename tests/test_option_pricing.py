import pytest
import numpy as np

from datetime import date
from fentu.strategyservices.black_scholes_model import BlackScholesPricer, OptionData
from scipy.stats import norm

class TestBlackScholesPricer:
    @pytest.fixture
    def bspricer(self):
        opdata = OptionData(89,91,30,0.05,0.1)
        bspricer = BlackScholesPricer(opdata)
        return bspricer
    
    @pytest.fixture
    def bspricer_2(self):
        opdata = OptionData(42,40,0.5,0.1,0.2)
        bspricer_2 = BlackScholesPricer(opdata)
        return bspricer_2
        
    def test_price_empty(self, bspricer):
        with pytest.raises(Exception):
            bspricer.price_empty()
    
    def test_how_far_asset_price_to_strike_price(self, bspricer):
        tol = 0.01
        assert abs(bspricer.how_far_asset_price_to_strike_price() - (-0.022)) < tol
    
    def test_what_is_expected_return_adjusted_for_riskness(self, bspricer):
        tol = 0.01
        assert abs(bspricer.what_is_expected_return_adjusted_for_riskness() - 1.65) < tol

    def test_d1(self, bspricer):
        tol = 0.01
        result = bspricer.calculate_d1()
        expected_result = 2.972
        assert abs(result - expected_result) < tol

    def test_d2(self, bspricer):
        tol = 0.01
        result = bspricer.calculate_d2()
        expected_result = 2.972 - 0.1 * np.sqrt(30)
        assert abs(result - expected_result) < tol

    def test_nostrike_change_at_expiration(self, bspricer):
        assert bspricer.nostrike_change_at_expiration() == 0
    
    def test_calculate_option_price_given(self, bspricer):
        tol = 0.01
        d1 = 2.972
        d2 = 2.423
        result = bspricer.calculate_option_price_given(d1, d2)
        expected_result = 89*norm.cdf(2.972) - 91*np.exp(-0.05*30)*norm.cdf(2.423)
        assert abs(result - expected_result) < tol

    @pytest.mark.usefixtures("bspricer_2")
    def test_option_pricing_formula(self, bspricer_2):
        tol = 0.01
        expected_price = 4.76
        assert abs(bspricer_2.option_pricing_formula("call") - expected_price) < tol