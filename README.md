Gemini charges 1.5% fee while buying on the interface. 0.35% when using ActiveTrader as a maker and 0.25% as a taker. And for limit order made via the API its 0.1% even for the plebs. This uses a python script to keep sending the best limit order for a given size until the purchase is completed 

## Setup:
1) Install redis and the requirements
2) Generate your Primary Account API and add GEMINI_KEY and GEMINI_SECRET to PATH
3) Install requirements
4) python3 trade.py gemini ETH-USD buy
