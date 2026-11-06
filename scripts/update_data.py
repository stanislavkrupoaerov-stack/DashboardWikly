import json
import os
import urllib.request
import urllib.error

API_TOKEN = os.environ["BITCOIN_DATA_API_TOKEN"]

ENDPOINT = "profit-loss"

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
    preferred_keys = []

    for key in row:
        key_lower = key.lower()

        if "profit" in key_lower or "percent" in key_lower:
            preferred_keys.append(key)

    for key in preferred_keys:
        value = row[key]

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue

    for key, value in row.items():
        key_lower = key.lower()

        if key == date_key:
            continue

        if key_lower in ["timestamp", "time", "unix", "ts"]:
            continue

        if isinstance(value, (int, float)):
            if 0 <= float(value) <= 100:
                return float(value)

        if isinstance(value, str):
            try:
                number = float(value)
                if 0 <= number <= 100:
                    return number
            except ValueError:
                continue

    return None


def normalize_row(row):
    if not isinstance(row, dict):
        return None

    date = find_date(row)
    value = find_value(row)

    if date is None or value is None:
        return None

    ratio = float(value)

    if ratio <= 0:
        percent = 0.0
    else:
        percent = ratio / (1 + ratio) * 100

    return {
        "date": str(date),
        "value": round(percent, 4)
    }


def normalize_rows(rows):
    result = []

    for row in rows:
        normalized = normalize_row(row)

        if normalized is not None:
            result.append(normalized)

    result.sort(key=lambda item: item["date"])
    return result


def get_list_response():
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

    return raw


def get_latest_row():
    url = f"https://api.bitcoin-data.com/v1/{ENDPOINT}/last?token={API_TOKEN}"

    print("Пробуем endpoint /last")

    try:
        raw = get_json(url)
    except urllib.error.HTTPError as error:
        print(f"Не удалось получить /last: {error.code}")
        return None

    print("Последняя запись из /last:", raw)

    if isinstance(raw, list) and len(raw) > 0:
        raw = raw[-1]

    return normalize_row(raw)


def main():
    raw_rows = get_list_response()
    rows = normalize_rows(raw_rows)

    print(f"После нормализации записей: {len(rows)}")

    latest_row = get_latest_row()

    if latest_row is not None:
        print("Нормализованная запись /last:", latest_row)

        if not rows or latest_row["date"] > rows[-1]["date"]:
            rows.append(latest_row)
            print(f"Добавлена более свежая запись: {latest_row['date']}")
        else:
            print("Запись из /last не новее данных списка.")

    rows.sort(key=lambda item: item["date"])

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
    print(f"Последняя дата: {rows[-1]['date']}")
    print(f"Последнее значение: {rows[-1]['value']}")
    print(f"Использованный endpoint: {ENDPOINT}")


if __name__ == "__main__":
    main()
