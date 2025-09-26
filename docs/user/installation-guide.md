# Guía de Instalación - SIRE

## Visión General

Esta guía te ayudará a instalar y configurar el sistema SIRE (Sistema de Integración de Registros Estadísticos) en tu ambiente local o de producción. El sistema está diseñado para funcionar con Docker, lo que facilita la instalación y el despliegue.

## Requisitos del Sistema

### Requisitos Mínimos

#### Hardware
- **CPU**: 4 cores (8 cores recomendados)
- **RAM**: 8 GB (16 GB recomendados)
- **Almacenamiento**: 50 GB de espacio libre
- **Red**: Conexión a internet para descargar imágenes Docker

#### Software
- **Sistema Operativo**: Windows 10/11, macOS, o Linux
- **Docker**: Versión 20.10 o superior
- **Docker Compose**: Versión 2.0 o superior
- **Git**: Para clonar el repositorio

### Requisitos Recomendados

#### Hardware
- **CPU**: 8 cores o más
- **RAM**: 32 GB o más
- **Almacenamiento**: 100 GB SSD
- **Red**: Conexión estable a internet

#### Software
- **Docker Desktop**: Última versión estable
- **PowerShell**: Para scripts de Windows
- **Terminal**: Para sistemas Unix/Linux

## Instalación Paso a Paso

### 1. Preparación del Sistema

#### Windows

1. **Instalar Docker Desktop**:
   - Descargar desde [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Ejecutar el instalador
   - Reiniciar el sistema
   - Verificar instalación: `docker --version`

2. **Instalar Git**:
   - Descargar desde [Git for Windows](https://git-scm.com/download/win)
   - Ejecutar el instalador
   - Verificar instalación: `git --version`

3. **Instalar PowerShell** (si no está instalado):
   - PowerShell 7.0 o superior
   - Verificar instalación: `pwsh --version`

#### macOS

1. **Instalar Docker Desktop**:
   ```bash
   # Usando Homebrew
   brew install --cask docker
   
   # O descargar desde el sitio web
   # https://www.docker.com/products/docker-desktop
   ```

2. **Instalar Git**:
   ```bash
   # Usando Homebrew
   brew install git
   
   # Verificar instalación
   git --version
   ```

#### Linux (Ubuntu/Debian)

1. **Instalar Docker**:
   ```bash
   # Actualizar paquetes
   sudo apt update
   
   # Instalar dependencias
   sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release
   
   # Agregar clave GPG de Docker
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   
   # Agregar repositorio de Docker
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   
   # Instalar Docker
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io
   
   # Agregar usuario al grupo docker
   sudo usermod -aG docker $USER
   
   # Reiniciar sesión o ejecutar
   newgrp docker
   ```

2. **Instalar Docker Compose**:
   ```bash
   # Instalar Docker Compose
   sudo apt install docker-compose-plugin
   
   # Verificar instalación
   docker compose version
   ```

### 2. Clonar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/tu-organizacion/sire.git

# Navegar al directorio del proyecto
cd sire

# Verificar estructura del proyecto
ls -la
```

### 3. Configuración del Ambiente

#### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Selector de backend y ambiente
DATABASE_TYPE=postgresql   # o oracle
ENVIRONMENT=dev            # o prod

# PostgreSQL (dev)
DEV_POSTGRES_JDBC_URL=jdbc:postgresql://sire-postgres-dw:5432/sire_dw
DEV_POSTGRES_JDBC_USER=sire_user
DEV_POSTGRES_JDBC_PASSWORD=sire_password
DEV_POSTGRES_CONNECTION_STRING=postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw

# Oracle (prod o dev-oracle)
PROD_ORACLE_JDBC_URL=jdbc:oracle:thin:@oracle-server:1521/XEPDB1
PROD_ORACLE_JDBC_USER=SIRE_STG
PROD_ORACLE_JDBC_PASSWORD=sire_password
PROD_ORACLE_CONNECTION_STRING=oracle://SIRE_STG:sire_password@oracle-server:1521/XEPDB1

# API
API_HOST=0.0.0.0
API_PORT=8001

# Airflow
AIRFLOW_HOME=/opt/airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
```

#### Configuración de Docker

Verificar que Docker esté ejecutándose:

```bash
# Verificar estado de Docker
docker --version
docker compose version

# Verificar que Docker esté ejecutándose
docker info
```

### 4. Instalación de Dependencias

#### Instalar Dependencias de Python

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Verificar Dependencias

```bash
# Verificar instalación de dependencias
pip list

# Verificar que todas las dependencias estén instaladas
pip check
```

### 5. Configuración de Base de Datos

#### Para Ambiente de Desarrollo (PostgreSQL)

1. **Iniciar servicios**:
   ```bash
   # Usar script de PowerShell (Windows)
   .\start-postgresql.ps1
   
   # O usar Docker Compose directamente
   docker compose -f docker-compose.postgresql.yml up -d
   ```

2. **Verificar servicios**:
   ```bash
   # Ver estado de contenedores
   docker compose -f docker-compose.postgresql.yml ps
   
   # Ver logs
   docker compose -f docker-compose.postgresql.yml logs
   ```

3. **Verificar conexión a base de datos**:
   ```bash
   # Conectar a PostgreSQL
   docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw
   
   # Verificar esquemas
   \dn
   
   # Salir
   \q
   ```

#### Para Ambiente de Producción (Oracle)

1. **Configurar variables de entorno**:
   ```bash
   # Configurar contraseña de Oracle
   export ORACLE_PASSWORD=tu_password_seguro
   ```

2. **Iniciar servicios**:
   ```bash
   # Usar script de PowerShell (Windows)
   .\start-oracle-prod.ps1
   
   # O usar Docker Compose directamente
   docker compose -f docker-compose.oracle.prod.yml up -d
   ```

3. **Verificar servicios**:
   ```bash
   # Ver estado de contenedores
   docker compose -f docker-compose.oracle.prod.yml ps
   
   # Ver logs
   docker compose -f docker-compose.oracle.prod.yml logs
   ```

### 6. Verificación de la Instalación

#### Verificar Servicios

```bash
# Verificar que todos los contenedores estén ejecutándose
docker ps

# Verificar logs de Airflow
docker logs sire-airflow-webserver

# Verificar logs de FastAPI
docker logs sire-fastapi

# Verificar logs de base de datos
docker logs sire-postgres-dw
```

#### Para Ambiente de Desarrollo con Oracle local (XE)

1. **Iniciar servicios**:
```bash
# Usar script de PowerShell (Windows)
.\start-oracle.ps1

# O usar Docker Compose directamente
docker compose -f docker-compose.oracle.yml up -d
```

2. **Verificar servicios**: igual que en producción Oracle, pero con el compose `docker-compose.oracle.yml`.

#### Verificar Acceso a Servicios

1. **Airflow Web UI**:
   - URL: http://localhost:8080
   - Usuario: `admin`
   - Contraseña: `admin`

2. **FastAPI Documentation**:
   - URL: http://localhost:8001/docs
   - Swagger UI: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

3. **Base de Datos**:
   - PostgreSQL: `localhost:5433`
   - Oracle: `localhost:1521`

#### Verificar Funcionalidad

1. **Probar API FastAPI**:
   ```bash
   # Probar endpoint de salud
   curl http://localhost:8001/health
   
   # Probar generación de ID
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

2. **Verificar DAGs de Airflow**:
   - Acceder a http://localhost:8080
   - Verificar que los DAGs estén visibles
   - Verificar que no haya errores

3. **Verificar Base de Datos**:
   ```sql
   -- Conectar a PostgreSQL
   docker exec -it sire-postgres-dw psql -U sire_user -d sire_dw
   
   -- Verificar esquemas
   SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'sire_%';
   
   -- Verificar tablas
   SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema LIKE 'sire_%';
   ```

## Configuración Avanzada

### 1. Configuración de Red

```yaml
# En docker-compose.yml
networks:
  sire_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 2. Configuración de Volúmenes

```yaml
# En docker-compose.yml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/sire/data/postgres
```

### 3. Configuración de Logging

```yaml
# En docker-compose.yml
services:
  airflow-webserver:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. Configuración de Recursos

```yaml
# En docker-compose.yml
services:
  oracle:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

## Troubleshooting

### Problemas Comunes

#### Error de Puerto en Uso

```
Error: Port 8080 is already in use
```

**Solución**:
```bash
# Verificar qué proceso está usando el puerto
netstat -ano | findstr :8080

# Detener el proceso o cambiar puerto
# En docker-compose.yml
ports:
  - "8081:8080"  # Cambiar puerto externo
```

#### Error de Memoria

```
Error: Out of memory
```

**Solución**:
```bash
# Aumentar memoria de Docker
# En Docker Desktop: Settings > Resources > Memory

# O optimizar contenedores
docker system prune -a
```

#### Error de Conexión a Base de Datos

```
Error: connection refused
```

**Solución**:
```bash
# Verificar que la base de datos esté ejecutándose
docker ps | grep postgres

# Ver logs de la base de datos
docker logs sire-postgres-dw

# Reiniciar servicios
docker compose restart
```

#### Error de Permisos

```
Error: Permission denied
```

**Solución**:
```bash
# En Linux/macOS
sudo chown -R $USER:$USER .

# En Windows
# Ejecutar PowerShell como administrador
```

### Comandos de Debug

```bash
# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f airflow-webserver

# Entrar a un contenedor
docker exec -it sire-airflow-webserver bash

# Ver variables de entorno
docker exec sire-airflow-webserver env

# Ver procesos en ejecución
docker exec sire-airflow-webserver ps aux

# Ver configuración de red
docker network inspect sire_network
```

### Logs y Monitoreo

```bash
# Ver logs en tiempo real
docker compose logs -f

# Ver métricas de recursos
docker stats

# Ver estado de contenedores
docker compose ps

# Ver logs de un contenedor específico
docker logs -f sire-airflow-webserver
```

## Desinstalación

### 1. Detener Servicios

```bash
# Detener todos los servicios
docker compose down

# Detener servicios específicos
docker compose stop airflow-webserver
```

### 2. Eliminar Contenedores

```bash
# Eliminar contenedores
docker compose down --rmi all

# Eliminar volúmenes
docker compose down -v

# Eliminar redes
docker network prune
```

### 3. Limpiar Sistema

```bash
# Limpiar imágenes no utilizadas
docker image prune -a

# Limpiar volúmenes no utilizados
docker volume prune

# Limpiar sistema completo
docker system prune -a
```

### 4. Eliminar Archivos

```bash
# Eliminar directorio del proyecto
rm -rf sire

# Eliminar entorno virtual
rm -rf .venv
```

## Soporte y Ayuda

### Recursos Adicionales

- **Documentación Técnica**: [docs/technical/](./technical/)
- **Guía de Usuario**: [docs/user/user-guide.md](./user-guide.md)
- **Troubleshooting**: [docs/user/troubleshooting.md](./troubleshooting.md)

### Contacto

- **Email**: soporte@sire.com
- **Documentación**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/tu-organizacion/sire/issues)

### Logs de Instalación

```bash
# Guardar logs de instalación
docker compose logs > installation.log 2>&1

# Ver logs de instalación
cat installation.log
```
