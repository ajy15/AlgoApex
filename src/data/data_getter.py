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
    """Fetch historical data for a given symbol using Alpaca API."""
    start_date = datetime(year=2024, month=4, day=1)
    end_date = datetime.today()  # Use today's date for the end date
    print(start_date)

    timeframe = TimeFrame.Minute  # Set timeframe to Day

    all_data = pd.DataFrame()
    current_end = end_date
    chunk_size = 1  # Days per request

    while current_end >= start_date:
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

            chunk_data = chunk_data.between_time("9:00", "16:30")
            if not chunk_data.empty:
                all_data = pd.concat([chunk_data, all_data])
                # save_to_csv(
                #     chunk_data,
                #     f"src/data/stored_data/{symbol}_{current_start_str}_to_{current_end_str}.csv",
                # )
                print(
                    f"Fetched and saved data for {current_start_str} to {current_end_str}"
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

    # Save all collected data to a CSV
    save_to_csv(all_data, f"src/data/stored_data/{symbol}_all_data.csv")
    print(f"Total data collected: {len(all_data)} records")
    return all_data


# Example usage
symbol = "SPY"
data = get_historical_data(symbol, years=1)
