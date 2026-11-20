import json
import os
import urllib.request
from pathlib import Path

TOKEN = os.environ.get("BITCOIN_DATA_API_TOKEN")

if not TOKEN:
    raise RuntimeError("BITCOIN_DATA_API_TOKEN is not set")

url = "https://bitcoin-data.com/v1/mvrv-zscore"

request = urllib.request.Request(url)
request.add_header("Authorization", f"Bearer {TOKEN}")
request.add_header("Accept", "application/json")

with urllib.request.urlopen(request, timeout=60) as response:
    payload = json.loads(response.read().decode("utf-8"))

rows = payload if isinstance(payload, list) else payload.get("data", [])

history = []

for row in rows:
    date = row.get("d") or row.get("date")
    value = row.get("mvrvZscore")

    if date is None or value is None:
        continue

    history.append({
        "date": str(date)[:10],
        "value": round(float(value), 6)
    })

history.sort(key=lambda item: item["date"])

if not history:
    raise ValueError("No MVRV Z-Score history returned by API")

output = Path("data")
output.mkdir(exist_ok=True)

with open(output / "mvrv-zscore.json", "w", encoding="utf-8") as file:
    json.dump(history, file, ensure_ascii=False, indent=2)

latest = history[-1]
print(f"Saved {len(history)} MVRV Z-Score points. Latest: {latest['date']} {latest['value']}")
