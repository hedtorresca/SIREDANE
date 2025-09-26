-- Script para migrar datos existentes a la tabla de control
-- Ejecutar después de crear la tabla control_ids_generados

-- 1. Migrar IDs de personas existentes a la tabla de control
INSERT INTO control_ids_generados (
    id_estadistico, 
    tipo_entidad, 
    tipo_documento, 
    numero_documento, 
    fecha_generacion, 
    estado
)
SELECT DISTINCT
    id_estadistico,
    '01' as tipo_entidad,
    tipo_documento,
    numero_documento,
    load_datetime as fecha_generacion,
    'utilizado' as estado
FROM raw_obt_personas
WHERE id_estadistico IS NOT NULL;

-- 2. Migrar IDs de empresas existentes a la tabla de control
INSERT INTO control_ids_generados (
    id_estadistico, 
    tipo_entidad, 
    tipo_documento, 
    numero_documento, 
    fecha_generacion, 
    estado
)
SELECT DISTINCT
    id_estadistico,
    '02' as tipo_entidad,
    tipo_documento,
    numero_documento,
    load_datetime as fecha_generacion,
    'utilizado' as estado
FROM raw_obt_empresas
WHERE id_estadistico IS NOT NULL;

-- 3. Verificar la migración
SELECT 
    tipo_entidad,
    COUNT(*) as total_ids,
    COUNT(CASE WHEN estado = 'utilizado' THEN 1 END) as utilizados,
    COUNT(CASE WHEN estado = 'generado' THEN 1 END) as generados
FROM control_ids_generados
GROUP BY tipo_entidad
ORDER BY tipo_entidad;

COMMIT;
