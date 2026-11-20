import json
import os
import urllib.request

API_URL = "https://bitcoin-data.com/v1/lth-sopr"
OUTPUT_PATH = "data/lth-sopr.json"


def get_api_token():
    token = os.environ.get("BITCOIN_DATA_API_TOKEN")

    if not token:
        raise RuntimeError(
            "Не найдена переменная окружения BITCOIN_DATA_API_TOKEN. "
            "Проверьте GitHub Secrets."
        )

    return token.strip()


def request_data():
    token = get_api_token()

    request = urllib.request.Request(API_URL)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/json")

    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"API вернул статус {response.status}")

        raw_data = response.read().decode("utf-8")

    return json.loads(raw_data)


def normalize_records(raw_data):
    if not isinstance(raw_data, list):
        raise RuntimeError("API вернул неожиданный формат данных: ожидается список.")

    records = []

    for item in raw_data:
        if not isinstance(item, dict):
            continue

        date = item.get("d") or item.get("date")
        value = item.get("lthSopr")

        if value is None:
            value = item.get("lth-sopr")

        if value is None:
            value = item.get("value")

        if not date or value is None:
            continue

        try:
            value = round(float(value), 6)
        except (TypeError, ValueError):
            continue

        records.append(
            {
                "date": str(date),
                "value": value
            }
        )

    records.sort(key=lambda record: record["date"])

    return records


def save_records(records):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    if not records:
        raise RuntimeError("Не удалось сохранить данные: получен пустой список.")

    last_record = records[-1]

    print(f"Сохранено точек: {len(records)}")
    print(f"Последняя дата: {last_record['date']}")
    print(f"Последнее значение LTH SOPR: {last_record['value']}")


def main():
    raw_data = request_data()
    records = normalize_records(raw_data)
    save_records(records)


if __name__ == "__main__":
    main()
