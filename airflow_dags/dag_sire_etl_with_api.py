"""
DAG de SIRE que usa el API de ID estadístico
Procesa archivos CSV y usa el servicio FastAPI para generar IDs estadísticos
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import requests
import json
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
    'sire_etl_with_api',
    default_args=default_args,
    description='ETL de SIRE usando API de ID estadístico',
    schedule_interval=None,
    catchup=False,
    tags=['sire', 'etl', 'api', 'id-estadistico']
)

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn_string = "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw"
        engine = create_engine(conn_string)
        return engine
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def call_fastapi_service(endpoint, data):
    """
    Llama al servicio FastAPI para generar IDs estadísticos
    """
    try:
        # URL del servicio FastAPI
        fastapi_url = "http://sire-fastapi:5003"
        
        response = requests.post(
            f"{fastapi_url}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response: {result}")
            return result
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            raise Exception(f"API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error calling FastAPI: {e}")
        raise

def load_bdua_to_obt():
    """Carga datos BDUA a raw_obt_personas usando el API"""
    print("🔄 Cargando datos BDUA a OBT usando API...")
    
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
        
        # Procesar cada registro usando el API
        for index, row in df.iterrows():
            try:
                # Función para limpiar valores NaN
                def clean_value(value):
                    if pd.isna(value) or value == '' or value is None:
                        return ''
                    return str(value)
                
                # Preparar datos para el API
                persona_data = {
                    "tipo_documento": clean_value(row.get('tipo_identificacion', '')),
                    "numero_documento": clean_value(row.get('numero_identificacion', '')),
                    "primer_nombre": clean_value(row.get('primer_nombre', '')),
                    "segundo_nombre": clean_value(row.get('segundo_nombre', '')),
                    "primer_apellido": clean_value(row.get('primer_apellido', '')),
                    "segundo_apellido": clean_value(row.get('segundo_apellido', '')),
                    "fecha_nacimiento": clean_value(row.get('fecha_nacimiento', '')),
                    "sexo_an": clean_value(row.get('sexo', '')),
                    "codigo_municipio_nacimiento": clean_value(row.get('cod_municipio', '')),
                    "codigo_pais_nacimiento": "170"  # Colombia por defecto
                }
                
                # Llamar al API para generar ID estadístico
                api_response = call_fastapi_service("/generar-id-personas", persona_data)
                
                # Agregar el ID estadístico a los datos (siempre, ya sea nuevo o existente)
                persona_data["id_estadistico"] = api_response.get("id_estadistico", "")
                
                # Solo insertar si es una nueva persona
                if "Nueva persona registrada" in api_response.get("mensaje", ""):
                    # Insertar en raw_obt_personas
                    persona_df = pd.DataFrame([persona_data])
                    persona_df.to_sql('raw_obt_personas', engine, schema='sire_sta', if_exists='append', index=False)
                    print(f"✅ Nueva persona insertada: {persona_data['id_estadistico']}")
                else:
                    print(f"ℹ️ Persona ya existe: {api_response.get('id_estadistico', '')}")
                
                print(f"✅ Persona {index+1}/{len(df)} procesada: {api_response.get('id_estadistico', '')}")
                
            except Exception as e:
                print(f"❌ Error procesando persona {index+1}: {e}")
                continue
        
        print(f"✅ {len(df)} personas procesadas con API")
        return f"BDUA procesado con API: {len(df)} registros"
        
    except Exception as e:
        print(f"❌ Error cargando BDUA: {e}")
        raise

def load_rues_to_obt():
    """Carga datos RUES a raw_obt_empresas usando el API"""
    print("🔄 Cargando datos RUES a OBT usando API...")
    
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
        
        # Procesar cada registro usando el API
        for index, row in df.iterrows():
            try:
                # Función para limpiar valores NaN
                def clean_value(value):
                    if pd.isna(value) or value == '' or value is None:
                        return ''
                    return str(value)
                
                # Función para limpiar fechas
                def clean_date(value):
                    if pd.isna(value) or value == '' or value is None:
                        return None
                    # Si tiene formato datetime, extraer solo la fecha
                    if ' ' in str(value):
                        return str(value).split(' ')[0]
                    return str(value)
                
                # Determinar tipo de documento basado en el NIT
                nit_value = clean_value(row.get('nit', ''))
                if nit_value and len(nit_value) <= 10 and nit_value.isdigit():
                    # Si el NIT es numérico y corto, probablemente es CC
                    tipo_doc = "CC"
                else:
                    # Si es más largo o tiene caracteres especiales, es NIT
                    tipo_doc = "NIT"
                
                # Preparar datos para el API
                empresa_data = {
                    "razon_social": clean_value(row.get('razon_social', '')),
                    "tipo_documento": tipo_doc,
                    "numero_documento": nit_value,
                    "digito_verificacion": clean_value(row.get('digito_verificacion', '')),
                    "codigo_camara": clean_value(row.get('codigo_camara', '')),
                    "camara_comercio": clean_value(row.get('camara_comercio', '')),
                    "matricula": clean_value(row.get('matricula', '')),
                    "fecha_matricula": clean_date(row.get('fecha_matricula', '')),
                    "fecha_renovacion": clean_date(row.get('fecha_renovacion', '')),
                    "ultimo_ano_renovado": clean_value(row.get('ultimo_ano_renovado', '')),
                    "fecha_vigencia": clean_date(row.get('fecha_vigencia', '')),
                    "fecha_cancelacion": clean_date(row.get('fecha_cancelacion', '')),
                    "codigo_tipo_sociedad": clean_value(row.get('codigo_tipo_sociedad', '')),
                    "tipo_sociedad": clean_value(row.get('tipo_sociedad', '')),
                    "codigo_organizacion_juridica": clean_value(row.get('codigo_organizacion_juridica', '')),
                    "organizacion_juridica": clean_value(row.get('organizacion_juridica', '')),
                    "codigo_estado_matricula": clean_value(row.get('codigo_estado_matricula', '')),
                    "estado_matricula": clean_value(row.get('estado_matricula', '')),
                    "representante_legal": clean_value(row.get('representante_legal', '')),
                    "num_identificacion_representante_legal": clean_value(row.get('num_identificacion_representante_legal', '')),
                    "clase_identificacion_rl": clean_value(row.get('clase_identificacion_rl', '')),
                    "fecha_actualizacion": clean_date(row.get('fecha_actualizacion', ''))
                }
                
                # Llamar al API para generar ID estadístico
                api_response = call_fastapi_service("/generar-id-empresas", empresa_data)
                
                # Agregar el ID estadístico a los datos (siempre, ya sea nuevo o existente)
                empresa_data["id_estadistico"] = api_response.get("id_estadistico", "")
                
                # Solo insertar si es una nueva empresa
                if "Nueva empresa registrada" in api_response.get("mensaje", ""):
                    # Insertar en raw_obt_empresas
                    empresa_df = pd.DataFrame([empresa_data])
                    empresa_df.to_sql('raw_obt_empresas', engine, schema='sire_sta', if_exists='append', index=False)
                    print(f"✅ Nueva empresa insertada: {empresa_data['id_estadistico']}")
                else:
                    print(f"ℹ️ Empresa ya existe: {api_response.get('id_estadistico', '')}")
                
                print(f"✅ Empresa {index+1}/{len(df)} procesada: {api_response.get('id_estadistico', '')}")
                
            except Exception as e:
                print(f"❌ Error procesando empresa {index+1}: {e}")
                continue
        
        print(f"✅ {len(df)} empresas procesadas con API")
        return f"RUES procesado con API: {len(df)} registros"
        
    except Exception as e:
        print(f"❌ Error cargando RUES: {e}")
        raise

def verify_obt_data():
    """Verifica que los datos se hayan cargado correctamente en OBT"""
    print("🔍 Verificando datos cargados en OBT...")
    
    try:
        engine = get_db_connection()
        
        queries = {
            "raw_obt_personas": "SELECT COUNT(*) FROM sire_sta.raw_obt_personas;",
            "raw_obt_empresas": "SELECT COUNT(*) FROM sire_sta.raw_obt_empresas;"
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

load_bdua_obt = PythonOperator(
    task_id='load_bdua_to_obt',
    python_callable=load_bdua_to_obt,
    dag=dag
)

load_rues_obt = PythonOperator(
    task_id='load_rues_to_obt',
    python_callable=load_rues_to_obt,
    dag=dag
)

verify_obt = PythonOperator(
    task_id='verify_obt_data',
    python_callable=verify_obt_data,
    dag=dag
)

# Dependencias
check_files >> load_bdua_obt
check_files >> load_rues_obt
load_bdua_obt >> verify_obt
load_rues_obt >> verify_obt
