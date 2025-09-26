# SIRE - Sistema de Integración de Registros Estadísticos

## Descripción
SIRE es un sistema ETL que procesa archivos CSV y los carga a un Data Warehouse usando Apache Airflow, Apache Spark y bases de datos Oracle/PostgreSQL.

## Flujo de Datos
```
Archivos CSV → Airflow (DAGs) → Spark (Procesamiento) → PostgreSQL/Oracle (Data Vault)
```

## Estructura del Proyecto

- **airflow_dags/**: DAGs de Airflow para orquestación ETL
- **src/**: Código fuente principal
  - **config/**: Configuración de base de datos
  - **pyspark_jobs/**: Procesos ETL con PySpark
  - **data/**: Archivos CSV de entrada (BDUA, RUES)
- **FastAPI/**: API REST para generación de IDs estadísticos
  - **Main.py**: Aplicación principal FastAPI
  - **utils/**: Utilidades y esquemas de datos
- **scripts_sql/**: Scripts SQL para crear tablas
  - **oracle/**: Scripts para Oracle (DV y STA)
  - **postgres/**: Scripts para PostgreSQL (DV y STA)
- **tests/**: Pruebas unitarias
- **config/**: Archivos de configuración por ambiente

## Dependencias
- Python >= 3.9, < 3.12
- Apache Airflow >= 2.8.1
- Apache Spark 3.5.5
- oracledb, psycopg[binary], python-dotenv

## Despliegue y ejecución

### Requisitos previos
- Docker y Docker Compose instalados
- Python 3.9+ para desarrollo local

### Inicio Rápido

#### Opción 1: PostgreSQL (Recomendado para desarrollo)
```powershell
./start-postgresql.ps1
```

#### Opción 2: Oracle (dos variantes)
```powershell
# Oracle local (XE) para pruebas/desarrollo
./start-oracle.ps1

# Oracle externo (producción o integración)
./start-oracle-prod.ps1
```

Variables importantes (se leen en tiempo de ejecución):
- `ENVIRONMENT` = `dev` | `prod`
- `DATABASE_TYPE` = `postgresql` | `oracle`

### Servicios Disponibles
- **Airflow Web UI**: http://localhost:8080 (admin/admin)
- **FastAPI SIRE**: http://localhost:5003 (API para IDs estadísticos)
- **Spark Master**: http://localhost:8081
- **Base de datos destino**: localhost:5433 (PostgreSQL) o localhost:1521 (Oracle)
- **PostgreSQL Airflow**: localhost:5432

### API FastAPI - Endpoints
- `POST /generar-id-personas`: Genera ID estadístico para personas
- `POST /generar-id-empresas`: Genera ID estadístico para empresas
- `POST /generar-id-empresas-cc`: Genera ID para empresas con CC (persona natural)

Entrypoints según variante:
- PostgreSQL: `FastAPI/Main.py` (utiliza `FastAPI/utils/utils.py` y esquemas `sire_sta.*`)
- Oracle: `FastAPI/Main_oracle.py` (utiliza `FastAPI/utils/utils_oracle.py` y esquemas `SIRE_STA.*`)

### DAG Principal
El DAG `sire_etl_main` procesa automáticamente:

#### **BDUA (Base de Datos Única de Afiliados)**
- `src/data/bdua.csv` → Genera IDs estadísticos para personas usando FastAPI
- Pobla tablas: `raw_bdua`, `hub_persona`, `sat_persona`, `link_afiliacion`

#### **RUES (Registro Único Empresarial y Social)**
- `src/data/rues.csv` → Genera IDs estadísticos para empresas usando FastAPI
- Pobla tablas: `raw_rues`, `hub_empresa`, `sat_empresa`

#### **Flujo de Procesamiento**
1. **Carga Raw**: Datos CSV → Tablas staging (raw_*)
2. **Generación IDs**: FastAPI genera IDs estadísticos únicos
3. **Data Vault**: Pobla tablas Hub, Satélite y Links
4. **Afiliaciones**: Procesa relaciones entre personas y empresas

## Estructura de Base de Datos

### Data Vault (DV)
- **hub_persona**: Identificadores únicos de personas
- **sat_persona**: Atributos de personas
- **hub_empresa**: Identificadores únicos de empresas
- **sat_empresa**: Atributos de empresas
- **link_afiliacion**: Relaciones entre personas y empresas

### Staging (STA)
- **raw_bdua**: Datos raw de BDUA
- **raw_rues**: Datos raw de RUES
