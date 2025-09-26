# Despliegue de SIRE con Oracle Externo (sin contenedor de Oracle)

## Objetivo

Esta guía explica cómo desplegar la variante Oracle de SIRE conectándose a una base de datos Oracle ya existente (gestionada por un tercero), sin levantar un contenedor de Oracle. Solo se desplegarán los contenedores de FastAPI y Airflow (PostgreSQL para metadatos), mientras la API se conecta al Oracle externo usando variables de entorno.

## Requisitos

- Acceso a una instancia Oracle existente (host, puerto, service name, usuario y contraseña)
- Esquemas requeridos creados (al menos `SIRE_STA` para la API; `SIRE_OBT` y `SIRE_DV` si usará ETLs)
- Docker y Docker Compose instalados en el host donde se desplegará SIRE
- Networking permitido desde el host de SIRE hacia el servidor Oracle

## Variables de Entorno

Cree `config/prod.oracle.env` o un `.env` en la raíz con:

```bash
# Selección de variante
DATABASE_TYPE=oracle
ENVIRONMENT=prod

# Conexión Oracle externa
# Ejemplo DSN: host:puerto/SERVICIO (XEPDB1 o servicio corporativo)
PROD_ORACLE_JDBC_URL=jdbc:oracle:thin:@oracle-server:1521/XEPDB1
PROD_ORACLE_JDBC_USER=SIRE_STG
PROD_ORACLE_JDBC_PASSWORD=********
PROD_ORACLE_CONNECTION_STRING=oracle://SIRE_STG:********@oracle-server:1521/XEPDB1

# (Opcional) Esquemas destino
ORACLE_SCHEMA_STA=SIRE_STA
ORACLE_SCHEMA_DV=SIRE_DV

# FastAPI
API_HOST=0.0.0.0
API_PORT=8001
```

Notas:
- La API usa `PROD_ORACLE_CONNECTION_STRING` para SQLAlchemy y `PROD_ORACLE_JDBC_URL` para clientes JDBC (Spark) si aplica.
- Si su instancia usa un `SERVICE_NAME` diferente, ajuste la parte final del DSN (`.../SU_SERVICIO`).

## Docker Compose recomendado

Use `docker-compose.oracle.prod.yml`. Este archivo NO levanta un contenedor de Oracle; solo inicia FastAPI (imagen con cliente Oracle) y PostgreSQL para Airflow.

Lanzamiento (Windows PowerShell):
```powershell
# Si usa .env o config/prod.oracle.env, Compose los lee automáticamente.
# También puede exportar variables en la sesión actual:
$env:ENVIRONMENT = "prod"
$env:DATABASE_TYPE = "oracle"
$env:PROD_ORACLE_CONNECTION_STRING = "oracle://SIRE_STG:********@oracle-server:1521/XEPDB1"
$env:PROD_ORACLE_JDBC_USER = "SIRE_STG"
$env:PROD_ORACLE_JDBC_PASSWORD = "********"

docker compose -f docker-compose.oracle.prod.yml up -d
```

Para detener:
```powershell
docker compose -f docker-compose.oracle.prod.yml down
```

## Estructura mínima en Oracle

Esquema `SIRE_STA` con tablas usadas por la API:
- `SIRE_STA.control_ids_generados`
- `SIRE_STA.raw_obt_empresas`

Scripts útiles en `scripts_sql/oracle/` (ejecutar en la instancia Oracle):
- `check_and_create_structure.sql` (crea `control_ids_generados` si falta)
- `sire_obt_tables.sql` (crea `raw_obt_personas` y `raw_obt_empresas`)
- `sire_sta_tables.sql` (staging generales)

Asegúrese de que el usuario `PROD_ORACLE_JDBC_USER` tenga permisos `SELECT` e `INSERT` sobre estas tablas.

## Entrypoint de la API (Oracle)

- Servicio FastAPI: `sire-fastapi-oracle-prod`
- Módulo: `FastAPI/Main_oracle.py`
- Utilidades DB: `FastAPI/utils/utils_oracle.py`

Endpoints principales:
- `POST /generar-id-personas`
- `POST /generar-id-empresas`
- `POST /generar-id-empresas-cc`

## Validación rápida

1) Salud de la API
```bash
curl http://localhost:8001/
```
Respuesta esperada: JSON indicando `database: "Oracle"`.

2) Prueba generación de ID (persona)
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

3) Verificar inserción
Ejecutar en Oracle:
```sql
SELECT *
FROM SIRE_STA.control_ids_generados
WHERE tipo_documento = 'CC'
  AND numero_documento = '12345678';
```

## Troubleshooting

- Conexión rechazada: valide reachability al host/puerto Oracle (`tnsping` o `telnet oracle-server 1521`).
- ORA-01017 (credenciales): verifique usuario/contraseña y que el usuario exista en Oracle.
- ORA-12514/12541 (servicio/listener): valide `SERVICE_NAME` correcto en el DSN y listener activo.
- Permisos insuficientes: otorgue `INSERT/SELECT` sobre `SIRE_STA.control_ids_generados` y `SIRE_STA.raw_obt_empresas` al usuario de conexión.
- NLS y formato de fecha: la API usa tipos Date; evite conversiones implícitas en triggers. Si hay problemas, revise `NLS_DATE_FORMAT`.

## Seguridad

- No committear credenciales. Use variables de entorno seguras o secretos del orquestador.
- Restringir networking a Oracle (firewall, allowlist de IP del host que corre SIRE).
- Rotar contraseñas periódicamente.

## Referencias

- `docker-compose.oracle.prod.yml`: composición sin contenedor Oracle
- `Dockerfile.fastapi.oracle`: imagen de FastAPI con cliente Oracle
- `FastAPI/Main_oracle.py` y `FastAPI/utils/utils_oracle.py`: lógica de API y acceso
- `scripts_sql/oracle/*`: scripts para DBA
