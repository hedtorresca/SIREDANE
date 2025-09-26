# Configuración SIRE con Oracle Externo

## Resumen

Este documento explica cómo configurar SIRE para conectarse a una base de datos Oracle ya existente, sin crear un contenedor Oracle.

## Pasos de Configuración

### 1. Configurar Credenciales

Edita el archivo `config/prod.oracle.env` con tus credenciales reales:

```bash
# Reemplazar estos valores con tus credenciales reales
PROD_ORACLE_JDBC_URL=jdbc:oracle:thin:@tu-servidor:1521/tu-servicio
PROD_ORACLE_JDBC_USER=tu_usuario_real
PROD_ORACLE_JDBC_PASSWORD=tu_password_real
PROD_ORACLE_CONNECTION_STRING=oracle://tu_usuario_real:tu_password_real@tu-servidor:1521/tu-servicio

# Ajustar esquemas según tu estructura
ORACLE_SCHEMA_STA=TU_ESQUEMA_STA
ORACLE_SCHEMA_DV=TU_ESQUEMA_DV
```

### 2. Verificar Conexión (Opcional)

Ejecuta el script de verificación:

```bash
# Instalar dependencias si es necesario
pip install cx_Oracle sqlalchemy python-dotenv

# Ejecutar verificación
python scripts_oracle/setup_oracle_structure.py
```

Este script:
- ✅ Prueba la conexión a Oracle
- ✅ Verifica permisos del usuario
- ✅ Crea las tablas necesarias si no existen
- ✅ Verifica que la estructura esté correcta

### 3. Desplegar Sistema

Ejecuta el script de inicio:

```powershell
# En Windows PowerShell
.\start-oracle-prod.ps1
```

O manualmente:

```bash
# Construir y ejecutar
docker-compose -f docker-compose.oracle.prod.yml up -d

# Verificar estado
docker-compose -f docker-compose.oracle.prod.yml ps
```

## Estructura de Tablas Creadas

El sistema creará automáticamente estas tablas en tu esquema:

### Tabla de Control
- **`control_ids_generados`**: Controla todos los IDs estadísticos generados
  - `id`: Clave primaria autoincremental
  - `id_estadistico`: ID único (01+consecutivo o 02+consecutivo)
  - `tipo_entidad`: '01' para personas, '02' para empresas
  - `tipo_documento`: Tipo de documento
  - `numero_documento`: Número de documento
  - `fecha_generacion`: Timestamp de generación
  - `estado`: 'generado', 'utilizado', 'error'

### Tablas OBT
- **`raw_obt_personas`**: Datos de personas con IDs estadísticos
- **`raw_obt_empresas`**: Datos de empresas con IDs estadísticos

## Verificación Post-Despliegue

### 1. Verificar API
```bash
curl http://localhost:8001/
```

Respuesta esperada:
```json
{
  "message": "SIRE - Sistema de Identificación Estadística (Oracle)",
  "database": "Oracle"
}
```

### 2. Verificar Airflow
```bash
curl http://localhost:8080/health
```

### 3. Verificar Logs
```bash
# Logs de FastAPI
docker-compose -f docker-compose.oracle.prod.yml logs sire-fastapi

# Logs de Airflow
docker-compose -f docker-compose.oracle.prod.yml logs sire-airflow-webserver
```

## Resolución de Problemas

### Error de Conexión
```
❌ Error de conexión: ORA-12541: TNS:no listener
```

**Solución:**
1. Verificar que el servidor Oracle esté ejecutándose
2. Verificar que el puerto 1521 esté abierto
3. Verificar la cadena de conexión en `config/prod.oracle.env`

### Error de Permisos
```
❌ Usuario no tiene permisos suficientes
```

**Solución:**
1. Conectar como DBA y otorgar permisos:
```sql
GRANT CREATE TABLE TO tu_usuario;
GRANT CREATE INDEX TO tu_usuario;
GRANT CREATE SEQUENCE TO tu_usuario;
```

### Error de Esquema
```
❌ ORA-00942: table or view does not exist
```

**Solución:**
1. Verificar que el esquema existe
2. Ajustar `ORACLE_SCHEMA_STA` en `config/prod.oracle.env`
3. Ejecutar el script de verificación nuevamente

## Comandos Útiles

### Verificar Tablas Creadas
```sql
-- Conectar a Oracle con tu usuario
SELECT table_name, num_rows 
FROM user_tables 
WHERE table_name LIKE '%SIRE%' OR table_name LIKE '%CONTROL%'
ORDER BY table_name;
```

### Verificar Índices
```sql
SELECT index_name, table_name, status 
FROM user_indexes 
WHERE table_name IN ('CONTROL_IDS_GENERADOS', 'RAW_OBT_PERSONAS', 'RAW_OBT_EMPRESAS')
ORDER BY table_name, index_name;
```

### Limpiar y Recrear (si es necesario)
```sql
-- CUIDADO: Esto elimina todos los datos
DROP TABLE raw_obt_empresas CASCADE CONSTRAINTS;
DROP TABLE raw_obt_personas CASCADE CONSTRAINTS;
DROP TABLE control_ids_generados CASCADE CONSTRAINTS;
```

## Monitoreo

### Verificar Conexiones Activas
```sql
SELECT username, machine, program, status 
FROM v$session 
WHERE username = 'TU_USUARIO';
```

### Verificar Espacio en Tablas
```sql
SELECT table_name, num_rows, blocks, empty_blocks 
FROM user_tables 
WHERE table_name IN ('CONTROL_IDS_GENERADOS', 'RAW_OBT_PERSONAS', 'RAW_OBT_EMPRESAS');
```

## Seguridad

### Recomendaciones
1. **Usar usuario dedicado**: Crear un usuario específico para SIRE
2. **Permisos mínimos**: Solo otorgar permisos necesarios
3. **Conexión segura**: Usar SSL si está disponible
4. **Backup regular**: Configurar backup de las tablas SIRE

### Ejemplo de Usuario Dedicado
```sql
-- Como DBA
CREATE USER sire_user IDENTIFIED BY password_secure;
GRANT CREATE SESSION TO sire_user;
GRANT CREATE TABLE TO sire_user;
GRANT CREATE INDEX TO sire_user;
GRANT CREATE SEQUENCE TO sire_user;
GRANT UNLIMITED TABLESPACE TO sire_user;
```

## Soporte

Si encuentras problemas:

1. **Revisar logs**: `docker-compose -f docker-compose.oracle.prod.yml logs`
2. **Verificar conectividad**: `telnet tu-servidor 1521`
3. **Probar conexión manual**: Usar SQL*Plus o SQL Developer
4. **Ejecutar script de verificación**: `python scripts_oracle/setup_oracle_structure.py`

## Checklist de Despliegue

- [ ] Credenciales configuradas en `config/prod.oracle.env`
- [ ] Conexión a Oracle verificada
- [ ] Permisos de usuario verificados
- [ ] Estructura de tablas creada
- [ ] Docker Compose ejecutándose
- [ ] API respondiendo en puerto 8001
- [ ] Airflow accesible en puerto 8080
- [ ] Logs sin errores críticos
- [ ] Datos insertándose correctamente








