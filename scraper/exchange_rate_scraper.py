import requests
import json
from datetime import datetime, timedelta

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/IDR%3DX"

def fetch_usd_idr_rate(days: int = 30) -> dict:
    """Fetch USD/IDR exchange rate from Yahoo Finance."""
    
    params = {
        "range": f"{days}d",
        "interval": "1d"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(YAHOO_URL, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if "chart" in data and data["chart"].get("result"):
            result = data["chart"]["result"][0]
            
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            
            historical = []
            for i, ts in enumerate(timestamps):
                close_price = quotes.get("close", [None])[i]
                if close_price is not None:
                    date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    historical.append({
                        "date": date,
                        "rate": round(close_price, 2),
                        "currency": "IDR"
                    })
            
            current_rate = historical[-1]["rate"] if historical else None
            
            return {
                "scraped_at": datetime.now().isoformat(),
                "source": "yahoo.finance",
                "currency_pair": "USD/IDR",
                "description": f"Indonesian Rupiah exchange rate to USD - {days} days history",
                "current_rate": current_rate,
                "historical": historical
            }
        
    except Exception as e:
        print(f"Error fetching USD/IDR: {e}")
        return None
    
    return None

def main():
    print("Fetching USD/IDR exchange rate...")
    print("=" * 60)
    
    output = fetch_usd_idr_rate(days=30)
    
    if output:
        output_file = "/home/portolas/kuliah/ipbd/IPBD-full-data-pipeline/scraper/data/usd_idr_rates.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Fetched {len(output['historical'])} data points")
        print(f"✓ Current rate: Rp {output['current_rate']:,.0f}/USD")
        print(f"✓ Date range: {output['historical'][0]['date']} to {output['historical'][-1]['date']}")
        print(f"✓ Saved to: {output_file}")
        
    else:
        print("Failed to fetch data")
    
    return output

if __name__ == "__main__":
    main()