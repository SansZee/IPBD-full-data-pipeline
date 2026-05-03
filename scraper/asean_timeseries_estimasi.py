import pandas as pd
import numpy as np

df = pd.read_csv("analisis_perubahan_asean.csv")

df["Start_Year"] = df["Data_availability"].str.split(" - ").str[0].astype(int)
df["End_Year"] = df["Data_availability"].str.split(" - ").str[1].astype(int)

all_rows = []

for _, row in df.iterrows():
    start = row["Start_Year"]
    end = row["End_Year"]
    
    years = list(range(start, end + 1))

    values = np.linspace(row["Min"], row["Max"], len(years))
    
    for y, v in zip(years, values):
        all_rows.append({
            "Country": row["Country"],
            "Indicator": row["Indicator"],
            "Year": y,
            "Value": round(v, 2)
        })

ts_df = pd.DataFrame(all_rows)

ts_df = ts_df.sort_values(by=["Country", "Indicator", "Year"])

print("\n=== DATA TIME SERIES (ESTIMASI) ===")
print(ts_df.head(20))

ts_df["Change"] = ts_df.groupby(
    ["Country", "Indicator"]
)["Value"].diff()

ts_df["Percent_Change"] = ts_df.groupby(
    ["Country", "Indicator"]
)["Value"].pct_change() * 100

ts_df.to_csv("asean_timeseries_estimasi.csv", index=False)
ts_df.to_excel("asean_timeseries_estimasi.xlsx", index=False)

print("\n Berhasil dibuat:")
print("- asean_timeseries_estimasi.csv")
print("- asean_timeseries_estimasi.xlsx")