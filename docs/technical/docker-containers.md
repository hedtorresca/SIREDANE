# Docker y Contenedores - SIRE

## Visión General

El proyecto SIRE utiliza Docker para containerizar todos sus componentes, facilitando el despliegue, escalabilidad y mantenimiento del sistema. Cada componente tiene su propio contenedor con configuraciones específicas para diferentes ambientes.

## Arquitectura de Contenedores

```mermaid
graph TB
    subgraph "Contenedores SIRE"
        A[Airflow Webserver<br/>Puerto: 8080]
        B[Airflow Scheduler<br/>Puerto: 8793]
        C[FastAPI<br/>Puerto: 8001]
        D[PostgreSQL Airflow<br/>Puerto: 5432]
        E[PostgreSQL Data Warehouse<br/>Puerto: 5433]
        F[Oracle Database<br/>Puerto: 1521]
    end
    
    subgraph "Volúmenes"
        G[airflow_logs]
        H[postgres_data]
        I[oracle_data]
        J[sire_data]
    end
    
    subgraph "Redes"
        K[sire_network]
    end
    
    A --> D
    B --> D
    C --> E
    A --> K
    B --> K
    C --> K
    D --> H
    E --> H
    F --> I
    A --> G
```

## Dockerfiles

### 1. Dockerfile.airflow

**Propósito**: Contenedor para Apache Airflow con todas las dependencias necesarias.

**Características**:
- ✅ Basado en Apache Airflow 2.7.0
- ✅ Python 3.9
- ✅ Dependencias de PySpark
- ✅ Conectores de base de datos
- ✅ Configuración optimizada

**Contenido**:
```dockerfile
FROM apache/airflow:2.7.0

# Instalar dependencias del sistema
USER root
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Cambiar a usuario airflow
USER airflow

# Instalar dependencias de Python
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copiar DAGs
COPY airflow_dags/ /opt/airflow/dags/

# Copiar plugins
COPY plugins/ /opt/airflow/plugins/

# Configurar Airflow
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True

# Exponer puerto
EXPOSE 8080

# Comando de inicio
CMD ["airflow", "webserver"]
```

### 2. Dockerfile.fastapi

**Propósito**: Contenedor para la API FastAPI con soporte para PostgreSQL.

**Características**:
- ✅ Python 3.9
- ✅ FastAPI con Uvicorn
- ✅ Conectores PostgreSQL
- ✅ Configuración de producción

**Contenido**:
```dockerfile
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY FastAPI/ /app/FastAPI/
COPY src/ /app/src/

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8001

# Exponer puerto
EXPOSE 8001

# Comando de inicio
CMD ["uvicorn", "FastAPI.Main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 3. Dockerfile.fastapi.oracle

**Propósito**: Contenedor para la API FastAPI con soporte para Oracle Database.

**Características**:
- ✅ Python 3.9
- ✅ FastAPI con Uvicorn
- ✅ Conectores Oracle
- ✅ Configuración para producción

**Contenido**:
```dockerfile
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.1.0.0.0dbru.zip \
    && unzip instantclient-basic-linux.x64-21.1.0.0.0dbru.zip \
    && mv instantclient_21_1 /opt/oracle \
    && rm instantclient-basic-linux.x64-21.1.0.0.0dbru.zip

# Configurar Oracle
ENV LD_LIBRARY_PATH=/opt/oracle:$LD_LIBRARY_PATH
ENV ORACLE_HOME=/opt/oracle

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY FastAPI/ /app/FastAPI/
COPY src/ /app/src/

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8001

# Exponer puerto
EXPOSE 8001

# Comando de inicio
CMD ["uvicorn", "FastAPI.Main_oracle:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Docker Compose

### 1. docker-compose.postgresql.yml

**Propósito**: Configuración para ambiente de desarrollo con PostgreSQL.

**Características**:
- ✅ PostgreSQL para Airflow
- ✅ PostgreSQL para Data Warehouse
- ✅ Airflow Webserver y Scheduler
- ✅ FastAPI con PostgreSQL
- ✅ Volúmenes persistentes

**Contenido**:
```yaml
version: '3.8'

services:
  # PostgreSQL para Airflow
  postgres:
    image: postgres:13
    container_name: sire-postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - sire_network

  # PostgreSQL para Data Warehouse
  postgres-dw:
    image: postgres:13
    container_name: sire-postgres-dw
    environment:
      POSTGRES_USER: sire_user
      POSTGRES_PASSWORD: sire_password
      POSTGRES_DB: sire_dw
    volumes:
      - postgres_dw_data:/var/lib/postgresql/data
      - ./scripts_sql/postgres:/docker-entrypoint-initdb.d
    ports:
      - "5433:5432"
    networks:
      - sire_network

  # Airflow Webserver
  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    container_name: sire-airflow-webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
    volumes:
      - ./airflow_dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - airflow_logs:/opt/airflow/logs
    depends_on:
      - postgres
    networks:
      - sire_network

  # Airflow Scheduler
  airflow-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    container_name: sire-airflow-scheduler
    command: airflow scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./airflow_dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - airflow_logs:/opt/airflow/logs
    depends_on:
      - postgres
    networks:
      - sire_network

  # FastAPI
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    container_name: sire-fastapi
    ports:
      - "8001:8001"
    environment:
      - POSTGRES_HOST=sire-postgres-dw
      - POSTGRES_PORT=5432
      - POSTGRES_USER=sire_user
      - POSTGRES_PASSWORD=sire_password
      - POSTGRES_DATABASE=sire_dw
    depends_on:
      - postgres-dw
    networks:
      - sire_network

volumes:
  postgres_data:
  postgres_dw_data:
  airflow_logs:

networks:
  sire_network:
    driver: bridge
```

### 2. docker-compose.oracle.yml

**Propósito**: Configuración para ambiente de desarrollo con Oracle.

**Características**:
- ✅ Oracle Database
- ✅ Airflow con conectores Oracle
- ✅ FastAPI con Oracle
- ✅ Configuración optimizada

**Contenido**:
```yaml
version: '3.8'

services:
  # Oracle Database
  oracle:
    image: container-registry.oracle.com/database/express:21.3.0-xe
    container_name: sire-oracle
    environment:
      - ORACLE_PWD=oracle123
      - ORACLE_CHARACTERSET=AL32UTF8
    volumes:
      - oracle_data:/opt/oracle/oradata
      - ./scripts_sql/oracle:/docker-entrypoint-initdb.d
    ports:
      - "1521:1521"
    networks:
      - sire_network

  # Airflow Webserver
  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    container_name: sire-airflow-webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./airflow_dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - airflow_logs:/opt/airflow/logs
    depends_on:
      - postgres
    networks:
      - sire_network

  # FastAPI con Oracle
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi.oracle
    container_name: sire-fastapi-oracle
    ports:
      - "8001:8001"
    environment:
      - ORACLE_HOST=sire-oracle
      - ORACLE_PORT=1521
      - ORACLE_SERVICE_NAME=XE
      - ORACLE_USER=sire_user
      - ORACLE_PASSWORD=sire_password
    depends_on:
      - oracle
    networks:
      - sire_network

volumes:
  oracle_data:
  airflow_logs:

networks:
  sire_network:
    driver: bridge
```

### 3. docker-compose.oracle.prod.yml

**Propósito**: Configuración para ambiente de producción con Oracle.

**Características**:
- ✅ Oracle Database optimizado
- ✅ Configuración de producción
- ✅ Monitoreo y logging
- ✅ Backup automático

**Contenido**:
```yaml
version: '3.8'

services:
  # Oracle Database
  oracle:
    image: container-registry.oracle.com/database/enterprise:21.3.0.0
    container_name: sire-oracle-prod
    environment:
      - ORACLE_PWD=oracle123
      - ORACLE_CHARACTERSET=AL32UTF8
      - ORACLE_EDITION=enterprise
    volumes:
      - oracle_data:/opt/oracle/oradata
      - ./scripts_sql/oracle:/docker-entrypoint-initdb.d
    ports:
      - "1521:1521"
    networks:
      - sire_network
    restart: unless-stopped

  # Airflow Webserver
  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    container_name: sire-airflow-webserver-prod
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./airflow_dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - airflow_logs:/opt/airflow/logs
    depends_on:
      - postgres
    networks:
      - sire_network
    restart: unless-stopped

  # FastAPI con Oracle
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi.oracle
    container_name: sire-fastapi-oracle-prod
    ports:
      - "8001:8001"
    environment:
      - ORACLE_HOST=sire-oracle-prod
      - ORACLE_PORT=1521
      - ORACLE_SERVICE_NAME=SIRE
      - ORACLE_USER=sire_user
      - ORACLE_PASSWORD=sire_password
    depends_on:
      - oracle
    networks:
      - sire_network
    restart: unless-stopped

volumes:
  oracle_data:
  airflow_logs:

networks:
  sire_network:
    driver: bridge
```

## Scripts de Inicio

### 1. start-postgresql.ps1

**Propósito**: Script de PowerShell para iniciar el ambiente con PostgreSQL.

**Contenido**:
```powershell
# Script para iniciar SIRE con PostgreSQL
Write-Host "Iniciando SIRE con PostgreSQL..." -ForegroundColor Green

# Verificar que Docker esté ejecutándose
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop no está ejecutándose. Por favor, inícielo primero." -ForegroundColor Red
    exit 1
}

# Iniciar contenedores
Write-Host "Iniciando contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.postgresql.yml up -d

# Esperar a que los servicios estén listos
Write-Host "Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar estado de los contenedores
Write-Host "Verificando estado de los contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.postgresql.yml ps

# Mostrar URLs de acceso
Write-Host "`nServicios disponibles:" -ForegroundColor Green
Write-Host "Airflow: http://localhost:8080" -ForegroundColor Cyan
Write-Host "FastAPI: http://localhost:8001" -ForegroundColor Cyan
Write-Host "FastAPI Docs: http://localhost:8001/docs" -ForegroundColor Cyan

Write-Host "`nSIRE iniciado exitosamente!" -ForegroundColor Green
```

### 2. start-oracle.ps1

**Propósito**: Script de PowerShell para iniciar el ambiente con Oracle.

**Contenido**:
```powershell
# Script para iniciar SIRE con Oracle
Write-Host "Iniciando SIRE con Oracle..." -ForegroundColor Green

# Verificar que Docker esté ejecutándose
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop no está ejecutándose. Por favor, inícielo primero." -ForegroundColor Red
    exit 1
}

# Iniciar contenedores
Write-Host "Iniciando contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle.yml up -d

# Esperar a que los servicios estén listos
Write-Host "Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Verificar estado de los contenedores
Write-Host "Verificando estado de los contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle.yml ps

# Mostrar URLs de acceso
Write-Host "`nServicios disponibles:" -ForegroundColor Green
Write-Host "Airflow: http://localhost:8080" -ForegroundColor Cyan
Write-Host "FastAPI: http://localhost:8001" -ForegroundColor Cyan
Write-Host "FastAPI Docs: http://localhost:8001/docs" -ForegroundColor Cyan

Write-Host "`nSIRE iniciado exitosamente!" -ForegroundColor Green
```

### 3. start-oracle-prod.ps1

**Propósito**: Script de PowerShell para iniciar el ambiente de producción con Oracle.

**Contenido**:
```powershell
# Script para iniciar SIRE en producción con Oracle
Write-Host "Iniciando SIRE en producción con Oracle..." -ForegroundColor Green

# Verificar que Docker esté ejecutándose
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop no está ejecutándose. Por favor, inícielo primero." -ForegroundColor Red
    exit 1
}

# Verificar variables de entorno de producción
if (-not $env:ORACLE_PASSWORD) {
    Write-Host "Variable de entorno ORACLE_PASSWORD no está configurada." -ForegroundColor Red
    exit 1
}

# Iniciar contenedores
Write-Host "Iniciando contenedores de producción..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle.prod.yml up -d

# Esperar a que los servicios estén listos
Write-Host "Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

# Verificar estado de los contenedores
Write-Host "Verificando estado de los contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle.prod.yml ps

# Mostrar URLs de acceso
Write-Host "`nServicios disponibles:" -ForegroundColor Green
Write-Host "Airflow: http://localhost:8080" -ForegroundColor Cyan
Write-Host "FastAPI: http://localhost:8001" -ForegroundColor Cyan
Write-Host "FastAPI Docs: http://localhost:8001/docs" -ForegroundColor Cyan

Write-Host "`nSIRE en producción iniciado exitosamente!" -ForegroundColor Green
```

## Configuración de Volúmenes

### Volúmenes Persistentes

```yaml
volumes:
  # Datos de PostgreSQL
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/sire/data/postgres
  
  # Datos de Oracle
  oracle_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/sire/data/oracle
  
  # Logs de Airflow
  airflow_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/sire/logs/airflow
```

### Configuración de Redes

```yaml
networks:
  sire_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Monitoreo y Logs

### Configuración de Logging

```yaml
# En docker-compose.yml
services:
  airflow-webserver:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  fastapi:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Comandos de Monitoreo

```bash
# Ver logs de todos los contenedores
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f airflow-webserver

# Ver estado de los contenedores
docker-compose ps

# Ver uso de recursos
docker stats

# Ver logs de un contenedor específico
docker logs -f sire-airflow-webserver
```

## Troubleshooting

### Problemas Comunes

#### Error de Puerto en Uso
```
Error: Port 8080 is already in use
```
**Solución**: Cambiar puerto o detener el proceso que lo está usando:
```yaml
ports:
  - "8081:8080"  # Cambiar puerto externo
```

#### Error de Memoria
```
Error: Out of memory
```
**Solución**: Aumentar memoria de Docker o optimizar contenedores:
```yaml
services:
  oracle:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

#### Error de Conexión a Base de Datos
```
Error: connection refused
```
**Solución**: Verificar que la base de datos esté ejecutándose y accesible:
```bash
# Verificar estado de la base de datos
docker-compose ps postgres

# Ver logs de la base de datos
docker-compose logs postgres
```

### Comandos de Debug

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

## Mejores Prácticas

### 1. Seguridad
- No hardcodear credenciales en Dockerfiles
- Usar variables de entorno para configuración sensible
- Implementar secrets management
- Configurar firewalls y redes

### 2. Performance
- Optimizar imágenes Docker
- Usar multi-stage builds
- Implementar caching de capas
- Monitorear uso de recursos

### 3. Mantenimiento
- Actualizar imágenes regularmente
- Implementar backup de volúmenes
- Monitorear logs y métricas
- Documentar configuraciones

### 4. Escalabilidad
- Usar Docker Swarm o Kubernetes
- Implementar load balancing
- Configurar auto-scaling
- Optimizar recursos

## Ejemplos de Uso

### Iniciar Ambiente de Desarrollo

```bash
# Con PostgreSQL
./start-postgresql.ps1

# Con Oracle
./start-oracle.ps1
```

### Iniciar Ambiente de Producción

```bash
# Con Oracle
./start-oracle-prod.ps1
```

### Verificar Estado

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs -f

# Ver métricas
docker stats
```

### Detener Servicios

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Detener servicios específicos
docker-compose stop airflow-webserver
```
