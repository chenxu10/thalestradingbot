def before_cs_trade():
    input_strategy = input("""Why do you want to express your bullish view on it?
              Do you want to express this view in an attacking way, defensive way or balanced way?
              'a' for attackive
              'd' for defensive
              'b' for balanced
              """)
    if input_strategy == "a":
        s = "attactive"
    return s

if __name__ == "__main__":
    before_cs_trade()