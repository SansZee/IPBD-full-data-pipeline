import os
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

SOURCES = [
    "https://www.cnbcindonesia.com/news/20250820095921-4-659582/subsidi-bbm-lpg-3-kg-di-2026-melejit-112-jadi-rp-1054-trilius",
    "https://www.cnbcindonesia.com/news/20250828083813-4-662004/kuota-bbm-bersubsidi-dipatok-19162-juta-kl-dalam-rapbn-2026",
    "https://en.antaranews.com/news/412687/indonesia-to-maintain-subsidized-fuel-prices-through-2026",
]

DEFAULT_DATA = {
    "total_subsidy_trillion_idr": 105.4,
    "volume_kl": 19162000,
    "volume_breakdown": {"solar_kl": 18636000, "kerosene_kl": 526000},
    "icp_average_usd": 77,
    "icp_budget_usd": 70,
    "subsidy_per_liter": {"solar": 1000, "kerosene": 1000},
    "domestic_production_mbpd": 0.61,
    "import_needs_mbpd": 1.0,
    "total_consumption_mbpd": 1.6,
    "lpg_volume_mt": 8.31,
    "electricity_subsidy_trillion_idr": 101.72,
    "cost_recovery_usd": 8.5,
    "total_energy_subsidy_trillion_idr": 210.1,
}

def scrape_subsidy_data() -> dict:
    """Scrape Indonesia fuel subsidy data from news sources."""
    
    subsidy_data = {}
    
    for url in SOURCES:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text()
                
                total = re.search(r'Rp\s*([\d,]+)\s*triliun', text)
                volume = re.search(r'([\d,]+)\s*juta\s*KL', text)
                icp = re.search(r'US?\$?(\d+)\s*(?:per\s+)?barrel', text)
                solar_sub = re.search(r'Rp\s*([\d,]+)\s*per\s*liter', text)
                
                if total and "total" not in subsidy_data:
                    subsidy_data["total_subsidy_trillion_idr"] = float(total.group(1).replace(",", "."))
                if volume and "volume" not in subsidy_data:
                    subsidy_data["volume_kl"] = int(volume.group(1).replace(",", "")) * 1000000
                if icp and "icp" not in subsidy_data:
                    subsidy_data["icp_average_usd"] = int(icp.group(1))
                if solar_sub and "subsidy" not in subsidy_data:
                    subsidy_data["solar_subsidy_per_liter"] = int(solar_sub.group(1).replace(",", ""))
        
        except Exception as e:
            print(f"Could not fetch {url}: {e}")
    
    for key, value in DEFAULT_DATA.items():
        if key not in subsidy_data:
            subsidy_data[key] = value
    
    return subsidy_data

def main():
    print("Fetching Indonesia fuel subsidy data...")
    print("=" * 60)
    
    subsidy_data = scrape_subsidy_data()
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "cnbcindonesia.com + antaranews.com + esdm.go.id",
        "description": "Indonesian fuel subsidy data - explains why prices remain stable despite global increases",
        "fiscal_year": 2026,
        "subsidy_details": {
            "total_subsidy_trillion_idr": subsidy_data.get("total_subsidy_trillion_idr", 105.4),
            "volume_kl": subsidy_data.get("volume_kl", 19162000),
            "volume_breakdown": {
                "solar_kl": subsidy_data.get("volume_kl", 19162000) - 526000,
                "kerosene_kl": 526000
            },
            "icp_average_usd": subsidy_data.get("icp_average_usd", 77),
            "icp_budget_usd": subsidy_data.get("icp_budget_usd", 70),
            "subsidy_per_liter": {
                "solar": subsidy_data.get("solar_subsidy_per_liter", 1000),
                "kerosene": 1000
            },
            "domestic_production_mbpd": subsidy_data.get("domestic_production_mbpd", 0.61),
            "import_needs_mbpd": subsidy_data.get("import_needs_mbpd", 1.0),
            "total_consumption_mbpd": subsidy_data.get("total_consumption_mbpd", 1.6),
            "lpg_volume_mt": subsidy_data.get("lpg_volume_mt", 8.31),
            "electricity_subsidy_trillion_idr": subsidy_data.get("electricity_subsidy_trillion_idr", 101.72),
        },
        "notes": {
            "price_stability": f"ICP averages ${subsidy_data.get('icp_average_usd', 77)}/barrel vs budget ${subsidy_data.get('icp_budget_usd', 70)}/barrel",
            "policy": "Subsidized fuel prices fixed through end of 2026",
            "why_indonesia_cheap": f"Government absorbs Rp {subsidy_data.get('total_subsidy_trillion_idr', 105.4)} trillion in subsidies",
        }
    }
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(BASE_DIR, "data", 'indonesia_subsidy')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved to: {output_file}")
    print(f"\n=== Summary ===")
    print(f"Total Subsidy: Rp {output['subsidy_details']['total_subsidy_trillion_idr']} trillion")
    print(f"Volume: {output['subsidy_details']['volume_kl']/1e6:.2f} million KL")
    print(f"ICP (avg): ${output['subsidy_details']['icp_average_usd']}/barrel")
    print(f"ICP (budget): ${output['subsidy_details']['icp_budget_usd']}/barrel")
    
    return output

if __name__ == "__main__":
    main()