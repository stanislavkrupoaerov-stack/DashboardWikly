import json
import os
from pathlib import Path

import requests

TOKEN = os.environ.get("BITCOIN_DATA_API_TOKEN")

if not TOKEN:
    raise ValueError("BITCOIN_DATA_API_TOKEN is not set")

BASE_URL = "https://bitcoin-data.com/v1/utxos-in-profit-pct"
OUTPUT_FILE = Path("data/utxo-in-profit.json")


def fetch_json(url):
    response = requests.get(
        url,
        params={"token": TOKEN},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def normalize(records):
    result = []

    for record in records:
        day = record.get("d")
        value = record.get("utxosInProfitPct")

        if day is None or value is None:
            continue

        result.append(
            {
                "date": day,
                "value": float(value),
            }
        )

    result.sort(key=lambda item: item["date"])
    return result


def main():
    history = fetch_json(BASE_URL)
    latest = fetch_json(BASE_URL + "/last")

    records = normalize(history)

    if latest:
        latest_records = normalize(latest if isinstance(latest, list) else [latest])

        if latest_records:
            last_date = records[-1]["date"] if records else ""
            latest_record = latest_records[-1]

            if latest_record["date"] > last_date:
                records.append(latest_record)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    if records:
        print(f"Saved {len(records)} records to {OUTPUT_FILE}")
        print(f"Last date: {records[-1]['date']}")
        print(f"Last value: {records[-1]['value']}%")
    else:
        raise ValueError("No valid UTXO in profit records received")


if __name__ == "__main__":
    main()
