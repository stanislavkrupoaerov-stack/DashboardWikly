import json
import os
import urllib.request
import urllib.error

API_TOKEN = os.environ["BITCOIN_DATA_API_TOKEN"]

BASE_URL = "https://api.bitcoin-data.com/v1/"

DATE_KEYS = [
    "d",
    "date",
    "day",
    "timestamp",
    "time",
    "datetime"
]

METRICS = [
    {
        "name": "Supply in Profit %",
        "output": "data/supply-in-profit.json",
        "endpoints": ["profit-loss"],
        "value_keys": ["profitLoss"],
        "conversion": "profit_loss_ratio"
    },
    {
        "name": "Number of UTXOs in Profit %",
        "output": "data/utxo-in-profit.json",
        "endpoints": [
            "utxos-in-profit-pct"
        ],
        "value_keys": [
            "utxosInProfitPct",
            "utxoInProfit",
            "utxoProfit",
            "utxosInProfit",
            "utxoInProfitPercent"
        ],
        "conversion": "direct"
    },
    {
        "name": "Short-Term Holder SOPR",
        "output": "data/sth-sopr.json",
        "endpoints": [
            "sth-sopr"
        ],
        "value_keys": [
            "sthSopr"
        ],
        "conversion": "direct"
    },
    {
        "name": "NUPL",
        "output": "data/nupl.json",
        "endpoints": [
            "nupl"
        ],
        "value_keys": [
            "nupl"
        ],
        "conversion": "direct"
    },
    {
        "name": "MVRV Z-Score",
        "output": "data/mvrv-zscore.json",
        "endpoints": [
            "mvrv-zscore"
        ],
        "value_keys": [
            "mvrvZscore",
            "mvrvZScore"
        ],
        "conversion": "direct"
    },
    {
        "name": "Long-Term Holder SOPR",
        "output": "data/lth-sopr.json",
        "endpoints": [
            "lth-sopr"
        ],
        "value_keys": [
            "lthSopr"
        ],
        "conversion": "direct"
    }
]


def get_json(url):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "btc-metrics-site")

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


def find_value(row, metric):
    for key in metric["value_keys"]:
        if key in row:
            value = row[key]

            if isinstance(value, (int, float)):
                return float(value)

            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue

    return None


def convert_value(raw_value, conversion):
    value = float(raw_value)

    if conversion == "profit_loss_ratio":
        if value <= 0:
            return 0.0

        return value / (1 + value) * 100

    return value


def normalize_row(row, metric):
    if not isinstance(row, dict):
        return None

    date = find_date(row)
    raw_value = find_value(row, metric)

    if date is None or raw_value is None:
        return None

    value = convert_value(raw_value, metric["conversion"])

    return {
        "date": str(date),
        "value": round(value, 6)
    }


def normalize_rows(rows, metric):
    result = []

    for row in rows:
        normalized = normalize_row(row, metric)

        if normalized is not None:
            result.append(normalized)

    result.sort(key=lambda item: item["date"])
    return result


def get_list_response(endpoint):
    url = f"{BASE_URL}{endpoint}?token={API_TOKEN}"

    print(f"Пробуем endpoint: {endpoint}")

    try:
        raw = get_json(url)
    except urllib.error.HTTPError as error:
        print(f"API вернул ошибку {error.code} для {endpoint}")
        return None

    print(f"Ответ получен. Тип: {type(raw).__name__}")

    if isinstance(raw, dict):
        print("Ответ является объектом. Ключи:", list(raw.keys()))

        for key, value in raw.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"Найден список в ключе: {key}")
                raw = value
                break

    if not isinstance(raw, list) or len(raw) == 0:
        print("API вернул неожиданный формат данных.")
        return None

    first_row = raw[0]
    print("Поля первой записи:", list(first_row.keys()))
    print("Первая запись:", first_row)

    return raw


def get_latest_row(endpoint, metric):
    url = f"{BASE_URL}{endpoint}/last?token={API_TOKEN}"

    print(f"Пробуем endpoint /last: {endpoint}")

    try:
        raw = get_json(url)
    except urllib.error.HTTPError as error:
        print(f"Не удалось получить /last для {endpoint}: {error.code}")
        return None

    print("Последняя запись из /last:", raw)

    if isinstance(raw, list) and len(raw) > 0:
        raw = raw[-1]

    return normalize_row(raw, metric)


def update_metric(metric):
    print("")
    print("=" * 60)
    print(f"Обновление метрики: {metric['name']}")
    print("=" * 60)

    rows = None
    used_endpoint = None

    for endpoint in metric["endpoints"]:
        raw_rows = get_list_response(endpoint)

        if raw_rows is None:
            continue

        normalized_rows = normalize_rows(raw_rows, metric)

        if len(normalized_rows) < 10:
            print(
                "Не удалось надёжно определить дату и значение. "
                "JSON не изменён."
            )
            continue

        rows = normalized_rows
        used_endpoint = endpoint
        break

    if rows is None:
        print(
            f"Метрика '{metric['name']}' не обновлена: "
            "не найден подходящий endpoint или формат данных."
        )
        return False

    latest_row = get_latest_row(used_endpoint, metric)

    if latest_row is not None:
        print("Нормализованная запись /last:", latest_row)

        if not rows or latest_row["date"] > rows[-1]["date"]:
            rows.append(latest_row)
            print(f"Добавлена более свежая запись: {latest_row['date']}")
        else:
            print("Запись из /last не новее данных списка.")

    rows.sort(key=lambda item: item["date"])

    os.makedirs("data", exist_ok=True)

    with open(metric["output"], "w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    print(f"Файл создан: {metric['output']}")
    print(f"Сохранено записей: {len(rows)}")
    print(f"Последняя дата: {rows[-1]['date']}")
    print(f"Последнее значение: {rows[-1]['value']}")
    print(f"Использованный endpoint: {used_endpoint}")

    return True


def main():
    updated = 0
    failed = 0

    for metric in METRICS:
        try:
            if update_metric(metric):
                updated += 1
            else:
                failed += 1
        except Exception as error:
            failed += 1
            print(f"Ошибка при обновлении '{metric['name']}': {error}")

    print("")
    print("=" * 60)
    print(f"Успешно обновлено метрик: {updated} из {len(METRICS)}")
    print(f"Метрик с проблемами: {failed}")

    if failed > 0:
        print(
            "Проверьте блоки лога выше для метрик с проблемами. "
            "Существующие JSON-файлы не были перезаписаны сомнительными данными."
        )


if __name__ == "__main__":
    main()
