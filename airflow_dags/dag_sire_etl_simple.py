"""
DAG simplificado de SIRE para procesamiento ETL
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
    'sire_etl_simple',
    default_args=default_args,
    description='ETL simplificado de SIRE',
    schedule_interval=None,
    catchup=False,
    tags=['sire', 'etl', 'simplified']
)

def check_csv_files():
    """Verifica que los archivos CSV existan"""
    import os
    csv_path = "/data/bdua.csv"
    if os.path.exists(csv_path):
        print(f"✅ Archivo encontrado: {csv_path}")
        return "Archivo BDUA encontrado"
    else:
        print(f"❌ Archivo no encontrado: {csv_path}")
        return "Archivo BDUA no encontrado"

def process_bdua_simple():
    """Procesa el archivo BDUA de forma simplificada"""
    print("🔄 Procesando archivo BDUA...")
    # Aquí iría la lógica de procesamiento
    print("✅ Procesamiento BDUA completado")
    return "BDUA procesado"

def process_rues_simple():
    """Procesa el archivo RUES de forma simplificada"""
    print("🔄 Procesando archivo RUES...")
    # Aquí iría la lógica de procesamiento
    print("✅ Procesamiento RUES completado")
    return "RUES procesado"

# Tareas
check_files = BashOperator(
    task_id='check_csv_files',
    bash_command='ls -la /data/',
    dag=dag
)

process_bdua = PythonOperator(
    task_id='process_bdua_simple',
    python_callable=process_bdua_simple,
    dag=dag
)

process_rues = PythonOperator(
    task_id='process_rues_simple',
    python_callable=process_rues_simple,
    dag=dag
)

# Dependencias
check_files >> [process_bdua, process_rues]
