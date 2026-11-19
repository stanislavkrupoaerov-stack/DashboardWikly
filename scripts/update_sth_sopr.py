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

rows = []

for record in records:
    date = record.get("d")
    value = record.get("sthSopr")

    if date is None or value is None:
        continue

    rows.append({
        "date": date,
        "value": float(value)
    })

if not rows:
    raise ValueError("No valid STH SOPR records found")

rows.sort(key=lambda row: row["date"])

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(rows, file, ensure_ascii=False, indent=2)

latest = rows[-1]

print(
    f"Saved {len(rows)} STH SOPR records. "
    f"Latest: {latest['date']} = {latest['value']}"
)
