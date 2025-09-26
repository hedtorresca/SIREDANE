# Troubleshooting - SIRE

## Visión General

Esta guía te ayudará a diagnosticar y resolver problemas comunes en el sistema SIRE. Incluye soluciones paso a paso para errores frecuentes, comandos de debug y mejores prácticas para el mantenimiento del sistema.

## Problemas de Instalación

### 1. Error de Docker no encontrado

**Síntoma**:
```
docker: command not found
```

**Causa**: Docker no está instalado o no está en el PATH.

**Solución**:
```bash
# Verificar instalación de Docker
docker --version

# Si no está instalado, instalar Docker Desktop
# Windows: Descargar desde https://www.docker.com/products/docker-desktop
# macOS: brew install --cask docker
# Linux: sudo apt install docker.io

# Verificar que Docker esté ejecutándose
docker info
```

### 2. Error de puerto en uso

**Síntoma**:
```
Error: Port 8080 is already in use
```

**Causa**: Otro servicio está usando el puerto 8080.

**Solución**:
```bash
# Verificar qué proceso está usando el puerto
# Windows
netstat -ano | findstr :8080

# macOS/Linux
lsof -i :8080

# Detener el proceso o cambiar puerto
# En docker-compose.yml
ports:
  - "8081:8080"  # Cambiar puerto externo
```

### 3. Error de memoria insuficiente

**Síntoma**:
```
Error: Out of memory
```

**Causa**: Docker no tiene suficiente memoria asignada.

**Solución**:
```bash
# Aumentar memoria de Docker
# Docker Desktop: Settings > Resources > Memory
# Asignar al menos 8GB de RAM

# O optimizar contenedores
docker system prune -a
docker volume prune
```

### 4. Error de permisos

**Síntoma**:
```
Error: Permission denied
```

**Causa**: Permisos insuficientes para ejecutar Docker.

**Solución**:
```bash
# En Linux/macOS
sudo usermod -aG docker $USER
newgrp docker

# En Windows
# Ejecutar PowerShell como administrador

# Verificar permisos
docker run hello-world
```

## Problemas de Servicios

### 1. Error de conexión a base de datos

**Síntoma**:
```
Error: connection refused
Error: database connection failed
```

**Causa**: La base de datos no está ejecutándose o no es accesible.

**Solución**:
```bash
# Verificar que la base de datos esté ejecutándose
docker ps | grep postgres

# Ver logs de la base de datos
docker logs sire-postgres-dw

# Verificar conexión
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw

# Reiniciar servicios
docker compose restart postgres-dw
```

### 2. Error de Airflow no accesible

**Síntoma**:
```
Error: Cannot connect to Airflow
```

**Causa**: Airflow no está ejecutándose o hay problemas de configuración.

**Solución**:
```bash
# Verificar estado de Airflow
docker ps | grep airflow

# Ver logs de Airflow
docker logs sire-airflow-webserver

# Verificar configuración
docker exec sire-airflow-webserver env | grep AIRFLOW

# Reiniciar Airflow
docker compose restart airflow-webserver
```

### 3. Error de FastAPI no accesible

**Síntoma**:
```
Error: Cannot connect to FastAPI
```

**Causa**: FastAPI no está ejecutándose o hay problemas de configuración.

**Solución**:
```bash
# Verificar estado de FastAPI
docker ps | grep fastapi

# Ver logs de FastAPI
docker logs sire-fastapi

# Verificar configuración
docker exec sire-fastapi env | grep POSTGRES

# Reiniciar FastAPI
docker compose restart fastapi
```

## Problemas de DAGs

### 1. DAG no aparece en la interfaz

**Síntoma**: El DAG no se muestra en la interfaz de Airflow.

**Causa**: Error de sintaxis o configuración en el DAG.

**Solución**:
```bash
# Verificar sintaxis del DAG
python -m py_compile airflow_dags/dag_sire_etl_complete.py

# Ver logs del scheduler
docker logs sire-airflow-scheduler

# Verificar permisos de archivos
ls -la airflow_dags/

# Reiniciar scheduler
docker compose restart airflow-scheduler
```

### 2. Error de tarea fallida

**Síntoma**: Una tarea falla repetidamente.

**Causa**: Error en la lógica de la tarea o dependencias faltantes.

**Solución**:
```bash
# Ver logs de la tarea específica
# En Airflow Web UI: DAG > Tarea > Log

# Verificar dependencias
docker exec sire-airflow-webserver pip list

# Reiniciar tarea
# En Airflow Web UI: Tarea > Clear

# Verificar configuración de conexiones
# En Airflow Web UI: Admin > Connections
```

### 3. Error de timeout en tarea

**Síntoma**: Las tareas se agotan por tiempo.

**Causa**: Tareas que toman demasiado tiempo en ejecutarse.

**Solución**:
```python
# En el DAG, aumentar timeout
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2)  # Aumentar timeout
}
```

## Problemas de API

### 1. Error de validación de datos

**Síntoma**:
```
Error: validation error for PersonaRequest
```

**Causa**: Datos de entrada inválidos o faltantes.

**Solución**:
```bash
# Verificar formato de datos
# Asegurar que todos los campos requeridos estén presentes
# Verificar tipos de datos (fechas, números, etc.)

# Ejemplo de datos válidos
{
  "tipo_documento": "CC",
  "numero_documento": "12345678",
  "primer_nombre": "Juan",
  "segundo_nombre": "Carlos",
  "primer_apellido": "Pérez",
  "segundo_apellido": "García",
  "fecha_nacimiento": "1990-05-15",
  "sexo_an": "M",
  "codigo_municipio_nacimiento": "05001",
  "codigo_pais_nacimiento": "170"
}
```

### 2. Error de conexión a base de datos desde API

**Síntoma**:
```
Error: connection timeout
```

**Causa**: La API no puede conectar a la base de datos.

**Solución**:
```bash
# Verificar configuración de conexión
docker exec sire-fastapi env | grep POSTGRES

# Verificar que la base de datos esté accesible
docker exec sire-fastapi ping sire-postgres-dw

# Verificar logs de la API
docker logs sire-fastapi

# Reiniciar servicios
docker compose restart fastapi postgres-dw
```

### 3. Error de rate limiting

**Síntoma**:
```
Error: Too many requests
```

**Causa**: Demasiadas solicitudes a la API.

**Solución**:
```bash
# Implementar rate limiting en la API
# O reducir la frecuencia de solicitudes
# O usar procesamiento por lotes
```

## Problemas de Base de Datos

### 1. Error de esquema no encontrado

**Síntoma**:
```
Error: schema "sire_sta" does not exist
```

**Causa**: Los esquemas no se crearon correctamente.

**Solución**:
```bash
# Ejecutar scripts de creación de esquemas
docker exec -i sire-postgres-dw psql -U sire_user -d sire_dw -f /docker-entrypoint-initdb.d/create_schemas.sql

# Verificar esquemas creados
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "\dn"

# Crear esquemas manualmente si es necesario
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "CREATE SCHEMA IF NOT EXISTS sire_sta;"
```

### 2. Error de tabla no encontrada

**Síntoma**:
```
Error: relation "personas_obt" does not exist
```

**Causa**: Las tablas no se crearon correctamente.

**Solución**:
```bash
# Ejecutar scripts de creación de tablas
docker exec -i sire-postgres-dw psql -U sire_user -d sire_dw -f /docker-entrypoint-initdb.d/sire_obt_tables.sql

# Verificar tablas creadas
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "\dt sire_obt.*"

# Crear tablas manualmente si es necesario
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "CREATE TABLE IF NOT EXISTS sire_obt.personas_obt (...);"
```

### 3. Error de permisos de base de datos

**Síntoma**:
```
Error: permission denied for table
```

**Causa**: Permisos insuficientes en la base de datos.

**Solución**:
```bash
# Verificar permisos del usuario
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "\dp sire_obt.personas_obt"

# Otorgar permisos necesarios
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sire_obt TO sire_user;"

# Verificar permisos
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "\dp sire_obt.*"
```

## Problemas de Performance

### 1. Sistema lento

**Síntoma**: El sistema responde lentamente.

**Causa**: Recursos insuficientes o configuración subóptima.

**Solución**:
```bash
# Verificar uso de recursos
docker stats

# Aumentar memoria de Docker
# Docker Desktop: Settings > Resources > Memory

# Optimizar contenedores
docker system prune -a
docker volume prune

# Verificar logs de errores
docker compose logs | grep -i error
```

### 2. Tareas que toman mucho tiempo

**Síntoma**: Las tareas de ETL toman demasiado tiempo.

**Causa**: Datos grandes o configuración subóptima.

**Solución**:
```python
# Optimizar configuración de Spark
spark_config = {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
}

# Usar particionamiento adecuado
df = df.coalesce(200)  # Reducir particiones
```

### 3. Memoria insuficiente

**Síntoma**: Errores de memoria en contenedores.

**Causa**: Contenedores necesitan más memoria.

**Solución**:
```yaml
# En docker-compose.yml
services:
  oracle:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

## Comandos de Debug

### 1. Verificar estado del sistema

```bash
# Ver estado de todos los contenedores
docker compose ps

# Ver logs de todos los servicios
docker compose logs

# Ver métricas de recursos
docker stats

# Ver uso de disco
docker system df
```

### 2. Debug de contenedores

```bash
# Entrar a un contenedor
docker exec -it sire-airflow-webserver bash

# Ver variables de entorno
docker exec sire-airflow-webserver env

# Ver procesos en ejecución
docker exec sire-airflow-webserver ps aux

# Ver configuración de red
docker network inspect sire_network
```

### 3. Debug de base de datos

```bash
# Conectar a PostgreSQL
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw

# Ver esquemas
\dn

# Ver tablas
\dt sire_obt.*

# Ver permisos
\dp sire_obt.*

# Ver conexiones activas
SELECT * FROM pg_stat_activity;
```

### 4. Debug de API

```bash
# Ver logs de FastAPI
docker logs -f sire-fastapi

# Probar endpoint de salud
curl http://localhost:8001/health

# Probar endpoint con datos
curl -X POST "http://localhost:8001/generar-id-personas" \
  -H "Content-Type: application/json" \
  -d '{"tipo_documento": "CC", "numero_documento": "12345678", ...}'
```

## Scripts de Diagnóstico

### 1. Script de verificación completa

```bash
#!/bin/bash
# Script de diagnóstico completo

echo "=== Verificación de SIRE ==="
echo "Fecha: $(date)"
echo

echo "=== Estado de Contenedores ==="
docker compose ps

echo
echo "=== Logs de Errores ==="
docker compose logs | grep -i error | tail -10

echo
echo "=== Uso de Recursos ==="
docker stats --no-stream

echo
echo "=== Salud de Servicios ==="
echo "FastAPI: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)"
echo "Airflow: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)"

echo
echo "=== Verificación de Base de Datos ==="
docker exec sire-postgres-dw pg_isready -U sire_user -d sire_dw

echo
echo "=== Verificación de Esquemas ==="
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'sire_%';"

echo
echo "=== Verificación de Tablas ==="
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema LIKE 'sire_%' ORDER BY table_schema, table_name;"

echo
echo "=== Verificación de IDs Generados ==="
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "SELECT tipo_entidad, COUNT(*) FROM sire_obt.control_ids_generados GROUP BY tipo_entidad;"

echo
echo "=== Verificación Completada ==="
```

### 2. Script de limpieza

```bash
#!/bin/bash
# Script de limpieza del sistema

echo "=== Limpieza de SIRE ==="
echo "Fecha: $(date)"
echo

echo "=== Detener Servicios ==="
docker compose down

echo
echo "=== Limpiar Contenedores ==="
docker container prune -f

echo
echo "=== Limpiar Imágenes ==="
docker image prune -f

echo
echo "=== Limpiar Volúmenes ==="
docker volume prune -f

echo
echo "=== Limpiar Redes ==="
docker network prune -f

echo
echo "=== Limpieza Completada ==="
```

### 3. Script de backup

```bash
#!/bin/bash
# Script de backup del sistema

echo "=== Backup de SIRE ==="
echo "Fecha: $(date)"
echo

# Crear directorio de backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cd backups/$(date +%Y%m%d_%H%M%S)

echo "=== Backup de Base de Datos ==="
docker exec sire-postgres-dw pg_dump -U sire_user -d sire_dw > sire_database_backup.sql

echo
echo "=== Backup de Configuración ==="
cp ../../docker-compose*.yml .
cp ../../.env .

echo
echo "=== Backup de DAGs ==="
cp -r ../../airflow_dags .

echo
echo "=== Backup de Scripts ==="
cp -r ../../scripts_sql .

echo
echo "=== Backup Completado ==="
```

## Mejores Prácticas

### 1. Prevención de Problemas

- ✅ Monitorear logs regularmente
- ✅ Hacer backup de datos importantes
- ✅ Mantener sistema actualizado
- ✅ Implementar alertas automáticas

### 2. Resolución de Problemas

- ✅ Identificar la causa raíz
- ✅ Documentar soluciones
- ✅ Probar soluciones en ambiente de desarrollo
- ✅ Implementar rollback cuando sea necesario

### 3. Mantenimiento

- ✅ Limpiar logs antiguos
- ✅ Optimizar base de datos
- ✅ Actualizar dependencias
- ✅ Revisar configuración regularmente

## Contacto y Soporte

### Recursos Adicionales

- **Documentación Técnica**: [docs/technical/](./technical/)
- **Guía de Usuario**: [docs/user/user-guide.md](./user-guide.md)
- **Guía de Instalación**: [docs/user/installation-guide.md](./installation-guide.md)

### Contacto

- **Email**: soporte@sire.com
- **Documentación**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/tu-organizacion/sire/issues)

### Logs de Troubleshooting

```bash
# Guardar logs de troubleshooting
docker compose logs > troubleshooting.log 2>&1

# Ver logs de troubleshooting
cat troubleshooting.log
```
