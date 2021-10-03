from cryptofeed import exchanges
from cryptofeed.feedhandler import FeedHandler
from cryptofeed.exchanges import Gemini, FTX
from cryptofeed.defines import L2_BOOK, TRADES, BID, ASK
import multiprocessing

import redis
import time

from live_trader import liveTrading
import sys

def get_obook(exchange, symbol, subaccount):
    r = redis.Redis(host='localhost', port=6379, db=0)   
    
    f = FeedHandler()

    def nbbo_update(symbol, bid, bid_size, ask, ask_size, bid_feed, ask_feed):    
        r.set('curr_best_ask', str(ask))
        r.set('curr_best_bid', str(bid))

        r.set('getting_data', 1)

    if exchange == 'gemini':
        f.add_nbbo([Gemini], [symbol], nbbo_update)
    elif exchange == 'ftx':
        f.add_nbbo([FTX], [symbol], nbbo_update)
    
    f.run()

if __name__ ==  '__main__':
    if len(sys.argv) > 3:
        subaccount = ""
        exchange = sys.argv[1]
        symbol = sys.argv[2]
        trade_type = sys.argv[3]
    
        if exchange == 'ftx':
            subaccount = sys.argv[4]
        
    else:
        print("Must contain symbol, exchange, trade_type as parameter")


    print(exchange, symbol, subaccount)

    p = multiprocessing.Process(target=get_obook, args=(exchange, symbol,subaccount,))
    p.start()

    r = redis.Redis(host='localhost', port=6379, db=0) 
    r.set('getting_data', 0)

    while int(r.get('getting_data').decode()) == 0:
        time.sleep(1)
    
    print("Started getting data")

    lt = liveTrading(exchange, symbol.replace("-", "/"), subaccount)
    lt.fill_order(trade_type)
    p.terminate()