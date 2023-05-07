import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

# Bot Logic
class Bot():
    ib = None
    def __init__(self):
        # connect to IB on init
        ib = IBApi()
        ib.connect('127.0.0.1',7496,1)
        ib.run()

if __name__ == '__main__':
    # Start Bo
    print("hello")
    bot = Bot()