from alpaca.trading.client import TradingClient
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

trading_client = TradingClient(API_KEY, API_SECRET)

def getall():
    # Get a list of all of our positions.
    portfolio = trading_client.get_all_positions()

    # Print the quantity of shares for each position.
    for position in portfolio:
        print("\n{} share(s) of {}".format(position.qty, position.symbol))
        print("{} is currently trading at {}".format(position.symbol, position.current_price))
        print("Unrealized PL: " + position.unrealized_pl + "\n")