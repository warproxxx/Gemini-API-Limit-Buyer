import ccxt
import os
from cryptofeed import exchanges
import pandas as pd
import decimal
import redis
import time

def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_DOWN
        return float(round(d, decimals))

class liveTrading():
    def __init__(self, exchange, symbol, subaccount=""):
        self.symbol = symbol
        self.exchange_name = exchange

        apiKey = os.getenv('{}_ID'.format(exchange.upper()))
        apiSecret = os.getenv('{}_SECRET'.format(exchange.upper()))

        if exchange == 'gemini':
            self.exchange = ccxt.gemini({
                                'apiKey': apiKey,
                                'secret': apiSecret,
                                'enableRateLimit': True
                            })
        elif exchange == 'ftx':
            self.exchange = ccxt.ftx({
                                'apiKey': apiKey,
                                'secret': apiSecret,
                                'enableRateLimit': True
                            })

            if subaccount != "":
                self.exchange.headers = {
                                            'FTX-SUBACCOUNT': subaccount,
                                        }
        self.increment = self.exchange.load_markets()[symbol]['precision']['price']
        self.attempts = 5
        self.r = redis.Redis(host='localhost', port=6379, db=0)   


    def close_open_orders(self):
        self.exchange.private_post_v1_order_cancel_all()


    def get_balance(self, trade_type):
        return self.exchange.fetch_balance()['USD']['free']


    def get_best_ask(self):
        return float(self.r.get('curr_best_ask').decode())

    def get_best_bid(self):
        return float(self.r.get('curr_best_bid').decode())

    def get_max_amount(self, trade_type):
        balance = self.get_balance(trade_type)
        price = (self.get_best_ask() *100 - self.increment * 100)/100
        amount = int((balance*100000)/(price*100000) * 100000 * 0.998)/100000
        
        return amount, price


    def send_limit_order(self, trade_type):
        for lp in range(self.attempts):
            try:
                amount, price = self.get_max_amount(trade_type)
                print(amount,price)

                if amount == 0:
                    return [], 0

                params = {}

                if self.exchange_name == 'gemini':
                    params = {'options': ['maker-or-cancel']}
                elif self.exchange_name == 'ftx':
                    params = {'postOnly': True}

                order = self.exchange.create_order(self.symbol, 'limit', trade_type, amount, price, params=params)
                print("Sent a limit order to {} {} {} at price {}".format(trade_type, amount, self.symbol, price))
                return order, price
            except ccxt.BaseError as e:
                print(e)
                pass


    def fill_order(self, trade_type):
        self.close_open_orders()
        order, limit_price = self.send_limit_order(trade_type)          

        while True:
            time.sleep(.5)
            order = self.exchange.fetch_order(order['info']['id'])
            print(order)
            if order['status'].lower() != 'closed':
                best_bid = self.get_best_bid()

                if best_bid > limit_price:
                        print("Current price is much better, closing to open new one")
                        self.close_open_orders()
                        order, limit_price = self.send_limit_order(trade_type)
            else:
                print("Order has been filled. Exiting out of loop")
                self.close_open_orders()
                break





            