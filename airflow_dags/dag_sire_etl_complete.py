"""
DAG completo de SIRE para procesamiento ETL
Flujo completo: CSV → STA → OBT → DV (Hub/Sat/Link) con logs
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os
import hashlib
import requests
import uuid
from typing import Dict, Any

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
    'sire_etl_complete',
    default_args=default_args,
    description='ETL completo de SIRE - Flujo completo con logs',
    schedule_interval=None,
    catchup=False,
    tags=['sire', 'etl', 'complete', 'logs']
)

# Variables globales para el DAG
CURRENT_RUN_ID = str(uuid.uuid4())
FASTAPI_URL = "http://sire-fastapi:5003"

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn_string = "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw"
        engine = create_engine(conn_string)
        return engine
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def calculate_file_hash(file_path: str) -> str:
    """Calcula hash MD5 de un archivo"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def start_etl_log(job_name: str, description: str, file_name: str, file_hash: str) -> int:
    """Inicia log ETL y retorna el ID del log"""
    try:
        engine = get_db_connection()
        
        query = """
        INSERT INTO sire_dv.log_etl (
            job_uuid, start_time, estado, tabla_destino, 
            nombre_etl, descripcion_etl, nombre_archivo, hash_archivo
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id;
        """
        
        with engine.connect() as conn:
            result = conn.execute(query, (
                CURRENT_RUN_ID,
                datetime.now(),
                'RUNNING',
                'multiple',
                job_name,
                description,
                file_name,
                file_hash
            ))
            log_id = result.scalar()
            conn.commit()
            
        print(f"📝 Log ETL iniciado: ID {log_id}")
        return log_id
        
    except Exception as e:
        print(f"❌ Error iniciando log ETL: {e}")
        raise

def end_etl_log(log_id: int, estado: str, registros_cargados: int, mensaje_error: str = None):
    """Finaliza log ETL"""
    try:
        engine = get_db_connection()
        
        query = """
        UPDATE sire_dv.log_etl 
        SET end_time = %s, estado = %s, registros_cargados = %s, 
            mensaje_error = %s, tiempo_ejecucion_segundos = EXTRACT(EPOCH FROM (%s - start_time))
        WHERE id = %s;
        """
        
        with engine.connect() as conn:
            conn.execute(query, (
                datetime.now(),
                estado,
                registros_cargados,
                mensaje_error,
                datetime.now(),
                log_id
            ))
            conn.commit()
            
        print(f"📝 Log ETL finalizado: {estado} - {registros_cargados} registros")
        
    except Exception as e:
        print(f"❌ Error finalizando log ETL: {e}")
        raise

def call_fastapi_service(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Llama al servicio FastAPI para generar IDs estadísticos"""
    try:
        url = f"{FASTAPI_URL}{endpoint}"
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error llamando FastAPI {endpoint}: {e}")
        raise

def check_csv_files():
    """Verifica que los archivos CSV existan"""
    print("🔍 Verificando archivos CSV...")
    
    files_to_check = ["/data/bdua.csv", "/data/rues.csv"]
    results = {}
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_hash = calculate_file_hash(file_path)
            results[file_path] = {
                "exists": True,
                "size": file_size,
                "hash": file_hash
            }
            print(f"✅ {file_path}: {file_size} bytes, hash: {file_hash[:8]}...")
        else:
            results[file_path] = {"exists": False}
            print(f"❌ {file_path}: No encontrado")
    
    return results

def load_bdua_to_staging():
    """Carga datos BDUA a raw_bdua con logs"""
    print("🔄 Cargando datos BDUa a staging...")
    
    csv_path = "/data/bdua.csv"
    file_hash = calculate_file_hash(csv_path)
    log_id = start_etl_log("Carga BDUA", "Carga datos BDUA a raw_bdua", "bdua.csv", file_hash)
    
    try:
        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Archivo BDUA leído: {len(df)} registros")
        
        # Convertir nombres de columnas a minúsculas
        df.columns = df.columns.str.lower()
        
        # Agregar metadatos
        df['load_date'] = datetime.now()
        df['file_name'] = 'bdua.csv'
        df['persona_hash'] = df.apply(lambda x: hashlib.md5(
            f"{x.get('tipo_identificacion', '')}-{x.get('numero_identificacion', '')}".encode()
        ).hexdigest(), axis=1)
        
        # Conectar y cargar
        engine = get_db_connection()
        df.to_sql('raw_bdua', engine, schema='sire_sta', if_exists='append', index=False)
        
        end_etl_log(log_id, 'SUCCESS', len(df))
        print(f"✅ {len(df)} registros cargados a sire_sta.raw_bdua")
        return {"status": "success", "records": len(df), "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error cargando BDUA: {e}")
        raise

def load_rues_to_staging():
    """Carga datos RUES a raw_rues con logs"""
    print("🔄 Cargando datos RUES a staging...")
    
    csv_path = "/data/rues.csv"
    file_hash = calculate_file_hash(csv_path)
    log_id = start_etl_log("Carga RUES", "Carga datos RUES a raw_rues", "rues.csv", file_hash)
    
    try:
        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Archivo RUES leído: {len(df)} registros")
        
        # Convertir nombres de columnas a minúsculas
        df.columns = df.columns.str.lower()
        
        # Agregar metadatos
        df['load_date'] = datetime.now()
        df['md5_hash'] = df.apply(lambda x: hashlib.md5(
            f"{x.get('nit', '')}-{x.get('numero_identificacion', '')}-{x.get('matricula', '')}".encode()
        ).hexdigest(), axis=1)
        
        # Conectar y cargar
        engine = get_db_connection()
        df.to_sql('raw_rues', engine, schema='sire_sta', if_exists='append', index=False)
        
        end_etl_log(log_id, 'SUCCESS', len(df))
        print(f"✅ {len(df)} registros cargados a sire_sta.raw_rues")
        return {"status": "success", "records": len(df), "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error cargando RUES: {e}")
        raise

def generate_person_ids():
    """Genera IDs estadísticos para personas usando FastAPI"""
    print("🔄 Generando IDs estadísticos para personas...")
    
    log_id = start_etl_log("Generar IDs Personas", "Genera IDs estadísticos para personas", "bdua.csv", "")
    
    try:
        engine = get_db_connection()
        
        # Obtener personas únicas sin ID estadístico con todos los campos necesarios
        query = """
        SELECT DISTINCT 
            tipo_identificacion, numero_identificacion,
            primer_apellido, segundo_apellido, 
            primer_nombre, segundo_nombre,
            fecha_nacimiento, sexo, cod_municipio
        FROM sire_sta.raw_bdua 
        WHERE id_estadistico_persona IS NULL
        LIMIT 1000;
        """
        
        df = pd.read_sql(query, engine)
        print(f"📊 Procesando {len(df)} personas...")
        
        processed_count = 0
        for index, row in df.iterrows():
            try:
                # Preparar datos para FastAPI según el esquema PersonaRequest
                persona_data = {
                    "tipo_documento": str(row['tipo_identificacion']),
                    "numero_documento": str(row['numero_identificacion']),
                    "primer_nombre": str(row['primer_nombre']),
                    "segundo_nombre": str(row['segundo_nombre']),
                    "primer_apellido": str(row['primer_apellido']),
                    "segundo_apellido": str(row['segundo_apellido']),
                    "fecha_nacimiento": str(row['fecha_nacimiento']),
                    "sexo_an": str(row['sexo']),
                    "codigo_municipio_nacimiento": str(row['cod_municipio']),
                    "codigo_pais_nacimiento": "170",  # Colombia por defecto
                    "fecha_defuncion": None
                }
                
                # Llamar FastAPI
                api_response = call_fastapi_service("/generar-id-personas", persona_data)
                id_estadistico = api_response.get("id_estadistico", "")
                
                # Actualizar registro en raw_bdua
                update_query = """
                UPDATE sire_sta.raw_bdua 
                SET id_estadistico_persona = %s
                WHERE tipo_identificacion = %s AND numero_identificacion = %s
                AND id_estadistico_persona IS NULL;
                """
                
                with engine.connect() as conn:
                    conn.execute(update_query, (id_estadistico, row['tipo_identificacion'], row['numero_identificacion']))
                    conn.commit()
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"✅ Procesadas {processed_count} personas...")
                    
            except Exception as e:
                print(f"❌ Error procesando persona {index}: {e}")
                continue
        
        end_etl_log(log_id, 'SUCCESS', processed_count)
        print(f"✅ {processed_count} personas procesadas con IDs estadísticos")
        return {"status": "success", "records": processed_count, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error generando IDs de personas: {e}")
        raise

def generate_company_ids():
    """Genera IDs estadísticos para empresas usando FastAPI"""
    print("🔄 Generando IDs estadísticos para empresas...")
    
    log_id = start_etl_log("Generar IDs Empresas", "Genera IDs estadísticos para empresas", "rues.csv", "")
    
    try:
        engine = get_db_connection()
        
        # Obtener empresas únicas sin ID estadístico con todos los campos necesarios
        query = """
        SELECT DISTINCT 
            razon_social, nit, numero_identificacion, matricula,
            clase_identificacion, digito_verificacion, codigo_camara,
            camara_comercio, fecha_matricula, fecha_renovacion,
            ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion,
            codigo_tipo_sociedad, tipo_sociedad, codigo_organizacion_juridica,
            organizacion_juridica, codigo_estado_matricula, estado_matricula,
            representante_legal, num_identificacion_representante_legal,
            clase_identificacion_rl, fecha_actualizacion,
            primer_apellido, segundo_apellido, primer_nombre, segundo_nombre,
            fecha_nacimiento, sexo, cod_municipio
        FROM sire_sta.raw_rues 
        WHERE id_estadistico_empresa IS NULL
        LIMIT 1000;
        """
        
        df = pd.read_sql(query, engine)
        print(f"📊 Procesando {len(df)} empresas...")
        
        processed_count = 0
        for index, row in df.iterrows():
            try:
                tipo_documento = str(row['clase_identificacion']).upper()
                
                # Determinar qué endpoint usar según el tipo de documento
                if tipo_documento == "CC":
                    # Usar endpoint específico para empresas CC
                    endpoint = "/generar-id-empresas-cc"
                    empresa_data = {
                        # Datos de la empresa
                        "razon_social": str(row['razon_social']),
                        "tipo_documento": tipo_documento,
                        "numero_documento": str(row['numero_identificacion']),
                        "digito_verificacion": str(row['digito_verificacion']),
                        "codigo_camara": str(row['codigo_camara']),
                        "camara_comercio": str(row['camara_comercio']),
                        "matricula": str(row['matricula']),
                        "fecha_matricula": str(row['fecha_matricula']),
                        "fecha_renovacion": str(row['fecha_renovacion']),
                        "ultimo_ano_renovado": int(row['ultimo_ano_renovado']) if pd.notna(row['ultimo_ano_renovado']) else 0,
                        "fecha_vigencia": str(row['fecha_vigencia']),
                        "fecha_cancelacion": str(row['fecha_cancelacion']) if pd.notna(row['fecha_cancelacion']) else None,
                        "codigo_tipo_sociedad": str(row['codigo_tipo_sociedad']),
                        "tipo_sociedad": str(row['tipo_sociedad']),
                        "codigo_organizacion_juridica": str(row['codigo_organizacion_juridica']),
                        "organizacion_juridica": str(row['organizacion_juridica']),
                        "codigo_estado_matricula": str(row['codigo_estado_matricula']),
                        "estado_matricula": str(row['estado_matricula']),
                        "representante_legal": str(row['representante_legal']),
                        "num_identificacion_representante_legal": str(row['num_identificacion_representante_legal']),
                        "clase_identificacion_rl": str(row['clase_identificacion_rl']),
                        "fecha_actualizacion": str(row['fecha_actualizacion']) if pd.notna(row['fecha_actualizacion']) else None,
                        # Datos de la persona (para CC)
                        "primer_nombre": str(row['primer_nombre']),
                        "segundo_nombre": str(row['segundo_nombre']),
                        "primer_apellido": str(row['primer_apellido']),
                        "segundo_apellido": str(row['segundo_apellido']),
                        "fecha_nacimiento": str(row['fecha_nacimiento']),
                        "sexo_an": str(row['sexo']),
                        "codigo_municipio_nacimiento": str(row['cod_municipio']),
                        "codigo_pais_nacimiento": "170",  # Colombia por defecto
                        "fecha_defuncion": None
                    }
                else:
                    # Usar endpoint estándar para empresas
                    endpoint = "/generar-id-empresas"
                    empresa_data = {
                        "razon_social": str(row['razon_social']),
                        "tipo_documento": tipo_documento,
                        "numero_documento": str(row['numero_identificacion']),
                        "digito_verificacion": str(row['digito_verificacion']),
                        "codigo_camara": str(row['codigo_camara']),
                        "camara_comercio": str(row['camara_comercio']),
                        "matricula": str(row['matricula']),
                        "fecha_matricula": str(row['fecha_matricula']),
                        "fecha_renovacion": str(row['fecha_renovacion']),
                        "ultimo_ano_renovado": int(row['ultimo_ano_renovado']) if pd.notna(row['ultimo_ano_renovado']) else 0,
                        "fecha_vigencia": str(row['fecha_vigencia']),
                        "fecha_cancelacion": str(row['fecha_cancelacion']) if pd.notna(row['fecha_cancelacion']) else None,
                        "codigo_tipo_sociedad": str(row['codigo_tipo_sociedad']),
                        "tipo_sociedad": str(row['tipo_sociedad']),
                        "codigo_organizacion_juridica": str(row['codigo_organizacion_juridica']),
                        "organizacion_juridica": str(row['organizacion_juridica']),
                        "codigo_estado_matricula": str(row['codigo_estado_matricula']),
                        "estado_matricula": str(row['estado_matricula']),
                        "representante_legal": str(row['representante_legal']),
                        "num_identificacion_representante_legal": str(row['num_identificacion_representante_legal']),
                        "clase_identificacion_rl": str(row['clase_identificacion_rl']),
                        "fecha_actualizacion": str(row['fecha_actualizacion']) if pd.notna(row['fecha_actualizacion']) else None
                    }
                
                # Llamar FastAPI con el endpoint correcto
                api_response = call_fastapi_service(endpoint, empresa_data)
                id_estadistico = api_response.get("id_estadistico", "")
                
                # Actualizar registro en raw_rues
                update_query = """
                UPDATE sire_sta.raw_rues 
                SET id_estadistico_empresa = %s
                WHERE (nit = %s OR numero_identificacion = %s OR matricula = %s)
                AND id_estadistico_empresa IS NULL;
                """
                
                with engine.connect() as conn:
                    conn.execute(update_query, (
                        id_estadistico, 
                        row['nit'], 
                        row['numero_identificacion'], 
                        row['matricula']
                    ))
                    conn.commit()
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"✅ Procesadas {processed_count} empresas...")
                    
            except Exception as e:
                print(f"❌ Error procesando empresa {index}: {e}")
                continue
        
        end_etl_log(log_id, 'SUCCESS', processed_count)
        print(f"✅ {processed_count} empresas procesadas con IDs estadísticos")
        return {"status": "success", "records": processed_count, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error generando IDs de empresas: {e}")
        raise

def process_to_obt_personas():
    """Procesa personas a raw_obt_personas (con datos sensibles)"""
    print("🔄 Procesando personas a OBT...")
    
    log_id = start_etl_log("Carga OBT Personas", "Carga personas a raw_obt_personas", "bdua.csv", "")
    
    try:
        engine = get_db_connection()
        
        # Consulta para insertar en OBT personas
        query = """
        INSERT INTO sire_sta.raw_obt_personas (
            id_estadistico, tipo_documento, numero_documento,
            primer_nombre, segundo_nombre, primer_apellido, segundo_apellido,
            fecha_nacimiento, sexo_an, codigo_municipio_nacimiento,
            load_datetime, id_log_etl
        )
        SELECT DISTINCT
            id_estadistico_persona,
            tipo_identificacion,
            numero_identificacion,
            primer_nombre,
            segundo_nombre,
            primer_apellido,
            segundo_apellido,
            fecha_nacimiento,
            sexo,
            cod_municipio,
            CURRENT_TIMESTAMP,
            %s
        FROM sire_sta.raw_bdua
        WHERE id_estadistico_persona IS NOT NULL
        ON CONFLICT (id_estadistico, tipo_documento, numero_documento) DO NOTHING;
        """
        
        with engine.connect() as conn:
            result = conn.execute(query, (log_id,))
            conn.commit()
        
        # Contar registros insertados
        count_query = "SELECT COUNT(*) FROM sire_sta.raw_obt_personas;"
        with engine.connect() as conn:
            count_result = conn.execute(count_query)
            count = count_result.scalar()
        
        end_etl_log(log_id, 'SUCCESS', count)
        print(f"✅ {count} personas en raw_obt_personas")
        return {"status": "success", "records": count, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error procesando OBT personas: {e}")
        raise

def process_to_obt_empresas():
    """Procesa empresas a raw_obt_empresas (con datos sensibles)"""
    print("🔄 Procesando empresas a OBT...")
    
    log_id = start_etl_log("Carga OBT Empresas", "Carga empresas a raw_obt_empresas", "rues.csv", "")
    
    try:
        engine = get_db_connection()
        
        # Consulta para insertar en OBT empresas
        query = """
        INSERT INTO sire_sta.raw_obt_empresas (
            id_estadistico, razon_social, nit, digito_verificacion,
            codigo_camara, camara_comercio, matricula, fecha_matricula,
            fecha_renovacion, ultimo_ano_renovado, fecha_vigencia,
            fecha_cancelacion, codigo_tipo_sociedad, tipo_sociedad,
            codigo_organizacion_juridica, organizacion_juridica,
            codigo_estado_matricula, estado_matricula,
            representante_legal, num_identificacion_representante_legal,
            clase_identificacion_rl, fecha_actualizacion,
            load_datetime, id_log_etl
        )
        SELECT DISTINCT
            id_estadistico_empresa,
            razon_social,
            nit,
            digito_verificacion,
            codigo_camara,
            camara_comercio,
            matricula,
            fecha_matricula,
            fecha_renovacion,
            ultimo_ano_renovado,
            fecha_vigencia,
            fecha_cancelacion,
            codigo_tipo_sociedad,
            tipo_sociedad,
            codigo_organizacion_juridica,
            organizacion_juridica,
            codigo_estado_matricula,
            estado_matricula,
            representante_legal,
            num_identificacion_representante_legal,
            clase_identificacion_rl,
            fecha_actualizacion,
            CURRENT_TIMESTAMP,
            %s
        FROM sire_sta.raw_rues
        WHERE id_estadistico_empresa IS NOT NULL
        ON CONFLICT (id_estadistico, nit) DO NOTHING;
        """
        
        with engine.connect() as conn:
            result = conn.execute(query, (log_id,))
            conn.commit()
        
        # Contar registros insertados
        count_query = "SELECT COUNT(*) FROM sire_sta.raw_obt_empresas;"
        with engine.connect() as conn:
            count_result = conn.execute(count_query)
            count = count_result.scalar()
        
        end_etl_log(log_id, 'SUCCESS', count)
        print(f"✅ {count} empresas en raw_obt_empresas")
        return {"status": "success", "records": count, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error procesando OBT empresas: {e}")
        raise

def process_to_dv_hubs():
    """Procesa datos a hubs DV (sin datos sensibles)"""
    print("🔄 Procesando datos a hubs DV...")
    
    log_id = start_etl_log("Carga Hubs DV", "Carga datos a hubs DV", "multiple", "")
    
    try:
        engine = get_db_connection()
        
        # Hub Persona
        hub_persona_query = """
        INSERT INTO sire_dv.hub_persona (id_estadistico, load_datetime, md5_hash)
        SELECT DISTINCT 
            id_estadistico_persona,
            CURRENT_TIMESTAMP,
            MD5(id_estadistico_persona)
        FROM sire_sta.raw_bdua
        WHERE id_estadistico_persona IS NOT NULL
        ON CONFLICT (id_estadistico) DO NOTHING;
        """
        
        # Hub Empresa
        hub_empresa_query = """
        INSERT INTO sire_dv.hub_empresa (id_estadistico, load_datetime, md5_hash)
        SELECT DISTINCT 
            id_estadistico_empresa,
            CURRENT_TIMESTAMP,
            MD5(id_estadistico_empresa)
        FROM sire_sta.raw_rues
        WHERE id_estadistico_empresa IS NOT NULL
        ON CONFLICT (id_estadistico) DO NOTHING;
        """
        
        with engine.connect() as conn:
            conn.execute(hub_persona_query)
            conn.execute(hub_empresa_query)
            conn.commit()
        
        # Contar registros
        count_queries = {
            "hub_persona": "SELECT COUNT(*) FROM sire_dv.hub_persona;",
            "hub_empresa": "SELECT COUNT(*) FROM sire_dv.hub_empresa;"
        }
        
        total_records = 0
        with engine.connect() as conn:
            for table, query in count_queries.items():
                result = conn.execute(query)
                count = result.scalar()
                total_records += count
                print(f"📊 {table}: {count} registros")
        
        end_etl_log(log_id, 'SUCCESS', total_records)
        print(f"✅ {total_records} registros en hubs DV")
        return {"status": "success", "records": total_records, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error procesando hubs DV: {e}")
        raise

def process_to_dv_satellites():
    """Procesa datos a satélites DV (sin datos sensibles)"""
    print("🔄 Procesando datos a satélites DV...")
    
    log_id = start_etl_log("Carga Satélites DV", "Carga datos a satélites DV", "multiple", "")
    
    try:
        engine = get_db_connection()
        
        # Satélite Persona (SIN datos sensibles)
        sat_persona_query = """
        INSERT INTO sire_dv.sat_persona (
            id_estadistico, fecha_nacimiento, sexo, 
            codigo_municipio_nacimiento, etnia, discapacidad,
            tipo_poblacion_especial, nombre_resguardo,
            md5_hash, load_datetime
        )
        SELECT DISTINCT
            rb.id_estadistico_persona,
            rb.fecha_nacimiento,
            rb.sexo,
            rb.cod_municipio,
            rb.etnia,
            rb.discapacidad,
            rb.tipo_poblacion_especial,
            rb.nombre_resguardo,
            MD5(CONCAT(
                rb.id_estadistico_persona,
                rb.fecha_nacimiento,
                rb.sexo,
                rb.etnia
            )),
            CURRENT_TIMESTAMP
        FROM sire_sta.raw_bdua rb
        WHERE rb.id_estadistico_persona IS NOT NULL
        ON CONFLICT (md5_hash) DO NOTHING;
        """
        
        # Satélite Empresa (SIN datos sensibles)
        sat_empresa_query = """
        INSERT INTO sire_dv.sat_empresa (
            id_estadistico_empresa, codigo_camara, camara_comercio,
            matricula, inscripcion_proponente, sigla,
            fecha_matricula, fecha_renovacion, ultimo_anio_renovado,
            fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
            tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
            codigo_categoria_matricula, categoria_matricula,
            codigo_estado_matricula, estado_matricula,
            fecha_actualizacion, codigo_clase_identificacion,
            digito_verificacion, estatus,
            md5_hash, load_datetime
        )
        SELECT DISTINCT
            rr.id_estadistico_empresa,
            rr.codigo_camara,
            rr.camara_comercio,
            rr.matricula,
            rr.inscripcion_proponente,
            rr.sigla,
            rr.fecha_matricula,
            rr.fecha_renovacion,
            rr.ultimo_ano_renovado,
            rr.fecha_vigencia,
            rr.fecha_cancelacion,
            rr.codigo_tipo_sociedad,
            rr.tipo_sociedad,
            rr.codigo_organizacion_juridica,
            rr.organizacion_juridica,
            rr.codigo_categoria_matricula,
            rr.categoria_matricula,
            rr.codigo_estado_matricula,
            rr.estado_matricula,
            rr.fecha_actualizacion,
            rr.codigo_clase_identificacion,
            rr.digito_verificacion,
            rr.estado_matricula as estatus,
            MD5(CONCAT(
                rr.id_estadistico_empresa,
                rr.codigo_camara,
                rr.matricula,
                rr.fecha_matricula
            )),
            CURRENT_TIMESTAMP
        FROM sire_sta.raw_rues rr
        WHERE rr.id_estadistico_empresa IS NOT NULL
        ON CONFLICT (md5_hash) DO NOTHING;
        """
        
        with engine.connect() as conn:
            conn.execute(sat_persona_query)
            conn.execute(sat_empresa_query)
            conn.commit()
        
        # Contar registros
        count_queries = {
            "sat_persona": "SELECT COUNT(*) FROM sire_dv.sat_persona;",
            "sat_empresa": "SELECT COUNT(*) FROM sire_dv.sat_empresa;"
        }
        
        total_records = 0
        with engine.connect() as conn:
            for table, query in count_queries.items():
                result = conn.execute(query)
                count = result.scalar()
                total_records += count
                print(f"📊 {table}: {count} registros")
        
        end_etl_log(log_id, 'SUCCESS', total_records)
        print(f"✅ {total_records} registros en satélites DV")
        return {"status": "success", "records": total_records, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error procesando satélites DV: {e}")
        raise

def process_afiliacion_links():
    """Procesa links de afiliación entre personas y empresas"""
    print("🔄 Procesando links de afiliación...")
    
    log_id = start_etl_log("Carga Links Afiliación", "Carga links de afiliación", "bdua.csv", "")
    
    try:
        engine = get_db_connection()
        
        # Link de afiliación
        link_query = """
        INSERT INTO sire_dv.link_afiliacion (
            id_hub_persona_afiliada, id_hub_persona_cotizante,
            id_hub_aportante_emp, id_cod_departamento, id_cod_municipio,
            id_zona, tipo_cotizante, tipo_afiliado, parentesco,
            ips_primaria, fecha_afiliacion, regimen, estado_afiliacion,
            md5_hash, load_datetime
        )
        SELECT DISTINCT
            rb.id_estadistico_persona,
            rb.id_estadistico_persona, -- Asumiendo que es el mismo
            NULL, -- Se puede mapear después con empresas
            rb.cod_departamento,
            rb.cod_municipio,
            CASE WHEN rb.zona = 'Rural' THEN 2 ELSE 1 END,
            rb.tipo_cotizante,
            rb.tipo_afiliado,
            rb.parentesco,
            rb.ips_primaria,
            rb.fecha_afiliacion,
            rb.regimen,
            rb.estado_afiliacion,
            MD5(CONCAT(
                rb.id_estadistico_persona,
                rb.cod_departamento,
                rb.cod_municipio,
                rb.fecha_afiliacion
            )),
            CURRENT_TIMESTAMP
        FROM sire_sta.raw_bdua rb
        WHERE rb.id_estadistico_persona IS NOT NULL
        ON CONFLICT (md5_hash) DO NOTHING;
        """
        
        with engine.connect() as conn:
            result = conn.execute(link_query)
            conn.commit()
        
        # Contar registros
        count_query = "SELECT COUNT(*) FROM sire_dv.link_afiliacion;"
        with engine.connect() as conn:
            count_result = conn.execute(count_query)
            count = count_result.scalar()
        
        end_etl_log(log_id, 'SUCCESS', count)
        print(f"✅ {count} links de afiliación procesados")
        return {"status": "success", "records": count, "log_id": log_id}
        
    except Exception as e:
        end_etl_log(log_id, 'FAILURE', 0, str(e))
        print(f"❌ Error procesando links de afiliación: {e}")
        raise

def verify_complete_etl():
    """Verifica que todo el ETL se haya ejecutado correctamente"""
    print("🔍 Verificando ETL completo...")
    
    try:
        engine = get_db_connection()
        
        verification_queries = {
            "raw_bdua": "SELECT COUNT(*) FROM sire_sta.raw_bdua;",
            "raw_rues": "SELECT COUNT(*) FROM sire_sta.raw_rues;",
            "raw_obt_personas": "SELECT COUNT(*) FROM sire_sta.raw_obt_personas;",
            "raw_obt_empresas": "SELECT COUNT(*) FROM sire_sta.raw_obt_empresas;",
            "hub_persona": "SELECT COUNT(*) FROM sire_dv.hub_persona;",
            "hub_empresa": "SELECT COUNT(*) FROM sire_dv.hub_empresa;",
            "sat_persona": "SELECT COUNT(*) FROM sire_dv.sat_persona;",
            "sat_empresa": "SELECT COUNT(*) FROM sire_dv.sat_empresa;",
            "link_afiliacion": "SELECT COUNT(*) FROM sire_dv.link_afiliacion;",
            "log_etl": "SELECT COUNT(*) FROM sire_dv.log_etl WHERE job_uuid = %s;"
        }
        
        results = {}
        with engine.connect() as conn:
            for table, query in verification_queries.items():
                if table == "log_etl":
                    result = conn.execute(query, (CURRENT_RUN_ID,))
                else:
                    result = conn.execute(query)
                count = result.scalar()
                results[table] = count
                print(f"📊 {table}: {count} registros")
        
        # Verificar logs
        log_query = """
        SELECT nombre_etl, estado, registros_cargados, tiempo_ejecucion_segundos
        FROM sire_dv.log_etl 
        WHERE job_uuid = %s
        ORDER BY start_time;
        """
        
        with engine.connect() as conn:
            log_results = conn.execute(log_query, (CURRENT_RUN_ID,))
            print("\n📝 Logs ETL:")
            for log in log_results:
                print(f"  - {log[0]}: {log[1]} ({log[2]} registros, {log[3]:.2f}s)")
        
        return results
        
    except Exception as e:
        print(f"❌ Error verificando ETL: {e}")
        raise

# Tareas del DAG
check_files = PythonOperator(
    task_id='check_csv_files',
    python_callable=check_csv_files,
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

generate_person_ids = PythonOperator(
    task_id='generate_person_ids',
    python_callable=generate_person_ids,
    dag=dag
)

generate_company_ids = PythonOperator(
    task_id='generate_company_ids',
    python_callable=generate_company_ids,
    dag=dag
)

process_obt_personas = PythonOperator(
    task_id='process_to_obt_personas',
    python_callable=process_to_obt_personas,
    dag=dag
)

process_obt_empresas = PythonOperator(
    task_id='process_to_obt_empresas',
    python_callable=process_to_obt_empresas,
    dag=dag
)

process_dv_hubs = PythonOperator(
    task_id='process_to_dv_hubs',
    python_callable=process_to_dv_hubs,
    dag=dag
)

process_dv_satellites = PythonOperator(
    task_id='process_to_dv_satellites',
    python_callable=process_to_dv_satellites,
    dag=dag
)

process_afiliacion = PythonOperator(
    task_id='process_afiliacion_links',
    python_callable=process_afiliacion_links,
    dag=dag
)

verify_etl = PythonOperator(
    task_id='verify_complete_etl',
    python_callable=verify_complete_etl,
    dag=dag
)

# Dependencias del DAG
check_files >> [load_bdua, load_rues]
load_bdua >> generate_person_ids
load_rues >> generate_company_ids
[generate_person_ids, generate_company_ids] >> [process_obt_personas, process_obt_empresas]
[process_obt_personas, process_obt_empresas] >> process_dv_hubs
process_dv_hubs >> process_dv_satellites
process_dv_satellites >> process_afiliacion
process_afiliacion >> verify_etl
