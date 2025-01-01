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
        total_buy_cost = self.cur_diluted_cost * self.cur_position_after_option_change \
            + (self.premium - self.closeprice)
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

def get_float_input(prompt):
    """Helper function to get valid float input"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number")

def get_int_input(prompt):
    """Helper function to get valid integer input"""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid integer")

def get_choice_input(prompt, choices):
    """Helper function to get valid choice from list"""
    while True:
        value = input(prompt).lower()
        if value in choices:
            return value
        print(f"Please enter one of: {', '.join(choices)}")


def main():
    """
    Interactive command line interface for calculating diluted cost.
    """
    print("\n=== Diluted Cost Calculator ===\n")
    
    # Get all inputs interactively
    to_calculate_order = {
        "cur_diluted_cost": get_float_input("Enter current diluted cost: "),
        
        "cur_position": get_int_input("Enter current position (number of shares): "),
        
        "type": get_choice_input(
            "Enter option type (call/put): ",
            ['call', 'put']
        ),
        
        "volume": get_int_input("Enter volume (negative for short position): "),
        
        "end_state": get_choice_input(
            "Enter end state (filled/expired/exercised): ",
            ['filled', 'expired', 'exercised']
        ),
        
        "premium": get_float_input("Enter option premium: "),
        
        "strikeprice": get_float_input("Enter strike price: "),
        
        "closeorderprice": get_float_input("Enter closing order price: ")
    }

    # Calculate and display result
    calculator = DilutedCostCalculator(to_calculate_order)
    result = calculator.calculate()
    
    print("\n=== Result ===")
    print(f"Diluted Cost: {result:.2f}")
    
    # Display summary of inputs
    print("\n=== Input Summary ===")
    for key, value in to_calculate_order.items():
        print(f"{key}: {value}")

def main():
    to_calculate_order = {
        "cur_diluted_cost":94.16,
        "cur_position":1050,
        "type":"call",
        "volume":-1,
        "end_state":"filled",
        "premium":91.33,
        "strikeprice":88,
        "closeorderprice":95.67
    }
    calculator = DilutedCostCalculator(to_calculate_order)
    di = calculator.calculate()
    print(di)

if __name__ == "__main__":
    main()