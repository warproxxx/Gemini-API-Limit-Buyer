from cryptofeed.feedhandler import FeedHandler
from cryptofeed.exchanges import Gemini
from cryptofeed.defines import L2_BOOK, TRADES, BID, ASK
import multiprocessing

import redis
import time

from live_trader import liveTrading
import sys

def get_obook(symbol):
    r = redis.Redis(host='localhost', port=6379, db=0)   
    
    f = FeedHandler()

    def nbbo_update(symbol, bid, bid_size, ask, ask_size, bid_feed, ask_feed):    
        r.set('gemini_best_ask', str(ask))
        r.set('gemini_best_bid', str(bid))

        r.set('getting_data', 1)

    f.add_nbbo([Gemini], [symbol], nbbo_update)
    f.run()

if __name__ ==  '__main__':
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = 'ETH-USD'

    print(symbol)

    p = multiprocessing.Process(target=get_obook, args=(symbol,))
    p.start()

    r = redis.Redis(host='localhost', port=6379, db=0) 
    r.set('getting_data', 0)

    while int(r.get('getting_data').decode()) == 0:
        time.sleep(1)
    
    print("Started getting data")

    lt = liveTrading(symbol.replace("-", "/"))
    lt.fill_order()
    p.terminate()