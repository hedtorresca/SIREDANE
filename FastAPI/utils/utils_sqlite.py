import sqlite3
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from difflib import SequenceMatcher

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

    conn = get_sqlite_connection()
    cur = conn.cursor()

    # Criterio C1 — DOC_EXACTO
    cur.execute(
        """
        SELECT id_estadistico
        FROM raw_obt_personas
        WHERE tipo_documento = ? AND numero_documento = ?
    """,
        [tipo_documento, numero_documento],
    )

    result = cur.fetchone()
    if result:
        cur.close()
        conn.close()
        return {
            "id_estadistico": result[0],
            "coincidencia": {
                "criterio": "C1_DOC_EXACTO",
                "puntaje": 1.0,
                "evidencia": {
                    "tipo_documento": tipo_documento,
                    "numero_documento": numero_documento,
                },
            },
        }

    nombre_solicitud = _construir_nombre_completo(
        primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
    )

    if not nombre_solicitud:
        cur.close()
        conn.close()
        return None

    bloques = _obtener_bloques_documento(numero_documento)

    condiciones = [
        "tipo_documento = ?",
        "ABS(LENGTH(numero_documento) - ?) <= 1",
    ]

    parametros = [tipo_documento, bloques["longitud"]]

    condiciones_or: List[str] = []

    if bloques["prefijo"]:
        condiciones_or.append("SUBSTR(numero_documento, 1, 2) = ?")
        parametros.append(bloques["prefijo"])

    if bloques["sufijo"]:
        condiciones_or.append("SUBSTR(numero_documento, -2, 2) = ?")
        parametros.append(bloques["sufijo"])

    for posicion in bloques["posiciones"]:
        condiciones_or.append("SUBSTR(numero_documento, ?, 1) = ?")
        parametros.extend([posicion, bloques["numero"][posicion - 1]])

    if condiciones_or:
        condiciones.append("(" + " OR ".join(condiciones_or) + ")")

    consulta = f"""
        SELECT id_estadistico,
               numero_documento,
               COALESCE(primer_nombre, ''),
               COALESCE(segundo_nombre, ''),
               COALESCE(primer_apellido, ''),
               COALESCE(segundo_apellido, '')
        FROM raw_obt_personas
        WHERE {' AND '.join(condiciones)}
    """

    cur.execute(consulta, parametros)

    mejor_coincidencia: Optional[Dict[str, Any]] = None
    mejor_puntaje = 0.0

    for row in cur.fetchall():
        numero_doc_cand = row[1]
        if not _doc_diff_una_operacion(str(numero_doc_cand or ""), str(numero_documento or "")):
            continue

        nombre_candidato = _construir_nombre_completo(row[2], row[3], row[4], row[5])
        sim_nombre = _similitud_nombres(nombre_solicitud, nombre_candidato)
        if sim_nombre < 0.90:
            continue

        puntaje = 0.90 + 0.10 * sim_nombre
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_coincidencia = {
                "id_estadistico": row[0],
                "coincidencia": {
                    "criterio": "C2_DOC_1DIG_NOMBRE_SIM",
                    "puntaje": round(puntaje, 4),
                    "evidencia": {
                        "doc_diff_1dig": True,
                        "sim_nombre": round(sim_nombre, 4),
                    },
                },
            }

    cur.close()
    conn.close()

    return mejor_coincidencia

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