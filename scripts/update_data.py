import json
import os
import urllib.request
import urllib.error

API_TOKEN = os.environ["BITCOIN_DATA_API_TOKEN"]

CANDIDATE_ENDPOINTS = [
    "supply-in-profit-percent",
    "supply-profit",
    "utxos-in-profit",
    "supply-in-profit",
    "percent-supply-in-profit"
]

def get_json(url):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "btc-supply-profit-site")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())

def normalize(rows):
    result = []

    for row in rows:
        date = row.get("d") or row.get("date")
        value = (
            row.get("supply_in_profit_percent")
            or row.get("supplyProfitPercent")
            or row.get("percent_supply_in_profit")
            or row.get("utxos_in_profit")
            or row.get("value")
            or row.get("v")
        )

        if date is not None and value is not None:
            result.append({
                "date": date,
                "value": float(value)
            })

    result.sort(key=lambda item: item["date"])
    return result

def main():
    rows = None
    used_endpoint = None

    for endpoint in CANDIDATE_ENDPOINTS:
        url = f"https://api.bitcoin-data.com/v1/{endpoint}?token={API_TOKEN}"
        print(f"Пробуем endpoint: {endpoint}")

        try:
            raw = get_json(url)
            print(f"Ответ получен. Тип: {type(raw).__name__}")

            if isinstance(raw, dict):
                print("Ключи ответа:", list(raw.keys()))

            normalized = normalize(raw)
            print(f"После нормализации записей: {len(normalized)}")

            if len(normalized) > 10:
                rows = normalized
                used_endpoint = endpoint
                break

        except urllib.error.HTTPError as error:
            print(f"HTTP ошибка {error.code} для {endpoint}")
        except Exception as error:
            print(f"Ошибка для {endpoint}: {error}")

    if rows is None:
        raise Exception(
            "Ни один endpoint не подошёл. "
            "Нужно найти точное название метрики в документации BGeometrics."
        )

    os.makedirs("data", exist_ok=True)

    output_path = "data/supply-in-profit.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    print(f"Файл создан: {output_path}")
    print(f"Сохранено записей: {len(rows)}")
    print(f"Использованный endpoint: {used_endpoint}")

if __name__ == "__main__":
    main()
