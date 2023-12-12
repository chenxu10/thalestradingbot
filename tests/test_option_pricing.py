import pytest

from datetime import date
from fentu.strategyservices.black_scholes_model import BlackScholesPricer, OptionData

class TestBlackScholesPricer:
    @pytest.fixture
    def bspricer(self):
        bspricer = BlackScholesPricer()
        return bspricer
        
    def test_price_empty(self, bspricer):
        with pytest.raises(Exception):
            bspricer.price_empty()
    
    def test_how_far_asset_price_to_strike_price(self, bspricer):
        opdata = OptionData(95,95,0,0.041,0.02)
        assert bspricer.how_far_asset_price_to_strike_price(opdata) == 0

    def test_nostrike_change_at_expiration(self, bspricer):
        opdata = OptionData(95,95,0,0.041,0.02)
        assert bspricer.nostrike_change_at_expiration(opdata) == 0
    
    def test_option_pricing_formula(self, bspricer):
        opdata = OptionData(42,40,0.5,0.1,0.2)
        tol = 0.01
        assert abs(bspricer.option_pricing_formula(opdata,"call") - 4.76) < tol