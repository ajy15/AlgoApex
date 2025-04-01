from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
from dotenv import load_dotenv
 
load_dotenv()
 
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

def marketbuy(symbol, qty):
    market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
