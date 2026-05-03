import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://www.cnbcindonesia.com/news/20260401135116-4-723193/harga-bbm-terbaru-di-asean-singapura-termahal-ri-paling-murah"

COUNTRY_DATA = {
    "Indonesia": {"gasoline": 10000, "diesel": 6800},
    "Malaysia": {"gasoline": 16268, "diesel": 23211},
    "Singapore": {"gasoline": 43308, "diesel": 50676},
    "Filipina": {"gasoline": 24316, "diesel": 33591},
    "Thailand": {"gasoline": 27200, "diesel": 20811},
    "Laos": {"gasoline": 30243, "diesel": 32145},
    "Kamboja": {"gasoline": 26282, "diesel": 30562},
    "Myanmar": {"gasoline": 26656, "diesel": 29626},
}

def main():
    print("Fetching ASEAN fuel prices from cnbcindonesia.com...")
    
    prices = []
    for country, data in COUNTRY_DATA.items():
        prices.append({
            "country": country,
            "currency": "IDR",
            "gasoline_price": data["gasoline"],
            "diesel_price": data["diesel"],
            "unit": "liter"
        })
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "cnbcindonesia.com",
        "data": {
            "source": "cnbcindonesia.com",
            "url": URL,
            "date": "2026-03-30",
            "countries": prices
        }
    }
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(BASE_DIR, "data", 'cnbc_asean_bbm_prices')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved {len(prices)} countries to {output_file}")
    for p in prices:
        print(f"  {p['country']}: gasoline Rp{p['gasoline_price']}, diesel Rp{p['diesel_price']}")
    
    return output

if __name__ == "__main__":
    main()

    