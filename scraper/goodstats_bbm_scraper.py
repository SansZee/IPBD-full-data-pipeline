import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

BASE_URL = "https://goodstats.id/data-trend/harga-bbm"
BRANDS = ["pertamina", "bp", "shell"]

REGIONS_BY_BRAND = {
    "pertamina": [
        "aceh", "bali", "riau", "batam", "jambi", "papua", "banten", "maluku",
        "sabang", "jakarta", "lampung", "bengkulu", "gorontalo", "jawa-barat",
        "jawa-timur", "jawa-tengah", "papua-barat", "maluku-utara", "papua-tengah",
        "di-yogyakarta", "papua-selatan", "kepulauan-riau", "sulawesi-barat",
        "sumatera-barat", "sumatera-utara", "bangka-belitung", "sulawesi-tengah",
        "kalimantan-barat", "kalimantan-timur", "kalimantan-utara",
        "papua-barat-daya", "papua-pegunungan", "sulawesi-selatan",
        "sumatera-selatan", "kalimantan-tengah", "sulawesi-tenggara",
        "kalimantan-selatan", "nusa-tenggara-barat", "nusa-tenggara-timur"
    ],
    "bp": ["jakarta", "jawa-timur"],
    "shell": ["jakarta", "jawa-timur"]
}

def get_regions_for_brand(brand: str) -> list:
    """Get regions for brand (using predefined list)."""
    return REGIONS_BY_BRAND.get(brand, [])

def extract_date(soup: BeautifulSoup) -> str:
    """Extract date from page (format: Minggu, 26 April 2026)."""
    text = soup.get_text()
    match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', text)
    if match:
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, "%d %B %Y")
            return dt.strftime("%Y-%m-%d")
        except:
            pass
    
    today = datetime.now().strftime("%Y-%m-%d")
    return today

def parse_price(price_text: str) -> int:
    """Parse price string like 'Rp12.800' to integer 12800."""
    price_text = price_text.replace("Rp", "").replace(".", "").strip()
    try:
        return int(price_text) if price_text != "0" else 0
    except:
        return 0

def scrape_region(brand: str, region: str) -> dict:
    """Scrape fuel prices for a specific brand and region."""
    url = f"{BASE_URL}/{brand}/{region}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    date = extract_date(soup)
    fuels = []
    
    h2_elements = soup.find_all("h2")
    for h2 in h2_elements:
        fuel_type = h2.get_text(strip=True).strip()
        if not fuel_type or not fuel_type[0].isalpha():
            continue
        
        p_elements = h2.find_all_next("p")
        for p in p_elements[:4]:
            p_text = p.get_text(strip=True)
            if p_text.startswith("Rp"):
                price = parse_price(p_text.replace(".", ""))
                if price is not None and price > 0:
                    fuels.append({
                        "type": fuel_type.lower().replace(" ", "_"),
                        "price": price
                    })
                break
    
    seen = set()
    unique_fuels = []
    for f in fuels:
        if f["type"] not in seen:
            seen.add(f["type"])
            unique_fuels.append(f)
    
    return {
        "source": "goodstats.id",
        "brand": brand,
        "region": region,
        "date": date,
        "fuels": unique_fuels
    }

def get_all_brands_regions() -> dict:
    """Get all brands and their available regions."""
    brand_regions = {}
    
    for brand in BRANDS:
        regions = get_regions_for_brand(brand)
        brand_regions[brand] = regions
    
    return brand_regions

def main():
    print("=" * 60)
    print("GoodStats BBM Price Scraper")
    print("=" * 60)
    
    brand_regions = get_all_brands_regions()
    
    all_data = {
        "scraped_at": datetime.now().isoformat(),
        "source": "goodstats.id",
        "data": []
    }
    
    total = sum(len(rs) for rs in brand_regions.values())
    current = 0
    
    print(f"Scraping {total} brand-region combinations...")
    
    for brand, regions in brand_regions.items():
        for region in regions:
            current += 1
            print(f"[{current}/{total}] {brand}/{region}...", end=" ")
            
            result = scrape_region(brand, region)
            if result and result["fuels"]:
                all_data["data"].append(result)
                print(f"✓ {len(result['fuels'])} fuels")
            else:
                print("✗ no data")
            
            time.sleep(0.3)
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "goodstats.id",
        "total_records": len(all_data["data"]),
        "records": all_data["data"]
    }
    
    output_file = "/home/portolas/kuliah/ipbd/IPBD-full-data-pipeline/scraper/data/bbm_prices.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Done! Saved {len(all_data['data'])} records to {output_file}")
    print("=" * 60)
    
    return output

if __name__ == "__main__":
    main()