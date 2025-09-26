"""
DAG funcional de SIRE para procesamiento ETL real
Procesa archivos CSV y los carga a las tablas DV y STA
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os

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
    'sire_etl_real',
    default_args=default_args,
    description='ETL real de SIRE - Procesa CSV y carga a DV/STA',
    schedule_interval=None,
    catchup=False,
    tags=['sire', 'etl', 'real']
)

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        # Configuración de conexión
        conn_string = "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw"
        engine = create_engine(conn_string)
        return engine
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def load_bdua_to_staging():
    """Carga datos BDUA a la tabla de staging"""
    print("🔄 Cargando datos BDUA a staging...")
    
    try:
        # Leer archivo CSV
        csv_path = "/data/bdua.csv"
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Archivo no encontrado: {csv_path}")
        
        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Archivo BDUA leído: {len(df)} registros")
        
        # Convertir nombres de columnas a minúsculas
        df.columns = df.columns.str.lower()
        print(f"📋 Columnas: {list(df.columns)}")
        
        # Conectar a la base de datos
        engine = get_db_connection()
        
        # Cargar a la tabla de staging
        df.to_sql('raw_bdua', engine, schema='sire_sta', if_exists='append', index=False)
        
        print(f"✅ {len(df)} registros cargados a sire_sta.raw_bdua")
        return f"BDUA cargado: {len(df)} registros"
        
    except Exception as e:
        print(f"❌ Error cargando BDUA: {e}")
        raise

def load_rues_to_staging():
    """Carga datos RUES a la tabla de staging"""
    print("🔄 Cargando datos RUES a staging...")
    
    try:
        # Leer archivo CSV
        csv_path = "/data/rues.csv"
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Archivo no encontrado: {csv_path}")
        
        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Archivo RUES leído: {len(df)} registros")
        
        # Conectar a la base de datos
        engine = get_db_connection()
        
        # Cargar a la tabla de staging
        df.to_sql('raw_rues', engine, schema='sire_sta', if_exists='append', index=False)
        
        print(f"✅ {len(df)} registros cargados a sire_sta.raw_rues")
        return f"RUES cargado: {len(df)} registros"
        
    except Exception as e:
        print(f"❌ Error cargando RUES: {e}")
        raise

def process_persons_to_hub():
    """Procesa personas desde staging a hub_persona"""
    print("🔄 Procesando personas a hub_persona...")
    
    try:
        engine = get_db_connection()
        
        # Consulta para obtener personas únicas desde raw_bdua
        query = """
        INSERT INTO sire_dv.hub_persona (id_estadistico, load_datetime, md5_hash)
        SELECT DISTINCT 
            CONCAT(tipo_identificacion, '-', numero_identificacion) as id_estadistico,
            CURRENT_TIMESTAMP as load_datetime,
            MD5(CONCAT(tipo_identificacion, '-', numero_identificacion)) as md5_hash
        FROM sire_sta.raw_bdua
        WHERE tipo_identificacion IS NOT NULL 
        AND numero_identificacion IS NOT NULL
        ON CONFLICT (id_estadistico) DO NOTHING;
        """
        
        with engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
        
        # Contar registros insertados
        count_query = "SELECT COUNT(*) FROM sire_dv.hub_persona;"
        with engine.connect() as conn:
            count_result = conn.execute(count_query)
            count = count_result.scalar()
        
        print(f"✅ {count} personas en hub_persona")
        return f"Personas procesadas: {count}"
        
    except Exception as e:
        print(f"❌ Error procesando personas: {e}")
        raise

def process_companies_to_hub():
    """Procesa empresas desde staging a hub_empresa"""
    print("🔄 Procesando empresas a hub_empresa...")
    
    try:
        engine = get_db_connection()
        
        # Consulta para obtener empresas únicas desde raw_rues
        query = """
        INSERT INTO sire_dv.hub_empresa (id_estadistico, load_datetime, md5_hash)
        SELECT DISTINCT 
            COALESCE(nit, numero_identificacion, 'EMP-' || matricula) as id_estadistico,
            CURRENT_TIMESTAMP as load_datetime,
            MD5(COALESCE(nit, numero_identificacion, 'EMP-' || matricula)) as md5_hash
        FROM sire_sta.raw_rues
        WHERE (nit IS NOT NULL OR numero_identificacion IS NOT NULL OR matricula IS NOT NULL)
        ON CONFLICT (id_estadistico) DO NOTHING;
        """
        
        with engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
        
        # Contar registros insertados
        count_query = "SELECT COUNT(*) FROM sire_dv.hub_empresa;"
        with engine.connect() as conn:
            count_result = conn.execute(count_query)
            count = count_result.scalar()
        
        print(f"✅ {count} empresas en hub_empresa")
        return f"Empresas procesadas: {count}"
        
    except Exception as e:
        print(f"❌ Error procesando empresas: {e}")
        raise

def verify_data_loaded():
    """Verifica que los datos se hayan cargado correctamente"""
    print("🔍 Verificando datos cargados...")
    
    try:
        engine = get_db_connection()
        
        queries = {
            "raw_bdua": "SELECT COUNT(*) FROM sire_sta.raw_bdua;",
            "raw_rues": "SELECT COUNT(*) FROM sire_sta.raw_rues;",
            "hub_persona": "SELECT COUNT(*) FROM sire_dv.hub_persona;",
            "hub_empresa": "SELECT COUNT(*) FROM sire_dv.hub_empresa;"
        }
        
        results = {}
        with engine.connect() as conn:
            for table, query in queries.items():
                result = conn.execute(query)
                count = result.scalar()
                results[table] = count
                print(f"📊 {table}: {count} registros")
        
        return results
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        raise

# Tareas
check_files = BashOperator(
    task_id='check_csv_files',
    bash_command='ls -la /data/ && echo "Archivos CSV verificados"',
    dag=dag
)

load_bdua = PythonOperator(
    task_id='load_bdua_to_staging',
    python_callable=load_bdua_to_staging,
    dag=dag
)

load_rues = PythonOperator(
    task_id='load_rues_to_staging',
    python_callable=load_rues_to_staging,
    dag=dag
)

process_persons = PythonOperator(
    task_id='process_persons_to_hub',
    python_callable=process_persons_to_hub,
    dag=dag
)

process_companies = PythonOperator(
    task_id='process_companies_to_hub',
    python_callable=process_companies_to_hub,
    dag=dag
)

verify_data = PythonOperator(
    task_id='verify_data_loaded',
    python_callable=verify_data_loaded,
    dag=dag
)

# Dependencias
check_files >> load_bdua
check_files >> load_rues
load_bdua >> process_persons
load_rues >> process_companies
process_persons >> verify_data
process_companies >> verify_data
