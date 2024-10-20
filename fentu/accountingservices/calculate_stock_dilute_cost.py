"""
This script calculated the breakeven price or diluted cost
for the spot equity you owned

Author: Xu Shen <xs286@cornell.edu>
"""

class DilutedCostCalculator:
    def __init__(self, data):
        self.status_end_state = data["end_state"]
        self.cur_diluted_cost = data["cur_diluted_cost"]
        self.cur_position_after_option_change = data["cur_position"]
        self.premium = data["premium"]
        self.strikeprice = data["strikeprice"]
        self.volume = data["volume"]
        self.option_type = data["type"]
        self.closeprice = data["closeorderprice"]

    def calculate(self):
        if self.volume < 0:
            self.volume = abs(self.volume)
            return self._calculate_short_new_diluted_cost()
        else:
            return self._calculate_long_new_diluted_cost()

    def _calculate_long_new_diluted_cost(self):
        if self.status_end_state == "filled":
            return self._calculate_long_filled_diluted_cost()
        
    def _calculate_short_new_diluted_cost(self):
        if self.status_end_state == "filled":
            return self._calculate_short_filled_diluted_cost()
        elif self.status_end_state == "expired":
            return self._calculate_not_exercised_diluted_cost()
        elif self.status_end_state == "exercised":
            return self._calculate_exercised_diluted_cost()
    
    def _calculate_long_filled_diluted_cost(self):
        total_buy_cost = self.cur_diluted_cost * self.cur_position_after_option_change
        + self.premium
        print(total_buy_cost)
        print(total_buy_cost/self.cur_position_after_option_change)
        return total_buy_cost / self.cur_position_after_option_change

    def _calculate_short_filled_diluted_cost(self):
        total_buy_cost = self.cur_diluted_cost * self.cur_position_after_option_change - \
            self.premium + self.closeprice
        return total_buy_cost / self.cur_position_after_option_change

    def _calculate_not_exercised_diluted_cost(self):
        if self.cur_position_after_option_change == 0:
            return -self.premium
        return self.cur_diluted_cost - self.premium / self.cur_position_after_option_change

    def _calculate_exercised_diluted_cost(self):
        exercised_shares = self.volume * 100
        if self.cur_position_after_option_change == 0:
            return self.strikeprice - self.premium / (self.volume * 100)

        total_buy_cost = self._calculate_total_buy_cost(exercised_shares)
        return (total_buy_cost - self.premium) / self.cur_position_after_option_change

    def _calculate_total_buy_cost(self, exercised_shares):
        if self.option_type == "put":
            return (self.strikeprice * exercised_shares +
                    self.cur_diluted_cost * (self.cur_position_after_option_change - exercised_shares))
        elif self.option_type == "call":
            return (self.cur_diluted_cost * (self.cur_position_after_option_change + exercised_shares) -
                    self.strikeprice * exercised_shares)


