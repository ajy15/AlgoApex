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


def get_historical_data(
    data_filename, symbol, start_date, end_date, timeframe, chunk_size=1
):
    """Fetch historical price data, handling invalid dates gracefully."""
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    print(f"Start Date: {start_date:%Y-%m-%d}, End Date: {end_date:%Y-%m-%d}")

    print(
        f"Fetching 1-minute data for {symbol} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    all_data = pd.DataFrame()
    current_end = end_date

    while current_end >= start_date:
        current_start = current_end - timedelta(days=chunk_size)
        if current_start < start_date:
            current_start = start_date

        print(f"\n{'*' * 50}")
        try:
            print(
                f"\nFetching: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}"
            )

            # Format the chunk start and end dates
            current_start_str = current_start.strftime("%Y-%m-%d")
            current_end_str = current_end.strftime("%Y-%m-%d")

            chunk_data = alpaca.get_bars(
                symbol,
                timeframe,
                start=current_start_str,
                end=current_end_str,
                adjustment="all",
                limit=10000,
            ).df

            print(f"\tTotal Number of Bars Retrieved: {len(chunk_data)}")
            if not chunk_data.empty:
                market_hour_data = chunk_data.between_time("9:00", "16:30")
                all_data = pd.concat([market_hour_data, all_data])
            else:
                print("\tNo data returned for this date")

        except Exception as e:
            print(f"Error fetching data: {e}")

        print(f"{'+' * 50}\n")
        current_end = current_start - timedelta(days=1)
        time.sleep(0.2)

    # final save
    if not all_data.empty:
        all_data = all_data.sort_index()
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
symbol = "SPY"
START_DATE = "2015-04-01"
END_DATE = "2025-04-02"
TIMEFRAME = TimeFrame.Minute

DIRECTORY_PREFIX = "src/data/stored_data/"

DATA_FILENAME = (
    f"{DIRECTORY_PREFIX}{symbol}_all_data_start_date{START_DATE}_end_date{END_DATE}.csv"
)
INVALID_DATES_FILENAME = f"{DIRECTORY_PREFIX}{symbol}_invalid_dates_start_date{START_DATE}_end_date{END_DATE}.csv"


# Check if file exists, fetch if not
if os.path.exists(DATA_FILENAME):
    print(f"Loading data from {DATA_FILENAME}")
    extracted_all_data = pd.read_csv(DATA_FILENAME, index_col=0, parse_dates=True)
    print("Number of bars in loaded content: " + str(len(extracted_all_data)))
else:
    print(f"Fetching new data for {symbol}")
    extracted_all_data = get_historical_data(
        DATA_FILENAME,
        symbol,
        START_DATE,
        END_DATE,
        TIMEFRAME,
        chunk_size=1,
    )
