from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = "/Users/snehayadav/nexvia-internship/DA-04"
PY = "/Users/snehayadav/nexvia-internship/DA-03/venv/bin/python"
PSQL = "/Applications/Postgres.app/Contents/Versions/16/bin/psql"
RUN = f"cd {PROJECT} && "

with DAG(
    dag_id="monthly_board_pack",
    start_date=datetime(2026, 11, 1),
    schedule="@monthly",
    catchup=False,
    default_args={"retries": 1},
    tags=["DA-04"],
) as dag:
    generate = BashOperator(task_id="generate_ledger", bash_command=RUN + f"{PY} scripts/generate_ledger.py")
    load = BashOperator(task_id="load_ledger", bash_command=RUN + f"{PY} scripts/load_ledger.py")
    views = BashOperator(task_id="build_report_views", bash_command=RUN + f"{PSQL} finance_risk -f sql/reports.sql")
    score = BashOperator(task_id="credit_scorecard", bash_command=RUN + f"{PY} scripts/scorecard.py")
    pack = BashOperator(task_id="build_board_pack", bash_command=RUN + f"{PY} scripts/board_pack.py")
    notify = BashOperator(task_id="notify", bash_command=RUN + f"{PY} scripts/notify_board_pack.py")

    generate >> load >> views >> score >> pack >> notify

    