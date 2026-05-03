import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(data, filename):
    output_path = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extract_items(data):
    """Flatten semua kemungkinan struktur JSON jadi list of dict"""
    items = []

    if isinstance(data, dict):
        for value in data.values():
            items.extend(extract_items(value))

    elif isinstance(data, list):
        for item in data:
            items.extend(extract_items(item))

    elif isinstance(data, str):
        # abaikan string
        pass

    else:
        # kalau sudah dict-like
        if isinstance(data, dict):
            items.append(data)

    # kalau langsung dict
    if isinstance(data, dict) and any(isinstance(v, (str, int, float)) for v in data.values()):
        items.append(data)

    return items


def main():
    print("Starting transformation...")

    final_rows = []

    # =========================
    # OIL DATA
    # =========================
    oil = load_json("oil_prices.json")
    if oil:
        historical = oil.get("historical", {})
        for code, info in historical.items():
            for item in extract_items(info):
                if isinstance(item, dict):
                    final_rows.append({
                        "date": item.get("date"),
                        "category": "oil",
                        "commodity": code,
                        "price": item.get("price"),
                        "currency": item.get("currency"),
                        "source": "oilpriceapi"
                    })

    # =========================
    # BBM ASEAN
    # =========================
    asean = load_json("cnbc_asean_bbm_prices.json")
    for item in extract_items(asean):
        if isinstance(item, dict):
            final_rows.append({
                "date": item.get("date"),
                "category": "bbm_asean",
                "country": item.get("country"),
                "price": item.get("price"),
                "currency": "IDR",
                "source": "cnbc"
            })

    # =========================
    # INDONESIA
    # =========================
    indo = load_json("indonesia_bbm_historical.json")
    for item in extract_items(indo):
        if isinstance(item, dict):
            final_rows.append({
                "date": item.get("date"),
                "category": "bbm_indonesia",
                "type": item.get("type"),
                "price": item.get("price"),
                "currency": "IDR",
                "source": "indonesia"
            })

    # =========================
    # EXCHANGE RATE
    # =========================
    kurs = load_json("usd_idr_rates.json")
    for item in extract_items(kurs):
        if isinstance(item, dict):
            final_rows.append({
                "date": item.get("date"),
                "category": "exchange_rate",
                "pair": "USD/IDR",
                "price": item.get("rate"),
                "currency": "IDR",
                "source": "exchange"
            })

    # =========================
    # FINAL OUTPUT
    # =========================
    transformed = {
        "processed_at": datetime.now().isoformat(),
        "total_rows": len(final_rows),
        "data": final_rows
    }

    save_json(transformed, "transformed_data.json")

    print(f"Transformation complete! Total rows: {len(final_rows)}")


if __name__ == "__main__":
    main()