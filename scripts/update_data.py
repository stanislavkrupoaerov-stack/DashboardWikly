import json
import os
import urllib.request
import urllib.error

API_TOKEN = os.environ["BITCOIN_DATA_API_TOKEN"]

ENDPOINT = "supply-profit"

DATE_KEYS = [
    "d", "date", "day", "timestamp", "time", "datetime"
]

def get_json(url):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "btc-supply-profit-site")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())

def find_date(row):
    for key in DATE_KEYS:
        if key in row:
            return row[key]

    for key, value in row.items():
        if isinstance(value, str) and ("-" in value or ":" in value):
            return value

    return None

def find_value(row, date_key=None):
    for key, value in row.items():
        if key == date_key:
            continue

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue

    return None

def normalize(rows):
    result = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        date = find_date(row)
        value = find_value(row)

        if date is not None and value is not None:
            result.append({
                "date": str(date),
                "value": value
            })

    result.sort(key=lambda item: item["date"])
    return result

def main():
    url = f"https://api.bitcoin-data.com/v1/{ENDPOINT}?token={API_TOKEN}"

    print(f"Пробуем endpoint: {ENDPOINT}")

    try:
        raw = get_json(url)
    except urllib.error.HTTPError as error:
        raise Exception(f"API вернул ошибку {error.code} для {ENDPOINT}")

    print(f"Ответ получен. Тип: {type(raw).__name__}")

    if isinstance(raw, dict):
        print("Ответ является объектом. Ключи:", list(raw.keys()))

        for key, value in raw.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"Найден список в ключе: {key}")
                raw = value
                break

    if not isinstance(raw, list) or len(raw) == 0:
        raise Exception("API вернул неожиданный формат данных.")

    first_row = raw[0]
    print("Поля первой записи:", list(first_row.keys()))
    print("Первая запись:", first_row)

    rows = normalize(raw)

    print(f"После нормализации записей: {len(rows)}")

    if len(rows) < 10:
        raise Exception(
            "Не удалось распознать дату и значение в данных. "
            "Нужно посмотреть поля первой записи в логе."
        )

    os.makedirs("data", exist_ok=True)

    output_path = "data/supply-in-profit.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    print(f"Файл создан: {output_path}")
    print(f"Сохранено записей: {len(rows)}")
    print(f"Использованный endpoint: {ENDPOINT}")

if __name__ == "__main__":
    main()
