import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca_trade_api.rest import REST, TimeFrame
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")

alpaca = REST(API_KEY, API_SECRET, BASE_URL)


def save_to_csv(data, filename):
    """Save DataFrame to a CSV file, flattening the index."""
    if not data.empty:
        data.reset_index(inplace=True)
        data.to_csv(filename, index=False)
        print(f"Saved {len(data)} records to {filename}")
    else:
        print(f"No data to save for {filename}")


def fetch_chunk(symbol, start, end, timeframe):
    """Fetch a single date range chunk from Alpaca API."""
    try:
        chunk_data = alpaca.get_bars(
            symbol,
            timeframe,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            adjustment="all",
            limit=10000,
        ).df
        if not chunk_data.empty:
            return chunk_data.between_time("9:00", "16:30")
    except Exception as e:
        print(f"Error fetching data for {start} - {end}: {e}")
    return pd.DataFrame()


def get_historical_data_parallel(
    data_filename, symbol, start_date, end_date, timeframe, chunk_size=1, max_workers=4
):
    """Fetch historical price data in parallel."""
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    date_ranges = []
    current_end = end_date
    while current_end >= start_date:
        current_start = max(start_date, current_end - timedelta(days=chunk_size))
        date_ranges.append((current_start, current_end))
        current_end = current_start - timedelta(days=1)

    all_data = pd.DataFrame()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_chunk, symbol, start, end, timeframe): (start, end)
            for start, end in date_ranges
        }

        for future in as_completed(futures):
            chunk_data = future.result()
            if not chunk_data.empty:
                all_data = pd.concat([chunk_data, all_data])

    if not all_data.empty:
        all_data.sort_index(inplace=True)
        all_data = all_data.astype(
            {
                "open": "float32",
                "high": "float32",
                "low": "float32",
                "close": "float32",
                "volume": "int32",
            }
        )
        all_data.index = pd.to_datetime(all_data.index)
        save_to_csv(all_data, data_filename)
    else:
        print("No data collected across the entire period")

    return all_data


# Example usage
symbol = "TQQQ"
START_DATE = "2015-04-01"
END_DATE = "2025-04-02"
TIMEFRAME = TimeFrame.Minute
DIRECTORY_PREFIX = "src/data/stored_data/"
DATA_FILENAME = f"{DIRECTORY_PREFIX}{symbol}_all_data_{START_DATE}_to_{END_DATE}.csv"

if os.path.exists(DATA_FILENAME):
    print(f"Loading data from {DATA_FILENAME}")
    extracted_all_data = pd.read_csv(DATA_FILENAME, index_col=0, parse_dates=True)
    print(f"Number of bars in loaded content: {len(extracted_all_data)}")
else:
    print(f"Fetching new data for {symbol}")
    extracted_all_data = get_historical_data_parallel(
        DATA_FILENAME,
        symbol,
        START_DATE,
        END_DATE,
        TIMEFRAME,
        chunk_size=1,
        max_workers=6
    )
