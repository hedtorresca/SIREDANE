# Scripts SQL - SIRE

## Visión General

Los scripts SQL de SIRE son fundamentales para la configuración y mantenimiento de la base de datos. Están organizados por tipo de base de datos (PostgreSQL y Oracle) y por funcionalidad (creación de esquemas, tablas, limpieza, etc.).

## Estructura de Scripts

```
scripts_sql/
├── oracle/
│   ├── create_schemas.sql
│   ├── sire_dv_tables.sql
│   ├── sire_obt_tables.sql
│   ├── sire_sta_tables.sql
│   ├── cleanup_duplicates.sql
│   ├── control_ids_generados.sql
│   ├── migrate_to_control_table.sql
│   ├── check_and_create_structure.sql
│   ├── create_user_docker_oracle.sql
│   └── init_minimal.sql
└── postgres/
    ├── create_schemas.sql
    ├── sire_dv_tables.sql
    ├── sire_obt_tables.sql
    ├── sire_sta_tables.sql
    ├── cleanup_duplicates.sql
    ├── control_ids_generados.sql
    └── migrate_to_control_table.sql
```

## Scripts de Oracle

### 1. create_schemas.sql

**Propósito**: Crea los esquemas necesarios para el sistema SIRE.

**Esquemas Creados**:
- `sire_sta` - Staging (datos temporales)
- `sire_obt` - Datos sensibles (obtenidos)
- `sire_dv` - Data Vault
- `sire_audit` - Auditoría

**Contenido**:
```sql
-- Crear esquemas para SIRE
CREATE USER sire_sta IDENTIFIED BY sire_sta_password;
CREATE USER sire_obt IDENTIFIED BY sire_obt_password;
CREATE USER sire_dv IDENTIFIED BY sire_dv_password;
CREATE USER sire_audit IDENTIFIED BY sire_audit_password;

-- Otorgar permisos
GRANT CONNECT, RESOURCE TO sire_sta;
GRANT CONNECT, RESOURCE TO sire_obt;
GRANT CONNECT, RESOURCE TO sire_dv;
GRANT CONNECT, RESOURCE TO sire_audit;

-- Permisos adicionales
GRANT CREATE TABLE TO sire_sta;
GRANT CREATE TABLE TO sire_obt;
GRANT CREATE TABLE TO sire_dv;
GRANT CREATE TABLE TO sire_audit;

-- Permisos de secuencias
GRANT CREATE SEQUENCE TO sire_sta;
GRANT CREATE SEQUENCE TO sire_obt;
GRANT CREATE SEQUENCE TO sire_dv;
GRANT CREATE SEQUENCE TO sire_audit;

-- Permisos de índices
GRANT CREATE INDEX TO sire_sta;
GRANT CREATE INDEX TO sire_obt;
GRANT CREATE INDEX TO sire_dv;
GRANT CREATE INDEX TO sire_audit;
```

### 2. sire_dv_tables.sql

**Propósito**: Crea las tablas del Data Vault siguiendo la metodología Data Vault 2.0.

**Tablas Creadas**:
- **Hubs**: `hub_persona`, `hub_empresa`, `hub_documento`
- **Satellites**: `sat_persona`, `sat_empresa`
- **Links**: `link_persona_empresa`

**Contenido**:
```sql
-- Conectar al esquema Data Vault
CONNECT sire_dv/sire_dv_password;

-- Tabla Hub Persona
CREATE TABLE hub_persona (
    hub_persona_key VARCHAR2(50) PRIMARY KEY,
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    hash_key VARCHAR2(64) NOT NULL,
    load_date DATE DEFAULT SYSDATE,
    record_source VARCHAR2(100) DEFAULT 'SIRE_ETL'
);

-- Tabla Hub Empresa
CREATE TABLE hub_empresa (
    hub_empresa_key VARCHAR2(50) PRIMARY KEY,
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    hash_key VARCHAR2(64) NOT NULL,
    load_date DATE DEFAULT SYSDATE,
    record_source VARCHAR2(100) DEFAULT 'SIRE_ETL'
);

-- Tabla Satellite Persona
CREATE TABLE sat_persona (
    hub_persona_key VARCHAR2(50) NOT NULL,
    primer_nombre VARCHAR2(100),
    segundo_nombre VARCHAR2(100),
    primer_apellido VARCHAR2(100),
    segundo_apellido VARCHAR2(100),
    fecha_nacimiento DATE,
    sexo_an CHAR(1),
    codigo_municipio_nacimiento VARCHAR2(10),
    codigo_pais_nacimiento VARCHAR2(10),
    fecha_defuncion DATE,
    hash_diff VARCHAR2(64) NOT NULL,
    load_date DATE DEFAULT SYSDATE,
    record_source VARCHAR2(100) DEFAULT 'SIRE_ETL',
    PRIMARY KEY (hub_persona_key, load_date),
    FOREIGN KEY (hub_persona_key) REFERENCES hub_persona(hub_persona_key)
);

-- Tabla Satellite Empresa
CREATE TABLE sat_empresa (
    hub_empresa_key VARCHAR2(50) NOT NULL,
    razon_social VARCHAR2(500),
    digito_verificacion VARCHAR2(2),
    codigo_camara VARCHAR2(10),
    camara_comercio VARCHAR2(100),
    matricula VARCHAR2(20),
    fecha_matricula DATE,
    fecha_renovacion DATE,
    ultimo_ano_renovado NUMBER(4),
    fecha_vigencia DATE,
    fecha_cancelacion DATE,
    codigo_tipo_sociedad VARCHAR2(10),
    tipo_sociedad VARCHAR2(100),
    codigo_organizacion_juridica VARCHAR2(10),
    organizacion_juridica VARCHAR2(100),
    codigo_estado_matricula VARCHAR2(10),
    estado_matricula VARCHAR2(50),
    representante_legal VARCHAR2(200),
    num_identificacion_representante_legal VARCHAR2(20),
    clase_identificacion_rl VARCHAR2(10),
    fecha_actualizacion DATE,
    hash_diff VARCHAR2(64) NOT NULL,
    load_date DATE DEFAULT SYSDATE,
    record_source VARCHAR2(100) DEFAULT 'SIRE_ETL',
    PRIMARY KEY (hub_empresa_key, load_date),
    FOREIGN KEY (hub_empresa_key) REFERENCES hub_empresa(hub_empresa_key)
);

-- Tabla Link Persona-Empresa
CREATE TABLE link_persona_empresa (
    link_persona_empresa_key VARCHAR2(50) PRIMARY KEY,
    hub_persona_key VARCHAR2(50) NOT NULL,
    hub_empresa_key VARCHAR2(50) NOT NULL,
    hash_key VARCHAR2(64) NOT NULL,
    load_date DATE DEFAULT SYSDATE,
    record_source VARCHAR2(100) DEFAULT 'SIRE_ETL',
    FOREIGN KEY (hub_persona_key) REFERENCES hub_persona(hub_persona_key),
    FOREIGN KEY (hub_empresa_key) REFERENCES hub_empresa(hub_empresa_key)
);

-- Crear índices para optimización
CREATE INDEX idx_hub_persona_hash ON hub_persona(hash_key);
CREATE INDEX idx_hub_empresa_hash ON hub_empresa(hash_key);
CREATE INDEX idx_sat_persona_hash ON sat_persona(hash_diff);
CREATE INDEX idx_sat_empresa_hash ON sat_empresa(hash_diff);
CREATE INDEX idx_link_persona_empresa_hash ON link_persona_empresa(hash_key);
```

### 3. sire_obt_tables.sql

**Propósito**: Crea las tablas para datos sensibles (obtenidos) que requieren pseudonimización.

**Tablas Creadas**:
- `personas_obt` - Datos sensibles de personas
- `empresas_obt` - Datos sensibles de empresas
- `control_ids_generados` - Control de IDs estadísticos

**Contenido**:
```sql
-- Conectar al esquema de datos sensibles
CONNECT sire_obt/sire_obt_password;

-- Tabla de control de IDs generados
CREATE TABLE control_ids_generados (
    id_estadistico VARCHAR2(50) PRIMARY KEY,
    tipo_entidad VARCHAR2(2) NOT NULL,
    consecutivo NUMBER(10) NOT NULL,
    fecha_generacion DATE DEFAULT SYSDATE,
    usuario_generacion VARCHAR2(100),
    estado VARCHAR2(20) DEFAULT 'ACTIVO',
    observaciones VARCHAR2(500)
);

-- Tabla de personas obtenidas
CREATE TABLE personas_obt (
    id_estadistico VARCHAR2(50) PRIMARY KEY,
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    primer_nombre VARCHAR2(100),
    segundo_nombre VARCHAR2(100),
    primer_apellido VARCHAR2(100),
    segundo_apellido VARCHAR2(100),
    fecha_nacimiento DATE,
    sexo_an CHAR(1),
    codigo_municipio_nacimiento VARCHAR2(10),
    codigo_pais_nacimiento VARCHAR2(10),
    fecha_defuncion DATE,
    fecha_obtencion DATE DEFAULT SYSDATE,
    fuente_datos VARCHAR2(100),
    hash_key VARCHAR2(64) NOT NULL,
    FOREIGN KEY (id_estadistico) REFERENCES sire_dv.hub_persona(hub_persona_key)
);

-- Tabla de empresas obtenidas
CREATE TABLE empresas_obt (
    id_estadistico VARCHAR2(50) PRIMARY KEY,
    razon_social VARCHAR2(500),
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    digito_verificacion VARCHAR2(2),
    codigo_camara VARCHAR2(10),
    camara_comercio VARCHAR2(100),
    matricula VARCHAR2(20),
    fecha_matricula DATE,
    fecha_renovacion DATE,
    ultimo_ano_renovado NUMBER(4),
    fecha_vigencia DATE,
    fecha_cancelacion DATE,
    codigo_tipo_sociedad VARCHAR2(10),
    tipo_sociedad VARCHAR2(100),
    codigo_organizacion_juridica VARCHAR2(10),
    organizacion_juridica VARCHAR2(100),
    codigo_estado_matricula VARCHAR2(10),
    estado_matricula VARCHAR2(50),
    representante_legal VARCHAR2(200),
    num_identificacion_representante_legal VARCHAR2(20),
    clase_identificacion_rl VARCHAR2(10),
    fecha_actualizacion DATE,
    fecha_obtencion DATE DEFAULT SYSDATE,
    fuente_datos VARCHAR2(100),
    hash_key VARCHAR2(64) NOT NULL,
    FOREIGN KEY (id_estadistico) REFERENCES sire_dv.hub_empresa(hub_empresa_key)
);

-- Crear índices
CREATE INDEX idx_personas_obt_hash ON personas_obt(hash_key);
CREATE INDEX idx_empresas_obt_hash ON empresas_obt(hash_key);
CREATE INDEX idx_control_ids_tipo ON control_ids_generados(tipo_entidad);
```

### 4. sire_sta_tables.sql

**Propósito**: Crea las tablas de staging para datos temporales durante el procesamiento ETL.

**Tablas Creadas**:
- `personas_sta` - Datos temporales de personas
- `empresas_sta` - Datos temporales de empresas
- `etl_log` - Log de operaciones ETL

**Contenido**:
```sql
-- Conectar al esquema de staging
CONNECT sire_sta/sire_sta_password;

-- Tabla de personas en staging
CREATE TABLE personas_sta (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    primer_nombre VARCHAR2(100),
    segundo_nombre VARCHAR2(100),
    primer_apellido VARCHAR2(100),
    segundo_apellido VARCHAR2(100),
    fecha_nacimiento DATE,
    sexo_an CHAR(1),
    codigo_municipio_nacimiento VARCHAR2(10),
    codigo_pais_nacimiento VARCHAR2(10),
    fecha_defuncion DATE,
    fecha_carga DATE DEFAULT SYSDATE,
    archivo_origen VARCHAR2(200),
    hash_key VARCHAR2(64),
    hash_diff VARCHAR2(64)
);

-- Tabla de empresas en staging
CREATE TABLE empresas_sta (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    razon_social VARCHAR2(500),
    tipo_documento VARCHAR2(10) NOT NULL,
    numero_documento VARCHAR2(20) NOT NULL,
    digito_verificacion VARCHAR2(2),
    codigo_camara VARCHAR2(10),
    camara_comercio VARCHAR2(100),
    matricula VARCHAR2(20),
    fecha_matricula DATE,
    fecha_renovacion DATE,
    ultimo_ano_renovado NUMBER(4),
    fecha_vigencia DATE,
    fecha_cancelacion DATE,
    codigo_tipo_sociedad VARCHAR2(10),
    tipo_sociedad VARCHAR2(100),
    codigo_organizacion_juridica VARCHAR2(10),
    organizacion_juridica VARCHAR2(100),
    codigo_estado_matricula VARCHAR2(10),
    estado_matricula VARCHAR2(50),
    representante_legal VARCHAR2(200),
    num_identificacion_representante_legal VARCHAR2(20),
    clase_identificacion_rl VARCHAR2(10),
    fecha_actualizacion DATE,
    fecha_carga DATE DEFAULT SYSDATE,
    archivo_origen VARCHAR2(200),
    hash_key VARCHAR2(64),
    hash_diff VARCHAR2(64)
);

-- Tabla de log ETL
CREATE TABLE etl_log (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    job_name VARCHAR2(100) NOT NULL,
    start_time DATE NOT NULL,
    end_time DATE,
    status VARCHAR2(20) NOT NULL,
    records_processed NUMBER(10),
    error_message CLOB,
    parameters CLOB,
    created_date DATE DEFAULT SYSDATE
);

-- Crear índices
CREATE INDEX idx_personas_sta_hash ON personas_sta(hash_key);
CREATE INDEX idx_empresas_sta_hash ON empresas_sta(hash_key);
CREATE INDEX idx_etl_log_job ON etl_log(job_name);
CREATE INDEX idx_etl_log_status ON etl_log(status);
```

### 5. cleanup_duplicates.sql

**Propósito**: Script para limpiar registros duplicados en las tablas del Data Vault.

**Funcionalidades**:
- ✅ Identifica duplicados por hash_key
- ✅ Mantiene el registro más reciente
- ✅ Registra la limpieza en logs
- ✅ Optimiza performance

**Contenido**:
```sql
-- Script para limpiar duplicados en Data Vault
-- Ejecutar como sire_dv

-- Limpiar duplicados en Hub Persona
DELETE FROM hub_persona 
WHERE hub_persona_key IN (
    SELECT hub_persona_key 
    FROM (
        SELECT hub_persona_key,
               ROW_NUMBER() OVER (PARTITION BY hash_key ORDER BY load_date DESC) as rn
        FROM hub_persona
    ) 
    WHERE rn > 1
);

-- Limpiar duplicados en Hub Empresa
DELETE FROM hub_empresa 
WHERE hub_empresa_key IN (
    SELECT hub_empresa_key 
    FROM (
        SELECT hub_empresa_key,
               ROW_NUMBER() OVER (PARTITION BY hash_key ORDER BY load_date DESC) as rn
        FROM hub_empresa
    ) 
    WHERE rn > 1
);

-- Limpiar duplicados en Satellite Persona
DELETE FROM sat_persona 
WHERE (hub_persona_key, load_date) IN (
    SELECT hub_persona_key, load_date
    FROM (
        SELECT hub_persona_key, load_date,
               ROW_NUMBER() OVER (PARTITION BY hub_persona_key, hash_diff ORDER BY load_date DESC) as rn
        FROM sat_persona
    ) 
    WHERE rn > 1
);

-- Limpiar duplicados en Satellite Empresa
DELETE FROM sat_empresa 
WHERE (hub_empresa_key, load_date) IN (
    SELECT hub_empresa_key, load_date
    FROM (
        SELECT hub_empresa_key, load_date,
               ROW_NUMBER() OVER (PARTITION BY hub_empresa_key, hash_diff ORDER BY load_date DESC) as rn
        FROM sat_empresa
    ) 
    WHERE rn > 1
);

-- Limpiar duplicados en Link Persona-Empresa
DELETE FROM link_persona_empresa 
WHERE link_persona_empresa_key IN (
    SELECT link_persona_empresa_key 
    FROM (
        SELECT link_persona_empresa_key,
               ROW_NUMBER() OVER (PARTITION BY hash_key ORDER BY load_date DESC) as rn
        FROM link_persona_empresa
    ) 
    WHERE rn > 1
);

-- Registrar limpieza en log
INSERT INTO sire_audit.etl_log (job_name, start_time, end_time, status, records_processed)
VALUES ('cleanup_duplicates', SYSDATE, SYSDATE, 'SUCCESS', 
        (SELECT COUNT(*) FROM hub_persona) + 
        (SELECT COUNT(*) FROM hub_empresa) + 
        (SELECT COUNT(*) FROM sat_persona) + 
        (SELECT COUNT(*) FROM sat_empresa) + 
        (SELECT COUNT(*) FROM link_persona_empresa));

COMMIT;
```

### 6. control_ids_generados.sql

**Propósito**: Script para gestionar el control de IDs estadísticos generados.

**Funcionalidades**:
- ✅ Consulta IDs existentes
- ✅ Genera nuevos IDs
- ✅ Valida unicidad
- ✅ Reporta estadísticas

**Contenido**:
```sql
-- Script para control de IDs estadísticos
-- Ejecutar como sire_obt

-- Función para generar próximo ID estadístico
CREATE OR REPLACE FUNCTION generar_proximo_id(tipo_entidad IN VARCHAR2) 
RETURN VARCHAR2 IS
    v_consecutivo NUMBER;
    v_id_estadistico VARCHAR2(50);
BEGIN
    -- Obtener próximo consecutivo
    SELECT NVL(MAX(consecutivo), 0) + 1 
    INTO v_consecutivo
    FROM control_ids_generados 
    WHERE tipo_entidad = tipo_entidad;
    
    -- Generar ID estadístico
    v_id_estadistico := tipo_entidad || LPAD(TO_CHAR(v_consecutivo, 'FM99999999'), 8, '0');
    
    -- Insertar en control
    INSERT INTO control_ids_generados (id_estadistico, tipo_entidad, consecutivo, fecha_generacion, usuario_generacion)
    VALUES (v_id_estadistico, tipo_entidad, v_consecutivo, SYSDATE, USER);
    
    RETURN v_id_estadistico;
END;
/

-- Procedimiento para validar ID estadístico
CREATE OR REPLACE PROCEDURE validar_id_estadistico(
    p_id_estadistico IN VARCHAR2,
    p_valido OUT BOOLEAN,
    p_mensaje OUT VARCHAR2
) IS
    v_count NUMBER;
BEGIN
    -- Verificar si existe
    SELECT COUNT(*) 
    INTO v_count
    FROM control_ids_generados 
    WHERE id_estadistico = p_id_estadistico;
    
    IF v_count > 0 THEN
        p_valido := TRUE;
        p_mensaje := 'ID estadístico válido';
    ELSE
        p_valido := FALSE;
        p_mensaje := 'ID estadístico no encontrado';
    END IF;
END;
/

-- Vista para estadísticas de IDs
CREATE OR REPLACE VIEW v_estadisticas_ids AS
SELECT 
    tipo_entidad,
    COUNT(*) as total_ids,
    MIN(fecha_generacion) as primera_generacion,
    MAX(fecha_generacion) as ultima_generacion,
    COUNT(CASE WHEN estado = 'ACTIVO' THEN 1 END) as ids_activos,
    COUNT(CASE WHEN estado = 'INACTIVO' THEN 1 END) as ids_inactivos
FROM control_ids_generados
GROUP BY tipo_entidad;

-- Consulta de ejemplo
SELECT * FROM v_estadisticas_ids;
```

### 7. migrate_to_control_table.sql

**Propósito**: Script para migrar datos existentes a la tabla de control de IDs.

**Funcionalidades**:
- ✅ Migra IDs existentes
- ✅ Valida integridad
- ✅ Actualiza referencias
- ✅ Genera reportes

**Contenido**:
```sql
-- Script para migrar datos a tabla de control
-- Ejecutar como sire_obt

-- Crear tabla temporal para IDs existentes
CREATE GLOBAL TEMPORARY TABLE temp_ids_existentes (
    id_estadistico VARCHAR2(50),
    tipo_entidad VARCHAR2(2),
    consecutivo NUMBER(10),
    fecha_generacion DATE,
    fuente VARCHAR2(100)
) ON COMMIT DELETE ROWS;

-- Insertar IDs de personas existentes
INSERT INTO temp_ids_existentes (id_estadistico, tipo_entidad, consecutivo, fecha_generacion, fuente)
SELECT 
    id_estadistico,
    '01' as tipo_entidad,
    TO_NUMBER(SUBSTR(id_estadistico, 3)) as consecutivo,
    fecha_obtencion as fecha_generacion,
    'MIGRACION_PERSONAS' as fuente
FROM personas_obt
WHERE id_estadistico IS NOT NULL;

-- Insertar IDs de empresas existentes
INSERT INTO temp_ids_existentes (id_estadistico, tipo_entidad, consecutivo, fecha_generacion, fuente)
SELECT 
    id_estadistico,
    '02' as tipo_entidad,
    TO_NUMBER(SUBSTR(id_estadistico, 3)) as consecutivo,
    fecha_obtencion as fecha_generacion,
    'MIGRACION_EMPRESAS' as fuente
FROM empresas_obt
WHERE id_estadistico IS NOT NULL;

-- Migrar a tabla de control
INSERT INTO control_ids_generados (id_estadistico, tipo_entidad, consecutivo, fecha_generacion, usuario_generacion, observaciones)
SELECT 
    id_estadistico,
    tipo_entidad,
    consecutivo,
    fecha_generacion,
    'MIGRACION' as usuario_generacion,
    fuente as observaciones
FROM temp_ids_existentes
WHERE id_estadistico NOT IN (SELECT id_estadistico FROM control_ids_generados);

-- Validar migración
SELECT 
    tipo_entidad,
    COUNT(*) as ids_migrados,
    MIN(fecha_generacion) as fecha_minima,
    MAX(fecha_generacion) as fecha_maxima
FROM control_ids_generados
WHERE usuario_generacion = 'MIGRACION'
GROUP BY tipo_entidad;

-- Limpiar tabla temporal
DELETE FROM temp_ids_existentes;

COMMIT;
```

### 8. check_and_create_structure.sql

**Propósito**: Script para verificar y crear la estructura completa de la base de datos.

**Funcionalidades**:
- ✅ Verifica esquemas existentes
- ✅ Crea esquemas faltantes
- ✅ Verifica tablas existentes
- ✅ Crea tablas faltantes
- ✅ Genera reporte de estado

**Contenido**:
```sql
-- Script para verificar y crear estructura completa
-- Ejecutar como SYSTEM o DBA

-- Verificar esquemas existentes
SELECT username FROM dba_users WHERE username IN ('SIRE_STA', 'SIRE_OBT', 'SIRE_DV', 'SIRE_AUDIT');

-- Crear esquemas si no existen
BEGIN
    -- Crear sire_sta
    BEGIN
        EXECUTE IMMEDIATE 'CREATE USER sire_sta IDENTIFIED BY sire_sta_password';
        EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO sire_sta';
        EXECUTE IMMEDIATE 'GRANT CREATE TABLE TO sire_sta';
        EXECUTE IMMEDIATE 'GRANT CREATE SEQUENCE TO sire_sta';
        EXECUTE IMMEDIATE 'GRANT CREATE INDEX TO sire_sta';
        DBMS_OUTPUT.PUT_LINE('Esquema sire_sta creado exitosamente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('Esquema sire_sta ya existe o error: ' || SQLERRM);
    END;
    
    -- Crear sire_obt
    BEGIN
        EXECUTE IMMEDIATE 'CREATE USER sire_obt IDENTIFIED BY sire_obt_password';
        EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO sire_obt';
        EXECUTE IMMEDIATE 'GRANT CREATE TABLE TO sire_obt';
        EXECUTE IMMEDIATE 'GRANT CREATE SEQUENCE TO sire_obt';
        EXECUTE IMMEDIATE 'GRANT CREATE INDEX TO sire_obt';
        DBMS_OUTPUT.PUT_LINE('Esquema sire_obt creado exitosamente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('Esquema sire_obt ya existe o error: ' || SQLERRM);
    END;
    
    -- Crear sire_dv
    BEGIN
        EXECUTE IMMEDIATE 'CREATE USER sire_dv IDENTIFIED BY sire_dv_password';
        EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO sire_dv';
        EXECUTE IMMEDIATE 'GRANT CREATE TABLE TO sire_dv';
        EXECUTE IMMEDIATE 'GRANT CREATE SEQUENCE TO sire_dv';
        EXECUTE IMMEDIATE 'GRANT CREATE INDEX TO sire_dv';
        DBMS_OUTPUT.PUT_LINE('Esquema sire_dv creado exitosamente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('Esquema sire_dv ya existe o error: ' || SQLERRM);
    END;
    
    -- Crear sire_audit
    BEGIN
        EXECUTE IMMEDIATE 'CREATE USER sire_audit IDENTIFIED BY sire_audit_password';
        EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO sire_audit';
        EXECUTE IMMEDIATE 'GRANT CREATE TABLE TO sire_audit';
        EXECUTE IMMEDIATE 'GRANT CREATE SEQUENCE TO sire_audit';
        EXECUTE IMMEDIATE 'GRANT CREATE INDEX TO sire_audit';
        DBMS_OUTPUT.PUT_LINE('Esquema sire_audit creado exitosamente');
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('Esquema sire_audit ya existe o error: ' || SQLERRM);
    END;
END;
/

-- Verificar tablas existentes
SELECT 
    owner,
    table_name,
    num_rows
FROM dba_tables 
WHERE owner IN ('SIRE_STA', 'SIRE_OBT', 'SIRE_DV', 'SIRE_AUDIT')
ORDER BY owner, table_name;

-- Generar reporte de estado
SELECT 
    'ESQUEMAS' as tipo,
    username as nombre,
    created as fecha_creacion,
    account_status as estado
FROM dba_users 
WHERE username IN ('SIRE_STA', 'SIRE_OBT', 'SIRE_DV', 'SIRE_AUDIT')

UNION ALL

SELECT 
    'TABLAS' as tipo,
    owner || '.' || table_name as nombre,
    created as fecha_creacion,
    'ACTIVO' as estado
FROM dba_tables 
WHERE owner IN ('SIRE_STA', 'SIRE_OBT', 'SIRE_DV', 'SIRE_AUDIT')
ORDER BY tipo, nombre;
```

### 9. create_user_docker_oracle.sql

**Propósito**: Script para crear usuarios específicos para el ambiente Docker de Oracle.

**Funcionalidades**:
- ✅ Crea usuarios para Docker
- ✅ Configura permisos específicos
- ✅ Optimiza para contenedores
- ✅ Configura conexiones

**Contenido**:
```sql
-- Script para crear usuarios en Docker Oracle
-- Ejecutar como SYSTEM

-- Crear usuario para Airflow
CREATE USER airflow IDENTIFIED BY airflow;
GRANT CONNECT, RESOURCE TO airflow;
GRANT CREATE TABLE TO airflow;
GRANT CREATE SEQUENCE TO airflow;
GRANT CREATE INDEX TO airflow;

-- Crear usuario para FastAPI
CREATE USER sire_fastapi IDENTIFIED BY sire_fastapi_password;
GRANT CONNECT, RESOURCE TO sire_fastapi;
GRANT CREATE TABLE TO sire_fastapi;
GRANT CREATE SEQUENCE TO sire_fastapi;
GRANT CREATE INDEX TO sire_fastapi;

-- Otorgar permisos entre esquemas
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_sta.personas_sta TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_sta.empresas_sta TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_obt.personas_obt TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_obt.empresas_obt TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_obt.control_ids_generados TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.hub_persona TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.hub_empresa TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.sat_persona TO sire_fastapi;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.sat_empresa TO sire_fastapi;

-- Configurar conexiones para Airflow
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_sta.personas_sta TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_sta.empresas_sta TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_obt.personas_obt TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_obt.empresas_obt TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.hub_persona TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.hub_empresa TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.sat_persona TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.sat_empresa TO airflow;
GRANT SELECT, INSERT, UPDATE, DELETE ON sire_dv.link_persona_empresa TO airflow;

-- Crear sinónimos para facilitar acceso
CREATE SYNONYM sire_fastapi.personas_sta FOR sire_sta.personas_sta;
CREATE SYNONYM sire_fastapi.empresas_sta FOR sire_sta.empresas_sta;
CREATE SYNONYM sire_fastapi.personas_obt FOR sire_obt.personas_obt;
CREATE SYNONYM sire_fastapi.empresas_obt FOR sire_obt.empresas_obt;
CREATE SYNONYM sire_fastapi.control_ids_generados FOR sire_obt.control_ids_generados;
CREATE SYNONYM sire_fastapi.hub_persona FOR sire_dv.hub_persona;
CREATE SYNONYM sire_fastapi.hub_empresa FOR sire_dv.hub_empresa;
CREATE SYNONYM sire_fastapi.sat_persona FOR sire_dv.sat_persona;
CREATE SYNONYM sire_fastapi.sat_empresa FOR sire_dv.sat_empresa;

-- Configurar parámetros de sesión
ALTER SYSTEM SET processes=300 SCOPE=SPFILE;
ALTER SYSTEM SET sessions=335 SCOPE=SPFILE;
ALTER SYSTEM SET transactions=400 SCOPE=SPFILE;

-- Reiniciar instancia para aplicar cambios
-- SHUTDOWN IMMEDIATE;
-- STARTUP;
```

### 10. init_minimal.sql

**Propósito**: Script mínimo para inicializar la base de datos con lo esencial.

**Funcionalidades**:
- ✅ Crea estructura básica
- ✅ Configura permisos mínimos
- ✅ Inicializa tablas esenciales
- ✅ Optimiza para inicio rápido

**Contenido**:
```sql
-- Script mínimo para inicializar SIRE
-- Ejecutar como SYSTEM

-- Crear esquemas básicos
CREATE USER sire_sta IDENTIFIED BY sire_sta_password;
CREATE USER sire_obt IDENTIFIED BY sire_obt_password;
CREATE USER sire_dv IDENTIFIED BY sire_dv_password;

-- Permisos básicos
GRANT CONNECT, RESOURCE TO sire_sta;
GRANT CONNECT, RESOURCE TO sire_obt;
GRANT CONNECT, RESOURCE TO sire_dv;

-- Crear tablas esenciales
CONNECT sire_obt/sire_obt_password;

CREATE TABLE control_ids_generados (
    id_estadistico VARCHAR2(50) PRIMARY KEY,
    tipo_entidad VARCHAR2(2) NOT NULL,
    consecutivo NUMBER(10) NOT NULL,
    fecha_generacion DATE DEFAULT SYSDATE,
    usuario_generacion VARCHAR2(100),
    estado VARCHAR2(20) DEFAULT 'ACTIVO'
);

-- Insertar datos iniciales
INSERT INTO control_ids_generados (id_estadistico, tipo_entidad, consecutivo, usuario_generacion)
VALUES ('0100000000', '01', 0, 'INICIALIZACION');

INSERT INTO control_ids_generados (id_estadistico, tipo_entidad, consecutivo, usuario_generacion)
VALUES ('0200000000', '02', 0, 'INICIALIZACION');

COMMIT;

-- Verificar inicialización
SELECT 'INICIALIZACION COMPLETA' as estado, COUNT(*) as registros FROM control_ids_generados;
```

## Scripts de PostgreSQL

### 1. create_schemas.sql

**Propósito**: Crea los esquemas necesarios para PostgreSQL.

**Contenido**:
```sql
-- Crear esquemas para SIRE en PostgreSQL
CREATE SCHEMA IF NOT EXISTS sire_sta;
CREATE SCHEMA IF NOT EXISTS sire_obt;
CREATE SCHEMA IF NOT EXISTS sire_dv;
CREATE SCHEMA IF NOT EXISTS sire_audit;

-- Crear usuarios
CREATE USER sire_sta_user WITH PASSWORD 'sire_sta_password';
CREATE USER sire_obt_user WITH PASSWORD 'sire_obt_password';
CREATE USER sire_dv_user WITH PASSWORD 'sire_dv_password';
CREATE USER sire_audit_user WITH PASSWORD 'sire_audit_password';

-- Otorgar permisos
GRANT USAGE ON SCHEMA sire_sta TO sire_sta_user;
GRANT USAGE ON SCHEMA sire_obt TO sire_obt_user;
GRANT USAGE ON SCHEMA sire_dv TO sire_dv_user;
GRANT USAGE ON SCHEMA sire_audit TO sire_audit_user;

GRANT CREATE ON SCHEMA sire_sta TO sire_sta_user;
GRANT CREATE ON SCHEMA sire_obt TO sire_obt_user;
GRANT CREATE ON SCHEMA sire_dv TO sire_dv_user;
GRANT CREATE ON SCHEMA sire_audit TO sire_audit_user;
```

### 2. sire_dv_tables.sql

**Propósito**: Crea las tablas del Data Vault para PostgreSQL.

**Contenido**:
```sql
-- Crear tablas Data Vault en PostgreSQL
-- Ejecutar como sire_dv_user

-- Tabla Hub Persona
CREATE TABLE sire_dv.hub_persona (
    hub_persona_key VARCHAR(50) PRIMARY KEY,
    tipo_documento VARCHAR(10) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    hash_key VARCHAR(64) NOT NULL,
    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(100) DEFAULT 'SIRE_ETL'
);

-- Tabla Hub Empresa
CREATE TABLE sire_dv.hub_empresa (
    hub_empresa_key VARCHAR(50) PRIMARY KEY,
    tipo_documento VARCHAR(10) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    hash_key VARCHAR(64) NOT NULL,
    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(100) DEFAULT 'SIRE_ETL'
);

-- Tabla Satellite Persona
CREATE TABLE sire_dv.sat_persona (
    hub_persona_key VARCHAR(50) NOT NULL,
    primer_nombre VARCHAR(100),
    segundo_nombre VARCHAR(100),
    primer_apellido VARCHAR(100),
    segundo_apellido VARCHAR(100),
    fecha_nacimiento DATE,
    sexo_an CHAR(1),
    codigo_municipio_nacimiento VARCHAR(10),
    codigo_pais_nacimiento VARCHAR(10),
    fecha_defuncion DATE,
    hash_diff VARCHAR(64) NOT NULL,
    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(100) DEFAULT 'SIRE_ETL',
    PRIMARY KEY (hub_persona_key, load_date),
    FOREIGN KEY (hub_persona_key) REFERENCES sire_dv.hub_persona(hub_persona_key)
);

-- Crear índices
CREATE INDEX idx_hub_persona_hash ON sire_dv.hub_persona(hash_key);
CREATE INDEX idx_hub_empresa_hash ON sire_dv.hub_empresa(hash_key);
CREATE INDEX idx_sat_persona_hash ON sire_dv.sat_persona(hash_diff);
```

## Mejores Prácticas

### 1. Seguridad
- Usar contraseñas seguras
- Otorgar permisos mínimos necesarios
- Implementar auditoría
- Validar entrada de datos

### 2. Performance
- Crear índices apropiados
- Optimizar consultas
- Usar particionamiento cuando sea necesario
- Monitorear performance

### 3. Mantenimiento
- Documentar scripts
- Versionar cambios
- Implementar rollback
- Monitorear logs

### 4. Escalabilidad
- Diseñar para crecimiento
- Implementar particionamiento
- Optimizar recursos
- Planificar capacidad

## Ejemplos de Uso

### Ejecutar Scripts de Oracle

```bash
# Conectar a Oracle y ejecutar script
sqlplus system/oracle123@localhost:1521/XE @scripts_sql/oracle/create_schemas.sql

# Ejecutar desde Docker
docker exec -i sire-oracle sqlplus system/oracle123@localhost:1521/XE @/docker-entrypoint-initdb.d/create_schemas.sql
```

### Ejecutar Scripts de PostgreSQL

```bash
# Conectar a PostgreSQL y ejecutar script
psql -h localhost -p 5433 -U sire_user -d sire_dw -f scripts_sql/postgres/create_schemas.sql

# Ejecutar desde Docker
docker exec -i sire-postgres-dw psql -U sire_user -d sire_dw -f /docker-entrypoint-initdb.d/create_schemas.sql
```

### Verificar Estructura

```sql
-- Verificar esquemas creados
SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'sire_%';

-- Verificar tablas creadas
SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema LIKE 'sire_%' ORDER BY table_schema, table_name;

-- Verificar permisos
SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_schema LIKE 'sire_%';
```
