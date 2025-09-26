-- Script para limpiar duplicados en las tablas raw_obt
-- Ejecutar con cuidado y hacer backup antes

-- 1. Identificar duplicados en raw_obt_personas
SELECT 
    id_estadistico,
    tipo_documento,
    numero_documento,
    COUNT(*) as duplicados
FROM sire_sta.raw_obt_personas 
GROUP BY id_estadistico, tipo_documento, numero_documento
HAVING COUNT(*) > 1
ORDER BY duplicados DESC;

-- 2. Identificar duplicados en raw_obt_empresas
SELECT 
    id_estadistico,
    tipo_documento,
    numero_documento,
    COUNT(*) as duplicados
FROM sire_sta.raw_obt_empresas 
GROUP BY id_estadistico, tipo_documento, numero_documento
HAVING COUNT(*) > 1
ORDER BY duplicados DESC;

-- 3. Eliminar duplicados en raw_obt_personas (mantener solo el registro más reciente)
WITH duplicados AS (
    SELECT 
        id,
        ROW_NUMBER() OVER (
            PARTITION BY id_estadistico, tipo_documento, numero_documento 
            ORDER BY load_datetime DESC
        ) as rn
    FROM sire_sta.raw_obt_personas
)
DELETE FROM sire_sta.raw_obt_personas 
WHERE id IN (
    SELECT id FROM duplicados WHERE rn > 1
);

-- 4. Eliminar duplicados en raw_obt_empresas (mantener solo el registro más reciente)
WITH duplicados AS (
    SELECT 
        id,
        ROW_NUMBER() OVER (
            PARTITION BY id_estadistico, tipo_documento, numero_documento 
            ORDER BY load_datetime DESC
        ) as rn
    FROM sire_sta.raw_obt_empresas
)
DELETE FROM sire_sta.raw_obt_empresas 
WHERE id IN (
    SELECT id FROM duplicados WHERE rn > 1
);

-- 5. Verificar que no queden duplicados
SELECT 'raw_obt_personas' as tabla, COUNT(*) as total_registros, COUNT(DISTINCT id_estadistico) as ids_unicos
FROM sire_sta.raw_obt_personas
UNION ALL
SELECT 'raw_obt_empresas' as tabla, COUNT(*) as total_registros, COUNT(DISTINCT id_estadistico) as ids_unicos
FROM sire_sta.raw_obt_empresas;
