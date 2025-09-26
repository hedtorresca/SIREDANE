-- Tablas Data Vault para PostgreSQL
-- Esquemas: sire_dv, sire_sta, catalogo, raw

-- Tabla de log ETL
CREATE TABLE IF NOT EXISTS sire_dv.log_etl (
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
    hash_archivo              VARCHAR(255) UNIQUE
);

-- Catálogo de fuentes de registro
CREATE TABLE IF NOT EXISTS catalogo.fuente_registro (
    id                      BIGSERIAL PRIMARY KEY,
    id_fuente               VARCHAR(4),
    nombre_fuente           VARCHAR(15),
    periodicidad_fuente     VARCHAR(20) CHECK (periodicidad_fuente IN ('Mensual', 'Anual', 'Trimestral', 'Semanal', 'Diario', 'Otro')),
    vigencia_fuente         VARCHAR(20),
    descripcion             VARCHAR(250),
    sistema_origen          VARCHAR(100),
    tipo_fuente             VARCHAR(50),
    fecha_creacion          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_carga           VARCHAR(50),
    estado                  VARCHAR(20) DEFAULT 'ACTIVO'
);

-- Hub Persona
CREATE TABLE IF NOT EXISTS sire_dv.hub_persona (
    id                     BIGSERIAL PRIMARY KEY,
    id_estadistico         VARCHAR(300) UNIQUE,
    load_datetime          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro     BIGINT REFERENCES catalogo.fuente_registro(id),
    id_log_etl             BIGINT REFERENCES sire_dv.log_etl(id),
    md5_hash               VARCHAR(40) UNIQUE
);

-- Satélite Persona (PSEUDONIMIZADO - Sin campos sensibles de OBT)
CREATE TABLE IF NOT EXISTS sire_dv.sat_persona (
    id                        BIGSERIAL PRIMARY KEY,
    id_estadistico            VARCHAR(300) REFERENCES sire_dv.hub_persona(id_estadistico),
    fecha_nacimiento          DATE,
    sexo                      VARCHAR(50),
    codigo_municipio_nacimiento VARCHAR(5),
    codigo_pais_nacimiento    VARCHAR(3),
    fecha_defuncion           DATE,
    estado_civil              VARCHAR(50),
    etnia                     VARCHAR(90),
    discapacidad              VARCHAR(50),
    tipo_poblacion_especial   VARCHAR(100),
    nombre_resguardo          VARCHAR(100),
    md5_hash                  VARCHAR(40) UNIQUE,
    load_datetime             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro        BIGINT REFERENCES catalogo.fuente_registro(id),
    id_log_etl                BIGINT REFERENCES sire_dv.log_etl(id)
);

-- Hub Empresa
CREATE TABLE IF NOT EXISTS sire_dv.hub_empresa (
    id                     BIGSERIAL PRIMARY KEY,
    id_estadistico         VARCHAR(300) UNIQUE,
    load_datetime          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro     BIGINT REFERENCES catalogo.fuente_registro(id),
    id_log_etl             BIGINT REFERENCES sire_dv.log_etl(id),
    md5_hash               VARCHAR(40) UNIQUE
);

-- Satélite Empresa (PSEUDONIMIZADO - Sin campos sensibles de OBT)
CREATE TABLE IF NOT EXISTS sire_dv.sat_empresa (
    id                                     BIGSERIAL PRIMARY KEY,
    id_estadistico_empresa                 VARCHAR(300) REFERENCES sire_dv.hub_empresa(id_estadistico),
    codigo_camara                          VARCHAR(250),
    camara_comercio                        VARCHAR(250),
    matricula                              VARCHAR(250),
    inscripcion_proponente                 VARCHAR(250),
    sigla                                  VARCHAR(250),
    fecha_matricula                        DATE,
    fecha_renovacion                       DATE,
    ultimo_anio_renovado                   INTEGER,
    fecha_vigencia                         DATE,
    fecha_cancelacion                      DATE,
    codigo_tipo_sociedad                   VARCHAR(250),
    tipo_sociedad                          VARCHAR(250),
    codigo_organizacion_juridica           VARCHAR(250),
    organizacion_juridica                  VARCHAR(250),
    codigo_categoria_matricula             VARCHAR(250),
    categoria_matricula                    VARCHAR(250),
    codigo_estado_matricula                VARCHAR(250),
    estado_matricula                       VARCHAR(250),
    fecha_actualizacion                    TIMESTAMP,
    codigo_clase_identificacion            VARCHAR(250),
    digito_verificacion                    VARCHAR(250),
    estatus                                VARCHAR(50),
    load_datetime                          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro                     BIGINT REFERENCES catalogo.fuente_registro(id),
    id_log_etl                             BIGINT REFERENCES sire_dv.log_etl(id),
    md5_hash                               VARCHAR(40) UNIQUE
);

-- Tabla de afiliaciones (Link)
CREATE TABLE IF NOT EXISTS sire_dv.link_afiliacion (
    id                             BIGSERIAL PRIMARY KEY,
    id_hub_persona_afiliada        VARCHAR(300) REFERENCES sire_dv.hub_persona(id_estadistico),
    id_hub_persona_cotizante       VARCHAR(300) REFERENCES sire_dv.hub_persona(id_estadistico),
    id_hub_aportante_emp           VARCHAR(300) REFERENCES sire_dv.hub_empresa(id_estadistico),
    id_cod_departamento            INTEGER,
    id_cod_municipio               INTEGER,
    id_zona                        INTEGER,
    tipo_cotizante                 VARCHAR(50),
    tipo_afiliado                  VARCHAR(50),
    parentesco                     VARCHAR(70),
    ips_primaria                   VARCHAR(100),
    fecha_afiliacion               DATE,
    regimen                        VARCHAR(30),
    estado_afiliacion              VARCHAR(30),
    load_datetime                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_fuente_registro             BIGINT REFERENCES catalogo.fuente_registro(id),
    id_log_etl                     BIGINT REFERENCES sire_dv.log_etl(id),
    md5_hash                       VARCHAR(40) UNIQUE
);
