"""
Hello World DAG for Airflow
"""

from datetime import datetime, timedelta

import pymysql
import requests
from airflow.operators.python import PythonOperator # type: ignore

from airflow import DAG

def hello_world():
    print("Hello from Airflow DAG!")
    return "success"

def check_service_health():
    try:
        response = requests.get("http://rag-api:8000/api/v1/health")
        print(f"RAG API Health Check Status Code: {response.status_code}")

        # Check connection to MySQL
        try:
            connection = pymysql.connect(
                host="mysql",
                user="rag_user",
                password="rag_password",
                database="rag_db",
            )
            print("Successfully connected to MySQL database.")
        except Exception as e:
            print(f"Error connecting to MySQL database: {e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()
                print("MySQL connection closed.")
        return "Service are accessible"
    except Exception as e:
        print(f"Services check failed: {e}")
        raise

# DAG configuration
default_args = {
    'owner': 'rag',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    "hello_world_dag",
    default_args=default_args,
    description="A simple Hello World DAG to test Airflow setup",
    schedule=None,
    catchup=False,
    tags=["testing"],
)

# Define tasks
hello_task = PythonOperator(
    task_id="hello_world_task",
    python_callable=hello_world,
    dag=dag,
)

service_check_task = PythonOperator(
    task_id="check_service",
    python_callable=check_service_health,
    dag=dag,
)

# Set task dependencies
hello_task >> service_check_task