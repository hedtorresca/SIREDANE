-- Tabla de control para IDs estadísticos generados
-- Esquema: sire_sta

-- Tabla de control de IDs generados
CREATE TABLE IF NOT EXISTS sire_sta.control_ids_generados (
    id                        BIGSERIAL PRIMARY KEY,
    id_estadistico            VARCHAR(100) UNIQUE,
    tipo_entidad              VARCHAR(2) CHECK (tipo_entidad IN ('01', '02')),
    tipo_documento            VARCHAR(50),
    numero_documento          VARCHAR(50),
    fecha_generacion          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado                    VARCHAR(20) DEFAULT 'generado' CHECK (estado IN ('generado', 'utilizado', 'error')),
    observaciones             TEXT,
    load_datetime             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_control_ids_tipo_entidad ON sire_sta.control_ids_generados(tipo_entidad);
CREATE INDEX IF NOT EXISTS idx_control_ids_documento ON sire_sta.control_ids_generados(tipo_documento, numero_documento);
CREATE INDEX IF NOT EXISTS idx_control_ids_fecha ON sire_sta.control_ids_generados(fecha_generacion);
CREATE INDEX IF NOT EXISTS idx_control_ids_estado ON sire_sta.control_ids_generados(estado);

-- Comentarios
COMMENT ON TABLE sire_sta.control_ids_generados IS 'Tabla de control para IDs estadísticos generados por la API';
COMMENT ON COLUMN sire_sta.control_ids_generados.id_estadistico IS 'ID estadístico generado (01+consecutivo para personas, 02+consecutivo para empresas)';
COMMENT ON COLUMN sire_sta.control_ids_generados.tipo_entidad IS 'Tipo de entidad: 01=Persona, 02=Empresa';
COMMENT ON COLUMN sire_sta.control_ids_generados.estado IS 'Estado del ID: generado, utilizado, error';
