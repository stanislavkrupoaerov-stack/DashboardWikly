import json
import os
import urllib.request

API_URL = (
    "https://cryptokeyhole.com/api/v1/fear-and-greed"
    "?coin=btc&format=json&limit=0"
)

OUTPUT_PATH = os.path.join("data", "fear-greed.json")


def fetch_history():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "DashboardWikly/1.0 (GitHub Pages Bitcoin metrics dashboard)"
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(
                f"CryptoKeyhole API returned HTTP {response.status}"
            )

        payload = json.loads(response.read().decode("utf-8"))

    history = payload.get("history")

    if not isinstance(history, list):
        raise RuntimeError("CryptoKeyhole API response does not contain history")

    return history


def normalize_history(history):
    normalized = []

    for item in history:
        date = item.get("date")
        value = item.get("value")

        if not date or value is None:
            continue

        try:
            value = int(value)
        except (TypeError, ValueError):
            continue

        if value < 0 or value > 100:
            continue

        normalized.append(
            {
                "date": date,
                "value": value,
            }
        )

    normalized.sort(key=lambda item: item["date"])

    return normalized


def save_history(records):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def main():
    history = fetch_history()
    records = normalize_history(history)

    if not records:
        raise RuntimeError("No valid Fear & Greed Index records were received")

    save_history(records)

    last_date = records[-1]["date"]
    last_value = records[-1]["value"]

    print(f"Saved {len(records)} Fear & Greed Index points")
    print(f"Last date: {last_date}")
    print(f"Last value: {last_value}")


if __name__ == "__main__":
    main()
