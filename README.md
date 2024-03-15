
# Project Veronica

Veronica is a trade management software that helps you to divide your main balance into smaller amounts and perform a cascade fashion buy/sell series.



## Features

- Ready to use with **Azure** and **Firestore**
- Optimized for **BINANCE** usage
- Operates at **low** cost
- Works with **1 minute** bars
- Auto price data management
- Ready for **TAlib** indicators


## Requirements

```bash
requests
python-binance==1.0.7
pandas==1.2.1
finta==1.2
numpy
firebase_admin
```


## Usage/Examples

You can design your strategy function in **Veronica** class

```python
class Veronica():
.
.
.
  def some_strategy():
    # when TSI indicator down below 0
    # our flag will be activate our limit orders
    FLAG = self.addFlag(lambda:self.source.tsi() < 0)

    # initialize sub managers
    BUY1 = Receptor(self)
    BUY2 = Receptor(self)
    BUY3 = Receptor(self)

    # when price go 1% up before go -1% down, abort orders 
    FLAG.removeFlagWhenRise(1)\
          # if price go -1% down, buy with 10% of balance
          .limitBuyWhenFall(-1, 10, callBack = BUY1)

    # if price go 1% up after main buy, sell all
    BUY1.limitSellWhenRise(1)\
          # if price go -2% down after main buy,
          # buy with 20% of REMAIN balance
          .limitBuyWhenFall(-2, 20, callBack = BUY2)

    # if price go 2% up after second buy, sell all
    BUY2.limitSellWhenRise(2)\
          # if price go -3% down after second buy,
          # buy with 40% of REMAIN balance
          .limitBuyWhenFall(-3, 40, callBack = BUY3)

    # if price go 4% up after third buy, sell all
    BUY3.limitSellWhenRise(4)
.
.
.
```
and call in main loop

```python
# stateless function for azure cloud
def main(azure_timer: func.TimerRequest) -> None:
.
.
.
    # initiate veronica
    broker : Veronica = Veronica(source = pair_source, client = client)
    
    # execute designed strategy
    broker.some_strategy()
.
.
.
```
you can add passive buys to earlier steps with **Perceptor** class for more dense strategies

```python
class Veronica():
.
.
.
  def some_strategy():
    .
    .
    .
    # these two sub managers will behave like Receptor, 
    # won't going to add any limit orders BUT will remove callbacks when RISE
    PASSIVE_BUY1 = Perceptor(self)
    PASSIVE_BUY2 = Perceptor(self)

    # normal manager
    BUY3 = Receptor(self)
    .
    .
    .
    # if price go 2% up after second buy, abort all (like FLAG)
    PASSIVE_BUY2.limitSellWhenRise(2)\
          # if price go -3% down after second buy,
          # buy with 100% of REMAIN balance
          .limitBuyWhenFall(-3, 100, callBack = BUY3)

    # if price go 4% up after third buy, sell all
    BUY3.limitSellWhenRise(4)
    .
    .
    .
```
**Veronica** will track valid strategy actions even if it didn't make any **real** buy
## Deployment to Cloud

Will be added soon with details..

