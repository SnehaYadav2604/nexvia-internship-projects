from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = "/Users/snehayadav/nexvia-internship/DA-03"
RUN = f"cd {PROJECT} && {PROJECT}/venv/bin/python scripts/"

with DAG(
    dag_id="hourly_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"retries": 1},
    tags=["DA-03"],
) as dag:

    refresh = BashOperator(task_id="refresh_hourly_data",
                           bash_command=RUN + "simulate_hourly_feed.py")
    demand = BashOperator(task_id="detect_demand_anomalies",
                          bash_command=RUN + "detect_anomalies.py")
    supplier = BashOperator(task_id="detect_supplier_delays",
                            bash_command=RUN + "detect_supplier_delays.py")
    forecast = BashOperator(task_id="forecast_demand",
                            bash_command=RUN + "forecast_demand.py")
    alerts = BashOperator(task_id="send_alerts",
                          bash_command=RUN + "send_alerts.py")

    refresh >> [demand, supplier, forecast] >> alerts

    