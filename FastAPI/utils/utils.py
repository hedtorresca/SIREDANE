import psycopg2
import os
import sys
from typing import Any, Dict, Optional
from difflib import SequenceMatcher
from sqlalchemy import create_engine, text

# Agregar el directorio src al path para importar configuraciones
sys.path.append('/app/src')

try:
    from config.db_config import DbConfig
    from config.database_adapter import DatabaseAdapter
except ImportError:
    # Fallback para desarrollo local
    pass

def get_postgres_connection():
    """Establece conexión con PostgreSQL usando la configuración del proyecto"""
    try:
        # Intentar usar la configuración del proyecto
        db_config = DbConfig(environment="dev", db_type="postgresql")
        conn_string = db_config.get_sqlalchemy_conn_string()
        return create_engine(conn_string)
    except:
        # Fallback a variables de entorno
        conn_string = "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw"
        return create_engine(conn_string)

def generar_id_estadistico(tipo_entidad: str, consecutivo_hex: str) -> str:
    """Genera un ID estadístico con el formato: tipo_entidad + consecutivo_hex"""
    return f"{tipo_entidad}{consecutivo_hex}"

def obtener_siguiente_consecutivo_personas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para personas"""
    engine = get_postgres_connection()
    
    with engine.connect() as conn:
        # Buscar el máximo ID estadístico de personas (que empieza con '01')
        result = conn.execute(text("""
            SELECT MAX(CAST(SUBSTRING(id_estadistico, 3) AS INTEGER))
            FROM sire_sta.control_ids_generados 
            WHERE tipo_entidad = '01'
        """))
        
        max_consecutivo = result.scalar()
    
    if max_consecutivo is None:
        return "00000001"
    
    # Incrementar y convertir a hexadecimal de 8 dígitos
    siguiente = max_consecutivo + 1
    return f"{siguiente:08X}"

def obtener_siguiente_consecutivo_empresas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para empresas"""
    engine = get_postgres_connection()
    
    with engine.connect() as conn:
        # Buscar el máximo ID estadístico de empresas (que empieza con '02')
        result = conn.execute(text("""
            SELECT MAX(CAST(SUBSTRING(id_estadistico, 3) AS INTEGER))
            FROM sire_sta.control_ids_generados 
            WHERE tipo_entidad = '02'
        """))
        
        max_consecutivo = result.scalar()
    
    if max_consecutivo is None:
        return "00000001"
    
    # Incrementar y convertir a hexadecimal de 8 dígitos
    siguiente = max_consecutivo + 1
    return f"{siguiente:08X}"

def _normalizar_cadena(valor: Optional[str]) -> str:
    if valor is None:
        return ""
    return " ".join(str(valor).strip().upper().split())


def _construir_nombre_completo(
    primer_nombre: Optional[str],
    segundo_nombre: Optional[str],
    primer_apellido: Optional[str],
    segundo_apellido: Optional[str],
) -> str:
    partes = [
        _normalizar_cadena(primer_nombre),
        _normalizar_cadena(segundo_nombre),
        _normalizar_cadena(primer_apellido),
        _normalizar_cadena(segundo_apellido),
    ]
    return " ".join([parte for parte in partes if parte])


def _doc_diff_una_operacion(doc_a: str, doc_b: str) -> bool:
    if doc_a is None or doc_b is None:
        return False

    if doc_a == doc_b:
        return False

    doc_a = doc_a.strip()
    doc_b = doc_b.strip()

    len_a = len(doc_a)
    len_b = len(doc_b)

    if abs(len_a - len_b) > 1:
        return False

    if len_a == len_b:
        diferencias = [i for i in range(len_a) if doc_a[i] != doc_b[i]]
        if len(diferencias) == 1:
            return True
        if len(diferencias) == 2:
            i, j = diferencias
            return j == i + 1 and doc_a[i] == doc_b[j] and doc_a[j] == doc_b[i]
        return False

    if len_a > len_b:
        largo, corto = doc_a, doc_b
    else:
        largo, corto = doc_b, doc_a

    i = j = 0
    diferencia_encontrada = False
    while i < len(largo) and j < len(corto):
        if largo[i] != corto[j]:
            if diferencia_encontrada:
                return False
            diferencia_encontrada = True
            i += 1
        else:
            i += 1
            j += 1

    return True


def _similitud_nombres(nombre_a: str, nombre_b: str) -> float:
    if not nombre_a or not nombre_b:
        return 0.0
    return SequenceMatcher(None, nombre_a, nombre_b).ratio()


def buscar_persona_existente(
    tipo_documento: str,
    numero_documento: str,
    primer_nombre: Optional[str] = None,
    segundo_nombre: Optional[str] = None,
    primer_apellido: Optional[str] = None,
    segundo_apellido: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Busca si una persona ya existe en la base de datos siguiendo los criterios de cruce C1 y C2."""

    engine = get_postgres_connection()

    with engine.connect() as conn:
        # Criterio C1 — DOC_EXACTO
        result = conn.execute(
            text(
                """
                SELECT id_estadistico
                FROM sire_sta.control_ids_generados
                WHERE tipo_entidad = '01'
                  AND tipo_documento = :tipo_doc
                  AND numero_documento = :num_doc
                """
            ),
            {"tipo_doc": tipo_documento, "num_doc": numero_documento},
        )

        row = result.fetchone()
        if row:
            id_estadistico = row[0]
            return {
                "id_estadistico": id_estadistico,
                "coincidencia": {
                    "criterio": "C1_DOC_EXACTO",
                    "puntaje": 1.0,
                    "evidencia": {
                        "tipo_documento": tipo_documento,
                        "numero_documento": numero_documento,
                    },
                },
            }

        # Criterio C2 — DOC_1DIG + NOMBRE_SIM≥0.90
        nombre_solicitud = _construir_nombre_completo(
            primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
        )

        if not nombre_solicitud:
            return None

        candidatos = conn.execute(
            text(
                """
                SELECT c.id_estadistico,
                       c.numero_documento,
                       COALESCE(p.primer_nombre, '') AS primer_nombre,
                       COALESCE(p.segundo_nombre, '') AS segundo_nombre,
                       COALESCE(p.primer_apellido, '') AS primer_apellido,
                       COALESCE(p.segundo_apellido, '') AS segundo_apellido
                FROM sire_sta.control_ids_generados c
                LEFT JOIN sire_sta.raw_obt_personas p
                  ON c.id_estadistico = p.id_estadistico
                WHERE c.tipo_entidad = '01'
                  AND c.tipo_documento = :tipo_doc
            """
            ),
            {"tipo_doc": tipo_documento},
        )

        mejor_coincidencia: Optional[Dict[str, Any]] = None
        mejor_puntaje = 0.0

        for candidato in candidatos:
            id_est_cand = candidato[0]
            numero_doc_cand = candidato[1]
            if not _doc_diff_una_operacion(str(numero_doc_cand or ""), str(numero_documento or "")):
                continue

            nombre_candidato = _construir_nombre_completo(
                candidato[2], candidato[3], candidato[4], candidato[5]
            )
            sim_nombre = _similitud_nombres(nombre_solicitud, nombre_candidato)
            if sim_nombre < 0.90:
                continue

            puntaje = 0.90 + 0.10 * sim_nombre
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_coincidencia = {
                    "id_estadistico": id_est_cand,
                    "coincidencia": {
                        "criterio": "C2_DOC_1DIG_NOMBRE_SIM",
                        "puntaje": round(puntaje, 4),
                        "evidencia": {
                            "doc_diff_1dig": True,
                            "sim_nombre": round(sim_nombre, 4),
                        },
                    },
                }

        return mejor_coincidencia

def buscar_empresa_existente(tipo_documento: str, numero_documento: str) -> Optional[str]:
    """Busca si una empresa ya existe en la base de datos"""
    engine = get_postgres_connection()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id_estadistico 
            FROM sire_sta.control_ids_generados 
            WHERE tipo_entidad = '02' AND tipo_documento = :tipo_doc AND numero_documento = :num_doc
        """), {"tipo_doc": tipo_documento, "num_doc": numero_documento})
        
        row = result.fetchone()
        return row[0] if row else None

def guardar_nueva_persona(data: dict) -> str:
    """Genera un nuevo ID estadístico para una persona y lo guarda en la tabla de control"""
    engine = get_postgres_connection()
    
    consecutivo = obtener_siguiente_consecutivo_personas()
    id_estadistico = generar_id_estadistico("01", consecutivo)
    
    # Solo guardar en la tabla de control de IDs generados, no en raw_obt_personas
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sire_sta.control_ids_generados (
                id_estadistico, tipo_entidad, tipo_documento, numero_documento, 
                fecha_generacion, estado
            ) VALUES (
                :id_est, :tipo_ent, :tipo_doc, :num_doc, 
                CURRENT_TIMESTAMP, 'generado'
            )
        """), {
            "id_est": id_estadistico,
            "tipo_ent": "01",
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"]
        })
    
    return id_estadistico

def guardar_nueva_empresa(data: dict) -> str:
    """Genera un nuevo ID estadístico para una empresa y lo guarda en la tabla de control"""
    engine = get_postgres_connection()
    
    consecutivo = obtener_siguiente_consecutivo_empresas()
    id_estadistico = generar_id_estadistico("02", consecutivo)
    
    # Solo guardar en la tabla de control de IDs generados, no en raw_obt_empresas
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sire_sta.control_ids_generados (
                id_estadistico, tipo_entidad, tipo_documento, numero_documento, 
                fecha_generacion, estado
            ) VALUES (
                :id_est, :tipo_ent, :tipo_doc, :num_doc, 
                CURRENT_TIMESTAMP, 'generado'
            )
        """), {
            "id_est": id_estadistico,
            "tipo_ent": "02",
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"]
        })
    
    return id_estadistico

def guardar_empresa_con_id_persona(data: dict, id_estadistico_persona: str) -> str:
    """Guarda una empresa usando el ID estadístico de una persona existente"""
    engine = get_postgres_connection()
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sire_sta.raw_obt_empresas (
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
            "id_est": id_estadistico_persona,
            "razon_soc": data["razon_social"],
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"],
            "dig_ver": data.get("digito_verificacion"),
            "cod_cam": data["codigo_camara"],
            "cam_com": data["camara_comercio"],
            "mat": data["matricula"],
            "fecha_mat": data["fecha_matricula"],
            "fecha_ren": data["fecha_renovacion"],
            "ult_ano": data["ultimo_ano_renovado"],
            "fecha_vig": data["fecha_vigencia"],
            "fecha_can": data["fecha_cancelacion"],
            "cod_tipo_soc": data["codigo_tipo_sociedad"],
            "tipo_soc": data["tipo_sociedad"],
            "cod_org_jur": data["codigo_organizacion_juridica"],
            "org_jur": data["organizacion_juridica"],
            "cod_est_mat": data["codigo_estado_matricula"],
            "est_mat": data["estado_matricula"],
            "rep_leg": data["representante_legal"],
            "num_id_rep": data["num_identificacion_representante_legal"],
            "clase_id_rl": data["clase_identificacion_rl"],
            "fecha_act": data["fecha_actualizacion"]
        })
    
    return id_estadistico_persona