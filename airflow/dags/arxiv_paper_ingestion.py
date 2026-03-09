from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator  # type: ignore
from airflow.operators.python import PythonOperator  # type: ignore
from arxiv_ingestion.fetching import fetch_daily_papers
from arxiv_ingestion.indexing import index_papers_to_opensearch
from arxiv_ingestion.reporting import generate_daily_report
from arxiv_ingestion.setup import setup_environment

from airflow import DAG

# Default arguments for the DAG
default_args = {
    "owner": "arxiv-curator",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 11),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    "arxiv_paper_ingestion",
    default_args=default_args,
    description="Daily arXiv CS.AI paper pipeline: fetch → store to MySQL",
    schedule="0 6 * * 1-5",  # Every weekday at 6:00 AM
    max_active_runs=3,
    catchup=True,
    tags=["arxiv", "ingestion", "papers"],
)

# Task definitions
setup_task = PythonOperator(
    task_id="setup_environment",
    python_callable=setup_environment,
    dag=dag,
)

# Fetch papers task
fetch_task = PythonOperator(
    task_id="fetch_daily_papers",
    python_callable=fetch_daily_papers,
    dag=dag,
)

# Generate report task
report_task = PythonOperator(
    task_id="generate_daily_report",
    python_callable=generate_daily_report,
    dag=dag,
)

# Index papers task
indexing_task = PythonOperator(
    task_id="index_papers_to_opensearch",
    python_callable=index_papers_to_opensearch,
    dag=dag,
)

cleanup_task = BashOperator(
    task_id="cleanup_temp_files",
    bash_command="""
    echo "Cleaning up temporary files..."
    # Remove PDFs older than 30 days to manage disk space
    find /tmp -name "*.pdf" -type f -mtime +30 -delete 2>/dev/null || true
    echo "Cleanup completed"
    """,
    dag=dag,
)

# Task dependencies
# Simplified pipeline: setup -> fetch -> indexing -> report -> cleanup
setup_task >> fetch_task >> indexing_task >> report_task >> cleanup_task
