import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

URL = "https://databoks.katadata.co.id/energi/statistik/69e57f877c750/harga-bbm-non-subsidi-pertamina-melonjak-pada-april-2026-ini-rinciannya"

HTML_TABLE = """
<table class="table table-striped text-left chart-data-datapublish">
<thead>
	<tr>
		<th>Nama Data</th>
		<th>sebelum naik</th>
		<th>sesudah naik</th>
	</tr>
</thead>
<tbody>
	<tr>
		<td>Pertamina Dex</td>
		<td>14.500</td>
		<td>23.900</td>
	</tr>
	<tr>
		<td>Dexlite</td>
		<td>14.200</td>
		<td>23.600</td>
	</tr>
	<tr>
		<td>Pertamax Turbo</td>
		<td>13.100</td>
		<td>19.400</td>
	</tr>
	<tr>
		<td>Pertamax Green</td>
		<td>12.900</td>
		<td>12.900</td>
	</tr>
	<tr>
		<td>Pertamax</td>
		<td>12.600</td>
		<td>12.600</td>
	</tr>
	<tr>
		<td>Pertalite</td>
		<td>10.000</td>
		<td>10.000</td>
	</tr>
	<tr>
		<td>Biosolar</td>
		<td>6.800</td>
		<td>6.800</td>
	</tr>
</tbody>
</table>
"""

FUEL_MAPPING = {
    "pertamina dex": "Pertamina Dex",
    "dexlite": "Dexlite",
    "pertamax turbo": "Pertamax Turbo",
    "pertamax green": "Pertamax Green 95",
    "pertamax": "Pertamax",
    "pertalite": "Pertalite",
    "biosolar": "Biosolar",
}

def normalize_fuel_name(name: str) -> str:
    name_lower = name.lower().strip()
    for key, mapped in FUEL_MAPPING.items():
        if key in name_lower:
            return mapped
    return name.strip()

def is_subsidi(fuel_name: str) -> bool:
    subsidi_types = ["pertalite", "biosolar"]
    return any(s in fuel_name.lower() for s in subsidi_types)

def parse_from_html(html_content: str) -> list:
    """Parse table from HTML string."""
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    
    if not table:
        return []
    
    fuels = []
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")
    
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        
        fuel_name = cells[0].get_text(strip=True)
        before_price = cells[1].get_text(strip=True).replace(".", "")
        after_price = cells[2].get_text(strip=True).replace(".", "")
        
        if not fuel_name:
            continue
        
        fuel_name = normalize_fuel_name(fuel_name)
        
        fuels.append({
            "type": fuel_name,
            "before_price": int(before_price) if before_price.isdigit() else 0,
            "after_price": int(after_price) if after_price.isdigit() else 0,
            "currency": "IDR",
            "unit": "liter",
        })
    
    return fuels

def main():
    print("Parsing table data...")
    
    fuels = parse_from_html(HTML_TABLE)
    
    if not fuels:
        print("No data found!")
        return None
    
    non_subsidi = []
    subsidi = []
    
    for f in fuels:
        if is_subsidi(f["type"]):
            subsidi.append(f)
        else:
            non_subsidi.append(f)
    
    data = {
        "source": "databoks.katadata.co.id",
        "url": URL,
        "date": "2026-04-18",
        "fuels": {
            "non_subsidi": non_subsidi,
            "subsidi": subsidi
        }
    }
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "source": "databoks.katadata.co.id",
        "data": data
    }
    
    output_file = "/home/portolas/kuliah/ipbd/IPBD-full-data-pipeline/scraper/data/katadata_bbm_prices.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Saved data to {output_file}")
    print(f"  Non-subsidi: {len(non_subsidi)} fuels")
    print(f"  Subsidi: {len(subsidi)} fuels")
    
    for f in fuels:
        print(f"    {f['type']}: {f['before_price']} -> {f['after_price']}")
    
    return output

if __name__ == "__main__":
    main()