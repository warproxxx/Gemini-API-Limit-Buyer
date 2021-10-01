import ccxt
import os
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
    def __init__(self, symbol):
        self.symbol = symbol
        apiKey = os.getenv('GEMINI_ID')
        apiSecret = os.getenv('GEMINI_SECRET')

        self.exchange = ccxt.gemini({
                            'apiKey': apiKey,
                            'secret': apiSecret,
                            'enableRateLimit': True
                        })

        self.increment = 0.01
        self.attempts = 5
        self.r = redis.Redis(host='localhost', port=6379, db=0)   


    def close_open_orders(self):
        self.exchange.private_post_v1_order_cancel_all()


    def get_balance(self):
        return self.exchange.fetch_balance()['USD']['free']


    def get_best_ask(self):
        return float(self.r.get('gemini_best_ask').decode())

    def get_best_bid(self):
        return float(self.r.get('gemini_best_bid').decode())

    def get_max_amount(self):
        balance = self.get_balance()
        price = (self.get_best_ask() *100 - self.increment * 100)/100
        amount = int((balance*100000)/(price*100000) * 100000 * 0.99)/100000
        
        return amount, price


    def send_limit_order(self):
        for lp in range(self.attempts):
            try:
                amount, price = self.get_max_amount()
                print(amount,price)

                if amount == 0:
                    return [], 0

                order = self.exchange.create_order(self.symbol, 'limit', 'buy', amount, price, params={'options': ['maker-or-cancel']})
                print("Sent a limit order to buy {} {} at price {}".format(amount, self.symbol, price))
                return order, price
            except ccxt.BaseError as e:
                print(e)
                pass


    def fill_order(self):
        self.close_open_orders()
        order, limit_price = self.send_limit_order()          

        while True:
            time.sleep(.5)
            order = self.exchange.fetch_order(order['info']['id'])
            print(order)
            if order['status'].lower() != 'closed':
                best_bid = self.get_best_bid()

                if best_bid > limit_price:
                        print("Current price is much better, closing to open new one")
                        self.close_open_orders()
                        order, limit_price = self.send_limit_order()
            else:
                print("Order has been filled. Exiting out of loop")
                self.close_open_orders()
                break





            