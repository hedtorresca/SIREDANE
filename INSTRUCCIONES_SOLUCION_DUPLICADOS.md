# Solución para IDs Estadísticos Duplicados

## Problema Identificado
El sistema estaba guardando los `idestadistico` tanto en la API como en el DAG, causando duplicación de registros en las tablas `raw_obt_personas` y `raw_obt_empresas`.

## Cambios Realizados

### 1. Modificaciones en la API (FastAPI/utils/utils.py)
- **Función `guardar_nueva_persona()`**: Ahora solo genera el ID estadístico y lo guarda en la tabla de control `control_ids_generados`, NO en `raw_obt_personas`
- **Función `guardar_nueva_empresa()`**: Ahora solo genera el ID estadístico y lo guarda en la tabla de control `control_ids_generados`, NO en `raw_obt_empresas`
- **Funciones de búsqueda**: Actualizadas para buscar en `control_ids_generados` en lugar de las tablas raw_obt
- **Funciones de consecutivo**: Actualizadas para obtener el siguiente número desde `control_ids_generados`

### 2. Modificaciones en el DAG (airflow_dags/dag_sire_etl_with_api.py)
- **Lógica de inserción**: Ahora el DAG es el único responsable de insertar en las tablas `raw_obt_*`
- **Flujo corregido**: API genera ID → DAG recibe ID → DAG inserta en raw_obt con el ID recibido

### 3. Nueva Tabla de Control
- **Tabla**: `sire_sta.control_ids_generados`
- **Propósito**: Controlar todos los IDs estadísticos generados por la API
- **Campos**: id_estadistico, tipo_entidad, tipo_documento, numero_documento, fecha_generacion, estado

## Pasos para Aplicar la Solución

### Paso 1: Crear la tabla de control
```sql
-- Ejecutar el script
\i scripts_sql/postgres/control_ids_generados.sql
```

### Paso 2: Limpiar duplicados existentes
```sql
-- Ejecutar el script de limpieza
\i scripts_sql/postgres/cleanup_duplicates.sql
```

### Paso 3: Migrar datos existentes
```sql
-- Migrar IDs existentes a la tabla de control
\i scripts_sql/postgres/migrate_to_control_table.sql
```

### Paso 4: Reiniciar servicios
```bash
# Reiniciar la API FastAPI
# Reiniciar Airflow si está ejecutándose
```

## Verificación

### Verificar que no hay duplicados:
```sql
-- Verificar personas
SELECT id_estadistico, COUNT(*) 
FROM sire_sta.raw_obt_personas 
GROUP BY id_estadistico 
HAVING COUNT(*) > 1;

-- Verificar empresas
SELECT id_estadistico, COUNT(*) 
FROM sire_sta.raw_obt_empresas 
GROUP BY id_estadistico 
HAVING COUNT(*) > 1;
```

### Verificar la tabla de control:
```sql
SELECT 
    tipo_entidad,
    COUNT(*) as total_ids,
    COUNT(CASE WHEN estado = 'utilizado' THEN 1 END) as utilizados,
    COUNT(CASE WHEN estado = 'generado' THEN 1 END) as generados
FROM sire_sta.control_ids_generados
GROUP BY tipo_entidad;
```

## Flujo Corregido

### Antes (Problemático):
1. DAG llama a API
2. API genera ID y guarda en raw_obt_personas/empresas
3. DAG recibe ID y vuelve a guardar en raw_obt_personas/empresas
4. **Resultado**: Duplicados

### Después (Corregido):
1. DAG llama a API
2. API genera ID y guarda en control_ids_generados
3. DAG recibe ID y guarda en raw_obt_personas/empresas
4. **Resultado**: Sin duplicados

## Beneficios de la Solución

1. **Eliminación de duplicados**: Cada ID estadístico se guarda una sola vez en las tablas raw_obt
2. **Control centralizado**: Todos los IDs generados se registran en la tabla de control
3. **Trazabilidad**: Se puede rastrear cuándo y cómo se generó cada ID
4. **Consistencia**: El flujo de datos es más claro y predecible
5. **Mantenimiento**: Más fácil identificar y resolver problemas futuros

## Archivos Modificados

- `FastAPI/utils/utils.py`: Funciones de generación y búsqueda de IDs
- `airflow_dags/dag_sire_etl_with_api.py`: Lógica de inserción en el DAG
- `scripts_sql/postgres/control_ids_generados.sql`: Nueva tabla de control
- `scripts_sql/postgres/cleanup_duplicates.sql`: Script de limpieza
- `scripts_sql/postgres/migrate_to_control_table.sql`: Script de migración
