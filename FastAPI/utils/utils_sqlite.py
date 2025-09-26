import sqlite3
import os
from typing import Optional
from datetime import datetime

def get_sqlite_connection():
    """Establece conexión con SQLite"""
    db_path = "/app/data/sire_test.db"  # Ruta dentro del contenedor en la carpeta data
    return sqlite3.connect(db_path)

def init_sqlite_database():
    """Inicializa la base de datos SQLite con las tablas necesarias"""
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        
        # Crear tabla raw_obt_personas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_obt_personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_estadistico TEXT,
                tipo_documento TEXT,
                numero_documento TEXT,
                primer_nombre TEXT,
                segundo_nombre TEXT,
                primer_apellido TEXT,
                segundo_apellido TEXT,
                fecha_nacimiento DATE,
                sexo_an TEXT,
                codigo_municipio_nacimiento TEXT,
                codigo_pais_nacimiento TEXT,
                fecha_defuncion DATE,
                load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla raw_obt_empresas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_obt_empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_estadistico TEXT,
                razon_social TEXT,
                tipo_documento TEXT,
                numero_documento TEXT,
                digito_verificacion TEXT,
                codigo_camara TEXT,
                camara_comercio TEXT,
                matricula TEXT,
                fecha_matricula DATE,
                fecha_renovacion DATE,
                ultimo_ano_renovado INTEGER,
                fecha_vigencia DATE,
                fecha_cancelacion DATE,
                codigo_tipo_sociedad TEXT,
                tipo_sociedad TEXT,
                codigo_organizacion_juridica TEXT,
                organizacion_juridica TEXT,
                codigo_estado_matricula TEXT,
                estado_matricula TEXT,
                representante_legal TEXT,
                num_identificacion_representante_legal TEXT,
                clase_identificacion_rl TEXT,
                fecha_actualizacion DATE,
                load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Base de datos SQLite inicializada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        raise

def generar_id_estadistico(tipo_entidad: str, consecutivo_hex: str) -> str:
    """Genera un ID estadístico con el formato: tipo_entidad + consecutivo_hex"""
    return f"{tipo_entidad}{consecutivo_hex}"

def obtener_siguiente_consecutivo_personas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para personas"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    # Buscar el máximo ID estadístico de personas (que empieza con '01')
    cur.execute("""
        SELECT MAX(CAST(SUBSTR(id_estadistico, 3) AS INTEGER))
        FROM raw_obt_personas 
        WHERE id_estadistico LIKE '01%'
    """)
    
    max_consecutivo = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    if max_consecutivo is None:
        return "00000001"
    
    # Incrementar y convertir a hexadecimal de 8 dígitos
    siguiente = max_consecutivo + 1
    return f"{siguiente:08X}"

def obtener_siguiente_consecutivo_empresas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para empresas"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    # Buscar el máximo ID estadístico de empresas (que empieza con '02')
    cur.execute("""
        SELECT MAX(CAST(SUBSTR(id_estadistico, 3) AS INTEGER))
        FROM raw_obt_empresas 
        WHERE id_estadistico LIKE '02%'
    """)
    
    max_consecutivo = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    if max_consecutivo is None:
        return "00000001"
    
    # Incrementar y convertir a hexadecimal de 8 dígitos
    siguiente = max_consecutivo + 1
    return f"{siguiente:08X}"

def buscar_persona_existente(tipo_documento: str, numero_documento: str) -> Optional[str]:
    """Busca si una persona ya existe en la base de datos"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id_estadistico 
        FROM raw_obt_personas 
        WHERE tipo_documento = ? AND numero_documento = ?
    """, [tipo_documento, numero_documento])
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return result[0] if result else None

def buscar_empresa_existente(tipo_documento: str, numero_documento: str) -> Optional[str]:
    """Busca si una empresa ya existe en la base de datos"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id_estadistico 
        FROM raw_obt_empresas 
        WHERE tipo_documento = ? AND numero_documento = ?
    """, [tipo_documento, numero_documento])
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return result[0] if result else None

def guardar_nueva_persona(data: dict) -> str:
    """Guarda una nueva persona en la base de datos y retorna el ID generado"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    consecutivo = obtener_siguiente_consecutivo_personas()
    id_estadistico = generar_id_estadistico("01", consecutivo)
    
    cur.execute("""
        INSERT INTO raw_obt_personas (
            id_estadistico, tipo_documento, numero_documento, primer_nombre, segundo_nombre,
            primer_apellido, segundo_apellido, fecha_nacimiento, sexo_an,
            codigo_municipio_nacimiento, codigo_pais_nacimiento, fecha_defuncion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_estadistico, data["tipo_documento"], data["numero_documento"],
        data["primer_nombre"], data["segundo_nombre"], data["primer_apellido"],
        data["segundo_apellido"], data["fecha_nacimiento"], data["sexo_an"],
        data["codigo_municipio_nacimiento"], data["codigo_pais_nacimiento"],
        data.get("fecha_defuncion")
    ])
    
    conn.commit()
    cur.close()
    conn.close()
    
    return id_estadistico

def guardar_nueva_empresa(data: dict) -> str:
    """Guarda una nueva empresa en la base de datos y retorna el ID generado"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    consecutivo = obtener_siguiente_consecutivo_empresas()
    id_estadistico = generar_id_estadistico("02", consecutivo)
    
    cur.execute("""
        INSERT INTO raw_obt_empresas (
            id_estadistico, razon_social, tipo_documento, numero_documento, digito_verificacion,
            codigo_camara, camara_comercio, matricula, fecha_matricula, fecha_renovacion,
            ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
            tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
            codigo_estado_matricula, estado_matricula, representante_legal,
            num_identificacion_representante_legal, clase_identificacion_rl, fecha_actualizacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_estadistico, data["razon_social"], data["tipo_documento"], data["numero_documento"],
        data.get("digito_verificacion"), data["codigo_camara"], data["camara_comercio"],
        data["matricula"], data["fecha_matricula"], data["fecha_renovacion"],
        data["ultimo_ano_renovado"], data["fecha_vigencia"], data["fecha_cancelacion"],
        data["codigo_tipo_sociedad"], data["tipo_sociedad"], data["codigo_organizacion_juridica"],
        data["organizacion_juridica"], data["codigo_estado_matricula"], data["estado_matricula"],
        data["representante_legal"], data["num_identificacion_representante_legal"],
        data["clase_identificacion_rl"], data["fecha_actualizacion"]
    ])
    
    conn.commit()
    cur.close()
    conn.close()
    
    return id_estadistico

def guardar_empresa_con_id_persona(data: dict, id_estadistico_persona: str) -> str:
    """Guarda una empresa usando el ID estadístico de una persona existente"""
    conn = get_sqlite_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO raw_obt_empresas (
            id_estadistico, razon_social, tipo_documento, numero_documento, digito_verificacion,
            codigo_camara, camara_comercio, matricula, fecha_matricula, fecha_renovacion,
            ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
            tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
            codigo_estado_matricula, estado_matricula, representante_legal,
            num_identificacion_representante_legal, clase_identificacion_rl, fecha_actualizacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_estadistico_persona, data["razon_social"], data["tipo_documento"], data["numero_documento"],
        data.get("digito_verificacion"), data["codigo_camara"], data["camara_comercio"],
        data["matricula"], data["fecha_matricula"], data["fecha_renovacion"],
        data["ultimo_ano_renovado"], data["fecha_vigencia"], data["fecha_cancelacion"],
        data["codigo_tipo_sociedad"], data["tipo_sociedad"], data["codigo_organizacion_juridica"],
        data["organizacion_juridica"], data["codigo_estado_matricula"], data["estado_matricula"],
        data["representante_legal"], data["num_identificacion_representante_legal"],
        data["clase_identificacion_rl"], data["fecha_actualizacion"]
    ])
    
    conn.commit()
    cur.close()
    conn.close()
    
    return id_estadistico_persona 