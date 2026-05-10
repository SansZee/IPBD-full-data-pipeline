import json
import time
import re
import os
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ASEAN_COUNTRIES = {
    "Indonesia": {"code": "IDN"},
    "Malaysia": {"code": "MYS"},
    "Thailand": {"code": "THA"},
    "Vietnam": {"code": "VNM"},
    "Philippines": {"code": "PHL"},
    "Singapore": {"code": "SGP"},
    "Myanmar": {"code": "MMR"},
    "Cambodia": {"code": "KHM"},
    "Laos": {"code": "LAO"},
    "Brunei": {"code": "BRN"},
}

BASE_URL = "https://www.eia.gov/international/data/country/{code}/electricity/electricity-imports"
API_URL = "https://www.eia.gov/international/api/series_data/data"

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_series_data_url(driver, country_name, country_code):
    url = BASE_URL.format(code=country_code)
    print(f"  Loading {country_name} page...")

    driver.get(url)
    time.sleep(5)

    logs = driver.get_log("performance")
    import json as j

    for log in logs:
        try:
            message = j.loads(log["message"])
            method = message.get("message", {}).get("method", "")
            if "Network.requestWillBeSent" in method:
                req_url = message.get("message", {}).get("params", {}).get("request", {}).get("url", "")
                if "series_data" in req_url:
                    return req_url
        except:
            pass

    return None

def fetch_data_from_api(series_url):
    params = {}
    if "?" in series_url:
        query_string = series_url.split("?")[1]
        for param in query_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                if key not in ["generated"]:
                    params[key] = value

    params["limit"] = "5000"

    try:
        response = requests.get(API_URL, params=params, timeout=60)
        return response.json()
    except Exception as e:
        print(f"  API request failed: {str(e)}")
        return None

def parse_api_data(api_data, country_name):
    if not api_data or "data" not in api_data:
        return {"country": country_name, "error": "No data in API response", "series": {}}

    series_data = api_data["data"]
    parsed = {}

    for series_id, values in series_data.items():
        year_values = []
        for year, val_list in sorted(values.items()):
            if val_list and len(val_list) > 0:
                val = val_list[0]
                if val is not None and val != "null":
                    try:
                        year_values.append({
                            "year": int(year),
                            "value": float(val) if isinstance(val, (int, float)) else val,
                        })
                    except (ValueError, TypeError):
                        pass

        if year_values:
            parsed[series_id] = {
                "values": year_values,
                "year_range": f"{year_values[0]['year']}-{year_values[-1]['year']}",
                "total_records": len(year_values),
            }

    return {"country": country_name, "series": parsed}

def main():
    print("=" * 60)
    print("EIA ASEAN Electricity Imports Scraper")
    print("=" * 60)

    all_data = {}
    successful = 0
    failed = 0

    driver = setup_driver()

    try:
        for country_name, country_info in ASEAN_COUNTRIES.items():
            series_url = get_series_data_url(driver, country_name, country_info["code"])

            if series_url:
                api_data = fetch_data_from_api(series_url)
                if api_data:
                    result = parse_api_data(api_data, country_name)
                    all_data[country_name] = result

                    series_count = len(result.get("series", {}))
                    if series_count > 0:
                        first_series = list(result["series"].values())[0]
                        print(f"  {country_name}: {first_series['year_range']} ({first_series['total_records']} records, {series_count} series)")
                        successful += 1
                    else:
                        print(f"  {country_name}: No series data")
                        failed += 1
                else:
                    print(f"  {country_name}: API request failed")
                    failed += 1
            else:
                print(f"  {country_name}: Could not get series URL")
                failed += 1

            time.sleep(1)
    finally:
        driver.quit()

    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "eia.gov",
        "description": "Electricity imports data for Southeast Asian countries",
        "summary": {
            "total_countries": len(ASEAN_COUNTRIES),
            "successful": successful,
            "failed": failed,
        },
        "data": all_data,
    }

    output_file = os.path.join(os.path.dirname(__file__), "data", "eia_electricity_imports.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Done! Saved to {output_file}")
    print(f"Successful: {successful}/{len(ASEAN_COUNTRIES)} countries")
    print(f"{'=' * 60}")

    return output

if __name__ == "__main__":
    main()
