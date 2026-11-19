import json
import os
import requests

API_URL = "https://bitcoin-data.com/v1/sth-sopr"
OUTPUT_PATH = "data/sth-sopr.json"

token = os.environ.get("BITCOIN_DATA_API_TOKEN")

headers = {}
if token:
    headers["Authorization"] = f"Bearer {token}"

response = requests.get(API_URL, headers=headers, timeout=60)
response.raise_for_status()

records = response.json()

if not records:
    raise ValueError("API returned no STH SOPR records")

latest = records[-1]

date = latest["d"]
value = float(latest["sthSopr"])

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

data = {
    "date": date,
    "value": value
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"Saved STH SOPR {value} for {date} to {OUTPUT_PATH}")
