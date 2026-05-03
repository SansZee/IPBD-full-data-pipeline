from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="etl_bbm_full_pipeline",
    default_args=default_args,
    description="Full ETL BBM pipeline",
    schedule="0 5 * * *",  # jam 5 pagi
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "bbm", "full"],
) as dag:

    # EXTRACT
    scrape_asean = BashOperator(
        task_id="scrape_asean",
        bash_command="python /opt/airflow/dags/scraper/cnbc_asean_bbm_scraper.py"
    )

    scrape_indonesia = BashOperator(
        task_id="scrape_indonesia",
        bash_command="python /opt/airflow/dags/scraper/indonesia_bbm_historical.py"
    )

    scrape_subsidy = BashOperator(
        task_id="scrape_subsidy",
        bash_command="python /opt/airflow/dags/scraper/indonesia_subsidy_scraper.py"
    )

    scrape_katadata = BashOperator(
        task_id="scrape_katadata",
        bash_command="python /opt/airflow/dags/scraper/katadata_bbm_scraper.py"
    )

    scrape_exchange = BashOperator(
        task_id="scrape_exchange",
        bash_command="python /opt/airflow/dags/scraper/exchange_rate_scraper.py"
    )

    scrape_oil = BashOperator(
        task_id="scrape_oil",
        bash_command="python /opt/airflow/dags/scraper/scraping_oil.py"
    )

    # TRANSFORM
    transform_data = BashOperator(
        task_id="transform_data",
        bash_command="python /opt/airflow/dags/scraper/transform_data.py"
    )

    # LOAD
    load_data = BashOperator(
        task_id="load_data",
        bash_command="python /opt/airflow/dags/scraper/load_data.py"
    )

    # FLOW
    [
        scrape_asean,
        scrape_indonesia,
        scrape_subsidy,
        scrape_katadata,
        scrape_exchange,
        scrape_oil
    ] >> transform_data >> load_data 