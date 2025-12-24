# -*- coding: utf-8 -*-
import requests
from datetime import datetime, timedelta
import sys
import io

# UTF-8 output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "https://coupang-wing-cs-backend.fly.dev/api"

# Fetch returns for last 90 days in batches
total_fetched = 0
batch_days = 7  # 7 days per batch

print("Fetching returns from Coupang...")
print(f"Period: Last 90 days")
print(f"Batch size: {batch_days} days\n")

for i in range(0, 90, batch_days):
    end_date = datetime.now() - timedelta(days=i)
    start_date = end_date - timedelta(days=batch_days)

    start_str = start_date.strftime("%Y-%m-%dT%H:%M")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M")

    print(f"Batch {i//batch_days + 1}: {start_str} ~ {end_str}")

    try:
        response = requests.get(
            f"{API_BASE_URL}/returns/fetch-from-coupang",
            params={
                "start_date": start_str,
                "end_date": end_str
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            fetched = data.get("total_fetched", 0)
            saved = data.get("saved", 0)
            updated = data.get("updated", 0)

            total_fetched += fetched
            print(f"  -> Fetched: {fetched}, Saved: {saved}, Updated: {updated}")
        else:
            print(f"  -> Error: {response.status_code}")

    except Exception as e:
        print(f"  -> Exception: {str(e)}")

print(f"\nTotal fetched: {total_fetched}")

# Now check the database
print("\n" + "="*50)
print("Checking database...")

response = requests.get(f"{API_BASE_URL}/returns/statistics")
if response.status_code == 200:
    stats = response.json()
    if stats.get("success"):
        statistics = stats.get("statistics", {})
        print(f"\nTotal in database: {statistics.get('total', 0)}")
        print(f"Status breakdown: {statistics.get('status', {})}")
