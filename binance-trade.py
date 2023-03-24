pip install python - binance
from binance import Client
import time
from decimal import Decimal

api_key = '...'
api_secret = '...'
client = Client(api_key, api_secret)


def buy_order(new_pair, new_quantity, new_price):
    order = client.order_limit_buy(
        symbol=new_pair,
        quantity=new_quantity,
        price=new_price)
    return order


def sell_order(new_pair, new_quantity, new_price):
    order = client.order_limit_sell(
        symbol=new_pair,
        quantity=new_quantity,
        price=new_price)
    return order


def market_sell_order(new_pair, new_quantity):
    order = client.order_market_sell(
        symbol=new_pair,
        quantity=new_quantity)
    return order


def market_buy_order(new_pair, new_quantity):
    order = client.order_market_buy(
        symbol=new_pair,
        quantity=new_quantity)


def get_price(new_pair):
    prices = client.get_all_tickers()
    for i in prices:
        if i['symbol'] == new_pair:
            curr_pair_price = i['price']
            break
    return float(curr_pair_price)


def refresh_orders(orders):
    size = len(orders)
    i = 0
    while (i < size):
        status = client.get_order(
            symbol='BTCUSDT',
            orderId=orders[i])
        if (status['status'] == 'FILLED' or status['status'] == 'CANCELED'):
            orders.pop(i)
            i -= 1
            size -= 1
        i += 1


def time_of_orders_life(orders):
    time_of_life = []
    for i in range(len(orders)):
        status = client.get_order(
            symbol='BTCUSDT',
            orderId=orders[i])
        time_of_life.append(time.time() - status['time'] / 1000)
    return time_of_life


def price_of_order(order_Id):
    status = client.get_order(
        symbol='BTCUSDT',
        orderId=order_Id)
    return status['price']


def balance_in_usdt(curr_pair, coin1, coin2):
    curr_pair_price = get_price(curr_pair)
    tmp = client.get_asset_balance(asset=coin1)
    coin1_bal = float(tmp['free']) + float(tmp['locked'])
    tmp = client.get_asset_balance(asset=coin2)
    coin2_bal = (float(tmp['free']) + float(tmp['locked'])) * curr_pair_price
    return coin1_bal + coin2_bal

    def b_price(percent, curr_pair, curr_pair_price):
        buy_price = Decimal(curr_pair_price * (1 - percent))

    buy_price = buy_price.quantize(Decimal("0.01"))
    return buy_price


def s_price(percent, curr_pair, curr_pair_price):
    sell_price = Decimal(curr_pair_price * (1 + percent))
    sell_price = sell_price.quantize(Decimal("0.01"))
    return sell_price


def q(investment, curr_pair_price):
    quant = Decimal(investment / curr_pair_price)
    quant = quant.quantize(Decimal("0.0001"))
    return quant


def circle(investment, percent, curr_pair):
    curr_pair_price = get_price(curr_pair)
    buy_price = b_price(percent, curr_pair, curr_pair_price)
    sell_price = s_price(percent, curr_pair, curr_pair_price)
    quant = q(investment, curr_pair_price)
    buy = buy_order(curr_pair, quant, buy_price)['orderId']
    sell = sell_order(curr_pair, quant, sell_price)['orderId']
    return [buy, sell]


def buy_equilib(orders_buy, max, investment, percent, curr_pair):
    j = 0
    min_price = price_of_order(orders_buy[0])
    for i in range(max):
        if (min_price > price_of_order(orders_buy[i])):
            j = i
    client.cancel_order(
        symbol='BTCUSDT',
        orderId=orders_buy[j])
    orders_buy.pop(j)
    curr_pair_price = get_price(curr_pair)
    quant = q(investment, curr_pair_price)
    market_buy_order(curr_pair, quant)
    print("Отменил покупку \n")


def sell_equilib(orders_sell, max, investment, percent, curr_pair):
    j = 0
    max_price = price_of_order(orders_sell[0])
    for i in range(max):
        if (max_price < price_of_order(orders_sell[i])):
            j = i
    client.cancel_order(
        symbol='BTCUSDT',
        orderId=orders_sell[j])
    orders_sell.pop(j)
    curr_pair_price = get_price(curr_pair)
    quant = q(investment, curr_pair_price)
    market_sell_order(curr_pair, quant)
    print("Отменил продажу \n")


def check_overflow(orders_buy, orders_sell, max, investment, percent, curr_pair, await_time):
    if (len(orders_buy) == max):
        buy_equilib(orders_buy, max, investment, percent, curr_pair)
    if (len(orders_sell) == max and await_time != 10):
        sell_equilib(orders_sell, max, investment, percent, curr_pair)
    return 1 + (len(orders_buy) + len(orders_sell)) * 0.7


# def check_exploit (orders_buy, orders_sell, max, investment, percent, curr_pair):


percent = 0.00002
investment = 12
curr_pair = 'BTCUSDT'
coin1 = 'USDT'
coin2 = 'BTC'
orders_buy = []
orders_sell = []
start_bal = balance_in_usdt(curr_pair, coin1, coin2)
max = int(start_bal / 2 / investment)
quant = q(start_bal / 2, get_price(curr_pair))
market_buy_order(curr_pair, quant)
start_btc = float(quant) * get_price(curr_pair)
print(start_bal, '\n', '\n')
await_time = 2
time0 = time.time()
i = 0
while (float(time.time() - time0) < 5400):
    tmp = circle(investment, percent, curr_pair)
    orders_buy.append(tmp[0])
    orders_sell.append(tmp[1])
    refresh_orders(orders_buy)
    refresh_orders(orders_sell)
    await_time = check_overflow(orders_buy, orders_sell, max, investment, percent, curr_pair, await_time)
    time.sleep(await_time)
    i += 1
    if (i % 50 == 0):
        print("Time: ", time.time() - time0, "Balance ", balance_in_usdt(curr_pair, coin1, coin2), "$")
        if (balance_in_usdt(curr_pair, coin1, coin2) - start_bal < -10):
            break
while (True):
    refresh_orders(orders_buy)
    refresh_orders(orders_sell)
    if (len(orders_buy) == 0 and len(orders_sell) == 0):
        tmp = float(client.get_asset_balance(asset=coin2)['free'])
        print("Overview: ", get_price(curr_pair) * tmp - start_btc, '\n')
        market_sell_order(curr_pair, client.get_asset_balance(asset=coin2)['free'])
        break
    time.sleep(2)
print(balance_in_usdt(curr_pair, coin1, coin2) - start_bal, '\n')