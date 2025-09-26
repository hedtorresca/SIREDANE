# Guía de Usuario - SIRE

## Visión General

Esta guía te ayudará a usar el sistema SIRE (Sistema de Integración de Registros Estadísticos) de manera efectiva. SIRE es una plataforma ETL que procesa, pseudonimiza y almacena datos estadísticos de manera segura.

## Acceso al Sistema

### 1. Interfaz Web de Airflow

**URL**: http://localhost:8080

**Credenciales**:
- Usuario: `admin`
- Contraseña: `admin`

**Funcionalidades**:
- ✅ Monitoreo de DAGs
- ✅ Ejecución manual de tareas
- ✅ Visualización de logs
- ✅ Gestión de conexiones
- ✅ Configuración de variables

### 2. API FastAPI

**URL**: http://localhost:8001

**Documentación Interactiva**:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**Funcionalidades**:
- ✅ Generación de IDs estadísticos
- ✅ Validación de datos
- ✅ Consulta de información
- ✅ Monitoreo de servicios

## Uso de la API FastAPI

### 1. Generar ID para Personas

**Endpoint**: `POST /generar-id-personas`

**Descripción**: Genera un ID estadístico único para una persona.

**Ejemplo de Uso**:

```bash
curl -X POST "http://localhost:8001/generar-id-personas" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Respuesta**:
```json
{
  "id_estadistico": "0100000001",
  "mensaje": "Nueva persona registrada exitosamente",
  "tipo_entidad": "01",
  "consecutivo": "00000001"
}
```

### 2. Generar ID para Empresas

**Endpoint**: `POST /generar-id-empresas`

**Descripción**: Genera un ID estadístico único para una empresa.

**Ejemplo de Uso**:

```bash
curl -X POST "http://localhost:8001/generar-id-empresas" \
  -H "Content-Type: application/json" \
  -d '{
    "razon_social": "EMPRESA EJEMPLO S.A.S.",
    "tipo_documento": "NIT",
    "numero_documento": "900123456",
    "digito_verificacion": "7",
    "codigo_camara": "11001",
    "camara_comercio": "BOGOTÁ",
    "matricula": "12345",
    "fecha_matricula": "2020-01-15",
    "fecha_renovacion": "2024-01-15",
    "ultimo_ano_renovado": 2024,
    "fecha_vigencia": "2025-01-15",
    "fecha_cancelacion": null,
    "codigo_tipo_sociedad": "01",
    "tipo_sociedad": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
    "codigo_organizacion_juridica": "01",
    "organizacion_juridica": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
    "codigo_estado_matricula": "01",
    "estado_matricula": "ACTIVA",
    "representante_legal": "Juan Pérez",
    "num_identificacion_representante_legal": "12345678",
    "clase_identificacion_rl": "CC",
    "fecha_actualizacion": "2024-01-15"
  }'
```

**Respuesta**:
```json
{
  "id_estadistico": "0200000001",
  "mensaje": "Nueva empresa registrada exitosamente",
  "tipo_entidad": "02",
  "consecutivo": "00000001"
}
```

### 3. Generar ID para Empresas con CC

**Endpoint**: `POST /generar-id-empresas-cc`

**Descripción**: Genera un ID estadístico para una empresa cuyo tipo de documento es CC.

**Ejemplo de Uso**:

```bash
curl -X POST "http://localhost:8001/generar-id-empresas-cc" \
  -H "Content-Type: application/json" \
  -d '{
    "razon_social": "JUAN PÉREZ GARCÍA",
    "tipo_documento": "CC",
    "numero_documento": "12345678",
    "digito_verificacion": null,
    "codigo_camara": "11001",
    "camara_comercio": "BOGOTÁ",
    "matricula": "67890",
    "fecha_matricula": "2020-01-15",
    "fecha_renovacion": "2024-01-15",
    "ultimo_ano_renovado": 2024,
    "fecha_vigencia": "2025-01-15",
    "fecha_cancelacion": null,
    "codigo_tipo_sociedad": "01",
    "tipo_sociedad": "PERSONA NATURAL",
    "codigo_organizacion_juridica": "01",
    "organizacion_juridica": "PERSONA NATURAL",
    "codigo_estado_matricula": "01",
    "estado_matricula": "ACTIVA",
    "representante_legal": "Juan Pérez García",
    "num_identificacion_representante_legal": "12345678",
    "clase_identificacion_rl": "CC",
    "fecha_actualizacion": "2024-01-15",
    "primer_nombre": "Juan",
    "segundo_nombre": "Carlos",
    "primer_apellido": "Pérez",
    "segundo_apellido": "García",
    "fecha_nacimiento": "1990-05-15",
    "sexo_an": "M",
    "codigo_municipio_nacimiento": "05001",
    "codigo_pais_nacimiento": "170",
    "fecha_defuncion": null
  }'
```

**Respuesta**:
```json
{
  "id_estadistico": "0100000001",
  "mensaje": "Empresa registrada usando ID de persona existente",
  "tipo_entidad": "01",
  "consecutivo": "00000001"
}
```

## Uso de Airflow

### 1. Acceder a la Interfaz Web

1. Abrir navegador web
2. Navegar a http://localhost:8080
3. Iniciar sesión con credenciales:
   - Usuario: `admin`
   - Contraseña: `admin`

### 2. Navegar por los DAGs

**DAGs Disponibles**:
- `sire_etl_complete` - DAG principal completo
- `sire_etl_oracle` - DAG para Oracle
- `sire_etl_real` - DAG de producción
- `sire_etl_simple` - DAG simplificado
- `sire_etl_with_api` - DAG con API
- `test_dag` - DAG de pruebas

### 3. Ejecutar un DAG

1. **Activar DAG**:
   - Hacer clic en el interruptor junto al nombre del DAG
   - El DAG se activará y aparecerá en verde

2. **Ejecutar DAG Manualmente**:
   - Hacer clic en el botón "Trigger DAG"
   - Seleccionar fecha de ejecución
   - Hacer clic en "Trigger"

3. **Monitorear Ejecución**:
   - Ver estado de las tareas en tiempo real
   - Hacer clic en una tarea para ver detalles
   - Ver logs de cada tarea

### 4. Ver Logs de Tareas

1. Hacer clic en una tarea específica
2. Seleccionar "Log" en el menú
3. Ver logs detallados de la ejecución

### 5. Configurar Variables

1. Ir a "Admin" > "Variables"
2. Agregar nuevas variables:
   - `POSTGRES_HOST`: `sire-postgres-dw`
   - `POSTGRES_PORT`: `5432`
   - `POSTGRES_USER`: `sire_user`
   - `POSTGRES_PASSWORD`: `sire_password`

## Procesamiento de Datos

### 1. Cargar Datos CSV

**Archivos Soportados**:
- BDUA (Base de Datos Única de Afiliados)
- RUES (Registro Único Empresarial y Social)

**Formato de Archivos**:
- Codificación: UTF-8
- Separador: Coma (,)
- Primera fila: Encabezados
- Formato de fechas: YYYY-MM-DD

**Ejemplo de Estructura BDUA**:
```csv
tipo_documento,numero_documento,primer_nombre,segundo_nombre,primer_apellido,segundo_apellido,fecha_nacimiento,sexo_an,codigo_municipio_nacimiento,codigo_pais_nacimiento
CC,12345678,Juan,Carlos,Pérez,García,1990-05-15,M,05001,170
CC,87654321,María,Ana,López,Rodríguez,1985-12-10,F,11001,170
```

**Ejemplo de Estructura RUES**:
```csv
razon_social,tipo_documento,numero_documento,digito_verificacion,codigo_camara,camara_comercio,matricula,fecha_matricula,fecha_renovacion,ultimo_ano_renovado
EMPRESA EJEMPLO S.A.S.,NIT,900123456,7,11001,BOGOTÁ,12345,2020-01-15,2024-01-15,2024
```

### 2. Ejecutar Proceso ETL

1. **Preparar Archivos**:
   - Colocar archivos CSV en la carpeta `src/data/`
   - Verificar formato y codificación
   - Validar datos de entrada

2. **Ejecutar DAG**:
   - Activar DAG `sire_etl_complete`
   - Ejecutar manualmente o programar
   - Monitorear progreso

3. **Verificar Resultados**:
   - Revisar logs de ejecución
   - Verificar datos en base de datos
   - Validar generación de IDs

### 3. Verificar Datos Procesados

**Consultar Base de Datos**:

```sql
-- Conectar a PostgreSQL
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw

-- Verificar esquemas
\dn

-- Verificar tablas
\dt sire_sta.*
\dt sire_obt.*
\dt sire_dv.*

-- Consultar datos de personas
SELECT COUNT(*) FROM sire_obt.personas_obt;

-- Consultar datos de empresas
SELECT COUNT(*) FROM sire_obt.empresas_obt;

-- Consultar control de IDs
SELECT tipo_entidad, COUNT(*) FROM sire_obt.control_ids_generados GROUP BY tipo_entidad;
```

## Monitoreo y Logs

### 1. Logs de Airflow

**Acceder a Logs**:
1. Ir a la interfaz web de Airflow
2. Seleccionar DAG y tarea
3. Hacer clic en "Log"

**Tipos de Logs**:
- Logs de ejecución de tareas
- Logs de errores
- Logs de conexiones
- Logs de variables

### 2. Logs de FastAPI

**Ver Logs en Tiempo Real**:
```bash
# Ver logs de FastAPI
docker logs -f sire-fastapi

# Ver logs de todos los servicios
docker compose logs -f
```

### 3. Logs de Base de Datos

**Ver Logs de PostgreSQL**:
```bash
# Ver logs de PostgreSQL
docker logs -f sire-postgres-dw

# Conectar a base de datos
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw
```

### 4. Métricas de Performance

**Ver Métricas de Recursos**:
```bash
# Ver uso de recursos
docker stats

# Ver estado de contenedores
docker ps

# Ver logs de sistema
docker system df
```

## Troubleshooting

### 1. Problemas Comunes

#### Error de Conexión a API

```
Error: connection refused
```

**Solución**:
```bash
# Verificar que FastAPI esté ejecutándose
docker ps | grep fastapi

# Reiniciar servicio
docker compose restart fastapi

# Ver logs
docker logs sire-fastapi
```

#### Error de DAG en Airflow

```
Error: DAG not found
```

**Solución**:
1. Verificar que el DAG esté en la carpeta correcta
2. Verificar sintaxis del DAG
3. Reiniciar Airflow scheduler
4. Verificar logs del scheduler

#### Error de Base de Datos

```
Error: database connection failed
```

**Solución**:
```bash
# Verificar que la base de datos esté ejecutándose
docker ps | grep postgres

# Verificar conexión
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw

# Reiniciar servicios
docker compose restart
```

### 2. Comandos de Debug

```bash
# Ver estado de todos los servicios
docker compose ps

# Ver logs de todos los servicios
docker compose logs

# Entrar a un contenedor
docker exec -it sire-airflow-webserver bash

# Ver variables de entorno
docker exec sire-airflow-webserver env

# Ver procesos en ejecución
docker exec sire-airflow-webserver ps aux
```

### 3. Verificar Salud del Sistema

```bash
# Verificar salud de FastAPI
curl http://localhost:8001/health

# Verificar salud de Airflow
curl http://localhost:8080/health

# Verificar conexión a base de datos
docker exec sire-postgres-dw pg_isready -U sire_user -d sire_dw
```

## Mejores Prácticas

### 1. Uso de la API

- ✅ Validar datos antes de enviar
- ✅ Usar códigos de respuesta HTTP
- ✅ Implementar manejo de errores
- ✅ Monitorear performance

### 2. Uso de Airflow

- ✅ Activar DAGs solo cuando sea necesario
- ✅ Monitorear logs regularmente
- ✅ Configurar alertas por email
- ✅ Mantener DAGs actualizados

### 3. Procesamiento de Datos

- ✅ Validar archivos antes de procesar
- ✅ Hacer backup de datos importantes
- ✅ Monitorear uso de recursos
- ✅ Implementar rollback cuando sea necesario

### 4. Monitoreo

- ✅ Revisar logs diariamente
- ✅ Monitorear métricas de performance
- ✅ Configurar alertas automáticas
- ✅ Mantener documentación actualizada

## Ejemplos de Uso

### 1. Procesar Archivo BDUA

```bash
# 1. Colocar archivo en la carpeta correcta
cp bdua.csv src/data/

# 2. Ejecutar DAG
# Ir a Airflow Web UI
# Activar DAG sire_etl_complete
# Ejecutar manualmente

# 3. Verificar resultados
docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw -c "SELECT COUNT(*) FROM sire_obt.personas_obt;"
```

### 2. Generar IDs Masivos

```python
import requests
import pandas as pd

# Leer archivo CSV
df = pd.read_csv('personas.csv')

# Generar IDs para cada persona
for index, row in df.iterrows():
    data = {
        'tipo_documento': row['tipo_documento'],
        'numero_documento': row['numero_documento'],
        'primer_nombre': row['primer_nombre'],
        'segundo_nombre': row['segundo_nombre'],
        'primer_apellido': row['primer_apellido'],
        'segundo_apellido': row['segundo_apellido'],
        'fecha_nacimiento': row['fecha_nacimiento'],
        'sexo_an': row['sexo_an'],
        'codigo_municipio_nacimiento': row['codigo_municipio_nacimiento'],
        'codigo_pais_nacimiento': row['codigo_pais_nacimiento']
    }
    
    response = requests.post('http://localhost:8001/generar-id-personas', json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"ID generado: {result['id_estadistico']}")
    else:
        print(f"Error: {response.text}")
```

### 3. Monitorear Sistema

```bash
#!/bin/bash
# Script de monitoreo

echo "=== Estado de Servicios ==="
docker compose ps

echo "=== Logs de FastAPI ==="
docker logs --tail 10 sire-fastapi

echo "=== Logs de Airflow ==="
docker logs --tail 10 sire-airflow-webserver

echo "=== Uso de Recursos ==="
docker stats --no-stream

echo "=== Salud de API ==="
curl -s http://localhost:8001/health
```

## Soporte y Ayuda

### Recursos Adicionales

- **Documentación Técnica**: [docs/technical/](./technical/)
- **Guía de Instalación**: [docs/user/installation-guide.md](./installation-guide.md)
- **Troubleshooting**: [docs/user/troubleshooting.md](./troubleshooting.md)

### Contacto

- **Email**: soporte@sire.com
- **Documentación**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/tu-organizacion/sire/issues)

### Logs de Usuario

```bash
# Guardar logs de sesión
docker compose logs > user_session.log 2>&1

# Ver logs de sesión
cat user_session.log
```
