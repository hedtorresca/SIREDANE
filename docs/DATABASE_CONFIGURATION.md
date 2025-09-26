# Configuración de Base de Datos - SIRE

## Flujo de Datos
```
Archivos CSV → Airflow (DAGs) → Spark (Procesamiento) → PostgreSQL/Oracle (Data Vault)
```

## Arquitectura
- **PostgreSQL para Airflow**: Metadatos de DAGs (puerto 5432)
- **Base de datos de destino**: PostgreSQL (puerto 5433) u Oracle (puerto 1521)
- **DAG principal**: `sire_etl_main` procesa CSV y carga a tablas DV/STA

## Inicio Rápido

### PostgreSQL (Recomendado)
```bash
./start-postgresql.ps1
```

### Oracle
```bash
./start-oracle.ps1
```

## Servicios Disponibles
- **Airflow Web UI**: http://localhost:8080 (admin/admin)
- **FastAPI SIRE**: http://localhost:8001 (API para IDs estadísticos)
- **Base de datos destino**: localhost:5433 (PostgreSQL) o localhost:1521 (Oracle)
- **PostgreSQL Airflow**: localhost:5432

## API FastAPI

### Endpoints Disponibles
- `POST /generar-id-personas`: Genera ID estadístico para personas
- `POST /generar-id-empresas`: Genera ID estadístico para empresas  
- `POST /generar-id-empresas-cc`: Genera ID para empresas con CC (persona natural)

### Formato de IDs Estadísticos
- **Personas**: `01` + consecutivo hexadecimal (8 dígitos)
- **Empresas**: `02` + consecutivo hexadecimal (8 dígitos)
- **Empresas CC**: Usa el ID de la persona asociada

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

## DAG Principal

El DAG `sire_etl_main` procesa automáticamente:

### **BDUA (Base de Datos Única de Afiliados)**
- **Fuente**: `src/data/bdua.csv`
- **Proceso**: Genera IDs estadísticos para personas usando FastAPI
- **Tablas pobladas**: `raw_bdua`, `hub_persona`, `sat_persona`, `link_afiliacion`

### **RUES (Registro Único Empresarial y Social)**
- **Fuente**: `src/data/rues.csv`
- **Proceso**: Genera IDs estadísticos para empresas usando FastAPI
- **Tablas pobladas**: `raw_rues`, `hub_empresa`, `sat_empresa`

### Tareas del DAG
- `validate_database_connection`: Valida conexión a BD
- `check_bdua_file_exists`: Verifica archivo BDUA
- `check_rues_file_exists`: Verifica archivo RUES  
- `process_bdua_csv`: Procesa BDUA usando FastAPI
- `process_rues_csv`: Procesa RUES usando FastAPI
- `process_afiliaciones`: Procesa relaciones entre personas y empresas

### Flujo de Procesamiento
1. **Carga Raw**: Datos CSV → Tablas staging (raw_*)
2. **Generación IDs**: FastAPI genera IDs estadísticos únicos
3. **Data Vault**: Pobla tablas Hub, Satélite y Links
4. **Afiliaciones**: Procesa relaciones entre personas y empresas

## Archivos de Configuración

### PostgreSQL
- `config/dev.postgresql.env`
- `docker-compose.postgresql.yml`

### Oracle  
- `config/dev.oracle.env`
- `docker-compose.oracle.yml`
