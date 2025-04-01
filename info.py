from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca_trade_api.rest import REST
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

trading_client = TradingClient(API_KEY, API_SECRET)

# Get our account information.
account = trading_client.get_account()

# Check our current balance vs. our balance at the last market close
balance_change = float(account.equity) - float(account.last_equity)
print(f'Today\'s portfolio balance change: ${balance_change}')
print(f'Buying Power: ${account.buying_power}')
print(f'Accrued Fees: ${account.accrued_fees}')
print(f'Portfolio Value: ${account.portfolio_value}')
print(f'Status: ${account.status}')



