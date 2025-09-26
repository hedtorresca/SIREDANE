from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import requests
import os
from sqlalchemy import create_engine, text

# Configuración del DAG
default_args = {
    'owner': 'sire_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sire_etl_oracle',
    default_args=default_args,
    description='ETL SIRE con Oracle como destino',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['sire', 'etl', 'oracle']
)

# Configuración de conexión Oracle
def get_oracle_connection():
    """Obtiene conexión a Oracle"""
    conn_string = os.getenv("ORACLE_CONNECTION_STRING", 
                           "oracle://SIRE_STG:sire_password@oracle-db:1521/XEPDB1")
    return create_engine(conn_string)

def call_fastapi_service(endpoint: str, data: dict) -> dict:
    """Llama al servicio FastAPI para generar IDs estadísticos"""
    try:
        api_url = os.getenv("FASTAPI_URL", "http://sire-fastapi:5003")
        response = requests.post(f"{api_url}{endpoint}", json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error llamando API: {e}")
        raise

def clean_value(value):
    """Limpia valores nulos y espacios"""
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()

def clean_date(value):
    """Limpia fechas"""
    if pd.isna(value) or value is None or value == "":
        return None
    try:
        return pd.to_datetime(value).strftime('%Y-%m-%d')
    except:
        return None

def load_bdua_to_obt():
    """Carga datos BDUA a raw_obt_personas usando el API"""
    try:
        # Leer archivo CSV
        csv_path = "/app/src/data/bdua.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Archivo no encontrado: {csv_path}")
            return "Archivo BDUA no encontrado"
        
        df = pd.read_csv(csv_path)
        print(f"📊 Procesando {len(df)} registros de BDUA")
        
        engine = get_oracle_connection()
        
        for index, row in df.iterrows():
            try:
                # Preparar datos para la API
                persona_data = {
                    "tipo_documento": clean_value(row.get('tipo_identificacion', '')),
                    "numero_documento": clean_value(row.get('numero_identificacion', '')),
                    "primer_nombre": clean_value(row.get('primer_nombre', '')),
                    "segundo_nombre": clean_value(row.get('segundo_nombre', '')),
                    "primer_apellido": clean_value(row.get('primer_apellido', '')),
                    "segundo_apellido": clean_value(row.get('segundo_apellido', '')),
                    "fecha_nacimiento": clean_date(row.get('fecha_nacimiento', '')),
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
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO raw_obt_personas (
                                id_estadistico, tipo_documento, numero_documento, primer_nombre, segundo_nombre,
                                primer_apellido, segundo_apellido, fecha_nacimiento, sexo_an,
                                codigo_municipio_nacimiento, codigo_pais_nacimiento
                            ) VALUES (
                                :id_est, :tipo_doc, :num_doc, :primer_nom, :segundo_nom,
                                :primer_ape, :segundo_ape, :fecha_nac, :sexo,
                                :cod_mun, :cod_pais
                            )
                        """), {
                            "id_est": persona_data["id_estadistico"],
                            "tipo_doc": persona_data["tipo_documento"],
                            "num_doc": persona_data["numero_documento"],
                            "primer_nom": persona_data["primer_nombre"],
                            "segundo_nom": persona_data["segundo_nombre"],
                            "primer_ape": persona_data["primer_apellido"],
                            "segundo_ape": persona_data["segundo_apellido"],
                            "fecha_nac": persona_data["fecha_nacimiento"],
                            "sexo": persona_data["sexo_an"],
                            "cod_mun": persona_data["codigo_municipio_nacimiento"],
                            "cod_pais": persona_data["codigo_pais_nacimiento"]
                        })
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
    try:
        # Leer archivo CSV
        csv_path = "/app/src/data/rues.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Archivo no encontrado: {csv_path}")
            return "Archivo RUES no encontrado"
        
        df = pd.read_csv(csv_path)
        print(f"📊 Procesando {len(df)} registros de RUES")
        
        engine = get_oracle_connection()
        
        for index, row in df.iterrows():
            try:
                # Preparar datos para la API
                empresa_data = {
                    "razon_social": clean_value(row.get('razon_social', '')),
                    "tipo_documento": clean_value(row.get('clase_identificacion', '')),
                    "numero_documento": clean_value(row.get('numero_identificacion', '')),
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
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO raw_obt_empresas (
                                id_estadistico, razon_social, tipo_documento, numero_documento, digito_verificacion,
                                codigo_camara, camara_comercio, matricula, fecha_matricula, fecha_renovacion,
                                ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
                                tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
                                codigo_estado_matricula, estado_matricula, representante_legal,
                                num_identificacion_representante_legal, clase_identificacion_rl, fecha_actualizacion
                            ) VALUES (
                                :id_est, :razon_soc, :tipo_doc, :num_doc, :dig_ver,
                                :cod_cam, :cam_com, :mat, :fecha_mat, :fecha_ren,
                                :ult_ano, :fecha_vig, :fecha_can, :cod_tipo_soc,
                                :tipo_soc, :cod_org_jur, :org_jur,
                                :cod_est_mat, :est_mat, :rep_leg,
                                :num_id_rep, :clase_id_rl, :fecha_act
                            )
                        """), {
                            "id_est": empresa_data["id_estadistico"],
                            "razon_soc": empresa_data["razon_social"],
                            "tipo_doc": empresa_data["tipo_documento"],
                            "num_doc": empresa_data["numero_documento"],
                            "dig_ver": empresa_data["digito_verificacion"],
                            "cod_cam": empresa_data["codigo_camara"],
                            "cam_com": empresa_data["camara_comercio"],
                            "mat": empresa_data["matricula"],
                            "fecha_mat": empresa_data["fecha_matricula"],
                            "fecha_ren": empresa_data["fecha_renovacion"],
                            "ult_ano": empresa_data["ultimo_ano_renovado"],
                            "fecha_vig": empresa_data["fecha_vigencia"],
                            "fecha_can": empresa_data["fecha_cancelacion"],
                            "cod_tipo_soc": empresa_data["codigo_tipo_sociedad"],
                            "tipo_soc": empresa_data["tipo_sociedad"],
                            "cod_org_jur": empresa_data["codigo_organizacion_juridica"],
                            "org_jur": empresa_data["organizacion_juridica"],
                            "cod_est_mat": empresa_data["codigo_estado_matricula"],
                            "est_mat": empresa_data["estado_matricula"],
                            "rep_leg": empresa_data["representante_legal"],
                            "num_id_rep": empresa_data["num_identificacion_representante_legal"],
                            "clase_id_rl": empresa_data["clase_identificacion_rl"],
                            "fecha_act": empresa_data["fecha_actualizacion"]
                        })
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
    try:
        engine = get_oracle_connection()
        
        with engine.connect() as conn:
            # Verificar personas
            result_personas = conn.execute(text("SELECT COUNT(*) FROM raw_obt_personas"))
            count_personas = result_personas.scalar()
            
            # Verificar empresas
            result_empresas = conn.execute(text("SELECT COUNT(*) FROM raw_obt_empresas"))
            count_empresas = result_empresas.scalar()
            
            # Verificar tabla de control
            result_control = conn.execute(text("SELECT COUNT(*) FROM control_ids_generados"))
            count_control = result_control.scalar()
            
            print(f"📊 Verificación de datos:")
            print(f"   - Personas en OBT: {count_personas}")
            print(f"   - Empresas en OBT: {count_empresas}")
            print(f"   - IDs en control: {count_control}")
            
            return f"Verificación completada: {count_personas} personas, {count_empresas} empresas, {count_control} IDs control"
            
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        raise

# Definir tareas
task_verify_files = BashOperator(
    task_id='verify_files',
    bash_command='ls -la /app/src/data/',
    dag=dag
)

task_load_bdua = PythonOperator(
    task_id='load_bdua_to_obt',
    python_callable=load_bdua_to_obt,
    dag=dag
)

task_load_rues = PythonOperator(
    task_id='load_rues_to_obt',
    python_callable=load_rues_to_obt,
    dag=dag
)

task_verify_data = PythonOperator(
    task_id='verify_obt_data',
    python_callable=verify_obt_data,
    dag=dag
)

# Definir dependencias
task_verify_files >> [task_load_bdua, task_load_rues] >> task_verify_data
