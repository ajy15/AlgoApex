import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = os.getenv('BASE_URL')

from alpaca_trade_api.rest import REST

alpaca = REST(API_KEY, API_SECRET, BASE_URL)

# Get latest price for AAPL
def getAPPL():
    barset = alpaca.get_latest_bar("AAPL")
    print(barset)
