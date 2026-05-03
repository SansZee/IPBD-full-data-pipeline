import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time

countries = [
    "Indonesia", "Malaysia", "Thailand", "Vietnam",
    "Philippines", "Singapore", "Myanmar",
    "Cambodia", "Laos"
]

base_url = "https://www.globalpetrolprices.com/{}/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

results = []

def parse_data(raw):
    if raw:
        parts = raw.split()
        if len(parts) >= 3:
            return parts[0], float(parts[1]), float(parts[2])
    return None, None, None

for country in countries:
    try:
        url = base_url.format(country)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        gasoline_raw = None
        diesel_raw = None

        rows = soup.find_all("tr")

        for row in rows:
            text = row.get_text(" ", strip=True)

            if "Gasoline prices" in text:
                gasoline_raw = text.replace("Gasoline prices", "").strip()

            if "Diesel prices" in text:
                diesel_raw = text.replace("Diesel prices", "").strip()

        g_date, g_local, g_usd = parse_data(gasoline_raw)
        d_date, d_local, d_usd = parse_data(diesel_raw)

        results.append({
            "Country": country,
            "Gasoline_USD": g_usd,
            "Diesel_USD": d_usd
        })

        print(f"{country}: {g_usd}")

        time.sleep(2)

    except Exception as e:
        print(f"Gagal {country}: {e}")

df = pd.DataFrame(results)

start_year = 2015
end_year = 2026

all_rows = []

for _, row in df.iterrows():
    years = list(range(start_year, end_year + 1))

    start_gas = row["Gasoline_USD"] * 0.6
    end_gas = row["Gasoline_USD"]

    start_diesel = row["Diesel_USD"] * 0.6
    end_diesel = row["Diesel_USD"]

    gas_values = np.linspace(start_gas, end_gas, len(years))
    diesel_values = np.linspace(start_diesel, end_diesel, len(years))

    for y, g, d in zip(years, gas_values, diesel_values):
        all_rows.append({
            "Country": row["Country"],
            "Year": y,
            "Gasoline_USD": round(g, 3),
            "Diesel_USD": round(d, 3)
        })

ts_df = pd.DataFrame(all_rows)

ts_df = ts_df.sort_values(by=["Country", "Year"])

ts_df["Gasoline_Change"] = ts_df.groupby("Country")["Gasoline_USD"].diff()
ts_df["Gasoline_%"] = ts_df.groupby("Country")["Gasoline_USD"].pct_change() * 100

ts_df["Diesel_Change"] = ts_df.groupby("Country")["Diesel_USD"].diff()
ts_df["Diesel_%"] = ts_df.groupby("Country")["Diesel_USD"].pct_change() * 100

ts_df.to_csv("bbm_asean_timeseries_estimasi.csv", index=False)
ts_df.to_excel("bbm_asean_timeseries_estimasi.xlsx", index=False)

print("\nData time series BBM berhasil dibuat")