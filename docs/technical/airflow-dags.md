# DAGs de Airflow - SIRE

## Visión General

Los DAGs (Directed Acyclic Graphs) de Apache Airflow en SIRE orquestan todo el proceso ETL, desde la carga de datos hasta la generación de IDs estadísticos. Cada DAG está diseñado para un propósito específico y maneja diferentes aspectos del pipeline de datos.

## DAGs Disponibles

### 1. `dag_sire_etl_complete.py` - DAG Principal Completo

**Descripción**: DAG principal que ejecuta todo el proceso ETL de SIRE de manera completa y secuencial.

**Características**:
- ✅ Procesamiento completo de datos BDUA y RUES
- ✅ Generación de IDs estadísticos
- ✅ Carga a Data Vault
- ✅ Manejo de errores y reintentos
- ✅ Notificaciones por email

**Estructura del DAG**:
```python
# Configuración
default_args = {
    'owner': 'sire-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

# Tareas principales
t1: load_bdua_data
t2: load_rues_data
t3: generate_statistical_ids
t4: load_data_vault
t5: cleanup_temp_files
```

**Dependencias**:
```
t1 → t3 → t4 → t5
t2 → t3
```

### 2. `dag_sire_etl_oracle.py` - DAG para Oracle

**Descripción**: DAG especializado para el procesamiento de datos con base de datos Oracle.

**Características**:
- ✅ Optimizado para Oracle Database
- ✅ Manejo de esquemas Oracle específicos
- ✅ Procesamiento de datos grandes
- ✅ Configuración de conexiones Oracle

**Configuración Oracle**:
```python
# Conexión Oracle
oracle_conn = BaseHook.get_connection('oracle_default')

# Configuración específica
oracle_config = {
    'host': oracle_conn.host,
    'port': oracle_conn.port,
    'service_name': oracle_conn.extra_dejson.get('service_name'),
    'user': oracle_conn.login,
    'password': oracle_conn.password
}
```

### 3. `dag_sire_etl_real.py` - DAG de Producción

**Descripción**: DAG configurado para el ambiente de producción con configuraciones optimizadas.

**Características**:
- ✅ Configuración de producción
- ✅ Monitoreo avanzado
- ✅ Alertas automáticas
- ✅ Backup de datos
- ✅ Logs detallados

**Configuración de Producción**:
```python
# Configuración específica para producción
production_config = {
    'max_active_runs': 1,
    'catchup': False,
    'schedule_interval': '@daily',
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 5,
    'retry_delay': timedelta(minutes=10)
}
```

### 4. `dag_sire_etl_simple.py` - DAG Simplificado

**Descripción**: DAG simplificado para pruebas y desarrollo, con menos tareas y configuraciones básicas.

**Características**:
- ✅ Configuración mínima
- ✅ Ideal para desarrollo
- ✅ Procesamiento rápido
- ✅ Fácil debugging

**Tareas Simplificadas**:
```python
# Solo las tareas esenciales
t1: load_data
t2: process_data
t3: save_results
```

### 5. `dag_sire_etl_with_api.py` - DAG con API

**Descripción**: DAG que integra la API FastAPI para la generación de IDs estadísticos.

**Características**:
- ✅ Integración con FastAPI
- ✅ Generación de IDs en tiempo real
- ✅ Validación de datos
- ✅ Manejo de respuestas de API

**Integración API**:
```python
# Llamada a la API FastAPI
def call_fastapi_generate_id(data):
    response = requests.post(
        'http://fastapi:8001/generar-id-personas',
        json=data
    )
    return response.json()
```

### 6. `test_dag.py` - DAG de Pruebas

**Descripción**: DAG para pruebas unitarias y de integración del sistema.

**Características**:
- ✅ Pruebas automatizadas
- ✅ Validación de datos
- ✅ Pruebas de rendimiento
- ✅ Reportes de calidad

## Configuración de DAGs

### Variables de Entorno

```bash
# Configuración de Airflow
AIRFLOW_HOME=/opt/airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow

# Configuración de base de datos
POSTGRES_HOST=sire-postgres-dw
POSTGRES_PORT=5432
POSTGRES_USER=sire_user
POSTGRES_PASSWORD=sire_password
POSTGRES_DATABASE=sire_dw

# Configuración de Oracle (producción)
ORACLE_HOST=oracle-server
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=SIRE
ORACLE_USER=sire_user
ORACLE_PASSWORD=sire_password
```

### Configuración de Conexiones

```python
# Conexión PostgreSQL
postgres_conn = BaseHook.get_connection('postgres_default')

# Conexión Oracle
oracle_conn = BaseHook.get_connection('oracle_default')

# Conexión FastAPI
fastapi_conn = BaseHook.get_connection('fastapi_default')
```

## Tareas Comunes

### 1. Carga de Datos CSV

```python
def load_csv_data(**context):
    """Carga datos desde archivos CSV"""
    file_path = context['params']['file_path']
    table_name = context['params']['table_name']
    
    # Cargar datos con PySpark
    spark = SparkSession.builder.appName("SIRE_ETL").getOrCreate()
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    
    # Guardar en base de datos
    df.write.mode("overwrite").jdbc(
        url=postgres_url,
        table=table_name,
        properties=postgres_properties
    )
    
    return f"Datos cargados en {table_name}"
```

### 2. Generación de IDs Estadísticos

```python
def generate_statistical_ids(**context):
    """Genera IDs estadísticos usando la API FastAPI"""
    # Obtener datos de personas
    personas_df = get_personas_data()
    
    # Generar IDs para cada persona
    for row in personas_df.collect():
        data = {
            'tipo_documento': row.tipo_documento,
            'numero_documento': row.numero_documento,
            'primer_nombre': row.primer_nombre,
            # ... otros campos
        }
        
        response = requests.post(
            'http://fastapi:8001/generar-id-personas',
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            update_persona_with_id(row.id, result['id_estadistico'])
```

### 3. Carga a Data Vault

```python
def load_data_vault(**context):
    """Carga datos procesados al Data Vault"""
    # Cargar Hubs
    load_hub_persona()
    load_hub_empresa()
    
    # Cargar Satellites
    load_sat_persona()
    load_sat_empresa()
    
    # Cargar Links
    load_link_persona_empresa()
    
    return "Data Vault actualizado exitosamente"
```

### 4. Limpieza de Archivos Temporales

```python
def cleanup_temp_files(**context):
    """Limpia archivos temporales después del procesamiento"""
    temp_dir = "/tmp/sire_etl"
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
    
    return "Archivos temporales limpiados"
```

## Manejo de Errores

### Configuración de Reintentos

```python
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30)
}
```

### Manejo de Fallos

```python
def handle_task_failure(context):
    """Maneja fallos de tareas"""
    task_instance = context['task_instance']
    exception = context['exception']
    
    # Log del error
    logging.error(f"Tarea {task_instance.task_id} falló: {exception}")
    
    # Enviar notificación
    send_failure_notification(task_instance.task_id, str(exception))
    
    # Limpiar recursos
    cleanup_resources()
```

### Notificaciones

```python
def send_success_notification(**context):
    """Envía notificación de éxito"""
    email_body = f"""
    El DAG {context['dag'].dag_id} se ejecutó exitosamente.
    
    Tiempo de ejecución: {context['execution_date']}
    Duración: {context['duration']}
    """
    
    send_email(
        to=['admin@sire.com'],
        subject=f'DAG {context["dag"].dag_id} - Éxito',
        body=email_body
    )
```

## Monitoreo y Logs

### Configuración de Logs

```python
# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airflow/logs/sire_etl.log'),
        logging.StreamHandler()
    ]
)
```

### Métricas de Performance

```python
def log_performance_metrics(**context):
    """Registra métricas de performance"""
    start_time = context['start_date']
    end_time = context['end_date']
    duration = (end_time - start_time).total_seconds()
    
    metrics = {
        'dag_id': context['dag'].dag_id,
        'execution_date': context['execution_date'],
        'duration_seconds': duration,
        'task_count': len(context['dag'].tasks),
        'success_count': context['dag'].get_task_instances().filter_by(state='success').count()
    }
    
    logging.info(f"Performance metrics: {metrics}")
```

## Configuración de Docker

### Dockerfile para Airflow

```dockerfile
FROM apache/airflow:2.7.0

# Instalar dependencias
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# Copiar DAGs
COPY airflow_dags/ /opt/airflow/dags/

# Configurar usuario
USER airflow

# Comando de inicio
CMD ["airflow", "webserver"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
    depends_on:
      - postgres

  airflow-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    command: airflow scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Troubleshooting

### Problemas Comunes

#### DAG no aparece en la interfaz
```
Problema: El DAG no se muestra en la interfaz de Airflow
Solución: 
1. Verificar sintaxis del DAG
2. Revisar logs del scheduler
3. Verificar permisos de archivos
```

#### Error de conexión a base de datos
```
Problema: Error al conectar a PostgreSQL/Oracle
Solución:
1. Verificar configuración de conexión
2. Verificar que la base de datos esté ejecutándose
3. Verificar credenciales
```

#### Tarea falla repetidamente
```
Problema: Una tarea falla en todos los reintentos
Solución:
1. Revisar logs de la tarea
2. Verificar dependencias
3. Verificar recursos disponibles
```

### Comandos de Debug

```bash
# Ver logs del scheduler
docker logs -f sire-airflow-scheduler

# Ver logs del webserver
docker logs -f sire-airflow-webserver

# Ejecutar DAG manualmente
airflow dags trigger sire_etl_complete

# Ver estado de tareas
airflow tasks list sire_etl_complete

# Ver logs de una tarea específica
airflow tasks log sire_etl_complete load_data 2024-01-01
```

## Mejores Prácticas

### 1. Diseño de DAGs
- Mantener DAGs simples y enfocados
- Usar tareas atómicas
- Evitar dependencias circulares
- Documentar cada tarea

### 2. Manejo de Datos
- Validar datos de entrada
- Usar transacciones cuando sea posible
- Implementar rollback en caso de fallo
- Limpiar archivos temporales

### 3. Performance
- Usar paralelización cuando sea posible
- Optimizar consultas SQL
- Monitorear uso de recursos
- Implementar caching

### 4. Seguridad
- No hardcodear credenciales
- Usar variables de entorno
- Implementar logging de seguridad
- Validar permisos de acceso

## Ejemplos de Uso

### Ejecutar DAG Manualmente

```bash
# Activar DAG
airflow dags unpause sire_etl_complete

# Ejecutar DAG
airflow dags trigger sire_etl_complete

# Ver estado
airflow dags state sire_etl_complete
```

### Programar DAG

```python
# Configuración de schedule
dag = DAG(
    'sire_etl_complete',
    default_args=default_args,
    description='ETL completo de SIRE',
    schedule_interval='@daily',  # Ejecutar diariamente
    catchup=False,
    max_active_runs=1
)
```

### Monitorear DAG

```python
# Configuración de monitoreo
dag = DAG(
    'sire_etl_complete',
    default_args=default_args,
    description='ETL completo de SIRE',
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
    email_on_failure=True,
    email_on_retry=True,
    email=['admin@sire.com']
)
```
