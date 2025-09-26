# Documentación del Proyecto SIRE

## Sistema de Integración de Registros Estadísticos

Bienvenido a la documentación completa del proyecto SIRE (Sistema de Integración de Registros Estadísticos). Este sistema está diseñado para procesar, pseudonimizar y almacenar datos estadísticos de manera segura y eficiente.

## 📚 Estructura de la Documentación

### 🏗️ [Documentación Técnica](./technical/)
- [Arquitectura del Sistema](./technical/architecture.md)
- [Configuración de Base de Datos](./technical/database-configuration.md)
- [API FastAPI](./technical/fastapi-api.md)
- [DAGs de Airflow](./technical/airflow-dags.md)
- [Jobs de PySpark](./technical/pyspark-jobs.md)
- [Docker y Contenedores](./technical/docker-containers.md)
- [Scripts SQL](./technical/sql-scripts.md)

### 👥 [Documentación de Usuario](./user/)
- [Guía de Instalación](./user/installation-guide.md)
- [Guía de Uso](./user/user-guide.md)
- [Troubleshooting](./user/troubleshooting.md)

### 📋 [Documentación Metodológica](./methodology/)
- [Data Vault 2.0](./methodology/data-vault-2.0.md)
- [Procesos ETL](./methodology/etl-processes.md)
- [Gobernanza de Datos](./methodology/data-governance.md)

## 🚀 Inicio Rápido

### 1. Instalación
```bash
# Clonar el repositorio
git clone https://github.com/tu-organizacion/sire.git
cd sire

# Iniciar con PostgreSQL (desarrollo)
.\start-postgresql.ps1

# O iniciar con Oracle (producción)
.\start-oracle-prod.ps1
```

### 2. Acceso a Servicios
- **Airflow Web UI**: http://localhost:8080
- **FastAPI Documentation**: http://localhost:8001/docs
- **Base de Datos**: `localhost:5433` (PostgreSQL) o `localhost:1521` (Oracle)

### 3. Primera Ejecución
1. Activar DAG `sire_etl_complete` en Airflow
2. Ejecutar el DAG manualmente
3. Verificar resultados en la base de datos

## 🏛️ Arquitectura del Sistema

SIRE implementa una arquitectura moderna basada en:

- **Apache Airflow**: Orquestación de procesos ETL
- **FastAPI**: API REST para generación de IDs estadísticos
- **Apache Spark**: Procesamiento de datos a gran escala
- **Data Vault 2.0**: Metodología de almacenamiento de datos
- **Docker**: Containerización y despliegue
- **PostgreSQL/Oracle**: Almacenamiento de datos

## 📊 Funcionalidades Principales

### ✅ Procesamiento ETL
- Extracción de datos desde múltiples fuentes (BDUA, RUES)
- Transformación y validación de datos
- Carga en Data Warehouse siguiendo metodología Data Vault 2.0

### ✅ Pseudonimización
- Generación de IDs estadísticos únicos
- Protección de datos sensibles
- Trazabilidad y auditoría completa

### ✅ API REST
- Generación de IDs para personas y empresas
- Validación automática de datos
- Documentación interactiva (Swagger/OpenAPI)

### ✅ Monitoreo y Auditoría
- Logs detallados de todas las operaciones
- Métricas de performance y calidad
- Alertas automáticas y notificaciones

## 🔧 Componentes del Sistema

### Airflow DAGs
- `sire_etl_complete`: DAG principal completo
- `sire_etl_oracle`: DAG para Oracle
- `sire_etl_real`: DAG de producción
- `sire_etl_simple`: DAG simplificado
- `sire_etl_with_api`: DAG con integración API

### FastAPI Endpoints
- `POST /generar-id-personas`: Generar ID para personas
- `POST /generar-id-empresas`: Generar ID para empresas
- `POST /generar-id-empresas-cc`: Generar ID para empresas con CC

### PySpark Jobs
- Carga de datos CSV a base de datos
- Procesamiento de Data Vault (Hubs, Satellites, Links)
- Cálculo de hashes y validaciones
- Auditoría y logging

### Scripts SQL
- Creación de esquemas y tablas
- Limpieza de duplicados
- Control de IDs generados
- Migración y mantenimiento

## 📈 Metodología Data Vault 2.0

SIRE implementa la metodología Data Vault 2.0 para:

- **Escalabilidad**: Soporte para grandes volúmenes de datos
- **Flexibilidad**: Adaptación a cambios en fuentes de datos
- **Auditoría**: Trazabilidad completa de cambios
- **Calidad**: Validaciones robustas de datos

### Estructura del Data Vault
- **Hubs**: Claves de negocio únicas
- **Satellites**: Atributos descriptivos e histórico
- **Links**: Relaciones entre entidades

## 🛡️ Seguridad y Gobernanza

### Protección de Datos
- Encriptación en tránsito y reposo
- Pseudonimización de datos sensibles
- Controles de acceso basados en roles
- Auditoría completa de accesos

### Cumplimiento Regulatorio
- Adherencia a regulaciones de protección de datos
- Políticas de retención de datos
- Derecho al olvido y portabilidad
- Transparencia en el manejo de datos

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Almacenamiento**: 50 GB
- **Docker**: Versión 20.10+
- **Docker Compose**: Versión 2.0+

### Requisitos Recomendados
- **CPU**: 8 cores
- **RAM**: 32 GB
- **Almacenamiento**: 100 GB SSD
- **Red**: Conexión estable a internet

## 🔍 Troubleshooting

### Problemas Comunes
- Error de puerto en uso
- Error de memoria insuficiente
- Error de conexión a base de datos
- Error de permisos

### Comandos de Debug
```bash
# Ver estado de contenedores
docker compose ps

# Ver logs de servicios
docker compose logs -f

# Ver métricas de recursos
docker stats
```

## 📞 Soporte y Contacto

### Recursos Adicionales
- **Documentación Técnica**: [docs/technical/](./technical/)
- **Guía de Usuario**: [docs/user/](./user/)
- **Documentación Metodológica**: [docs/methodology/](./methodology/)

### Contacto
- **Email**: soporte@sire.com
- **Documentación**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/tu-organizacion/sire/issues)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, lee las [guías de contribución](CONTRIBUTING.md) para más información.

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para un historial de cambios.

---

**SIRE** - Sistema de Integración de Registros Estadísticos  
*Procesando datos estadísticos de manera segura y eficiente*