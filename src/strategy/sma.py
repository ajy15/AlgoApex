import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca.data.historical import StockHistoricalDataClient

# API Configuration
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")


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

    def get_historical_data(self, years=1):
        """Get historical price data for SPY"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)

        # For extended historical data, we may need to use multiple API calls
        # Alpaca may limit how far back we can fetch in a single call
        try:
            print(
                f"Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            barset = self.api.get_bars(
                self.symbol,
                self.timeframe,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
            ).df

            print(f"Fetched {len(barset)} bars of historical data")
            return barset

        except Exception as e:
            print(f"Error fetching historical data: {e}")

            # Alternative: For very long historical data, you might need to use a different data source
            # This is a fallback option for demonstration - you'd need to implement the actual code
            print(
                "Alpaca might limit historical data. Consider using an alternative data source like Yahoo Finance."
            )
            print("Example implementation using yfinance:")
            print("import yfinance as yf")
            print(
                "data = yf.download('SPY', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))"
            )
            print("data.columns = [col.lower() for col in data.columns]")

            # Return limited data we can get
            shorter_start = end_date - timedelta(days=365 * 2)  # Try with just 2 years
            barset = self.api.get_bars(
                self.symbol,
                self.timeframe,
                start=shorter_start.strftime("%Y-%m-%d"),
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

    def run_backtest(self, initial_capital=10000.0, years=10):
        """Run a backtest on historical data"""
        print(f"Running backtest with {years} years of historical data...")

        # Get historical data - using yfinance as an alternative for longer history
        try:
            # First try with Alpaca API
            data = self.get_historical_data(years=years)
        except Exception as e:
            print(f"Error with Alpaca API, trying yfinance: {e}")
            # Fallback to yfinance if needed
            import yfinance as yf

            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * years)

            data = yf.download(
                "SPY",
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
            )
            data.columns = [col.lower() for col in data.columns]

        # Calculate signals
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
        signals["strategy_equity"] = (
            initial_capital * signals["cumulative_strategy_returns"]
        )
        signals["buy_hold_equity"] = initial_capital * signals["cumulative_returns"]

        # Calculate metrics
        total_return = signals["cumulative_strategy_returns"].iloc[-1]
        buy_hold_return = signals["cumulative_returns"].iloc[-1]
        sharpe_ratio = (
            signals["strategy_returns"].mean()
            / signals["strategy_returns"].std()
            * np.sqrt(252)
        )
        max_drawdown = (
            signals["strategy_equity"] / signals["strategy_equity"].cummax() - 1
        ).min()

        # Calculate annual returns
        years_in_backtest = (signals.index[-1] - signals.index[0]).days / 365
        annual_return = (total_return ** (1 / years_in_backtest)) - 1

        # Count trades
        trades = signals["signal"].abs().sum()

        print(f"\nBacktest Results for SPY Moving Average Strategy:")
        print(
            f"Period: {signals.index[0].date()} to {signals.index[-1].date()} ({years_in_backtest:.2f} years)"
        )
        print(f"Initial Capital: ${initial_capital:.2f}")
        print(f"Final Capital: ${initial_capital * total_return:.2f}")
        print(f"Total Return: {(total_return - 1) * 100:.2f}%")
        print(f"Buy & Hold Return: {(buy_hold_return - 1) * 100:.2f}%")
        print(f"Annual Return: {annual_return * 100:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
        print(f"Maximum Drawdown: {max_drawdown * 100:.2f}%")
        print(f"Number of Trades: {trades}")

        # Plot results
        self.plot_backtest_results(signals, initial_capital)

        return signals

    def plot_backtest_results(self, signals, initial_capital):
        """Plot the results of the backtest"""
        plt.figure(figsize=(12, 8))

        # Plot equity curves
        plt.subplot(2, 1, 1)
        plt.plot(signals.index, signals["strategy_equity"], label="Strategy")
        plt.plot(signals.index, signals["buy_hold_equity"], label="Buy & Hold")
        plt.title("SPY Moving Average Strategy Performance")
        plt.ylabel("Portfolio Value ($)")
        plt.legend()
        plt.grid(True)

        # Plot drawdown
        plt.subplot(2, 1, 2)
        drawdown = signals["strategy_equity"] / signals["strategy_equity"].cummax() - 1
        plt.plot(signals.index, drawdown * 100)
        plt.title("Strategy Drawdown")
        plt.ylabel("Drawdown (%)")
        plt.grid(True)

        # Save the plot
        plt.tight_layout()
        plt.savefig("backtest_results.png")
        plt.close()

        print("\nBacktest plot saved as 'backtest_results.png'")


if __name__ == "__main__":
    # Create the bot
    bot = SPYMovingAverageBot(API_KEY, API_SECRET, BASE_URL)

    # Run backtest with 10 years of data
    backtest_results = bot.run_backtest(years=10, initial_capital=100000)

    # Optional: Run live trading
    # while True:
    #     try:
    #         bot.run_strategy()
    #         # Wait for 1 hour before checking again
    #         time.sleep(3600)
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         time.sleep(60)  # Wait a minute if there's an error
