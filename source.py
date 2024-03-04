from finta import TA
from . import utility as ut
'''
    pair data manager
'''
class Source():
    def __init__(self,symbol,window):
        self.symbol = symbol
        self.index = window
        self.rawData = None

    def fetch(self):
        # set data
        self.rawData = ut.getDataFromBinance(symbol=self.symbol,limit=101)[:-1]

    def tsi(self):
        # initialize column
        tsi = TA.TSI(self.rawData).fillna(0)

        return tsi["TSI"].tail(1).item()
            
    def stoch(self):
        # initialize column
        stoch = TA.STOCHD(self.rawData).fillna(0)
            
        return stoch.tail(1).item()

    @property
    def close(self):
        return self.rawData[self.index:self.index+1]['close'].item()

    @property
    def oldClose(self,index=None):
        if index is None: index = self.index - 1
        return self.rawData[index:index+1]['close'].item()

    @property
    def high(self):
        return self.rawData[self.index:self.index+1]['high'].item()

    @property
    def oldHigh(self,index=None):
        if index is None: index = self.index - 1
        return self.rawData[index:index+1]['high'].item()

    @property
    def low(self):
        return self.rawData[self.index:self.index+1]['low'].item()
    