import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca_trade_api.rest import REST, TimeFrame
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")

alpaca = REST(API_KEY, API_SECRET, BASE_URL)

def save_to_csv(data, filename):
    """Save DataFrame to a CSV file, flattening the index."""
    if not data.empty:
        data.reset_index(inplace=True)  # Flatten the index
        data.to_csv(filename, index=False)
        print(f"Saved {len(data)} records to {filename}")
    else:
        print(f"No data to save for {filename}")


def analyze_time_gaps(df):
    """Analyze time gaps between consecutive data points and count gaps per day."""
    # Ensure the index is datetime
    df.index = pd.to_datetime(df.index)

    # Calculate time differences in minutes
    time_diffs = df.index.to_series().diff().dt.total_seconds() / 60

    # Create a DataFrame with dates and time differences
    gap_analysis = pd.DataFrame({"timestamp": df.index, "time_diff": time_diffs})

    # Group by date and count gaps (where time_diff > 1 minute)
    gap_analysis["date"] = gap_analysis["timestamp"].dt.date
    gaps_per_day = gap_analysis[gap_analysis["time_diff"] > 1].groupby("date").size()

    # Create a complete summary including days with no gaps
    all_dates = pd.date_range(
        start=df.index.min().date(), end=df.index.max().date(), freq="D"
    )
    gap_summary = pd.Series(0, index=all_dates)
    gap_summary.update(gaps_per_day)

    return gap_summary


def get_historical_data(symbol, start_date, end_date, chunk_size=1):
    """Fetch historical 1-minute price data and analyze time gaps."""

    # Convert string dates to datetime if necessary
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    print(f"Start Date: {start_date}, End Date: {end_date}")

    timeframe = TimeFrame.Minute

    all_data = pd.DataFrame()
    current_end = end_date

    while current_end >= start_date:
        current_start = current_end - timedelta(days=chunk_size)
        if current_start < start_date:
            current_start = start_date

        current_start_str = current_start.strftime("%Y-%m-%d")
        current_end_str = current_end.strftime("%Y-%m-%d")

        try:
            print(f"Fetching: {current_start_str} to {current_end_str}")
            chunk_data = alpaca.get_bars(
                symbol,
                timeframe,
                start=current_start_str,
                end=current_end_str,
                adjustment="all",
                limit=10000,
            ).df

            chunk_data = chunk_data.between_time("9:00", "16:30")
            if not chunk_data.empty:
                all_data = pd.concat([chunk_data, all_data])
                print(
                    f"Fetched {len(chunk_data)} bars of data for {current_start_str} to {current_end_str}"
                )

        except Exception as e:
            print(
                f"Error fetching data for {current_start_str} to {current_end_str}: {e}"
            )

        current_end = current_start - timedelta(days=1)
        time.sleep(0.5)

    all_data.sort_index(inplace=True)
    for col in ["open", "high", "low", "close"]:
        all_data[col] = all_data[col].astype("float32")
    all_data["volume"] = all_data["volume"].astype("int32")
    all_data.index = pd.to_datetime(all_data.index)
    market_hours_data = all_data.between_time("9:00", "16:30")

    # Save all collected data to a CSV
    save_to_csv(
        market_hours_data,
        f"src/data/stored_data/{symbol}_all_data_start_date{start_date}_end_date{end_date}.csv",
    )

    print(f"Total data collected: {len(market_hours_data)} records")

    return market_hours_data


# Example usage
symbol = "SPY"
daily_chunk_data = get_historical_data(
    symbol, start_date="2024-04-01", end_date="2025-04-02", chunk_size=1
)
