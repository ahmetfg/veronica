import math
import datetime as dt
import json
import pandas as pd
import requests
import time
import numpy as np
import random
import string
from binance.exceptions import BinanceAPIException
import json
none = None

def getPercentage(balance,per):
    # find percentage of given balance
    Y = per / 100
    return balance * Y

def getPercentageDiff(balance, oldBalance):
    # find difference percentage of a - b
    diff = (balance - oldBalance)
    return diff / oldBalance * 100

def exposePercentage(balance, per):
    if balance is None:
        raise NotImplementedError('balance cant be null')
    if per is None:
        raise NotImplementedError('percent cant be null')
    # find percentage of given balance
    result = getPercentage(balance, per)

    # apply
    return balance + result

def rawArrangeData(text):
    try:
        data = json.loads(text)
        df : pd.DataFrame = None 

        # check error
        if type(data) is dict:
            error = data['msg']
            return None, error
        else:
            # arrange data
            df = pd.DataFrame(data)
            df.columns = ['open_time',
                            'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'qav', 'num_trades',
                            'taker_base_vol', 'taker_quote_vol', 'ignore']
            
            # arrange from utc + 3 difference
            threeHour = 10800

            # indexing
            df.index = [dt.datetime.fromtimestamp(x/1000.0 - threeHour) for x in df.close_time]
            df = df.drop(['ignore','taker_base_vol','taker_quote_vol','num_trades','qav'], axis=1)\
                    .to_json(orient="records")

            df = pd.read_json(df)
            return df, None
    except Exception as e:
        return None,e

def getDataFromBinance(symbol, interval='1m', limit=None, startDate=None, endDate=None, debugThrow=False):

    # fake exception
    if debugThrow:
        raise NotImplementedError("fake exception executed")

    root_url = 'https://api.binance.com/api/v1/klines'
    
    # set url
    url = root_url + '?symbol=' + symbol + '&interval=' + interval 
    
    # add date
    if startDate is not None:
        url += "&startTime=" + str(startDate)

    # add date
    if endDate is not None:
        url += "&endTime=" + str(endDate)

    if limit is not None:
        url += '&limit=' + str(limit)

    # download
    result, error = rawArrangeData(requests.get(url).text)

    if error is not None:
        print(error)
    else:
        return result

def truncate(value, n):
    if type(value) is str:
        value = float(value)
    return math.floor(value * 10 ** n) / 10 ** n

def formats(value):
    if type(value) is str:
        value = float(value)
    return "{:.0f}".format(value)

def getData(symbol):
    return pd.read_json(symbol + '.json')

def getCoinTag(name):
    return name.split('_')[0]

def con(*args):
    lst=[]
    for arg in args:
        lst.append(str(arg))
    return ' '.join(lst)

def generate():
    # Generate a random string
    # with 32 characters.
    rand = ''.join([random.choice(string.ascii_letters
                + string.digits) for n in range(32)])
    return rand

def today():
    return dt.datetime.now()

def arrangeData(df=None, symbol=None):
    df = getData(symbol=symbol) if df is None else df
    if 'O' in df.columns:
        column = {'O':'open','H':'high','L':'low','C':'close','V':'volume'}
    elif 'o' in df.columns:
        column = {'o':'open','h':'high','l':'low','c':'close','v':'volume'}
    else:
        return df
    return df.rename(columns=column).drop(['ignore','taker_base_vol','taker_quote_vol','num_trades','qav'], axis=1)

def intervalLoop(callBack, targetInterval = 1,until=lambda:False,debug=False):
    while True:
        if until() == True:
            break
        callBack()
        
        if debug is False:
            time.sleep(targetInterval)

def minuteExecution(callBack, targetSecond = 59):
    while True:
        # check target second
        if dt.datetime.now().second == targetSecond:
            # run callback
            if callBack is not None:
                callBack()
            
            # sleep
            time.sleep(2)

class EmptyClass():
    pass

class RawLogger():
    def __init__(self,target) -> None:
        self.logLevel = 0
        target.setLog = self._setLog
        target.setSerialize = self._setSerialize
        target.log = self._log
        self.target = target
        self._serialize=False

    def _setLog(self,level):
        self.logLevel = level
        
        return self.target

    def _setSerialize(self,bool):
        self._serialize = bool
        
        return self.target

    def _log(self,level,*message):
        if self.logLevel >= level:
            print(*message)

    def serialize(self,message):
        try:
            file = np.load("session_logs.npy",allow_pickle=True)
            file = np.append(file, [message],axis=0)
        except Exception as e:
            file = np.array([message])
            print(e)

        np.save("session_logs.npy",file)

    def serializeJSON(self,message):
        if self._serialize is False:
            return
        try:
            with open('session_logs.json', 'r+') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Join new_data with file_data
                file_data.append(message)
                # Sets file's current position at offset.
                file.seek(0)
                json.dump(file_data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)
            with open('session_logs.json', 'w', encoding='utf-8') as f:
                json.dump([message], f, ensure_ascii=False, indent=4)

def readBinary(path,log=True):
    file = np.load(path+".npy",allow_pickle=True)
    if log:
        print(file)
    return file

class Measure():
    def __init__(self):
        self.begin = time.time()
    @property
    def printSecond(self):
        now = time.time()
        result = (now - self.begin)
        print("execution minute:", result)
        
        return self

    def second(self):
        now = time.time()
        result = (now - self.begin)
        
        return result
    
    @property
    def reset(self):
        self.begin = time.time()
        return self

def persist(job,excpt=None,loopCount=3,sleep=2,condition=None,throwAtFinal=True):
    for i in range(loopCount):
        try:
            if job is not None:
                result = job()
                if i > 0:
                    print("additional attempt successfully executed..")
                return result
        except Exception as e:
            if condition is not None and condition[0](e):
                if condition[1] is not None:
                    condition[1]()
                    break
            elif i < loopCount -1:
                if excpt is not None:
                    excpt(i + 1,e)
                else:
                    print("failed atempt")
                time.sleep(sleep)
            else:
                if throwAtFinal:
                    raise e
                else:
                    if excpt is not None:
                        excpt(i + 1,e)
                    else:
                        print("final attempt failed either")

def runChance(chance,count=1):
    otherChance = 1 - chance
    return random.choices(
        [True,False],
        [chance,otherChance],
        k=count
    )[0]

def isOnline(debug = None): # debug = (unconnectedTime,MaxTime)
    if debug != None:
        if debug[0] >= debug[1]:
            return True
        else:
            return False
            
    url = "http://www.google.com"
    timeout = 5
    try:
        request = requests.get(url, timeout=timeout)
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        return False

def reconnectionWizard(sleep=5,maxTry=None,debug=None):
    unconnectedWhile = 0

    if debug is not None:
        check = lambda: isOnline(debug=(unconnectedWhile,debug))
    else:
        check = lambda: isOnline()

    while check() == False:
        print("still offline... next try {} seconds later... (unconnected second:".format(sleep),end='{})\r'.format(unconnectedWhile))
        unconnectedWhile += sleep
        time.sleep(sleep)

    if unconnectedWhile == 0:
        print("\nconnection came back immediately")
    else:
        print("\nconnection back after {:.2f} minute".format(unconnectedWhile / 60))