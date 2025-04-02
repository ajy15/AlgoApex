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


def get_historical_data(symbol, years=1):
    """Fetch historical 1-minute price data for a given symbol using Alpaca API."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365 * years)
    print(start_date)
    timeframe = TimeFrame.Minute

    # Format dates in RFC3339 format (YYYY-MM-DDTHH:MM:SS)
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")

    print(
        f"Fetching 1-minute data for {symbol} from {start_date_str} to {end_date_str}"
    )

    all_data = pd.DataFrame()
    current_end = end_date
    chunk_size = 7  # Days per request

    while current_end > start_date:
        current_start = current_end - timedelta(days=chunk_size)
        if current_start < start_date:
            current_start = start_date

        # Format the chunk start and end dates
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

            if not chunk_data.empty:
                all_data = pd.concat([chunk_data, all_data])
                print(f"Fetched {len(chunk_data)} bars")
        except Exception as e:
            print(f"Error fetching data: {e}")

        current_end = current_start - timedelta(seconds=1)
        time.sleep(0.5)

    if all_data.empty:
        print("Falling back to daily data...")
        try:
            daily_data = alpaca.get_bars(
                symbol,
                TimeFrame.Day,
                start=start_date_str,
                end=end_date_str,
                adjustment="all",
            ).df
            save_to_csv(daily_data, f"src/data/stored_data/{symbol}_daily_data.csv")
            return daily_data
        except Exception as e:
            print(f"Error fetching daily data: {e}")
            return pd.DataFrame()

    all_data.sort_index(inplace=True)
    for col in ["open", "high", "low", "close"]:
        all_data[col] = all_data[col].astype("float32")
    all_data["volume"] = all_data["volume"].astype("int32")
    all_data.index = pd.to_datetime(all_data.index)

    save_to_csv(all_data, f"src/data/stored_data/{symbol}_1min_data.csv")
    print(all_data)
    return all_data


# Example usage
symbol = "SPY"
data = get_historical_data(symbol, years=1)
