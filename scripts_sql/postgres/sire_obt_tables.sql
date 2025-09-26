-- Tablas OBT para PostgreSQL (equivalente a Oracle)
-- Esquema: sire_sta

-- Tabla de log ETL
CREATE TABLE IF NOT EXISTS sire_sta.raw_log_etl (
    id                        BIGSERIAL PRIMARY KEY,
    job_uuid                  VARCHAR(100) UNIQUE,
    start_time                TIMESTAMP,
    end_time                  TIMESTAMP,
    estado                    VARCHAR(20) CHECK (estado IN ('SUCCESS', 'FAILURE')),
    registros_cargados        INTEGER,
    tabla_destino             VARCHAR(255),
    mensaje_error             TEXT,
    nombre_etl                VARCHAR(255),
    descripcion_etl           VARCHAR(255),
    tiempo_ejecucion_segundos INTEGER,
    nombre_archivo            VARCHAR(255),
    hash_archivo              VARCHAR(255) UNIQUE,
    usuario_ldap              VARCHAR(20)
);

-- Tabla OBT Personas (ID estadístico 01+Consecutivo)
CREATE TABLE IF NOT EXISTS sire_sta.raw_obt_personas (
    id                        BIGSERIAL PRIMARY KEY,
    id_estadistico            VARCHAR(100),
    tipo_documento            VARCHAR(50),
    numero_documento          VARCHAR(50),
    primer_nombre             VARCHAR(100),
    segundo_nombre            VARCHAR(100),
    primer_apellido           VARCHAR(100),
    segundo_apellido          VARCHAR(100),
    fecha_nacimiento          DATE,
    sexo_an                   VARCHAR(50),
    codigo_municipio_nacimiento VARCHAR(50), -- divipola
    codigo_pais_nacimiento    VARCHAR(3), -- m49
    fecha_defuncion           DATE,
    load_datetime             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_log_etl                BIGINT REFERENCES sire_sta.raw_log_etl(id)
);

-- Tabla OBT Empresas (ID estadístico 02+Consecutivo)
-- ID estadístico 01+Consecutivo solo cuando empresa tiene tipo documento CC
CREATE TABLE IF NOT EXISTS sire_sta.raw_obt_empresas (
    id                        BIGSERIAL PRIMARY KEY,
    id_estadistico            VARCHAR(100),
    razon_social              VARCHAR(255),
    nit                       VARCHAR(50),
    digito_verificacion       VARCHAR(5),
    codigo_camara             VARCHAR(50),
    camara_comercio           VARCHAR(100),
    matricula                 VARCHAR(100),
    fecha_matricula           DATE,
    fecha_renovacion          DATE,
    ultimo_ano_renovado       INTEGER,
    fecha_vigencia            DATE,
    fecha_cancelacion         DATE,
    codigo_tipo_sociedad      VARCHAR(50),
    tipo_sociedad             VARCHAR(100),
    codigo_organizacion_juridica VARCHAR(50),
    organizacion_juridica     VARCHAR(100),
    codigo_estado_matricula   VARCHAR(50),
    estado_matricula          VARCHAR(100),
    representante_legal       VARCHAR(255),
    num_identificacion_representante_legal VARCHAR(100),
    clase_identificacion_rl   VARCHAR(50),
    fecha_actualizacion       DATE,
    load_datetime             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_log_etl                BIGINT REFERENCES sire_sta.raw_log_etl(id)
);
