import alpaca_trade_api as tradeapi
import pandas as pd
import time
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")

# Connect to Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version="v2")

df1 = pd.read_csv("src/data/stored_data/SPY_all_data_2015-04-01_to_2025-04-02.csv")

def save_to_csv(data, filename):
    """Save DataFrame to a CSV file, flattening the index."""
    if not data.empty:
        data.reset_index(inplace=True)  # Flatten the index
        data.to_csv(filename, index=False)
        print(f"Saved {len(data)} records to {filename}")
    else:
        print(f"No data to save for {filename}")
def compute_moving_averages(df, short_window=10, long_window=100):
    df["SMA50"] = df["close"].rolling(window=short_window).mean()
    df["SMA200"] = df["close"].rolling(window=long_window).mean()
    df["Signal"] = 0
    df.loc[df["SMA50"] > df["SMA200"], "Signal"] = 1  # Buy
    df.loc[df["SMA50"] < df["SMA200"], "Signal"] = -1  # Sell
    return df

df = compute_moving_averages(df1)

import pandas as pd
import numpy as np

def backtest(df, initial_capital=100000000):
    """
    Backtests the moving average strategy on the given DataFrame.

    Parameters:
    - df: DataFrame with 'Signal' and 'close' columns.
    - initial_capital: The starting amount of money.

    Returns:
    - A new DataFrame with performance metrics.
    """
    # Ensure no NaN values in signals
    df = df.dropna().copy()

    # Track capital and holdings
    capital = initial_capital
    shares = 0
    capital_over_time = []

    for i in range(len(df)):
        signal = df["Signal"].iloc[i]
        price = df["close"].iloc[i]

        if signal == 1 and capital >= price:  # Buy
            shares = capital // price  # Buy as many shares as possible
            capital -= shares * price

        elif signal == -1 and shares > 0:  # Sell
            capital += shares * price
            shares = 0  # Sell all holdings

        capital_over_time.append(capital + (shares * price))

    # Store results
    df["Strategy Capital"] = capital_over_time
    df["Buy & Hold"] = initial_capital * (df["close"] / df["close"].iloc[0])  # Market return

    return df

# Run backtest
df = backtest(df)
save_to_csv(df, "he.csv")
# Plot results
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["Strategy Capital"], label="Strategy Performance", color="green")
plt.plot(df.index, df["Buy & Hold"], label="Buy & Hold Performance", linestyle="--", color="blue")
plt.legend()
plt.title("Backtest: Moving Average Strategy vs. Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Portfolio Value ($)")
plt.show()


