class RiskManager(object):
    def stoploss(self):
        raise notImplementedError

    def stopgaincontrol(self):
        raise notImplementedError

    def movingmaxdrawdown(self):
        raise notImplementedError