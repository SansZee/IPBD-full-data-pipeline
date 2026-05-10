import yfinance as yf
import json
import os
from datetime import datetime

TICKERS = {
    "BZ=F": {"name": "Brent Crude", "unit": "barrel"},
    "CL=F": {"name": "West Texas Intermediate", "unit": "barrel"},
    "NG=F": {"name": "Natural Gas (Henry Hub)", "unit": "mmbtu"},
}

def get_current_price(ticker: str) -> dict:
    """Get current price for a commodity."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        return {
            "code": ticker,
            "price": round(price, 2) if price else None,
            "currency": "USD",
            "unit": TICKERS[ticker]["unit"],
            "source": "Yahoo Finance",
            "updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching current price for {ticker}: {e}")
    return None

def get_historical_prices(ticker: str, days: int = 180) -> list:
    """Get historical prices for a commodity."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=f"{days}d", interval="1d")
        return [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "price": round(row["Close"], 2),
                "currency": "USD",
            }
            for idx, row in df.iterrows()
        ]
    except Exception as e:
        print(f"Error fetching historical prices for {ticker}: {e}")
    return []

def main():
    print("Fetching oil price data (current + historical) from Yahoo Finance...")
    print("=" * 60)

    current_prices = []
    historical_data = {}

    for ticker in TICKERS:
        print(f"\nProcessing {ticker}...")

        current = get_current_price(ticker)
        if current:
            current_prices.append(current)
            print(f"  Current price: ${current['price']}")

        hist = get_historical_prices(ticker, days=180)
        if hist:
            historical_data[ticker] = {
                "name": TICKERS[ticker]["name"],
                "unit": TICKERS[ticker]["unit"],
                "data": hist
            }
            print(f"  Historical data: {len(hist)} points")

    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "yahoo.finance (yfinance)",
        "current_prices": current_prices,
        "historical": historical_data
    }

    output_file = os.path.join(os.path.dirname(__file__), "data", "oil_prices.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Saved to {output_file}")
    print(f"  Current prices: {len(current_prices)}")
    print(f"  Historical commodities: {len(historical_data)}")

    return output

if __name__ == "__main__":
    main()
