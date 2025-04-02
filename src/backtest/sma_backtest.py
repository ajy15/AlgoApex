import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame

# API Configuration
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
BASE_URL = "https://paper-api.alpaca.markets"  # Using paper trading by default


class SPYMovingAverageBot:
    def __init__(self, api_key, api_secret, base_url):
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.symbol = "SPY"
        self.timeframe = TimeFrame.Day
        self.position = 0
        self.is_market_open = False

    def check_market_hours(self):
        """Check if the market is open"""
        clock = self.api.get_clock()
        self.is_market_open = clock.is_open
        return self.is_market_open

    def get_historical_data(self, days=200):
        """Get historical price data for SPY"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        barset = self.api.get_bars(
            self.symbol,
            self.timeframe,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        ).df

        return barset

    def calculate_signals(self, data):
        """Calculate moving average signals"""
        data["sma_20"] = data["close"].rolling(window=20).mean()
        data["sma_50"] = data["close"].rolling(window=50).mean()
        data["sma_100"] = data["close"].rolling(window=100).mean()

        # Generate signals
        # Buy when SMA20 crosses above SMA50 and both are above SMA100
        # Sell when SMA20 crosses below SMA50
        data["signal"] = 0

        # SMA20 crosses above SMA50
        data.loc[
            (data["sma_20"] > data["sma_50"])
            & (data["sma_20"].shift(1) <= data["sma_50"].shift(1))
            & (data["sma_50"] > data["sma_100"]),
            "signal",
        ] = 1

        # SMA20 crosses below SMA50
        data.loc[
            (data["sma_20"] < data["sma_50"])
            & (data["sma_20"].shift(1) >= data["sma_50"].shift(1)),
            "signal",
        ] = -1

        return data

    def get_current_position(self):
        """Get current position of SPY"""
        try:
            position = self.api.get_position(self.symbol)
            self.position = int(position.qty)
        except:
            self.position = 0

        return self.position

    def get_buying_power(self):
        """Get current buying power"""
        account = self.api.get_account()
        return float(account.buying_power)

    def execute_trade(self, signal):
        """Execute trade based on signal"""
        self.get_current_position()

        if signal == 1 and self.position <= 0:  # Buy signal
            # Calculate number of shares based on available buying power
            buying_power = self.get_buying_power() * 0.95  # Using 95% of buying power
            latest_price = self.api.get_latest_trade(self.symbol).price
            shares_to_buy = int(buying_power / latest_price)

            if shares_to_buy > 0:
                print(
                    f"BUY: Submitting order for {shares_to_buy} shares of {self.symbol}"
                )
                self.api.submit_order(
                    symbol=self.symbol,
                    qty=shares_to_buy,
                    side="buy",
                    type="market",
                    time_in_force="day",
                )

        elif signal == -1 and self.position > 0:  # Sell signal
            print(
                f"SELL: Submitting order to sell {self.position} shares of {self.symbol}"
            )
            self.api.submit_order(
                symbol=self.symbol,
                qty=self.position,
                side="sell",
                type="market",
                time_in_force="day",
            )

    def run_strategy(self):
        """Run the trading strategy"""
        # Check if market is open
        if not self.check_market_hours():
            print("Market is closed. Waiting for market hours...")
            return

        print("Market is open. Running strategy...")

        # Get historical data
        historical_data = self.get_historical_data()

        # Calculate signals
        signals = self.calculate_signals(historical_data)

        # Get the latest signal
        latest_signal = signals["signal"].iloc[-1]

        if latest_signal != 0:
            print(f"Signal detected: {latest_signal}")
            self.execute_trade(latest_signal)
        else:
            print("No trading signal detected")

    def run_backtest(self, initial_capital=10000.0):
        """Run a backtest on historical data"""
        data = self.get_historical_data(days=365)  # Get a year of data
        signals = self.calculate_signals(data)

        # Add columns for backtest
        signals["position"] = signals["signal"].cumsum().shift(1).fillna(0)
        signals["returns"] = signals["close"].pct_change()
        signals["strategy_returns"] = signals["position"] * signals["returns"]

        # Calculate cumulative returns
        signals["cumulative_returns"] = (1 + signals["returns"]).cumprod()
        signals["cumulative_strategy_returns"] = (
            1 + signals["strategy_returns"]
        ).cumprod()

        # Calculate metrics
        total_return = signals["cumulative_strategy_returns"].iloc[-1]
        sharpe_ratio = (
            signals["strategy_returns"].mean()
            / signals["strategy_returns"].std()
            * np.sqrt(252)
        )

        print(f"Backtest Results for SPY Moving Average Strategy:")
        print(f"Period: {signals.index[0].date()} to {signals.index[-1].date()}")
        print(f"Initial Capital: ${initial_capital:.2f}")
        print(f"Final Capital: ${initial_capital * total_return:.2f}")
        print(f"Total Return: {(total_return - 1) * 100:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.4f}")

        return signals


if __name__ == "__main__":
    # Create the bot
    bot = SPYMovingAverageBot(API_KEY, API_SECRET, BASE_URL)

    # Run backtest
    backtest_results = bot.run_backtest()

    # # Run live trading
    # while True:
    #     try:
    #         bot.run_strategy()
    #         # Wait for 1 hour before checking again
    #         time.sleep(3600)
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         time.sleep(60)  # Wait a minute if there's an error
