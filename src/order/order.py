from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.requests import StopLimitOrderRequest
from alpaca.trading.requests import StopOrderRequest
from alpaca.trading.requests import StopLossRequest
import os
from dotenv import load_dotenv
 
load_dotenv()
 
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

def marketbuy(symbol, qty, TIF=TimeInForce.GTC):
    
    market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
def marketsell(symbol, qty, TIF=TimeInForce.GTC):
    market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
def limitbuy(symbol, qty, limitprice, TIF=TimeInForce.GTC):
    market_order_data = LimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
def limitsell(symbol, qty, limitprice, TIF=TimeInForce.GTC):
    market_order_data = LimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )

def stoplimitbuy(symbol, qty, limitprice, stopprice, TIF=TimeInForce.GTC):
    market_order_data = StopLimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    stop_price=stopprice,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
def stoplimitsell(symbol, qty, limitprice, stopprice, TIF=TimeInForce.GTC):
    market_order_data = StopLimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    stop_price=stopprice,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )

def stopbuy(symbol, qty, limitprice, stopprice, TIF=TimeInForce.GTC):
    market_order_data = StopLimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    stop_price=stopprice,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
def stopsell(symbol, qty, limitprice, stopprice, TIF=TimeInForce.GTC):
    market_order_data = StopLimitOrderRequest(
                    symbol=symbol,
                    limit_price=limitprice,
                    stop_price=stopprice,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force= TIF
                    )
    market_order = trading_client.submit_order(
                order_data=market_order_data
               )
    
