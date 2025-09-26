"""
DAG de prueba simple
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Configuración del DAG
default_args = {
    'owner': 'sire-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'test_simple',
    default_args=default_args,
    description='DAG de prueba simple',
    schedule_interval=None,
    catchup=False,
    tags=['test']
)

def test_function():
    """Función de prueba"""
    print("¡DAG de prueba funcionando!")
    return "Éxito"

# Tarea de prueba
test_task = PythonOperator(
    task_id='test_task',
    python_callable=test_function,
    dag=dag
)

# Tarea bash de prueba
bash_task = BashOperator(
    task_id='bash_test',
    bash_command='echo "Bash task funcionando"',
    dag=dag
)

# Dependencias
test_task >> bash_task
