from . import source as Source
from . import utility as ut
from binance.client import Client
none = None

'''
    decision making controller
'''
class Veronica():
    def __init__(self, source, client):
        self.client : Client = client
        self.source : Source = source
        self.symbol = self.source.symbol
        self.logger = ut.RawLogger(self)
        self.flags = []
        self.orderCache = None

    def step(self):

        ## generate a unique id for this step (optional)
        ## self.stepId = ut.generate()

        # fire receptors
        for flag in self.flags:
            flag.step()

        # remove the used chache
        self.orderCache = None
    
    @property
    def exactIndex(self):
        return ut.today()
        
    def addFlag(self,condition):
        rec = Flag(condition,self)
        self.flags.append(rec)
        return rec

    def createReceptor(self):
        rec = Receptor(self)
        self.flags.append(rec)
        return rec

    @property
    def freeUsd(self):
        def job():
            balance = self.client.get_asset_balance('USDT')['free']
            return float(balance)

        return job()     

    @property
    def freeSymbol(self):
        def job():
            asset = self.symbol[:-4]
            balance = self.client.get_asset_balance(asset)['free']
            return float(balance)

        return job()  

    def didOrderFilled(self,orderId):
        if self.orderCache is None:
            self.orderCache = self.getOrders()

        if self.orderCache != []:
            # find order with id
            orders = [x for x in self.orderCache if x['orderId'] == orderId]
            # if there are no order with id, it should be filled, return true
            if orders == []:
                return True
            # if there are orders, get first and check state
            else:
                return orders[0]['status'] == 'FILLED'
        # if there are no order , it should be filled, return true
        else:
            return True 

    def getOrders(self):

        def job():
            orders = self.client.get_open_orders(
                symbol=self.symbol
            )

            return orders
        
        return ut.persist(job,
            lambda i,e:self.log(0,i,"orders check failed:",e,"at:",self.exactIndex))

    def abortAll(self,reason = None):

        def job():
            self.client.cancel_orders(
                symbol=self.symbol
            )
            self.log(1,"orders are succesfuly aborted for:",reason,"at:",self.exactIndex)

        def condition(e):
            return e.code == -2011

        ut.persist(job,
            excpt=lambda i,e:self.log(0,i,"order cancels failed for:",reason,"from:",e,"at:",self.exactIndex),
            condition=(condition, lambda:self.log(0,"no order to abort for:",reason,"at:",self.exactIndex)))

    def abort(self, id,reason = None):
        
        def job():
            cancel = self.client.cancel_order(
                symbol=self.symbol,
                orderId=id
            )

            self.log(2,"succesful abort | for:",reason,"id:",id,"at:", self.exactIndex)

        def condition(e):
            return e.code == -2011

        ut.persist(job,
            excpt=lambda i,e:self.log(0,i,"order cancel failed for:",reason,"from:",e,"at:",self.exactIndex),
            condition=(condition, lambda:self.log(0,"no order to abort for:",reason,"at:",self.exactIndex)))

    def limitBuy(self,price,percent = 100):

        def job(price):
            # get free balance
            balance = self.freeUsd if percent == 100 else ut.getPercentage(self.freeUsd, percent)

            # find quantity for target symbol
            balance /= price

            # set precisions
            balance = "{:.0f}".format(ut.truncate(balance,0))
            price = "{:.6f}".format(ut.truncate(price,6))

            orderId = self.client.order_limit_buy(
                symbol = self.symbol,
                quantity=balance,
                price=price
            )['orderId']
            
            # log
            self.log(1,"limit buy ordered | price:",price,"id:",orderId,"balance:",balance,"at:",self.exactIndex)
            
            return orderId
        
        return ut.persist(lambda:job(price),
            excpt=lambda i,e: self.log(0,i,"limit buy order rejected | price:",price,"percent:",percent,"at:",self.exactIndex,"message:",e)
        )

    def limitSell(self,price):

        def job(price):
            # get free balance
            assetBalance = self.freeSymbol

            # set precisions
            assetBalance = "{:.0f}".format(ut.truncate(assetBalance,0))
            price = "{:.6f}".format(ut.truncate(price,6))

            orderId = self.client.order_limit_sell(
                symbol = self.symbol,
                quantity=assetBalance,
                price=str(price)
            )['orderId']
            # log
            self.log(1,"sell ordered | price:",price,"id:",orderId,"at:",self.exactIndex)

            return orderId
        
        return ut.persist(lambda:job(price),
            excpt=lambda i,e: self.log(0,i,"limit sell order rejected | price:",price,"at:",self.exactIndex,"message:",e)
        )

    # this strategy utilizes some very well optimized parameters for decision making but acts only at final buy oppurtunity for DENT-USDT pair
    def strategy_one(self, balance_percentages = [1,2,4,8,16,38,100],
                    drop_percentages=[0,-1.864024907352492, -2.893588399902174, -3.946016745975842, -5.072344859259828, -5.144096791047913, -7.907342731764012],
                    rise_percentages=[1.8117461299399744, 2.926685800089782, 3.52732153834936, 5.749646662802631, 6.109972817372269, 7.686370826028769, 7.819310135625294]):
        
        FLAG = self.addFlag(lambda:self.source.tsi() < 0)

        MAINBUY = Perceptor(self)
        RESCUE = Perceptor(self)
        RESCUE2 = Perceptor(self)
        RESCUE3 = Perceptor(self)
        RESCUE4 = Perceptor(self)
        RESCUE5 = Perceptor(self)

        RESCUE6 = Receptor(self)

        FLAG.removeFlagWhenRise(1)\
            .limitBuyWhenFall(drop_percentages[0], balance_percentages[0], callBack = MAINBUY)

        MAINBUY.limitSellWhenRise(rise_percentages[0])\
            .limitBuyWhenFall(drop_percentages[1], balance_percentages[1], callBack = RESCUE)

        RESCUE.limitSellWhenRise(rise_percentages[1])\
            .limitBuyWhenFall(drop_percentages[2], balance_percentages[2], callBack = RESCUE2)

        RESCUE2.limitSellWhenRise(rise_percentages[2])\
            .limitBuyWhenFall(drop_percentages[3], balance_percentages[3], callBack = RESCUE3)

        RESCUE3.limitSellWhenRise(rise_percentages[3])\
            .limitBuyWhenFall(drop_percentages[4], balance_percentages[4], callBack = RESCUE4)

        RESCUE4.limitSellWhenRise(rise_percentages[4])\
            .limitBuyWhenFall(drop_percentages[5], balance_percentages[5], callBack = RESCUE5)

        RESCUE5.limitSellWhenRise(rise_percentages[5])\
            .limitBuyWhenFall(drop_percentages[6], balance_percentages[6], callBack = RESCUE6)
            
        RESCUE6.limitSellWhenRise(rise_percentages[6])
    
    # this strategy utilizes ordinary parameters for decision making and acts for 7 different buy oppurtunity for DENT-USDT pair
    def strategy_two(self, balance_percentages = [1,2,4,8,16,38,100],drop_percentages=[0,-2,-3,-4,-5,-6,-7],rise_percentages=[1,3,3.1,5,6,7,7.8]):
        FLAG = self.addFlag(lambda:self.source.tsi() < -1)
        
        MAINBUY = Receptor(self)
        RESCUE = Receptor(self)
        RESCUE2 = Receptor(self)
        RESCUE3 = Receptor(self)
        RESCUE4 = Receptor(self)
        RESCUE5 = Receptor(self)
        RESCUE6 = Receptor(self)

        FLAG.removeFlagWhenRise(1)\
            .limitBuyWhenFall(drop_percentages[0], balance_percentages[0], callBack = MAINBUY)

        MAINBUY.limitSellWhenRise(rise_percentages[0])\
            .limitBuyWhenFall(drop_percentages[1], balance_percentages[1], callBack = RESCUE)

        RESCUE.limitSellWhenRise(rise_percentages[1])\
            .limitBuyWhenFall(drop_percentages[2], balance_percentages[2], callBack = RESCUE2)

        RESCUE2.limitSellWhenRise(rise_percentages[2])\
            .limitBuyWhenFall(drop_percentages[3], balance_percentages[3], callBack = RESCUE3)

        RESCUE3.limitSellWhenRise(rise_percentages[3])\
            .limitBuyWhenFall(drop_percentages[4], balance_percentages[4], callBack = RESCUE4)

        RESCUE4.limitSellWhenRise(rise_percentages[4])\
            .limitBuyWhenFall(drop_percentages[5], balance_percentages[5], callBack = RESCUE5)

        RESCUE5.limitSellWhenRise(rise_percentages[5])\
            .limitBuyWhenFall(drop_percentages[6], balance_percentages[6], callBack = RESCUE6)
            
        RESCUE6.limitSellWhenRise(rise_percentages[6])
   
    def serialize(self):
        return { 
            str(x.index):x.serialize() for x in self.flags
        }
    
    def initialize(self,data):
        if data is not None:
            for key,value in data.items():
                self.flags[int(key)].load(value)
    
    def image(self):
        print(*self.serialize(),sep="\n")

'''
    use flag class for condition
'''
class Flag():
    def __init__(self,condition,broker:Veronica) -> None:
        # save the index
        self.index = 0 if len(broker.flags) == 0 else len(broker.flags) - 1
        self.originPrice = none
        self.targetPercent = none
        self.targetPrice = none
        self.condition = condition
        self.limitBuyPackage = none
        self.callBacks = none
        self.plotCallBacks = none
        self.broker = broker
        self.ready = True
   
    def load(self, data):
        self.ready = data[0]
        self.targetPrice = data[1]
        self.originPrice  = data[2]

    def serialize(self):
        return [self.ready,
                self.targetPrice,
                self.originPrice] 

    def removeFlagWhenRise(self, per):
        self.targetPercent = per
        return self
    
    def limitBuyWhenFall(self, per, balancePercent, callBack):
        self.limitBuyPackage = (per , balancePercent, callBack.index)
        return self
    
    def completed(self):
        self.originPrice = None
        self.targetPrice = None

    def stop(self,reason=""):
        self.ready = False
        self.broker.log(3, reason)
        return self

    def reset(self):
        self.completed()
        self.ready = True

    @property
    def notReady(self):
        return self.ready == False

    def loss(self, per):
        return self.notReady and self.broker.source.close <= ut.exposePercentage(self.originPrice,per)

    def step(self):
        if self.ready == False:
            return

        # check 
        if self.originPrice is None and self.condition():
            # fire plot callBacks
            self.firePlotCallBacks()

            self.originPrice = self.broker.source.close
            self.targetPrice = ut.exposePercentage(self.originPrice, self.targetPercent)
            # arrange limit buy call if it exists
            if self.limitBuyPackage is not None:
                # find target
                targetReceptor = self.broker.flags[self.limitBuyPackage[2]]
                # send package
                targetReceptor._rescueBuy(self.originPrice,self.limitBuyPackage[0],self.limitBuyPackage[1])
        
        
        else:
            # check fire
            self.check()

    def check(self):
        if self.originPrice is not None:
            # if flag raised
            if self.targetPrice <= self.broker.source.high:

                floorPrice = ut.exposePercentage(self.originPrice, self.limitBuyPackage[0])
                # but the next buy didnt filled
                if self.broker.source.low > floorPrice:
                    # fire
                    self.fireWhenRiseCallBacks()
                    # complete cycle
                    self.completed()
                else:
                    # sometimes out margin is small
                    # and you can get, out signal from the same
                    # bar that you bought the asset. just pass it
                    self.broker.log(3,"BWO bounce event skipped at:",self.broker.exactIndex)

    def whenRise(self, callBacks):
        self.callBacks = callBacks
        return self

    def whenPlot(self, callBacks):
        self.plotCallBacks = callBacks
        return self
    
    def fireWhenRiseCallBacks(self):
        # first receptor is the flag, 
        # start from second one to enumeration
        for receptor in self.broker.flags[1:]:
            receptor.abortBuy("flag rised")

        if self.callBacks is not None:
            for call in self.callBacks:
                call()   

    def firePlotCallBacks(self):
        if self.plotCallBacks is not None:
            for pcall in self.plotCallBacks:
                pcall()

'''
    use receptor class for real decision actions
'''            
class Receptor():
    def __init__(self,broker:Veronica) -> None:
        # add receptor to broker list
        broker.flags.append(self)
        # save the index
        self.index = len(broker.flags) - 1
        self.limitBuyTarget = none
        self.limitBuyID = none
        self.limitSellID = none
        self.sellTargetPercent = none
        self.sellBalancePercent = none
        self.limitBuyPackage = none
        self.sellCallBack = none
        self.buyCallBack = none
        self.broker = broker
        self.initialLock = False

    def load(self, data):
        self.limitBuyID = data[0]
        self.limitSellID = data[1]
        self.limitBuyTarget = data[2]

    def serialize(self):
        return [self.limitBuyID,
                self.limitSellID,
                self.limitBuyTarget] 

    def step(self):
        # if we gave a buy order
        if self.limitBuyID is not None and self.initialLock == False:
            
            # if buy order filled
            if self.broker.didOrderFilled(self.limitBuyID):
                
                # log
                self.broker.log(1,"buy order filled | id:",self.limitBuyID,"price:",self.limitBuyTarget,"receptor:",self.index,"at:",self.broker.exactIndex)

                # fire callback if it exist
                self.fireBuyCallBacks()

                # and we have sell target
                if self.sellTargetPercent is not None:
                    # find sell target price
                    limitSellTarget = ut.exposePercentage(self.limitBuyTarget, self.sellTargetPercent)
                    # give order
                    self.limitSellID = self.broker.limitSell(limitSellTarget)

                # remove used data
                self.limitBuyID = None

        elif self.limitSellID is not None:

            # if buy order filled
            if self.broker.didOrderFilled(self.limitSellID):
                # log
                self.broker.log(1,"sell order filled | id:",self.limitSellID,"price: ","receptor:",self.index,"at:",self.broker.exactIndex)

                # fire callback if it exist
                self.fireSellCallBacks()

                # remove used data
                self.limitSellID = None

    def _rescueBuy(self, originPrice, percent, balancePercent):
        self.limitBuyTarget = ut.exposePercentage(originPrice, percent)
        self.limitBuyID = self.broker.limitBuy(self.limitBuyTarget,percent=balancePercent)
        
        # arrange limit buy call if it exists
        if self.limitBuyPackage is not None:
            self.initialLock = True
            
            # find target
            targetReceptor = self.broker.flags[self.limitBuyPackage[2]]
            # send package
            targetReceptor._rescueBuy(self.limitBuyTarget,self.limitBuyPackage[0],self.limitBuyPackage[1])

    def whenBuy(self, callBack):
        self.buyCallBack = callBack
        return self

    def whenSell(self, callBack):
        self.sellCallBack = callBack
        return self

    def limitBuyWhenFall(self, per, balancePercent, callBack):
        self.limitBuyPackage = (per , balancePercent, callBack.index)
        return self

    def limitSellWhenRise(self, per, balancePercent = 100):
        self.sellTargetPercent = per
        self.sellBalancePercent = balancePercent
        return self
    
    def reset(self):
        self.limitBuyTarget = none
        self.limitBuyID = none
        self.limitSellID = none
    
    def abortBuy(self,reason = ""):
        if self.limitBuyID is not None and self.broker.didOrderFilled(self.limitBuyID) == False:
            self.broker.abort(self.limitBuyID, reason=reason)
            self.reset()

    def abortSell(self,reason = ""):
        if self.limitSellID is not None:
            self.broker.abort(self.limitSellID, reason)
            self.reset()

    def fireBuyCallBacks(self):
        index = self.index

        # first receptor is the flag, pass
        if index == 0:
            pass
        # main buy receptor
        elif index == 1:
            # stop the flag
            self.broker.flags[0].stop(reason = "flag stopped from main buy execution")
        # rescue buy receptors
        else:
            # abort previous receptors sell
            self.broker.flags[index-1].abortSell("{}. receptor buy executed, aborting previous sell".format(self.index))

        if self.buyCallBack is not None:
            for call in self.buyCallBack:
                call()

    def fireSellCallBacks(self):
        for i,receptor in enumerate(self.broker.flags):
            # if target receptor previous from this one, reset it
            if i < self.index:
                receptor.reset()
            # if target receptor front of this one, abort it
            elif i > self.index:
                receptor.abortBuy("{}. receptor sell executed, aborting next buys".format(self.index))

        if self.sellCallBack is not None:
            for call in self.sellCallBack:
                call()

'''
    use perceptor class for fake decision actions
'''
class Perceptor():
    def __init__(self,broker:Veronica) -> None:
        # add receptor to broker list
        broker.flags.append(self)
        # save the index
        self.index = len(broker.flags) - 1
        self.limitBuyTarget = none
        self.limitBuyID = none
        self.limitSellTarget = none
        self.sellTargetPercent = none
        self.sellBalancePercent = none
        self.limitBuyPackage = none
        self.sellCallBack = none
        self.buyCallBack = none
        self.broker = broker
        self.initialLock = False
        self.notPassive = False

    def load(self, data):
        self.limitBuyID = data[0]
        self.limitSellTarget = data[1]
        self.limitBuyTarget = data[2]

    def serialize(self):
        return [self.limitBuyID,
                self.limitSellTarget,
                self.limitBuyTarget]

    def step(self):
        # if we gave a buy order
        if self.limitBuyID is not None and self.initialLock == False:
            
            # if passive buy order filled
            if self.broker.source.low <= self.limitBuyTarget:
                
                # log
                self.broker.log(1,"passive buy order filled | price:",self.limitBuyTarget,"receptor:",self.index,"at:",self.broker.exactIndex)

                # fire callback if it exist
                self.fireBuyCallBacks()

                # and we have sell target
                if self.sellTargetPercent is not None:
                    # find sell target price
                    limitSellTarget = ut.exposePercentage(self.limitBuyTarget, self.sellTargetPercent)
                    # give order
                    self.limitSellTarget = limitSellTarget

                # remove used data
                self.limitBuyID = None

        elif self.limitSellTarget is not None:

            # if buy order filled
            if self.broker.source.high >= self.limitSellTarget:
                # log
                self.broker.log(1,"passive sell order filled | price: ","perceptor:",self.index,"at:",self.broker.exactIndex)

                # fire callback if it exist
                self.fireSellCallBacks()

                # remove used data
                self.limitSellTarget = None

    def _rescueBuy(self, originPrice, percent, balancePercent):
        self.limitBuyTarget = ut.exposePercentage(originPrice, percent)
        self.limitBuyID = "on"

        # arrange limit buy call if it exists
        if self.limitBuyPackage is not None:
            # find target
            targetReceptor = self.broker.flags[self.limitBuyPackage[2]]
            # send package
            targetReceptor._rescueBuy(self.limitBuyTarget,self.limitBuyPackage[0],self.limitBuyPackage[1])

    def whenBuy(self, callBack):
        self.buyCallBack = callBack
        return self

    def whenSell(self, callBack):
        self.sellCallBack = callBack
        return self

    def limitBuyWhenFall(self, per, balancePercent, callBack):
        self.limitBuyPackage = (per , balancePercent, callBack.index)
        return self

    def limitSellWhenRise(self, per, balancePercent = 100):
        self.sellTargetPercent = per
        self.sellBalancePercent = balancePercent
        return self
    
    def reset(self):
        self.limitBuyTarget = none
        self.limitBuyID = none
        self.limitSellTarget = none
    
    def abortBuy(self,reason = ""):
        if self.limitBuyID is not None:
            self.reset()

    def abortSell(self,reason = ""):
        if self.limitSellTarget is not None:
            self.reset()

    def fireBuyCallBacks(self):
        index = self.index

        # first receptor is the flag, pass
        if index == 0:
            pass
        # main buy receptor
        elif index == 1:
            # stop the flag
            self.broker.flags[0].stop(reason = "flag stopped from main buy execution")
        # rescue buy receptors
        else:
            # abort previous receptors sell
            self.broker.flags[index-1].abortSell("{}. receptor buy executed, aborting previous sell".format(self.index))

        if self.buyCallBack is not None:
            for call in self.buyCallBack:
                call()

    def fireSellCallBacks(self):
        for i,receptor in enumerate(self.broker.flags):
            # if target receptor previous from this one, reset it
            if i < self.index:
                receptor.reset()
            # if target receptor front of this one, abort it
            elif i > self.index:
                receptor.abortBuy("{}. receptor sell executed, aborting next buys".format(self.index))

        if self.sellCallBack is not None:
            for call in self.sellCallBack:
                call()
