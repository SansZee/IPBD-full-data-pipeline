import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def main():
    print("=== LOAD DATA START ===")

    input_file = os.path.join(DATA_DIR, "transformed_data.json")

    print(f"Reading file: {input_file}")

    if not os.path.exists(input_file):
        raise Exception("File transform tidak ditemukan!")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Transform data loaded")

    df = pd.DataFrame(data["data"])

    print("DataFrame dibuat")

    output_file = os.path.join(DATA_DIR, "final_dataset.csv")

    df.to_csv(output_file, index=False)

    print(f"File berhasil disimpan di: {output_file}")
    print("=== LOAD DATA DONE ===")

if __name__ == "__main__":
    main()