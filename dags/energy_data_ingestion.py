import os
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import json

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

CONN_ID = "postgres-metabase"

DATA_DIR = "/opt/airflow/data"

TABLES = {
    "dim_country": """
        CREATE TABLE IF NOT EXISTS dim_country (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            code VARCHAR(10) NOT NULL UNIQUE
        );
    """,
    "dim_commodity": """
        CREATE TABLE IF NOT EXISTS dim_commodity (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            unit VARCHAR(20) NOT NULL
        );
    """,
    "fact_coal_production": """
        CREATE TABLE IF NOT EXISTS fact_coal_production (
            id SERIAL PRIMARY KEY,
            country_id INT REFERENCES dim_country(id),
            series_id VARCHAR(50),
            year INT,
            value FLOAT,
            UNIQUE(country_id, series_id, year)
        );
    """,
    "fact_electricity_imports": """
        CREATE TABLE IF NOT EXISTS fact_electricity_imports (
            id SERIAL PRIMARY KEY,
            country_id INT REFERENCES dim_country(id),
            series_id VARCHAR(50),
            year INT,
            value FLOAT,
            UNIQUE(country_id, series_id, year)
        );
    """,
    "fact_asean_bbm_snapshot": """
        CREATE TABLE IF NOT EXISTS fact_asean_bbm_snapshot (
            id SERIAL PRIMARY KEY,
            country_id INT REFERENCES dim_country(id),
            snapshot_date DATE,
            gasoline_price_idr INT,
            diesel_price_idr INT,
            source VARCHAR(100),
            UNIQUE(country_id, snapshot_date, source)
        );
    """,
    "fact_global_oil_current": """
        CREATE TABLE IF NOT EXISTS fact_global_oil_current (
            id SERIAL PRIMARY KEY,
            commodity_id INT REFERENCES dim_commodity(id),
            price_usd FLOAT,
            updated_at TIMESTAMP WITH TIME ZONE,
            source VARCHAR(100),
            UNIQUE(commodity_id, source)
        );
    """,
    "fact_global_oil_historical": """
        CREATE TABLE IF NOT EXISTS fact_global_oil_historical (
            id SERIAL PRIMARY KEY,
            commodity_id INT REFERENCES dim_commodity(id),
            date DATE,
            price_usd FLOAT,
            source VARCHAR(100),
            UNIQUE(commodity_id, date, source)
        );
    """,
}

COUNTRIES_DATA = [
    ("Indonesia", "IDN"),
    ("Malaysia", "MYS"),
    ("Thailand", "THA"),
    ("Vietnam", "VNM"),
    ("Philippines", "PHL"),
    ("Singapore", "SGP"),
    ("Myanmar", "MMR"),
    ("Cambodia", "KHM"),
    ("Laos", "LAO"),
    ("Brunei", "BRN"),
    ("Filipina", "PH"),
]

COMMODITIES_DATA = [
    ("BZ=F", "Brent Crude", "barrel"),
    ("CL=F", "West Texas Intermediate", "barrel"),
    ("NG=F", "Natural Gas (Henry Hub)", "mmbtu"),
]


def create_tables():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        for table_name, sql in TABLES.items():
            print(f"Creating table: {table_name}")
            cur.execute(sql)
        conn.commit()
        print("All tables created successfully")
    finally:
        cur.close()
        conn.close()


def load_countries():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        for name, code in COUNTRIES_DATA:
            cur.execute(
                """
                INSERT INTO dim_country (name, code)
                VALUES (%s, %s) ON CONFLICT (name) DO NOTHING
                """,
                (name, code),
            )
        conn.commit()
        print(f"Loaded {len(COUNTRIES_DATA)} countries")
    finally:
        cur.close()
        conn.close()


def load_commodities():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        for code, name, unit in COMMODITIES_DATA:
            cur.execute(
                """
                INSERT INTO dim_commodity (code, name, unit)
                VALUES (%s, %s, %s) ON CONFLICT (code) DO NOTHING
                """,
                (code, name, unit),
            )
        conn.commit()
        print(f"Loaded {len(COMMODITIES_DATA)} commodities")
    finally:
        cur.close()
        conn.close()


def load_coal_production():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        filepath = os.path.join(DATA_DIR, "eia_coal_production.json")
        with open(filepath, "r") as f:
            data = json.load(f)

        cur.execute("SELECT id, name FROM dim_country")
        country_map = {name: pid for pid, name in cur.fetchall()}

        total = 0
        countries_data = data.get("data", {})
        for country_name, country_info in countries_data.items():
            if country_name not in country_map:
                print(f"  Skipping unknown country: {country_name}")
                continue
            country_id = country_map[country_name]
            series = country_info.get("series", {})
            for series_id, series_info in series.items():
                for record in series_info.get("values", []):
                    cur.execute(
                        """
                        INSERT INTO fact_coal_production (country_id, series_id, year, value)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (country_id, series_id, year) DO UPDATE SET value = EXCLUDED.value
                        """,
                        (country_id, series_id, record["year"], record["value"]),
                    )
                    total += 1

        conn.commit()
        print(f"Loaded {total} coal production records")
    finally:
        cur.close()
        conn.close()


def load_electricity_imports():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        filepath = os.path.join(DATA_DIR, "eia_electricity_imports.json")
        with open(filepath, "r") as f:
            data = json.load(f)

        cur.execute("SELECT id, name FROM dim_country")
        country_map = {name: pid for pid, name in cur.fetchall()}

        total = 0
        countries_data = data.get("data", {})
        for country_name, country_info in countries_data.items():
            if country_name not in country_map:
                print(f"  Skipping unknown country: {country_name}")
                continue
            country_id = country_map[country_name]
            series = country_info.get("series", {})
            for series_id, series_info in series.items():
                for record in series_info.get("values", []):
                    cur.execute(
                        """
                        INSERT INTO fact_electricity_imports (country_id, series_id, year, value)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (country_id, series_id, year) DO UPDATE SET value = EXCLUDED.value
                        """,
                        (country_id, series_id, record["year"], record["value"]),
                    )
                    total += 1

        conn.commit()
        print(f"Loaded {total} electricity import records")
    finally:
        cur.close()
        conn.close()


def load_asean_bbm():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        filepath = os.path.join(DATA_DIR, "cnbc_asean_bbm_prices.json")
        with open(filepath, "r") as f:
            data = json.load(f)

        cur.execute("SELECT id, name FROM dim_country")
        country_map = {name: pid for pid, name in cur.fetchall()}

        countries_list = data.get("data", {}).get("countries", [])
        snapshot_date = data.get("data", {}).get("date")
        source = data.get("data", {}).get("source", "cnbcindonesia.com")

        total = 0
        for country in countries_list:
            country_name = country.get("country")
            if country_name not in country_map:
                print(f"  Skipping unknown country: {country_name}")
                continue
            country_id = country_map[country_name]
            cur.execute(
                """
                INSERT INTO fact_asean_bbm_snapshot (country_id, snapshot_date, gasoline_price_idr, diesel_price_idr, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (country_id, snapshot_date, source)
                DO UPDATE SET gasoline_price_idr = EXCLUDED.gasoline_price_idr, diesel_price_idr = EXCLUDED.diesel_price_idr
                """,
                (country_id, snapshot_date, country["gasoline_price"], country["diesel_price"], source),
            )
            total += 1

        conn.commit()
        print(f"Loaded {total} ASEAN BBM snapshot records")
    finally:
        cur.close()
        conn.close()


def load_oil_current():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        filepath = os.path.join(DATA_DIR, "oil_prices.json")
        with open(filepath, "r") as f:
            data = json.load(f)

        cur.execute("SELECT id, code FROM dim_commodity")
        commodity_map = {code: pid for pid, code in cur.fetchall()}

        source = data.get("source", "yahoo.finance")
        total = 0
        for item in data.get("current_prices", []):
            code = item.get("code")
            if code not in commodity_map:
                print(f"  Skipping unknown commodity: {code}")
                continue
            commodity_id = commodity_map[code]
            updated_at = item.get("updated")
            cur.execute(
                """
                INSERT INTO fact_global_oil_current (commodity_id, price_usd, updated_at, source)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (commodity_id, source)
                DO UPDATE SET price_usd = EXCLUDED.price_usd, updated_at = EXCLUDED.updated_at
                """,
                (commodity_id, item["price"], updated_at, source),
            )
            total += 1

        conn.commit()
        print(f"Loaded {total} current oil price records")
    finally:
        cur.close()
        conn.close()


def load_oil_historical():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        filepath = os.path.join(DATA_DIR, "oil_prices.json")
        with open(filepath, "r") as f:
            data = json.load(f)

        cur.execute("SELECT id, code FROM dim_commodity")
        commodity_map = {code: pid for pid, code in cur.fetchall()}

        source = data.get("source", "yahoo.finance")
        total = 0
        historical = data.get("historical", {})
        for code, commodity_data in historical.items():
            if code not in commodity_map:
                print(f"  Skipping unknown commodity: {code}")
                continue
            commodity_id = commodity_map[code]
            for record in commodity_data.get("data", []):
                cur.execute(
                    """
                    INSERT INTO fact_global_oil_historical (commodity_id, date, price_usd, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (commodity_id, date, source)
                    DO UPDATE SET price_usd = EXCLUDED.price_usd
                    """,
                    (commodity_id, record["date"], record["price"], source),
                )
                total += 1

        conn.commit()
        print(f"Loaded {total} historical oil price records")
    finally:
        cur.close()
        conn.close()


def validate_summary():
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        tables = [
            "dim_country",
            "dim_commodity",
            "fact_coal_production",
            "fact_electricity_imports",
            "fact_asean_bbm_snapshot",
            "fact_global_oil_current",
            "fact_global_oil_historical",
        ]
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} records")
    finally:
        cur.close()
        conn.close()


with DAG(
    "energy_data_ingestion",
    default_args=DEFAULT_ARGS,
    description="Ingest ASEAN energy data into Postgres",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["energy", "asean", "etl"],
) as dag:

    t1 = PythonOperator(task_id="create_tables", python_callable=create_tables)
    t2 = PythonOperator(task_id="load_countries", python_callable=load_countries)
    t3 = PythonOperator(task_id="load_commodities", python_callable=load_commodities)
    t4 = PythonOperator(task_id="load_coal_production", python_callable=load_coal_production)
    t5 = PythonOperator(task_id="load_electricity_imports", python_callable=load_electricity_imports)
    t6 = PythonOperator(task_id="load_asean_bbm", python_callable=load_asean_bbm)
    t7 = PythonOperator(task_id="load_oil_current", python_callable=load_oil_current)
    t8 = PythonOperator(task_id="load_oil_historical", python_callable=load_oil_historical)
    t9 = PythonOperator(task_id="validate_summary", python_callable=validate_summary)

    t1 >> t2 >> t3
    t3 >> [t4, t5, t6]
    t6 >> [t7, t8]
    [t4, t5, t7, t8] >> t9
