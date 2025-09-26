# Configuración de Base de Datos - SIRE

## Visión General

El sistema SIRE soporta múltiples bases de datos para diferentes propósitos y ambientes. La configuración se maneja a través de variables de entorno y archivos de configuración específicos para cada ambiente.

## Arquitectura de Base de Datos

```mermaid
graph TB
    subgraph "Ambiente de Desarrollo"
        A[PostgreSQL Airflow<br/>Puerto: 5432]
        B[PostgreSQL Data Warehouse<br/>Puerto: 5433]
    end
    
    subgraph "Ambiente de Producción"
        C[PostgreSQL Airflow<br/>Puerto: 5432]
        D[Oracle Data Warehouse<br/>Puerto: 1521]
    end
    
    subgraph "Esquemas"
        E[sire_sta<br/>Staging]
        F[sire_obt<br/>Datos Sensibles]
        G[sire_dv<br/>Data Vault]
    end
    
    A --> E
    B --> E
    B --> F
    B --> G
    C --> E
    D --> E
    D --> F
    D --> G
```

## Configuración por Ambiente

### Desarrollo (PostgreSQL)

#### Variables de Entorno
```bash
# config/dev.postgresql.env
DATABASE_TYPE=postgresql
ENVIRONMENT=dev

# PostgreSQL Data Warehouse
DEV_POSTGRES_JDBC_URL=jdbc:postgresql://sire-postgres-dw:5432/sire_dw
DEV_POSTGRES_JDBC_USER=sire_user
DEV_POSTGRES_JDBC_PASSWORD=sire_password
DEV_POSTGRES_CONNECTION_STRING=postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw

# PostgreSQL Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@sire-postgres:5432/airflow
```

#### Docker Compose
```yaml
# docker-compose.postgresql.yml
services:
  sire-postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"

  sire-postgres-dw:
    image: postgres:13
    environment:
      POSTGRES_USER: sire_user
      POSTGRES_PASSWORD: sire_password
      POSTGRES_DB: sire_dw
    ports:
      - "5433:5432"
```

### Producción (Oracle)

#### Variables de Entorno
```bash
# config/prod.oracle.env
DATABASE_TYPE=oracle
ENVIRONMENT=prod

# Oracle Data Warehouse
PROD_ORACLE_JDBC_URL=jdbc:oracle:thin:@oracle-server:1521/XEPDB1
PROD_ORACLE_JDBC_USER=SIRE_STG
PROD_ORACLE_JDBC_PASSWORD=sire_password
PROD_ORACLE_CONNECTION_STRING=oracle://SIRE_STG:sire_password@oracle-server:1521/XEPDB1
```

Notas:
- En desarrollo con Oracle local (XE), usar `docker-compose.oracle.yml` y `config/dev.oracle.env`.
- La API selecciona el backend leyendo `DATABASE_TYPE` y `ENVIRONMENT` en `src/config/db_config.py`.

## Esquemas de Base de Datos

### 1. Staging (sire_sta)

**Propósito**: Almacenar datos raw sin procesar.

#### Tablas Principales
```sql
-- Datos raw de BDUA
CREATE TABLE sire_sta.raw_bdua (
    id_estadistico_persona VARCHAR(300),
    tipo_identificacion VARCHAR(50),
    numero_identificacion VARCHAR(50),
    primer_nombre VARCHAR(100),
    segundo_nombre VARCHAR(100),
    primer_apellido VARCHAR(100),
    segundo_apellido VARCHAR(100),
    fecha_nacimiento DATE,
    sexo VARCHAR(10),
    cod_municipio VARCHAR(5),
    -- ... otros campos
    load_date TIMESTAMP,
    file_name VARCHAR(255),
    persona_hash VARCHAR(40)
);

-- Datos raw de RUES
CREATE TABLE sire_sta.raw_rues (
    id_estadistico_empresa VARCHAR(300),
    razon_social VARCHAR(500),
    nit VARCHAR(20),
    numero_identificacion VARCHAR(50),
    matricula VARCHAR(50),
    -- ... otros campos
    load_date TIMESTAMP,
    md5_hash VARCHAR(40)
);

-- Log de archivos procesados
CREATE TABLE sire_sta.raw_log_etl (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(255),
    hash_archivo VARCHAR(40) UNIQUE,
    fecha_carga TIMESTAMP,
    registros_procesados INTEGER
);
```

### 2. OBT - Datos Sensibles (sire_obt)

**Propósito**: Almacenar datos con información sensible para acceso controlado.

#### Tablas Principales
```sql
-- Personas con datos sensibles
CREATE TABLE sire_obt.raw_obt_personas (
    id_estadistico VARCHAR(300) PRIMARY KEY,
    tipo_documento VARCHAR(50),
    numero_documento VARCHAR(50),
    primer_nombre VARCHAR(100),
    segundo_nombre VARCHAR(100),
    primer_apellido VARCHAR(100),
    segundo_apellido VARCHAR(100),
    fecha_nacimiento DATE,
    sexo_an VARCHAR(10),
    codigo_municipio_nacimiento VARCHAR(5),
    load_datetime TIMESTAMP,
    id_log_etl INTEGER
);

-- Empresas con datos sensibles
CREATE TABLE sire_obt.raw_obt_empresas (
    id_estadistico VARCHAR(300) PRIMARY KEY,
    razon_social VARCHAR(500),
    nit VARCHAR(20),
    digito_verificacion VARCHAR(10),
    -- ... otros campos
    load_datetime TIMESTAMP,
    id_log_etl INTEGER
);
```

### 3. Data Vault (sire_dv)

**Propósito**: Almacenar datos pseudonimizados siguiendo la metodología Data Vault 2.0.

#### Hubs
```sql
-- Hub de Personas
CREATE TABLE sire_dv.hub_persona (
    id SERIAL PRIMARY KEY,
    id_estadistico VARCHAR(300) UNIQUE,
    load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro INTEGER,
    id_log_etl INTEGER,
    md5_hash VARCHAR(40) UNIQUE
);

-- Hub de Empresas
CREATE TABLE sire_dv.hub_empresa (
    id SERIAL PRIMARY KEY,
    id_estadistico VARCHAR(300) UNIQUE,
    load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro INTEGER,
    id_log_etl INTEGER,
    md5_hash VARCHAR(40) UNIQUE
);
```

#### Satellites
```sql
-- Satélite de Personas (PSEUDONIMIZADO)
CREATE TABLE sire_dv.sat_persona (
    id SERIAL PRIMARY KEY,
    id_estadistico VARCHAR(300) REFERENCES hub_persona(id_estadistico),
    fecha_nacimiento DATE,
    sexo VARCHAR(50),
    codigo_municipio_nacimiento VARCHAR(5),
    codigo_pais_nacimiento VARCHAR(3),
    fecha_defuncion DATE,
    estado_civil VARCHAR(50),
    etnia VARCHAR(90),
    discapacidad VARCHAR(50),
    tipo_poblacion_especial VARCHAR(100),
    nombre_resguardo VARCHAR(100),
    md5_hash VARCHAR(40) UNIQUE,
    load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro INTEGER,
    id_log_etl INTEGER
);

-- Satélite de Empresas (PSEUDONIMIZADO)
CREATE TABLE sire_dv.sat_empresa (
    id SERIAL PRIMARY KEY,
    id_estadistico_empresa VARCHAR(300) REFERENCES hub_empresa(id_estadistico),
    codigo_camara VARCHAR(250),
    camara_comercio VARCHAR(250),
    matricula VARCHAR(250),
    inscripcion_proponente VARCHAR(250),
    sigla VARCHAR(250),
    fecha_matricula DATE,
    fecha_renovacion DATE,
    ultimo_anio_renovado INTEGER,
    fecha_vigencia DATE,
    fecha_cancelacion DATE,
    codigo_tipo_sociedad VARCHAR(250),
    tipo_sociedad VARCHAR(250),
    codigo_organizacion_juridica VARCHAR(250),
    organizacion_juridica VARCHAR(250),
    codigo_categoria_matricula VARCHAR(250),
    categoria_matricula VARCHAR(250),
    codigo_estado_matricula VARCHAR(250),
    estado_matricula VARCHAR(250),
    fecha_actualizacion TIMESTAMP,
    codigo_clase_identificacion VARCHAR(250),
    digito_verificacion VARCHAR(250),
    estatus VARCHAR(50),
    md5_hash VARCHAR(40) UNIQUE,
    load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro INTEGER,
    id_log_etl INTEGER
);
```

#### Links
```sql
-- Link de Afiliación
CREATE TABLE sire_dv.link_afiliacion (
    id SERIAL PRIMARY KEY,
    id_hub_persona_afiliada VARCHAR(300) REFERENCES hub_persona(id_estadistico),
    id_hub_persona_cotizante VARCHAR(300) REFERENCES hub_persona(id_estadistico),
    id_hub_aportante_emp VARCHAR(300) REFERENCES hub_empresa(id_estadistico),
    id_cod_departamento INTEGER,
    id_cod_municipio INTEGER,
    id_zona INTEGER,
    tipo_cotizante VARCHAR(50),
    tipo_afiliado VARCHAR(50),
    parentesco VARCHAR(70),
    ips_primaria VARCHAR(100),
    fecha_afiliacion DATE,
    regimen VARCHAR(30),
    estado_afiliacion VARCHAR(30),
    md5_hash VARCHAR(40) UNIQUE,
    load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro INTEGER,
    id_log_etl INTEGER
);
```

#### Logs ETL
```sql
-- Log de operaciones ETL
CREATE TABLE sire_dv.log_etl (
    id SERIAL PRIMARY KEY,
    job_uuid VARCHAR(100) UNIQUE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    estado VARCHAR(20) CHECK (estado IN ('SUCCESS', 'FAILURE', 'RUNNING')),
    registros_cargados INTEGER,
    tabla_destino VARCHAR(255),
    mensaje_error TEXT,
    nombre_etl VARCHAR(255),
    descripcion_etl VARCHAR(255),
    tiempo_ejecucion_segundos NUMERIC,
    nombre_archivo VARCHAR(255),
    hash_archivo VARCHAR(255) UNIQUE
);
```

## Configuración de Conexiones

### Python (SQLAlchemy)
```python
# src/config/db_config.py
class DbConfig:
    def __init__(self):
        db_type = os.getenv("DATABASE_TYPE", "postgresql").lower()
        
        if db_type == "postgresql":
            self.connection_string = "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw"
        elif db_type == "oracle":
            self.connection_string = "oracle://SIRE_STG:sire_password@oracle-db:1521/XEPDB1"
```

### PySpark
```python
# Parámetros JDBC para PySpark
jdbc_params = {
    "url": "jdbc:postgresql://sire-postgres-dw:5432/sire_dw",
    "user": "sire_user",
    "password": "sire_password",
    "driver": "org.postgresql.Driver"
}
```

### Airflow
```python
# Configuración de conexión en Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@sire-postgres:5432/airflow
```

## Scripts de Inicialización

### PostgreSQL
```sql
-- scripts_sql/postgres/create_schemas.sql
CREATE SCHEMA IF NOT EXISTS sire_sta;
CREATE SCHEMA IF NOT EXISTS sire_obt;
CREATE SCHEMA IF NOT EXISTS sire_dv;

-- Otorgar permisos
GRANT ALL PRIVILEGES ON SCHEMA sire_sta TO sire_user;
GRANT ALL PRIVILEGES ON SCHEMA sire_obt TO sire_user;
GRANT ALL PRIVILEGES ON SCHEMA sire_dv TO sire_user;
```

### Oracle
```sql
-- scripts_sql/oracle/create_schemas.sql
CREATE USER SIRE_STA IDENTIFIED BY sire_password;
CREATE USER SIRE_OBT IDENTIFIED BY sire_password;
CREATE USER SIRE_DV IDENTIFIED BY sire_password;

-- Otorgar permisos
GRANT CONNECT, RESOURCE TO SIRE_STA;
GRANT CONNECT, RESOURCE TO SIRE_OBT;
GRANT CONNECT, RESOURCE TO SIRE_DV;
```

## Optimización de Performance

### Índices Recomendados
```sql
-- Índices para búsquedas frecuentes
CREATE INDEX idx_hub_persona_id_estadistico ON sire_dv.hub_persona(id_estadistico);
CREATE INDEX idx_hub_empresa_id_estadistico ON sire_dv.hub_empresa(id_estadistico);
CREATE INDEX idx_sat_persona_id_estadistico ON sire_dv.sat_persona(id_estadistico);
CREATE INDEX idx_sat_empresa_id_estadistico ON sire_dv.sat_empresa(id_estadistico);

-- Índices para auditoría
CREATE INDEX idx_log_etl_job_uuid ON sire_dv.log_etl(job_uuid);
CREATE INDEX idx_log_etl_start_time ON sire_dv.log_etl(start_time);
```

### Particionamiento
```sql
-- Particionamiento por fecha (PostgreSQL)
CREATE TABLE sire_dv.sat_persona_partitioned (
    LIKE sire_dv.sat_persona INCLUDING ALL
) PARTITION BY RANGE (load_datetime);

-- Crear particiones mensuales
CREATE TABLE sat_persona_2024_01 PARTITION OF sire_dv.sat_persona_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Monitoreo y Mantenimiento

### Consultas de Monitoreo
```sql
-- Verificar estado de logs ETL
SELECT 
    nombre_etl,
    estado,
    COUNT(*) as total_ejecuciones,
    AVG(tiempo_ejecucion_segundos) as tiempo_promedio
FROM sire_dv.log_etl 
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY nombre_etl, estado;

-- Verificar volumen de datos
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname IN ('sire_sta', 'sire_obt', 'sire_dv')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Limpieza de Datos
```sql
-- Limpiar logs antiguos (mantener últimos 90 días)
DELETE FROM sire_dv.log_etl 
WHERE start_time < CURRENT_DATE - INTERVAL '90 days';

-- Limpiar datos de staging antiguos
DELETE FROM sire_sta.raw_bdua 
WHERE load_date < CURRENT_DATE - INTERVAL '30 days';
```

## Backup y Recuperación

### Backup Automático
```bash
#!/bin/bash
# backup_sire.sh

# Backup de esquemas específicos
pg_dump -h sire-postgres-dw -U sire_user -n sire_dv sire_dw > sire_dv_backup_$(date +%Y%m%d).sql
pg_dump -h sire-postgres-dw -U sire_user -n sire_obt sire_dw > sire_obt_backup_$(date +%Y%m%d).sql
pg_dump -h sire-postgres-dw -U sire_user -n sire_sta sire_dw > sire_sta_backup_$(date +%Y%m%d).sql
```

### Restauración
```bash
# Restaurar esquema específico
psql -h sire-postgres-dw -U sire_user -d sire_dw < sire_dv_backup_20240101.sql
```

## Consideraciones de Seguridad

### Control de Acceso
- **sire_sta**: Acceso de lectura para procesos ETL
- **sire_obt**: Acceso restringido solo para personal autorizado
- **sire_dv**: Acceso de lectura para análisis y reportes

### Encriptación
- Datos en tránsito: SSL/TLS
- Datos en reposo: Encriptación a nivel de base de datos
- Backups: Encriptación de archivos de respaldo

### Auditoría
- Logs de acceso a datos sensibles
- Registro de modificaciones en esquemas críticos
- Monitoreo de accesos no autorizados
