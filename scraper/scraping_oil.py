import requests
import os
import json
from datetime import datetime, timedelta

api_key = "6f05fdaecd3e2263536da4d17a5f2d25128192bd2b5c0071845aa594786789b4"
base_url = "https://api.oilpriceapi.com"

codes = [
    "BRENT_CRUDE_USD",
    "WTI_USD",
    "NATURAL_GAS_USD",
]

COMMODITY_INFO = {
    "BRENT_CRUDE_USD": {"name": "Brent Crude", "unit": "barrel"},
    "WTI_USD": {"name": "West Texas Intermediate", "unit": "barrel"},
    "NATURAL_GAS_USD": {"name": "Natural Gas (Henry Hub)", "unit": "mmbtu"},
}

def get_current_price(code: str) -> dict:
    """Get current price for a commodity."""
    url = f"{base_url}/v1/prices/latest?by_code={code}"
    headers = {"Authorization": f"Token {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("status") == "success" and "data" in data:
            item = data["data"]
            return {
                "code": item.get("code"),
                "price": item.get("price"),
                "currency": item.get("currency"),
                "unit": item.get("unit"),
                "source": item.get("source"),
                "updated": item.get("updated_at")
            }
    except Exception as e:
        print(f"Error fetching current price for {code}: {e}")
    
    return None

def get_historical_prices(code: str, days: int = 180) -> list:
    """Get historical prices for a commodity."""
    url = f"{base_url}/v1/prices/historical"
    headers = {"Authorization": f"Token {api_key}"}
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        "by_code": code,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "interval": "1d",
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        data = response.json()
        
        if data.get("status") == "success" and "data" in data:
            prices = data["data"].get("prices", [])
            return [
                {
                    "date": p.get("created_at", "")[:10],
                    "price": p.get("price"),
                    "currency": p.get("currency"),
                }
                for p in prices
            ]
    except Exception as e:
        print(f"Error fetching historical prices for {code}: {e}")
    
    return []

def main():
    print("Fetching oil price data (current + historical) from oilpriceapi.com...")
    print("=" * 60)
    
    current_prices = []
    historical_data = {}
    
    for code in codes:
        print(f"\nProcessing {code}...")
        
        current = get_current_price(code)
        if current:
            current_prices.append(current)
            print(f"  Current price: ${current['price']}")
        
        hist = get_historical_prices(code, days=180)
        if hist:
            historical_data[code] = {
                "name": COMMODITY_INFO.get(code, {}).get("name", code),
                "unit": COMMODITY_INFO.get(code, {}).get("unit", "barrel"),
                "data": hist
            }
            print(f"  Historical data: {len(hist)} points")
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "oilpriceapi.com",
        "current_prices": current_prices,
        "historical": historical_data
    }
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(BASE_DIR, "data", "oil_prices.json")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Saved to {output_file}")
    print(f"  Current prices: {len(current_prices)}")
    print(f"  Historical commodities: {len(historical_data)}")
    
    return output

if __name__ == "__main__":
    main()