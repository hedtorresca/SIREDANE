import cx_Oracle
import os
import sys
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.oracle import VARCHAR2, NUMBER, DATE, TIMESTAMP, CLOB

# Agregar el directorio src al path para importar configuraciones
sys.path.append('/app/src')

try:
    from config.db_config import DbConfig
    from config.database_adapter import DatabaseAdapter
except ImportError:
    # Fallback para desarrollo local
    pass

def get_oracle_connection():
    """Establece conexión con Oracle usando la configuración del proyecto"""
    try:
        # Intentar usar la configuración del proyecto
        db_config = DbConfig()
        if db_config.is_oracle():
            conn_string = db_config.get_connection_string()
            print(f"🔗 Conectando a Oracle: {conn_string}")
            return create_engine(conn_string)
        else:
            raise Exception("Configuración no es para Oracle")
    except Exception as e:
        print(f"⚠️  Error con configuración del proyecto: {e}")
        # Fallback a variables de entorno directas
        try:
            # Intentar con variables de entorno de producción
            host = os.getenv("PROD_ORACLE_HOST", "10.168.48.79")
            port = os.getenv("PROD_ORACLE_PORT", "1522")
            service = os.getenv("PROD_ORACLE_SERVICE", "dbkactus")
            user = os.getenv("PROD_ORACLE_JDBC_USER", "RRAA_DWH")
            password = os.getenv("PROD_ORACLE_JDBC_PASSWORD", "D4n3.rR3E*202S")
            
            conn_string = f"oracle://{user}:{password}@{host}:{port}/{service}"
            print(f"🔗 Conectando con fallback: {conn_string}")
            return create_engine(conn_string)
        except Exception as fallback_error:
            print(f"❌ Error en fallback: {fallback_error}")
            # Último fallback para desarrollo
            conn_string = "oracle://SIRE_STG:sire_password@oracle-db:1521/XEPDB1"
            print(f"🔗 Usando configuración de desarrollo: {conn_string}")
            return create_engine(conn_string)

def generar_id_estadistico(tipo_entidad: str, consecutivo_hex: str) -> str:
    """Genera un ID estadístico con el formato: tipo_entidad + consecutivo_hex"""
    return f"{tipo_entidad}{consecutivo_hex}"

def obtener_siguiente_consecutivo_personas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para personas"""
    engine = get_oracle_connection()
    
    with engine.connect() as conn:
        # Tomar el máximo sufijo HEX (8 chars) como cadena para evitar TO_NUMBER en SQL
        result = conn.execute(text("""
            SELECT NVL(MAX(SUBSTR(id_estadistico, 3)), '00000000')
            FROM RRAA_DWH.control_ids_generados 
            WHERE tipo_entidad = '01'
              AND REGEXP_LIKE(SUBSTR(id_estadistico, 3), '^[0-9A-Fa-f]{8}$')
        """))
        max_hex = result.scalar()

    try:
        base = int(str(max_hex), 16) if max_hex else 0
    except Exception:
        base = 0
    siguiente = base + 1
    return f"{siguiente:08X}"

def obtener_siguiente_consecutivo_empresas() -> str:
    """Obtiene el siguiente consecutivo hexadecimal para empresas"""
    engine = get_oracle_connection()
    
    with engine.connect() as conn:
        # Tomar el máximo sufijo HEX (8 chars) como cadena para evitar TO_NUMBER en SQL
        result = conn.execute(text("""
            SELECT NVL(MAX(SUBSTR(id_estadistico, 3)), '00000000')
            FROM RRAA_DWH.control_ids_generados 
            WHERE tipo_entidad = '02'
              AND REGEXP_LIKE(SUBSTR(id_estadistico, 3), '^[0-9A-Fa-f]{8}$')
        """))
        max_hex = result.scalar()

    try:
        base = int(str(max_hex), 16) if max_hex else 0
    except Exception:
        base = 0
    siguiente = base + 1
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


def _obtener_bloques_documento(numero_documento: Optional[str]) -> Dict[str, Any]:
    numero = "" if numero_documento is None else str(numero_documento).strip()

    longitud = len(numero)
    bloques: Dict[str, Any] = {
        "numero": numero,
        "longitud": longitud,
        "prefijo": numero[:2] if longitud >= 2 else None,
        "sufijo": numero[-2:] if longitud >= 2 else None,
        "posiciones": []
    }

    if longitud > 1:
        posiciones: List[int] = [1, longitud]
        if longitud > 2:
            posiciones.append((longitud // 2) + 1)
            if longitud % 2 == 0:
                posiciones.append(longitud // 2)
        bloques["posiciones"] = sorted(set(posiciones))

    return bloques


def buscar_persona_existente(
    tipo_documento: str,
    numero_documento: str,
    primer_nombre: Optional[str] = None,
    segundo_nombre: Optional[str] = None,
    primer_apellido: Optional[str] = None,
    segundo_apellido: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Busca si una persona ya existe en la base de datos siguiendo los criterios de cruce C1 y C2."""

    engine = get_oracle_connection()

    with engine.connect() as conn:
        # Criterio C1 — DOC_EXACTO
        result = conn.execute(
            text(
                """
                SELECT id_estadistico
                FROM RRAA_DWH.control_ids_generados
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

        bloques = _obtener_bloques_documento(numero_documento)

        condiciones = [
            "c.tipo_entidad = '01'",
            "c.tipo_documento = :tipo_doc",
            "ABS(LENGTH(c.numero_documento) - :len_doc) <= 1",
        ]

        parametros: Dict[str, Any] = {
            "tipo_doc": tipo_documento,
            "len_doc": bloques["longitud"],
        }

        condiciones_or: List[str] = []

        if bloques["prefijo"]:
            parametros["prefijo"] = bloques["prefijo"]
            condiciones_or.append("SUBSTR(c.numero_documento, 1, 2) = :prefijo")

        if bloques["sufijo"]:
            parametros["sufijo"] = bloques["sufijo"]
            condiciones_or.append("SUBSTR(c.numero_documento, -2, 2) = :sufijo")

        for idx, posicion in enumerate(bloques["posiciones"]):
            parametros[f"pos_{idx}"] = posicion
            parametros[f"char_{idx}"] = bloques["numero"][posicion - 1]
            condiciones_or.append(
                f"SUBSTR(c.numero_documento, :pos_{idx}, 1) = :char_{idx}"
            )

        if condiciones_or:
            condiciones.append("(" + " OR ".join(condiciones_or) + ")")

        consulta = text(
            f"""
            SELECT c.id_estadistico,
                   c.numero_documento,
                   NVL(p.primer_nombre, '') AS primer_nombre,
                   NVL(p.segundo_nombre, '') AS segundo_nombre,
                   NVL(p.primer_apellido, '') AS primer_apellido,
                   NVL(p.segundo_apellido, '') AS segundo_apellido
            FROM RRAA_DWH.control_ids_generados c
            LEFT JOIN RRAA_DWH.raw_obt_personas p
              ON c.id_estadistico = p.id_estadistico
            WHERE {'\n              AND '.join(condiciones)}
            """
        )

        candidatos = conn.execute(consulta, parametros)

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
    engine = get_oracle_connection()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id_estadistico 
            FROM RRAA_DWH.control_ids_generados 
            WHERE tipo_entidad = '02' AND tipo_documento = :tipo_doc AND numero_documento = :num_doc
        """), {"tipo_doc": tipo_documento, "num_doc": numero_documento})
        
        row = result.fetchone()
        return row[0] if row else None

def guardar_nueva_persona(data: dict) -> str:
    """Genera un nuevo ID estadístico para una persona y lo guarda en la tabla de control y raw_obt_personas"""
    engine = get_oracle_connection()
    
    consecutivo = obtener_siguiente_consecutivo_personas()
    id_estadistico = generar_id_estadistico("01", consecutivo)
    
    # Normalización y saneamiento de entrada para evitar ORA-01722 (invalid number)
    def _normalize_str(value):
        v = None if value is None else str(value).strip()
        return None if v == "" else v
    def _normalize_int(value):
        if value is None:
            return None
        s = str(value).strip()
        if s == "":
            return None
        try:
            return int(s)
        except Exception:
            return None
    def _normalize_date(value):
        if value is None:
            return None
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return value
        try:
            # admitir formatos comunes
            import datetime as _dt
            from datetime import datetime as _dtc
            # intentar ISO o dd/mm/yyyy
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    return _dtc.strptime(str(value).strip(), fmt).date()
                except Exception:
                    continue
        except Exception:
            pass
        return None

    tipo_doc_norm = _normalize_str(data.get("tipo_documento"))
    num_doc_norm = _normalize_str(data.get("numero_documento"))
    primer_nom_norm = _normalize_str(data.get("primer_nombre"))
    segundo_nom_norm = _normalize_str(data.get("segundo_nombre"))
    primer_ape_norm = _normalize_str(data.get("primer_apellido"))
    segundo_ape_norm = _normalize_str(data.get("segundo_apellido"))
    fecha_nac_norm = _normalize_date(data.get("fecha_nacimiento"))
    sexo_norm = _normalize_str(data.get("sexo_an"))
    cod_mun_norm = _normalize_int(data.get("codigo_municipio_nacimiento"))
    cod_pais_norm = _normalize_int(data.get("codigo_pais_nacimiento"))

    # Validaciones defensivas adicionales (además del esquema Pydantic)
    if not tipo_doc_norm or not num_doc_norm:
        raise ValueError("tipo_documento y numero_documento no pueden ser vacíos")

    with engine.begin() as conn:
        # Guardar en la tabla de control de IDs generados
        conn.execute(text("""
            INSERT INTO RRAA_DWH.control_ids_generados (
                id_estadistico, tipo_entidad, tipo_documento, numero_documento, 
                fecha_generacion, estado
            ) VALUES (
                :id_est, :tipo_ent, :tipo_doc, :num_doc, 
                CURRENT_TIMESTAMP, 'generado'
            )
        """), {
            "id_est": id_estadistico,
            "tipo_ent": "01",
            "tipo_doc": tipo_doc_norm,
            "num_doc": num_doc_norm
        })
        
        # Guardar en la tabla raw_obt_personas
        conn.execute(text("""
            INSERT INTO RRAA_DWH.raw_obt_personas (
                id_estadistico, tipo_documento, numero_documento, primer_nombre,
                segundo_nombre, primer_apellido, segundo_apellido, fecha_nacimiento,
                sexo_an, codigo_municipio_nacimiento, codigo_pais_nacimiento, load_date
            ) VALUES (
                :id_est, :tipo_doc, :num_doc, :primer_nom,
                :segundo_nom, :primer_ape, :segundo_ape, :fecha_nac,
                :sexo, :cod_mun, :cod_pais, CURRENT_TIMESTAMP
            )
        """), {
            "id_est": id_estadistico,
            "tipo_doc": tipo_doc_norm,
            "num_doc": num_doc_norm,
            "primer_nom": primer_nom_norm,
            "segundo_nom": segundo_nom_norm,
            "primer_ape": primer_ape_norm,
            "segundo_ape": segundo_ape_norm,
            "fecha_nac": fecha_nac_norm,
            "sexo": sexo_norm,
            "cod_mun": cod_mun_norm,
            "cod_pais": cod_pais_norm
        })
    
    return id_estadistico

def guardar_nueva_empresa(data: dict) -> str:
    """Genera un nuevo ID estadístico para una empresa y lo guarda en la tabla de control y raw_obt_empresas"""
    engine = get_oracle_connection()
    
    consecutivo = obtener_siguiente_consecutivo_empresas()
    id_estadistico = generar_id_estadistico("02", consecutivo)
    
    with engine.begin() as conn:
        # Guardar en la tabla de control de IDs generados
        conn.execute(text("""
            INSERT INTO RRAA_DWH.control_ids_generados (
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
        
        # Guardar en la tabla raw_obt_empresas
        conn.execute(text("""
            INSERT INTO RRAA_DWH.raw_obt_empresas (
                id_estadistico, razon_social, tipo_documento, numero_documento, digito_verificacion,
                codigo_camara, camara_comercio, matricula, fecha_matricula, fecha_renovacion,
                ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
                tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
                codigo_estado_matricula, estado_matricula, representante_legal,
                num_identificacion_representante_legal, clase_identificacion_rl, fecha_actualizacion, load_date
            ) VALUES (
                :id_est, :razon_soc, :tipo_doc, :num_doc, :dig_ver,
                :cod_cam, :cam_com, :mat, :fecha_mat, :fecha_ren,
                :ult_ano, :fecha_vig, :fecha_can, :cod_tipo_soc,
                :tipo_soc, :cod_org_jur, :org_jur,
                :cod_est_mat, :est_mat, :rep_leg,
                :num_id_rep, :clase_id_rl, :fecha_act, CURRENT_TIMESTAMP
            )
        """), {
            "id_est": id_estadistico,
            "razon_soc": data.get("razon_social"),
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"],
            "dig_ver": data.get("digito_verificacion"),
            "cod_cam": data.get("codigo_camara"),
            "cam_com": data.get("camara_comercio"),
            "mat": data.get("matricula"),
            "fecha_mat": data.get("fecha_matricula"),
            "fecha_ren": data.get("fecha_renovacion"),
            "ult_ano": data.get("ultimo_ano_renovado"),
            "fecha_vig": data.get("fecha_vigencia"),
            "fecha_can": data.get("fecha_cancelacion"),
            "cod_tipo_soc": data.get("codigo_tipo_sociedad"),
            "tipo_soc": data.get("tipo_sociedad"),
            "cod_org_jur": data.get("codigo_organizacion_juridica"),
            "org_jur": data.get("organizacion_juridica"),
            "cod_est_mat": data.get("codigo_estado_matricula"),
            "est_mat": data.get("estado_matricula"),
            "rep_leg": data.get("representante_legal"),
            "num_id_rep": data.get("num_identificacion_representante_legal"),
            "clase_id_rl": data.get("clase_identificacion_rl"),
            "fecha_act": data.get("fecha_actualizacion")
        })
    
    return id_estadistico

def guardar_empresa_con_id_persona(data: dict, id_estadistico_persona: str) -> str:
    """Guarda una empresa usando el ID estadístico de una persona existente"""
    engine = get_oracle_connection()
    
    with engine.begin() as conn:
        # Guardar en la tabla de control de IDs generados (como empresa)
        conn.execute(text("""
            INSERT INTO RRAA_DWH.control_ids_generados (
                id_estadistico, tipo_entidad, tipo_documento, numero_documento, 
                fecha_generacion, estado
            ) VALUES (
                :id_est, :tipo_ent, :tipo_doc, :num_doc, 
                CURRENT_TIMESTAMP, 'generado'
            )
        """), {
            "id_est": id_estadistico_persona,
            "tipo_ent": "02",  # Empresa
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"]
        })
        
        # Guardar en la tabla raw_obt_empresas
        conn.execute(text("""
            INSERT INTO RRAA_DWH.raw_obt_empresas (
                id_estadistico, razon_social, tipo_documento, numero_documento, digito_verificacion,
                codigo_camara, camara_comercio, matricula, fecha_matricula, fecha_renovacion,
                ultimo_ano_renovado, fecha_vigencia, fecha_cancelacion, codigo_tipo_sociedad,
                tipo_sociedad, codigo_organizacion_juridica, organizacion_juridica,
                codigo_estado_matricula, estado_matricula, representante_legal,
                num_identificacion_representante_legal, clase_identificacion_rl, fecha_actualizacion, load_date
            ) VALUES (
                :id_est, :razon_soc, :tipo_doc, :num_doc, :dig_ver,
                :cod_cam, :cam_com, :mat, :fecha_mat, :fecha_ren,
                :ult_ano, :fecha_vig, :fecha_can, :cod_tipo_soc,
                :tipo_soc, :cod_org_jur, :org_jur,
                :cod_est_mat, :est_mat, :rep_leg,
                :num_id_rep, :clase_id_rl, :fecha_act, CURRENT_TIMESTAMP
            )
        """), {
            "id_est": id_estadistico_persona,
            "razon_soc": data.get("razon_social"),
            "tipo_doc": data["tipo_documento"],
            "num_doc": data["numero_documento"],
            "dig_ver": data.get("digito_verificacion"),
            "cod_cam": data.get("codigo_camara"),
            "cam_com": data.get("camara_comercio"),
            "mat": data.get("matricula"),
            "fecha_mat": data.get("fecha_matricula"),
            "fecha_ren": data.get("fecha_renovacion"),
            "ult_ano": data.get("ultimo_ano_renovado"),
            "fecha_vig": data.get("fecha_vigencia"),
            "fecha_can": data.get("fecha_cancelacion"),
            "cod_tipo_soc": data.get("codigo_tipo_sociedad"),
            "tipo_soc": data.get("tipo_sociedad"),
            "cod_org_jur": data.get("codigo_organizacion_juridica"),
            "org_jur": data.get("organizacion_juridica"),
            "cod_est_mat": data.get("codigo_estado_matricula"),
            "est_mat": data.get("estado_matricula"),
            "rep_leg": data.get("representante_legal"),
            "num_id_rep": data.get("num_identificacion_representante_legal"),
            "clase_id_rl": data.get("clase_identificacion_rl"),
            "fecha_act": data.get("fecha_actualizacion")
        })
    
    return id_estadistico_persona
